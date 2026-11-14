"""Step 3: baselines + models for the turnover 're-entry price', temporal held-out evaluation, subgroup/fairness
analysis, failure cases, ZIP-level re-entry cost table and figures.
Split by next_start (re-listing date): train < 2025-07-01 <= val < 2026-01-01 <= test.
Hyper-parameters / thresholds are chosen on val only; final models are refit on train+val and scored once on test."""
import os, json, itertools, warnings
import numpy as np, pandas as pd
import lightgbm as lgb
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.model_selection import KFold
from sklearn.metrics import (mean_absolute_error, mean_squared_error, roc_auc_score, average_precision_score,
                             precision_recall_fscore_support, precision_recall_curve)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from common import *
warnings.filterwarnings("ignore")

NUM = ["beds", "baths", "sqft", "age", "lat", "lon", "start_gap_y", "log_last_p", "ppsf", "rel_zip_rent", "rel_zip_ppsf",
       "n_changes", "prev_cut", "prev_year", "next_month", "ep", "mgmt", "large_landlord", "sold_between",
       "mkt_chg", "mkt_mom", "zip_te", "county_te", "zip_te_cap"]
CAT = ["homeType", "typ_group"]
LGB_FEATS = NUM + CAT

# ---------------------------------------------------------------- feature engineering (fit on "fit" rows only)
def te_fit(fit, col, y, k=20):
    g = fit.groupby(col)[y].agg(["mean", "size"]); m = fit[y].mean()
    return ((g["mean"] * g["size"] + m * k) / (g["size"] + k)).to_dict(), m

def add_features(fit, others):
    """Target encodings + ZIP-relative rent computed on `fit`; out-of-fold TE inside `fit` to avoid leakage."""
    fit = fit.copy(); others = [o.copy() for o in others]
    zmed = fit.groupby("zipcode").apply(lambda d: (d.log_last_p - d.mkt_lvl0.fillna(0)).median()).to_dict()
    zppsf = fit.groupby("zipcode").ppsf.median().to_dict()
    gm, gp = (fit.log_last_p - fit.mkt_lvl0.fillna(0)).median(), fit.ppsf.median()
    for d in [fit] + others:
        d["rel_zip_rent"] = d.log_last_p - d.mkt_lvl0.fillna(0) - d.zipcode.map(zmed).fillna(gm)
        d["rel_zip_ppsf"] = np.log(d.ppsf / d.zipcode.map(zppsf).fillna(gp)).replace([np.inf, -np.inf], np.nan)
    specs = [("zip_te", "zipcode", "r"), ("county_te", "county", "r"), ("zip_te_cap", "zipcode", "y_over_cap")]
    for name, col, y in specs:
        mp, m = te_fit(fit, col, y)
        for d in others: d[name] = d[col].map(mp).fillna(m)
        oof = np.zeros(len(fit))
        for tr, te in KFold(5, shuffle=True, random_state=SEED).split(fit):
            mp2, m2 = te_fit(fit.iloc[tr], col, y)
            oof[te] = fit.iloc[te][col].map(mp2).fillna(m2).values
        fit[name] = oof
    for d in [fit] + others:
        for c in CAT: d[c] = pd.Categorical(d[c].fillna("NA"), categories=sorted(set(fit[c].fillna("NA")) | {"NA"}))
    return fit, others

def lin_X(d, cols=None):
    X = pd.concat([d[NUM].astype(float), pd.get_dummies(d[CAT], dtype=float)], axis=1).replace([np.inf, -np.inf], np.nan)
    return X if cols is None else X.reindex(columns=cols, fill_value=0.0)

# ---------------------------------------------------------------- metrics
def reg_metrics(y, p):
    return dict(MAE=mean_absolute_error(y, p), RMSE=mean_squared_error(y, p) ** 0.5, bias=float(np.mean(p - y)))

def clf_metrics(y, s, thr):
    out = dict(AUC=roc_auc_score(y, s) if len(set(y)) > 1 else np.nan, PR_AUC=average_precision_score(y, s))
    pr, rc, f1, _ = precision_recall_fscore_support(y, (s >= thr).astype(int), average="binary", zero_division=0)
    out.update(precision=pr, recall=rc, F1=f1, thr=thr)
    return out

def best_f1_thr(y, s):
    p, r, t = precision_recall_curve(y, s)
    f = 2 * p * r / np.clip(p + r, 1e-9, None)
    return float(t[np.argmax(f[:-1])])

# ---------------------------------------------------------------- models
def tune_lgb_reg(tr, va):
    best = None
    for obj, nl, mcs, lr in itertools.product(["l2", "huber", "l1"], [15, 31, 63], [20, 100], [0.03]):
        prm = dict(objective=obj, num_leaves=nl, min_child_samples=mcs, learning_rate=lr, n_estimators=2000,
                   subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, random_state=SEED, deterministic=True, force_row_wise=True, n_jobs=4)
        if obj == "huber": prm["alpha"] = 0.05
        m = lgb.LGBMRegressor(**prm).fit(tr[LGB_FEATS], tr.r, eval_set=[(va[LGB_FEATS], va.r)], eval_metric="l1",
                                         callbacks=[lgb.early_stopping(100, verbose=False)])
        mae = mean_absolute_error(va.r, m.predict(va[LGB_FEATS]))
        if best is None or mae < best[0]: best = (mae, {**prm, "n_estimators": max(m.best_iteration_, 50)})
    return best

def tune_lgb_clf(tr, va):
    best = None
    for nl, mcs in itertools.product([15, 31, 63], [20, 100]):
        prm = dict(objective="binary", num_leaves=nl, min_child_samples=mcs, learning_rate=0.03, n_estimators=2000,
                   subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, random_state=SEED, deterministic=True, force_row_wise=True, n_jobs=4)
        m = lgb.LGBMClassifier(**prm).fit(tr[LGB_FEATS], tr.y_over_cap, eval_set=[(va[LGB_FEATS], va.y_over_cap)],
                                          eval_metric="average_precision", callbacks=[lgb.early_stopping(100, verbose=False)])
        ap = average_precision_score(va.y_over_cap, m.predict_proba(va[LGB_FEATS])[:, 1])
        if best is None or ap > best[0]: best = (ap, {**prm, "n_estimators": max(m.best_iteration_, 50)})
    return best

def tune_ridge(tr, va, cols):
    res = []
    for a in [0.1, 1, 10, 100, 1000]:
        m = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=a)).fit(lin_X(tr, cols), tr.r)
        res.append((mean_absolute_error(va.r, m.predict(lin_X(va, cols))), a))
    return min(res)

def tune_logit(tr, va, cols):
    res = []
    for C in [0.001, 0.01, 0.1, 1]:
        m = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                          LogisticRegression(C=C, max_iter=2000)).fit(lin_X(tr, cols), tr.y_over_cap)
        res.append((average_precision_score(va.y_over_cap, m.predict_proba(lin_X(va, cols))[:, 1]), C))
    return max(res)

# ---------------------------------------------------------------- baselines
def zip_median_baseline(fit, d):
    zm, cm, g = fit.groupby("zipcode").r.median(), fit.groupby("county").r.median(), fit.r.median()
    n = fit.zipcode.value_counts()
    zm = zm[n.reindex(zm.index) >= 10]
    return d.zipcode.map(zm).fillna(d.county.map(cm)).fillna(g).values

def legal_cap_baseline(d):
    return np.array([ab1482_cap(int(s[:4])) for s in d.next_start])

def zip_rate_baseline(fit, d):
    mp, m = te_fit(fit, "zipcode", "y_over_cap"); return d.zipcode.map(mp).fillna(m).values

# ---------------------------------------------------------------- main
def main():
    S = pd.read_parquet(SAMPLE)
    S = S[S.r.notna()].reset_index(drop=True)
    tr0, va0, te0 = (S[S.split == k].copy() for k in ["train", "val", "test"])
    log = {}
    # ----- tuning stage: features fit on train, evaluated on val
    tr, (va,) = add_features(tr0, [va0])
    cols = lin_X(tr).columns
    mae_l, prm_r = tune_lgb_reg(tr, va); ap_l, prm_c = tune_lgb_clf(tr, va)
    mae_rd, alpha = tune_ridge(tr, va, cols); ap_lr, C = tune_logit(tr, va, cols)
    log["val"] = dict(lgb_reg_mae=mae_l, lgb_reg_params=prm_r, lgb_clf_ap=ap_l, lgb_clf_params=prm_c,
                      ridge_mae=mae_rd, ridge_alpha=alpha, logit_ap=ap_lr, logit_C=C,
                      zipmed_mae=mean_absolute_error(va.r, zip_median_baseline(tr, va)))
    # thresholds chosen on val (models fit on train only)
    mc = lgb.LGBMClassifier(**prm_c).fit(tr[LGB_FEATS], tr.y_over_cap)
    ml = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C=C, max_iter=2000)).fit(lin_X(tr, cols), tr.y_over_cap)
    thr = dict(lgb=best_f1_thr(va.y_over_cap, mc.predict_proba(va[LGB_FEATS])[:, 1]),
               logit=best_f1_thr(va.y_over_cap, ml.predict_proba(lin_X(va, cols))[:, 1]),
               ziprate=best_f1_thr(va.y_over_cap, zip_rate_baseline(tr, va)))
    log["thresholds_from_val"] = thr
    print(json.dumps(log, indent=1, default=str))

    # ----- final: refit on train+val, score test once
    fit0 = pd.concat([tr0, va0])
    fit, (te,) = add_features(fit0, [te0])
    cols = lin_X(fit).columns
    reg = lgb.LGBMRegressor(**prm_r).fit(fit[LGB_FEATS], fit.r)
    rid = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=alpha)).fit(lin_X(fit, cols), fit.r)
    clf = lgb.LGBMClassifier(**prm_c).fit(fit[LGB_FEATS], fit.y_over_cap)
    lgt = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C=C, max_iter=2000)).fit(lin_X(fit, cols), fit.y_over_cap)
    te["pred_lgb"] = reg.predict(te[LGB_FEATS]); te["pred_ridge"] = rid.predict(lin_X(te, cols))
    te["pred_zipmed"] = zip_median_baseline(fit, te); te["pred_cap"] = legal_cap_baseline(te)
    te["pred_zero"] = 0.0; te["pred_mkt"] = te.mkt_chg.fillna(fit.r.median())
    te["s_lgb"] = clf.predict_proba(te[LGB_FEATS])[:, 1]; te["s_logit"] = lgt.predict_proba(lin_X(te, cols))[:, 1]
    te["s_ziprate"] = zip_rate_baseline(fit, te)

    # sensitivity: train-only fit (no val in training) for the LGB regressor / classifier
    trS, (teS,) = add_features(tr0, [te0])
    mae_trainonly = mean_absolute_error(teS.r, lgb.LGBMRegressor(**prm_r).fit(trS[LGB_FEATS], trS.r).predict(teS[LGB_FEATS]))
    ap_trainonly = average_precision_score(teS.y_over_cap, lgb.LGBMClassifier(**prm_c).fit(trS[LGB_FEATS], trS.y_over_cap).predict_proba(teS[LGB_FEATS])[:, 1])

    # ----- regression table
    R = []
    for name, col in [("Zero change (no jump)", "pred_zero"), ("Legal rule: CPI+5% capped 10%", "pred_cap"),
                      ("County market index change", "pred_mkt"), ("ZIP median of train r", "pred_zipmed"),
                      ("Ridge (regularized linear)", "pred_ridge"), ("LightGBM", "pred_lgb")]:
        R.append(dict(model=name, **reg_metrics(te.r, te[col])))
    R = pd.DataFrame(R); R.to_csv(os.path.join(OUT, "metrics_regression_test.csv"), index=False)
    # log-ratio target variant (LightGBM on logr, same params) for robustness
    reg_log = lgb.LGBMRegressor(**prm_r).fit(fit[LGB_FEATS], fit.logr)
    te["pred_lgb_log"] = np.expm1(reg_log.predict(te[LGB_FEATS]))
    # ----- classification table
    prev = te.y_over_cap.mean()
    C_ = [dict(model="Majority class (never over cap)", AUC=0.5, PR_AUC=prev, precision=0.0, recall=0.0, F1=0.0, thr=np.nan),
          dict(model="ZIP over-cap rate (train)", **clf_metrics(te.y_over_cap, te.s_ziprate, thr["ziprate"])),
          dict(model="Logistic regression (L2)", **clf_metrics(te.y_over_cap, te.s_logit, thr["logit"])),
          dict(model="LightGBM classifier", **clf_metrics(te.y_over_cap, te.s_lgb, thr["lgb"]))]
    # "legal rule" for classification: flag if regression model predicts above cap
    C_.append(dict(model="LightGBM regressor: pred r > 10%", **clf_metrics(te.y_over_cap, te.pred_lgb, CAP)))
    C_ = pd.DataFrame(C_); C_.to_csv(os.path.join(OUT, "metrics_classification_test.csv"), index=False)
    print(R.round(4).to_string(index=False)); print(C_.round(3).to_string(index=False))
    log["test"] = dict(n=len(te), prevalence=prev, mean_r=te.r.mean(), median_r=te.r.median(),
                       lgb_logtarget_mae=mean_absolute_error(te.r, te.pred_lgb_log),
                       lgb_trainonly_mae=mae_trainonly, lgb_trainonly_ap=ap_trainonly,
                       train_mean_r=fit0.r.mean(), train_prev=fit0.y_over_cap.mean())
    # robustness: target with next_last (final ask of next episode) instead of first ask
    rl = (te.next_last / te.last_p) ** (1 / te.start_gap_y) - 1
    log["robustness"] = dict(median_r_next_first=te.r.median(), median_r_next_last=float(rl.median()),
                             share_over_cap_next_last=float((rl > CAP).mean()))

    # ----- subgroups
    q = fit0.last_p.quantile([.25, .5, .75]).values
    te["rent_quartile"] = pd.cut(te.last_p, [-np.inf, *q, np.inf], labels=["Q1 lowest", "Q2", "Q3", "Q4 highest"])
    te["landlord"] = np.where(te.large_landlord == 1, "large mgmt co", np.where(te.mgmt == 1, "other mgmt co", "not mgmt co"))
    te["homeType_s"] = te.homeType.astype(str)
    te["typology"] = te.typology.fillna("NA"); te["typ_group_s"] = te.typ_group.astype(str)
    rows = []
    for gcol in ["county", "rent_quartile", "homeType_s", "typ_group_s", "typology", "landlord"]:
        for g, d in te.groupby(gcol, observed=True):
            if len(d) < 30: continue
            yb = d.y_over_cap
            rows.append(dict(group_set=gcol.replace("_s", ""), group=g, n=len(d), obs_mean_r=d.r.mean(), pred_mean_r=d.pred_lgb.mean(),
                             bias_lgb=(d.pred_lgb - d.r).mean(), MAE_lgb=mean_absolute_error(d.r, d.pred_lgb),
                             MAE_zipmed=mean_absolute_error(d.r, d.pred_zipmed), MAE_cap=mean_absolute_error(d.r, d.pred_cap),
                             obs_over_cap=yb.mean(), flagged_rate=(d.s_lgb >= thr["lgb"]).mean(),
                             recall=((d.s_lgb >= thr["lgb"]) & (yb == 1)).sum() / max(yb.sum(), 1),
                             AUC=roc_auc_score(yb, d.s_lgb) if yb.nunique() > 1 else np.nan,
                             under_pred_big_jumps=(d.pred_lgb[yb == 1] - d.r[yb == 1]).mean() if yb.sum() else np.nan))
    G = pd.DataFrame(rows); G.to_csv(os.path.join(OUT, "subgroup_metrics_test.csv"), index=False)
    print(G.round(3).to_string(index=False))

    # ----- 10 worst failures (no addresses: the address column is never loaded)
    te["abs_err"] = (te.pred_lgb - te.r).abs()
    W = te.nlargest(10, "abs_err")[["zpid", "county", "zipcode", "homeType_s", "beds", "sqft", "last_p", "next_first", "next_last",
                                    "start_d", "next_start", "start_gap_y", "n_changes", "mgmt", "sold_between", "typology",
                                    "r", "pred_lgb", "abs_err"]]
    W["last_p"] = (W.last_p / 250).round() * 250; W["next_first"] = (W.next_first / 250).round() * 250   # coarsen
    W["next_last"] = (W.next_last / 250).round() * 250
    W.to_csv(os.path.join(OUT, "worst_failures_test.csv"), index=False)
    print(W.round(3).to_string(index=False))
    # aggregate view of large errors (top 2% abs error) vs rest
    big = te.abs_err >= te.abs_err.quantile(0.98)
    agg = pd.DataFrame({"top2pct_errors": te[big][["start_gap_y", "n_changes", "mgmt", "sold_between", "last_p"]].mean(),
                        "rest": te[~big][["start_gap_y", "n_changes", "mgmt", "sold_between", "last_p"]].mean()})
    agg.loc["share_APARTMENT"] = [(te[big].homeType_s == "APARTMENT").mean(), (te[~big].homeType_s == "APARTMENT").mean()]
    agg.loc["share_r_negative"] = [(te[big].r < 0).mean(), (te[~big].r < 0).mean()]
    agg.to_csv(os.path.join(OUT, "failure_profile_test.csv"))

    # ----- feature importance
    imp = pd.Series(reg.booster_.feature_importance("gain"), index=LGB_FEATS).sort_values(ascending=False)
    (imp / imp.sum()).rename("gain_share").to_csv(os.path.join(OUT, "feature_importance_lgb_reg.csv"))

    # ----- ZIP-level re-entry cost (test period = relistings in 2026: out-of-sample predictions)
    cpi = np.array([CPI.get(int(s[:4]), 2.6) / 100 for s in te.next_start])
    capv = te.pred_cap.values
    te["stay_rent_cpi"] = te.last_p * (1 + cpi) ** te.start_gap_y          # typical in-place path (rent rises with CPI)
    te["stay_rent_cap"] = te.last_p * (1 + capv) ** te.start_gap_y         # maximum legal in-place path under AB 1482
    te["prem_obs"] = te.next_first - te.stay_rent_cpi
    te["prem_obs_vs_cap"] = te.next_first - te.stay_rent_cap
    te["pred_next"] = te.last_p * (1 + te.pred_lgb) ** te.start_gap_y
    te["prem_pred"] = te.pred_next - te.stay_rent_cpi
    te["over_cap_pred"] = (te.s_lgb >= thr["lgb"]).astype(int)
    Z = te.groupby("zipcode").agg(county=("county", lambda s: s.mode().iloc[0]), city_n=("city", "nunique"),
                                  lat=("lat", "mean"), lon=("lon", "mean"), n_turnovers=("r", "size"),
                                  median_prev_rent=("last_p", "median"), median_next_rent=("next_first", "median"),
                                  obs_median_jump_annual=("r", "median"), pred_median_jump_annual=("pred_lgb", "median"),
                                  obs_median_premium_month_vs_cpi=("prem_obs", "median"),
                                  pred_median_premium_month_vs_cpi=("prem_pred", "median"),
                                  obs_median_premium_month_vs_legal_max=("prem_obs_vs_cap", "median"),
                                  obs_share_over_10pct_cap=("y_over_cap", "mean"), pred_share_over_10pct_cap=("over_cap_pred", "mean"),
                                  pred_mean_prob_over_cap=("s_lgb", "mean"), median_gap_years=("start_gap_y", "median")).reset_index()
    Z = Z.drop(columns="city_n")
    Z["low_n_flag"] = Z.n_turnovers < 20
    Z = Z.sort_values("obs_median_jump_annual", ascending=False)
    Z.round(4).to_csv(os.path.join(OUT, "zip_reentry_cost.csv"), index=False)
    Zr = Z[~Z.low_n_flag]
    print(Zr.head(10).round(3).to_string(index=False)); print(Zr.tail(10).round(3).to_string(index=False))
    log["zip"] = dict(n_zips=len(Z), n_zips_n20=len(Zr),
                      corr_pred_obs_median=float(Zr[["obs_median_jump_annual", "pred_median_jump_annual"]].corr().iloc[0, 1]),
                      corr_pred_obs_share=float(Zr[["obs_share_over_10pct_cap", "pred_share_over_10pct_cap"]].corr().iloc[0, 1]),
                      overall_median_premium_month=float(te.prem_obs.median()),
                      overall_mean_premium_month=float(te.prem_obs.mean()))
    json.dump(log, open(os.path.join(OUT, "run_log.json"), "w"), indent=1, default=str)
    te.drop(columns=[c for c in te.columns if c in ("lat", "lon")]).to_parquet(os.path.join(OUT, "test_predictions.parquet"), index=False)
    figures(te, R, C_, G, Z, imp, thr)

# ---------------------------------------------------------------- figures
BLUE, ORANGE, RED, GRAY, INK, INK2 = "#2a78d6", "#eb6834", "#e34948", "#f0efec", "#0b0b0b", "#52514e"
DIV = LinearSegmentedColormap.from_list("div", [BLUE, GRAY, RED])
def style(ax):
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]: ax.spines[s].set_color("#b5b4ae")
    ax.tick_params(colors=INK2, labelsize=9); ax.grid(color="#e8e7e3", lw=0.6); ax.set_axisbelow(True)

def figures(te, R, C_, G, Z, imp, thr):
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold", "text.color": INK,
                         "axes.labelcolor": INK2, "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})
    # 1. ZIP map: observed and predicted median annual jump
    Zr = Z[~Z.low_n_flag]
    fig, axs = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)
    norm = TwoSlopeNorm(vmin=-0.05, vcenter=0.0, vmax=0.15)
    for ax, col, t in [(axs[0], "obs_median_jump_annual", "Observed median jump, 2026 relistings"),
                       (axs[1], "pred_median_jump_annual", "LightGBM predicted (out-of-sample)")]:
        ax.scatter(Z[Z.low_n_flag].lon, Z[Z.low_n_flag].lat, s=8, c="#d6d5d0", lw=0, label="ZIP with <20 turnovers")
        sc = ax.scatter(Zr.lon, Zr.lat, s=np.clip(Zr.n_turnovers, 20, 400) * 0.6, c=Zr[col].clip(-0.05, 0.15), cmap=DIV, norm=norm,
                        edgecolors="#fcfcfb", linewidths=1.0)
        ax.set_title(t, loc="left"); style(ax); ax.set_xlabel("longitude"); ax.set_aspect(1.25)
        ax.set_xticks([-123.5, -123.0, -122.5, -122.0, -121.5])
    axs[0].set_ylabel("latitude"); axs[0].legend(loc="lower left", frameon=False, fontsize=8)
    cb = fig.colorbar(sc, ax=axs, shrink=0.7, pad=0.02); cb.set_label("annualized rent change at turnover (10% = AB 1482 max)")
    cb.ax.axhline(0.10, color=INK, lw=1.5)
    fig.suptitle("Re-entry price by ZIP: annualized rent change when the same unit is re-rented (dot size = # turnovers)",
                 x=0.02, ha="left", fontsize=12)
    fig.savefig(os.path.join(FIG, "map_zip_reentry_jump.png"), dpi=150, bbox_inches="tight"); plt.close(fig)
    # 1b. map of share over cap
    fig, ax = plt.subplots(figsize=(7, 6.5))
    sc = ax.scatter(Zr.lon, Zr.lat, s=np.clip(Zr.n_turnovers, 20, 400) * 0.6, c=Zr.obs_share_over_10pct_cap,
                    cmap=LinearSegmentedColormap.from_list("seq", ["#dbe8f8", BLUE, "#0d3a73"]), vmin=0, vmax=0.5,
                    edgecolors="#fcfcfb", linewidths=1.0)
    style(ax); ax.set_aspect(1.25); ax.set_title("Share of 2026 turnovers above 10%/yr (AB 1482 max)", loc="left"); ax.set_xticks([-123.5, -123.0, -122.5, -122.0, -121.5])
    fig.colorbar(sc, ax=ax, shrink=0.7).set_label("share of turnovers above cap")
    fig.savefig(os.path.join(FIG, "map_zip_share_over_cap.png"), dpi=150, bbox_inches="tight"); plt.close(fig)
    # 2. metrics vs baselines
    fig, axs = plt.subplots(1, 2, figsize=(12, 4))
    r = R.iloc[::-1]; ax = axs[0]
    ax.barh(r.model, r.MAE * 100, color=[BLUE if "LightGBM" in m or "Ridge" in m else "#b5b4ae" for m in r.model], height=0.6)
    for i, v in enumerate(r.MAE * 100): ax.text(v + 0.05, i, f"{v:.2f}", va="center", fontsize=9, color=INK)
    ax.set_xlabel("test MAE (percentage points of annual rent change)"); ax.set_title("Regression: lower is better", loc="left"); style(ax)
    c = C_.iloc[::-1]; ax = axs[1]
    ax.barh(c.model, c.PR_AUC, color=[BLUE if ("LightGBM" in m or "Logistic" in m) else "#b5b4ae" for m in c.model], height=0.6)
    for i, v in enumerate(c.PR_AUC): ax.text(v + 0.005, i, f"{v:.3f}", va="center", fontsize=9, color=INK)
    ax.set_xlabel("test PR-AUC (r > 10%/yr)"); ax.set_title("Classification: higher is better", loc="left"); style(ax)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "metrics_vs_baselines.png"), dpi=150); plt.close(fig)
    # 3. subgroup bias
    sets = ["county", "rent_quartile", "homeType", "typ_group", "landlord"]
    g = G[G.group_set.isin(sets)].copy(); g["label"] = g.group_set + ": " + g.group.astype(str)
    fig, ax = plt.subplots(figsize=(8, 0.28 * len(g) + 1))
    y = np.arange(len(g))[::-1]
    ax.scatter(g.obs_mean_r * 100, y, color=ORANGE, s=40, label="observed mean", zorder=3, edgecolors="#fcfcfb")
    ax.scatter(g.pred_mean_r * 100, y, color=BLUE, s=40, label="LightGBM predicted mean", zorder=3, edgecolors="#fcfcfb")
    for yy, a, b in zip(y, g.obs_mean_r * 100, g.pred_mean_r * 100): ax.plot([a, b], [yy, yy], color="#b5b4ae", lw=1.5, zorder=2)
    ax.set_yticks(y); ax.set_yticklabels(g.label, fontsize=8); ax.axvline(10, color=INK2, ls="--", lw=1)
    ax.text(10.1, y.max(), "AB 1482 max", fontsize=8, color=INK2, va="top")
    ax.set_xlabel("annualized turnover rent change, % (test = 2026 relistings)"); style(ax)
    ax.set_title("2026 test: observed vs predicted mean jump by subgroup", loc="left"); ax.legend(frameon=False, loc="lower right")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "subgroup_bias.png"), dpi=150); plt.close(fig)
    # 4. calibration by decile of prediction
    te = te.copy(); te["dec"] = pd.qcut(te.pred_lgb, 10, labels=False, duplicates="drop")
    c = te.groupby("dec").agg(p=("pred_lgb", "mean"), o=("r", "mean"), om=("r", "median"))
    fig, ax = plt.subplots(figsize=(5.5, 5))
    lim = [min(c.p.min(), c.o.min()) * 100 - 1, max(c.p.max(), c.o.max()) * 100 + 1]
    ax.plot(lim, lim, color="#b5b4ae", lw=1, ls="--"); ax.plot(c.p * 100, c.o * 100, "-o", color=BLUE, lw=2, ms=6, label="mean")
    ax.plot(c.p * 100, c.om * 100, "-o", color=ORANGE, lw=2, ms=6, label="median")
    ax.set_xlabel("predicted annual jump, % (decile mean)"); ax.set_ylabel("observed annual jump, %"); style(ax)
    ax.set_title("Calibration on 2026 test set", loc="left"); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "calibration_test.png"), dpi=150); plt.close(fig)
    # 5. feature importance
    i = (imp / imp.sum()).head(15)[::-1]
    fig, ax = plt.subplots(figsize=(6, 5)); ax.barh(i.index, i.values, color=BLUE, height=0.6); style(ax)
    ax.set_xlabel("share of total split gain"); ax.set_title("LightGBM regressor: top features", loc="left")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "feature_importance.png"), dpi=150); plt.close(fig)

if __name__ == "__main__":
    main()
