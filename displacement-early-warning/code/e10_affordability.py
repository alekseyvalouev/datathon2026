import sys, os, site; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); site.addsitedir(site.getusersitepackages())  # needed because scripts run with python -I
"""E10 Current affordability: asking rent (FOR_RENT rows, price = monthly rent) by tract vs UDP tract median household income
(hinc_18 / real_hinc_18 are 2018 dollars, NOT inflated here), and rent-to-value ratios, by UDP typology."""
import numpy as np, pandas as pd
from common import *

u = load_udp().set_index('GEOID'); p = load_joined(); p = p[p.GEOID.isin(u.index)]
fr = p[(p.homeStatus == 'FOR_RENT') & p.price.between(500, 20000)]
print('FOR_RENT listings used:', len(fr), '| bedrooms known share %.3f' % fr.bedrooms.notna().mean())
t = fr.groupby('GEOID').price.agg(['size', 'median']); t = t[t['size'] >= 5].rename(columns={'size': 'n_rent', 'median': 'ask_rent'})
t2 = fr[fr.bedrooms == 2].groupby('GEOID').price.agg(['size', 'median']); t['ask_rent_2br'] = t2['median'].where(t2['size'] >= 3)
t = t.join(u[['typ', 'typ_group', 'county_name', 'real_hinc_18', 'hinc_18', 'real_mrent_18', 'mrent_18', 'per_rent_18', 'hh_18', 'rhu_18']])
t = t[t.real_hinc_18 > 0]; t['rent_to_income'] = 12 * t.ask_rent / t.real_hinc_18; t['ask_vs_acs_rent'] = t.ask_rent / t.real_mrent_18.where(t.real_mrent_18 > 0)
t['income_needed'] = t.ask_rent * 12 / 0.30; t['need_vs_income'] = t.income_needed / t.real_hinc_18
print('tracts with >=5 asking rents:', len(t), 'of', len(u), '| check real_hinc_18 == hinc_18: %s' % bool(np.allclose(t.real_hinc_18, t.hinc_18, equal_nan=True)))
def summ(g): return pd.Series({'tracts': len(g), 'listings': g.n_rent.sum(), 'median_ask_rent': g.ask_rent.median(), 'median_2br': g.ask_rent_2br.median(), 'median_hinc_2018usd': g.real_hinc_18.median(), 'median_rent_to_income': g.rent_to_income.median(),
                               'share_tracts_over_30pct': (g.rent_to_income > .30).mean(), 'share_tracts_over_50pct': (g.rent_to_income > .50).mean(), 'ask_vs_2018_acs_rent': g.ask_vs_acs_rent.median(),
                               'share_over_30pct_if_income_up_30pct': (g.rent_to_income / 1.3 > .30).mean()})
a = t.groupby('typ').apply(summ).reindex(TYP_ORDER[:-1]); print('\nasking rent vs tract median household income (2018 dollars) by typology:'); print(a.to_string()); a.to_csv(os.path.join(RES, 'e10_rent_burden_by_typology.csv'))
print('\nall tracts:'); print(summ(t).to_string()); print('\nby county:'); print(t.groupby('county_name').apply(summ).to_string())
t.to_csv(os.path.join(RES, 'e10_tract_affordability.csv'))
# rent-to-value: (a) same-property Zillow estimates on sold/for-sale homes, (b) tract asking rent vs tract median sold price
v = p[p.homeStatus.isin(['RECENTLY_SOLD', 'FOR_SALE']) & (p.zestimate > 50000) & (p.rentZestimate > 300)].copy(); v['gross_yield'] = 12 * v.rentZestimate / v.zestimate
v = v[v.gross_yield.between(.005, .25)].join(u[['typ', 'county_name']], on='GEOID')
y1 = v.groupby('typ').gross_yield.agg(['size', 'median']).reindex(TYP_ORDER[:-1]); y1.columns = ['homes', 'median_gross_yield_zestimates']
sold = p[(p.homeStatus == 'RECENTLY_SOLD') & (p.price > 50000)].groupby('GEOID').price.agg(['size', 'median']); sold = sold[sold['size'] >= 5]['median']
t['rent_to_value'] = 12 * t.ask_rent / sold.reindex(t.index); y2 = t.groupby('typ').rent_to_value.agg(['count', 'median']).reindex(TYP_ORDER[:-1]); y2.columns = ['tracts', 'median_tract_ask_rent_x12_over_median_sold_price']
y = y1.join(y2).join(v.groupby('typ').zestimate.median().rename('median_zestimate')); print('\nrent-to-value by typology:'); print(y.to_string()); y.to_csv(os.path.join(RES, 'e10_rent_to_value_by_typology.csv'))
print('\ngross yield by county:'); print(v.groupby('county_name').gross_yield.agg(['size', 'median']).to_string())
