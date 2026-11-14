"""Step 4 (Analysis 3): renovation / luxury language and move-in concessions on the CURRENT listing.
(a) Among E2 turnover pairs whose NEXT episode is the unit's current FOR_RENT listing (so the description describes the
    newcomer's listing), regress the annualized turnover jump r on text flags with ZIP fixed effects, bedroom dummies,
    gap, log prior rent, prior-listing year and a management-company flag; SEs clustered by ZIP.
(b) Concessions ('N weeks free', 'N months free'): where are they (rent tier, building age, management company,
    home type)? Effective first-year rent for a newcomer = ask x (1 - weeks/52) on a 12-month lease."""
import os, sys, numpy as np, pandas as pd, duckdb
import statsmodels.formula.api as smf
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from textflags import *

def current_listings():
    ex = pd.read_parquet(os.path.join(CACHE, "extra.parquet"))
    ex = ex[(ex.homeStatus == "FOR_RENT") & ex.county.isin(BAY.values())].copy()
    txt = ex.description.fillna("") + " || " + ex.special_offer.fillna("")
    ex["remodel"] = ex.description.map(lambda t: flag(REMODEL, t)).astype(int)
    ex["luxury"] = ex.description.map(lambda t: flag(LUXURY, t)).astype(int)
    ex["conc_weeks"] = txt.map(concession_weeks)
    ex["concession"] = ex.conc_weeks.notna().astype(int)
    ex["price"] = pd.to_numeric(ex.price, errors="coerce"); ex["beds"] = pd.to_numeric(ex.bedrooms, errors="coerce")
    ex["yearBuilt"] = pd.to_numeric(ex.yearBuilt, errors="coerce")
    ex["mgmt"] = (ex.is_listed_by_management_company == "true").astype(int)
    return ex

def main():
    ex = current_listings()
    print(f"current Bay Area FOR_RENT listings {len(ex)}: remodel {ex.remodel.mean():.1%}, luxury {ex.luxury.mean():.1%}, "
          f"concession {ex.concession.mean():.1%}")
    # ---- (a) regression on turnover pairs
    con = duckdb.connect(DB, read_only=True)
    last_ep = con.execute("select zpid, max(ep) max_ep from rep group by 1").df(); con.close()
    df = pd.read_parquet(E2_SAMPLE).merge(last_ep, on="zpid")
    df = df[(df.ep + 1 == df.max_ep) & (df.next_start >= "2025-06-01")]
    df = df.merge(ex[["zpid", "remodel", "luxury", "concession", "conc_weeks", "yearBuilt"]].rename(columns={"yearBuilt": "yb"}), on="zpid")
    df["beds_g"] = df.beds.clip(0, 4).astype("Int64").astype(str); df["log_last_p"] = np.log(df.last_p)
    df["r_pct"] = 100 * df.r; df["over_cap"] = (df.r > 0.10).astype(int)
    df["new_bldg"] = (df.yearBuilt >= 2015).astype(int)
    df["conc_weeks0"] = df.conc_weeks.fillna(0)
    df["r_eff_pct"] = 100 * ((df.next_first * (1 - df.conc_weeks0 / 52) / df.last_p) ** (1 / df.start_gap_y) - 1)
    zc = df.zipcode.value_counts(); df = df[df.zipcode.isin(zc[zc >= 5].index)].copy()
    print(f"regression sample (next episode = current listing, re-listed >= 2025-06, ZIP n>=5): {len(df)}")
    rows = []
    specs = {"r_pct ~ flags + ZIP FE": "r_pct ~ remodel + luxury + concession + C(beds_g) + start_gap_y + log_last_p + prev_year + mgmt + C(zipcode)",
             "r_pct ~ remodel only + ZIP FE": "r_pct ~ remodel + C(beds_g) + start_gap_y + log_last_p + prev_year + mgmt + C(zipcode)",
             "r_pct ~ flags, SFR/condo/TH only": "r_pct ~ remodel + luxury + concession + C(beds_g) + start_gap_y + log_last_p + prev_year + mgmt + C(zipcode)",
             "over_cap (LPM) ~ flags + ZIP FE": "over_cap ~ remodel + luxury + concession + C(beds_g) + start_gap_y + log_last_p + prev_year + mgmt + C(zipcode)"}
    for name, f in specs.items():
        d = df[df.homeType != "APARTMENT"] if "SFR" in name else df
        m = smf.ols(f, data=d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.zipcode)[0]})
        for v in ["remodel", "luxury", "concession", "mgmt"]:
            if v in m.params:
                rows.append(dict(model=name, term=v, coef=m.params[v], se=m.bse[v], p=m.pvalues[v], n=int(m.nobs),
                                 share_flag=d[v].mean()))
    reg = pd.DataFrame(rows).round(4); reg.to_csv(os.path.join(OUT, "a3_text_regression.csv"), index=False); print(reg.to_string())
    raw = df.groupby("remodel").agg(n=("r", "size"), med_r=("r_pct", "median"), mean_r=("r_pct", "mean"), over_cap=("over_cap", "mean")).round(3)
    raw.to_csv(os.path.join(OUT, "a3_remodel_raw.csv")); print(raw)
    # effective vs asking jump for pairs with a concession
    eff = df.groupby("concession").agg(n=("r", "size"), med_r_ask=("r_pct", "median"), med_r_eff=("r_eff_pct", "median"),
                                       over_cap_ask=("over_cap", "mean"), over_cap_eff=("r_eff_pct", lambda s: (s > 10).mean()),
                                       med_weeks=("conc_weeks", "median")).round(3)
    eff.to_csv(os.path.join(OUT, "a3_concession_effective_jump.csv")); print(eff)
    # ---- (b) where are concessions (all current listings)
    ex["zip_med"] = ex.groupby("zipcode").price.transform("median")
    ex["rel"] = ex.price / ex.zip_med
    ex["rent_tier"] = pd.cut(ex.rel, [0, 0.8, 1.0, 1.25, 99], labels=["<0.8x ZIP median", "0.8-1.0x", "1.0-1.25x", ">1.25x"])
    ex["bldg_age"] = pd.cut(ex.yearBuilt, [0, 1979, 1999, 2014, 2100], labels=["<=1979", "1980-99", "2000-14", "2015+"])
    ex["htype"] = ex.homeType.replace({"SINGLEFAMILY": "SINGLE_FAMILY", "TOWNHOME": "TOWNHOUSE"})
    out = []
    for by in ["rent_tier", "bldg_age", "mgmt", "htype", "county", "luxury"]:
        g = ex.groupby(by, observed=True).agg(n=("zpid", "size"), share_concession=("concession", "mean"),
                                              med_weeks_if_any=("conc_weeks", "median"), med_ask=("price", "median"))
        g["by"] = by; g.index = g.index.astype(str); g.index.name = "level"; out.append(g.reset_index())
    ct = pd.concat(out)[["by", "level", "n", "share_concession", "med_weeks_if_any", "med_ask"]].round(4)
    ct.to_csv(os.path.join(OUT, "a3_concessions_where.csv"), index=False); print(ct.to_string())
    c = ex[ex.concession == 1]
    print(f"concession listings {len(c)}: median weeks {c.conc_weeks.median()}, median effective discount {np.median(c.conc_weeks / 52):.1%}")
    # figure: concession share by building age x mgmt
    p = ex[ex.bldg_age.notna()].pivot_table(index="bldg_age", columns="mgmt", values="concession", aggfunc="mean", observed=True)
    fig, ax = plt.subplots(figsize=(6.5, 3.8)); x = np.arange(len(p)); h = 0.38
    ax.bar(x - h / 2, 100 * p.get(0, np.nan), h, color="#9bb7d4", label="individual / broker listing")
    ax.bar(x + h / 2, 100 * p.get(1, np.nan), h, color="#2c5d8f", label="management-company listing")
    ax.set_xticks(x, p.index.astype(str)); ax.set_xlabel("year built"); ax.set_ylabel("% of current rental listings offering free weeks/months")
    ax.legend(frameon=False, fontsize=8); ax.set_title("Move-in concessions are a new-building, corporate-landlord tool", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "a3_concessions_by_age_mgmt.png"), dpi=150); plt.close(fig)
    ex[["zpid", "remodel", "luxury", "concession", "conc_weeks"]].to_parquet(os.path.join(OUT, "a3_current_listing_flags.parquet"), index=False)

if __name__ == "__main__":
    main()
