import sys, os, site; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); site.addsitedir(site.getusersitepackages())  # needed because scripts run with python -I
"""E4b cross-check: tract GEOIDs in the UDP GeoPackage (data/downloads_for_public/sanfrancisco.gpkg) vs the
cartographic boundary shapefile used for the point-in-polygon join (cb_2018_06_tract_500k) vs the 1,550 Bay tracts."""
import geopandas as gpd
from common import *
u = load_udp()
g = gpd.read_file(os.path.join(UDP_REPO, 'data/downloads_for_public/sanfrancisco.gpkg'))
print('gpkg rows', len(g), 'crs', g.crs, 'columns', list(g.columns)[:12])
gc = [c for c in g.columns if c.upper() in ('GEOID', 'FIPS')][0]
g['GEOID'] = g[gc].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(11)
s = gpd.read_file(TRACT_SHP + '.shp'); s = s[s.COUNTYFP.isin(COUNTY)]
print('Bay tracts (1,550) matched in GeoPackage:', int(u.GEOID.isin(g.GEOID).sum()), '| matched in cb_2018 shapefile:', int(u.GEOID.isin(s.GEOID).sum()))
m = g.merge(s[['GEOID', 'geometry']], on='GEOID', suffixes=('', '_shp'))
m = m[m.GEOID.isin(u.GEOID)]
a = gpd.GeoSeries(m.geometry, crs=g.crs).to_crs(3310); b = gpd.GeoSeries(m.geometry_shp, crs=s.crs).to_crs(3310)
iou = a.intersection(b).area.values / a.union(b).area.values
print('polygon overlap (IoU) between the two sources, n=%d: median %.4f, min %.4f, share >0.99: %.4f' % (len(m), np.median(iou), iou.min(), (iou > .99).mean()))
