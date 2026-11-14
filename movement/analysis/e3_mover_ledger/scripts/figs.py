"""Step 4: figures in ../figs/."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "outputs")
FIG = os.path.join(HERE, "..", "figs")
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3de"
C = {"Stay (in-place)": "#2a78d6", "Re-rent in Bay (turnover)": "#eb6834", "CA inland": "#1baf7a", "Out of state": "#eda100"}
MK = {"Stay (in-place)": "o", "Re-rent in Bay (turnover)": "D", "CA inland": "s", "Out of state": "^"}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False})


def cat(row):
    if row.group == "Bay":
        return row.scenario if not row.scenario.startswith("Stay +1y") else None
    return row.group


def dotplot(L, beds, src, origin, fname, metric="residual"):
    d = L[(L.beds == beds) & (L.wage_source == src) & (L.origin == origin)].copy()
    d["cat"] = d.apply(cat, axis=1)
    d = d[d.cat.notna()]
    order = d[d.cat == "Stay (in-place)"].sort_values(metric).occupation.tolist()
    y = {o: i for i, o in enumerate(order)}
    fig, ax = plt.subplots(figsize=(8.2, 0.42 * len(order) + 1.6))
    off = {"Stay (in-place)": 0.18, "Re-rent in Bay (turnover)": 0.06, "CA inland": -0.06, "Out of state": -0.18}
    for c in C:
        q = d[d.cat == c]
        v = q[metric] * (100 if metric == "rent_burden" else 1)
        ax.scatter(v, q.occupation.map(y) + off[c], s=34, marker=MK[c], color=C[c], edgecolor="white", linewidth=0.8,
                   label=c + (" (4 metros)" if c == "CA inland" else " (7 metros)" if c == "Out of state" else ""), zorder=3)
    for o in order:
        q = d[d.occupation == o][metric] * (100 if metric == "rent_burden" else 1)
        ax.plot([q.min(), q.max()], [y[o]] * 2, color=GRID, lw=1.2, zorder=1)
    if metric == "residual":
        ax.axvline(0, color=MUTED, lw=1)
        ax.set_xlabel("Residual income after rent, $/month (full-time gross wage − rent)")
    else:
        ax.axvline(30, color=MUTED, lw=1, ls="--"); ax.text(30.5, -0.9, "30% burden line", color=MUTED, fontsize=8)
        ax.axvline(50, color=MUTED, lw=1, ls=":"); ax.text(50.5, -0.9, "50% severe", color=MUTED, fontsize=8)
        ax.set_xlabel("Rent as % of full-time gross wage")
    ax.set_yticks(range(len(order))); ax.set_yticklabels(order)
    ax.set_ylim(-1.2, len(order) - 0.4)
    ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    t = "1-BR, single worker" if beds == 1 else "2-BR, one earner (family version)"
    ax.set_title(f"The mover's ledger — {origin} origin, {t}\nWages: {src}, 173 h/mo; destination rents: ZORI × Bay bedroom factor",
                 loc="left", fontsize=10, color=INK)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13 if metric == "residual" else -0.13), ncol=2, frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, fname), dpi=160)
    plt.close(fig)


def wage_compare():
    iw = pd.read_csv(os.path.join(OUT, "indeed_wages_by_occ_metro.csv"))
    L = pd.read_csv(os.path.join(OUT, "ledger_long.csv"))
    o = L[(L.wage_source == "OEWS median") & (L.beds == 1) & (L.origin == "Bay Area")]
    o = o[o.scenario.isin(["Stay (in-place)", "Sacramento", "Stockton", "Modesto", "Fresno"])][["occ", "occupation", "scenario", "hourly"]]
    o["metro"] = o.scenario.replace({"Stay (in-place)": "Bay Area"})
    m = o.merge(iw[["occ", "metro", "n_pay", "med_mid"]], on=["occ", "metro"])
    m = m[m.n_pay >= 15]
    m.to_csv(os.path.join(OUT, "wage_indeed_vs_oews.csv"), index=False)
    fig, ax = plt.subplots(figsize=(5.4, 5))
    cols = {"Bay Area": "#2a78d6", "Sacramento": "#eb6834", "Stockton": "#1baf7a", "Modesto": "#e87ba4", "Fresno": "#eda100"}
    for k, q in m.groupby("metro"):
        ax.scatter(q.hourly, q.med_mid, s=36, color=cols[k], edgecolor="white", label=f"{k} (n={len(q)} occs)", zorder=3)
    lo, hi = 15, 32
    ax.plot([lo, hi], [lo, hi], color=MUTED, lw=1, ls="--"); ax.text(hi - 4, hi - 1.2, "y = x", color=MUTED)
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    ax.set_xlabel("BLS OEWS May-2025 median hourly wage ($)"); ax.set_ylabel("Indeed posted median hourly (mid of range, $)")
    ax.set_title("Posted vs. surveyed wages, occupation × CA metro\n(cells with ≥15 Indeed postings with pay)", loc="left", fontsize=10)
    ax.grid(color=GRID, lw=0.6); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig4_indeed_vs_oews_wages.png"), dpi=160); plt.close(fig)


def model_fig():
    s = pd.read_csv(os.path.join(OUT, "salary_model_subgroups.csv"))
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.2), gridspec_kw={"width_ratios": [1, 1.1, 0.7], "wspace": 0.75})
    names = {"area": "Region", "occ_lab": "Occupation group", "tier": "True wage tier"}
    for ax, dim in zip(axes, ["area", "occ_lab", "tier"]):
        q = s[s.dimension == dim].pivot_table(index="group", columns="model", values="MAE")
        if dim == "tier":
            q = q.reindex(["<$20", "$20-30", "$30-50", "$50+"])
        else:
            q = q.sort_values("ridge")
        yy = np.arange(len(q))
        ax.barh(yy + 0.2, q["B2"], height=0.38, color="#9ec5f4", label="Baseline B2: median by title × region")
        ax.barh(yy - 0.2, q["ridge"], height=0.38, color="#2a78d6", label="TF-IDF + location ridge")
        ax.set_yticks(yy); ax.set_yticklabels(q.index, fontsize=8); ax.set_title(names[dim], loc="left", fontsize=10)
        ax.set_xlabel("MAE, $/hour (company-held-out test)"); ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, frameon=False)
    fig.subplots_adjust(left=0.11, right=0.98, bottom=0.2, top=0.9); fig.savefig(os.path.join(FIG, "fig5_salary_model_subgroup_mae.png"), dpi=160); plt.close(fig)


def missing_fig():
    m = pd.read_csv(os.path.join(OUT, "pay_missing_share.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for ax, dim in zip(axes, ["area", "occupation"]):
        q = m[m.dimension == dim].sort_values("share_no_usable_hourly")
        ax.barh(q.group, 100 * q.share_no_usable_hourly, color="#2a78d6", height=0.6, label="no usable hourly pay")
        ax.barh(q.group, 100 * q.share_no_salary_text, color="#eb6834", height=0.3, label="no salary text at all")
        ax.set_xlabel("% of postings"); ax.tick_params(axis="y", labelsize=8); ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    axes[0].set_title("Postings lacking pay, by region", loc="left", fontsize=10)
    axes[1].set_title("…by occupation group", loc="left", fontsize=10)
    axes[1].legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig6_missing_pay_share.png"), dpi=160); plt.close(fig)


def main():
    os.makedirs(FIG, exist_ok=True)
    L = pd.read_csv(os.path.join(OUT, "ledger_long.csv"))
    dotplot(L, 1, "OEWS median", "Bay Area", "fig1_residual_1br_oews_bay.png")
    dotplot(L, 1, "OEWS median", "Bay Area", "fig2_rentburden_1br_oews_bay.png", metric="rent_burden")
    dotplot(L, 2, "OEWS median", "Bay Area", "fig3_residual_2br_family_oews_bay.png")
    dotplot(L, 1, "OEWS median", "San Francisco", "figS1_residual_1br_oews_sf.png")
    dotplot(L, 1, "Indeed posted median", "Bay Area", "figS2_residual_1br_indeed_bay_CAonly.png")
    wage_compare()
    model_fig()
    missing_fig()


if __name__ == "__main__":
    main()
