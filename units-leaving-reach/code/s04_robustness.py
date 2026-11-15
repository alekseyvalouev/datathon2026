"""Step 4: robustness and fairness follow-ups. Re-uses the hyper-parameters chosen on validation in s03 (no re-tuning).
 R1 label variants: first ask instead of settled ask; drop annualized jumps > 30%/yr (likely unit swaps, see hand
    check); 50% AMI (very low income) line; 2.5x income rule.
 R2 test units never seen in train/validation.
 R3 leave-one-county-out: train on train+val pairs of the other eight counties (encodings also exclude the county),
    test on that county's 2026 pairs.
 R5 seed stability of the feature-set ablation: refit each feature set with 10 seeds (bagging and column sampling
    are random), report mean and spread of test AUC; the bootstrap intervals in s03 cover test sampling only.
 R4 budget allocation: one regional top-20% list against a top-20% list inside each UDP typology group (thresholds
    from validation quantiles), to show the recall / parity trade-off."""
import os, sys, json, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modlib import *

RULE = "Legal-max rule: crosses if rent rises at AB 1482 max (10%/yr)"

def variant(full, thr_col, settled=True, drop_jumps=False):
    d = full[full.last_p <= full[thr_col]].copy()
    d["thr"] = d[thr_col]
    d["y"] = ((d.next_last if settled else d.next_first) > d.thr).astype(int)
    d["headroom"] = np.log(d.thr / d.last_p)
    d["req_growth"] = (d.thr / d.last_p) ** (1 / d.start_gap_y) - 1
    if drop_jumps: d = d[d.r <= 0.30]
    d["renter_majority"] = np.where(d.per_rent_18.isna(), np.nan, (d.per_rent_18 > 0.5).astype(float))
    return static_features(d)

def run(df, hist, p, n, test_mask=None, fit_mask=None, hist_mask=None):
    fit = df[df.split.isin(["train", "val"])] if fit_mask is None else df[fit_mask]
    te = df[df.split == "test"] if test_mask is None else df[test_mask]
    h = hist if hist_mask is None else hist[hist_mask]
    fit_e, (te_e,) = add_encodings(fit, [te], h, VAL_END)
    s = fit_lgb(fit_e[ALL], fit_e.y, p, n).predict_proba(te_e[ALL])[:, 1]
    r = baseline_scores(te_e)[RULE]
    lo, hi = boot_auc_diff(te_e.y.values, s, r, B=500)
    return dict(n=len(te_e), prevalence=te_e.y.mean(), model_AUC=roc_auc_score(te_e.y, s),
                rule_AUC=roc_auc_score(te_e.y, r), diff_lo=lo, diff_hi=hi)

def main():
    df, hist = load()
    cfg = json.load(open(os.path.join(RES, "s03_config.json")))
    p, n = cfg["lgb_params"]["+ tract + city jobs (all workstreams)"]
    p = eval(p) if isinstance(p, str) else p
    rows = [dict(check="main (settled ask, 80% AMI, 3x)", **run(df, hist, p, n))]
    full = pd.read_parquet(os.path.join(RES, "pairs_all_relisted.parquet"))
    for name, kw in [("R1 first ask instead of settled ask", dict(thr_col="thr", settled=False)),
                     ("R1 drop jumps > 30%/yr (likely unit swaps)", dict(thr_col="thr", drop_jumps=True)),
                     ("R1 50% AMI (very low income) line", dict(thr_col="thr_vli")),
                     ("R1 2.5x income rule", dict(thr_col="thr_25"))]:
        rows.append(dict(check=name, **run(variant(full, **kw), hist, p, n)))
    seen = set(df[df.split.isin(["train", "val"])].zpid)
    rows.append(dict(check="R2 test units never seen in train/val",
                     **run(df, hist, p, n, test_mask=(df.split == "test") & ~df.zpid.isin(seen))))
    for c in COUNTIES:
        rows.append(dict(check=f"R3 hold out {c.replace(' County', '')}",
                         **run(df, hist, p, n, test_mask=(df.split == "test") & (df.county == c),
                               fit_mask=df.split.isin(["train", "val"]) & (df.county != c), hist_mask=hist.county != c)))
    out = pd.DataFrame(rows); out["gain"] = out.model_AUC - out.rule_AUC
    out.round(4).to_csv(os.path.join(RES, "s04_robustness.csv"), index=False); print(out.round(3).to_string(index=False))
    seed_ablation(df, hist, cfg)

    # R4 budget allocation by UDP typology group
    pr = pd.read_parquet(os.path.join(RES, "s03_test_predictions.parquet"))
    tr, va = df[df.split == "train"], df[df.split == "val"]
    tr_e, (va_e,) = add_encodings(tr, [va], hist, TRAIN_END)
    va_e["score"] = fit_lgb(tr_e[ALL], tr_e.y, p, n).predict_proba(va_e[ALL])[:, 1]
    va_e["udp_group"] = va_e.udp_group.fillna("unmatched"); pr["udp_group"] = pr.udp_group.fillna("unmatched")
    reg_thr = np.quantile(va_e.score, 0.8)
    grp_thr = va_e.groupby("udp_group").score.quantile(0.8)
    pr["flag_regional"] = pr.score >= reg_thr
    pr["flag_within_group"] = pr.score >= pr.udp_group.map(grp_thr)
    rows = []
    for policy in ["flag_regional", "flag_within_group"]:
        for g, d in [("ALL", pr)] + list(pr.groupby("udp_group")):
            f = d[policy]; y = d.y == 1
            rows.append(dict(policy=policy.replace("flag_", ""), group=g, n=len(d), flagged=f.mean(),
                             recall=(f & y).sum() / y.sum(), precision=(f & y).sum() / max(f.sum(), 1),
                             units_caught=int((f & y).sum()), units_flagged=int(f.sum())))
    b = pd.DataFrame(rows); b.round(3).to_csv(os.path.join(RES, "s04_budget_allocation.csv"), index=False)
    print("\n", b.round(3).to_string(index=False))

def seed_ablation(df, hist, cfg):
    fit = df[df.split.isin(["train", "val"])]; te = df[df.split == "test"]
    fit_e, (te_e,) = add_encodings(fit, [te], hist, VAL_END)
    rows = []
    for name, cols in SETS.items():
        p, n = cfg["lgb_params"][name]
        for seed in range(10):
            s = fit_lgb(fit_e[cols], fit_e.y, p, n, seed=seed).predict_proba(te_e[cols])[:, 1]
            rows.append(dict(features=name, seed=seed, AUC=roc_auc_score(te_e.y, s)))
    r = pd.DataFrame(rows)
    w = r.pivot(index="seed", columns="features", values="AUC")
    names = list(SETS)
    w["gain tract"] = w[names[1]] - w[names[0]]; w["gain city jobs"] = w[names[2]] - w[names[1]]
    w["gain both"] = w[names[2]] - w[names[0]]
    summ = w.agg(["mean", "std", "min", "max"]).T.round(4)
    summ.to_csv(os.path.join(RES, "s04_seed_ablation.csv")); print("\n", summ.to_string())

if __name__ == "__main__":
    main()
