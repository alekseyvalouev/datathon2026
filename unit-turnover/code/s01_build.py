"""Step 1: unit x year panel for the turnover model.

Question: on 1 January of year Y, for a rental we have seen listed before, will it be listed for a new tenant
during Y?

Tenancy starts. Zillow `rep` has one row per "Listed for rent" event. Listings of the same unit that start within
180 days of the previous listing are the same vacancy (re-lists, price resets) and are merged into one tenancy
start; a listing later than that is a turnover.

Population. Units whose Zillow status at the 2026 crawl is FOR_RENT (75% of units with rental history). They are in
the data BECAUSE they were listed in 2026, so 2026 itself cannot be used: nearly every unit "turns over" that year
by construction. Risk years are 2019-2025. Split by risk year: train 2019-2023, validation 2024, test 2025.

Features use only what is known on 1 January of Y. Writes results/panel.parquet and results/s01_flow.csv."""
import os, sys, numpy as np, pandas as pd, duckdb
HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WS, "..", "movement", "analysis", "e2_turnover_model"))
from s01_build_sample import tract_join, market_index      # same tract join and county rent index as the rent model
from common import DB
DEW = os.path.join(WS, "..", "displacement-early-warning", "results")
RES = os.path.join(WS, "results"); os.makedirs(RES, exist_ok=True)
YEARS = list(range(2019, 2026)); SAME_VACANCY_DAYS = 180
TRACT_COLS = ["per_rent_18", "per_nonwhite_18", "real_hinc_18", "per_all_li_18", "per_col_18", "real_mrent_18",
              "per_limove_18", "rail", "typ"]

def load():
    con = duckdb.connect(DB, read_only=True)
    r = con.execute("""
      with zz as (select zpid, any_value(homeStatus) hs, any_value(is_listed_by_management_company)='true' mgmt,
                         any_value(listing_provided_by->>'company') company from z group by zpid),
           sz as (select listing_provided_by->>'company' company, count(distinct zpid) n from z
                  where is_listed_by_management_company='true' group by 1)
      select r.*, zz.hs, coalesce(zz.mgmt,false) mgmt, coalesce(sz.n,0) company_n
      from rep r join zz using(zpid) left join sz using(company)""").df()
    con.close(); return r

def main():
    r = load(); flow = [("units with any rental listing", r.zpid.nunique())]
    r = r[r.hs == "FOR_RENT"]; flow.append(("status FOR_RENT at the 2026 crawl", r.zpid.nunique()))
    r["homeType"] = r.homeType.replace({"TOWNHOME": "TOWNHOUSE", "SINGLEFAMILY": "SINGLE_FAMILY"})
    r = r[r.homeType.isin(["APARTMENT", "SINGLE_FAMILY", "CONDO", "TOWNHOUSE", "MULTI_FAMILY"])
          & r.lat.notna() & r.lon.notna() & r.zipcode.notna()]
    flow.append(("residential home type, has location", r.zpid.nunique()))
    r["sd"] = pd.to_datetime(r.start_d); r = r.sort_values(["zpid", "sd"], kind="mergesort")
    # floor-plan duplicates: different zpids at one location with an identical listing history
    sig = r.groupby("zpid").apply(lambda g: hash(tuple(zip(g.start_d, g.last_p))), include_groups=False).rename("sig")
    u = r.drop_duplicates("zpid")[["zpid", "lat", "lon", "beds", "baths", "sqft"]].join(sig, on="zpid")
    keep = u.sort_values("zpid").drop_duplicates(["lat", "lon", "beds", "baths", "sqft", "sig"]).zpid
    r = r[r.zpid.isin(keep)]; flow.append(("drop floor-plan duplicate zpids", r.zpid.nunique()))
    # merge same-vacancy re-lists into tenancy starts
    gap = r.groupby("zpid").sd.diff().dt.days
    r["ten"] = (gap.isna() | (gap > SAME_VACANCY_DAYS)).groupby(r.zpid).cumsum()
    t = r.groupby(["zpid", "ten"]).agg(t_start=("sd", "first"), last_p=("last_p", "last"), first_p=("first_p", "first"),
                                       n_changes=("n_changes", "sum"), n_listings=("sd", "size"),
                                       end_d=("end_d", "last")).reset_index()
    t["next_start"] = t.groupby("zpid").t_start.shift(-1); t["prev_start"] = t.groupby("zpid").t_start.shift(1)
    t["first_seen"] = t.groupby("zpid").t_start.transform("min")
    flow.append(("tenancy starts (listings merged within 180 days)", len(t)))
    unit = r.drop_duplicates("zpid").set_index("zpid")[["county", "city", "zipcode", "homeType", "beds", "baths", "sqft",
                                                         "yearBuilt", "lat", "lon", "mgmt", "company_n"]]
    rows = []
    for Y in YEARS:
        A = pd.Timestamp(f"{Y}-01-01"); B = pd.Timestamp(f"{Y + 1}-01-01")
        c = t[t.t_start < A].sort_values("t_start").groupby("zpid").tail(1).copy()   # tenancy in place on 1 January
        c["year"] = Y; c["y"] = ((c.next_start >= A) & (c.next_start < B)).astype(int)
        c["tenure_y"] = (A - c.t_start).dt.days / 365.25
        c["obs_y"] = (A - c.first_seen).dt.days / 365.25
        c["n_prior"] = c.ten - 1                                     # turnovers seen before this tenancy
        c["last_gap_y"] = (c.t_start - c.prev_start).dt.days / 365.25
        c["prior_rate"] = np.where(c.obs_y - c.tenure_y > 0.5, c.n_prior / (c.obs_y - c.tenure_y), np.nan)
        rows.append(c)
    p = pd.concat(rows, ignore_index=True).join(unit, on="zpid")
    flow.append(("unit-years at risk, 2019-2025", len(p))); flow.append(("  distinct units", p.zpid.nunique()))
    for c in ["yearBuilt", "n_changes", "ten"]: p[c] = p[c].astype(float)
    p["start_month"] = p.t_start.dt.month
    p["vacancy_d"] = (pd.to_datetime(p.end_d) - p.t_start).dt.days.clip(0, 400)
    p["prev_cut"] = np.log(p.last_p / p.first_p); p["log_last_p"] = np.log(p.last_p)
    p["ppsf"] = np.where(p.sqft > 100, p.last_p / p.sqft, np.nan)
    p["age"] = np.where(p.yearBuilt > 1800, p.year - p.yearBuilt, np.nan)
    p["mgmt"] = p.mgmt.astype(int); p["large_landlord"] = ((p.mgmt == 1) & (p.company_n >= 200)).astype(int)
    # county rent index: level when the tenancy started, now, and the gap (how far the market moved past the sitting rent)
    idx = market_index().to_dict()
    def get(cty, q):
        for k in range(4):
            v = idx.get((cty, q - k))
            if v is not None: return v
        return np.nan
    q0 = pd.PeriodIndex(p.t_start, freq="Q"); q1 = pd.PeriodIndex([f"{y - 1}Q4" for y in p.year], freq="Q")
    a = np.array([get(c, q) for c, q in zip(p.county, q0)]); b = np.array([get(c, q) for c, q in zip(p.county, q1)])
    b4 = np.array([get(c, q - 4) for c, q in zip(p.county, q1)])
    p["mkt_lvl0"] = a; p["mkt_since"] = b - a; p["mkt_mom"] = b - b4
    # tract features (displacement workstream)
    p = tract_join(p)
    tt = pd.read_csv(os.path.join(DEW, "e5_tract_table.csv"), usecols=["GEOID"] + TRACT_COLS, dtype={"GEOID": str})
    tt["tract"] = tt.GEOID.astype(np.int64); p["tract"] = p.tract.astype("Int64")
    p = p.merge(tt.drop(columns="GEOID").rename(columns={"typ": "udp_typ"}), on="tract", how="left")
    p["renter_majority"] = np.where(p.per_rent_18.isna(), np.nan, (p.per_rent_18 > 0.5).astype(float))
    p["poc_majority"] = np.where(p.per_nonwhite_18.isna(), np.nan, (p.per_nonwhite_18 > 0.5).astype(float))
    p["split"] = np.where(p.year <= 2023, "train", np.where(p.year == 2024, "val", "test"))
    p.drop(columns=["typology", "typ_group"], errors="ignore").to_parquet(os.path.join(RES, "panel.parquet"), index=False)
    flow.append(("  tract features joined", int(p.per_rent_18.notna().sum())))
    pd.DataFrame(flow, columns=["step", "n"]).to_csv(os.path.join(RES, "s01_flow.csv"), index=False)
    print(pd.DataFrame(flow, columns=["step", "n"]).to_string(index=False))
    print(p.groupby("year").y.agg(["size", "sum", "mean"]).round(3))
    print(p.groupby(pd.cut(p.tenure_y, [0, .5, 1, 1.5, 2, 3, 4, 6, 20])).y.agg(["size", "mean"]).round(3))
    print(p.groupby("homeType").y.agg(["size", "mean"]).round(3)); print(p.groupby("large_landlord").y.agg(["size", "mean"]).round(3))

if __name__ == "__main__":
    main()
