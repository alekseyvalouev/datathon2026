"""Robustness 3: drift handling.
(a) Recent-market features: trailing 6-month (183-day) median observed jump r of OTHER turnover pairs in the same ZIP
    (needs >= 5 pairs) and county (>= 10 pairs), plus the county share over 10%, using only pairs re-listed STRICTLY
    before this pair's next_start (a pair's r is known on its own re-listing date: it needs only the prior rent and the
    first new ask). For test rows this is an online/rolling feature: a Nov-2026 prediction uses realized jumps from
    May-Oct 2026. A 'frozen' variant computes test rows' features as of 2026-01-01 (no 2026 outcomes at all).
    LightGBM/Ridge/classifier hyper-parameters are re-tuned on val with the new feature set (same grid as s03).
(b) Recalibration on the last validation quarter (2025-Q4): the base model is fit on pairs re-listed before
    2025-10-01, a linear map r ~ a + b*pred (OLS) and a median shift are fit on 2025-Q4 predictions, and applied to the
    2026 test predictions. Classifier: Platt scaling on 2025-Q4. Test is never used to choose anything.
Outputs: outputs/robustness/drift_metrics_test.csv, drift_subgroup_bias_test.csv, drift_calibration_deciles.csv,
drift_recalibration_params.csv; figs/robustness/calibration_before_after.png."""
from robustness_common import *
from sklearn.linear_model import LinearRegression

REC = ["rec_zip_r6", "rec_zip_n6", "rec_cnty_r6", "rec_cnty_cap6"]
Q4 = "2025-10-01"

def trailing(S, key, asof, days=183, min_n=5):
    """Median r / share over cap of pairs in the same `key` group with next_start in [asof - days, asof)."""
    t = pd.to_datetime(S.next_start).values.astype("datetime64[D]").astype(np.int64)
    a = pd.to_datetime(asof).values.astype("datetime64[D]").astype(np.int64)
    med, n, cap = np.full(len(S), np.nan), np.zeros(len(S)), np.full(len(S), np.nan)
    for _, idx in S.groupby(key).indices.items():
        o = idx[np.argsort(t[idx], kind="mergesort")]; ts = t[o]; rv = S.r.values[o]; cv = S.y_over_cap.values[o]
        lo = np.searchsorted(ts, a[idx] - days, "left"); hi = np.searchsorted(ts, a[idx], "left")   # strictly before asof
        for i, l, h in zip(idx, lo, hi):
            n[i] = h - l
            if h - l >= min_n: med[i] = np.median(rv[l:h]); cap[i] = cv[l:h].mean()
    return med, n, cap

def add_recent(S, frozen_test=False):
    S = S.copy()
    asof = S.next_start.copy()
    if frozen_test: asof = np.where(S.split == "test", np.minimum(S.next_start, VAL_END), S.next_start)
    asof = pd.Series(asof, index=S.index)
    S["rec_zip_r6"], S["rec_zip_n6"], _ = trailing(S, "zipcode", asof, min_n=5)
    S["rec_cnty_r6"], _, S["rec_cnty_cap6"] = trailing(S, "county", asof, min_n=10)
    return S

def with_feats(num, fn, *a):
    """Run an s03 tuning function with a different numeric feature list (s03 reads module globals)."""
    old = M.NUM, M.LGB_FEATS
    M.NUM, M.LGB_FEATS = num, num + M.CAT
    try: return fn(*a)
    finally: M.NUM, M.LGB_FEATS = old

def decile_calib(y, p, label):
    d = pd.DataFrame({"y": y, "p": p}); d["dec"] = pd.qcut(d.p.rank(method="first"), 10, labels=False)
    c = d.groupby("dec").agg(pred_mean=("p", "mean"), obs_mean=("y", "mean"), obs_median=("y", "median"), n=("y", "size")).reset_index()
    c["model"] = label; return c

def main():
    S = load_sample()
    S = add_recent(S); Sf = add_recent(S, frozen_test=True)
    print(S.groupby("split")[REC].apply(lambda d: d.notna().mean()).round(3))
    NUM1 = M.NUM + REC
    p_r0, p_c0, a0, C0, thr0 = tuned()
    # ----- tuning for the new feature set (train -> val), same grids as s03
    tr, (va,) = M.add_features(S[S.split == "train"], [S[S.split == "val"]])
    mae1, p_r1 = with_feats(NUM1, M.tune_lgb_reg, tr, va); ap1, p_c1 = with_feats(NUM1, M.tune_lgb_clf, tr, va)
    cols1 = lin_X(tr, NUM1).columns
    rmae1, a1 = with_feats(NUM1, M.tune_ridge, tr, va, cols1); lap1, C1 = with_feats(NUM1, M.tune_logit, tr, va, cols1)
    tune = dict(val_mae_lgb_recent=mae1, val_mae_ridge_recent=rmae1, val_ap_lgb_recent=ap1, val_ap_logit_recent=lap1,
                lgb_reg=p_r1, lgb_clf=p_c1, ridge_alpha=a1, logit_C=C1)
    print(json.dumps(tune, indent=1, default=str)); json.dump(tune, open(os.path.join(ROUT, "drift_tuning_val.json"), "w"), indent=1, default=str)
    cfg = {"M0": dict(num=M.NUM, prm_r=p_r0, prm_c=p_c0, alpha=a0, C=C0), "M1": dict(num=NUM1, prm_r=p_r1, prm_c=p_c1, alpha=a1, C=C1)}

    # ----- final fits on train+val, scored on test
    preds = {}
    def final(Sx, name, c):
        fit, (te,) = M.add_features(Sx[Sx.split != "test"], [Sx[Sx.split == "test"]])
        p = fit_predict(fit, te, **c)
        for k, v in p.items(): preds[f"{name}_{k}"] = v
        return te
    te = final(S, "M0", cfg["M0"]); final(S, "M1", cfg["M1"]); final(Sf, "M1frozen", cfg["M1"])
    # ----- recalibration path: fit < 2025-10-01, calibrate on 2025-Q4, apply to test
    recal_params = []
    for name, c in cfg.items():
        fitR0 = S[S.next_start < Q4]; q40 = S[(S.next_start >= Q4) & (S.split == "val")]; te0 = S[S.split == "test"]
        fitR, (q4, teR) = M.add_features(fitR0, [q40, te0])
        pq = fit_predict(fitR, q4, **c); pt = fit_predict(fitR, teR, **c)
        for mk in ["lgb", "ridge"]:
            lr = LinearRegression().fit(pq[mk].reshape(-1, 1), q4.r.values)
            shift = float(np.median(q4.r.values - pq[mk]))
            preds[f"{name}pre_{mk}"] = pt[mk]
            preds[f"{name}pre_{mk}_recal_lin"] = lr.predict(pt[mk].reshape(-1, 1))
            preds[f"{name}pre_{mk}_recal_shift"] = pt[mk] + shift
            recal_params.append(dict(model=f"{name} {mk}", n_q4=len(q4), q4_mean_r=q4.r.mean(), q4_mean_pred=pq[mk].mean(),
                                     intercept=lr.intercept_, slope=lr.coef_[0], median_shift=shift))
        for mk in ["clf", "logit"]:
            z = lambda s: np.log(np.clip(s, 1e-6, 1 - 1e-6) / (1 - np.clip(s, 1e-6, 1 - 1e-6))).reshape(-1, 1)
            pl = LogisticRegression(C=1e6).fit(z(pq[mk]), q4.y_over_cap.values)
            preds[f"{name}pre_{mk}"] = pt[mk]; preds[f"{name}pre_{mk}_recal_platt"] = pl.predict_proba(z(pt[mk]))[:, 1]
            recal_params.append(dict(model=f"{name} {mk} (Platt)", n_q4=len(q4), q4_mean_r=q4.y_over_cap.mean(),
                                     q4_mean_pred=pq[mk].mean(), intercept=pl.intercept_[0], slope=pl.coef_[0][0]))
    pd.DataFrame(recal_params).to_csv(os.path.join(ROUT, "drift_recalibration_params.csv"), index=False)
    P = pd.DataFrame(preds); te = te.reset_index(drop=True)
    T = pd.read_parquet(os.path.join(OUT, "test_predictions.parquet"))[["zpid", "ep", "pred_lgb", "pred_zipmed", "pred_cap", "s_lgb"]]
    te = pd.concat([te, P], axis=1).merge(T, on=["zpid", "ep"], how="left")
    assert np.allclose(te.M0_lgb, te.pred_lgb), "M0 refit must reproduce s03 predictions"

    # ----- metrics
    LAB = {"pred_zipmed": "ZIP median of train r", "pred_cap": "Legal rule",
           "M0_lgb": "LightGBM (s03, train+val)", "M0_ridge": "Ridge (s03, train+val)",
           "M1_lgb": "LightGBM + recent-market (rolling)", "M1_ridge": "Ridge + recent-market (rolling)",
           "M1frozen_lgb": "LightGBM + recent-market (frozen at 2026-01-01)", "M1frozen_ridge": "Ridge + recent-market (frozen)",
           "M0pre_lgb": "LightGBM fit <2025-10, raw", "M0pre_lgb_recal_lin": "LightGBM fit <2025-10, recal linear (Q4)",
           "M0pre_lgb_recal_shift": "LightGBM fit <2025-10, recal shift (Q4)",
           "M0pre_ridge": "Ridge fit <2025-10, raw", "M0pre_ridge_recal_lin": "Ridge fit <2025-10, recal linear (Q4)",
           "M1pre_lgb": "LightGBM+recent fit <2025-10, raw", "M1pre_lgb_recal_lin": "LightGBM+recent fit <2025-10, recal linear (Q4)",
           "M1pre_lgb_recal_shift": "LightGBM+recent fit <2025-10, recal shift (Q4)",
           "M1pre_ridge": "Ridge+recent fit <2025-10, raw", "M1pre_ridge_recal_lin": "Ridge+recent fit <2025-10, recal linear (Q4)"}
    R = pd.DataFrame([dict(model=v, key=k, **reg_row(te.r, te[k])) for k, v in LAB.items()])
    CL = {"M0_clf": "LightGBM clf (s03)", "M0_logit": "Logistic (s03)", "M1_clf": "LightGBM clf + recent (rolling)",
          "M1_logit": "Logistic + recent (rolling)", "M1frozen_clf": "LightGBM clf + recent (frozen)",
          "M0pre_clf": "LightGBM clf fit <2025-10, raw", "M0pre_clf_recal_platt": "LightGBM clf fit <2025-10, Platt (Q4)",
          "M1pre_clf": "LightGBM clf+recent fit <2025-10, raw", "M1pre_clf_recal_platt": "LightGBM clf+recent fit <2025-10, Platt (Q4)"}
    Cm = pd.DataFrame([dict(model=v, key=k, AUC=auc(te.y_over_cap, te[k]), PR_AUC=ap(te.y_over_cap, te[k]),
                            brier=float(np.mean((te[k] - te.y_over_cap) ** 2)), mean_prob=te[k].mean(), prevalence=te.y_over_cap.mean())
                       for k, v in CL.items()])
    R.to_csv(os.path.join(ROUT, "drift_metrics_test.csv"), index=False); Cm.to_csv(os.path.join(ROUT, "drift_metrics_clf_test.csv"), index=False)
    print(R.round(4).to_string()); print(Cm.round(4).to_string())

    # ----- subgroup bias (fairness): does under-prediction in gentrifying tracts shrink?
    te["typ_group_s"] = te.typ_group.astype(str); te["typology_s"] = te.typology.fillna("NA").astype(str)
    keys = ["M0_lgb", "M1_lgb", "M1frozen_lgb", "M0pre_lgb", "M0pre_lgb_recal_lin", "M0pre_lgb_recal_shift", "M1pre_lgb_recal_lin",
            "M0_ridge", "M1_ridge"]
    rows = []
    for gcol in ["typ_group_s", "typology_s", "county"]:
        for g, d in te.groupby(gcol):
            if len(d) < 30: continue
            row = dict(group_set=gcol.replace("_s", ""), group=g, n=len(d), obs_mean_r=d.r.mean())
            for k in keys: row[f"bias_{k}"] = (d[k] - d.r).mean(); row[f"MAE_{k}"] = mean_absolute_error(d.r, d[k])
            rows.append(row)
    G = pd.DataFrame(rows)
    gap = {k: float(G.query("group=='2 Gentrifying'")[f"bias_{k}"].iloc[0] - G.query("group=='3 Moderate/mixed'")[f"bias_{k}"].iloc[0]) for k in keys}
    G = pd.concat([G, pd.DataFrame([dict(group_set="gap", group="bias Gentrifying - bias Moderate/mixed", **{f"bias_{k}": v for k, v in gap.items()})])])
    G.to_csv(os.path.join(ROUT, "drift_subgroup_bias_test.csv"), index=False)
    print(G[G.group_set.isin(["typ_group", "gap"]) | G.group.isin(["Advanced gentrification", "San Francisco County"])]
          [["group", "n", "obs_mean_r"] + [f"bias_{k}" for k in keys]].round(4).to_string())

    # ----- calibration plot before / after (test)
    pairs = [("M0_lgb", "LightGBM (s03)"), ("M0pre_lgb_recal_lin", "LightGBM, recalibrated on 2025-Q4"),
             ("M1_lgb", "LightGBM + recent-market feature"), ("M1pre_lgb_recal_lin", "LightGBM + recent, recalibrated")]
    CD = pd.concat([decile_calib(te.r.values, te[k].values, lab) for k, lab in pairs])
    CD.to_csv(os.path.join(ROUT, "drift_calibration_deciles.csv"), index=False)
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.8), sharex=True, sharey=True)
    for ax, (a, b), title in [(axs[0], pairs[:2], "s03 features"), (axs[1], pairs[2:], "with recent-market feature")]:
        for (k, lab), col in zip([a, b], [ORANGE, BLUE]):
            c = CD[CD.model == lab]; ax.plot(c.pred_mean * 100, c.obs_mean * 100, "-o", color=col, lw=2, ms=6, label=lab)
        lim = [CD[["pred_mean", "obs_mean"]].min().min() * 100 - 1, CD[["pred_mean", "obs_mean"]].max().max() * 100 + 1]
        ax.plot(lim, lim, color=MUTED, lw=1, ls="--"); style(ax); ax.set_title(f"Test calibration: {title}", loc="left")
        ax.set_xlabel("predicted annual jump, % (decile mean)"); ax.legend(frameon=False, fontsize=8, loc="upper left")
    axs[0].set_ylabel("observed mean annual jump, %")
    fig.tight_layout(); fig.savefig(os.path.join(RFIG, "calibration_before_after.png"), dpi=150); plt.close(fig)
    te[["zpid", "ep", "county", "typ_group", "typology", "r", "y_over_cap"] + list(P.columns)].to_parquet(
        os.path.join(ROUT, "drift_test_predictions.parquet"), index=False)

if __name__ == "__main__":
    main()
