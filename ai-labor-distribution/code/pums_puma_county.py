import sys, pandas as pd
src, out = sys.argv[1], sys.argv[2]
t = pd.read_csv(src, dtype=str, encoding='utf-8-sig')
t = t[t.STATEFP=='06']
bay = {'001':'Alameda','013':'Contra Costa','041':'Marin','055':'Napa','075':'San Francisco','081':'San Mateo','085':'Santa Clara','095':'Solano','097':'Sonoma'}
g = t.groupby(['PUMA5CE','COUNTYFP']).size().rename('tracts').reset_index()
tot = g.groupby('PUMA5CE').tracts.transform('sum')
g['share'] = g.tracts/tot
g['ncounty'] = g.groupby('PUMA5CE').COUNTYFP.transform('nunique')
dom = g.sort_values(['PUMA5CE','tracts'],ascending=[True,False]).drop_duplicates('PUMA5CE')
dom = dom.rename(columns={'COUNTYFP':'dom_county','share':'dom_share'})
# any bay county touched
touch = g[g.COUNTYFP.isin(bay)].groupby('PUMA5CE').COUNTYFP.apply(lambda s: ','.join(sorted(s))).rename('bay_counties_touched')
x = dom.merge(touch, on='PUMA5CE', how='left')
x['is_bay'] = x.dom_county.isin(bay)
x['county_name'] = x.dom_county.map(bay)
x['split'] = x.ncounty>1
x[['PUMA5CE','dom_county','county_name','dom_share','ncounty','split','is_bay','bay_counties_touched']].to_csv(out, index=False)
b = x[x.is_bay | x.bay_counties_touched.notna()]
print(b.to_string())
