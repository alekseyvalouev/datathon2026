"""Side experiment (not in run_all.py): swap LightGBM for a random forest in the E2 turnover rent-jump model.

Same split, features and protocol as s03: tune on validation, refit on train+validation, score 2026 test.
LightGBM and Ridge are refit here with the settings s03 logged, so all models are scored on identical rows.
Note: this is a second look at the test set, made after the s03 result was known."""
import os, json, time, numpy as np, pandas as pd, lightgbm as lgb
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, roc_auc_score, average_precision_score
import s03_model as M
from common import *

# squared-error splits only: the absolute-error forest did not finish in 10 minutes on 12,500 rows.
# LightGBM was tuned with an l1 objective, so on MAE the forest is at a small disadvantage by construction.
REG_GRID = [dict(max_features=mf, min_samples_leaf=ml) for mf in (0.2, 0.33, 0.5) for ml in (5, 20, 50)]
CLF_GRID = [dict(max_features=mf, min_samples_leaf=ml) for mf in ("sqrt", 0.33, 0.5) for ml in (1, 5, 20)]

# median imputation + missing flags (sklearn's forest regressor rejects NaN here)
def _imp(m): return make_pipeline(SimpleImputer(strategy="median", add_indicator=True), m)
def rf_reg(X, y, p, seed=SEED, n=300): return _imp(RandomForestRegressor(n_estimators=n, random_state=seed, n_jobs=-1, **p)).fit(X, y)
def rf_clf(X, y, p, seed=SEED, n=500): return _imp(RandomForestClassifier(n_estimators=n, random_state=seed, n_jobs=-1, **p)).fit(X, y)

def boot_diff(y, a, b, f, B=1000):
    rng = np.random.default_rng(SEED); d = []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y)); d.append(f(y[i], a[i]) - f(y[i], b[i]))
    return np.percentile(d, [2.5, 97.5])

def main():
    S = pd.read_parquet(SAMPLE); S = S[S.r.notna()].reset_index(drop=True)
    tr0, va0, te0 = (S[S.split == k].copy() for k in ["train", "val", "test"])
    log = json.load(open(os.path.join(OUT, "run_log.json")))["val"]
    prm_r, prm_c, alpha, C = log["lgb_reg_params"], log["lgb_clf_params"], log["ridge_alpha"], log["logit_C"]
    tr, (va,) = M.add_features(tr0, [va0]); cols = M.lin_X(tr).columns
    Xtr, Xva = M.lin_X(tr, cols), M.lin_X(va, cols)          # one-hot categoricals
    tune = []
    for p in REG_GRID:
        t = time.time(); mae = mean_absolute_error(va.r, rf_reg(Xtr, tr.r, p).predict(Xva))
        tune.append(dict(task="regression", **p, val_MAE=mae, secs=time.time() - t)); print(tune[-1], flush=True)
    p_r = {k: v for k, v in min(tune, key=lambda d: d["val_MAE"]).items() if k in REG_GRID[0]}
    ctune = [dict(task="over-cap classifier", **p, val_PR_AUC=average_precision_score(va.y_over_cap, rf_clf(Xtr, tr.y_over_cap, p).predict_proba(Xva)[:, 1])) for p in CLF_GRID]
    p_c = {k: v for k, v in max(ctune, key=lambda d: d["val_PR_AUC"]).items() if k in CLF_GRID[0]}
    pd.DataFrame(tune + ctune).round(4).to_csv(os.path.join(OUT, "s08_rf_tuning.csv"), index=False)
    print("chosen:", p_r, p_c, "| val MAE LightGBM", round(log["lgb_reg_mae"], 4), "Ridge", round(log["ridge_mae"], 4))

    fit, (te,) = M.add_features(pd.concat([tr0, va0]), [te0]); cols = M.lin_X(fit).columns
    Xf, Xt = M.lin_X(fit, cols), M.lin_X(te, cols); y = te.r.values; yc = te.y_over_cap.values
    pred = {"LightGBM": lgb.LGBMRegressor(**prm_r).fit(fit[M.LGB_FEATS], fit.r).predict(te[M.LGB_FEATS]),
            "Ridge": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=alpha)).fit(Xf, fit.r).predict(Xt),
            "Random forest": rf_reg(Xf, fit.r, p_r).predict(Xt),
            "ZIP median of train r": M.zip_median_baseline(fit, te)}
    seeds = {"LightGBM": [mean_absolute_error(y, lgb.LGBMRegressor(**{**prm_r, "random_state": s}).fit(fit[M.LGB_FEATS], fit.r).predict(te[M.LGB_FEATS])) for s in range(5)],
             "Random forest": [mean_absolute_error(y, rf_reg(Xf, fit.r, p_r, s).predict(Xt)) for s in range(5)]}
    R = pd.DataFrame([dict(model=k, **M.reg_metrics(y, v), seed_MAE_mean=np.mean(seeds[k]) if k in seeds else np.nan,
                           seed_MAE_sd=np.std(seeds[k]) if k in seeds else np.nan) for k, v in pred.items()])
    mae = lambda yy, pp: np.mean(np.abs(yy - pp))
    for b in ("LightGBM", "Ridge"):
        lo, hi = boot_diff(y, pred["Random forest"], pred[b], mae)
        print(f"MAE random forest minus {b}: {mae(y, pred['Random forest']) - mae(y, pred[b]):+.4f} [{lo:+.4f}, {hi:+.4f}]")
    sc = {"LightGBM classifier": lgb.LGBMClassifier(**prm_c).fit(fit[M.LGB_FEATS], fit.y_over_cap).predict_proba(te[M.LGB_FEATS])[:, 1],
          "Logistic regression (L2)": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C=C, max_iter=2000)).fit(Xf, fit.y_over_cap).predict_proba(Xt)[:, 1],
          "Random forest classifier": rf_clf(Xf, fit.y_over_cap, p_c).predict_proba(Xt)[:, 1]}
    Cc = pd.DataFrame([dict(model=k, AUC=roc_auc_score(yc, v), PR_AUC=average_precision_score(yc, v), mean_pred=v.mean(), prevalence=yc.mean()) for k, v in sc.items()])
    lo, hi = boot_diff(yc, sc["Random forest classifier"], sc["LightGBM classifier"], roc_auc_score)
    print(f"AUC random forest minus LightGBM: {roc_auc_score(yc, sc['Random forest classifier']) - roc_auc_score(yc, sc['LightGBM classifier']):+.4f} [{lo:+.4f}, {hi:+.4f}]")
    R.round(4).to_csv(os.path.join(OUT, "s08_rf_regression_test.csv"), index=False); Cc.round(4).to_csv(os.path.join(OUT, "s08_rf_classification_test.csv"), index=False)
    print(R.round(4).to_string(index=False)); print(Cc.round(4).to_string(index=False))
    # bias by typology group and for San Francisco (the E2 fairness finding)
    te = te.assign(lgbp=pred["LightGBM"], rfp=pred["Random forest"], rdp=pred["Ridge"])
    g = pd.concat([te.groupby("typ_group", observed=True).apply(lambda d: pd.Series(dict(n=len(d), obs=d.r.mean(), bias_lgb=(d.lgbp - d.r).mean(), bias_rf=(d.rfp - d.r).mean(), bias_ridge=(d.rdp - d.r).mean(), MAE_lgb=mae(d.r, d.lgbp), MAE_rf=mae(d.r, d.rfp)))),
                   te.groupby("county").apply(lambda d: pd.Series(dict(n=len(d), obs=d.r.mean(), bias_lgb=(d.lgbp - d.r).mean(), bias_rf=(d.rfp - d.r).mean(), bias_ridge=(d.rdp - d.r).mean(), MAE_lgb=mae(d.r, d.lgbp), MAE_rf=mae(d.r, d.rfp))))])
    g.round(4).to_csv(os.path.join(OUT, "s08_rf_subgroups.csv")); print(g.round(4).to_string())

if __name__ == "__main__":
    main()
