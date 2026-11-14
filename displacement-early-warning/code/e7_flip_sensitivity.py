import sys, os, site; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); site.addsitedir(site.getusersitepackages())  # needed because scripts run with python -I
"""E7 Flip definition sensitivity (resale within 12/18/24 months at >=10/20/30% markup), geography, typology, persistence."""
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from common import *

u = load_udp(); p = load_joined(); p = p[p.GEOID.isin(u.GEOID)]; s, pr = sales_and_pairs(p)
pr = pr.join(u.set_index('GEOID')[['typ', 'typ_group', 'county_name']], on='GEOID')
post = pr[pr.y >= 2019].copy(); pre = pr[(pr.y >= 2009) & (pr.y <= 2018)].copy()
print('resale pairs all years', len(pr), '| base-definition flips', int(pr.flip.sum()), '| post-2019 pairs', len(post), 'flips', int(post.flip.sum()), '| 2009-18 pairs', len(pre), 'flips', int(pre.flip.sum()))
base = post.groupby('GEOID').flip.agg(['size', 'mean']); base = base[base['size'] >= 15]['mean']
rows = []; bytyp = {}
for mo in [12, 18, 24]:
    for mk in [.1, .2, .3]:
        f = ((post.mo <= mo) & (post.mk >= mk)).astype(int); fp_ = ((pre.mo <= mo) & (pre.mk >= mk)).astype(int)
        tr = f.groupby(post.GEOID).agg(['size', 'mean']); tr = tr[tr['size'] >= 15]['mean']
        top = set(tr.nlargest(len(tr) // 4).index) & set(base.nlargest(len(base) // 4).index)
        rows.append(dict(months=mo, markup=mk, flips_2019_26=int(f.sum()), share_2019_26=f.mean(), share_2009_18=fp_.mean(), median_markup=post.mk[f == 1].median(),
                         spearman_tract_vs_base=spearmanr(tr, base.reindex(tr.index)).correlation, top_quartile_overlap=len(top) / (len(base) // 4)))
        bytyp[f'{mo}mo_{int(mk*100)}pct'] = f.groupby(post.typ).mean()
sens = pd.DataFrame(rows); print(sens.to_string(index=False)); sens.to_csv(os.path.join(RES, 'e7_flip_sensitivity.csv'), index=False)
bt = pd.DataFrame(bytyp).reindex(TYP_ORDER[:-1]); bt.insert(0, 'resales', post.groupby('typ').size()); print('\nflip share of 2019-26 resales by UDP typology, each definition:'); print(bt.to_string()); bt.to_csv(os.path.join(RES, 'e7_flip_by_typology.csv'))
print('\nbase definition by typology group, 2009-18 vs 2019-26:'); print(pd.DataFrame({'pre_n': pre.groupby('typ_group').size(), 'pre_share': pre.groupby('typ_group').flip.mean(), 'post_n': post.groupby('typ_group').size(), 'post_share': post.groupby('typ_group').flip.mean()}).to_string())
print('\nby county (base):'); print(pd.DataFrame({'pre_n': pre.groupby('county_name').size(), 'pre_share': pre.groupby('county_name').flip.mean(), 'post_n': post.groupby('county_name').size(), 'post_flips': post.groupby('county_name').flip.sum(), 'post_share': post.groupby('county_name').flip.mean()}).to_string())
z = post.groupby('zipcode').agg(city=('city', lambda x: x.mode().iat[0]), county=('county_name', lambda x: x.mode().iat[0]), n=('flip', 'size'), flips=('flip', 'sum'), share=('flip', 'mean'), med_markup=('mk', lambda x: x[post.loc[x.index, 'flip'] == 1].median()))
z = z[z.n >= 80]; print('\nzips with >=80 resales 2019-26:', len(z)); print(z.sort_values('share', ascending=False).head(12).to_string()); print(z.sort_values('share').head(5).to_string()); z.to_csv(os.path.join(RES, 'e7_flip_by_zip.csv'))
zp = pre.groupby('zipcode').flip.agg(['size', 'mean']); zp = zp[zp['size'] >= 40]; j = z.join(zp, how='inner'); print('\npersistence zip level (>=40 pairs 2009-18, >=80 2019-26): n=%d Spearman %.3f' % (len(j), spearmanr(j.share, j['mean']).correlation))
tp = pre.groupby('GEOID').flip.agg(['size', 'mean']); tp = tp[tp['size'] >= 15]; j = tp.join(base.rename('post'), how='inner'); print('persistence tract level (>=15 pairs both periods): n=%d Spearman %.3f' % (len(j), spearmanr(j['mean'], j.post).correlation))
tr = post.groupby('GEOID').flip.agg(['size', 'mean']); tr = tr[tr['size'] >= 15].join(u.set_index('GEOID')[['per_all_li_18', 'per_nonwhite_18', 'per_rent_18', 'per_col_18', 'real_hinc_18', 'real_mhval_18', 'vul_gent_18']])
print('\nSpearman of tract flip share 2019-26 with 2018 tract traits (n=%d):' % len(tr)); print(tr.drop(columns='size').corr(method='spearman')['mean'].round(3).to_string())
print('who flips: home type share among flips vs all resales'); print(pd.DataFrame({'flips': post[post.flip == 1].homeType.value_counts(normalize=True), 'all': post.homeType.value_counts(normalize=True)}).head(6).to_string())
print('median purchase price: flips %.0f vs other resales %.0f' % (post.pp[post.flip == 1].median(), post.pp[post.flip == 0].median()))
