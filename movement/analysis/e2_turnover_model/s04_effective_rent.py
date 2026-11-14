"""Robustness 1: effective-rent target (free-rent concessions).
Concession text exists only for the CURRENT listing (E6 regex on description / special_offer), so it applies to a pair
only when the pair's NEXT episode is the unit's current FOR_RENT listing. Effective first-year next rent
= next_first x (1 - weeks_free/52), i.e. a 12-month lease with the free weeks spread over the year. Pairs without a
parsed concession keep effective = asking. The PRIOR tenancy's concession is unobserved (assumed none).
Outputs (outputs/robustness/): eff_counts.csv, eff_metrics_test.csv, eff_subgroups_test.csv, eff_headline.csv;
figs/robustness/eff_vs_ask_subgroups.png."""
from robustness_common import *

def main():
    S = add_concessions(load_sample())
    S.to_parquet(os.path.join(ROUT, "sample_with_concessions.parquet"), index=False)
    # (a) counts
    cnt = S.groupby("split").agg(n=("r", "size"), next_is_current_for_rent=("conc_known", "sum"),
                                 with_concession=("conc_flag", "sum"), median_weeks=("conc_weeks", "median")).reset_index()
    cnt["share_with_concession"] = cnt.with_concession / cnt.n
    cnt.to_csv(os.path.join(ROUT, "eff_counts.csv"), index=False); print(cnt)

    T = pd.read_parquet(os.path.join(OUT, "test_predictions.parquet"))
    te = S[S.split == "test"].merge(T[["zpid", "ep", "pred_lgb", "pred_ridge", "pred_zipmed", "pred_cap", "s_lgb", "s_logit",
                                       "s_ziprate", "landlord", "rent_quartile"]], on=["zpid", "ep"], how="left")
    assert te.pred_lgb.notna().all() and len(te) == len(T)
    # (c) models that know the concession (a feature of the new listing, posted at re-listing time)
    fit0, te0 = S[S.split != "test"].copy(), S[S.split == "test"].copy()
    fit, (tef,) = M.add_features(fit0, [te0])
    numc = M.NUM + ["conc_flag", "conc_weeks0"]
    pc = fit_predict(fit, tef, num=numc, target="r_eff", ytarget="y_eff")
    pe = fit_predict(fit, tef, target="r_eff", ytarget="y_eff", which=("lgb",))      # effective target, no concession feature
    k = tef[["zpid", "ep"]].assign(pred_lgb_conc=pc["lgb"], pred_ridge_conc=pc["ridge"], s_lgb_conc=pc["clf"],
                                   s_logit_conc=pc["logit"], pred_lgb_efftarget=pe["lgb"])
    te = te.merge(k, on=["zpid", "ep"])
    # mechanical adjustment: apply the posted concession to the asking-rent prediction
    adj = lambda p: ((1 + te[p]) ** te.start_gap_y * (1 - te.conc_weeks0 / 52)) ** (1 / te.start_gap_y) - 1
    te["pred_lgb_adj"] = adj("pred_lgb"); te["pred_ridge_adj"] = adj("pred_ridge")

    # (b) metrics: asking vs effective target
    rows = []
    for subset, d in [("all test", te), ("test pairs with concession", te[te.conc_flag == 1])]:
        for tgt, y, yb in [("asking", "r", "y_over_cap"), ("effective", "r_eff", "y_eff")]:
            base = dict(subset=subset, target=tgt, n=len(d), mean_r=d[y].mean(), median_r=d[y].median(), over_cap_share=d[yb].mean())
            for name, col in [("Legal rule", "pred_cap"), ("ZIP median (train r)", "pred_zipmed"), ("Ridge (asking-trained)", "pred_ridge"),
                              ("LightGBM (asking-trained)", "pred_lgb"), ("LightGBM trained on effective target", "pred_lgb_efftarget"),
                              ("LightGBM + concession features", "pred_lgb_conc"), ("Ridge + concession features", "pred_ridge_conc"),
                              ("LightGBM asking pred x posted concession", "pred_lgb_adj"), ("Ridge asking pred x posted concession", "pred_ridge_adj")]:
                rows.append(dict(base, model=name, **reg_row(d[y], d[col])))
            for name, col in [("ZIP over-cap rate", "s_ziprate"), ("Logistic (asking-trained)", "s_logit"), ("LightGBM clf (asking-trained)", "s_lgb"),
                              ("LightGBM clf + concession features", "s_lgb_conc"), ("Logistic + concession features", "s_logit_conc")]:
                rows.append(dict(base, model=name, AUC=auc(d[yb], d[col]), PR_AUC=ap(d[yb], d[col])))
    R = pd.DataFrame(rows); R.to_csv(os.path.join(ROUT, "eff_metrics_test.csv"), index=False)
    print(R.round(4).to_string())

    # headline: how much of the turnover premium survives on an effective basis
    cpi = np.array([CPI.get(int(s[:4]), 2.6) / 100 for s in te.next_start])
    te["stay_cpi"] = te.last_p * (1 + cpi) ** te.start_gap_y
    te["prem_ask"] = te.next_first - te.stay_cpi; te["prem_eff"] = te.next_eff - te.stay_cpi
    te["xs_ask"] = te.r - cpi; te["xs_eff"] = te.r_eff - cpi            # annual jump in excess of CPI
    H = []
    for subset, d in [("all test", te), ("next = current listing", te[te.conc_known == 1]), ("with concession", te[te.conc_flag == 1]),
                      ("mgmt co, with concession", te[(te.conc_flag == 1) & (te.mgmt == 1)])]:
        H.append(dict(subset=subset, n=len(d), mean_r_ask=d.r.mean(), mean_r_eff=d.r_eff.mean(), median_r_ask=d.r.median(),
                      median_r_eff=d.r_eff.median(), mean_excess_over_cpi_ask=d.xs_ask.mean(), mean_excess_over_cpi_eff=d.xs_eff.mean(),
                      survival_excess_over_cpi=d.xs_eff.mean() / d.xs_ask.mean(),
                      mean_premium_month_ask=d.prem_ask.mean(), mean_premium_month_eff=d.prem_eff.mean(),
                      median_premium_month_ask=d.prem_ask.median(), median_premium_month_eff=d.prem_eff.median(),
                      survival_mean_premium=d.prem_eff.mean() / d.prem_ask.mean(),
                      over_cap_ask=d.y_over_cap.mean(), over_cap_eff=d.y_eff.mean()))
    H = pd.DataFrame(H); H.to_csv(os.path.join(ROUT, "eff_headline.csv"), index=False); print(H.round(4).T)

    # (d) subgroups
    te["mgmt_s"] = np.where(te.mgmt == 1, "management company", "individual / not mgmt")
    G = []
    for gcol in ["mgmt_s", "landlord", "county"]:
        for g, d in te.groupby(gcol, observed=True):
            G.append(dict(group_set=gcol.replace("_s", ""), group=g, n=len(d), share_next_current=d.conc_known.mean(),
                          share_concession=d.conc_flag.mean(), median_weeks=d.conc_weeks.median(),
                          mean_r_ask=d.r.mean(), mean_r_eff=d.r_eff.mean(), over_cap_ask=d.y_over_cap.mean(), over_cap_eff=d.y_eff.mean(),
                          mean_premium_month_ask=d.prem_ask.mean(), mean_premium_month_eff=d.prem_eff.mean(),
                          bias_lgb_vs_ask=(d.pred_lgb - d.r).mean(), bias_lgb_vs_eff=(d.pred_lgb - d.r_eff).mean(),
                          MAE_lgb_vs_ask=mean_absolute_error(d.r, d.pred_lgb), MAE_lgb_vs_eff=mean_absolute_error(d.r_eff, d.pred_lgb),
                          MAE_lgb_conc_vs_eff=mean_absolute_error(d.r_eff, d.pred_lgb_conc),
                          MAE_lgb_adj_vs_eff=mean_absolute_error(d.r_eff, d.pred_lgb_adj),
                          MAE_zipmed_vs_eff=mean_absolute_error(d.r_eff, d.pred_zipmed)))
    G = pd.DataFrame(G); G.to_csv(os.path.join(ROUT, "eff_subgroups_test.csv"), index=False); print(G.round(3).to_string())
    te[["zpid", "ep", "county", "zipcode", "mgmt", "landlord", "typ_group", "typology", "conc_known", "conc_flag", "conc_weeks",
        "r", "r_eff", "y_over_cap", "y_eff", "pred_lgb", "pred_lgb_conc", "pred_lgb_adj", "pred_lgb_efftarget", "s_lgb", "s_lgb_conc"]
       ].to_parquet(os.path.join(ROUT, "eff_test_predictions.parquet"), index=False)

    # figure
    g = G[G.group_set.isin(["mgmt", "county"])].copy(); g["label"] = g.group_set + ": " + g.group.astype(str)
    fig, ax = plt.subplots(figsize=(8, 0.32 * len(g) + 1.2)); y = np.arange(len(g))[::-1]
    for yy, a, b in zip(y, g.mean_r_ask * 100, g.mean_r_eff * 100): ax.plot([a, b], [yy, yy], color=MUTED, lw=1.5, zorder=2)
    ax.scatter(g.mean_r_ask * 100, y, color=ORANGE, s=45, zorder=3, edgecolors="#fcfcfb", label="asking rent")
    ax.scatter(g.mean_r_eff * 100, y, color=BLUE, s=45, zorder=3, edgecolors="#fcfcfb", label="effective (net of posted free weeks)")
    ax.set_yticks(y); ax.set_yticklabels([f"{l}  ({s:.0%} conc.)" for l, s in zip(g.label, g.share_concession)], fontsize=8)
    ax.set_xlabel("mean annualized turnover rent change, % (2026 test)"); style(ax)
    ax.set_title("Asking vs effective turnover jump, 2026 test", loc="left", fontsize=10)
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(RFIG, "eff_vs_ask_subgroups.png"), dpi=150); plt.close(fig)

if __name__ == "__main__":
    main()
