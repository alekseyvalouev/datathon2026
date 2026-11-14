"""Step 2: every current FOR_RENT listing -> income gate (E6 method), UDP typology (E2 join), and access to services.
Writes cache/listings_access.parquet (internal; has coordinates) and outputs/listing_flow.csv,
outputs/distance_check.csv (BallTree vs brute-force haversine on 300 random locations)."""
import os, sys, ast, duckdb, numpy as np, pandas as pd
from sklearn.neighbors import BallTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

BAY_COUNTIES = ["Alameda County", "Contra Costa County", "Marin County", "Napa County", "San Francisco County",
                "San Mateo County", "Santa Clara County", "Solano County", "Sonoma County"]
# downtown points of the region's larger cities (approximate city-hall/downtown coordinates) -> baseline feature
CITY_CENTERS = {"San Francisco": (37.7793, -122.4193), "Oakland": (37.8044, -122.2712), "San Jose": (37.3382, -121.8863),
                "Berkeley": (37.8715, -122.2730), "Fremont": (37.5485, -121.9886), "Hayward": (37.6688, -122.0808),
                "Santa Rosa": (38.4404, -122.7141), "Vallejo": (38.1041, -122.2566), "Fairfield": (38.2494, -122.0400),
                "Concord": (37.9780, -122.0311), "Walnut Creek": (37.9101, -122.0652), "San Mateo": (37.5630, -122.3255),
                "Palo Alto": (37.4419, -122.1430), "Sunnyvale": (37.3688, -122.0363), "Santa Clara": (37.3541, -121.9552),
                "Napa": (38.2975, -122.2869), "San Rafael": (37.9735, -122.5311), "Richmond": (37.9358, -122.3477),
                "Redwood City": (37.4852, -122.2364), "Mountain View": (37.3861, -122.0839)}


def load_listings():
    con = duckdb.connect(DB, read_only=True)
    df = con.execute("""
        select zpid, county, zipcode, city, homeType,
               try_cast(price as double) rent, try_cast(bedrooms as double) beds, try_cast(bathrooms as double) baths,
               try_cast(livingArea as double) sqft, try_cast(yearBuilt as int) yearBuilt,
               try_cast(latitude as double) lat, try_cast(longitude as double) lon,
               is_listed_by_management_company = 'true' mgmt, try_cast(daysOnZillow as double) days_on
        from z where homeStatus = 'FOR_RENT'""").df()
    allp = con.execute("""select try_cast(latitude as double) lat, try_cast(longitude as double) lon, homeStatus
                          from z where try_cast(latitude as double) is not null""").df()
    con.close()
    flow = [("FOR_RENT listings", len(df))]
    df = df[df.county.isin(BAY_COUNTIES)]; flow.append(("in the 9 Bay counties", len(df)))
    df = df[df.lat.notna() & df.lon.notna()]; flow.append(("with coordinates", len(df)))
    df = df[df.rent.between(500, 30000)]; flow.append(("rent in [500, 30000] (E2 range)", len(df)))
    df = df[df.beds.notna()]; flow.append(("bedrooms known", len(df)))
    df.loc[df.sqft <= 100, "sqft"] = np.nan; df.loc[(df.yearBuilt < 1850) | (df.yearBuilt > 2027), "yearBuilt"] = np.nan
    df["homeType_s"] = df.homeType.replace({"SINGLEFAMILY": "SINGLE_FAMILY", "TOWNHOME": "TOWNHOUSE"})
    df.loc[~df.homeType_s.isin(["APARTMENT", "SINGLE_FAMILY", "TOWNHOUSE", "CONDO"]), "homeType_s"] = "OTHER"
    return df.reset_index(drop=True), allp, flow


def income_gate(df):
    """E6 method: min income = 3 x 12 x rent; household = beds + 1 (studio = 1); HCD 2026 limits by county."""
    il = pd.read_csv(E6_LIMITS); il = il[il.year == LIMIT_YEAR]
    df["hh"] = (df.beds.clip(0, 7) + 1).astype(int)
    for lev in ["LI", "VLI", "MED"]:
        m = {(r.county, k): getattr(r, f"p{k}") for r in il[il.level == lev].itertuples() for k in range(1, 9)}
        df[lev] = [m.get((c, h), np.nan) for c, h in zip(df.county, df.hh)]
    df["inc_needed"] = 3 * 12 * df.rent
    df["ami_needed"] = df.inc_needed / df.MED
    df["qual_LI"] = df.inc_needed <= df.LI; df["qual_VLI"] = df.inc_needed <= df.VLI
    df["qual_LI_25"] = 2.5 * 12 * df.rent <= df.LI      # sensitivity: 2.5x screen
    return df


def tract_join(df):
    """Copied from analysis/e2_turnover_model/s01_build_sample.py (pyshp + shapely point-in-polygon on 2018 TIGER
    tracts, then the Urban Displacement Project SF Bay typology), reading E2's downloaded files in E2_EXT."""
    import shapefile
    from shapely.geometry import shape, Point
    from shapely.strtree import STRtree
    zp = os.path.join(E2_EXT, "tl_2018_06_tract.zip"); ty = os.path.join(E2_EXT, "SanFrancisco_typology_output.csv")
    if not (os.path.exists(zp) and os.path.exists(ty)):
        print("E2 external files missing (run analysis/e2_turnover_model/run_all.py); skipping typology")
        df["tract"] = np.nan; df["typology"] = np.nan; df["typ_group"] = np.nan; return df
    bay = {"001", "013", "041", "055", "075", "081", "085", "095", "097"}
    r = shapefile.Reader(zp)
    geoms, ids = [], []
    for sr in r.iterShapeRecords():
        rec = sr.record.as_dict()
        if rec["COUNTYFP"] in bay:
            geoms.append(shape(sr.shape.__geo_interface__)); ids.append(int(rec["GEOID"]))
    tree = STRtree(geoms)
    out = {}
    for lo, la in df[["lon", "lat"]].drop_duplicates().itertuples(index=False):
        p = Point(lo, la)
        for i in tree.query(p):
            if geoms[i].contains(p): out[(lo, la)] = ids[i]; break
    df["tract"] = [out.get((lo, la)) for lo, la in zip(df.lon, df.lat)]
    t = pd.read_csv(ty, usecols=["GEOID", "typ_cat"])
    def grp(s):
        c = ast.literal_eval(s) if isinstance(s, str) else []
        if not c: return np.nan
        return {"LISD": "Low-income/susceptible", "OD": "Ongoing displacement", "ARG": "At risk of gentrification",
                "EOG": "Early/ongoing gentrification", "AdvG": "Advanced gentrification", "SMMI": "Stable moderate/mixed",
                "ARE": "At risk of exclusive", "BE": "Becoming exclusive", "SAE": "Stable/advanced exclusive"}[c[0]]
    t["typology"] = t.typ_cat.map(grp)
    coarse = {"Low-income/susceptible": "1 Low-income/displacement", "Ongoing displacement": "1 Low-income/displacement",
              "At risk of gentrification": "2 Gentrifying", "Early/ongoing gentrification": "2 Gentrifying",
              "Advanced gentrification": "2 Gentrifying", "Stable moderate/mixed": "3 Moderate/mixed",
              "At risk of exclusive": "4 Exclusive", "Becoming exclusive": "4 Exclusive", "Stable/advanced exclusive": "4 Exclusive"}
    t["typ_group"] = t.typology.map(coarse)
    df = df.merge(t[["GEOID", "typology", "typ_group"]].rename(columns={"GEOID": "tract"}), on="tract", how="left")
    print(f"tract matched {df.tract.notna().mean():.1%}; typology joined for {df.typology.notna().mean():.1%} of listings")
    return df


def access(df, places):
    loc = df[["lat", "lon"]].drop_duplicates().reset_index(drop=True)
    X = np.radians(loc[["lat", "lon"]].values)
    for k in CATS + ["clinic_broad"]:
        p = places[places.svc == k].reset_index(drop=True)
        tree = BallTree(np.radians(p[["lat", "lon"]].values), metric="haversine")
        d, i = tree.query(X, k=1)
        loc[f"d_{k}"] = d[:, 0] * EARTH_M
        for r in RADII:
            loc[f"n{r}_{k}"] = tree.query_radius(X, r / EARTH_M, count_only=True)
        if k == "clinic":
            loc["nearest_clinic_rating"] = p.rating.values[i[:, 0]]
            loc["nearest_clinic_reviews"] = p.reviews_count.values[i[:, 0]]
            rated = p[p.rating.notna()].reset_index(drop=True)
            t2 = BallTree(np.radians(rated[["lat", "lon"]].values), metric="haversine")
            d2, i2 = t2.query(X, k=1)
            loc["d_rated_clinic"] = d2[:, 0] * EARTH_M; loc["nearest_rated_clinic_rating"] = rated.rating.values[i2[:, 0]]
            ind = t2.query_radius(X, TH["clinic"] / EARTH_M)
            loc["mean_rating_clinics_3km"] = [rated.rating.values[j].mean() if len(j) else np.nan for j in ind]
    # brute-force check of the BallTree distances on 300 random locations
    rng = np.random.default_rng(SEED); s = rng.choice(len(loc), 300, replace=False); chk = []
    for k in ["grocery", "clinic", "transit"]:
        p = places[places.svc == k]
        bf = np.array([haversine_m(loc.lat[j], loc.lon[j], p.lat.values, p.lon.values).min() for j in s])
        chk.append((k, 300, float(np.abs(bf - loc[f"d_{k}"].values[s]).max())))
    pd.DataFrame(chk, columns=["service", "n_checked", "max_abs_diff_m"]).to_csv(os.path.join(OUT, "distance_check.csv"), index=False)
    print("distance check (BallTree vs brute force):", chk)
    return df.merge(loc, on=["lat", "lon"], how="left")


def zillow_context(df, allp):
    """Zillow-only spatial context for the model: property density (all statuses) and distance to a big-city center."""
    allp = allp[allp.lat.between(36.8, 39.0) & allp.lon.between(-123.7, -121.4)]
    loc = df[["lat", "lon"]].drop_duplicates().reset_index(drop=True)
    X = np.radians(loc[["lat", "lon"]].values)
    tree = BallTree(np.radians(allp[["lat", "lon"]].drop_duplicates().values), metric="haversine")
    for r in [1000, 3000]:
        loc[f"z_props_{r}"] = tree.query_radius(X, r / EARTH_M, count_only=True)
    cc = np.array(list(CITY_CENTERS.values()))
    dm = np.stack([haversine_m(loc.lat.values, loc.lon.values, la, lo) for la, lo in cc], axis=1)
    loc["d_city_center"] = dm.min(1); loc["nearest_city"] = np.array(list(CITY_CENTERS))[dm.argmin(1)]
    return df.merge(loc, on=["lat", "lon"], how="left")


def main():
    ensure_dirs()
    df, allp, flow = load_listings()
    df = income_gate(df)
    df = tract_join(df)
    places = pd.read_parquet(os.path.join(CACHE, "places_cat.parquet"))
    df = access(df, places)
    df = zillow_context(df, allp)
    # origin areas: SF + San Mateo (the high-turnover-premium counties in E2/E6) and E2's top-10 ZIPs (n>=20)
    z = pd.read_csv(E2_ZIPS); z = z[~z.low_n_flag].sort_values("obs_median_jump_annual", ascending=False).head(10)
    df["e2_top_zip"] = df.zipcode.astype(str).isin(z.zipcode.astype(str))
    df["origin_area"] = df.county.isin(["San Francisco County", "San Mateo County"]) | df.e2_top_zip
    df["loc_id"] = df.groupby(["lat", "lon"]).ngroup()
    df["n_at_loc"] = df.groupby("loc_id").zpid.transform("size")
    flow.append(("final listings", len(df))); flow.append(("distinct coordinates (buildings)", df.loc_id.nunique()))
    pd.DataFrame(flow, columns=["step", "n"]).to_csv(os.path.join(OUT, "listing_flow.csv"), index=False)
    print(pd.DataFrame(flow).to_string(index=False))
    df.to_parquet(os.path.join(CACHE, "listings_access.parquet"), index=False)


if __name__ == "__main__":
    main()
