"""Step 4: can Zillow-only information flag rental buildings that sit in a service desert?
Unit = rental building (distinct listing coordinate). Label `desert` = nearest grocery > 1.6 km OR nearest clinic
> 3.2 km OR nearest bus/transit stop > 800 m (Google Maps Places, straight line). Features come from Zillow only.
Spatial held-out test: the region is cut into 0.05-degree blocks (~5.5 x 4.4 km); 25% of occupied blocks (seed 42) are
test and never used for training, tuning or threshold choice. Tuning / threshold = 5-fold GroupKFold over train blocks.
Models: B0 county prior; B1 logistic on log distance to nearest big-city downtown; M1 LightGBM on listing attributes
(rent, beds, size, age, type, landlord, income gate) + county; M2 = M1 + Zillow-derived spatial context (property
density, downtown distance); M3 = M2 + raw lat/lon. Writes outputs/model_*.csv and figs/model_*.png."""
import os, sys, numpy as np, pandas as pd, lightgbm as lgb, statsmodels.formula.api as smf
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, precision_score, recall_score, brier_score_loss
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from s03_compare import add_labels

BLOCK = 0.05; TEST_FRAC = 0.25


def buildings(d):
    d = add_labels(d)
    d["rent_psf"] = d.rent / d.sqft
    d["rent_per_person"] = d.rent / d.hh
    g = d.groupby("loc_id")
    b = g.agg(lat=("lat", "first"), lon=("lon", "first"), county=("county", "first"), zipcode=("zipcode", "first"),
              city=("city", "first"), typ_group=("typ_group", "first"), desert=("desert", "first"),
              fail_grocery=("fail_grocery", "first"), fail_clinic=("fail_clinic", "first"), fail_transit=("fail_transit", "first"),
              d_grocery=("d_grocery", "first"), d_clinic=("d_clinic", "first"), d_transit=("d_transit", "first"),
              n_listings=("zpid", "size"), med_rent=("rent", "median"), min_rent=("rent", "min"), max_rent=("rent", "max"),
              med_beds=("beds", "median"), max_beds=("beds", "max"), med_baths=("baths", "median"), med_sqft=("sqft", "median"),
              med_rent_psf=("rent_psf", "median"), med_rent_pp=("rent_per_person", "median"), med_year=("yearBuilt", "median"),
              share_apt=("homeType_s", lambda s: (s == "APARTMENT").mean()),
              share_sfr=("homeType_s", lambda s: (s == "SINGLE_FAMILY").mean()),
              share_mgmt=("mgmt", "mean"), med_days_on=("days_on", "median"),
              share_LI=("qual_LI", "mean"), share_VLI=("qual_VLI", "mean"), min_ami_needed=("ami_needed", "min"),
              z_props_1000=("z_props_1000", "first"), z_props_3000=("z_props_3000", "first"),
              d_city_center=("d_city_center", "first")).reset_index()
    b["any_VLI"] = b.share_VLI > 0; b["any_LI"] = b.share_LI > 0
    b["log_d_city"] = np.log(b.d_city_center)
    # rent relative to the county median building rent (affordability within the local market)
    b["rent_rel_county"] = b.med_rent / b.groupby("county").med_rent.transform("median")
    b["block"] = (np.floor(b.lat / BLOCK).astype(int).astype(str) + "_" + np.floor(b.lon / BLOCK).astype(int).astype(str))
    return b


ATTR = ["med_rent", "min_rent", "max_rent", "med_beds", "max_beds", "med_baths", "med_sqft", "med_rent_psf", "med_rent_pp",
        "med_year", "share_apt", "share_sfr", "share_mgmt", "med_days_on", "n_listings", "share_LI", "share_VLI",
        "min_ami_needed", "rent_rel_county", "county_c"]
CTX = ["z_props_1000", "z_props_3000", "log_d_city"]
FEATS = {"M1_attributes": ATTR, "M2_attr+zillow_context": ATTR + CTX, "M3_M2+latlon": ATTR + CTX + ["lat", "lon"]}
GRID = [dict(num_leaves=nl, min_child_samples=mc, learning_rate=0.03, n_estimators=400, subsample=0.8, subsample_freq=1,
             colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, random_state=SEED)
        for nl in (7, 15, 31) for mc in (20, 60)]


def best_f1_threshold(y, p):
    ts = np.unique(np.quantile(p, np.linspace(0.5, 0.995, 120)))
    f = [f1_score(y, p >= t, zero_division=0) for t in ts]
    return float(ts[int(np.argmax(f))])


def fit_predict(name, tr, te, cv_folds):
    """Returns (oof train preds, test preds, chosen params)."""
    y = tr.desert.values
    if name == "B0_county_prior":
        def f(a, b): m = a.groupby("county").desert.mean(); return b.county.map(m).fillna(a.desert.mean()).values
        oof = np.zeros(len(tr))
        for i, j in cv_folds: oof[j] = f(tr.iloc[i], tr.iloc[j])
        return oof, f(tr, te), {}
    if name == "B1_logit_dist_city_center":
        def f(a, b): return LogisticRegression().fit(a[["log_d_city"]], a.desert).predict_proba(b[["log_d_city"]])[:, 1]
        oof = np.zeros(len(tr))
        for i, j in cv_folds: oof[j] = f(tr.iloc[i], tr.iloc[j])
        return oof, f(tr, te), {}
    X, Xt = tr[FEATS[name]], te[FEATS[name]]
    best, best_s, best_oof = None, -1, None
    for prm in GRID:
        oof = np.zeros(len(tr))
        for i, j in cv_folds:
            m = lgb.LGBMClassifier(**prm).fit(X.iloc[i], y[i], categorical_feature=["county_c"])
            oof[j] = m.predict_proba(X.iloc[j])[:, 1]
        s = average_precision_score(y, oof)
        if s > best_s: best, best_s, best_oof = prm, s, oof
    m = lgb.LGBMClassifier(**best).fit(X, y, categorical_feature=["county_c"])
    fit_predict.models[name] = m
    return best_oof, m.predict_proba(Xt)[:, 1], {k: best[k] for k in ("num_leaves", "min_child_samples")}
fit_predict.models = {}


def metrics(y, p, thr, w=None):
    yhat = p >= thr
    return dict(n=len(y), prevalence=np.average(y, weights=w), auc=roc_auc_score(y, p, sample_weight=w),
                avg_precision=average_precision_score(y, p, sample_weight=w),
                f1=f1_score(y, yhat, sample_weight=w, zero_division=0), precision=precision_score(y, yhat, sample_weight=w, zero_division=0),
                recall=recall_score(y, yhat, sample_weight=w, zero_division=0), flagged_share=np.average(yhat, weights=w),
                brier=brier_score_loss(y, p, sample_weight=w))


def block_bootstrap(te, preds, names, reps=500):
    rng = np.random.default_rng(SEED); blocks = te.block.unique(); idx = {b: np.where(te.block.values == b)[0] for b in blocks}
    out = {n: [] for n in names}; diff = []
    for _ in range(reps):
        s = np.concatenate([idx[b] for b in rng.choice(blocks, len(blocks), replace=True)])
        y = te.desert.values[s]
        if y.min() == y.max(): continue
        a = {n: roc_auc_score(y, preds[n][s]) for n in names}
        for n in names: out[n].append(a[n])
        diff.append(a["M2_attr+zillow_context"] - a["B1_logit_dist_city_center"])
    r = pd.DataFrame({n: np.percentile(v, [2.5, 97.5]) for n, v in out.items()}, index=["auc_lo", "auc_hi"]).T
    return r, np.percentile(diff, [2.5, 50, 97.5])


def main():
    d = pd.read_parquet(os.path.join(CACHE, "listings_access.parquet"))
    b = buildings(d)
    b["county_c"] = b.county.astype("category")
    rng = np.random.default_rng(SEED)
    blocks = np.sort(b.block.unique()); test_blocks = set(rng.choice(blocks, int(round(TEST_FRAC * len(blocks))), replace=False))
    b["split"] = np.where(b.block.isin(test_blocks), "test", "train")
    tr, te = b[b.split == "train"].reset_index(drop=True), b[b.split == "test"].reset_index(drop=True)
    print(f"buildings {len(b)} (blocks {len(blocks)}); train {len(tr)} / test {len(te)}; prevalence train {tr.desert.mean():.3f} test {te.desert.mean():.3f}")
    pd.DataFrame([dict(split=s, n_buildings=len(x), n_blocks=x.block.nunique(), n_listings=x.n_listings.sum(),
                       desert_rate=x.desert.mean(), desert_rate_listing_w=np.average(x.desert, weights=x.n_listings))
                  for s, x in [("train", tr), ("test", te)]]).to_csv(os.path.join(OUT, "model_split.csv"), index=False)
    folds = list(GroupKFold(5).split(tr, tr.desert, tr.block))
    names = ["B0_county_prior", "B1_logit_dist_city_center"] + list(FEATS)
    rows, preds, params = [], {}, {}
    for n in names:
        oof, pt, prm = fit_predict(n, tr, te, folds)
        thr = best_f1_threshold(tr.desert.values, oof)
        preds[n] = pt; params[n] = prm
        rows.append(dict(model=n, weight="building", threshold=thr, cv_auc_train=roc_auc_score(tr.desert, oof), params=str(prm),
                         **metrics(te.desert.values, pt, thr)))
        rows.append(dict(model=n, weight="listing", threshold=thr, cv_auc_train=np.nan, params=str(prm),
                         **metrics(te.desert.values, pt, thr, w=te.n_listings.values)))
        te[f"p_{n}"] = pt; te[f"thr_{n}"] = thr
    m = pd.DataFrame(rows)
    ci, dci = block_bootstrap(te, preds, names)
    m = m.merge(ci, left_on="model", right_index=True, how="left")
    m.loc[m.weight == "listing", ["auc_lo", "auc_hi"]] = np.nan
    m.to_csv(os.path.join(OUT, "model_metrics_test.csv"), index=False)
    pd.DataFrame([dict(comparison="AUC(M2) - AUC(B1)", lo=dci[0], median=dci[1], hi=dci[2])]).to_csv(
        os.path.join(OUT, "model_auc_diff_bootstrap.csv"), index=False)
    pd.set_option("display.width", 250)
    print(m.drop(columns=["params"]).round(3).to_string()); print("AUC(M2)-AUC(B1) 95% block-bootstrap:", np.round(dci, 3))
    # feature importance (gain) of M2
    mm = fit_predict.models["M2_attr+zillow_context"]
    pd.Series(mm.booster_.feature_importance("gain"), index=FEATS["M2_attr+zillow_context"]).sort_values(ascending=False).rename(
        "gain").to_csv(os.path.join(OUT, "model_feature_importance_M2.csv"))
    subgroups(te, tr)
    failures(te)
    affordability_test(b)
    product(te)
    figs(te, m)


def subgroups(te, tr):
    q = tr.med_rent.quantile([.25, .5, .75]).values
    te["rent_tier"] = pd.cut(te.med_rent, [-np.inf, *q, np.inf], labels=["Q1 cheapest", "Q2", "Q3", "Q4 priciest"]).astype(str)
    te["vli_bldg"] = np.where(te.any_VLI, "has <=50% AMI-reachable unit", "no <=50% AMI-reachable unit")
    te["typ_group_s"] = te.typ_group.fillna("NA (no typology)")
    rows = []
    for g in ["county", "typ_group_s", "rent_tier", "vli_bldg"]:
        for k, x in te.groupby(g):
            for n in ["B1_logit_dist_city_center", "M2_attr+zillow_context"]:
                y, p, thr = x.desert.values, x[f"p_{n}"].values, x[f"thr_{n}"].iloc[0]
                yh = p >= thr
                rows.append(dict(subgroup=g, value=k, model=n, n=len(x), n_desert=int(y.sum()), prevalence=y.mean(),
                                 auc=roc_auc_score(y, p) if 5 <= y.sum() <= len(y) - 5 else np.nan,
                                 recall=yh[y == 1].mean() if y.sum() else np.nan,
                                 precision=y[yh].mean() if yh.sum() else np.nan,
                                 fpr=yh[y == 0].mean() if (y == 0).sum() else np.nan,
                                 mean_pred=p.mean()))
    s = pd.DataFrame(rows); s.to_csv(os.path.join(OUT, "model_subgroup_metrics_test.csv"), index=False)
    print(s[s.model.str.startswith("M2")].round(3).to_string(index=False))


def failures(te):
    n = "M2_attr+zillow_context"; thr = te[f"thr_{n}"].iloc[0]
    te["err"] = np.select([(te.desert == 1) & (te[f"p_{n}"] < thr), (te.desert == 0) & (te[f"p_{n}"] >= thr)], ["FN missed desert", "FP false alarm"], "ok")
    def agg(x):
        return pd.Series(dict(n_buildings=len(x), n_listings=x.n_listings.sum(), mean_pred=x[f"p_{n}"].mean(),
                              fail_grocery=int(x.fail_grocery.sum()), fail_clinic=int(x.fail_clinic.sum()), fail_transit=int(x.fail_transit.sum()),
                              med_d_grocery_100m=round(x.d_grocery.median(), -2), med_d_clinic_100m=round(x.d_clinic.median(), -2),
                              med_d_transit_100m=round(x.d_transit.median(), -2), med_rent_100=round(x.med_rent.median(), -2),
                              med_z_props_1km=x.z_props_1000.median(), med_d_city_km=round(x.d_city_center.median() / 1000, 1),
                              typology=x.typ_group.mode().iloc[0] if x.typ_group.notna().any() else "NA"))
    f = te[te.err != "ok"].groupby(["err", "county", "city", "zipcode"]).apply(agg, include_groups=False).reset_index()
    f = f.sort_values(["err", "n_buildings"], ascending=[True, False])
    f.to_csv(os.path.join(OUT, "model_failures_by_area_test.csv"), index=False)
    print(f.groupby("err").head(8).to_string(index=False))
    # error-type profile
    prof = te.groupby("err")[["med_rent", "z_props_1000", "d_city_center", "share_apt", "n_listings", "d_grocery", "d_clinic", "d_transit"]].median()
    prof["n"] = te.err.value_counts(); prof.to_csv(os.path.join(OUT, "model_error_profile_test.csv"))
    print(prof.round(1).to_string())


def affordability_test(b):
    """Does affordability predict isolation? Building-level logit of desert on log median rent (+beds), county FE."""
    x = b.dropna(subset=["med_rent"]).copy(); x["lr"] = np.log(x.med_rent); x["lpp"] = np.log(x.med_rent_pp)
    rows = []
    for f in ["desert ~ lr + med_beds", "desert ~ lr + med_beds + C(county)", "desert ~ lpp + C(county)",
              "desert ~ any_VLI + C(county)", "desert ~ any_LI + C(county)"]:
        r = smf.logit(f, data=x.assign(any_VLI=x.any_VLI.astype(int), any_LI=x.any_LI.astype(int))).fit(disp=0, cov_type="cluster", cov_kwds={"groups": pd.factorize(x.block)[0]})
        v = [k for k in r.params.index if k in ("lr", "lpp", "any_VLI", "any_LI")][0]
        rows.append(dict(formula=f, term=v, coef=r.params[v], se=r.bse[v], p=r.pvalues[v], odds_ratio=np.exp(r.params[v]), n=int(r.nobs)))
    t = pd.DataFrame(rows); t.to_csv(os.path.join(OUT, "affordability_vs_desert_logit.csv"), index=False)
    print(t.round(4).to_string(index=False))


def product(te):
    """Held-out-area flag list: ZIPs where buildings with <=80% AMI-reachable units are predicted/observed deserts."""
    n = "M2_attr+zillow_context"; x = te[te.any_LI]
    z = x.groupby(["county", "zipcode"]).agg(n_buildings=("loc_id", "size"), n_listings=("n_listings", "sum"),
                                              obs_desert_share=("desert", "mean"), pred_desert_share=(f"p_{n}", "mean")).reset_index()
    z = z[z.n_buildings >= 5].sort_values("pred_desert_share", ascending=False)
    z.to_csv(os.path.join(OUT, "model_flagged_zips_li_units_test.csv"), index=False)


def figs(te, m):
    from sklearn.metrics import roc_curve, precision_recall_curve
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    for n, c in zip(["B0_county_prior", "B1_logit_dist_city_center", "M1_attributes", "M2_attr+zillow_context", "M3_M2+latlon"],
                    ["#999", "#e6a23c", "#7fb3d5", "#c0392b", "#5b2c6f"]):
        fpr, tpr, _ = roc_curve(te.desert, te[f"p_{n}"]); pr, rc, _ = precision_recall_curve(te.desert, te[f"p_{n}"])
        a = m[(m.model == n) & (m.weight == "building")].iloc[0]
        ax[0].plot(fpr, tpr, color=c, label=f"{n} AUC {a.auc:.2f}"); ax[1].plot(rc, pr, color=c, label=f"{n} AP {a.avg_precision:.2f}")
    ax[0].plot([0, 1], [0, 1], ls=":", color="#ccc"); ax[0].set_xlabel("false positive rate"); ax[0].set_ylabel("true positive rate")
    ax[1].axhline(te.desert.mean(), ls=":", color="#ccc"); ax[1].set_xlabel("recall"); ax[1].set_ylabel("precision")
    for a in ax: a.legend(fontsize=7, frameon=False)
    fig.suptitle("Service-desert rental buildings, spatially held-out test blocks", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "model_roc_pr_test.png"), dpi=140); plt.close(fig)
    n = "M2_attr+zillow_context"; thr = te[f"thr_{n}"].iloc[0]
    fig, ax = plt.subplots(figsize=(7, 7.5))
    col = np.select([(te.desert == 1) & (te[f"p_{n}"] >= thr), (te.desert == 1), (te[f"p_{n}"] >= thr)], ["#1a9850", "#c0392b", "#e6a23c"], "#cccccc")
    ax.scatter(te.lon, te.lat, c=col, s=6)
    for c, l in [("#1a9850", "desert, flagged (TP)"), ("#c0392b", "desert, missed (FN)"), ("#e6a23c", "false alarm (FP)"), ("#cccccc", "served, not flagged")]:
        ax.scatter([], [], c=c, s=12, label=l)
    ax.legend(fontsize=8, frameon=False, loc="lower left"); ax.set_aspect(1 / np.cos(np.radians(37.8)))
    ax.set_title("M2 on held-out test blocks (rental buildings)", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "model_test_errors_map.png"), dpi=140); plt.close(fig)


if __name__ == "__main__":
    main()
