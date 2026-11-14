"""Step 2: predict hourly pay from title + description + location (TF-IDF + ridge on log hourly pay).

Split: GroupShuffleSplit by company (80/20), so no employer appears in both train and test.
Baselines (fit on train only):
  B1 location-only : median hourly by county (fallback area, then global)
  B2 title x metro : median by normalized title x area (fallback normalized title, then area, then global)
Outputs: outputs/salary_model_metrics.csv, salary_model_subgroups.csv, salary_model_failures.csv,
         postings_with_pay.parquet (observed or imputed hourly), pay_missing_share.csv
"""
import os, sys, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from occupations import LABELS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "outputs")
SEED = 42


def norm_title(t):
    t = str(t).lower()
    t = re.sub(r"\(.*?\)|\[.*?\]", " ", t)
    t = re.sub(r"\b(i{1,3}|iv|[0-9]+|sr|senior|jr|junior|part[- ]time|full[- ]time|pt|ft|per diem|seasonal|"
               r"temporary|temp|remote|hybrid|hiring now|immediate(ly)?|urgent(ly)?)\b", " ", t)
    t = re.sub(r"[-–|/,:].*$", " ", t)  # keep text before first separator
    t = re.sub(r"[^a-z ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def med_lookup(train, test, keys_list, y="y"):
    """Hierarchical median: try each key set in order, first with >=5 train rows wins."""
    pred = pd.Series(np.nan, index=test.index)
    for keys in keys_list:
        g = train.groupby(keys)[y].agg(["median", "size"])
        g = g[g["size"] >= 5]["median"]
        m = test[keys].merge(g.rename("m"), left_on=keys, right_index=True, how="left")["m"]
        pred = pred.fillna(m)
    return pred.fillna(train[y].median())


def features(fit_df, dfs):
    v_title_w = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    v_title_c = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=5, sublinear_tf=True, max_features=60000)
    v_desc = TfidfVectorizer(ngram_range=(1, 2), min_df=5, max_df=0.5, sublinear_tf=True, max_features=150000,
                             stop_words="english")
    ohe = OneHotEncoder(handle_unknown="ignore", min_frequency=5)
    cat = lambda d: d[["county_f", "area", "job_type_f"]]
    desc = lambda d: d.description_text.fillna("").str.slice(0, 4000)
    v_title_w.fit(fit_df.job_title.fillna("")); v_title_c.fit(fit_df.job_title.fillna(""))
    v_desc.fit(desc(fit_df)); ohe.fit(cat(fit_df))
    out = []
    for d in dfs:
        X = sparse.hstack([v_title_w.transform(d.job_title.fillna("")) * 1.0,
                           v_title_c.transform(d.job_title.fillna("")) * 1.0,
                           v_desc.transform(desc(d)) * 0.7,
                           ohe.transform(cat(d)) * 1.0]).tocsr()
        out.append(X)
    return out


def metrics(y, p, name):
    return dict(model=name, n=len(y), MAE=mean_absolute_error(y, p), RMSE=mean_squared_error(y, p) ** 0.5,
                R2=r2_score(y, p), MAPE_pct=100 * np.mean(np.abs(p - y) / y),
                R2_log=r2_score(np.log(y), np.log(p)))


def wage_tier(y):
    return pd.cut(y, [0, 20, 30, 50, 1e9], labels=["<$20", "$20-30", "$30-50", "$50+"], right=False)


def main():
    df = pd.read_parquet(os.path.join(OUT, "postings_clean.parquet"))
    df["county_f"] = df.county.fillna("unknown")
    df["job_type_f"] = df.job_type.fillna("unknown").str.lower().str.slice(0, 40)
    df["ntitle"] = df.job_title.map(norm_title)
    df["occ_f"] = df.occ.fillna("other")
    df["company_f"] = df.company_name.fillna("unknown_" + df.jobid)
    lab = df[df.pay_mid.notna()].copy()
    lab["y"] = lab.pay_mid
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED)
    tr_idx, te_idx = next(gss.split(lab, groups=lab.company_f))
    tr, te = lab.iloc[tr_idx].copy(), lab.iloc[te_idx].copy()
    assert not set(tr.company_f) & set(te.company_f)
    print(f"train {len(tr)}  test {len(te)}  companies train {tr.company_f.nunique()} test {te.company_f.nunique()}")

    te["p_b1"] = med_lookup(tr, te, [["county_f"], ["area"]])
    te["p_b2"] = med_lookup(tr, te, [["ntitle", "area"], ["ntitle"], ["occ_f", "area"], ["area"]])

    Xtr, Xte = features(tr, [tr, te])
    best = None
    # small alpha search on an inner company-grouped split of train
    itr, iva = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED + 1).split(tr, groups=tr.company_f))
    for a in [0.3, 1.0, 3.0]:
        r = Ridge(alpha=a, solver="sag", max_iter=2000, random_state=SEED) if False else Ridge(alpha=a)
        r.fit(Xtr[itr], np.log(tr.y.values[itr]))
        mae = mean_absolute_error(tr.y.values[iva], np.exp(r.predict(Xtr[iva])))
        print(f"  alpha {a}: inner-val MAE {mae:.2f}")
        if best is None or mae < best[1]:
            best = (a, mae)
    alpha = best[0]
    ridge = Ridge(alpha=alpha).fit(Xtr, np.log(tr.y.values))
    te["p_ridge"] = np.exp(ridge.predict(Xte))

    m = pd.DataFrame([metrics(te.y, te.p_b1, "B1 median by county"),
                      metrics(te.y, te.p_b2, "B2 median by normalized title x area"),
                      metrics(te.y, te.p_ridge, f"TF-IDF(title+desc)+location ridge (alpha={alpha})")])
    m.to_csv(os.path.join(OUT, "salary_model_metrics.csv"), index=False)
    print(m.round(3).to_string())

    # subgroup errors
    te["tier"] = wage_tier(te.y).astype(str)
    te["occ_lab"] = te.occ_f.map(lambda k: LABELS.get(k, "Other / not low-wage group"))
    rows = []
    for col in ["area", "occ_lab", "tier"]:
        for g, d in te.groupby(col):
            for name, p in [("B2", "p_b2"), ("ridge", "p_ridge")]:
                rows.append(dict(dimension=col, group=g, model=name, n=len(d),
                                 MAE=mean_absolute_error(d.y, d[p]), median_y=d.y.median(),
                                 bias_mean=(d[p] - d.y).mean()))
    sg = pd.DataFrame(rows)
    sg.to_csv(os.path.join(OUT, "salary_model_subgroups.csv"), index=False)

    te["abs_err"] = (te.p_ridge - te.y).abs()
    fail = te.sort_values("abs_err", ascending=False).head(25)[
        ["jobid", "company_name", "job_title", "location", "salary_formatted", "y", "p_ridge", "p_b2", "abs_err"]]
    fail.to_csv(os.path.join(OUT, "salary_model_failures.csv"), index=False)
    # low-wage-group failures specifically
    lw = te[te.occ.notna()].sort_values("abs_err", ascending=False).head(15)[
        ["jobid", "occ", "job_title", "location", "salary_formatted", "y", "p_ridge", "abs_err"]]
    lw.to_csv(os.path.join(OUT, "salary_model_failures_lowwage.csv"), index=False)

    # refit on all labelled rows and impute missing
    Xall, Xmiss = features(lab, [lab, df[df.pay_mid.isna()]])
    ridge_all = Ridge(alpha=alpha).fit(Xall, np.log(lab.y.values))
    df["pay_hourly_pred"] = np.nan
    df.loc[df.pay_mid.isna(), "pay_hourly_pred"] = np.exp(ridge_all.predict(Xmiss))
    df["pay_hourly"] = df.pay_mid.fillna(df.pay_hourly_pred)
    df["pay_imputed"] = df.pay_mid.isna()
    df.drop(columns=["description_text"]).to_parquet(os.path.join(OUT, "postings_with_pay.parquet"), index=False)

    # missing-pay shares (SB 1162 requires pay ranges in CA postings for employers with 15+ employees)
    df["no_pay"] = df.pay_mid.isna()
    df["occ_lab"] = df.occ_f.map(lambda k: LABELS.get(k, "Other"))
    miss = pd.concat([
        df.groupby("area").agg(n=("jobid", "size"), share_no_salary_text=("has_salary_text", lambda s: 1 - s.mean()),
                               share_no_usable_hourly=("no_pay", "mean")).reset_index().rename(columns={"area": "group"}).assign(dimension="area"),
        df.groupby("occ_lab").agg(n=("jobid", "size"), share_no_salary_text=("has_salary_text", lambda s: 1 - s.mean()),
                                  share_no_usable_hourly=("no_pay", "mean")).reset_index().rename(columns={"occ_lab": "group"}).assign(dimension="occupation"),
        pd.DataFrame([dict(group="All CA", n=len(df), share_no_salary_text=1 - df.has_salary_text.mean(),
                           share_no_usable_hourly=df.no_pay.mean(), dimension="all")])])
    miss.to_csv(os.path.join(OUT, "pay_missing_share.csv"), index=False)
    print(miss.round(3).to_string())
    json.dump({"alpha": alpha, "n_train": len(tr), "n_test": len(te)}, open(os.path.join(OUT, "salary_model_info.json"), "w"))
    return m


if __name__ == "__main__":
    main()
