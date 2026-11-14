import sys, os, site; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); site.addsitedir(site.getusersitepackages())  # needed because scripts run with python -I
"""E1 UDP landscape: typology counts, population, tract profile, by county."""
import os, pandas as pd, numpy as np
from common import *

d = load_udp()
print('Bay Area tracts (9 counties, pop00flag==1):', len(d), '| population 2018:', int(d.pop_18.sum()))
print('share lostli_18:', round(d.lostli_18.mean(), 4), '| lostli_18 == (ch_all_li_count_00_18<0):',
      bool(((d.ch_all_li_count_00_18 < 0).astype(int) == d.lostli_18).all()))
prof = d.groupby('typ').agg(tracts=('GEOID', 'size'), pop_18=('pop_18', 'sum'), lostli_18=('lostli_18', 'mean'),
                            med_hinc_18=('real_hinc_18', 'median'), med_rent_18=('real_mrent_18', 'median'),
                            med_hval_18=('real_mhval_18', 'median'), per_li_18=('per_all_li_18', 'mean'),
                            per_nonwhite_18=('per_nonwhite_18', 'mean'), per_rent_18=('per_rent_18', 'mean'),
                            per_col_18=('per_col_18', 'mean'), rail=('rail', 'mean'),
                            ch_li_hh_00_18=('ch_all_li_count_00_18', 'sum')).reindex(TYP_ORDER)
prof['share_tracts'] = prof.tracts / len(d); prof['share_pop'] = prof.pop_18 / d.pop_18.sum()
prof.insert(0, 'name', [TYP_NAME[t] for t in prof.index])
print(prof.T.to_string()); prof.to_csv(os.path.join(RES, 'e1_typology_profile.csv'))
cty = d.groupby('county_name').agg(tracts=('GEOID', 'size'), pop_18=('pop_18', 'sum'), lostli_18=('lostli_18', 'mean'),
                                   vul_gent_18=('vul_gent_18', 'mean'), hotmarket_18=('hotmarket_18', 'mean'),
                                   net_ch_li_hh_00_18=('ch_all_li_count_00_18', 'sum'))
ct = pd.crosstab(d.county_name, d.typ).reindex(columns=TYP_ORDER, fill_value=0)
cty = cty.join(ct); print(cty.to_string()); cty.to_csv(os.path.join(RES, 'e1_by_county.csv'))
risk = d.typ.isin(['LISD', 'OD', 'ARG', 'EOG', 'AdvG'])
print('tracts in displacement/gentrification typologies (LISD,OD,ARG,EOG,AdvG):', int(risk.sum()),
      'pop', int(d.pop_18[risk].sum()), 'share pop', round(d.pop_18[risk].sum() / d.pop_18.sum(), 3))
print('leakage check: lostli_18 mean by typology'); print(d.groupby('typ').lostli_18.agg(['mean', 'size']).T.to_string())
print('net low-income households 2000-18, all tracts:', int(d.ch_all_li_count_00_18.sum()),
      '| in losing tracts:', int(d.ch_all_li_count_00_18[d.lostli_18 == 1].sum()))
