"""Leaver-vs-stayer comparisons: raw weighted and IPW (ATT) with ACS replicate-weight SEs.

SE = sqrt(4/80 * sum_r (theta_r - theta)^2)  (successive-difference replication, ACS PUMS docs).
For IPW contrasts the propensity model is re-fit under each of the 80 replicate weights, so the
SE reflects propensity estimation as well (headline contrasts). Subgroup tables re-fit too.
"""
import os
import warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA, OUT = os.path.join(BASE, "data"), os.path.join(BASE, "outputs")
REP = [f"PWGTP{i}" for i in range(1, 81)]
WCOLS = ["PWGTP"] + REP
OUTCOMES = ["own", "renter", "rent_burden30", "rent_burden50", "overcrowded", "commute60", "commute_min",
            "wfh", "employed", "wage_2024usd", "below_200pov"]
CAT = ["race_eth", "educ", "age_grp", "hh_type", "YEAR", "origin_county"]
BIN = ["female", "foreign_born", "married", "disabled", "kids"]
TREATMENTS = {"left_any": ["left_ca", "left_saccv", "left_othca"], "left_ca": ["left_ca"],
              "left_saccv": ["left_saccv"], "left_othca": ["left_othca"]}


def design(df):
    X = pd.get_dummies(df[CAT].astype(str), drop_first=True)
    X[BIN] = df[BIN].values
    X["age"] = (df.AGEP.values - 40) / 12
    X["age2"] = X["age"] ** 2
    return X.astype(float).values


def rep_se(est, reps):
    return np.sqrt(4 / 80 * np.nansum((reps - est) ** 2, axis=0))


def wmean(Y, W):
    """Y: n x k outcomes (NaN allowed); W: n x R weights -> R x k weighted means."""
    M = (~np.isnan(Y)).astype(float)
    Y0 = np.nan_to_num(Y)
    return (W.T @ Y0) / (W.T @ M)


def contrast(df, treat_groups, ipw=True, refit=True):
    """Returns dict outcome -> (leaver mean, stayer mean, raw diff, se, ipw stayer mean, ipw diff, se)."""
    sub = df[df.group.isin(treat_groups) | (df.stayer == 1)].reset_index(drop=True)
    t = sub.group.isin(treat_groups).values
    W = sub[WCOLS].values.astype(float)
    Y = sub[OUTCOMES].values.astype(float)
    mt = wmean(Y[t], W[t])            # R+1 x k
    mc = wmean(Y[~t], W[~t])
    raw = mt - mc
    res = {"n_treat": int(t.sum()), "n_ctrl": int((~t).sum()),
           "wN_treat": float(W[t, 0].sum()), "wN_ctrl": float(W[~t, 0].sum())}
    if ipw:
        X = design(sub)
        Wc = np.zeros_like(W[~t])
        ps_main = None
        lr = LogisticRegression(C=1.0, max_iter=2000)
        for r in range(W.shape[1]):
            if r > 0 and not refit:
                ps = ps_main
            else:
                lr.fit(X, t.astype(int), sample_weight=W[:, r] / W[:, r].mean())
                ps = lr.predict_proba(X[~t])[:, 1]
                if r == 0:
                    ps_main = ps
            ps = np.clip(ps, 1e-4, 0.99)
            Wc[:, r] = W[~t, r] * ps / (1 - ps)
        mc_ipw = wmean(Y[~t], Wc)
        ipw_d = mt - mc_ipw
        # effective sample size of reweighted controls
        w0 = Wc[:, 0]
        res["ess_ctrl"] = float(w0.sum() ** 2 / (w0 ** 2).sum())
        res["max_ps"] = float(ps_main.max())
        res["balance"] = balance(sub, t, W[:, 0], Wc[:, 0])
    rows = []
    for j, o in enumerate(OUTCOMES):
        n_t = int((~np.isnan(Y[t, j])).sum())
        row = {"outcome": o, "n_treat_nonmissing": n_t, "leaver_mean": mt[0, j], "leaver_se": rep_se(mt[0, j], mt[1:, j]),
               "stayer_mean": mc[0, j], "raw_diff": raw[0, j], "raw_se": rep_se(raw[0, j], raw[1:, j])}
        if ipw:
            row.update({"stayer_ipw_mean": mc_ipw[0, j], "ipw_diff": ipw_d[0, j],
                        "ipw_se": rep_se(ipw_d[0, j], ipw_d[1:, j])})
        rows.append(row)
    out = pd.DataFrame(rows)
    for k in ("raw", "ipw"):
        if f"{k}_diff" in out:
            out[f"{k}_lo"] = out[f"{k}_diff"] - 1.96 * out[f"{k}_se"]
            out[f"{k}_hi"] = out[f"{k}_diff"] + 1.96 * out[f"{k}_se"]
    return out, res


def balance(sub, t, w, wc):
    X = pd.get_dummies(sub[["race_eth", "educ", "age_grp", "hh_type"]].astype(str))
    for b in BIN:
        X[b] = sub[b].values
    X = X.astype(float)
    rows = []
    for c in X.columns:
        x = X[c].values
        mt = np.average(x[t], weights=w[t])
        mc = np.average(x[~t], weights=w[~t])
        mi = np.average(x[~t], weights=wc)
        sd = np.sqrt((x[t].var() + x[~t].var()) / 2) or 1
        rows.append({"covariate": c, "leaver": mt, "stayer_raw": mc, "stayer_ipw": mi,
                     "smd_raw": (mt - mc) / sd, "smd_ipw": (mt - mi) / sd})
    return pd.DataFrame(rows)


def main():
    df = pd.read_parquet(os.path.join(DATA, "bay_origin_adults.parquet"))
    df["noBA"] = (df.educ != "BA+").astype(int)
    df["lowinc"] = (df.below_200pov == 1).astype(int)

    # group sizes
    gs = df.groupby("group").agg(n_unweighted=("PWGTP", "size"), weighted_persons=("PWGTP", "sum")).reset_index()
    gs["weighted_per_year"] = gs.weighted_persons / df.YEAR.nunique()
    gs.to_csv(os.path.join(OUT, "group_sizes.csv"), index=False)
    print(gs)

    # destinations of out-of-state leavers
    st = df[df.group == "left_ca"].groupby("ST").agg(n=("PWGTP", "size"), w=("PWGTP", "sum")).reset_index()
    st["share"] = st.w / st.w.sum()
    st.sort_values("w", ascending=False).to_csv(os.path.join(OUT, "left_ca_destination_states.csv"), index=False)

    samples = {"all": df, "lowinc_pov200": df[df.lowinc == 1], "noBA": df[df.noBA == 1],
               "householders": df[df.householder == 1],
               "age25_64": df[df.AGEP >= 25]}  # robustness: drops college-age movers
    allres, meta = [], []
    for sname, s in samples.items():
        for tname, tg in TREATMENTS.items():
            out, res = contrast(s, tg, ipw=True, refit=True)
            out.insert(0, "treatment", tname)
            out.insert(0, "sample", sname)
            allres.append(out)
            bal = res.pop("balance")
            if sname == "all":
                bal.to_csv(os.path.join(OUT, f"balance_{tname}.csv"), index=False)
            meta.append({"sample": sname, "treatment": tname, **res,
                         "max_abs_smd_raw": bal.smd_raw.abs().max(), "max_abs_smd_ipw": bal.smd_ipw.abs().max()})
            print(sname, tname, res, flush=True)
    pd.concat(allres).to_csv(os.path.join(OUT, "leaver_vs_stayer_contrasts.csv"), index=False)
    pd.DataFrame(meta).to_csv(os.path.join(OUT, "contrast_samples_meta.csv"), index=False)

    # subgroup outcomes: any leaver vs stayers within race/ethnicity and education groups
    sg = []
    for var in ["race_eth", "educ"]:
        for lvl, s in df.groupby(var):
            out, res = contrast(s, TREATMENTS["left_any"], ipw=True, refit=True)
            out.insert(0, "level", lvl)
            out.insert(0, "subgroup_var", var)
            out["n_leavers"] = res["n_treat"]
            out["n_stayers"] = res["n_ctrl"]
            sg.append(out)
            print(var, lvl, res["n_treat"], flush=True)
    pd.concat(sg).to_csv(os.path.join(OUT, "subgroup_contrasts_left_any.csv"), index=False)


if __name__ == "__main__":
    main()
