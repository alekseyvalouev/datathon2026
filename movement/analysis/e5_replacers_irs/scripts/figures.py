"""E5 figures. Usage: python3 -I scripts/figures.py <out_dir> <fig_dir>"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np
import pandas as pd

OUT, FIG = Path(sys.argv[1]), Path(sys.argv[2])
FIG.mkdir(parents=True, exist_ok=True)
REGION = "Bay Area (9-county region)"
BLUE, ORANGE, AQUA, GRAY, INK, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#8a8980", "#1f1f1d", "#6b6a63"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.grid": True, "grid.color": "#e1e0d9", "grid.linewidth": 0.6,
                     "figure.facecolor": "white", "axes.titleweight": "bold", "axes.titlesize": 11})

cat = pd.read_csv(OUT / "flows_by_origin_type.csv")
rr = pd.read_csv(OUT / "replacement_ratios.csv")


def shade_break(ax):
    ax.axvspan(2021.5, 2022.5, color="#f0efec", zorder=0, lw=0)
    ax.text(2022, ax.get_ylim()[1], "new IRS\nmethod", ha="center", va="top", fontsize=8, color=MUTED)


# ---- Fig 1: region in-mover origins and AGI by origin vs out-mover destination
r = cat[cat.unit == REGION]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
ax = axes[0]
ins = r[r.direction == "in"].pivot(index="ty", columns="cat", values="share_of_direction_total")
bottom = np.zeros(len(ins))
for c, col, lab in [("rest_of_CA", BLUE, "Rest of California"), ("other_states", ORANGE, "Other states"),
                    ("foreign", AQUA, "Foreign / abroad")]:
    ax.bar(ins.index, ins[c] * 100, bottom=bottom, color=col, label=lab, width=0.8, edgecolor="white", lw=1.5)
    bottom += ins[c].to_numpy() * 100
ax.set_ylim(0, 100)
ax.set_ylabel("% of in-moving returns")
ax.set_title("Where the Bay's in-movers come from (9-county region)")
ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
ax.grid(axis="x", visible=False)
ax = axes[1]
for c, col, lab in [("rest_of_CA", BLUE, "Rest of CA"), ("other_states", ORANGE, "Other states")]:
    s_in = r[(r.direction == "in") & (r.cat == c)].set_index("ty").mean_agi / 1000
    s_out = r[(r.direction == "out") & (r.cat == c)].set_index("ty").mean_agi / 1000
    ax.plot(s_out.index, s_out, color=col, lw=2, ls="--", marker="o", ms=4, label=f"Out-movers to {lab}")
    ax.plot(s_in.index, s_in, color=col, lw=2, marker="o", ms=4, label=f"In-movers from {lab}")
st = r[r.direction == "stay"].set_index("ty").mean_agi / 1000
ax.plot(st.index, st, color=GRAY, lw=2, label="Stayers")
ax.legend(fontsize=8, loc="upper left")
ax.set_ylabel("Mean AGI per return, $k (nominal, year-2)")
ax.set_title("Like-for-like geography: in-movers (solid) < out-movers (dashed)")
ax.title.set_fontsize(10)
shade_break(ax)
fig.tight_layout()
fig.savefig(FIG / "fig1_region_origins_and_agi.png", dpi=150)
plt.close(fig)

# ---- Fig 2: replacement ratio heat maps (per return vs per person), all movers
order = ["San Francisco", "Santa Clara", "San Mateo", "Alameda", "Contra Costa", "Solano", "Marin", "Sonoma", "Napa", REGION]
cmap = LinearSegmentedColormap.from_list("div", ["#c22f2f", "#f0efec", "#1f63b8"])
fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)
for ax, col, title in [(axes[0], "replacement_ratio_per_return", "Replacement ratio per RETURN: in-mover AGI / out-mover AGI"),
                       (axes[1], "replacement_ratio_per_person", "Per PERSON (AGI / n2): household size removed")]:
    m = rr[rr.cat == "domestic"].pivot(index="unit", columns="ty", values=col).loc[order]
    im = ax.imshow(m.to_numpy(), cmap=cmap, norm=TwoSlopeNorm(1.0, 0.4, 1.6), aspect="auto")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            v = m.iat[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if abs(v - 1) > 0.35 else INK)
    ax.set_xticks(range(m.shape[1]), [str(t) if t < 2022 else "2022*" for t in m.columns], rotation=45)
    ax.set_yticks(range(m.shape[0]), [u.replace(" (9-county region)", " region") for u in m.index])
    ax.set_title(title, fontsize=10)
    ax.grid(False)
fig.colorbar(im, ax=axes, shrink=0.8, label="<1: replacers report less AGI than leavers")
fig.suptitle("Domestic movers only (foreign excluded). Tax year of year-2 AGI. *2022 = new IRS method", fontsize=9, color=MUTED, y=-0.04)
fig.savefig(FIG / "fig2_replacement_ratio_heatmap.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ---- Fig 3: persons per return
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
ax = axes[0]
for d, cc, col, lab in [("stay", "stayers", GRAY, "Stayers"), ("out", "all", ORANGE, "Out-movers"), ("in", "all", BLUE, "In-movers")]:
    s = r[(r.direction == d) & (r.cat == cc)].set_index("ty").persons_per_return
    ax.plot(s.index, s, color=col, lw=2, marker="o", ms=4)
    ax.annotate(lab, (s.index[0], s.iloc[0]), xytext=(0, 6), textcoords="offset points", fontsize=8, color=INK)
ax.axvline(2018.5, color=MUTED, lw=1, ls=":")
ax.text(2018.6, 2.15, "n2 = exemptions | n2 = individuals", fontsize=7.5, color=MUTED, ha="center")
ax.set_ylabel("Persons per return (n2 / n1)")
ax.set_title("Bay region: replacers are smaller households")
shade_break(ax)
ax = axes[1]
t = rr[(rr.ty == 2021) & (rr.cat == "all")].set_index("unit").loc[order]
y = np.arange(len(t))
ax.barh(y + 0.27, t.ppr_stay, height=0.26, color=GRAY, label="Stayers")
ax.barh(y, t.persons_per_return_out, height=0.26, color=ORANGE, label="Out-movers")
ax.barh(y - 0.27, t.persons_per_return_in, height=0.26, color=BLUE, label="In-movers")
ax.set_yticks(y, [u.replace(" (9-county region)", " region") for u in t.index])
ax.invert_yaxis()
ax.set_xlim(1, 2.4)
ax.set_xlabel("Persons per return, TY2021")
ax.legend(fontsize=8, loc="lower right")
ax.grid(axis="y", visible=False)
ax.set_title("By county, TY2021")
fig.tight_layout()
fig.savefig(FIG / "fig3_persons_per_return.png", dpi=150)
plt.close(fig)

# ---- Fig 4: California (statewide) age profile of in- vs out-migrants
a = pd.read_csv(OUT / "ca_age_profile.csv")
s = pd.read_csv(OUT / "ca_in_vs_out_age_standardised.csv")
ages = ["<26", "26-34", "35-44", "45-54", "55-64", "65+"]
fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
a21 = a[(a.ty == 2021)].set_index(["group", "age"])
x = np.arange(len(ages))
for k, (g, col, lab) in enumerate([("nonmig", GRAY, "Non-migrants"), ("outflow", ORANGE, "Out-migrants (CA → other state)"),
                                   ("inflow", BLUE, "In-migrants (other state → CA)")]):
    axes[0].bar(x + (k - 1) * 0.27, [a21.loc[(g, ag), "share_of_group"] * 100 for ag in ages], width=0.26, color=col, label=lab)
    axes[1].plot(x, [a21.loc[(g, ag), "mean_y2_agi"] / 1000 for ag in ages], color=col, lw=2, marker="o", ms=5, label=lab)
axes[0].set_xticks(x, ages); axes[0].set_ylabel("% of returns"); axes[0].set_xlabel("Age of primary taxpayer")
axes[0].set_title("California TY2021: in-migrants are younger"); axes[0].legend(fontsize=8); axes[0].grid(axis="x", visible=False)
axes[1].set_xticks(x, ages); axes[1].set_ylabel("Mean year-2 AGI, $k"); axes[1].set_xlabel("Age of primary taxpayer")
axes[1].set_title("Same age → near-identical AGI under 35")
ax = axes[2]
ax.plot(s.ty, s.ratio_raw, color=BLUE, lw=2, marker="o", ms=4, label="Raw in/out AGI ratio")
ax.plot(s.ty, s.ratio_age_standardised, color=AQUA, lw=2, marker="o", ms=4, label="In-migrants reweighted to out-migrant ages")
ax.axhline(1, color=MUTED, lw=1)
ax.set_ylabel("In-migrant / out-migrant mean AGI"); ax.legend(fontsize=8, loc="lower left")
ax.set_title("Age explains part of the gap (statewide)")
shade_break(ax)
fig.tight_layout()
fig.savefig(FIG / "fig4_ca_age_profile.png", dpi=150)
plt.close(fig)
print("figures done")
