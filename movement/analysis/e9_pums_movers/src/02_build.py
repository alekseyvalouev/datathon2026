"""Build the Bay-origin analysis frame from the slim PUMS extracts.

Origin = lived in a Bay Area MIGPUMA one year ago (2020-vintage MIGPUMAs; ACS 2022+ uses 2020 PUMAs).
Groups:
  stay_same       MIG==1 (same house) and current PUMA in the Bay
  stay_moved_bay  MIG==3, MIGSP==6, MIGPUMA in Bay, current PUMA in Bay
  left_saccv      MIG==3 from Bay, now in Sacramento region / Central Valley (CA)
  left_othca      MIG==3 from Bay, now elsewhere in CA
  left_ca         MIG==3 from Bay, now in another state
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
RAW, DATA = os.path.join(BASE, "raw"), os.path.join(BASE, "data")
YEARS = [int(y) for y in os.environ.get("E9_YEARS", "2022,2023,2024").split(",")]

# 2020 MIGPUMA codes (IPUMS county_migpuma_pwpuma_2022.xls) - each Bay county is its own MIGPUMA.
BAY_COUNTIES = {"001": "Alameda", "013": "Contra Costa", "041": "Marin", "055": "Napa", "075": "San Francisco",
                "081": "San Mateo", "085": "Santa Clara", "095": "Solano", "097": "Sonoma"}
# Sacramento region + Central Valley counties (Sacramento Valley + San Joaquin Valley + Sac metro).
SACCV_COUNTIES = {"007", "011", "017", "019", "021", "029", "031", "039", "047", "061", "067", "077", "089",
                  "099", "101", "103", "107", "113", "115"}
CPI = {2022: 292.655, 2023: 304.702, 2024: 313.689}  # CPI-U annual averages, to 2024 dollars
REP = [f"PWGTP{i}" for i in range(1, 81)]


def crosswalks():
    c = pd.read_excel(os.path.join(RAW, "county_migpuma_pwpuma_2022.xls"), dtype=str)
    c.columns = ["st", "county", "mst", "migpuma"]
    c = c[c.st == "06"]
    p = pd.read_excel(os.path.join(RAW, "puma_migpuma1_pwpuma00_2020.xls"), dtype=str)
    p.columns = ["st", "puma", "mst", "migpuma"]
    p = p[p.st == "06"]
    mig_counties = c.groupby("migpuma").county.apply(set).to_dict()

    def region(mp):
        cs = mig_counties.get(mp, set())
        if cs and cs <= set(BAY_COUNTIES):
            return "bay"
        if cs and cs <= SACCV_COUNTIES:
            return "saccv"
        if cs & set(BAY_COUNTIES):
            raise ValueError(f"MIGPUMA {mp} mixes Bay and non-Bay counties: {cs}")
        return "othca"

    mig_region = {mp: region(mp) for mp in mig_counties}
    mig_county = {mp: (BAY_COUNTIES[next(iter(cs))] if mig_region[mp] == "bay" else None)
                  for mp, cs in mig_counties.items()}
    puma_mig = dict(zip(p.puma.astype(int), p.migpuma))
    return mig_region, mig_county, puma_mig


def race(df):
    r = pd.Series("Other/Multi", index=df.index)
    r[df.RAC1P == 1] = "White"
    r[df.RAC1P == 2] = "Black"
    r[df.RAC1P.isin([6, 7])] = "Asian/PI"
    r[df.HISP > 1] = "Latino"
    return r


def build():
    mig_region, mig_county, puma_mig = crosswalks()
    frames = []
    for y in YEARS:
        p = pd.read_parquet(os.path.join(DATA, f"persons_{y}.parquet"))
        h = pd.read_parquet(os.path.join(DATA, f"housing_{y}.parquet")).drop(columns=["YEAR"])
        frames.append(p.merge(h, on="SERIALNO", how="left"))
    d = pd.concat(frames, ignore_index=True)

    d["cur_mig"] = np.where(d.ST == 6, d.PUMA.map(lambda x: puma_mig.get(int(x))), None)
    d["cur_region"] = np.where(d.ST == 6, d.cur_mig.map(mig_region), "out")
    d["mig_str"] = d.MIGPUMA.map(lambda x: f"{int(x):05d}" if pd.notna(x) else None)
    from_bay_mover = (d.MIG == 3) & (d.MIGSP == 6) & (d.mig_str.map(mig_region) == "bay")
    stay_same = (d.MIG == 1) & (d.ST == 6) & (d.cur_region == "bay")
    d = d[from_bay_mover | stay_same].copy()
    d["origin_county"] = np.where(d.MIG == 1, d.cur_mig.map(mig_county), d.mig_str.map(mig_county))
    g = pd.Series(index=d.index, dtype=object)
    mv = d.MIG == 3
    g[~mv] = "stay_same"
    g[mv & (d.cur_region == "bay")] = "stay_moved_bay"
    g[mv & (d.cur_region == "saccv")] = "left_saccv"
    g[mv & (d.cur_region == "othca")] = "left_othca"
    g[mv & (d.cur_region == "out")] = "left_ca"
    d["group"] = g
    d["stayer"] = d.group.str.startswith("stay").astype(int)
    d["leaver"] = 1 - d.stayer

    # population: adults 18-64 in households (housing outcomes undefined in group quarters)
    d = d[(d.AGEP >= 18) & (d.AGEP <= 64) & (d.TYPEHUGQ == 1)].copy()

    # pre-determined-ish covariates
    d["race_eth"] = race(d)
    d["educ"] = pd.cut(d.SCHL, [0, 15, 17, 20, 30], labels=["<HS", "HS/GED", "Some college/AA", "BA+"]).astype(str)
    d["age_grp"] = pd.cut(d.AGEP, [17, 24, 34, 44, 54, 64], labels=["18-24", "25-34", "35-44", "45-54", "55-64"]).astype(str)
    d["female"] = (d.SEX == 2).astype(int)
    d["foreign_born"] = (d.NATIVITY == 2).astype(int)
    d["married"] = (d.MAR == 1).astype(int)
    d["disabled"] = (d.DIS == 1).astype(int)
    hht = d.HHT.map({1: "married couple", 2: "other family", 3: "other family", 4: "alone", 6: "alone",
                     5: "nonfamily", 7: "nonfamily"})
    d["hh_type"] = hht.fillna("other").astype(str)
    d["kids"] = d.HUPAC.isin([1, 2, 3]).astype(int)
    d["householder"] = (d.RELSHIPP == 20).astype(int)

    # outcomes (NaN where not applicable)
    renter = d.TEN == 3
    d["own"] = d.TEN.isin([1, 2]).astype(float)
    d["renter"] = renter.astype(float)
    d["rent_burden30"] = np.where(renter & d.GRPIP.notna(), (d.GRPIP >= 30).astype(float), np.nan)
    d["rent_burden50"] = np.where(renter & d.GRPIP.notna(), (d.GRPIP >= 50).astype(float), np.nan)
    d["overcrowded"] = np.where(d.RMSP > 0, (d.NP / d.RMSP > 1).astype(float), np.nan)
    d["commute_min"] = d.JWMNP.astype(float)
    d["commute60"] = np.where(d.JWMNP.notna(), (d.JWMNP >= 60).astype(float), np.nan)
    d["employed"] = d.ESR.isin([1, 2, 4, 5]).astype(float)
    adj = d.ADJINC / 1e6 * d.YEAR.map(lambda y: CPI[2024] / CPI[y])
    d["wage_2024usd"] = np.where(d.WAGP > 0, d.WAGP * adj, np.nan)
    d["below_200pov"] = np.where(d.POVPIP.notna(), (d.POVPIP < 200).astype(float), np.nan)
    d["wfh"] = np.where(d.JWTRNS.notna(), (d.JWTRNS == 11).astype(float), np.nan)
    keep = ["SERIALNO", "SPORDER", "YEAR", "ST", "PUMA", "MIG", "MIGPUMA", "group", "stayer", "leaver",
            "origin_county", "AGEP", "race_eth", "educ", "age_grp", "female", "foreign_born", "married",
            "disabled", "hh_type", "kids", "householder", "POVPIP", "TEN", "GRPIP", "NP", "RMSP", "JWMNP",
            "own", "renter", "rent_burden30", "rent_burden50", "overcrowded", "commute_min", "commute60",
            "employed", "wage_2024usd", "below_200pov", "wfh", "PWGTP"] + REP
    d = d[keep].reset_index(drop=True)
    d.to_parquet(os.path.join(DATA, "bay_origin_adults.parquet"), index=False)
    print("analysis frame", d.shape)
    print(d.groupby("group").agg(n=("PWGTP", "size"), wN=("PWGTP", "sum")))
    return d


if __name__ == "__main__":
    build()
