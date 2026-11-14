"""Figures for E1. Usage: python3 -I scripts/figures.py <out_dir> <figs_dir>"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT, FIGS = Path(sys.argv[1]), Path(sys.argv[2])
FIGS.mkdir(parents=True, exist_ok=True)
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.facecolor": "white"})

g = pd.read_csv(OUT / "groups_by_unit_year.csv")

# (a) region means over time
r = g[g.unit.str.startswith("Bay")].sort_values("ty")
fig, ax = plt.subplots(figsize=(8, 4.6))
for col, lab, c in [("mean_stay", "Stayers (non-migrants)", C1), ("mean_out", "Out-movers (leave 9-county region)", C2),
                    ("mean_in", "In-movers (arrive from outside region)", C3)]:
    ax.plot(r.ty, r[col] / 1000, color=c, lw=2, marker="o", ms=5, label=lab)
    ax.annotate(f"${r[col].iloc[-2]/1000:,.0f}k", (r.ty.iloc[-2], r[col].iloc[-2] / 1000), xytext=(-4, 6),
                textcoords="offset points", ha="right", color=INK, fontsize=8)
ax.axvspan(2021.5, 2022.5, color=GRID, alpha=0.6, lw=0)
ax.text(2022, ax.get_ylim()[1] * 0.97, "IRS method\nchange", ha="center", va="top", fontsize=8, color=MUTED)
ax.set_ylabel("Mean AGI per return ($ thousands, nominal)")
ax.set_xlabel("Tax year of AGI (year-2 return of each IRS file)")
ax.grid(axis="y", color=GRID, lw=0.8)
ax.legend(frameon=False, loc="upper left")
ax.set_title("Bay Area 9-county region: mean AGI per return by migration status", loc="left", color=INK)
fig.tight_layout(); fig.savefig(FIGS / "a_region_means_by_status.png", dpi=150); plt.close(fig)

# (b) decomposition by county, TY2011 -> TY2021
p = pd.read_csv(OUT / "decomposition_period.csv")
p = p[p.period == "TY2011->TY2021"].copy()
p["order"] = p.unit.str.startswith("Bay")
p = p.sort_values(["order", "change"])
fig, ax = plt.subplots(figsize=(8.5, 5))
y = range(len(p))
h = 0.26
for k, (col, lab, c) in enumerate([("people", "People effect (same residents, income growth)", C1),
                                   ("exit", "Exit effect (out-movers removed)", C2),
                                   ("entry", "Entry effect (in-movers added)", C3)]):
    ax.barh([i + (k - 1) * h for i in y], p[col] / 1000, height=h - 0.03, color=c, label=lab)
for i, (_, row) in zip(y, p.iterrows()):
    ax.text(max(row.people, 0) / 1000 + 3, i - h, f"composition {row.composition_share_pct:+.1f}% of change",
            va="center", fontsize=7.5, color=MUTED)
ax.set_yticks(list(y)); ax.set_yticklabels(p.unit)
ax.axvline(0, color=MUTED, lw=0.8)
ax.set_xlabel("Contribution to change in mean AGI per return, TY2011 to TY2021 ($ thousands, nominal)")
ax.grid(axis="x", color=GRID, lw=0.8)
ax.legend(frameon=False, loc="lower right", fontsize=8)
ax.set_title("Most of the rise is people getting richer; leavers push the mean up, arrivals pull it down",
             loc="left", fontsize=10, color=INK)
ax.set_xlim(right=p.people.max() / 1000 * 1.45)
fig.tight_layout(); fig.savefig(FIGS / "b_decomposition_by_county.png", dpi=150); plt.close(fig)

# (c) top destinations, pooled files 2011-12..2021-22
t = pd.read_csv(OUT / "destinations_county.csv")
t = t[t.period.str.startswith("files")]
CV = {67, 77, 99, 47, 19}
fig, axes = plt.subplots(1, 3, figsize=(13, 5.2), sharex=False)
for ax, o in zip(axes, ["San Francisco", "Santa Clara", "Alameda"]):
    d = t[t.origin == o].sort_values("n1", ascending=False).head(12).iloc[::-1]
    stay = d.mean_stay.iloc[0] / 1000
    colors = [C2 if (s == 6 and c in CV) else (C3 if s != 6 else C1) for s, c in zip(d.os, d.oc)]
    ax.barh(range(len(d)), d.agi_per_return / 1000, color=colors, height=0.7)
    ax.axvline(stay, color=INK, lw=1, ls="--")
    ax.text(stay, len(d) - 0.3, f" stayers ${stay:,.0f}k", fontsize=8, color=INK, va="bottom")
    labels = [f"{n.replace(' County','')}, {s}  ({r/1000:,.0f}k ret.)" for n, s, r in zip(d.oname, d.ost, d.n1)]
    ax.set_yticks(range(len(d))); ax.set_yticklabels(labels, fontsize=8)
    ax.set_title(f"From {o}", loc="left", color=INK)
    ax.set_xlabel("Out-movers' mean AGI per return ($k)")
    ax.grid(axis="x", color=GRID, lw=0.8)
from matplotlib.patches import Patch
fig.legend(handles=[Patch(color=C1, label="Other California county"), Patch(color=C2, label="Central Valley (Sac, SJ, Stan, Merced, Fresno)"),
                    Patch(color=C3, label="Out of state")], loc="lower center", ncol=3, frameon=False)
fig.suptitle("Top 12 destination counties of out-movers (by returns), pooled IRS files 2011-12 to 2021-22; AGI is year-2 (after move)",
             x=0.01, ha="left", fontsize=10, color=INK)
fig.tight_layout(rect=(0, 0.05, 1, 0.95)); fig.savefig(FIGS / "c_top_destinations.png", dpi=150); plt.close(fig)
print("figs done")
