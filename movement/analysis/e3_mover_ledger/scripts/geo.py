"""Map free-text Indeed `location` strings to California county and a metro/region label.

Rules (in order):
  1. A 5-digit CA ZIP (9xxxx) in the string -> county via Census 2020 ZCTA->county relationship file
     (county with the largest land-area overlap).
  2. Otherwise the city name before ", CA" -> county, using the modal county of that city among Indeed rows
     that do carry a ZIP (built from the data itself), then a small manual table for frequent ZIP-less names.
  3. Strings like "California", "Remote" -> unknown.
"""
import os, re
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "raw")

BAY9 = ["Alameda", "Contra Costa", "Marin", "Napa", "San Francisco", "San Mateo", "Santa Clara", "Solano", "Sonoma"]
COUNTY_TO_METRO = {
    **{c: "Bay Area" for c in BAY9},
    **{c: "Sacramento" for c in ["Sacramento", "Placer", "El Dorado", "Yolo"]},
    "San Joaquin": "Stockton", "Stanislaus": "Modesto", "Fresno": "Fresno",
}
COUNTY_TO_REGION = {
    **{c: "Bay Area" for c in BAY9},
    **{c: "Sacramento" for c in ["Sacramento", "Placer", "El Dorado", "Yolo"]},
    **{c: "Central Valley" for c in ["San Joaquin", "Stanislaus", "Fresno", "Merced", "Kern", "Tulare", "Kings", "Madera"]},
    **{c: "Los Angeles/Orange" for c in ["Los Angeles", "Orange"]},
    **{c: "Inland Empire" for c in ["Riverside", "San Bernardino"]},
    "San Diego": "San Diego",
}
# ZIP-less names seen often in the data (checked by hand)
MANUAL_CITY = {
    "san francisco bay area": "BAY", "los angeles county": "Los Angeles", "orange county": "Orange",
    "san diego county": "San Diego", "santa clara county": "Santa Clara", "alameda county": "Alameda",
    "sacramento county": "Sacramento", "riverside county": "Riverside", "san bernardino county": "San Bernardino",
    "contra costa county": "Contra Costa", "san mateo county": "San Mateo", "fresno county": "Fresno",
    "greater sacramento": "Sacramento", "silicon valley": "BAY", "east bay": "BAY", "south bay": "BAY", "peninsula": "BAY",
}
ZIP_RE = re.compile(r"\b(9[0-6]\d{3})\b")
CITY_RE = re.compile(r"(?:^|,\s*)([^,]+?),\s*CA\b")


def zip_to_county():
    f = os.path.join(RAW, "tab20_zcta520_county20_natl.txt")
    d = pd.read_csv(f, sep="|", dtype=str, encoding="utf-8-sig")
    d = d[d.GEOID_ZCTA5_20.notna() & d.GEOID_COUNTY_20.str.startswith("06")].copy()
    d["a"] = d.AREALAND_PART.astype(float)
    d = d.sort_values("a").drop_duplicates("GEOID_ZCTA5_20", keep="last")
    return dict(zip(d.GEOID_ZCTA5_20, d.NAMELSAD_COUNTY_20.str.replace(" County", "", regex=False)))


def assign(loc: pd.Series) -> pd.DataFrame:
    z2c = zip_to_county()
    loc = loc.fillna("")
    zips = loc.str.extract(ZIP_RE, expand=False)
    city = loc.str.extract(CITY_RE, expand=False).str.strip().str.lower()
    # drop street-address remnants: keep the last comma-separated chunk before ", CA"
    county = zips.map(z2c)
    tab = pd.DataFrame({"city": city, "county": county}).dropna()
    city2county = tab.groupby("city").county.agg(lambda s: s.value_counts().index[0]).to_dict()
    for c in set(city.dropna()):  # "Napa County, CA" style
        if c.endswith(" county"):
            city2county[c] = c[:-7].title()
    city2county.update(MANUAL_CITY)
    c2 = city.map(city2county)
    county = county.fillna(c2)
    out = pd.DataFrame({"zip": zips, "city": city, "county": county})
    out["metro"] = out.county.map(lambda c: "Bay Area" if c == "BAY" else COUNTY_TO_METRO.get(c, "Other CA" if isinstance(c, str) else "Unknown"))
    out["area"] = out.county.map(lambda c: "Bay Area" if c == "BAY" else COUNTY_TO_REGION.get(c, "Other CA" if isinstance(c, str) else "Unknown"))
    out.loc[out.county == "BAY", "county"] = None
    return out
