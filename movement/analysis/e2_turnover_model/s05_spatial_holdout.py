"""Robustness 2: spatial holdout within the same time windows.
(a) Leave-one-county-out (LOCO): fit on train+val pairs (re-listed before 2026) of 8 counties, score the 2026 test
    pairs of the 9th. Target encodings / ZIP-relative rent are refit without the held-out county, so its ZIP/county
    encodings fall back to the global mean. The county market index (mkt_chg, mkt_mom) is still computed from the held-out
    county's own listing asks before re-listing (public market data a deployment would have; no turnover outcomes).
(b) Held-out ZIP blocks: ZIP centroids clustered into 25 spatial blocks (KMeans, seed 42); 5-fold GroupKFold over blocks.
Hyper-parameters are the val-tuned ones from s03 (no re-tuning). Baselines: legal rule; "ZIP median of train r" (which,
for a held-out county, has no ZIP/county rows and falls back to the global median of the training counties); and,
as a NON-held-out reference, the in-county ZIP median and s03's temporal-only LightGBM on the same test rows.
Outputs: outputs/robustness/spatial_loco.csv, spatial_zipblocks.csv; figs/robustness/spatial_loco.png."""
from robustness_common import *
from sklearn.cluster import KMeans
from sklearn.model_selection import GroupKFold

def score(te, preds, label, extra):
    d = dict(extra, holdout=label, n=len(te), obs_mean_r=te.r.mean(), over_cap=te.y_over_cap.mean())
    for k in ["lgb", "ridge", "zipmed_heldout", "cap", "zipmed_incounty", "lgb_temporal_only"]:
        d[f"MAE_{k}"] = mean_absolute_error(te.r, preds[k]); d[f"bias_{k}"] = float(np.mean(preds[k] - te.r.values))
    for k in ["clf", "logit", "clf_temporal_only"]:
        d[f"AUC_{k}"] = auc(te.y_over_cap, preds[k]); d[f"PRAUC_{k}"] = ap(te.y_over_cap, preds[k])
    return d

def run_fold(S, T, fit_mask, te_mask):
    fit0, te0 = S[fit_mask].copy(), S[te_mask].copy()
    fit, (te,) = M.add_features(fit0, [te0])
    p = fit_predict(fit, te)
    p["zipmed_heldout"] = M.zip_median_baseline(fit, te)
    p["cap"] = M.legal_cap_baseline(te)
    allfit = S[S.split != "test"]                      # reference: ZIP medians that DO include the held-out area
    p["zipmed_incounty"] = M.zip_median_baseline(allfit, te)
    t = te[["zpid", "ep"]].merge(T, on=["zpid", "ep"], how="left")
    p["lgb_temporal_only"] = t.pred_lgb.values; p["clf_temporal_only"] = t.s_lgb.values
    return te, p

def main():
    S = load_sample()
    T = pd.read_parquet(os.path.join(OUT, "test_predictions.parquet"))[["zpid", "ep", "pred_lgb", "s_lgb"]]
    pre, post = S.split != "test", S.split == "test"
    rows, allc = [], []
    for c in sorted(S.county.unique()):
        te, p = run_fold(S, T, pre & (S.county != c), post & (S.county == c))
        rows.append(score(te, p, c, dict(scheme="leave-one-county-out")))
        allc.append(pd.DataFrame({**p, "r": te.r.values, "y_over_cap": te.y_over_cap.values}))
        print(c, {k: round(v, 4) for k, v in rows[-1].items() if k.startswith("MAE") or k.startswith("AUC")})
    # pooled over all held-out counties (each test row predicted by the model that never saw its county)
    Pc = pd.concat(allc)
    rows.append(score(Pc, {k: Pc[k].values for k in Pc.columns}, "pooled (all 9)", dict(scheme="leave-one-county-out")))
    Pn = Pc.iloc[np.flatnonzero(np.concatenate([np.full(len(a), c != "San Francisco County") for a, c in zip(allc, sorted(S.county.unique()))]))]
    rows.append(score(Pn, {k: Pn[k].values for k in Pn.columns}, "pooled excl. SF", dict(scheme="leave-one-county-out")))
    L = pd.DataFrame(rows)
    L.to_csv(os.path.join(ROUT, "spatial_loco.csv"), index=False)

    # ZIP blocks
    zc = S.groupby("zipcode")[["lat", "lon"]].mean()
    zc["block"] = KMeans(25, random_state=SEED, n_init=10).fit_predict(zc[["lat", "lon"]].values * [1.0, 0.8])
    S["block"] = S.zipcode.map(zc.block)
    blocks = np.arange(25); rows, allp = [], []
    for k, (_, tb) in enumerate(GroupKFold(5).split(blocks, groups=blocks)):
        te, p = run_fold(S, T, pre & ~S.block.isin(tb), post & S.block.isin(tb))
        rows.append(score(te, p, f"fold {k}", dict(scheme="ZIP blocks (25 blocks, 5 folds)")))
        allp.append(pd.DataFrame({**{k2: v for k2, v in p.items()}, "r": te.r.values, "y_over_cap": te.y_over_cap.values}))
    P = pd.concat(allp)
    pooled = dict(scheme="ZIP blocks (25 blocks, 5 folds)", holdout="pooled", n=len(P), obs_mean_r=P.r.mean(), over_cap=P.y_over_cap.mean())
    for k in ["lgb", "ridge", "zipmed_heldout", "cap", "zipmed_incounty", "lgb_temporal_only"]:
        pooled[f"MAE_{k}"] = mean_absolute_error(P.r, P[k]); pooled[f"bias_{k}"] = float((P[k] - P.r).mean())
    for k in ["clf", "logit", "clf_temporal_only"]:
        pooled[f"AUC_{k}"] = auc(P.y_over_cap, P[k]); pooled[f"PRAUC_{k}"] = ap(P.y_over_cap, P[k])
    B = pd.DataFrame(rows + [pooled]); B.to_csv(os.path.join(ROUT, "spatial_zipblocks.csv"), index=False)
    print(B.round(4).to_string())

    # figure: LOCO MAE by held-out county
    fig, ax = plt.subplots(figsize=(8, 4.6)); L2 = L[~L.holdout.str.startswith("pooled")].sort_values("MAE_lgb"); y = np.arange(len(L2))
    for col, lab, colr, mk in [("MAE_lgb", "LightGBM, county held out", BLUE, "o"), ("MAE_zipmed_heldout", "median baseline, county held out", ORANGE, "o"),
                               ("MAE_cap", "legal rule (CPI+5%, max 10%)", MUTED, "s"), ("MAE_lgb_temporal_only", "LightGBM, county seen (s03)", INK2, "x")]:
        ax.scatter(L2[col] * 100, y, label=lab, color=colr, marker=mk, s=40, zorder=3)
    ax.set_yticks(y); ax.set_yticklabels([f"{c.replace(' County', '')} (n={n})" for c, n in zip(L2.holdout, L2.n)], fontsize=8)
    ax.set_xlabel("test MAE, pp of annual rent change (2026 re-listings of the held-out county)"); style(ax)
    ax.set_title("Leave-one-county-out", loc="left"); ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout(); fig.savefig(os.path.join(RFIG, "spatial_loco.png"), dpi=150); plt.close(fig)

if __name__ == "__main__":
    main()
