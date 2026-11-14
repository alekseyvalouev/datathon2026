import sys, os, site; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); site.addsitedir(site.getusersitepackages())  # needed because scripts run with python -I
"""E9 Price trajectories: price per square foot 2012-14 -> 2017-19 -> 2025-26 by zip and UDP typology, and the mean-reversion test.
Because the 2017-19 median appears in both growth rates, noise in it creates a spurious negative correlation;
the robustness check uses four non-overlapping windows (2012-14 -> 2016-18 vs 2019-21 -> 2025-26)."""
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from common import *

u = load_udp(); p = load_joined(); p = p[p.GEOID.isin(u.GEOID)]; s, pr = sales_and_pairs(p)
s = s.dropna(subset=['ppsf']).join(u.set_index('GEOID')[['typ', 'typ_group', 'county_name']], on='GEOID')
def era(y): return 'a_2012_14' if 2012 <= y <= 2014 else 'b_2017_19' if 2017 <= y <= 2019 else 'c_2025_26' if y >= 2025 else None
s['era'] = s.y.map(era)
def traj(key, k):
    g = s.dropna(subset=['era']).groupby([key, 'era']).ppsf.agg(['median', 'size']).unstack(); ok = (g['size'] >= k).all(axis=1)
    m = g['median'][ok].copy(); m['n_min'] = g['size'][ok].min(axis=1); m['pre_ann'] = (m.b_2017_19 / m.a_2012_14) ** (1 / 5) - 1; m['post_ann'] = (m.c_2025_26 / m.b_2017_19) ** (1 / 7.5) - 1; return m
z = traj('zipcode', 15).join(s.groupby('zipcode').agg(city=('city', lambda x: x.mode().iat[0]), county=('county_name', lambda x: x.mode().iat[0])))
print('zips with >=15 sales in each era:', len(z), '| Spearman pre vs post growth: %.3f' % spearmanr(z.pre_ann, z.post_ann).correlation)
print('fastest pre-2019 growth:'); print(z.sort_values('pre_ann', ascending=False).head(10).to_string()); print('slowest post-2019 growth:'); print(z.sort_values('post_ann').head(10).to_string()); print('fastest post-2019 growth:'); print(z.sort_values('post_ann', ascending=False).head(8).to_string())
print('named zips:'); print(z.reindex(['94606', '94607', '94612', '94103']).to_string()); z.to_csv(os.path.join(RES, 'e9_zip_trajectories.csv'))
# robustness: four disjoint windows
def w(y): return 'w1' if 2012 <= y <= 2014 else 'w2' if 2016 <= y <= 2018 else 'w3' if 2019 <= y <= 2021 else 'w4' if y >= 2025 else None
s['w'] = s.y.map(w); g = s.dropna(subset=['w']).groupby(['zipcode', 'w']).ppsf.agg(['median', 'size']).unstack(); m = g['median'][(g['size'] >= 15).all(axis=1)]
print('\ndisjoint windows: zips n=%d Spearman(2012-14->2016-18, 2019-21->2025-26) = %.3f' % (len(m), spearmanr(m.w2 / m.w1, m.w4 / m.w3).correlation))
print('level effect: Spearman(2016-18 ppsf level, 2019-21->2025-26 growth) = %.3f' % spearmanr(m.w2, m.w4 / m.w3).correlation)
t = traj('GEOID', 8); print('tract level (>=8 sales per era): n=%d Spearman pre vs post %.3f (shared-midpoint caveat applies)' % (len(t), spearmanr(t.pre_ann, t.post_ann).correlation))
ty = traj('typ', 30).reindex(TYP_ORDER[:-1]); print('\npooled median $/sqft by UDP typology:'); print(ty.to_string()); ty.to_csv(os.path.join(RES, 'e9_typology_trajectories.csv'))
print('\nby county:'); print(traj('county_name', 30).to_string())
# composition-robust: same-property repeat sales
pr = pr.join(u.set_index('GEOID')[['typ', 'typ_group', 'county_name']], on='GEOID'); pr = pr[pr.mo >= 24]
a = pr[(pr.buy_y >= 2012) & (pr.y <= 2019)]; b = pr[pr.buy_y >= 2019]
rs = pd.DataFrame({'pre_pairs': a.groupby('typ').size(), 'pre_median_ann': a.groupby('typ').ann.median(), 'post_pairs': b.groupby('typ').size(), 'post_median_ann': b.groupby('typ').ann.median()}).reindex(TYP_ORDER[:-1])
print('\nrepeat-sale median annualized appreciation (held >=24 months): bought 2012+ & sold by 2019 vs bought 2019+'); print(rs.to_string()); rs.to_csv(os.path.join(RES, 'e9_repeat_sales_by_typology.csv'))
print(pd.DataFrame({'pre_pairs': a.groupby('county_name').size(), 'pre_median_ann': a.groupby('county_name').ann.median(), 'post_pairs': b.groupby('county_name').size(), 'post_median_ann': b.groupby('county_name').ann.median()}).to_string())
