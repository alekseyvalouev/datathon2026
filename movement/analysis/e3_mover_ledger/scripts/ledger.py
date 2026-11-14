"""Step 3: the mover's ledger. Residual income = monthly gross wage (173 h x hourly) - monthly rent.

Rents
  Bay in-place   : median current Zillow FOR_RENT listing rent (1-BR / 2-BR), 9-county Bay and SF county.
  Bay stay +1y   : in-place x (1 + AB 1482 cap) where cap = min(5% + CPI, 10%); CPI assumed 3% -> 8% (max legal raise).
  Bay re-entry   : in-place x county turnover premium (median next_first/last_p for the same unit, consecutive
                   rental listings, start_gap_y in [1,6], next listing started 2025+), listing-weighted for the Bay.
  Destinations   : ZORI (latest month) x bedroom factor k_b, where k_b = Bay b-BR median listing / Bay ZORI
                   (county-matched ZORI metro, listing-weighted). Assumes the b-BR-to-typical-rent ratio is the
                   same as in the Bay.
Wages (hourly, full-time 173 h/month)
  OEWS : BLS OEWS May 2025 metro median hourly (all places; Bay = San Francisco-Oakland-Fremont MSA).
  Indeed posted : median posted hourly mid-point of postings with pay (CA only). Destinations with < MIN_N
                  postings with pay fall back to the pooled Central Valley (Stockton+Modesto+Fresno) and are flagged.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import duckdb
from occupations import LABELS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "outputs")
RAW = os.path.join(HERE, "..", "raw")
ZDB = os.path.abspath(os.path.join(HERE, "..", "..", "cache", "zillow.duckdb"))
HOURS = 173
AB1482_CAP = min(0.05 + 0.03, 0.10)
MIN_N = 15
OCCS = ["cna", "caregiver", "med_asst", "warehouse", "cashier", "cook", "crew", "janitor", "security", "driver"]
OCC_SOC = {"cna": "311131", "caregiver": "311120", "med_asst": "319092", "warehouse": "537062", "cashier": "412011",
           "cook": "352014", "crew": "353023", "janitor": "372011", "security": "339032", "driver": "533033"}
DEST = [  # scenario label, group, ZORI RegionName, OEWS CBSA, Indeed metro
    ("Sacramento", "CA inland", "Sacramento, CA", "40900", "Sacramento"),
    ("Stockton", "CA inland", "Stockton, CA", "44700", "Stockton"),
    ("Modesto", "CA inland", "Modesto, CA", "33700", "Modesto"),
    ("Fresno", "CA inland", "Fresno, CA", "23420", "Fresno"),
    ("Phoenix", "Out of state", "Phoenix, AZ", "38060", None),
    ("Las Vegas", "Out of state", "Las Vegas, NV", "29820", None),
    ("Reno", "Out of state", "Reno, NV", "39900", None),
    ("Boise", "Out of state", "Boise City, ID", "14260", None),
    ("Dallas", "Out of state", "Dallas, TX", "19100", None),
    ("Houston", "Out of state", "Houston, TX", "26420", None),
    ("Portland", "Out of state", "Portland, OR", "38900", None),
]
COUNTY_ZORI = {"Alameda County": "San Francisco, CA", "Contra Costa County": "San Francisco, CA",
               "Marin County": "San Francisco, CA", "San Francisco County": "San Francisco, CA",
               "San Mateo County": "San Francisco, CA", "Santa Clara County": "San Jose, CA",
               "Napa County": "Napa, CA", "Solano County": "Vallejo, CA", "Sonoma County": "Santa Rosa, CA"}


def bay_rents():
    con = duckdb.connect(ZDB, read_only=True)
    r = con.execute("""select county, try_cast(bedrooms as int) beds, count(*) n, median(try_cast(price as double)) rent
        from z where homeStatus='FOR_RENT' and try_cast(price as double) between 500 and 20000
          and try_cast(bedrooms as int) in (1,2) group by 1,2""").df()
    rb = con.execute("""select try_cast(bedrooms as int) beds, count(*) n, median(try_cast(price as double)) rent
        from z where homeStatus='FOR_RENT' and try_cast(price as double) between 500 and 20000
          and try_cast(bedrooms as int) in (1,2) group by 1""").df()
    t = con.execute("""select county, count(*) n, median(next_first/last_p) jump, median(start_gap_y) gap,
          median(power(next_first/last_p, 1/start_gap_y)) - 1 jump_per_year
        from turn where start_gap_y between 1 and 6 and next_start >= '2025-01-01' and last_p > 0
        group by 1""").df()
    tb = con.execute("""select count(*) n, median(next_first/last_p) jump, median(start_gap_y) gap,
          median(power(next_first/last_p, 1/start_gap_y)) - 1 jump_per_year
        from turn where start_gap_y between 1 and 6 and next_start >= '2025-01-01' and last_p > 0""").df()
    t_all = con.execute("""select count(*) n, median(next_first/last_p) jump from turn
        where start_gap_y between 1 and 6""").df()
    con.close()
    return r, rb, t, tb, t_all


def zori():
    z = pd.read_csv(os.path.join(RAW, "Metro_zori_uc_sfrcondomfr_sm_month.csv"))
    last = [c for c in z.columns if c[:2] == "20"][-1]
    return z.set_index("RegionName")[last], last


def oews():
    r = json.load(open(os.path.join(RAW, "oews_api.json")))
    rows = []
    for s in r:
        sid = s["seriesID"]
        if not s["data"]:
            continue
        rows.append(dict(cbsa=sid[6:11], soc=sid[17:23], dtype=sid[23:25], year=s["data"][0]["year"],
                         value=pd.to_numeric(s["data"][0]["value"], errors="coerce")))
    d = pd.DataFrame(rows)
    return d[d.dtype == "08"].set_index(["cbsa", "soc"]).value, d[d.dtype == "03"].set_index(["cbsa", "soc"]).value


def indeed_wages():
    p = pd.read_parquet(os.path.join(OUT, "postings_with_pay.parquet"))
    p = p[p.occ.isin(OCCS)]
    p["place"] = p.metro
    p.loc[p.county == "San Francisco", "place2"] = "San Francisco"
    obs = p[p.pay_mid.notna()]
    g = obs.groupby(["occ", "metro"]).agg(n_pay=("pay_mid", "size"), med_mid=("pay_mid", "median"),
                                          med_low=("pay_low", "median")).reset_index()
    gi = p.groupby(["occ", "metro"]).agg(n_all=("pay_hourly", "size"), med_with_imputed=("pay_hourly", "median")).reset_index()
    g = gi.merge(g, on=["occ", "metro"], how="left")
    sf = obs[obs.county == "San Francisco"].groupby("occ").agg(n_pay=("pay_mid", "size"), med_mid=("pay_mid", "median"),
                                                               med_low=("pay_low", "median")).reset_index().assign(metro="San Francisco")
    cv = obs[obs.metro.isin(["Stockton", "Modesto", "Fresno"])].groupby("occ").agg(
        n_pay=("pay_mid", "size"), med_mid=("pay_mid", "median"), med_low=("pay_low", "median")).reset_index().assign(metro="Central Valley pooled")
    return pd.concat([g, sf, cv], ignore_index=True)


def main():
    r, rb, t, tb, t_all = bay_rents()
    zs, zmonth = zori()
    med, mean = oews()
    iw = indeed_wages()
    iw.to_csv(os.path.join(OUT, "indeed_wages_by_occ_metro.csv"), index=False)

    # turnover premium
    t = t.merge(r.groupby("county").n.sum().rename("n_list"), on="county")
    bay_prem = float(np.average(t.jump, weights=t.n_list))
    sf_prem = float(t.set_index("county").loc["San Francisco County", "jump"])
    t.to_csv(os.path.join(OUT, "turnover_premium_by_county.csv"), index=False)

    # bedroom factor
    r["zori"] = r.county.map(COUNTY_ZORI).map(zs)
    k = {b: float(np.average(d.rent / d.zori, weights=d.n)) for b, d in r.groupby("beds")}
    rent_bay = rb.set_index("beds").rent.to_dict()
    rent_sf = r[r.county == "San Francisco County"].set_index("beds").rent.to_dict()
    bay_zori = float(np.average(r.zori, weights=r.n))

    # rent table
    rents = []
    for beds in (1, 2):
        for origin, base, prem in [("Bay Area", rent_bay[beds], bay_prem), ("San Francisco", rent_sf[beds], sf_prem)]:
            rents += [dict(origin=origin, scenario="Stay (in-place)", group="Bay", beds=beds, rent=base),
                      dict(origin=origin, scenario=f"Stay +1y at AB1482 max (+{AB1482_CAP:.0%})", group="Bay", beds=beds, rent=base * (1 + AB1482_CAP)),
                      dict(origin=origin, scenario="Re-rent in Bay (turnover)", group="Bay", beds=beds, rent=base * prem)]
        for lab, grp, zname, _, _ in DEST:
            rents.append(dict(origin="dest", scenario=lab, group=grp, beds=beds, rent=zs[zname] * k[beds], zori=zs[zname]))
    rents = pd.DataFrame(rents)
    rents.to_csv(os.path.join(OUT, "rents_by_scenario.csv"), index=False)

    # ledger
    rows = []
    for origin in ["Bay Area", "San Francisco"]:
        for occ in OCCS:
            soc = OCC_SOC[occ]
            for beds in (1, 2):
                rr = rents[(rents.beds == beds) & ((rents.origin == origin) | (rents.origin == "dest"))]
                for x in rr.itertuples():
                    if x.group == "Bay":
                        cbsa, imetro = "41860", ("San Francisco" if origin == "San Francisco" else "Bay Area")
                    else:
                        d = next(d for d in DEST if d[0] == x.scenario)
                        cbsa, imetro = d[3], d[4]
                    w_oews = med.get((cbsa, soc), np.nan)
                    w_ind, n_ind, ind_src = np.nan, 0, None
                    if imetro is not None:
                        q = iw[(iw.occ == occ) & (iw.metro == imetro)]
                        if len(q) and q.n_pay.fillna(0).iloc[0] >= MIN_N:
                            w_ind, n_ind, ind_src = q.med_mid.iloc[0], int(q.n_pay.iloc[0]), imetro
                        else:
                            fb = "Bay Area" if imetro == "San Francisco" else "Central Valley pooled"
                            q = iw[(iw.occ == occ) & (iw.metro == fb)]
                            if len(q) and q.n_pay.fillna(0).iloc[0] >= MIN_N:
                                w_ind, n_ind, ind_src = q.med_mid.iloc[0], int(q.n_pay.iloc[0]), fb + " (fallback)"
                    for src, w in [("OEWS median", w_oews), ("Indeed posted median", w_ind)]:
                        if np.isnan(w):
                            continue
                        gross = w * HOURS
                        rows.append(dict(origin=origin, occ=occ, occupation=LABELS[occ], beds=beds, scenario=x.scenario,
                                         group=x.group, wage_source=src, hourly=w,
                                         indeed_n=n_ind if src.startswith("Indeed") else None,
                                         indeed_wage_from=ind_src if src.startswith("Indeed") else None,
                                         gross_monthly=gross, rent=x.rent, residual=gross - x.rent, rent_burden=x.rent / gross))
    L = pd.DataFrame(rows)
    L.to_csv(os.path.join(OUT, "ledger_long.csv"), index=False)

    info = dict(zori_month=zmonth, bedroom_factor=k, bay_zori_weighted=bay_zori, bay_turnover_premium=bay_prem,
                sf_turnover_premium=sf_prem, bay_turnover_overall=tb.to_dict("records"),
                turnover_all_years=t_all.to_dict("records"), rent_bay=rent_bay, rent_sf=rent_sf,
                ab1482_cap_assumed=AB1482_CAP, hours_per_month=HOURS)
    json.dump(info, open(os.path.join(OUT, "ledger_info.json"), "w"), indent=1, default=float)
    # compact wide table: 1-BR, OEWS, Bay origin
    for src, tag in [("OEWS median", "oews"), ("Indeed posted median", "indeed")]:
        for origin in ["Bay Area", "San Francisco"]:
            w = L[(L.beds == 1) & (L.wage_source == src) & (L.origin == origin)]
            w.pivot_table(index="occupation", columns="scenario", values="rent_burden").round(3).to_csv(
                os.path.join(OUT, f"ledger_burden_1br_{tag}_{origin.replace(' ', '_').lower()}.csv"))
            w.pivot_table(index="occupation", columns="scenario", values="residual").round(0).to_csv(
                os.path.join(OUT, f"ledger_residual_1br_{tag}_{origin.replace(' ', '_').lower()}.csv"))
    print(json.dumps(info, indent=1, default=float))
    return L


if __name__ == "__main__":
    main()
