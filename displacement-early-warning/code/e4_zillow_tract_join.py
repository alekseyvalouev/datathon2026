import sys, os, site; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); site.addsitedir(site.getusersitepackages())  # needed because scripts run with python -I
"""E4 Zillow-to-tract join: point-in-polygon of every property into 2010-vintage census tracts
(Census cartographic boundary file cb_2018_06_tract_500k shipped in the UDP repo; 2010 tract
definitions were in force through 2019). Coverage by homeStatus and a 30-property hand check."""
import os, numpy as np, pandas as pd, shapefile, shapely
from shapely.geometry import shape
from shapely.strtree import STRtree
from common import *

p = load_props()
print('properties:', len(p), '| with lat/lon:', int(p.latitude.notna().sum()))
print(p.homeStatus.value_counts().to_string())
sf = shapefile.Reader(TRACT_SHP)
fld = [f[0] for f in sf.fields[1:]]
recs = [dict(zip(fld, r)) for r in sf.records()]
geoms = [shape(s.__geo_interface__) for s in sf.shapes()]
keep = [i for i, r in enumerate(recs) if r['COUNTYFP'] in COUNTY]
geoms = [geoms[i] for i in keep]; geoid = np.array([recs[i]['GEOID'] for i in keep])
print('Bay Area tract polygons:', len(geoms))
tree = STRtree(geoms)
cen = shapely.centroid(geoms)
pd.DataFrame({'GEOID': geoid, 'lon': shapely.get_x(cen), 'lat': shapely.get_y(cen)}).to_csv(os.path.join(RES, 'e4_tract_centroids.csv'), index=False)
pts = shapely.points(p.longitude.values, p.latitude.values)
ip, it = tree.query(pts, predicate='within')
g = pd.Series(geoid[it], index=ip); g = g[~g.index.duplicated()]
p['GEOID'] = g.reindex(range(len(p))).values
miss = p.GEOID.isna()
print('matched inside a polygon:', int((~miss).sum()), '| unmatched:', int(miss.sum()))
# unmatched points (simplified 1:500k coastline / water edges): nearest tract within ~250 m
if miss.any():
    ok = miss & p.latitude.between(36, 39.5) & p.longitude.between(-124, -121)
    near = tree.query_nearest(pts[ok.values], max_distance=0.0025, return_distance=False)
    n2 = pd.Series(geoid[near[1]], index=np.flatnonzero(ok.values)[near[0]]); n2 = n2[~n2.index.duplicated()]
    p.loc[p.index[n2.index], 'GEOID'] = n2.values
    print('recovered by nearest-tract (<=0.0025 deg):', len(n2), '| still unmatched:', int(p.GEOID.isna().sum()))
p['join'] = np.where(miss & p.GEOID.notna(), 'nearest', np.where(p.GEOID.notna(), 'within', 'none'))
p['tract_county'] = p.GEOID.str[2:5].map(COUNTY)
m = p.GEOID.notna()
agree = (p.tract_county[m] == p.county[m])
print('county agreement (tract county vs Zillow county field), all matched rows: %.4f (n=%d, disagree=%d)' % (agree.mean(), m.sum(), (~agree).sum()))
print(pd.crosstab(p.county[m], p.tract_county[m]).to_string())
u = load_udp()
p['in_udp'] = p.GEOID.isin(u.GEOID)
print('properties in a UDP-classified tract (pop00flag==1):', int(p.in_udp.sum()))
cov = pd.crosstab(p.GEOID[m], p.homeStatus[m]).reindex(u.GEOID, fill_value=0)
cov['total'] = cov.sum(axis=1)
print('UDP tracts with >=1 property: %d of %d; >=10: %d; >=30: %d' % ((cov.total > 0).sum(), len(u), (cov.total >= 10).sum(), (cov.total >= 30).sum()))
print(cov.describe(percentiles=[.1, .25, .5, .75, .9]).T.to_string())
for c in ['FOR_RENT', 'RECENTLY_SOLD', 'FOR_SALE']:
    print(c, 'tracts with >=5:', int((cov[c] >= 5).sum()), '>=10:', int((cov[c] >= 10).sum()))
cov.to_csv(os.path.join(RES, 'e4_tract_coverage.csv'))
cc = cov.join(u.set_index('GEOID')[['typ', 'county_name']])
print(cc.groupby('typ')[['FOR_RENT', 'RECENTLY_SOLD', 'FOR_SALE', 'total']].agg(['sum', 'median']).to_string())
print(cc.groupby('county_name')[['FOR_RENT', 'RECENTLY_SOLD', 'FOR_SALE', 'total']].sum().to_string())
# hand check: 30 random properties (seeded); no street addresses, coordinates rounded to 3 decimals
hc = p[m].sample(30, random_state=SEED)[['zpid', 'city', 'county', 'zipcode', 'homeStatus', 'latitude', 'longitude', 'GEOID', 'tract_county', 'join']].copy()
hc['latitude'] = hc.latitude.round(3); hc['longitude'] = hc.longitude.round(3)
hc['county_match'] = hc.county == hc.tract_county
hc = hc.drop(columns='zpid')
print(hc.to_string()); print('hand-check county agreement: %d of 30' % hc.county_match.sum())
p[m & p.in_udp].groupby('GEOID').city.agg(lambda x: x.mode().iat[0] if x.notna().any() else '').rename('city').to_csv(os.path.join(RES, 'e4_tract_city.csv'))
hc.to_csv(os.path.join(RES, 'e4_hand_check_30.csv'), index=False)
p.to_csv(os.path.join(RES, 'e4_property_tract.csv.gz'), index=False)
