"""Shared helpers for the E2 robustness scripts (s04-s07). Reads E2 outputs; never writes outside
outputs/robustness/ and figs/robustness/. Hyper-parameters are the val-tuned ones stored in outputs/run_log.json
(chosen by s03 on the 2025-H2 validation window), so nothing here is tuned on the 2026 test set."""
import os, sys, json, importlib.util, warnings
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import *
import s03_model as M
import lightgbm as lgb
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, roc_auc_score, average_precision_score
warnings.filterwarnings("ignore")

ROUT = os.path.join(OUT, "robustness"); RFIG = os.path.join(FIG, "robustness")
os.makedirs(ROUT, exist_ok=True); os.makedirs(RFIG, exist_ok=True)
E6 = os.path.join(ROOT, "analysis/e6_unit_replacement")
E6_EXTRA = os.path.join(E6, "cache/extra.parquet")

def tuned():
    log = json.load(open(os.path.join(OUT, "run_log.json")))
    v = log["val"]
    return v["lgb_reg_params"], v["lgb_clf_params"], v["ridge_alpha"], v["logit_C"], log["thresholds_from_val"]

def load_sample():
    """Rows ordered train, val, test (stable), exactly as s03 concatenates them, so the out-of-fold target encodings
    (KFold over row order) and hence the refit models reproduce s03 bit-for-bit."""
    S = pd.read_parquet(SAMPLE)
    S = S[S.r.notna()].reset_index(drop=True)
    rank = S.split.map({"train": 0, "val": 1, "test": 2})
    return S.iloc[np.argsort(rank.values, kind="mergesort")].reset_index(drop=True)

def _textflags():
    spec = importlib.util.spec_from_file_location("e6_textflags", os.path.join(E6, "textflags.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def add_concessions(S):
    """Concession weeks from the unit's CURRENT FOR_RENT listing (E6 regex on description + special_offer), attached
    only to pairs whose NEXT episode is that current listing (ep + 1 == last episode of the zpid)."""
    import duckdb
    con = duckdb.connect(DB, read_only=True)
    last = con.execute("select zpid, max(ep) max_ep from rep group by 1").df(); con.close()
    tf = _textflags()
    ex = pd.read_parquet(E6_EXTRA, columns=["zpid", "homeStatus", "description", "special_offer"])
    ex = ex[ex.homeStatus == "FOR_RENT"].drop_duplicates("zpid").copy()
    ex["cw"] = (ex.description.fillna("") + " || " + ex.special_offer.fillna("")).map(tf.concession_weeks)
    S = S.merge(last, on="zpid", how="left").merge(ex[["zpid", "cw"]].assign(cur_for_rent=1), on="zpid", how="left")
    S["conc_known"] = ((S.ep + 1 == S.max_ep) & (S.cur_for_rent == 1)).astype(int)   # next episode = current listing
    S["conc_weeks"] = np.where(S.conc_known == 1, S.cw, np.nan)
    S["conc_flag"] = S.conc_weeks.notna().astype(int)
    S["conc_weeks0"] = S.conc_weeks.fillna(0.0)
    # effective first-year rent on a 12-month lease: ask x (1 - weeks_free / 52)
    S["next_eff"] = S.next_first * (1 - S.conc_weeks0 / 52)
    S["r_eff"] = (S.next_eff / S.last_p) ** (1 / S.start_gap_y) - 1
    S["y_eff"] = (S.r_eff > CAP).astype(int)
    return S.drop(columns=["cw", "cur_for_rent", "max_ep"])

# ---------------------------------------------------------------- model fitting with a configurable feature list
def lin_X(d, num, cols=None):
    X = pd.concat([d[num].astype(float), pd.get_dummies(d[M.CAT], dtype=float)], axis=1).replace([np.inf, -np.inf], np.nan)
    return X if cols is None else X.reindex(columns=cols, fill_value=0.0)

def fit_predict(fit, te, num=None, target="r", ytarget="y_over_cap", prm_r=None, prm_c=None, alpha=None, C=None,
                which=("lgb", "ridge", "clf", "logit")):
    """fit/te must already have features from M.add_features. Returns dict of test predictions."""
    num = num or M.NUM; feats = num + M.CAT
    p_r, p_c, a_, C_, _ = tuned()
    prm_r, prm_c = prm_r or p_r, prm_c or p_c
    alpha = alpha if alpha is not None else a_; C = C if C is not None else C_
    out = {}
    if "lgb" in which:
        out["lgb"] = lgb.LGBMRegressor(**prm_r).fit(fit[feats], fit[target]).predict(te[feats])
    cols = lin_X(fit, num).columns
    if "ridge" in which:
        m = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=alpha)).fit(lin_X(fit, num, cols), fit[target])
        out["ridge"] = m.predict(lin_X(te, num, cols))
    if "clf" in which and fit[ytarget].nunique() > 1:
        out["clf"] = lgb.LGBMClassifier(**prm_c).fit(fit[feats], fit[ytarget]).predict_proba(te[feats])[:, 1]
    if "logit" in which and fit[ytarget].nunique() > 1:
        m = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C=C, max_iter=2000)).fit(lin_X(fit, num, cols), fit[ytarget])
        out["logit"] = m.predict_proba(lin_X(te, num, cols))[:, 1]
    return out

def reg_row(y, p):
    return dict(MAE=mean_absolute_error(y, p), RMSE=float(np.sqrt(np.mean((np.asarray(p) - np.asarray(y)) ** 2))),
                bias=float(np.mean(np.asarray(p) - np.asarray(y))))

def auc(y, s):
    return roc_auc_score(y, s) if pd.Series(y).nunique() > 1 else np.nan

def ap(y, s):
    return average_precision_score(y, s) if pd.Series(y).nunique() > 1 else np.nan

# ---------------------------------------------------------------- figure style (same as s03)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
BLUE, ORANGE, INK, INK2, MUTED = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#b5b4ae"
def style(ax):
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]: ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=9); ax.grid(color="#e8e7e3", lw=0.6); ax.set_axisbelow(True)
plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold", "text.color": INK,
                     "axes.labelcolor": INK2, "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})

def md(df, floatfmt=".4f"):
    try: return df.to_markdown(index=False, floatfmt=floatfmt)
    except Exception: return df.to_string(index=False)
