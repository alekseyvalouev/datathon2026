"""Step 9 (side analysis, not in run_all.sh): accuracy, error and fairness analysis of the main LightGBM model on the 2026 test set.

Same split, encodings, features and tuned settings as s03 (read from s03_config.json); thresholds are re-derived from
validation scores exactly as in s03. Nothing is re-tuned here: this is a deeper read of the s03 test result.
Outputs: s09_overall.csv, s09_subgroups.csv, s09_gaps.csv, s09_headroom_adjusted.csv, s09_error_profile.csv,
s09_by_headroom.csv, s09_by_month.csv, s09_group_thresholds.csv, figs/s09_subgroup_errors.png."""
import os, sys, json, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, brier_score_loss
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modlib import *

BUDGET, B = 0.20, 1000
FULL = "+ tract + city jobs (all workstreams)"
RULE = "Legal-max rule: crosses if rent rises at AB 1482 max (10%/yr)"
HBINS = [-0.01, 0.025, 0.05, 0.10, 0.15, 0.20, 0.30, 0.45, 5]

def conf(y, f):
    y = np.asarray(y).astype(bool); f = np.asarray(f).astype(bool)
    tp, fp, fn, tn = (f & y).sum(), (f & ~y).sum(), (~f & y).sum(), (~f & ~y).sum()
    d = lambda a, b: a / b if b else np.nan
    return dict(TP=int(tp), FP=int(fp), FN=int(fn), TN=int(tn), accuracy=d(tp + tn, len(y)), recall=d(tp, tp + fn),
                FPR=d(fp, fp + tn), precision=d(tp, tp + fp), balanced_acc=(d(tp, tp + fn) + d(tn, tn + fp)) / 2,
                F1=d(2 * tp, 2 * tp + fp + fn), flagged=f.mean())

def group_stats(y, s, f):
    """Point metrics for one group: y labels, s scores, f flags at the fixed operating point."""
    c = conf(y, f)
    return dict(accuracy=c["accuracy"], recall=c["recall"], FPR=c["FPR"], precision=c["precision"],
                AUC=roc_auc_score(y, s) if 0 < y.sum() < len(y) else np.nan,
                pred_over_obs=s.mean() / y.mean() if y.sum() else np.nan)

def main():
    df, hist = load()
    tr, va, te = (df[df.split == s].copy() for s in ("train", "val", "test"))
    trva = df[df.split.isin(["train", "val"])].copy()
    tr_e, (va_e,) = add_encodings(tr, [va], hist, TRAIN_END)
    trva_e, (te_e,) = add_encodings(trva, [te], hist, VAL_END)
    p, n = json.load(open(os.path.join(RES, "s03_config.json")))["lgb_params"][FULL]
    val_s = fit_lgb(tr_e[ALL], tr_e.y, p, n).predict_proba(va_e[ALL])[:, 1]
    s = fit_lgb(trva_e[ALL], trva_e.y, p, n).predict_proba(te_e[ALL])[:, 1]
    y = te_e.y.values.astype(int)
    thr_f1, thr_b = f1_threshold(va_e.y.values, val_s), np.quantile(val_s, 1 - BUDGET)
    thr_top = np.sort(s)[::-1][int(round(BUDGET * len(s))) - 1]          # exactly 20% of test units (uses test scores, ranking only)
    rule_s = baseline_scores(te_e)[RULE]
    te_e = te_e.assign(score=s, flag=(s >= thr_b).astype(int), flag_f1=(s >= thr_f1).astype(int))
    print(f"test n={len(y)}, positives={y.sum()}, prevalence={y.mean():.3f}; F1 thr={thr_f1:.3f}, budget thr={thr_b:.3f}")

    # ---------------------------------------------------------------- 1. overall accuracy
    rows = [dict(model="Majority class (never leaves)", operating_point="-", **conf(y, np.zeros(len(y)))),
            dict(model="Legal-max rule", operating_point="rule's own cut (10%/yr)", **conf(y, rule_s >= RULE_THR[RULE])),
            dict(model="LightGBM", operating_point="0.5 (default)", **conf(y, s >= 0.5)),
            dict(model="LightGBM", operating_point=f"F1-max on validation ({thr_f1:.3f})", **conf(y, s >= thr_f1)),
            dict(model="LightGBM", operating_point=f"20% budget from validation ({thr_b:.3f})", **conf(y, s >= thr_b)),
            dict(model="LightGBM", operating_point="top 20% of test", **conf(y, s >= thr_top)),
            dict(model="Legal-max rule", operating_point="top 20% of test", **conf(y, rule_s >= np.sort(rule_s)[::-1][int(round(BUDGET * len(y))) - 1]))]
    ov = pd.DataFrame(rows); ov["AUC"] = [np.nan if "Majority" in m else roc_auc_score(y, rule_s if "rule" in m else s) for m in ov.model]
    ov.loc[ov.model == "LightGBM", "Brier"] = brier_score_loss(y, s)
    ov.loc[ov.model == "LightGBM", "Brier_constant_rate"] = brier_score_loss(y, np.full(len(y), trva_e.y.mean()))
    rng = np.random.default_rng(SEED); acc = []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y)); acc.append([((s[i] >= t) == y[i]).mean() - (1 - y[i].mean()) for t in (thr_f1, thr_b)])
    lo, hi = np.percentile(acc, [2.5, 97.5], axis=0)
    print("accuracy minus majority-class accuracy: F1 point %+.3f [%.3f, %.3f]; budget point %+.3f [%.3f, %.3f]" %
          (np.mean(acc, 0)[0], lo[0], hi[0], np.mean(acc, 0)[1], lo[1], hi[1]))
    ov.round(4).to_csv(os.path.join(RES, "s09_overall.csv"), index=False)
    pd.set_option("display.width", 250); print(ov.round(3).to_string(index=False))

    # ---------------------------------------------------------------- 2. subgroups with bootstrap intervals
    q = np.nanquantile(df.drop_duplicates("tract").real_hinc_18, [1 / 3, 2 / 3])
    sub = {"Tract income (2018 tercile)": pd.cut(te_e.real_hinc_18, [-np.inf, q[0], q[1], np.inf], labels=["low", "middle", "high"]).astype(str),
           "Tract race": te_e.poc_majority.map({1.0: "majority people of color", 0.0: "majority white"}).fillna("unmatched"),
           "Tract tenure": te_e.renter_majority.map({1.0: "majority renter", 0.0: "majority owner"}).fillna("unmatched"),
           "UDP typology group": te_e.udp_group.fillna("unmatched"),
           "Home type": np.where(te_e.homeType == "APARTMENT", "apartment", "house/condo/townhouse"),
           "Landlord": np.where(te_e.large_landlord == 1, "large manager (200+ units)", "other"),
           "County": te_e.county.str.replace(" County", "")}
    sub = {k: np.asarray(v) for k, v in sub.items()}
    f = te_e.flag.values; mets = ["accuracy", "recall", "FPR", "precision", "AUC", "pred_over_obs"]
    masks = {(g, v): sub[g] == v for g in sub for v in sorted(set(sub[g])) if v not in ("unmatched", "nan")}
    boot = {k: [] for k in masks}; rng = np.random.default_rng(SEED)
    for _ in range(B):
        i = rng.integers(0, len(y), len(y)); yi, si, fi = y[i], s[i], f[i]
        for k, m in masks.items():
            mi = m[i]; boot[k].append([group_stats(yi[mi], si[mi], fi[mi])[c] for c in mets])
    boot = {k: np.array(v, float) for k, v in boot.items()}
    srows = []
    for (g, v), m in masks.items():
        st = group_stats(y[m], s[m], f[m]); c = conf(y[m], f[m]); lo, hi = np.nanpercentile(boot[(g, v)], [2.5, 97.5], axis=0)
        r = dict(grouping=g, group=v, n=int(m.sum()), positives=int(y[m].sum()), leave_rate=y[m].mean(), flagged=c["flagged"],
                 missed_FN=c["FN"], false_alarms_FP=c["FP"], median_headroom=np.median(te_e.headroom.values[m]))
        for j, c_ in enumerate(mets): r[c_] = st[c_]; r[c_ + "_lo"] = lo[j]; r[c_ + "_hi"] = hi[j]
        srows.append(r)
    sg = pd.DataFrame(srows); sg.round(3).to_csv(os.path.join(RES, "s09_subgroups.csv"), index=False)
    show = ["grouping", "group", "n", "leave_rate", "accuracy", "AUC", "recall", "recall_lo", "recall_hi", "FPR", "FPR_lo", "FPR_hi", "precision", "pred_over_obs"]
    print("\nSubgroups at the 20% budget threshold\n", sg[show].round(3).to_string(index=False))

    # ---------------------------------------------------------------- 3. gaps between paired groups (bootstrap difference)
    pairs = [("Tract income (2018 tercile)", "low", "high"), ("Tract race", "majority people of color", "majority white"),
             ("Tract tenure", "majority renter", "majority owner"), ("UDP typology group", "low_income", "exclusive"),
             ("UDP typology group", "gentrifying", "exclusive"), ("Home type", "apartment", "house/condo/townhouse"),
             ("Landlord", "large manager (200+ units)", "other")]
    grows = []
    for g, a, b in pairs:
        d = boot[(g, a)] - boot[(g, b)]; lo, hi = np.nanpercentile(d, [2.5, 97.5], axis=0)
        pa, pb = group_stats(y[masks[(g, a)]], s[masks[(g, a)]], f[masks[(g, a)]]), group_stats(y[masks[(g, b)]], s[masks[(g, b)]], f[masks[(g, b)]])
        for j, c_ in enumerate(mets):
            grows.append(dict(grouping=g, a=a, b=b, metric=c_, a_value=pa[c_], b_value=pb[c_], diff=pa[c_] - pb[c_], lo=lo[j], hi=hi[j],
                              clear=bool(lo[j] > 0 or hi[j] < 0)))
    gaps = pd.DataFrame(grows); gaps.round(3).to_csv(os.path.join(RES, "s09_gaps.csv"), index=False)
    print("\nGaps (a minus b), 95% bootstrap\n", gaps[gaps.metric.isin(["recall", "FPR", "AUC", "pred_over_obs"])].round(3).to_string(index=False))

    # ---------------------------------------------------------------- 4. is the recall gap just headroom composition?
    # Direct standardisation: recall (and FPR) inside headroom bins, reweighted to the pair's pooled distribution of positives (negatives).
    hb = pd.cut(te_e.headroom, HBINS, labels=False).values
    def std_rate(mask, cls, w):
        num = 0.0
        for b_, wt in w.items():
            mm = mask & (hb == b_) & (y == cls); num += wt * f[mm].mean()
        return num
    def adj_gap(ma, mb, cls, idx=None):
        yy, ff, hh = (y, f, hb) if idx is None else (y[idx], f[idx], hb[idx])
        ma, mb = (ma, mb) if idx is None else (ma[idx], mb[idx])
        bins = [b_ for b_ in range(len(HBINS) - 1) if (ma & (hh == b_) & (yy == cls)).sum() >= 5 and (mb & (hh == b_) & (yy == cls)).sum() >= 5]
        if not bins: return np.nan, np.nan, np.nan, 0
        cnt = np.array([((ma | mb) & (hh == b_) & (yy == cls)).sum() for b_ in bins], float); w = cnt / cnt.sum()
        ra = sum(wt * ff[ma & (hh == b_) & (yy == cls)].mean() for b_, wt in zip(bins, w))
        rb = sum(wt * ff[mb & (hh == b_) & (yy == cls)].mean() for b_, wt in zip(bins, w))
        return ra, rb, ra - rb, len(bins)
    arows = []; rng = np.random.default_rng(SEED); idxs = [rng.integers(0, len(y), len(y)) for _ in range(B)]
    for g, a, b in pairs:
        ma, mb = masks[(g, a)], masks[(g, b)]
        for cls, name in ((1, "recall"), (0, "FPR")):
            raw = f[ma & (y == cls)].mean() - f[mb & (y == cls)].mean()
            ra, rb, dd, nb = adj_gap(ma, mb, cls)
            bs = [adj_gap(ma, mb, cls, i)[2] for i in idxs]; lo, hi = np.nanpercentile(bs, [2.5, 97.5])
            arows.append(dict(grouping=g, a=a, b=b, metric=name, raw_gap=raw, a_adj=ra, b_adj=rb, adj_gap=dd, adj_lo=lo, adj_hi=hi,
                              bins_used=nb, share_of_gap_left=dd / raw if raw else np.nan,
                              a_median_headroom_pos=np.median(te_e.headroom.values[ma & (y == 1)]),
                              b_median_headroom_pos=np.median(te_e.headroom.values[mb & (y == 1)])))
    adj = pd.DataFrame(arows); adj.round(3).to_csv(os.path.join(RES, "s09_headroom_adjusted.csv"), index=False)
    print("\nHeadroom-standardised gaps\n", adj.round(3).to_string(index=False))

    # ---------------------------------------------------------------- 5. what the errors look like
    te_e["outcome"] = np.select([(y == 1) & (f == 1), (y == 1) & (f == 0), (y == 0) & (f == 1)], ["caught (TP)", "missed (FN)", "false alarm (FP)"], "correctly cleared (TN)")
    te_e["ann_growth"] = (te_e.next_last / te_e.last_p) ** (1 / te_e.start_gap_y.clip(lower=0.25)) - 1
    te_e["over_line_by"] = te_e.next_last / te_e.thr - 1
    prof = te_e.groupby("outcome").agg(n=("y", "size"), median_headroom=("headroom", "median"), median_req_growth=("req_growth", "median"),
                                       median_rent_change=("r", "median"), median_ann_growth=("ann_growth", "median"),
                                       median_over_line_by=("over_line_by", "median"), median_gap_years=("start_gap_y", "median"),
                                       share_apartment=("homeType", lambda x: (x == "APARTMENT").mean()),
                                       share_large_landlord=("large_landlord", "mean"), median_prev_rent=("last_p", "median"),
                                       mean_score=("score", "mean")).round(3)
    prof.to_csv(os.path.join(RES, "s09_error_profile.csv")); print("\n", prof.to_string())
    fn = te_e[te_e.outcome == "missed (FN)"]
    print("missed losses: %.0f%% had headroom >15%%; %.0f%% rose more than 10%%/yr; %.0f%% more than 30%%/yr; %.0f%% ended <5%% over the line" %
          (100 * (fn.headroom > .15).mean(), 100 * (fn.ann_growth > .10).mean(), 100 * (fn.ann_growth > .30).mean(), 100 * (fn.over_line_by < .05).mean()))
    hd = te_e.assign(hbin=pd.cut(te_e.headroom, [-0.01, 0.05, 0.15, 0.30, 5], labels=["<5%", "5-15%", "15-30%", ">30%"]))
    hrow = hd.groupby("hbin", observed=True).apply(include_groups=False, func=lambda d: pd.Series(dict(n=len(d), leave_rate=d.y.mean(), **{k: conf(d.y, d.flag)[k] for k in ("accuracy", "recall", "FPR", "FN", "FP")},
                                                                         mean_pred=d.score.mean(), share_of_all_FN=((d.y == 1) & (d.flag == 0)).sum() / max(((y == 1) & (f == 0)).sum(), 1),
                                                                         share_of_all_FP=((d.y == 0) & (d.flag == 1)).sum() / max(((y == 0) & (f == 1)).sum(), 1))))
    print("\nBy headroom\n", hrow.round(3).to_string())
    hrow.round(3).to_csv(os.path.join(RES, "s09_by_headroom.csv"))
    te_e["month"] = pd.to_datetime(te_e.next_start).dt.to_period("M").astype(str)
    mo = te_e.groupby("month").apply(include_groups=False, func=lambda d: pd.Series(dict(n=len(d), leave_rate=d.y.mean(), mean_pred=d.score.mean(), AUC=roc_auc_score(d.y, d.score) if 0 < d.y.sum() < len(d) else np.nan,
                                                              **{k: conf(d.y, d.flag)[k] for k in ("accuracy", "recall", "FPR", "flagged")})))
    mo.round(3).to_csv(os.path.join(RES, "s09_by_month.csv")); print("\nBy re-listing month\n", mo.round(3).to_string())

    # ---------------------------------------------------------------- 6. what a per-group threshold would do (validation-chosen, like s04 R4 but for each grouping)
    va_e = va_e.assign(score=val_s)
    vsub = {"Tract income (2018 tercile)": pd.cut(va_e.real_hinc_18, [-np.inf, q[0], q[1], np.inf], labels=["low", "middle", "high"]).astype(str),
            "Tract tenure": va_e.renter_majority.map({1.0: "majority renter", 0.0: "majority owner"}).fillna("unmatched"),
            "Home type": np.where(va_e.homeType == "APARTMENT", "apartment", "house/condo/townhouse")}
    trows = []
    for g, lab in vsub.items():
        lab = np.asarray(lab); flag2 = np.zeros(len(y), bool)
        for v in sorted(set(sub[g])):
            vm = lab == v; t = np.quantile(val_s[vm], 1 - BUDGET) if vm.sum() >= 30 else thr_b
            flag2 |= (sub[g] == v) & (s >= t)
        for v in sorted(set(sub[g])):
            if v in ("unmatched", "nan"): continue
            m = sub[g] == v; c1, c2 = conf(y[m], f[m]), conf(y[m], flag2[m])
            trows.append(dict(grouping=g, group=v, recall_one_list=c1["recall"], recall_group_lists=c2["recall"], FPR_one_list=c1["FPR"], FPR_group_lists=c2["FPR"],
                              precision_one_list=c1["precision"], precision_group_lists=c2["precision"]))
        c1, c2 = conf(y, f), conf(y, flag2)
        trows.append(dict(grouping=g, group="ALL", recall_one_list=c1["recall"], recall_group_lists=c2["recall"], FPR_one_list=c1["FPR"], FPR_group_lists=c2["FPR"],
                          precision_one_list=c1["precision"], precision_group_lists=c2["precision"]))
    gt = pd.DataFrame(trows); gt.round(3).to_csv(os.path.join(RES, "s09_group_thresholds.csv"), index=False)
    print("\nOne regional list vs a top-20% list inside each group (thresholds from validation)\n", gt.round(3).to_string(index=False))

    # ---------------------------------------------------------------- figure
    d = sg[sg.grouping.isin(["Tract income (2018 tercile)", "Tract race", "Tract tenure", "Home type", "Landlord"])].reset_index(drop=True)
    fig, ax = plt.subplots(1, 3, figsize=(11, 4.6), sharey=True); yy = np.arange(len(d))
    for a_, (c_, title, ref) in zip(ax, [("recall", "Recall: losses caught", conf(y, f)["recall"]), ("FPR", "False-alarm rate", conf(y, f)["FPR"]),
                                         ("pred_over_obs", "Mean prediction / observed rate", 1.0)]):
        a_.errorbar(d[c_], yy, xerr=[d[c_] - d[c_ + "_lo"], d[c_ + "_hi"] - d[c_]], fmt="o", color="#1f4e79", ecolor="#9db7d1", capsize=2, ms=5)
        a_.axvline(ref, ls=":", color="#c55a11", lw=1); a_.set_title(title, fontsize=10, loc="left"); a_.grid(axis="x", color="#eee")
        for sp in ("top", "right"): a_.spines[sp].set_visible(False)
    ax[0].set_yticks(yy, [f"{g.split(' (')[0]}: {v}" for g, v in zip(d.grouping, d.group)], fontsize=8); ax[0].invert_yaxis()
    fig.suptitle("LightGBM on 2026 test, one regional 20% list: subgroup errors with 95% bootstrap intervals (dotted = all units; 1.0 for calibration)", fontsize=9, x=0.01, ha="left")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "s09_subgroup_errors.png"), dpi=150); plt.close(fig)

if __name__ == "__main__":
    main()
