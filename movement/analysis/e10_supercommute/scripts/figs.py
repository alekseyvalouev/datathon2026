"""E10 figures -> figs/*.png (reads outputs/*.csv)."""
import os, glob
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT, FIG = os.path.join(HERE, "outputs"), os.path.join(HERE, "figs")
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # categorical slots 1-4 (dataviz reference palette)
GRAY, INK, INK2 = "#8a8985", "#0b0b0b", "#52514e"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#c9c8c3", "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": "#ecebe8", "grid.linewidth": 0.8,
                     "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.dpi": 160})


def covid(ax):
    ax.axvspan(2019.5, 2020.5, color="#ecebe8", zorder=0)
    ax.text(2020, ax.get_ylim()[1], "2020", ha="center", va="top", fontsize=8, color=INK2)


def dodge(vals, gap):
    """return label y-positions spaced at least gap apart (keeps order)"""
    order = sorted(range(len(vals)), key=lambda i: vals[i]); pos = list(vals)
    for k in range(1, len(order)):
        a, b = order[k - 1], order[k]
        if pos[b] - pos[a] < gap: pos[b] = pos[a] + gap
    return pos


def line_panel(sh, bands, labels, title, fname, col="share_outside9_ca", ylabel=None, pct=True):
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ends, labs, cols = [], [], []
    for i, (b, lab) in enumerate(zip(bands + ["S000"], labels + ["All jobs"])):
        s = sh[sh.band == b].sort_values("year")
        y = s[col] * (100 if pct else 1)
        if b == "S000": ax.plot(s.year, y, color=GRAY, lw=1.5, ls="--", label=lab)
        else: ax.plot(s.year, y, color=C[i], lw=2, marker="o", ms=4, label=lab)
        ends.append(y.iloc[-1]); labs.append(f"{lab}  {y.iloc[-1]:.1f}{'%' if pct else ''}")
        cols.append(INK2 if b == "S000" else INK)
    yr = sh.year.max(); lo, hi = ax.get_ylim()
    for yv, py, lab, c in zip(ends, dodge(ends, (hi - lo) * 0.045), labs, cols):
        ax.annotate(lab, (yr, yv), xytext=(yr + 0.4, py), va="center", fontsize=9, color=c)
    ax.set_xlim(sh.year.min() - 0.5, sh.year.max() + 4.8)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_ylabel(ylabel or "% of Bay jobs held by residents outside the 9 counties")
    ax.set_title(title, loc="left", fontsize=10, color=INK, wrap=True)
    covid(ax)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, fname)); plt.close(fig)


def main():
    os.makedirs(FIG, exist_ok=True)
    sh = pd.read_csv(os.path.join(OUT, "bay_jobs_outside_share_by_band.csv"))
    line_panel(sh, ["SE01", "SE02", "SE03"], ["<=$1,250/mo", "$1,251-3,333", ">$3,333 (nominal)"],
               "Bay jobs held by CA residents living outside the 9 counties,\nshare by monthly earnings band (LODES8 JT00, nominal bands)",
               "fig1_share_outside_by_earnings.png")
    line_panel(sh, ["SA01", "SA02", "SA03"], ["Age <=29", "Age 30-54", "Age 55+"],
               "Bay jobs held by CA residents living outside the 9 counties,\nshare by age band (LODES8 JT00)",
               "fig2_share_outside_by_age.png")
    # index of counts
    sh2 = sh.copy()
    base = sh2[sh2.year == sh2.year.min()].set_index("band")
    sh2["idx_outside"] = sh2.apply(lambda r: 100 * r.outside9_ca / base.loc[r.band, "outside9_ca"], axis=1)
    line_panel(sh2, ["SE01", "SE02", "SE03"], ["<=$1,250/mo", "$1,251-3,333", ">$3,333 (nominal)"],
               "Bay jobs held by outside-9 CA residents, count index (2010 = 100),\nby nominal earnings band (the $3,333 line is not inflation-adjusted)",
               "fig3_outside_count_index_by_earnings.png", col="idx_outside",
               ylabel="Index, 2010 = 100", pct=False)

    # top pairs
    tp = sorted(glob.glob(os.path.join(OUT, "top_pairs_*.csv")))[-1]
    yl = int(tp[-8:-4]); t = pd.read_csv(tp).head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 5.6))
    lab = t.h_name + " -> " + t.w_name
    ax.barh(lab, t.S000 / 1000, color=C[0], height=0.7)
    ax.scatter(t.S000_2010 / 1000, lab, color=INK, s=18, zorder=3, label="2010")
    for i, (v, mi) in enumerate(zip(t.S000, t.miles_oneway)):
        ax.text(v / 1000 + 0.4, i, f"{v/1000:.1f}k  ({mi:.0f} mi)", va="center", fontsize=8, color=INK2)
    ax.set_xlabel(f"Bay jobs held by residents of origin county, thousands ({yl}; dot = 2010)")
    ax.set_title(f"Top 15 outside-9 origin -> Bay workplace county pairs, {yl}\n(one-way driving miles between "
                 "county population centers, OSRM)", loc="left", fontsize=11, color=INK)
    ax.grid(axis="y", visible=False); ax.set_xlim(0, t.S000.max() / 1000 * 1.3)
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig4_top_pairs.png")); plt.close(fig)

    # ledger with commute
    p = os.path.join(OUT, "ledger_with_commute.csv")
    if os.path.exists(p):
        L = pd.read_csv(p); L = L[L.beds == 1]
        occs = ["caregiver", "cashier", "janitor", "warehouse", "cna", "med_asst"]
        fig, axes = plt.subplots(1, 2, figsize=(11, 5.6), sharey=True, sharex=True)
        for ax, m in zip(axes, ["Sacramento", "Stockton"]):
            d = L[(L.dest_metro == m) & L.occ.isin(occs)].set_index("occ").loc[occs[::-1]]
            series = [("rerent_bay_residual", "Re-rent in Bay"),
                      ("move_local_wage_residual", f"Move to {m}, local wage"),
                      ("keep_bay_job_residual_fuel", f"Live in {m}, keep Bay job (fuel only)"),
                      ("keep_bay_job_residual_irs", f"Live in {m}, keep Bay job (IRS full cost)")]
            h = 0.2
            for i, (c, lab) in enumerate(series):
                ax.barh([k + (i - 1.5) * h for k in range(len(d))], d[c], height=h * 0.9, color=C[i], label=lab)
            ax.axvline(0, color=INK, lw=0.8)
            ax.set_yticks(range(len(d))); ax.set_yticklabels(d.occupation)
            ax.set_title(m, loc="left", color=INK)
            ax.set_xlabel("$ left per month after rent (and commute)")
            ax.grid(axis="y", visible=False)
        hs, ls_ = axes[0].get_legend_handles_labels()
        ls_ = [l.replace("Sacramento", "inland metro") for l in ls_]
        fig.legend(hs[::-1], ls_[::-1], frameon=False, fontsize=8.5, loc="lower center", ncol=2)
        fig.subplots_adjust(bottom=0.2)
        fig.suptitle("Keeping the Bay job from inland: rent savings vs. commute cost\n"
                     "1-BR, Bay OEWS median wage; 250 commute days/yr; LODES-weighted county-to-county drive", x=0.01, ha="left", color=INK)
        fig.tight_layout(rect=(0, 0.1, 1, 1)); fig.savefig(os.path.join(FIG, "fig5_ledger_with_commute.png")); plt.close(fig)
    # distance bands
    db = pd.read_csv(os.path.join(OUT, "bay_jobs_by_distance_band.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
    bands = ["Outside 9, <=60 mi", "Outside 9, 60-120 mi", "Outside 9, >120 mi (not daily-commutable)"]
    for ax, (cols, ttl) in zip(axes, [(["SE01", "SE02"], "Earning <= $3,333/mo (SE01+SE02)"),
                                       (["SE03"], "Earning > $3,333/mo (SE03, nominal)")]):
        for i, b in enumerate(bands):
            d = db[db.dist_band == b].sort_values("year")
            den = db[db.dist_band != "Out of state"].groupby("year")[cols].sum().sum(axis=1)
            y = 100 * d[cols].sum(axis=1).values / den.loc[d.year].values
            ax.plot(d.year, y, color=C[i], lw=2, marker="o", ms=4, label=b)
            ax.annotate(f"{y[-1]:.1f}%", (d.year.iloc[-1], y[-1]), xytext=(5, 0), textcoords="offset points",
                        va="center", fontsize=9, color=INK)
        ax.set_title(ttl, loc="left", color=INK, fontsize=10); ax.set_xlim(2009.5, 2025.8)
        covid(ax)
    axes[0].set_ylabel("% of Bay jobs in band held by CA residents")
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Bay jobs held by residents outside the 9 counties, by one-way drive distance (OSRM, county "
                 "population centers)", x=0.01, ha="left", color=INK)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig6_distance_bands.png")); plt.close(fig)
    print("figs done")


if __name__ == "__main__":
    main()
