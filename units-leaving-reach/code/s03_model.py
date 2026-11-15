"""Step 3: baselines, models, one-shot temporal test, ablation by workstream, subgroup fairness, failures, figures.

Split (re-listing date): train < 2025-07-01, validation 2025-07..12 (tuning, thresholds), test >= 2026-01-01.
Final models are refit on train+validation with validation-chosen settings and scored once on test.
Two operating points: F1-maximising threshold chosen on validation, and a fixed outreach budget that flags the
riskiest 20% of units (threshold = 80th percentile of validation scores)."""
import os, sys, json, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, precision_recall_curve, roc_auc_score
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modlib import *

BUDGET = 0.20

def main():
    df, hist = load()
    tr, va, te = (df[df.split == s].copy() for s in ("train", "val", "test"))
    trva = df[df.split.isin(["train", "val"])].copy()   # original row order (LightGBM bagging is order-sensitive)
    # --- tuning: encodings fit on train only, evaluated on validation
    tr_e, (va_e,) = add_encodings(tr, [va], hist, TRAIN_END)
    tuned, rows = {}, []
    for name, cols in SETS.items():
        auc, p, n = tune_lgb(tr_e[cols], tr_e.y, va_e[cols], va_e.y)
        tuned[name] = (p, n); rows.append(dict(model="LightGBM", features=name, val_AUC=auc, params=str(p), n_trees=n))
    aucC, C = tune_logit(tr_e[ALL], tr_e.y, va_e[ALL], va_e.y)
    rows.append(dict(model="Logistic (L2)", features="all", val_AUC=aucC, params=f"C={C}"))
    aucH, CH = tune_logit(tr_e[HEAD + ["start_gap_y"]], tr_e.y, va_e[HEAD + ["start_gap_y"]], va_e.y)
    rows.append(dict(model="Logistic, headroom only", features="headroom + gap", val_AUC=aucH, params=f"C={CH}"))
    pd.DataFrame(rows).to_csv(os.path.join(RES, "s03_tuning.csv"), index=False)
    print(pd.DataFrame(rows).to_string(index=False))

    # validation scores of the chosen configurations (for thresholds), fit on train
    full = "+ tract + city jobs (all workstreams)"
    val_scores = {}
    for name in SETS:
        p, n = tuned[name]
        val_scores[f"LightGBM [{name}]"] = fit_lgb(tr_e[SETS[name]], tr_e.y, p, n).predict_proba(va_e[SETS[name]])[:, 1]
    val_scores["Logistic (L2) [all features]"] = fit_logit(tr_e[ALL], tr_e.y, C).predict_proba(va_e[ALL])[:, 1]
    val_scores["Logistic, headroom only"] = fit_logit(tr_e[HEAD + ["start_gap_y"]], tr_e.y, CH).predict_proba(va_e[HEAD + ["start_gap_y"]])[:, 1]
    for b, s in baseline_scores(va_e).items(): val_scores[b] = s

    # --- final: refit on train+val, score test once
    trva_e, (te_e,) = add_encodings(trva, [te], hist, VAL_END)
    test_scores, models = {}, {}
    for b, s in baseline_scores(te_e).items(): test_scores[b] = s
    test_scores["Logistic, headroom only"] = fit_logit(trva_e[HEAD + ["start_gap_y"]], trva_e.y, CH).predict_proba(te_e[HEAD + ["start_gap_y"]])[:, 1]
    test_scores["Logistic (L2) [all features]"] = fit_logit(trva_e[ALL], trva_e.y, C).predict_proba(te_e[ALL])[:, 1]
    for name in SETS:
        p, n = tuned[name]
        models[name] = fit_lgb(trva_e[SETS[name]], trva_e.y, p, n)
        test_scores[f"LightGBM [{name}]"] = models[name].predict_proba(te_e[SETS[name]])[:, 1]
    MAIN = f"LightGBM [{full}]"

    # --- test metrics
    y = te_e.y.values; res = []
    for k, s in test_scores.items():
        thr = RULE_THR.get(k, None) if k in RULE_THR else f1_threshold(va_e.y.values, val_scores[k])
        bthr = np.quantile(val_scores[k], 1 - BUDGET) if k not in ("Majority class (never leaves reach)",) else None
        if k.startswith("UDP"): bthr = None
        m = metrics(y, s, thr, bthr); m["model"] = k
        lo, hi = boot_auc_ci(y, s) if 0 < np.std(s) else (np.nan, np.nan)
        m["AUC_lo"], m["AUC_hi"] = lo, hi
        res.append(m)
    res = pd.DataFrame(res).set_index("model")
    cols = ["n", "prevalence", "AUC", "AUC_lo", "AUC_hi", "PR_AUC", "precision", "recall", "F1", "FPR",
            "budget_flagged", "budget_precision", "budget_recall"]
    res[cols].round(3).to_csv(os.path.join(RES, "s03_test_metrics.csv"))
    print("\nTEST (n=%d, prevalence %.3f)" % (len(y), y.mean())); print(res[cols].round(3).to_string())

    # --- paired bootstrap: model vs best rule baseline, and ablation gains
    best_rule = max([k for k in RULE_THR if k.startswith(("Legal", "ZIP"))], key=lambda k: res.loc[k, "AUC"])
    names = list(SETS)
    comps = [(MAIN, best_rule), (MAIN, "Logistic, headroom only"), (MAIN, "Logistic (L2) [all features]"),
             (f"LightGBM [{names[1]}]", f"LightGBM [{names[0]}]"), (f"LightGBM [{names[2]}]", f"LightGBM [{names[1]}]")]
    cmp = []
    for a, b in comps:
        lo, hi = boot_auc_diff(y, test_scores[a], test_scores[b])
        cmp.append(dict(a=a, b=b, AUC_a=res.loc[a, "AUC"], AUC_b=res.loc[b, "AUC"],
                        diff=res.loc[a, "AUC"] - res.loc[b, "AUC"], lo=lo, hi=hi))
    cmp = pd.DataFrame(cmp); cmp.round(4).to_csv(os.path.join(RES, "s03_comparisons.csv"), index=False)
    print("\n", cmp.round(4).to_string(index=False))

    # --- grouped permutation importance on test (AUC drop when a feature group is shuffled together)
    rng = np.random.default_rng(SEED); base_auc = roc_auc_score(y, test_scores[MAIN]); imp = []
    for g, cols_g in GROUPS.items():
        drops = []
        for rep in range(5):
            X = te_e[ALL].copy(); idx = rng.permutation(len(X))
            X[cols_g] = X[cols_g].values[idx]
            drops.append(base_auc - roc_auc_score(y, models[full].predict_proba(X)[:, 1]))
        imp.append(dict(group=g, n_features=len(cols_g), auc_drop=np.mean(drops), sd=np.std(drops)))
    imp = pd.DataFrame(imp).sort_values("auc_drop", ascending=False); imp.round(4).to_csv(os.path.join(RES, "s03_group_importance.csv"), index=False)
    gain = pd.Series(models[full].booster_.feature_importance("gain"), index=ALL).sort_values(ascending=False)
    (gain / gain.sum()).round(4).rename("gain_share").to_csv(os.path.join(RES, "s03_feature_gain.csv"))
    print("\n", imp.round(4).to_string(index=False)); print((gain / gain.sum()).head(12).round(3).to_string())

    # --- subgroup fairness on test: main model vs best rule baseline, same operating points as above
    te_e["score"] = test_scores[MAIN]; te_e["score_rule"] = test_scores[best_rule]
    thr = f1_threshold(va_e.y.values, val_scores[MAIN]); bthr = np.quantile(val_scores[MAIN], 1 - BUDGET)
    rthr = RULE_THR[best_rule]; rbthr = np.quantile(val_scores[best_rule], 1 - BUDGET)
    inc = te_e.real_hinc_18; q = np.nanquantile(df.drop_duplicates("tract").real_hinc_18, [1 / 3, 2 / 3])
    sub = {
        "UDP typology group": te_e.udp_group.fillna("unmatched"),
        "County": te_e.county.str.replace(" County", ""),
        "Tract tenure": te_e.renter_majority.map({1.0: "majority renter", 0.0: "majority owner"}).fillna("unmatched"),
        "Tract race": te_e.poc_majority.map({1.0: "majority people of color", 0.0: "majority white"}).fillna("unmatched"),
        "Tract income (2018 tercile)": pd.cut(inc, [-np.inf, q[0], q[1], np.inf], labels=["low", "middle", "high"]).astype(str),
        "Home type": np.where(te_e.homeType == "APARTMENT", "apartment", "house/condo/townhouse"),
        "Landlord": np.where(te_e.large_landlord == 1, "large manager (200+ units)", "other"),
        "Headroom below the line": pd.cut(te_e.headroom, [-0.01, 0.05, 0.15, 0.30, 5], labels=["<5%", "5-15%", "15-30%", ">30%"]).astype(str),
    }
    srows = []
    for gname, lab in sub.items():
        for g in sorted(pd.Series(lab).unique()):
            mask = (np.asarray(lab) == g)
            if mask.sum() < 30: continue
            d = te_e[mask]
            m = metrics(d.y, d.score, thr, bthr); r = metrics(d.y, d.score_rule, rthr, rbthr)
            srows.append(dict(grouping=gname, group=g, n=m["n"], positives=int(d.y.sum()), prevalence=m["prevalence"],
                              AUC=m["AUC"], recall=m["recall"], FPR=m["FPR"], precision=m["precision"],
                              budget_recall=m["budget_recall"], budget_flagged=m["budget_flagged"],
                              mean_pred=d.score.mean(), rule_AUC=r["AUC"], rule_budget_recall=r["budget_recall"]))
    sg = pd.DataFrame(srows); sg.round(3).to_csv(os.path.join(RES, "s03_subgroups.csv"), index=False)
    print("\n", sg.round(3).to_string(index=False))

    # --- calibration (deciles) and failures
    te_e["dec"] = pd.qcut(te_e.score, 10, labels=False, duplicates="drop")
    cal = te_e.groupby("dec").agg(n=("y", "size"), mean_pred=("score", "mean"), observed=("y", "mean")).round(3)
    cal.to_csv(os.path.join(RES, "s03_calibration.csv")); print("\n", cal.to_string())
    keep = ["zpid", "county", "city", "zipcode", "homeType", "beds", "udp_typ", "start_d", "next_start", "start_gap_y",
            "last_p", "next_first", "next_last", "thr", "headroom", "req_growth", "te_zip_r", "large_landlord", "score", "y"]
    fn = te_e[te_e.y == 1].nsmallest(12, "score")[keep].assign(kind="missed (false negative)")
    fp = te_e[te_e.y == 0].nlargest(12, "score")[keep].assign(kind="false alarm (false positive)")
    pd.concat([fn, fp]).round(3).to_csv(os.path.join(RES, "s03_failures.csv"), index=False)
    te_e[["zpid", "county", "zipcode", "udp_group", "y", "score", "score_rule"]].to_parquet(os.path.join(RES, "s03_test_predictions.parquet"), index=False)
    json.dump(dict(main=MAIN, best_rule=best_rule, f1_threshold=float(thr), budget_threshold=float(bthr),
                   lgb_params={k: (v[0], v[1]) for k, v in tuned.items()}, logit_C=C),
              open(os.path.join(RES, "s03_config.json"), "w"), indent=1, default=str)
    figures(y, test_scores, MAIN, best_rule, sg, cal)

def figures(y, sc, main, rule, sg, cal):
    show = [main, "Logistic (L2) [all features]", rule, "Logistic, headroom only", "UDP typology rule (low-income or gentrifying tract)"]
    col = ["#1f4e79", "#5b9bd5", "#c55a11", "#f4b183", "#7f7f7f"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
    for k, c in zip(show, col):
        f, t, _ = roc_curve(y, sc[k]); ax[0].plot(f, t, color=c, lw=1.8, label=f"{k[:48]} ({roc_auc_score(y, sc[k]):.2f})")
        p, r, _ = precision_recall_curve(y, sc[k]); ax[1].plot(r, p, color=c, lw=1.8)
    ax[0].plot([0, 1], [0, 1], ls=":", color="#aaa"); ax[0].set_xlabel("false-positive rate"); ax[0].set_ylabel("true-positive rate")
    ax[1].axhline(y.mean(), ls=":", color="#aaa"); ax[1].set_xlabel("recall"); ax[1].set_ylabel("precision")
    ax[0].legend(fontsize=7, frameon=False, loc="lower right"); ax[0].set_title("ROC, 2026 test", fontsize=10); ax[1].set_title("Precision-recall, 2026 test", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "roc_pr_test.png"), dpi=150); plt.close(fig)
    d = sg[sg.grouping.isin(["UDP typology group", "Tract tenure", "Tract race", "Tract income (2018 tercile)", "Home type"])]
    d = d[~d.group.astype(str).isin(["unmatched", "nan"])]
    fig, ax = plt.subplots(figsize=(8, 5)); yy = np.arange(len(d))
    ax.barh(yy + 0.2, d.budget_recall, 0.4, color="#1f4e79", label="model")
    ax.barh(yy - 0.2, d.rule_budget_recall, 0.4, color="#f4b183", label="best rule baseline")
    ax.set_yticks(yy, [f"{g}: {h}" for g, h in zip(d.grouping, d.group)], fontsize=8); ax.invert_yaxis()
    ax.set_xlabel(f"recall when flagging the riskiest {int(BUDGET*100)}% of units"); ax.legend(frameon=False, fontsize=8, loc="lower right", bbox_to_anchor=(1, 1.0), ncol=2)
    ax.set_title("Units that left low-income reach, caught when flagging the riskiest 20%", fontsize=9, loc="left", pad=16)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "subgroup_budget_recall.png"), dpi=150); plt.close(fig)
    fig, ax = plt.subplots(figsize=(4.2, 4)); ax.plot(cal.mean_pred, cal.observed, "o-", color="#1f4e79"); ax.plot([0, 1], [0, 1], ":", color="#aaa")
    ax.set_xlabel("mean predicted"); ax.set_ylabel("observed"); ax.set_title("Calibration by decile, 2026 test", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "calibration_test.png"), dpi=150); plt.close(fig)

if __name__ == "__main__":
    main()
