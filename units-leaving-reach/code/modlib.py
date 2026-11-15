"""Feature construction, baselines and model fitting shared by s03 (main test) and s04 (robustness)."""
import os, sys, warnings, numpy as np, pandas as pd, lightgbm as lgb
warnings.filterwarnings("ignore", category=UserWarning)
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.model_selection import KFold
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

HOMETYPES = ["APARTMENT", "SINGLE_FAMILY", "CONDO", "TOWNHOUSE", "MULTI_FAMILY"]
COUNTIES = ["Alameda County", "Contra Costa County", "Marin County", "Napa County", "San Francisco County",
            "San Mateo County", "Santa Clara County", "Solano County", "Sonoma County"]
UDP_GROUP = {"LISD": "low_income", "OD": "low_income", "ARG": "gentrifying", "EOG": "gentrifying",
             "AdvG": "gentrifying", "SMMI": "moderate", "ARE": "exclusive", "BE": "exclusive", "SAE": "exclusive"}

UNIT = ["beds", "baths", "sqft", "age", "ppsf", "log_last_p", "start_gap_y", "prev_year", "next_month", "ep",
        "n_changes", "prev_cut", "mgmt", "large_landlord", "sold_between", "hh"] + \
       [f"ht_{h}" for h in HOMETYPES] + [f"cty_{c[:-7].replace(' ', '_')}" for c in COUNTIES]
HEAD = ["headroom", "req_growth", "ami_share0"]
MKT = ["mkt_chg", "mkt_mom", "mkt_lvl0", "te_zip_r", "te_zip_cap", "te_cty_r", "te_zip_y"]
TRACT = ["risk_backtest", "per_rent_18", "per_nonwhite_18", "real_hinc_18", "per_all_li_18", "per_col_18",
         "real_mrent_18", "pctch_real_mrent_12_18", "per_limove_18", "rail", "z_flip_pre", "z_apprec_pre",
         "z_ppsf_growth_pre", "z_rent_pre", "z_nb_flip_pre"] + [f"udp_{g}" for g in ["low_income", "gentrifying", "moderate", "exclusive"]]
LABOR = ["ai_positioned_share", "exposed_share", "frontline_share", "log_postings"]
SETS = {"unit+headroom+market": UNIT + HEAD + MKT,
        "+ tract (displacement workstream)": UNIT + HEAD + MKT + TRACT,
        "+ tract + city jobs (all workstreams)": UNIT + HEAD + MKT + TRACT + LABOR}
ALL = SETS["+ tract + city jobs (all workstreams)"]
GROUPS = {"unit": UNIT, "headroom": HEAD, "market": MKT, "tract": TRACT, "city jobs": LABOR}

def static_features(df):
    df = df.replace([np.inf, -np.inf], np.nan)
    for h in HOMETYPES: df[f"ht_{h}"] = (df.homeType == h).astype(int)
    for c in COUNTIES: df[f"cty_{c[:-7].replace(' ', '_')}"] = (df.county == c).astype(int)
    df["udp_group"] = df.udp_typ.map(UDP_GROUP)
    for g in ["low_income", "gentrifying", "moderate", "exclusive"]:
        df[f"udp_{g}"] = np.where(df.udp_group.isna(), np.nan, (df.udp_group == g).astype(float))
    return df

def _te(fit, app, key, target, k=20, prior=None):
    prior = fit[target].mean() if prior is None else prior
    g = fit.groupby(key)[target].agg(["sum", "count"])
    m = (g["sum"] + k * prior) / (g["count"] + k)
    return app[key].map(m).fillna(prior).values

def add_encodings(fit, app_list, e2_hist, fit_end):
    """Target encodings fit on `fit` rows only. ZIP/county mean turnover change r and over-cap rate come from ALL
    movement-E2 pairs re-listed before `fit_end` (a larger history, same time cut). ZIP rate of the label itself is
    out-of-fold inside `fit`."""
    h = e2_hist[e2_hist.next_start < fit_end]
    def enc(d):
        d = d.copy()
        d["te_zip_r"] = _te(h, d, "zipcode", "r"); d["te_zip_cap"] = _te(h, d, "zipcode", "y_over_cap")
        d["te_cty_r"] = _te(h, d, "county", "r", k=5)
        return d
    fit = enc(fit); apps = [enc(a) for a in app_list]
    oof = np.zeros(len(fit))
    for tr, te in KFold(5, shuffle=True, random_state=SEED).split(fit):
        oof[te] = _te(fit.iloc[tr], fit.iloc[te], "zipcode", "y", prior=fit.y.mean())
    fit["te_zip_y"] = oof
    for a in apps: a["te_zip_y"] = _te(fit, a, "zipcode", "y")
    return fit, apps

# ---------------------------------------------------------------- baselines (score: higher = more likely to leave reach)
def baseline_scores(d):
    return {"Majority class (never leaves reach)": np.zeros(len(d)),
            "UDP typology rule (low-income or gentrifying tract)": d.udp_group.isin(["low_income", "gentrifying"]).astype(float).values,
            "Legal-max rule: crosses if rent rises at AB 1482 max (10%/yr)": -d.req_growth.values,
            "ZIP-trend rule: ZIP median turnover change vs growth needed": (d.te_zip_r - d.req_growth).values}
RULE_THR = {"Legal-max rule: crosses if rent rises at AB 1482 max (10%/yr)": -0.10,
            "ZIP-trend rule: ZIP median turnover change vs growth needed": 0.0,
            "UDP typology rule (low-income or gentrifying tract)": 0.5,
            "Majority class (never leaves reach)": 0.5}

# ---------------------------------------------------------------- models
def fit_logit(Xtr, ytr, C):
    m = make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(),
                      LogisticRegression(C=C, max_iter=5000))
    return m.fit(Xtr, ytr)

LGB_GRID = [dict(num_leaves=nl, min_child_samples=mc) for nl in (7, 15, 31) for mc in (20, 50, 100)]
def lgb_params(p, seed=SEED):
    return dict(objective="binary", learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                reg_lambda=1.0, random_state=seed, deterministic=True, force_row_wise=True, verbose=-1, **p)

def tune_lgb(Xtr, ytr, Xva, yva):
    best = None
    for p in LGB_GRID:
        m = lgb.LGBMClassifier(n_estimators=3000, **lgb_params(p))
        m.fit(Xtr, ytr, eval_set=[(Xva, yva)], callbacks=[lgb.early_stopping(100, verbose=False)])
        auc = roc_auc_score(yva, m.predict_proba(Xva)[:, 1])
        if best is None or auc > best[0]: best = (auc, p, max(m.best_iteration_, 50))
    return best

def fit_lgb(X, y, p, n, seed=SEED):
    return lgb.LGBMClassifier(n_estimators=n, **lgb_params(p, seed)).fit(X, y)

def tune_logit(Xtr, ytr, Xva, yva):
    res = [(roc_auc_score(yva, fit_logit(Xtr, ytr, C).predict_proba(Xva)[:, 1]), C) for C in (0.01, 0.1, 1, 10)]
    return max(res)

# ---------------------------------------------------------------- metrics
def f1_threshold(y, s):
    qs = np.unique(np.quantile(s, np.linspace(0.3, 0.99, 140)))
    f = [(2 * ((s >= t) & (y == 1)).sum() / max((s >= t).sum() + (y == 1).sum(), 1), t) for t in qs]
    return max(f)[1]

def metrics(y, s, thr=None, budget_thr=None):
    y = np.asarray(y); s = np.asarray(s, float)
    out = dict(n=len(y), prevalence=y.mean())
    out["AUC"] = roc_auc_score(y, s) if 0 < y.sum() < len(y) else np.nan
    out["PR_AUC"] = average_precision_score(y, s) if y.sum() > 0 else np.nan
    for name, t in (("", thr), ("budget_", budget_thr)):
        if t is None: continue
        f = s >= t; tp = (f & (y == 1)).sum()
        out[name + "flagged"] = f.mean()
        out[name + "precision"] = tp / f.sum() if f.sum() else np.nan
        out[name + "recall"] = tp / (y == 1).sum() if (y == 1).sum() else np.nan
        out[name + "FPR"] = (f & (y == 0)).sum() / (y == 0).sum() if (y == 0).sum() else np.nan
        if name == "": out["F1"] = 2 * tp / (f.sum() + (y == 1).sum()) if (f.sum() + (y == 1).sum()) else np.nan
    return out

def boot_auc_diff(y, s1, s2, B=1000, seed=SEED):
    rng = np.random.default_rng(seed); y = np.asarray(y); d = []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        if 0 < y[i].sum() < len(i): d.append(roc_auc_score(y[i], s1[i]) - roc_auc_score(y[i], s2[i]))
    return np.percentile(d, [2.5, 97.5])

def boot_auc_ci(y, s, B=1000, seed=SEED):
    rng = np.random.default_rng(seed); y = np.asarray(y); a = []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        if 0 < y[i].sum() < len(i): a.append(roc_auc_score(y[i], s[i]))
    return np.percentile(a, [2.5, 97.5])

def load():
    df = static_features(pd.read_parquet(DATA))
    hist = pd.read_parquet(E2_SAMPLE, columns=["zipcode", "county", "next_start", "r", "y_over_cap"])
    return df, hist
