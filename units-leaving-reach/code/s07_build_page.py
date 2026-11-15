"""Step 7: inline the projection data and county outlines into the map page template.
Writes site/out-of-reach-atlas.html (self-contained apart from d3 and Google Fonts)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import WS, RES

def main():
    t = open(os.path.join(WS, "site", "template.html")).read()
    units = open(os.path.join(RES, "viz", "units.json")).read()
    geo = open(os.path.join(RES, "viz", "counties.json")).read()
    assert "/*__UNITS__*/null" in t and "/*__GEO__*/null" in t
    out = t.replace("/*__UNITS__*/null", units).replace("/*__GEO__*/null", geo)
    p = os.path.join(WS, "site", "out-of-reach-atlas.html")
    open(p, "w").write(out)
    print(p, os.path.getsize(p) // 1024, "KB")

if __name__ == "__main__":
    main()
