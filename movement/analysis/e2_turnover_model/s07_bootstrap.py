"""Robustness 4: uncertainty. 95% percentile bootstrap CIs on test MAE / AUC (B = 2000 row resamples; B = 1000
ZIP-cluster resamples, since pairs in one ZIP share a market) for the main models vs the best baselines, including
paired differences. Plus seed variability: the s03 LightGBM regressor/classifier refit on train+val with 5 other seeds.
Outputs: outputs/robustness/bootstrap_ci_test.csv, seed_variability_test.csv; figs/robustness/bootstrap_ci.png."""
from robustness_common import *

def main():
    T = pd.read_parquet(os.path.join(OUT, "test_predictions.parquet"))
    D = pd.read_parquet(os.path.join(ROUT, "drift_test_predictions.parquet"))[["zpid", "ep", "M1_lgb", "M1_ridge", "M1_clf", "M1_logit"]]
    te = T.merge(D, on=["zpid", "ep"], how="left").reset_index(drop=True)
    assert te.M1_lgb.notna().all()
    y, yb = te.r.values, te.y_over_cap.values
    REG = {"LightGBM (s03)": "pred_lgb", "Ridge (s03)": "pred_ridge", "ZIP median": "pred_zipmed", "Legal rule": "pred_cap",
           "Ridge + recent-market (s06)": "M1_ridge", "LightGBM + recent-market (s06)": "M1_lgb"}
    CLF = {"LightGBM clf (s03)": "s_lgb", "Logistic (s03)": "s_logit", "ZIP over-cap rate": "s_ziprate",
           "LightGBM clf + recent-market (s06)": "M1_clf"}
    DIFF_R = [("LightGBM (s03)", "ZIP median"), ("Ridge (s03)", "ZIP median"), ("LightGBM (s03)", "Ridge (s03)"),
              ("Ridge + recent-market (s06)", "Ridge (s03)")]
    DIFF_C = [("LightGBM clf (s03)", "ZIP over-cap rate"), ("Logistic (s03)", "ZIP over-cap rate"),
              ("LightGBM clf + recent-market (s06)", "LightGBM clf (s03)")]
    ae = {k: np.abs(te[c].values - y) for k, c in REG.items()}

    def stats(idx):
        o = {f"MAE | {k}": ae[k][idx].mean() for k in REG}
        for k, c in CLF.items(): o[f"AUC | {k}"] = roc_auc_score(yb[idx], te[c].values[idx])
        for a, b in DIFF_R: o[f"MAE diff | {a} - {b}"] = o[f"MAE | {a}"] - o[f"MAE | {b}"]
        for a, b in DIFF_C: o[f"AUC diff | {a} - {b}"] = o[f"AUC | {a}"] - o[f"AUC | {b}"]
        return o

    point = stats(np.arange(len(te)))
    rng = np.random.default_rng(SEED)
    boot_iid = pd.DataFrame([stats(rng.integers(0, len(te), len(te))) for _ in range(2000)])
    groups = te.groupby("zipcode").indices; keys = list(groups)
    def cl():
        pick = rng.integers(0, len(keys), len(keys)); return np.concatenate([groups[keys[i]] for i in pick])
    boot_cl = pd.DataFrame([stats(cl()) for _ in range(1000)])
    rows = []
    for k, v in point.items():
        metric, model = [s.strip() for s in k.split("|")]
        rows.append(dict(metric=metric, model=model, estimate=v,
                         iid_lo=boot_iid[k].quantile(.025), iid_hi=boot_iid[k].quantile(.975),
                         zip_cluster_lo=boot_cl[k].quantile(.025), zip_cluster_hi=boot_cl[k].quantile(.975)))
    B = pd.DataFrame(rows); B.to_csv(os.path.join(ROUT, "bootstrap_ci_test.csv"), index=False); print(B.round(4).to_string())

    # seed variability (same val-tuned hyper-parameters; only random_state changes)
    S = load_sample()
    fit, (tt,) = M.add_features(S[S.split != "test"], [S[S.split == "test"]])
    p_r, p_c, *_ = tuned(); sr = []
    for seed in [42, 1, 2, 3, 4, 5]:
        pr = lgb.LGBMRegressor(**{**p_r, "random_state": seed}).fit(fit[M.LGB_FEATS], fit.r).predict(tt[M.LGB_FEATS])
        pc = lgb.LGBMClassifier(**{**p_c, "random_state": seed}).fit(fit[M.LGB_FEATS], fit.y_over_cap).predict_proba(tt[M.LGB_FEATS])[:, 1]
        sr.append(dict(seed=seed, MAE_lgb=mean_absolute_error(tt.r, pr), bias_lgb=float(np.mean(pr - tt.r)),
                       AUC_lgb_clf=roc_auc_score(tt.y_over_cap, pc), PRAUC_lgb_clf=average_precision_score(tt.y_over_cap, pc)))
    SR = pd.DataFrame(sr); SR.loc[len(SR)] = dict(seed="mean", **SR.iloc[:, 1:].mean()); SR.loc[len(SR)] = dict(seed="sd", **SR.iloc[:-1, 1:].std())
    SR.to_csv(os.path.join(ROUT, "seed_variability_test.csv"), index=False); print(SR.round(4))

    # figure
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
    for ax, met, scale, xl in [(axs[0], "MAE", 100, "test MAE, pp"), (axs[1], "AUC", 1, "test AUC (r > 10%/yr)")]:
        b = B[B.metric == met].reset_index(drop=True); yy = np.arange(len(b))[::-1]
        ax.errorbar(b.estimate * scale, yy + 0.12, xerr=[(b.estimate - b.iid_lo) * scale, (b.iid_hi - b.estimate) * scale], fmt="o",
                    color=BLUE, ms=5, capsize=3, label="row bootstrap")
        ax.errorbar(b.estimate * scale, yy - 0.12, xerr=[(b.estimate - b.zip_cluster_lo) * scale, (b.zip_cluster_hi - b.estimate) * scale],
                    fmt="s", color=ORANGE, ms=4, capsize=3, label="ZIP-cluster bootstrap")
        ax.set_yticks(yy); ax.set_yticklabels(b.model, fontsize=8); ax.set_xlabel(xl); style(ax)
    axs[0].set_title("95% bootstrap intervals, 2026 test", loc="left"); axs[1].legend(frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout(); fig.savefig(os.path.join(RFIG, "bootstrap_ci.png"), dpi=150); plt.close(fig)

if __name__ == "__main__":
    main()
