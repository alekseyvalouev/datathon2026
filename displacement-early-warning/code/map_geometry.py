"""Simplified tract polygons for the web map: reads the Census tract shapefile shipped in the UDP repo,
keeps the 1,550 study tracts, projects to a local equirectangular plane, simplifies, and writes compact JSON."""
import sys, os, json, math
import shapefile  # pyshp
from shapely.geometry import shape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
d = load_udp(); keep = set(d.GEOID)
r = shapefile.Reader(TRACT_SHP); fields = [f[0] for f in r.fields[1:]]; gi = fields.index('GEOID')
lat0 = 37.8; kx = math.cos(math.radians(lat0))
out = {}; minx = miny = 1e9; maxx = maxy = -1e9
geoms = {}
for sr in r.iterShapeRecords():
    g = sr.record[gi]
    if g not in keep: continue
    geoms[g] = shape(sr.shape.__geo_interface__).simplify(0.0012, preserve_topology=True)
    b = geoms[g].bounds; minx = min(minx, b[0]); miny = min(miny, b[1]); maxx = max(maxx, b[2]); maxy = max(maxy, b[3])
W = 1000; sc = W / ((maxx - minx) * kx); H = (maxy - miny) * sc
def ring(c): return [[round((x - minx) * kx * sc, 1), round((maxy - y) * sc, 1)] for x, y in c]
for g, geom in geoms.items():
    polys = [geom] if geom.geom_type == 'Polygon' else list(geom.geoms)
    out[g] = [ring(p.exterior.coords) for p in polys if not p.is_empty]
cities = {'San Francisco': (-122.44, 37.76), 'Oakland': (-122.22, 37.80), 'San Jose': (-121.89, 37.30), 'Santa Rosa': (-122.71, 38.44), 'Napa': (-122.29, 38.30), 'Vallejo': (-122.25, 38.11), 'Concord': (-122.03, 37.98), 'Fremont': (-121.98, 37.55), 'San Mateo': (-122.32, 37.55), 'Antioch': (-121.80, 38.00), 'Richmond': (-122.35, 37.94)}
labels = {k: [round((x - minx) * kx * sc, 1), round((maxy - y) * sc, 1)] for k, (x, y) in cities.items()}
json.dump({'w': W, 'h': round(H, 1), 'labels': labels, 'tracts': out}, open(os.path.join(RES, 'map_geometry.json'), 'w'), separators=(',', ':'))
print(len(out), 'tracts', W, round(H, 1), os.path.getsize(os.path.join(RES, 'map_geometry.json')))
