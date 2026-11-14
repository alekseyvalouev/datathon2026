import sys, os, site; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); site.addsitedir(site.getusersitepackages())  # needed because scripts run with python -I
"""E8 Same-unit asking-rent jump between consecutive listing episodes of the same zpid, 1-6 years apart.
A listing episode starts at a 'Listed for rent' event; its rent is that event's price. Annualized change between consecutive episodes.
Apartment zpids can be whole buildings (different units under one id), so results are shown separately for non-apartment homes."""
import numpy as np, pandas as pd
from common import *

u = load_udp(); p = load_joined(); p = p[p.GEOID.isin(u.GEOID)]
e = load_events(); r = e[(e.rental == 1) & (e.event == 'Listed for rent') & (e.price > 500) & (e.price < 20000)].sort_values(['zpid', 'd'])
r = r.join(p.set_index('zpid')[['GEOID', 'zipcode', 'city', 'homeType', 'bedrooms']], on='zpid', how='inner').join(u.set_index('GEOID')[['typ', 'typ_group', 'county_name']], on='GEOID')
r['pd_'] = r.groupby('zpid').d.shift(); r['pp'] = r.groupby('zpid').price.shift()
x = r.dropna(subset=['pp']).copy(); x['yrs'] = (x.d - x.pd_).dt.days / 365.25
print("'Listed for rent' events:", len(r), '| consecutive pairs:', len(x))
x = x[x.yrs.between(1, 6)]; x['ratio'] = x.price / x.pp; print('pairs 1-6 years apart:', len(x))
x = x[x.ratio.between(0.5, 2.0)]; x['ann'] = x.ratio ** (1 / x.yrs) - 1
x['unit'] = np.where(x.homeType == 'APARTMENT', 'apartment zpid', 'house/condo/townhome zpid'); x['end_y'] = x.d.dt.year
print('after dropping ratios outside 0.5-2.0:', len(x), '| distinct zpids', x.zpid.nunique(), '| end year range', x.end_y.min(), x.end_y.max())
def summ(g): return pd.Series({'pairs': len(g), 'median_ann': g.ann.median(), 'p75_ann': g.ann.quantile(.75), 'share_over_5pct': (g.ann > .05).mean(), 'share_over_10pct': (g.ann > .10).mean(), 'share_decline': (g.ann < 0).mean(), 'median_gap_yrs': g.yrs.median()})
out = []
for name, key in [('all', lambda d: pd.Series('all', index=d.index)), ('unit type', 'unit'), ('end year', lambda d: np.where(d.end_y <= 2019, '<=2019', np.where(d.end_y <= 2022, '2020-22', np.where(d.end_y <= 2024, '2023-24', '2025-26')))), ('county', 'county_name'), ('typology', 'typ'), ('typology group', 'typ_group')]:
    k = key(x) if callable(key) else x[key]; t = x.groupby(k).apply(summ); t.insert(0, 'cut', name); out.append(t); print('\n--', name); print(t.drop(columns='cut').to_string())
pd.concat(out).to_csv(os.path.join(RES, 'e8_rent_turnover.csv'))
h = x[x.unit != 'apartment zpid']; print('\nhouses/condos only, by typology group:'); print(h.groupby('typ_group').apply(summ).to_string()); print('houses/condos only, by county:'); print(h.groupby('county_name').apply(summ).to_string())
z = x.groupby('zipcode').apply(summ).join(x.groupby('zipcode').agg(city=('city', lambda s: s.mode().iat[0]))); z = z[z.pairs >= 40]
print('\nzips with >=40 pairs:', len(z)); print(z.sort_values('share_over_10pct', ascending=False).head(10).to_string()); print(z.sort_values('median_ann').head(6).to_string()); z.to_csv(os.path.join(RES, 'e8_rent_turnover_by_zip.csv'))
