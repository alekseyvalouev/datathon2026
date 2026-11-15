"""Step 2: baselines, models, one-shot temporal test, subgroup checks.

Split by risk year: train 2019-2023, validation 2024 (tuning, thresholds), test 2025. Final models are refit on
train+validation with validation-chosen settings and scored once on 2025. Same LightGBM settings, tuning grid and
metrics as the rent model (units-leaving-reach/code/modlib.py)."""
import os, sys, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WS, "..", "units-leaving-reach", "code"))
from modlib import (HOMETYPES, COUNTIES, UDP_GROUP, tune_lgb, fit_lgb, tune_logit, fit_logit, metrics, boot_auc_ci,
                    boot_auc_diff, f1_threshold, SEED)
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.model_selection import GroupKFold
RES = os.path.join(WS, "results"); BUDGET = 0.20

HIST = ["tenure_y", "n_prior", "obs_y", "last_gap_y", "prior_rate", "start_month"]
LAST = ["log_last_p", "ppsf", "prev_cut", "n_changes", "n_listings", "vacancy_d"]
UNIT = ["beds", "baths", "sqft", "age", "mgmt", "large_landlord"] + [f"ht_{h}" for h in HOMETYPES] + \
       [f"cty_{c[:-7].replace(' ', '_')}" for c in COUNTIES]
MKT = ["mkt_lvl0", "mkt_since", "mkt_mom", "te_zip_y"]
TRACT = ["per_rent_18", "per_nonwhite_18", "real_hinc_18", "per_all_li_18", "per_col_18", "real_mrent_18",
         "per_limove_18", "rail"] + [f"udp_{g}" for g in ["low_income", "gentrifying", "moderate", "exclusive"]]
ALL = HIST + LAST + UNIT + MKT + TRACT
GROUPS = {"tenancy history": HIST, "last listing": LAST, "unit": UNIT, "market": MKT, "tract": TRACT}
TEN_BINS = [0, .5, 1, 1.5, 2, 3, 4, 6, 99]

def static(df):
    df = df.replace([np.inf, -np.inf], np.nan)
    for h in HOMETYPES: df[f"ht_{h}"] = (df.homeType == h).astype(int)
    for c in COUNTIES: df[f"cty_{c[:-7].replace(' ', '_')}"] = (df.county == c).astype(int)
    df["udp_group"] = df.udp_typ.map(UDP_GROUP)
    for g in ["low_income", "gentrifying", "moderate", "exclusive"]:
        df[f"udp_{g}"] = np.where(df.udp_group.isna(), np.nan, (df.udp_group == g).astype(float))
    df["ten_bin"] = pd.cut(df.tenure_y, TEN_BINS, labels=False, include_lowest=True)
    return df

def te(fit, app, key, k=20):
    prior = fit.y.mean(); g = fit.groupby(key).y.agg(["sum", "count"])
    return app[key].map((g["sum"] + k * prior) / (g["count"] + k)).fillna(prior).values

def encode(fit, apps):
    """ZIP turnover rate and tenure-bin rate from `fit` rows only; ZIP rate is out-of-fold by unit inside `fit`."""
    fit = fit.copy(); apps = [a.copy() for a in apps]; oof = np.zeros(len(fit))
    for tr, ho in GroupKFold(5).split(fit, groups=fit.zpid): oof[ho] = te(fit.iloc[tr], fit.iloc[ho], "zipcode")
    fit["te_zip_y"] = oof
    for a in apps: a["te_zip_y"] = te(fit, a, "zipcode")
    for d in [fit] + apps: d["rule_tenure"] = te(fit, d, "ten_bin", k=0)
    return fit, apps

def baselines(d, base):
    return {"Flat rate (the atlas assumption: every unit the same)": np.full(len(d), base),
            "Lease-clock rule: turnover rate by time since last listing": d.rule_tenure.values,
            "Own-history rule: the unit's past turnovers per year": d.prior_rate.fillna(base).values}

def main():
    df = static(pd.read_parquet(os.path.join(RES, "panel.parquet")))
    tr, va, test = (df[df.split == s].copy() for s in ("train", "val", "test"))
    trva = df[df.split.isin(["train", "val"])].copy()
    tr_e, (va_e,) = encode(tr, [va])
    auc, p, n = tune_lgb(tr_e[ALL], tr_e.y, va_e[ALL], va_e.y)
    aucC, C = tune_logit(tr_e[ALL], tr_e.y, va_e[ALL], va_e.y)
    aucT, CT = tune_logit(tr_e[["tenure_y"]], tr_e.y, va_e[["tenure_y"]], va_e.y)
    print(f"validation AUC  LightGBM {auc:.3f} {p} trees={n} | logistic {aucC:.3f} | logistic tenure only {aucT:.3f}")
    val = {"LightGBM": fit_lgb(tr_e[ALL], tr_e.y, p, n).predict_proba(va_e[ALL])[:, 1],
           "Logistic (L2), all features": fit_logit(tr_e[ALL], tr_e.y, C).predict_proba(va_e[ALL])[:, 1]}
    val.update(baselines(va_e, tr_e.y.mean()))
    trva_e, (te_e,) = encode(trva, [test]); base = trva_e.y.mean()
    model = fit_lgb(trva_e[ALL], trva_e.y, p, n)
    sc = dict(baselines(te_e, base))
    sc["Logistic (L2), all features"] = fit_logit(trva_e[ALL], trva_e.y, C).predict_proba(te_e[ALL])[:, 1]
    sc["LightGBM"] = model.predict_proba(te_e[ALL])[:, 1]
    y = te_e.y.values; res = []
    for k, s in sc.items():
        flat = np.std(s) == 0
        m = metrics(y, s, None if flat else f1_threshold(va_e.y.values, val[k]), None if flat else np.quantile(val[k], 1 - BUDGET))
        m["model"] = k; m["Brier"] = brier_score_loss(y, np.clip(s, 0, 1)); m["mean_pred"] = np.mean(s)
        m["AUC_lo"], m["AUC_hi"] = (np.nan, np.nan) if flat else boot_auc_ci(y, s)
        res.append(m)
    res = pd.DataFrame(res).set_index("model")
    cols = ["n", "prevalence", "mean_pred", "AUC", "AUC_lo", "AUC_hi", "PR_AUC", "Brier", "precision", "recall", "F1",
            "budget_flagged", "budget_precision", "budget_recall"]
    res[cols].round(3).to_csv(os.path.join(RES, "s02_test_metrics.csv"))
    print("\nTEST 2025 (n=%d, turnover rate %.3f)" % (len(y), y.mean())); print(res[cols].round(3).to_string())
    rule = "Lease-clock rule: turnover rate by time since last listing"
    lo, hi = boot_auc_diff(y, sc["LightGBM"], sc[rule])
    print(f"\nLightGBM minus lease-clock rule, AUC: {res.loc['LightGBM','AUC'] - res.loc[rule,'AUC']:.3f} [{lo:.3f}, {hi:.3f}]")
    pd.DataFrame([dict(a="LightGBM", b=rule, diff=res.loc["LightGBM", "AUC"] - res.loc[rule, "AUC"], lo=lo, hi=hi)]).round(4).to_csv(os.path.join(RES, "s02_comparisons.csv"), index=False)

    rng = np.random.default_rng(SEED); imp = []
    for g, cg in GROUPS.items():
        drops = []
        for _ in range(5):
            X = te_e[ALL].copy(); X[cg] = X[cg].values[rng.permutation(len(X))]
            drops.append(res.loc["LightGBM", "AUC"] - roc_auc_score(y, model.predict_proba(X)[:, 1]))
        imp.append(dict(group=g, n_features=len(cg), auc_drop=np.mean(drops)))
    imp = pd.DataFrame(imp).sort_values("auc_drop", ascending=False); imp.round(4).to_csv(os.path.join(RES, "s02_group_importance.csv"), index=False)
    gain = pd.Series(model.booster_.feature_importance("gain"), index=ALL).sort_values(ascending=False)
    (gain / gain.sum()).round(4).rename("gain_share").to_csv(os.path.join(RES, "s02_feature_gain.csv"))
    print("\n", imp.round(4).to_string(index=False)); print((gain / gain.sum()).head(10).round(3).to_string())

    te_e["score"] = sc["LightGBM"]; te_e["score_rule"] = sc[rule]
    bthr = np.quantile(val["LightGBM"], 1 - BUDGET); rbthr = np.quantile(val[rule], 1 - BUDGET)
    q = np.nanquantile(df.drop_duplicates("tract").real_hinc_18, [1 / 3, 2 / 3])
    sub = {"UDP typology group": te_e.udp_group.fillna("unmatched"),
           "County": te_e.county.str.replace(" County", ""),
           "Tract tenure": te_e.renter_majority.map({1.0: "majority renter", 0.0: "majority owner"}).fillna("unmatched"),
           "Tract race": te_e.poc_majority.map({1.0: "majority people of color", 0.0: "majority white"}).fillna("unmatched"),
           "Tract income (2018 tercile)": pd.cut(te_e.real_hinc_18, [-np.inf, q[0], q[1], np.inf], labels=["low", "middle", "high"]).astype(str),
           "Home type": np.where(te_e.homeType == "APARTMENT", "apartment", "house/condo/townhouse"),
           "Landlord": np.where(te_e.large_landlord == 1, "large manager (200+ units)", "other"),
           "Time since last listing": pd.cut(te_e.tenure_y, [0, 1, 2, 4, 99], labels=["<1y", "1-2y", "2-4y", "4y+"], include_lowest=True).astype(str)}
    rows = []
    for gname, lab in sub.items():
        for g in sorted(pd.Series(lab).unique()):
            d = te_e[np.asarray(lab) == g]
            if len(d) < 30 or g in ("unmatched", "nan"): continue
            m = metrics(d.y, d.score, None, bthr); r = metrics(d.y, d.score_rule, None, rbthr)
            rows.append(dict(grouping=gname, group=g, n=len(d), turnover_rate=d.y.mean(), mean_pred=d.score.mean(),
                             pred_over_actual=d.score.mean() / d.y.mean(), AUC=m["AUC"], budget_recall=m["budget_recall"],
                             rule_AUC=r["AUC"], rule_budget_recall=r["budget_recall"]))
    sg = pd.DataFrame(rows); sg.round(3).to_csv(os.path.join(RES, "s02_subgroups.csv"), index=False)
    print("\n", sg.round(3).to_string(index=False))
    te_e["dec"] = pd.qcut(te_e.score, 10, labels=False, duplicates="drop")
    cal = te_e.groupby("dec").agg(n=("y", "size"), mean_pred=("score", "mean"), observed=("y", "mean")).round(3)
    cal.to_csv(os.path.join(RES, "s02_calibration.csv")); print("\n", cal.to_string())
    te_e[["zpid", "year", "county", "zipcode", "homeType", "tenure_y", "y", "score", "score_rule"]].to_parquet(os.path.join(RES, "s02_test_predictions.parquet"), index=False)
    model.booster_.save_model(os.path.join(RES, "turnover_model.txt"))
    json.dump(dict(lgb_params=p, n_trees=n, logit_C=C, features=ALL, budget_threshold=float(bthr)), open(os.path.join(RES, "s02_config.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
