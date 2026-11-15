"""Step 8 (side experiment, not in run_all.sh): swap LightGBM for a random forest, same protocol as s03.

Same split, encodings and feature sets. The forest is tuned on validation AUC, refit on train+validation and scored
on the 2026 test set. LightGBM is refit here with the s03 settings so both are scored on identical rows.
Note: this is a second look at the test set, made after the s03 result was known."""
import os, sys, json, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modlib import *

BUDGET = 0.20
RF_GRID = [dict(max_features=mf, min_samples_leaf=ml) for mf in ("sqrt", 0.33, 0.5) for ml in (1, 5, 20, 50)]
FULL = "+ tract + city jobs (all workstreams)"

def fit_rf(X, y, p, seed=SEED, n=500):
    return RandomForestClassifier(n_estimators=n, random_state=seed, n_jobs=-1, **p).fit(X, y)   # NaN handled natively

def tune_rf(Xtr, ytr, Xva, yva):
    res = [(roc_auc_score(yva, fit_rf(Xtr, ytr, p).predict_proba(Xva)[:, 1]), i) for i, p in enumerate(RF_GRID)]
    auc, i = max(res)
    return auc, RF_GRID[i], res

def top_caught(y, s, share=BUDGET):
    k = int(round(share * len(y))); idx = np.argsort(-s, kind="stable")[:k]
    return int(y[idx].sum())

def main():
    df, hist = load()
    tr, va, te = (df[df.split == s].copy() for s in ("train", "val", "test"))
    trva = df[df.split.isin(["train", "val"])].copy()
    tr_e, (va_e,) = add_encodings(tr, [va], hist, TRAIN_END)
    trva_e, (te_e,) = add_encodings(trva, [te], hist, VAL_END)
    y = te_e.y.values
    lgb_cfg = json.load(open(os.path.join(RES, "s03_config.json")))["lgb_params"]

    rows, tune_rows, val_s, test_s, models = [], [], {}, {}, {}
    for name, cols in SETS.items():
        p_l, n_l = lgb_cfg[name]
        auc_rf, p_r, grid = tune_rf(tr_e[cols], tr_e.y, va_e[cols], va_e.y)
        for a, i in grid: tune_rows.append(dict(features=name, **RF_GRID[i], val_AUC=a))
        fits = {"LightGBM": (lambda X, yy, seed=SEED: fit_lgb(X, yy, p_l, n_l, seed)),
                "Random forest": (lambda X, yy, seed=SEED: fit_rf(X, yy, p_r, seed))}
        for mname, f in fits.items():
            k = f"{mname} [{name}]"
            val_s[k] = f(tr_e[cols], tr_e.y).predict_proba(va_e[cols])[:, 1]
            models[k] = f(trva_e[cols], trva_e.y); s = models[k].predict_proba(te_e[cols])[:, 1]; test_s[k] = s
            bthr = np.quantile(val_s[k], 1 - BUDGET); m = metrics(y, s, None, bthr)
            lo, hi = boot_auc_ci(y, s)
            # training randomness: 10 seeds, settings fixed
            sa = [roc_auc_score(y, f(trva_e[cols], trva_e.y, seed).predict_proba(te_e[cols])[:, 1]) for seed in range(10)]
            rows.append(dict(model=mname, features=name, params=str(p_r if mname == "Random forest" else p_l),
                             val_AUC=roc_auc_score(va_e.y, val_s[k]), AUC=m["AUC"], AUC_lo=lo, AUC_hi=hi, PR_AUC=m["PR_AUC"],
                             Brier=brier_score_loss(y, s), mean_pred=s.mean(), prevalence=y.mean(),
                             budget_flagged=m["budget_flagged"], budget_precision=m["budget_precision"],
                             budget_recall=m["budget_recall"], caught_top20pct=top_caught(y, s), positives=int(y.sum()),
                             seed_AUC_mean=np.mean(sa), seed_AUC_sd=np.std(sa)))
    res = pd.DataFrame(rows); res.round(4).to_csv(os.path.join(RES, "s08_rf_metrics.csv"), index=False)
    pd.DataFrame(tune_rows).round(4).to_csv(os.path.join(RES, "s08_rf_tuning.csv"), index=False)
    pd.set_option("display.width", 250); print(res.round(3).drop(columns=["params"]).to_string(index=False))
    print(pd.DataFrame(tune_rows).query("features == @FULL").round(4).to_string(index=False))

    # paired bootstrap, forest minus LightGBM and forest minus rule / logistic (main feature set)
    L, R = f"LightGBM [{FULL}]", f"Random forest [{FULL}]"
    rule = baseline_scores(te_e)["Legal-max rule: crosses if rent rises at AB 1482 max (10%/yr)"]
    C = json.load(open(os.path.join(RES, "s03_config.json")))["logit_C"]
    logit = fit_logit(trva_e[ALL], trva_e.y, C).predict_proba(te_e[ALL])[:, 1]
    cmp = []
    for a, sa_, b, sb in [(R, test_s[R], L, test_s[L]), (R, test_s[R], "Legal-max rule", rule), (R, test_s[R], "Logistic (L2) all", logit),
                          (L, test_s[L], "Logistic (L2) all", logit)]:
        lo, hi = boot_auc_diff(y, sa_, sb)
        cmp.append(dict(a=a, b=b, diff=roc_auc_score(y, sa_) - roc_auc_score(y, sb), lo=lo, hi=hi))
    cmp = pd.DataFrame(cmp); cmp.round(4).to_csv(os.path.join(RES, "s08_rf_comparisons.csv"), index=False)
    print("\n", cmp.round(4).to_string(index=False))
    both = np.corrcoef(pd.Series(test_s[L]).rank(), pd.Series(test_s[R]).rank())[0, 1]
    k = int(round(BUDGET * len(y))); tl = set(np.argsort(-test_s[L])[:k]); trf = set(np.argsort(-test_s[R])[:k])
    print(f"rank correlation of the two scores {both:.3f}; overlap of the two top-20% lists {len(tl & trf) / k:.3f}")

    # grouped permutation importance for the forest
    rng = np.random.default_rng(SEED); base = roc_auc_score(y, test_s[R]); imp = []
    for g, cg in GROUPS.items():
        d = []
        for _ in range(5):
            X = te_e[ALL].copy(); X[cg] = X[cg].values[rng.permutation(len(X))]
            d.append(base - roc_auc_score(y, models[R].predict_proba(X)[:, 1]))
        imp.append(dict(group=g, rf_auc_drop=np.mean(d)))
    print("\n", pd.DataFrame(imp).round(4).to_string(index=False))

    # subgroups: same groupings as s03, both models, budget threshold from validation scores
    te_e["s_l"], te_e["s_r"] = test_s[L], test_s[R]
    bl, br = np.quantile(val_s[L], 1 - BUDGET), np.quantile(val_s[R], 1 - BUDGET)
    q = np.nanquantile(df.drop_duplicates("tract").real_hinc_18, [1 / 3, 2 / 3])
    sub = {"UDP typology group": te_e.udp_group.fillna("unmatched"),
           "Tract tenure": te_e.renter_majority.map({1.0: "majority renter", 0.0: "majority owner"}).fillna("unmatched"),
           "Tract race": te_e.poc_majority.map({1.0: "majority people of color", 0.0: "majority white"}).fillna("unmatched"),
           "Tract income (2018 tercile)": pd.cut(te_e.real_hinc_18, [-np.inf, q[0], q[1], np.inf], labels=["low", "middle", "high"]).astype(str),
           "Home type": np.where(te_e.homeType == "APARTMENT", "apartment", "house/condo/townhouse"),
           "Landlord": np.where(te_e.large_landlord == 1, "large manager (200+ units)", "other"),
           "County": te_e.county.str.replace(" County", "")}
    srows = []
    for gname, lab in sub.items():
        for g in sorted(pd.Series(lab).unique()):
            d = te_e[np.asarray(lab) == g]
            if len(d) < 30 or g in ("unmatched", "nan") or d.y.sum() == 0: continue
            ml, mr = metrics(d.y, d.s_l, None, bl), metrics(d.y, d.s_r, None, br)
            srows.append(dict(grouping=gname, group=g, n=len(d), leave_rate=d.y.mean(), lgb_AUC=ml["AUC"], rf_AUC=mr["AUC"],
                              lgb_budget_recall=ml["budget_recall"], rf_budget_recall=mr["budget_recall"],
                              lgb_pred_over_actual=d.s_l.mean() / d.y.mean(), rf_pred_over_actual=d.s_r.mean() / d.y.mean()))
    sg = pd.DataFrame(srows); sg.round(3).to_csv(os.path.join(RES, "s08_rf_subgroups.csv"), index=False)
    print("\n", sg.round(3).to_string(index=False))
    te_e["dec_l"] = pd.qcut(te_e.s_l, 10, labels=False, duplicates="drop"); te_e["dec_r"] = pd.qcut(te_e.s_r, 10, labels=False, duplicates="drop")
    cal = pd.concat([te_e.groupby("dec_l").agg(lgb_pred=("s_l", "mean"), lgb_obs=("y", "mean")),
                     te_e.groupby("dec_r").agg(rf_pred=("s_r", "mean"), rf_obs=("y", "mean"))], axis=1).round(3)
    cal.to_csv(os.path.join(RES, "s08_rf_calibration.csv")); print("\n", cal.to_string())

if __name__ == "__main__":
    main()
