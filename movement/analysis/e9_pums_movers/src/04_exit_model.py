"""Who leaves the Bay? Predict leave (any destination) vs stay from pre-determined covariates.

Models: base-rate (majority/prior) baseline, logistic regression, histogram gradient boosting.
Held-out 30% test split (stratified). Metrics: ROC-AUC, PR-AUC (average precision), Brier,
recall/precision at the top-decile risk threshold; unweighted and PWGTP-weighted.
Fairness: same metrics + calibration (mean predicted vs observed) by race/ethnicity, education, age group.
"""
import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA, OUT = os.path.join(BASE, "data"), os.path.join(BASE, "outputs")
CAT = ["race_eth", "educ", "age_grp", "hh_type", "YEAR", "origin_county"]
BIN = ["female", "foreign_born", "married", "disabled", "kids"]
SEED = 20261114


def features(df):
    X = pd.get_dummies(df[CAT].astype(str), drop_first=False)
    X[BIN] = df[BIN].values
    X["age"] = df.AGEP.values
    return X.astype(float)


def metrics(y, p, w=None, thr=None):
    m = {"n": int(len(y)), "n_pos": int(y.sum()), "prevalence": float(np.average(y, weights=w))}
    if len(np.unique(y)) == 2:
        m["roc_auc"] = roc_auc_score(y, p, sample_weight=w)
        m["pr_auc"] = average_precision_score(y, p, sample_weight=w)
    m["brier"] = brier_score_loss(y, p, sample_weight=w)
    m["mean_pred"] = float(np.average(p, weights=w))
    if thr is not None:
        flag = p >= thr
        ww = np.ones_like(p) if w is None else w
        m["flag_rate"] = float(np.average(flag, weights=ww))
        m["recall_top10"] = float((ww * flag * y).sum() / max((ww * y).sum(), 1e-9))
        m["precision_top10"] = float((ww * flag * y).sum() / max((ww * flag).sum(), 1e-9))
    return m


def main():
    df = pd.read_parquet(os.path.join(DATA, "bay_origin_adults.parquet"))
    X = features(df)
    y = df.leaver.values
    w = df.PWGTP.values.astype(float)
    idx = np.arange(len(df))
    tr, te = train_test_split(idx, test_size=0.3, stratify=y, random_state=SEED)

    models = {
        "baseline_base_rate": DummyClassifier(strategy="prior"),
        "logistic": LogisticRegression(C=1.0, max_iter=3000),
        "gradient_boosting": HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                                            min_samples_leaf=50, l2_regularization=1.0,
                                                            random_state=SEED),
    }
    Xs = X.copy()
    Xs["age"] = (Xs["age"] - 40) / 12
    preds, rows = {}, []
    for name, m in models.items():
        Xm = Xs if name == "logistic" else X
        m.fit(Xm.iloc[tr], y[tr], sample_weight=w[tr] / w[tr].mean())
        p = m.predict_proba(Xm.iloc[te])[:, 1]
        preds[name] = p
        thr = np.quantile(p, 0.9) if name != "baseline_base_rate" else None
        for wt_name, ww in (("unweighted", None), ("weighted", w[te])):
            r = metrics(y[te], p, ww, thr)
            r.update({"model": name, "weighting": wt_name})
            rows.append(r)
    met = pd.DataFrame(rows)
    met.to_csv(os.path.join(OUT, "exit_model_metrics.csv"), index=False)
    print(met.round(4).to_string())

    # bootstrap CI for test AUC difference (GBM - logistic) and vs baseline (0.5)
    rng = np.random.default_rng(SEED)
    yt = y[te]
    boots = []
    for _ in range(300):
        b = rng.integers(0, len(te), len(te))
        if yt[b].min() == yt[b].max():
            continue
        boots.append([roc_auc_score(yt[b], preds["logistic"][b]), roc_auc_score(yt[b], preds["gradient_boosting"][b]),
                      average_precision_score(yt[b], preds["logistic"][b]),
                      average_precision_score(yt[b], preds["gradient_boosting"][b])])
    boots = np.array(boots)
    ci = {k: [float(np.percentile(boots[:, i], 2.5)), float(np.percentile(boots[:, i], 97.5))]
          for i, k in enumerate(["auc_logistic", "auc_gbm", "prauc_logistic", "prauc_gbm"])}
    d = boots[:, 1] - boots[:, 0]
    ci["auc_gbm_minus_logistic"] = [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]
    with open(os.path.join(OUT, "exit_model_bootstrap_ci.json"), "w") as f:
        json.dump(ci, f, indent=2)
    print(ci)

    # fairness / subgroup performance (test set, unweighted + weighted)
    best = "gradient_boosting" if met.query("weighting=='unweighted'").set_index("model").loc["gradient_boosting", "roc_auc"] >= \
        met.query("weighting=='unweighted'").set_index("model").loc["logistic", "roc_auc"] else "logistic"
    test = df.iloc[te].copy()
    for name in ("logistic", "gradient_boosting"):
        test[f"p_{name}"] = preds[name]
    fr = []
    for name in ("logistic", "gradient_boosting"):
        thr = np.quantile(preds[name], 0.9)
        for var in ["race_eth", "educ", "age_grp"]:
            for lvl, g in test.groupby(var):
                r = metrics(g.leaver.values, g[f"p_{name}"].values, g.PWGTP.values.astype(float), thr)
                r.update({"model": name, "subgroup_var": var, "level": lvl})
                fr.append(r)
    fr = pd.DataFrame(fr)
    fr["calib_ratio"] = fr.mean_pred / fr.prevalence
    fr.to_csv(os.path.join(OUT, "exit_model_fairness.csv"), index=False)
    print(fr[fr.model == best].round(3).to_string())

    # failure examples: confident misses
    cols = ["group", "AGEP", "race_eth", "educ", "hh_type", "kids", "married", "foreign_born", "origin_county", "YEAR",
            f"p_{best}"]
    fp = test[test.leaver == 0].nlargest(10, f"p_{best}")[cols].assign(failure="high-risk stayer (false positive)")
    fn = test[test.leaver == 1].nsmallest(10, f"p_{best}")[cols].assign(failure="low-risk leaver (false negative)")
    pd.concat([fp, fn]).to_csv(os.path.join(OUT, "exit_model_failure_examples.csv"), index=False)
    # what share of actual out-of-state leavers fall below the median predicted risk
    med = np.median(test[f"p_{best}"])
    miss = test[test.leaver == 1].assign(low=lambda g: g[f"p_{best}"] < med)
    miss.groupby("group").low.mean().rename("share_leavers_below_median_risk").to_csv(
        os.path.join(OUT, "exit_model_missed_leavers_by_destination.csv"))

    # interpretation: logistic odds ratios (full-sample fit, weighted) + weighted exit rates by group
    lr = LogisticRegression(C=1.0, max_iter=3000)
    lr.fit(Xs, y, sample_weight=w / w.mean())
    orr = pd.DataFrame({"feature": Xs.columns, "coef": lr.coef_[0], "odds_ratio": np.exp(lr.coef_[0])})
    orr.sort_values("coef", ascending=False).to_csv(os.path.join(OUT, "exit_model_logistic_odds_ratios.csv"), index=False)
    REP = [f"PWGTP{i}" for i in range(1, 81)]
    er = []
    for var in ["race_eth", "educ", "age_grp", "hh_type", "origin_county"]:
        for lvl, g in df.groupby(var):
            Wg = g[["PWGTP"] + REP].values.astype(float)
            est = (Wg * g.leaver.values[:, None]).sum(0) / Wg.sum(0)
            ec = (Wg * (g.group == "left_ca").values[:, None]).sum(0) / Wg.sum(0)
            er.append({"var": var, "level": lvl, "n": len(g), "n_leavers": int(g.leaver.sum()),
                       "exit_rate": est[0], "exit_rate_se": np.sqrt(4 / 80 * ((est[1:] - est[0]) ** 2).sum()),
                       "left_ca_rate": ec[0], "left_ca_rate_se": np.sqrt(4 / 80 * ((ec[1:] - ec[0]) ** 2).sum())})
    pd.DataFrame(er).to_csv(os.path.join(OUT, "exit_rates_by_group.csv"), index=False)

    # save curves for figures
    np.savez(os.path.join(DATA, "exit_model_test_preds.npz"), y=y[te], w=w[te],
             **{k: v for k, v in preds.items()})


if __name__ == "__main__":
    main()
