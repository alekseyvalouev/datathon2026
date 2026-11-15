"""Step 11 (side figure, not in run_all.sh): where the model did badly on the 2026 test set, on a map.

Same model, split and threshold as s03/s09: main LightGBM refit on train+validation with the s03 settings, one regional
list flagging units above the 80th percentile of validation scores. A loss is a unit that left 80% AMI reach in 2026;
it is "missed" if the unit was not on that list.

Selection: ZIPs with at least MIN_POS losses in 2026 and a missed share above the regional one, ranked by the number of
missed losses. The top three are drawn; every ZIP is written to results/s11_missed_by_zip.csv.
Dots show losses only (false alarms are in the CSV, not on the map), on ~110 m cells as in s10.
Layout, map helpers and network sources (Census TIGERweb ZCTAs, OpenStreetMap tiles) are those of s10_neighborhoods.py;
the palette is inverted (dark ground) so this figure contrasts with that one.
Writes figs/missed_losses_map.png."""
import os, sys, json, math, textwrap, numpy as np, pandas as pd, requests
import matplotlib; matplotlib.use("Agg")
import matplotlib.font_manager
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modlib import *
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image, ImageEnhance, ImageOps
from s10_neighborhoods import wx, wy, rings, fit_box, EXT, TILES

# Dark palette of the deck's title slide, inverted from s10 so the two maps read as a pair: near-black ground,
# off-white ink, salmon for "missed".
PAPER, INK, MUTED, OUT = "#17181D", "#F6F4F0", "#A9A9B3", "#E39A82"
GREY, TRACK, RULE = "#7C7C86", "#2B2C33", "#3A3B43"
CMAP = LinearSegmentedColormap.from_list("missed", ["#565760", "#A8776A", "#F2A78E"])

def basemap(ax, x0, x1, y0, y1, px):
    """s10's basemap with the OpenStreetMap tiles inverted and sunk into the dark ground."""
    z = int(np.clip(round(math.log2(px / (256 * (x1 - x0))) - 0.35), 3, 17)); n = 2 ** z
    tx0, tx1, ty0, ty1 = int(x0 * n), int(x1 * n), int(y0 * n), int(y1 * n)
    canvas = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256), "#FFFFFF")
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            f = os.path.join(TILES, f"osm_{z}_{tx}_{ty}.png")
            if not os.path.exists(f):
                r = requests.get(f"https://tile.openstreetmap.org/{z}/{tx}/{ty}.png",
                                 headers={"User-Agent": "static-map-figure/1.0"}, timeout=30)
                r.raise_for_status(); open(f, "wb").write(r.content)
            canvas.paste(Image.open(f).convert("RGB"), ((tx - tx0) * 256, (ty - ty0) * 256))
    canvas = ImageOps.invert(ImageEnhance.Color(canvas).enhance(0.0))
    canvas = Image.blend(canvas, Image.new("RGB", canvas.size, "#1B1C22"), 0.62)
    ax.imshow(canvas, extent=(tx0 / n, (tx1 + 1) / n, (ty1 + 1) / n, ty0 / n), interpolation="lanczos", zorder=0)
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color(RULE); s.set_linewidth(0.8)

BUDGET, MIN_POS = 0.20, 15
FULL = "+ tract + city jobs (all workstreams)"
NAMES = {"94612": "Downtown Oakland", "94109": "Nob Hill / Polk Gulch, SF", "94115": "Western Addition, SF",
         "94080": "South San Francisco", "94704": "Southside Berkeley", "94133": "North Beach, SF", "94110": "Mission, SF",
         "94002": "Belmont", "94501": "Alameda", "94107": "Potrero Hill / South Beach, SF", "94103": "SoMa, SF"}
OFFS = {"94612": (0.66, 0.92), "94109": (0.30, 0.80), "94115": (0.30, 0.20)}   # overview label anchors, axes fraction

def scored_test():
    df, hist = load()
    tr, va, te = (df[df.split == s].copy() for s in ("train", "val", "test"))
    trva = df[df.split.isin(["train", "val"])].copy()
    tr_e, (va_e,) = add_encodings(tr, [va], hist, TRAIN_END)
    trva_e, (te_e,) = add_encodings(trva, [te], hist, VAL_END)
    p, n = json.load(open(os.path.join(RES, "s03_config.json")))["lgb_params"][FULL]
    thr = np.quantile(fit_lgb(tr_e[ALL], tr_e.y, p, n).predict_proba(va_e[ALL])[:, 1], 1 - BUDGET)
    te_e["score"] = fit_lgb(trva_e[ALL], trva_e.y, p, n).predict_proba(te_e[ALL])[:, 1]
    te_e["flag"] = (te_e.score >= thr).astype(int); te_e["zipcode"] = te_e.zipcode.astype(str)
    te_e["missed"] = ((te_e.y == 1) & (te_e.flag == 0)).astype(int); te_e["caught"] = ((te_e.y == 1) & (te_e.flag == 1)).astype(int)
    te_e["false_alarm"] = ((te_e.y == 0) & (te_e.flag == 1)).astype(int)
    return te_e, df

def zcta(zips):
    path = os.path.join(EXT, "zcta_s11.json")
    if os.path.exists(path):
        d = json.load(open(path))
        if set(zips) <= {f["properties"]["ZCTA5"] for f in d["features"]}: return d
    r = requests.get("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/2/query",
                     params=dict(where="ZCTA5 IN (%s)" % ",".join(f"'{z}'" for z in zips), outFields="ZCTA5", outSR=4326,
                                 f="geojson"), timeout=60)
    r.raise_for_status(); d = r.json(); json.dump(d, open(path, "w")); return d

def main():
    te, df = scored_test()
    # annotation numbers: low-income tracts = bottom tercile of 2018 tract median household income (as in s03/s09)
    q = np.nanquantile(df.drop_duplicates("tract").real_hinc_18, [1 / 3, 2 / 3])
    lo_t, hi_t = te[te.real_hinc_18 <= q[0]], te[te.real_hinc_18 > q[1]]
    d_lo = df[df.real_hinc_18 <= q[0]].copy()
    d_lo["fast"] = (d_lo.next_last / d_lo.last_p) ** (1 / d_lo.start_gap_y.clip(lower=0.25)) - 1 > 0.10   # above the AB 1482 maximum
    fast26, fast_before = d_lo[d_lo.split == "test"].fast.mean(), d_lo[d_lo.split != "test"].fast.mean()
    notes = [("The model under-predicts in low-income neighborhoods",
              f"In low-income tracts it expected {lo_t.score.mean():.0%} of units to leave reach in 2026; {lo_t.y.mean():.0%} did. "
              f"One regional list caught {lo_t.caught.sum() / lo_t.y.sum():.0%} of those losses, against {hi_t.caught.sum() / hi_t.y.sum():.0%} in high-income tracts."),
             ("Why: rents there jumped in 2026",
              f"In low-income tracts, {fast26:.0%} of 2026 turnovers raised the rent by more than 10% a year, up from {fast_before:.0%} "
              f"in the years the model was trained on. It had only seen the slower years.")]
    for h, b in notes: print(h, "|", b)
    reg_miss = te.missed.sum() / te.y.sum()
    g = te.groupby("zipcode").agg(n=("y", "size"), city=("city", lambda s: s.mode()[0]), county=("county", "first"), losses=("y", "sum"),
                                  missed=("missed", "sum"), caught=("caught", "sum"), false_alarms=("false_alarm", "sum"),
                                  leave_rate=("y", "mean"), mean_pred=("score", "mean"), share_apartment=("homeType", lambda s: (s == "APARTMENT").mean()),
                                  median_headroom_losses=("headroom", lambda s: s[te.loc[s.index, "y"] == 1].median()))
    g["missed_share"] = g.missed / g.losses
    g["eligible"] = (g.losses >= MIN_POS) & (g.missed_share > reg_miss)
    g = g.sort_values(["eligible", "missed"], ascending=False)
    g["selected"] = False; g.loc[g.index[:3], "selected"] = True
    g.round(3).to_csv(os.path.join(RES, "s11_missed_by_zip.csv"))
    sel = g[g.selected]
    print("region: %d of %d losses missed (%.1f%%)" % (te.missed.sum(), te.y.sum(), 100 * reg_miss))
    print(g[g.eligible].drop(columns=["county", "eligible"]).round(3).to_string())
    shapes = {f["properties"]["ZCTA5"]: rings(f["geometry"]) for f in zcta(list(sel.index))["features"]}

    for w in ("Medium", "Bold"):
        matplotlib.font_manager.fontManager.addfont(os.path.join(EXT, "fonts", f"Figtree-{w}.ttf"))   # fetched by s10
    plt.rcParams.update({"font.family": ["Figtree", "Arial", "DejaVu Sans"]})
    fig = plt.figure(figsize=(16, 9), dpi=200, facecolor=PAPER); W, Hh = 16, 9
    fig.text(0.035, 0.925, "Limitations", fontsize=30, fontweight="bold", color=INK, va="center")
    oa = fig.add_axes([0.035, 0.06, 0.27, 0.80])
    allx = np.concatenate([wx(r[:, 0]) for z in sel.index for r in shapes[z]])
    ally = np.concatenate([wy(r[:, 1]) for z in sel.index for r in shapes[z]])
    basemap(oa, *fit_box(allx, ally, (0.27 * W) / (0.80 * Hh), pad=0.14), px=0.27 * W * 200)
    for i, z in enumerate(sel.index):
        for r in shapes[z]:
            oa.add_patch(Polygon(np.c_[wx(r[:, 0]), wy(r[:, 1])], closed=True, fc=OUT, ec=OUT, alpha=0.38, lw=0, zorder=3))
            oa.add_patch(Polygon(np.c_[wx(r[:, 0]), wy(r[:, 1])], closed=True, fc="none", ec=OUT, lw=1.6, zorder=4))
        big = max(shapes[z], key=len); cx, cy = wx(big[:, 0]).mean(), wy(big[:, 1]).mean()
        oa.annotate(f"{i + 1}.  {NAMES.get(z, sel.city[z])}", xy=(cx, cy), xytext=OFFS.get(z, (0.3, 0.9 - 0.3 * i)), textcoords="axes fraction",
                    fontsize=11.5, fontweight="bold", color=INK, ha="center", va="center", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.35", fc=PAPER, ec=RULE, lw=0.8),
                    arrowprops=dict(arrowstyle="-", color=INK, lw=0.9, shrinkB=2))

    left, gap, pw, ph, TOP = 0.335, 0.016, 0.2045, 0.38, 0.86
    for i, z in enumerate(sel.index):
        r_ = sel.loc[z]; x0 = left + i * (pw + gap)
        ax = fig.add_axes([x0, TOP - ph, pw, ph])
        xs = np.concatenate([wx(r[:, 0]) for r in shapes[z]]); ys = np.concatenate([wy(r[:, 1]) for r in shapes[z]])
        basemap(ax, *fit_box(xs, ys, (pw * W) / (ph * Hh), pad=0.07), px=pw * W * 200)
        for r in shapes[z]:
            ax.add_patch(Polygon(np.c_[wx(r[:, 0]), wy(r[:, 1])], closed=True, fc=OUT, alpha=0.08, lw=0, zorder=2))
            ax.add_patch(Polygon(np.c_[wx(r[:, 0]), wy(r[:, 1])], closed=True, fc="none", ec=OUT, lw=1.5, zorder=3))
        d = te[(te.zipcode == z) & (te.y == 1)].assign(clon=lambda t: t.lon.round(3), clat=lambda t: t.lat.round(3))
        c = d.groupby(["clon", "clat"]).agg(k=("y", "size"), p=("missed", "mean")).reset_index().sort_values("p")
        ax.scatter(wx(c.clon), wy(c.clat), s=16 + 15 * np.sqrt(c.k), c=c.p, cmap=CMAP, vmin=0, vmax=1,
                   edgecolors=PAPER, linewidths=0.7, zorder=5)
        ty = TOP - ph - 0.04
        fig.text(x0, ty, f"{i + 1}.  {NAMES.get(z, r_.city)}", fontsize=16, fontweight="bold", color=INK, va="center")
        ba = fig.add_axes([x0, ty - 0.125, pw, 0.095]); ba.set_xlim(0, 1); ba.set_ylim(-0.6, 1.6); ba.axis("off")
        for row, (lab, v, col) in enumerate([("Missed, Bay Area", reg_miss, GREY), ("Missed here", r_.missed_share, OUT)]):
            yb = 1 - row
            ba.add_patch(Rectangle((0.40, yb - 0.26), 0.48, 0.52, fc=TRACK, lw=0))
            ba.add_patch(Rectangle((0.40, yb - 0.26), 0.48 * v, 0.52, fc=col, lw=0))
            ba.text(0, yb, lab, fontsize=11, color=INK, va="center")
            ba.text(1.0, yb, f"{v:.0%}", fontsize=13, fontweight="bold", color=INK, va="center", ha="right")
        fig.text(x0, ty - 0.140, f"{int(r_.missed)} of {int(r_.losses)} units that left reach were not flagged",
                 fontsize=9.5, color=MUTED, va="center")

    full = 3 * pw + 2 * gap
    ca = fig.add_axes([left, 0.232, 0.24, 0.016])
    ca.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", cmap=CMAP, extent=(0, 1, 0, 1)); ca.set_yticks([])
    ca.set_xticks([0, 0.5, 1]); ca.set_xticklabels(["all caught", "half missed", "all missed"], fontsize=9.5, color=MUTED)
    for t_, ha in zip(ca.get_xticklabels(), ("left", "center", "right")): t_.set_ha(ha)
    ca.tick_params(length=3, color=MUTED, pad=3)
    for s in ca.spines.values(): s.set_visible(False)
    fig.text(left + 0.255, 0.240, "Units that left reach in 2026: share the model missed (larger dot = more units)", fontsize=10.5, color=MUTED, va="center")
    fig.add_artist(plt.Line2D([left, left + full], [0.178, 0.178], color=RULE, lw=0.8))
    cw = (full - 0.03) / 2
    for j, (head, body) in enumerate(notes):
        xn = left + j * (cw + 0.03)
        fig.text(xn, 0.145, head, fontsize=14, fontweight="bold", color=OUT if j == 0 else INK, va="center")
        fig.text(xn, 0.118, textwrap.fill(body, 64), fontsize=11.5, color=INK, va="top", linespacing=1.45)
    fig.text(0.981, 0.03, "© OpenStreetMap contributors", fontsize=7, color=GREY, va="center", ha="right")
    out = os.path.join(FIG, "missed_losses_map.png")
    fig.savefig(out, facecolor=PAPER); print("wrote", out)

if __name__ == "__main__":
    main()
