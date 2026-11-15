"""Step 1: build the unit-level analysis table.

Population: same-unit turnover pairs (movement E2) re-listed on/after 2022-06 (first year of parsed income limits)
whose PREVIOUS rent a low-income household (<= 80% of area median income, household size = bedrooms + 1) could
still qualify for under the income limit in force at re-listing (3x-rent rule).
Label y = 1 if the NEXT tenancy's settled asking rent (last ask of the re-listing episode, i.e. after any cuts; the
closest the data gets to the rent the unit let at) is above that same limit: the turnover took the unit out of
low-income reach. Holding the limit fixed isolates the price move. y_first uses the first ask instead (robustness):
the hand check found first asks that crossed the line and were cut back below it within weeks.

Joins: tract features from displacement-early-warning (2018 census, pre-2019 Zillow, backtest risk score) and city
job mix from ai-labor-distribution. Writes results/pairs.parquet and results/s01_sample_flow.csv."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

TRACT_COLS = ["per_rent_18", "per_nonwhite_18", "real_hinc_18", "per_all_li_18", "per_col_18", "real_mrent_18",
              "pctch_real_mrent_12_18", "per_limove_18", "rail", "z_flip_pre", "z_apprec_pre", "z_ppsf_growth_pre",
              "z_rent_pre", "z_nb_flip_pre", "typ"]
CITY_COLS = ["ai_positioned_share", "exposed_share", "frontline_share", "postings_total"]

def limit_year(s):
    d = pd.to_datetime(s)
    return np.where(d.dt.month >= 6, d.dt.year, d.dt.year - 1)   # HCD limits take effect ~June

def limits():
    il = pd.read_csv(LIMITS)
    return {(r.year, r.county, r.level, k): getattr(r, f"p{k}") for r in il.itertuples() for k in range(1, 9)}

def main():
    df = pd.read_parquet(E2_SAMPLE)
    flow = [("movement E2 turnover pairs", len(df))]
    df = df[df.beds.notna()].copy(); flow.append(("bedrooms known (household size)", len(df)))
    df["hh"] = (df.beds.clip(0, 7) + 1).astype(int)
    df["ly"] = limit_year(df.next_start)
    lim = limits()
    for lev in ["LI", "VLI", "MED"]:
        df[lev] = [lim.get((y, c, lev, h), np.nan) for y, c, h in zip(df.ly, df.county, df.hh)]
    df = df[df.LI.notna()].copy(); flow.append(("re-listed 2022-06 or later (income limit available)", len(df)))
    df["thr"] = df.LI / (12 * MULT)                     # highest rent an 80%-AMI household of this size qualifies for
    df["thr_vli"] = df.VLI / (12 * MULT)
    df["thr_25"] = df.LI / (12 * 2.5)
    full = df.copy()                                    # kept for label-variant robustness (different populations)
    df = df[df.last_p <= df.thr].copy(); flow.append(("previous rent within 80% AMI reach (population)", len(df)))
    df["y"] = (df.next_last > df.thr).astype(int)
    df["y_first"] = (df.next_first > df.thr).astype(int)

    # Headroom features: how far below the line the unit sits, and the yearly growth that would cross it
    for d in (df, full):
        d["headroom"] = np.log(d.thr / d.last_p)
        d["req_growth"] = (d.thr / d.last_p) ** (1 / d.start_gap_y) - 1
        d["ami_share0"] = 12 * MULT * d.last_p / d.MED     # income needed for the old rent, as share of AMI

    # Tract features from displacement-early-warning
    tt = pd.read_csv(os.path.join(DEW, "e5_tract_table.csv"), usecols=["GEOID"] + TRACT_COLS, dtype={"GEOID": str})
    pr = pd.read_csv(os.path.join(DEW, "e2_predictions.csv"), usecols=["GEOID", "p_loco"], dtype={"GEOID": str})
    tt = tt.merge(pr, on="GEOID", how="left").rename(columns={"p_loco": "risk_backtest", "typ": "udp_typ"})
    tt["tract"] = tt.GEOID.astype(np.int64)
    # City job mix from ai-labor-distribution (Indeed, cross-sectional 2026 crawl)
    cj = pd.read_csv(os.path.join(AIL, "asset_city_jobs_housing.csv"), usecols=["county", "city"] + CITY_COLS)
    cj["city_key"] = cj.city.str.lower().str.strip(); cj["log_postings"] = np.log1p(cj.postings_total)
    cj = cj[cj.postings_total >= 30].drop_duplicates("city_key")     # thin cities left missing
    for name, d in (("df", df), ("full", full)):
        d["tract"] = d.tract.astype("Int64")
        m = d.merge(tt.drop(columns="GEOID"), on="tract", how="left")
        m["city_key"] = m.city.str.lower().str.strip()
        m = m.merge(cj[["city_key", "ai_positioned_share", "exposed_share", "frontline_share", "log_postings"]],
                    on="city_key", how="left")
        if name == "df": df = m
        else: full = m
    flow.append(("  of which: tract features joined", int(df.per_rent_18.notna().sum())))
    flow.append(("  of which: city job mix joined", int(df.ai_positioned_share.notna().sum())))
    df["renter_majority"] = np.where(df.per_rent_18.isna(), np.nan, (df.per_rent_18 > 0.5).astype(float))
    df["poc_majority"] = np.where(df.per_nonwhite_18.isna(), np.nan, (df.per_nonwhite_18 > 0.5).astype(float))

    df.to_parquet(DATA, index=False)
    full.to_parquet(os.path.join(RES, "pairs_all_relisted.parquet"), index=False)
    flow = pd.DataFrame(flow, columns=["step", "n"]); flow.to_csv(os.path.join(RES, "s01_sample_flow.csv"), index=False)
    print(flow.to_string(index=False))
    print(df.groupby("split").y.agg(["size", "sum", "mean"]).round(3))

if __name__ == "__main__":
    main()
