"""Step 10: three neighbourhoods (ZIP codes) that are in reach today and that the model projects out of reach, on a map.

Input: results/s05_unit_projections.parquet (written by s05_project.py: one row per tracked unit, its latest observed
status and the deployment LightGBM's P(leaves reach | turns over in year Y), Y = 2027..2031).

Definitions (same as the atlas page defaults: rents keep their 2026 trend, 20% of units turn over each year):
  - share out of reach in 2026 = tracked units whose latest observed re-listing left 80% AMI reach;
  - chance a still-in-reach unit is out by Y = 1 - prod_t (1 - H * p_t); already-lost units count as 1;
  - a ZIP is "in reach today" if under half of its tracked units have left reach, and "projected out of reach" if the
    expected share passes one half by 2031. ZIPs need >= MIN_N tracked units.
The three ZIPs with the highest projected 2031 share are drawn. All ZIPs are written to results/s10_neighborhoods.csv.

Network (cached under external/, only public reference data, nothing about the units is sent):
  - ZIP outlines: US Census TIGERweb, 2020 ZCTAs;
  - basemap tiles: OpenStreetMap standard tiles (c OpenStreetMap contributors), desaturated and lightened here.
Dots are drawn on ~110 m cells (coordinates rounded to 3 decimals), as on the atlas page, so no listing is pinpointed.
Writes figs/neighborhoods_leaving_reach.png."""
import os, sys, io, json, math, numpy as np, pandas as pd, requests
import matplotlib; matplotlib.use("Agg")
import matplotlib.font_manager
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon, Rectangle
from PIL import Image, ImageEnhance
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import WS, RES, FIG

H, MIN_N, YEARS = 0.20, 25, list(range(2027, 2032))
EXT = os.path.join(WS, "external"); TILES = os.path.join(EXT, "tiles"); os.makedirs(TILES, exist_ok=True)
NAMES = {"94103": "SoMa, San Francisco", "95014": "Cupertino", "94404": "Foster City", "95134": "North San José",
         "94025": "Menlo Park", "94063": "Redwood City", "94089": "Sunnyvale (Moffett Park)", "95054": "Santa Clara (north)",
         "94108": "Chinatown / Nob Hill, San Francisco", "94109": "Polk Gulch / Nob Hill, San Francisco"}
INK, MUTED, PAPER, OUT = "#1C1D21", "#6B6862", "#F6F4F0", "#8B3A2B"   # deck palette: ink, warm grey, paper, rust
GREY, TRACK, RULE = "#A8A096", "#E6E2DB", "#CFCAC2"
CMAP = LinearSegmentedColormap.from_list("reach", ["#D3CDC4", "#BC8A7A", OUT])

# ---------------------------------------------------------------- roll-up
def rollup():
    u = pd.read_parquet(os.path.join(RES, "s05_unit_projections.parquet"))
    u["zipcode"] = u.zipcode.astype(str)
    for scen in ("trend", "frozen"):
        surv = np.ones(len(u))
        for Y in YEARS:
            surv = surv * (1 - H * u[f"p_{scen}_{Y}"].fillna(0))
            u[f"out_{scen}_{Y}"] = np.where(u.y == 1, 1.0, 1 - surv)
    agg = dict(n=("y", "size"), city=("city", lambda s: s.mode()[0]), county=("county", "first"),
               median_rent=("next_last", "median"), out_2026=("y", "mean"))
    for scen in ("trend", "frozen"):
        for Y in YEARS: agg[f"out_{scen}_{Y}"] = (f"out_{scen}_{Y}", "mean")
    g = u.groupby("zipcode").agg(**agg)
    g["eligible"] = (g.n >= MIN_N) & (g.out_2026 < 0.5)
    g["crosses"] = g.eligible & (g.out_trend_2031 > 0.5)
    g["cross_year"] = [next((Y for Y in YEARS if r[f"out_trend_{Y}"] > 0.5), 0) if r.crosses else 0 for _, r in g.iterrows()]
    g = g.sort_values(["crosses", "out_trend_2031"], ascending=False)
    g["selected"] = False; g.loc[g.index[:3], "selected"] = True
    g.round(4).to_csv(os.path.join(RES, "s10_neighborhoods.csv"))
    return u, g

# ---------------------------------------------------------------- geography helpers (web mercator, world units 0..1)
def wx(lon): return (np.asarray(lon, float) + 180) / 360
def wy(lat): return (1 - np.arcsinh(np.tan(np.radians(np.asarray(lat, float)))) / math.pi) / 2

def zcta(zips):
    path = os.path.join(EXT, "zcta_selected.json")
    if os.path.exists(path):
        d = json.load(open(path))
        if set(zips) <= {f["properties"]["ZCTA5"] for f in d["features"]}: return d
    r = requests.get("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/2/query",
                     params=dict(where="ZCTA5 IN (%s)" % ",".join(f"'{z}'" for z in zips), outFields="ZCTA5", outSR=4326,
                                 f="geojson"), timeout=60)
    r.raise_for_status(); d = r.json(); json.dump(d, open(path, "w")); return d

def rings(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return [np.array(p[0]) for p in polys]

def basemap(ax, x0, x1, y0, y1, px):
    """Draw muted OpenStreetMap tiles covering the world-unit box; px = target width in pixels."""
    z = int(np.clip(round(math.log2(px / (256 * (x1 - x0))) - 0.35), 3, 17)); n = 2 ** z
    tx0, tx1, ty0, ty1 = int(x0 * n), int(x1 * n), int(y0 * n), int(y1 * n)
    canvas = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256), PAPER)
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            f = os.path.join(TILES, f"osm_{z}_{tx}_{ty}.png")
            if not os.path.exists(f):
                r = requests.get(f"https://tile.openstreetmap.org/{z}/{tx}/{ty}.png",
                                 headers={"User-Agent": "static-map-figure/1.0"}, timeout=30)
                r.raise_for_status(); open(f, "wb").write(r.content)
            canvas.paste(Image.open(f).convert("RGB"), ((tx - tx0) * 256, (ty - ty0) * 256))
    canvas = ImageEnhance.Color(canvas).enhance(0.0)                       # greyscale, then tint toward the paper colour
    canvas = Image.blend(canvas, Image.new("RGB", canvas.size, "#F3EEE6"), 0.45)
    ax.imshow(canvas, extent=(tx0 / n, (tx1 + 1) / n, (ty1 + 1) / n, ty0 / n), interpolation="lanczos", zorder=0)
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color(RULE); s.set_linewidth(0.8)

def fit_box(xs, ys, aspect, pad=0.12):
    """Smallest box around the points with the given width/height ratio."""
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    w, h = (xs.max() - xs.min()) * (1 + 2 * pad), (ys.max() - ys.min()) * (1 + 2 * pad)
    if w / h < aspect: w = h * aspect
    else: h = w / aspect
    return cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2

# ---------------------------------------------------------------- figure
def main():
    u, g = rollup()
    sel = g[g.selected]
    cols = ["n", "city", "out_2026", "out_trend_2031", "out_frozen_2031", "cross_year", "selected"]
    print(g[g.crosses][cols].round(3).to_string())
    print("eligible ZIPs:", int(g.eligible.sum()), "| cross under trend:", int(g.crosses.sum()),
          "| cross under frozen too:", int((g.crosses & (g.out_frozen_2031 > 0.5)).sum()))
    shapes = {f["properties"]["ZCTA5"]: rings(f["geometry"]) for f in zcta(list(sel.index))["features"]}

    for w in ("Medium", "Bold"):               # Figtree (SIL OFL), static weights from github.com/erikdkennedy/figtree
        fp = os.path.join(EXT, "fonts", f"Figtree-{w}.ttf")
        if not os.path.exists(fp):
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            r = requests.get(f"https://github.com/erikdkennedy/figtree/raw/master/fonts/ttf/Figtree-{w}.ttf", timeout=60)
            r.raise_for_status(); open(fp, "wb").write(r.content)
        matplotlib.font_manager.fontManager.addfont(fp)
    plt.rcParams.update({"font.family": ["Figtree", "Arial", "DejaVu Sans"]})
    fig = plt.figure(figsize=(16, 9), dpi=200, facecolor=PAPER)
    # overview
    W, Hh = 16, 9
    oa = fig.add_axes([0.035, 0.05, 0.27, 0.65])     # top ~28% of the slide is left empty for a title
    asp = (0.27 * W) / (0.65 * Hh)
    allx = np.concatenate([wx(r[:, 0]) for z in sel.index for r in shapes[z]])
    ally = np.concatenate([wy(r[:, 1]) for z in sel.index for r in shapes[z]])
    box = fit_box(allx, ally, asp, pad=0.10)
    basemap(oa, *box, px=0.27 * W * 200)
    offs = {"94103": (0.60, 0.90), "94404": (0.72, 0.60), "95014": (0.26, 0.22)}   # label anchor, axes fraction
    for i, z in enumerate(sel.index):
        for r in shapes[z]:
            oa.add_patch(Polygon(np.c_[wx(r[:, 0]), wy(r[:, 1])], closed=True, fc=OUT, ec=OUT, alpha=0.30, lw=0, zorder=3))
            oa.add_patch(Polygon(np.c_[wx(r[:, 0]), wy(r[:, 1])], closed=True, fc="none", ec=OUT, lw=1.6, zorder=4))
        big = max(shapes[z], key=len); cx, cy = wx(big[:, 0]).mean(), wy(big[:, 1]).mean()
        ax_, ay_ = offs.get(z, (0.15, 0.9 - 0.3 * i))
        oa.annotate(f"{i + 1}.  {NAMES.get(z, sel.city[z])}", xy=(cx, cy), xytext=(ax_, ay_), textcoords="axes fraction",
                    fontsize=11.5, fontweight="bold", color=INK, ha="center", va="center", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.35", fc=PAPER, ec=RULE, lw=0.8),
                    arrowprops=dict(arrowstyle="-", color=INK, lw=0.9, shrinkB=2))

    # three zooms
    left, gap, pw = 0.335, 0.016, 0.2045
    ph, TOP = 0.36, 0.70
    for i, z in enumerate(sel.index):
        r_ = sel.loc[z]; x0 = left + i * (pw + gap)
        ax = fig.add_axes([x0, TOP - ph, pw, ph])
        xs = np.concatenate([wx(r[:, 0]) for r in shapes[z]]); ys = np.concatenate([wy(r[:, 1]) for r in shapes[z]])
        bx = fit_box(xs, ys, (pw * W) / (ph * Hh), pad=0.07)
        basemap(ax, *bx, px=pw * W * 200)
        for r in shapes[z]:
            ax.add_patch(Polygon(np.c_[wx(r[:, 0]), wy(r[:, 1])], closed=True, fc=OUT, alpha=0.06, lw=0, zorder=2))
            ax.add_patch(Polygon(np.c_[wx(r[:, 0]), wy(r[:, 1])], closed=True, fc="none", ec=OUT, lw=1.5, zorder=3))
        d = u[u.zipcode == z].assign(clon=lambda t: t.lon.round(3), clat=lambda t: t.lat.round(3))
        c = d.groupby(["clon", "clat"]).agg(k=("y", "size"), p=("out_trend_2031", "mean")).reset_index().sort_values("p")
        ax.scatter(wx(c.clon), wy(c.clat), s=16 + 15 * np.sqrt(c.k), c=c.p, cmap=CMAP, vmin=0, vmax=1,
                   edgecolors="white", linewidths=0.7, zorder=5)
        # caption block
        ty = TOP - ph - 0.04
        fig.text(x0, ty, f"{i + 1}.  {NAMES.get(z, r_.city)}", fontsize=16, fontweight="bold", color=INK, va="center")
        ba = fig.add_axes([x0, ty - 0.140, pw, 0.105]); ba.set_xlim(0, 1); ba.set_ylim(-0.6, 1.6); ba.axis("off")
        for row, (lab, v, col) in enumerate([("2026, observed", r_.out_2026, GREY), ("2031, projected", r_.out_trend_2031, OUT)]):
            yb = 1 - row
            ba.add_patch(Rectangle((0.36, yb - 0.26), 0.52, 0.52, fc=TRACK, lw=0))
            ba.add_patch(Rectangle((0.36, yb - 0.26), 0.52 * v, 0.52, fc=col, lw=0))
            ba.text(0, yb, lab, fontsize=11, color=INK, va="center")
            ba.text(1.0, yb, f"{v:.0%}", fontsize=13, fontweight="bold", color=INK, va="center", ha="right")
        ba.plot([0.62, 0.62], [-0.42, 1.42], color=INK, lw=0.9)
        fig.text(x0 + pw * 0.62, ty - 0.155, "half", fontsize=9.5, color=MUTED, ha="center", va="center")

    # legend for dots
    full = 3 * pw + 2 * gap
    ca = fig.add_axes([left, 0.082, 0.30, 0.022])
    ca.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", cmap=CMAP, extent=(0, 1, 0, 1)); ca.set_yticks([])
    ca.set_xticks([0, 0.5, 1]); ca.set_xticklabels(["0%", "50%", "100% (already out)"], fontsize=11, color=MUTED)
    for t, ha in zip(ca.get_xticklabels(), ("left", "center", "right")): t.set_ha(ha)
    ca.tick_params(length=3, color=MUTED, pad=4)
    for s in ca.spines.values(): s.set_visible(False)
    fig.text(left + 0.318, 0.093, "Chance out of reach by 2031 (larger dot = more units)", fontsize=12, color=INK, va="center")
    fig.text(0.981, 0.045, "© OpenStreetMap contributors", fontsize=7, color=GREY, va="center", ha="right")
    out = os.path.join(FIG, "neighborhoods_leaving_reach.png")
    fig.savefig(out, facecolor=PAPER); print("wrote", out)

if __name__ == "__main__":
    main()
