"""Step 1: build the analysis sample of same-unit turnover pairs from the cached Zillow DuckDB (read-only).
Writes outputs/sample.parquet and outputs/sample_flow.csv."""
import duckdb, numpy as np, pandas as pd, os, zipfile, ast
from common import *

def load_pairs():
    con = duckdb.connect(DB, read_only=True)
    df = con.execute("""
    with sold as (select distinct zpid, d from ev where not rental and event='Sold'),
    zz as (select zpid, any_value(listing_provided_by->>'company') company,
                  any_value(is_listed_by_management_company) mgmt from z group by zpid)
    select t.*, zz.company, zz.mgmt='true' mgmt,
      exists (select 1 from sold s where s.zpid=t.zpid and s.d > t.end_d and s.d < t.next_start) sold_between
    from turn t left join zz using(zpid)""").df()
    # landlord size: number of zpids (whole dataset) listed by the same company among management-company listings
    sz = con.execute("""select listing_provided_by->>'company' company, count(distinct zpid) n
                        from z where is_listed_by_management_company='true' group by 1""").df()
    con.close()
    df = df.merge(sz.rename(columns={"n": "company_n_mgmt"}), on="company", how="left")
    return df

def tract_join(df):
    """Point-in-polygon join to 2018 census tracts, then Urban Displacement Project SF Bay typology."""
    try:
        import shapefile
        from shapely.geometry import shape, Point
        from shapely.strtree import STRtree
    except ImportError:
        print("pyshp/shapely missing; skipping typology join"); df["typ_cat"] = np.nan; return df
    zp = os.path.join(EXT, "tl_2018_06_tract.zip"); ty = os.path.join(EXT, "SanFrancisco_typology_output.csv")
    if not (os.path.exists(zp) and os.path.exists(ty)):
        print("external files missing; skipping typology join"); df["typ_cat"] = np.nan; return df
    bay = {"001", "013", "041", "055", "075", "081", "085", "095", "097"}
    r = shapefile.Reader(zp)
    geoms, ids = [], []
    for sr in r.iterShapeRecords():
        rec = sr.record.as_dict()
        if rec["COUNTYFP"] in bay:
            geoms.append(shape(sr.shape.__geo_interface__)); ids.append(int(rec["GEOID"]))
    tree = STRtree(geoms)
    pts = df[["lon", "lat"]].drop_duplicates().dropna()
    out = {}
    for lo, la in pts.itertuples(index=False):
        p = Point(lo, la)
        for i in tree.query(p):
            if geoms[i].contains(p): out[(lo, la)] = ids[i]; break
    df["tract"] = [out.get((lo, la)) for lo, la in zip(df.lon, df.lat)]
    t = pd.read_csv(ty, usecols=["GEOID", "typ_cat"])
    def grp(s):
        c = ast.literal_eval(s) if isinstance(s, str) else []
        if not c: return np.nan
        c = c[0]
        return {"LISD": "Low-income/susceptible", "OD": "Ongoing displacement", "ARG": "At risk of gentrification",
                "EOG": "Early/ongoing gentrification", "AdvG": "Advanced gentrification", "SMMI": "Stable moderate/mixed",
                "ARE": "At risk of exclusive", "BE": "Becoming exclusive", "SAE": "Stable/advanced exclusive"}[c]
    t["typology"] = t.typ_cat.map(grp)
    coarse = {"Low-income/susceptible": "1 Low-income/displacement", "Ongoing displacement": "1 Low-income/displacement",
              "At risk of gentrification": "2 Gentrifying", "Early/ongoing gentrification": "2 Gentrifying",
              "Advanced gentrification": "2 Gentrifying", "Stable moderate/mixed": "3 Moderate/mixed",
              "At risk of exclusive": "4 Exclusive", "Becoming exclusive": "4 Exclusive", "Stable/advanced exclusive": "4 Exclusive"}
    t["typ_group"] = t.typology.map(coarse)
    df = df.merge(t[["GEOID", "typology", "typ_group"]].rename(columns={"GEOID": "tract"}), on="tract", how="left")
    print(f"typology joined for {df.typology.notna().mean():.1%} of pairs")
    return df

def market_index():
    """County x quarter asking-rent index from ALL rental listing starts (rep), composition-adjusted by subtracting the
    (zipcode, beds, apartment-or-not) cell mean of log first ask. Cell means use only listings before TRAIN_END."""
    con = duckdb.connect(DB, read_only=True)
    r = con.execute("""select distinct county, zipcode, lat, lon, least(coalesce(beds,0),4) b, homeType='APARTMENT' apt,
                       start_d, first_p from rep where first_p between 500 and 30000""").df(); con.close()
    # fixed row order: DuckDB returns rows in arbitrary order, which changes float sums in the last bits
    r = r.sort_values(["county", "zipcode", "start_d", "lat", "lon", "b", "apt", "first_p"], kind="mergesort").reset_index(drop=True)
    r["lp"] = np.log(r.first_p)
    cell = r[r.start_d < TRAIN_END].groupby(["zipcode", "b", "apt"]).lp.mean().rename("cm")
    r = r.join(cell, on=["zipcode", "b", "apt"]).dropna(subset=["cm"])
    r["res"] = r.lp - r.cm
    r["q"] = pd.PeriodIndex(pd.to_datetime(r.start_d), freq="Q")
    idx = r.groupby(["county", "q"]).res.agg(["median", "size"])
    idx = idx[idx["size"] >= 20]["median"]
    return idx

def add_market(df, idx):
    d = idx.to_dict()
    q0 = pd.PeriodIndex(pd.to_datetime(df.start_d), freq="Q")
    q1 = pd.PeriodIndex(pd.to_datetime(df.next_start), freq="Q") - 1   # last full quarter before re-listing
    def get(c, q):
        for k in range(4):   # fall back to nearest earlier quarter with data
            v = d.get((c, q - k))
            if v is not None: return v
        return np.nan
    a = np.array([get(c, q) for c, q in zip(df.county, q0)]); b = np.array([get(c, q) for c, q in zip(df.county, q1)])
    b4 = np.array([get(c, q - 4) for c, q in zip(df.county, q1)])
    df["mkt_chg"] = (b - a) / df.start_gap_y          # annualized county market change over the tenancy
    df["mkt_lvl0"] = a                               # county market level when the previous tenancy started
    df["mkt_mom"] = b - b4                           # trailing 1-year county momentum at re-listing
    return df

def main():
    df = load_pairs().sort_values(["zpid", "ep"], kind="mergesort").reset_index(drop=True)
    flow = [("all consecutive listing pairs (turn)", len(df))]
    for c in ["yearBuilt", "ep", "n_changes", "next_n_changes"]: df[c] = df[c].astype(float)
    df["ratio"] = df.next_first / df.last_p
    df = df[(df.start_gap_y >= 1) & (df.start_gap_y <= 6)]
    flow.append(("1 <= start_gap_y <= 6 (drop same-vacancy relists & very old pairs)", len(df)))
    df = df[(df.ratio >= 0.5) & (df.ratio <= 2.0)]
    flow.append(("0.5 <= next_first/last_p <= 2.0 (drop typos/unit swaps)", len(df)))
    df["homeType"] = df.homeType.replace({"TOWNHOME": "TOWNHOUSE", "SINGLEFAMILY": "SINGLE_FAMILY"})
    df = df[df.homeType.isin(["APARTMENT", "SINGLE_FAMILY", "CONDO", "TOWNHOUSE", "MULTI_FAMILY"])]
    flow.append(("residential homeType (drop LOT/MANUFACTURED/UNKNOWN)", len(df)))
    df = df[df.lat.notna() & df.lon.notna() & df.zipcode.notna()]
    flow.append(("has lat/lon/zipcode", len(df)))
    key = ["lat", "lon", "beds", "baths", "sqft", "start_d", "last_p", "next_start", "next_first"]
    df = df.sort_values(["zpid", "ep"], kind="mergesort").drop_duplicates(key).reset_index(drop=True)
    flow.append(("dedupe identical histories at same location (floor-plan duplicate zpids)", len(df)))

    # targets
    df["r"] = df.ratio ** (1 / df.start_gap_y) - 1
    df["logr"] = np.log(df.ratio) / df.start_gap_y
    df["y_over_cap"] = (df.r > CAP).astype(int)
    # features known at re-listing time (nothing from the *next* episode except its start date)
    sd, ed, ns = pd.to_datetime(df.start_d), pd.to_datetime(df.end_d), pd.to_datetime(df.next_start)
    df["prev_year"] = sd.dt.year + (sd.dt.dayofyear / 366)
    df["next_month"] = ns.dt.month
    df["prev_dur_d"] = (ed - sd).dt.days
    df["prev_cut"] = np.log(df.last_p / df.first_p)
    df["log_last_p"] = np.log(df.last_p)
    df["ppsf"] = np.where(df.sqft > 100, df.last_p / df.sqft, np.nan)
    df["age"] = np.where(df.yearBuilt > 1800, sd.dt.year - df.yearBuilt, np.nan)
    df["mgmt"] = df.mgmt.fillna(False).astype(int)
    df["large_landlord"] = ((df.mgmt == 1) & (df.company_n_mgmt.fillna(0) >= 200)).astype(int)
    df["sold_between"] = df.sold_between.astype(int)
    df["split"] = np.where(df.next_start < TRAIN_END, "train", np.where(df.next_start < VAL_END, "val", "test"))
    df = add_market(df, market_index())
    df = tract_join(df)
    df.drop(columns=["company"]).to_parquet(SAMPLE, index=False)
    flow = pd.DataFrame(flow, columns=["step", "n_pairs"])
    flow.to_csv(os.path.join(OUT, "sample_flow.csv"), index=False)
    print(flow.to_string(index=False)); print(df.split.value_counts())
    print(df.groupby("split")[["r", "y_over_cap", "mgmt", "large_landlord", "sold_between"]].mean().round(3))

if __name__ == "__main__":
    main()
