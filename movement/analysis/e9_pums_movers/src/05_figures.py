"""Figures for E9 (static PNGs in figs/)."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, precision_recall_curve

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA, OUT, FIG = (os.path.join(BASE, x) for x in ("data", "outputs", "figs"))
os.makedirs(FIG, exist_ok=True)

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # validated categorical order (dataviz default palette)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
                     "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6})

LABEL = {"own": "Owns home", "renter": "Rents", "rent_burden30": "Rent burden >=30% (renters)",
         "rent_burden50": "Rent burden >=50% (renters)", "overcrowded": "Overcrowded (>1 person/room)",
         "commute60": "Commute >=60 min (commuters)", "wfh": "Works from home (workers)",
         "employed": "Employed", "below_200pov": "Below 200% poverty"}
BIN_OUT = list(LABEL)
TLAB = {"left_ca": "Left California", "left_saccv": "Sacramento / Central Valley", "left_othca": "Other California",
        "left_any": "Any leaver"}
FIPS = {1: "AL", 2: "AK", 4: "AZ", 5: "AR", 8: "CO", 9: "CT", 10: "DE", 11: "DC", 12: "FL", 13: "GA", 15: "HI",
        16: "ID", 17: "IL", 18: "IN", 19: "IA", 20: "KS", 21: "KY", 22: "LA", 23: "ME", 24: "MD", 25: "MA", 26: "MI",
        27: "MN", 28: "MS", 29: "MO", 30: "MT", 31: "NE", 32: "NV", 33: "NH", 34: "NJ", 35: "NM", 36: "NY", 37: "NC",
        38: "ND", 39: "OH", 40: "OK", 41: "OR", 42: "PA", 44: "RI", 45: "SC", 46: "SD", 47: "TN", 48: "TX", 49: "UT",
        50: "VT", 51: "VA", 53: "WA", 54: "WV", 55: "WI", 56: "WY", 72: "PR"}


def forest(ax, df, series, key, colors, labels):
    k = len(series)
    ys = np.arange(len(BIN_OUT))[::-1]
    for i, s in enumerate(series):
        d = df[df[key] == s].set_index("outcome").reindex(BIN_OUT)
        off = (i - (k - 1) / 2) * 0.22
        ax.errorbar(d.ipw_diff * 100, ys + off, xerr=1.96 * d.ipw_se * 100, fmt="o", ms=5, color=colors[i],
                    elinewidth=1.6, capsize=0, label=labels[i], markeredgecolor=SURF, markeredgewidth=1)
    ax.axvline(0, color=INK2, lw=1)
    ax.set_yticks(ys)
    ax.set_yticklabels([LABEL[o] for o in BIN_OUT])
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Leaver minus matched stayer (percentage points, 95% CI)")


def main():
    c = pd.read_csv(os.path.join(OUT, "leaver_vs_stayer_contrasts.csv"))

    fig, ax = plt.subplots(figsize=(8.5, 5.6))
    tr = ["left_ca", "left_saccv", "left_othca"]
    forest(ax, c[c["sample"] == "all"], tr, "treatment", SERIES, [TLAB[t] for t in tr])
    ax.set_title("Bay leavers vs comparable stayers, adults 18-64 (IPW, ACS 2022-24)", loc="left", fontsize=11)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.35, -0.1), ncol=3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1_ipw_by_destination.png"), dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 5.6))
    sm = ["all", "noBA", "lowinc_pov200"]
    sl = ["All adults", "No bachelor's degree", "Below 200% poverty (post-move)"]
    forest(ax, c[c.treatment == "left_any"], sm, "sample", SERIES, sl)
    ax.set_title("Any Bay leaver vs comparable stayers, by sample (IPW)", loc="left", fontsize=11)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.35, -0.1), ncol=3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_ipw_low_income_samples.png"), dpi=160)
    plt.close(fig)

    sg = pd.read_csv(os.path.join(OUT, "subgroup_contrasts_left_any.csv"))
    outs = ["own", "rent_burden30", "overcrowded", "commute60", "employed", "below_200pov"]
    fig, axes = plt.subplots(1, len(outs), figsize=(15, 4.6), sharey=True)
    order = [("race_eth", l) for l in ["Asian/PI", "Black", "Latino", "Other/Multi", "White"]] + \
            [("educ", l) for l in ["<HS", "HS/GED", "Some college/AA", "BA+"]]
    ys = np.arange(len(order))[::-1]
    for ax, o in zip(axes, outs):
        d = sg[sg.outcome == o].set_index(["subgroup_var", "level"]).reindex(order)
        col = [SERIES[0] if v == "race_eth" else SERIES[1] for v, _ in order]
        for y, (_, r), cc in zip(ys, d.iterrows(), col):
            ax.errorbar(r.ipw_diff * 100, y, xerr=1.96 * r.ipw_se * 100, fmt="o", ms=5, color=cc, elinewidth=1.5,
                        markeredgecolor=SURF)
        ax.axvline(0, color=INK2, lw=1)
        ax.set_title(LABEL[o].replace(" (", "\n("), fontsize=9, loc="left")
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(ys)
    axes[0].set_yticklabels([f"{l} (n={int(sg[(sg.subgroup_var==v)&(sg.level==l)].n_leavers.iloc[0])})" for v, l in order])
    fig.supxlabel("Any leaver minus matched stayer within subgroup (pp, 95% CI); blue = race/ethnicity, orange = education; n = unweighted leavers",
                  fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_subgroup_contrasts.png"), dpi=160)
    plt.close(fig)

    z = np.load(os.path.join(DATA, "exit_model_test_preds.npz"))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.4))
    names = [("baseline_base_rate", "Base-rate baseline"), ("logistic", "Logistic regression"),
             ("gradient_boosting", "Gradient boosting")]
    for i, (k, lab) in enumerate(names):
        fpr, tpr, _ = roc_curve(z["y"], z[k])
        pr, rc, _ = precision_recall_curve(z["y"], z[k])
        a1.plot(fpr, tpr, color=[INK2, SERIES[0], SERIES[1]][i], lw=2, label=lab)
        a2.plot(rc, pr, color=[INK2, SERIES[0], SERIES[1]][i], lw=2, label=lab)
    a1.set_xlabel("False positive rate"); a1.set_ylabel("True positive rate"); a1.set_title("ROC (held-out test)", loc="left")
    a2.set_xlabel("Recall"); a2.set_ylabel("Precision"); a2.set_title("Precision-recall (held-out test)", loc="left")
    a1.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig4_exit_model_curves.png"), dpi=160)
    plt.close(fig)

    er = pd.read_csv(os.path.join(OUT, "exit_rates_by_group.csv"))
    er = er[er["var"].isin(["race_eth", "educ", "age_grp"])]
    fig, ax = plt.subplots(figsize=(7.5, 5.6))
    ys = np.arange(len(er))[::-1]
    cols = {"race_eth": SERIES[0], "educ": SERIES[1], "age_grp": SERIES[2]}
    ax.barh(ys, er.exit_rate * 100, color=[cols[v] for v in er["var"]], height=0.7, edgecolor=SURF, linewidth=2)
    ax.errorbar(er.exit_rate * 100, ys, xerr=1.96 * er.exit_rate_se * 100, fmt="none", ecolor=INK, elinewidth=1)
    ax.set_yticks(ys); ax.set_yticklabels(er.level)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Share of Bay residents (1 yr ago) who left the Bay within the year, % (95% CI)")
    ax.set_title("Who leaves: one-year exit rate by group, adults 18-64, ACS 2022-24", loc="left", fontsize=11)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=v, label=l) for l, v in zip(["Race/ethnicity", "Education", "Age"], cols.values())],
              frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5_exit_rates_by_group.png"), dpi=160)
    plt.close(fig)

    st = pd.read_csv(os.path.join(OUT, "left_ca_destination_states.csv")).head(12)
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ys = np.arange(len(st))[::-1]
    ax.barh(ys, st.share * 100, color=SERIES[0], height=0.7)
    ax.set_yticks(ys); ax.set_yticklabels([f"{FIPS.get(int(s), s)} (n={n})" for s, n in zip(st.ST, st.n)])
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Share of out-of-state Bay leavers 18-64 (weighted %)")
    ax.set_title("Where out-of-state Bay leavers went (ACS 2022-24)", loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig6_destination_states.png"), dpi=160)
    plt.close(fig)
    print("figures written")


if __name__ == "__main__":
    main()
