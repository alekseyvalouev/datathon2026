"""Step 6: county outlines for the map page. Run with python3 -I (external/ holds a downloaded, untrusted zip).
Input: external/cb_2018_us_county_500k.zip (US Census cartographic boundary, clipped to the shoreline):
  https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_county_500k.zip
Output: results/viz/counties.json (9 Bay Area counties + neighbours for context, simplified, 4-decimal coords)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shapefile
from shapely.geometry import shape, mapping, box
from common import WS, RES

BAY = {"001": "Alameda", "013": "Contra Costa", "041": "Marin", "055": "Napa", "075": "San Francisco",
       "081": "San Mateo", "085": "Santa Clara", "095": "Solano", "097": "Sonoma"}
NEAR = {"077": "San Joaquin", "087": "Santa Cruz", "067": "Sacramento", "113": "Yolo", "033": "Lake",
        "045": "Mendocino", "099": "Stanislaus", "069": "San Benito", "011": "Colusa"}
CLIP = box(-123.65, 36.85, -121.15, 38.92)

def rnd(o):
    if isinstance(o, (list, tuple)):
        return [rnd(x) for x in o] if not isinstance(o[0], float) else [round(o[0], 4), round(o[1], 4)]
    return o

def main():
    r = shapefile.Reader(os.path.join(WS, "external", "cb_2018_us_county_500k.zip"))
    feats = []
    for sr in r.iterShapeRecords():
        rec = sr.record.as_dict()
        if rec["STATEFP"] != "06" or rec["COUNTYFP"] not in BAY | NEAR: continue
        g = shape(sr.shape.__geo_interface__).intersection(CLIP).simplify(0.0012, preserve_topology=True)
        if g.is_empty: continue
        feats.append(dict(type="Feature", properties=dict(name=(BAY | NEAR)[rec["COUNTYFP"]], bay=rec["COUNTYFP"] in BAY),
                          geometry=dict(type=g.geom_type, coordinates=rnd(mapping(g)["coordinates"]))))
    out = os.path.join(RES, "viz", "counties.json")
    json.dump(dict(type="FeatureCollection", features=feats), open(out, "w"), separators=(",", ":"))
    print(len(feats), "features,", os.path.getsize(out) // 1024, "KB")

if __name__ == "__main__":
    main()
