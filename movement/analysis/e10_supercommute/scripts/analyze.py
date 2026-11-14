"""E10 analysis: super-commuting into the 9-county Bay from county flows (outputs/county_flows.csv).
Writes outputs/*.csv; figures are made by figs.py."""
import os, json, math
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, OUT = os.path.join(HERE, "raw"), os.path.join(HERE, "outputs")
LEDGER = os.path.join(HERE, "..", "e3_mover_ledger", "outputs", "ledger_long.csv")

BAY = ["06001", "06013", "06041", "06055", "06075", "06081", "06085", "06095", "06097"]
RING = ["06077", "06099", "06067", "06047", "06113", "06061", "06017", "06069", "06087", "06053", "06033"]
BANDS = ["S000", "SE01", "SE02", "SE03", "SA01", "SA02", "SA03", "SI01", "SI02", "SI03"]
BAND_LABEL = {"S000": "All jobs", "SE01": "<= $1,250/mo", "SE02": "$1,251-3,333/mo", "SE03": "> $3,333/mo",
              "SA01": "Age <= 29", "SA02": "Age 30-54", "SA03": "Age 55+",
              "SI01": "Goods producing", "SI02": "Trade, transp., utilities", "SI03": "All other services"}
# E3 ledger destination metros -> home counties (same definitions as E3 README; Merced added)
METROS = {"Sacramento": ["06067", "06061", "06017", "06113"], "Stockton": ["06077"],
          "Modesto": ["06099"], "Fresno": ["06019"], "Merced": ["06047"]}
# Cost assumptions (sources in README)
IRS_RATE = 0.76      # $/mile, IRS business standard mileage rate, Jul 1-Dec 31 2026 (irs.gov, IR-2026-29)
AAA_FUEL = 0.13      # $/mile, AAA Your Driving Costs 2025: average fuel cost 13.00 cents/mile (fuel only)
DAYS_FULL = 250      # 5 days x 50 weeks, assumption
DAYS_HYBRID = 150    # 3 days x 50 weeks, assumption (sensitivity)
CIRCUITY = 1.2       # fallback only if OSRM table missing: haversine x 1.2 (assumption)


def load(jt="JT00"):
    f = pd.read_csv(os.path.join(OUT, "county_flows.csv"), dtype={"h_cty": str, "w_cty": str})
    return f[f.jt == jt]


def jt01_check():
    """multiple-job robustness: outside-9 share among CA-resident-held Bay jobs, all jobs vs primary jobs"""
    rows = []
    for jt in ["JT00", "JT01"]:
        f = load(jt); f = f[(f.part == "main") & f.w_cty.isin(BAY)]
        for y, d in f.groupby("year"):
            out9 = d[~d.h_cty.isin(BAY)]
            for b in ["S000", "SE01", "SE02", "SE03"]:
                rows.append(dict(jt=jt, year=y, band=b, bay_jobs=d[b].sum(), outside9=out9[b].sum(),
                                 share_outside9=out9[b].sum() / d[b].sum()))
    r = pd.DataFrame(rows)
    r = r[r.year.isin(r[r.jt == "JT01"].year.unique())]
    r.to_csv(os.path.join(OUT, "jt01_primary_job_check.csv"), index=False)


def cenpop():
    c = pd.read_csv(os.path.join(RAW, "CenPop2020_Mean_CO06.txt"), dtype=str, encoding="utf-8-sig")
    c.columns = [x.strip() for x in c.columns]
    c["fips"] = c.STATEFP + c.COUNTYFP
    c["lat"], c["lon"], c["pop"] = c.LATITUDE.astype(float), c.LONGITUDE.astype(float), c.POPULATION.astype(int)
    return c.set_index("fips")[["COUNAME", "lat", "lon", "pop"]].rename(columns={"COUNAME": "name"})


def routes(cp):
    """one-way driving miles and free-flow minutes, county center of pop -> Bay county center of pop"""
    p = os.path.join(RAW, "osrm_table.json")
    rows = []
    if os.path.exists(p):
        d = json.load(open(p)); order = d["_order"]
        bay_order = [x for x in order if x in BAY]
        for i, h in enumerate(order):
            for j, w in enumerate(bay_order):
                rows.append((h, w, d["distances"][i][j] / 1609.344, d["durations"][i][j] / 60, "OSRM"))
    else:
        for h in cp.index:
            for w in BAY:
                a, b = cp.loc[h], cp.loc[w]
                la1, lo1, la2, lo2 = map(math.radians, [a.lat, a.lon, b.lat, b.lon])
                hv = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
                mi = 2 * 3958.8 * math.asin(math.sqrt(hv)) * CIRCUITY
                rows.append((h, w, mi, np.nan, "haversine*1.2"))
    return pd.DataFrame(rows, columns=["h_cty", "w_cty", "miles_oneway", "minutes_freeflow", "route_src"])


def home_group(h):
    if h in BAY: return "Bay (9 counties)"
    if h in RING: return "Exurban ring (11 named)"
    if h.startswith("06"): return "Other CA"
    return "Out of state"


def cpi_annual():
    vals = {}
    for fn in ["cpi_2010_2019.json", "cpi_2020_2024.json"]:
        p = os.path.join(RAW, fn)
        if not os.path.exists(p): continue
        for x in json.load(open(p))["Results"]["series"][0]["data"]:
            if x["period"].startswith("M") and x["period"] != "M13":
                vals.setdefault(int(x["year"]), []).append(float(x["value"]))
    return {y: np.mean(v) for y, v in vals.items() if len(v) == 12}


def main():
    f = load(); cp = cenpop(); names = cp["name"].to_dict()
    years = sorted(f.year.unique()); y0, yl = years[0], years[-1]
    has_aux = set(f[f.part == "aux"].year)
    bay = f[f.w_cty.isin(BAY)].copy()
    bay["home_group"] = bay.h_cty.map(home_group)

    # ---- 1. full county x county flows into Bay work counties
    pair = bay.groupby(["year", "h_cty", "w_cty"], as_index=False)[BANDS].sum()
    pair["h_name"] = pair.h_cty.map(names).fillna("Out of state (" + pair.h_cty.str[:2] + ")")
    pair["w_name"] = pair.w_cty.map(names)
    pair.to_csv(os.path.join(OUT, "bay_inflows_by_county_pair.csv"), index=False)

    # ---- 2. share of Bay jobs held by residents outside the 9 counties, by band
    g = bay.groupby(["year", "home_group"])[BANDS].sum()
    rows = []
    for y in years:
        gy = g.loc[y]
        for b in BANDS:
            tot_main = gy.drop("Out of state", errors="ignore")[b].sum()
            tot_all = gy[b].sum()
            outside_ca = tot_main - gy.loc["Bay (9 counties)", b]
            oos = gy[b].get("Out of state", np.nan) if y in has_aux else np.nan
            rows.append(dict(year=y, band=b, band_label=BAND_LABEL[b],
                             bay_jobs_ca_res=tot_main, bay_jobs_all=tot_all if y in has_aux else np.nan,
                             held_by_bay_res=gy.loc["Bay (9 counties)", b],
                             held_by_ring=gy.loc["Exurban ring (11 named)", b],
                             held_by_other_ca=gy.loc["Other CA", b],
                             held_by_out_of_state=oos,
                             outside9_ca=outside_ca,
                             share_outside9_ca=outside_ca / tot_main,
                             share_ring=gy.loc["Exurban ring (11 named)", b] / tot_main,
                             share_outside9_incl_oos=(outside_ca + oos) / tot_all if y in has_aux else np.nan,
                             share_oos=oos / tot_all if y in has_aux else np.nan))
    sh = pd.DataFrame(rows)
    sh.to_csv(os.path.join(OUT, "bay_jobs_outside_share_by_band.csv"), index=False)

    # ---- growth decomposition: who accounts for the change in outside-resident Bay jobs
    dec = []
    for a, b_ in [(y0, 2019), (2019, yl), (y0, yl)]:
        if a not in years or b_ not in years or a >= b_: continue
        A, B = sh[sh.year == a].set_index("band"), sh[sh.year == b_].set_index("band")
        d_out_all = B.loc["S000", "outside9_ca"] - A.loc["S000", "outside9_ca"]
        for band in ["SE01", "SE02", "SE03", "SA01", "SA02", "SA03"]:
            d_out = B.loc[band, "outside9_ca"] - A.loc[band, "outside9_ca"]
            d_tot = B.loc[band, "bay_jobs_ca_res"] - A.loc[band, "bay_jobs_ca_res"]
            dec.append(dict(period=f"{a}-{b_}", band=band, band_label=BAND_LABEL[band],
                            outside9_start=A.loc[band, "outside9_ca"], outside9_end=B.loc[band, "outside9_ca"],
                            change_outside9=d_out, pct_change_outside9=d_out / A.loc[band, "outside9_ca"],
                            share_of_total_outside9_change=d_out / d_out_all if d_out_all else np.nan,
                            bay_jobs_change=d_tot, pct_change_bay_jobs=d_tot / A.loc[band, "bay_jobs_ca_res"],
                            share_outside9_start=A.loc[band, "share_outside9_ca"],
                            share_outside9_end=B.loc[band, "share_outside9_ca"],
                            share_change_pp=100 * (B.loc[band, "share_outside9_ca"] - A.loc[band, "share_outside9_ca"])))
    pd.DataFrame(dec).to_csv(os.path.join(OUT, "growth_decomposition.csv"), index=False)

    # ---- nominal-band check: CPI drift of the $3,333 threshold + composition index robust to common drift
    cpi = cpi_annual()
    infl = []
    if y0 in cpi and yl in cpi:
        for y in years:
            if y in cpi:
                infl.append(dict(year=y, cpi_u=cpi[y],
                                 se03_threshold_in_2010_dollars=3333 * cpi[y0] / cpi[y],
                                 se02_floor_in_2010_dollars=1251 * cpi[y0] / cpi[y]))
    comp = []
    for y in years:
        gy = g.loc[y]
        bres = gy.loc["Bay (9 counties)"]
        outs = gy.loc[["Exurban ring (11 named)", "Other CA"]].sum()
        ring = gy.loc["Exurban ring (11 named)"]
        lo_b = (bres.SE01 + bres.SE02) / bres.S000
        lo_o = (outs.SE01 + outs.SE02) / outs.S000
        lo_r = (ring.SE01 + ring.SE02) / ring.S000
        comp.append(dict(year=y, lowmid_share_bay_res=lo_b, lowmid_share_outside9=lo_o, lowmid_share_ring=lo_r,
                         lowmid_ratio_outside_vs_bay=lo_o / lo_b, lowmid_gap_pp=100 * (lo_o - lo_b),
                         se03_share_bay_res=bres.SE03 / bres.S000, se03_share_outside9=outs.SE03 / outs.S000))
    comp = pd.DataFrame(comp)
    if infl: comp = comp.merge(pd.DataFrame(infl), on="year", how="left")
    comp.to_csv(os.path.join(OUT, "earnings_mix_nominal_check.csv"), index=False)

    # ---- 3. top origin -> destination pairs with distance/time/cost
    rt = routes(cp)
    rt.to_csv(os.path.join(OUT, "county_drive_distances.csv"), index=False)
    nb = pair[~pair.h_cty.isin(BAY) & pair.h_cty.str.startswith("06")]
    last = nb[nb.year == yl].merge(nb[nb.year == y0][["h_cty", "w_cty", "S000", "SE01", "SE02", "SE03"]],
                                   on=["h_cty", "w_cty"], how="left", suffixes=("", f"_{y0}"))
    if 2019 in years:
        last = last.merge(nb[nb.year == 2019][["h_cty", "w_cty", "S000"]].rename(columns={"S000": "S000_2019"}),
                          on=["h_cty", "w_cty"], how="left")
    last = last.merge(rt, on=["h_cty", "w_cty"], how="left")
    last["lowmid_share"] = (last.SE01 + last.SE02) / last.S000
    last[f"change_{y0}_{yl}"] = last.S000 - last[f"S000_{y0}"]
    last["annual_cost_irs_full"] = 2 * last.miles_oneway * DAYS_FULL * IRS_RATE
    last["annual_cost_fuel_only"] = 2 * last.miles_oneway * DAYS_FULL * AAA_FUEL
    last["annual_hours_freeflow"] = 2 * last.minutes_freeflow * DAYS_FULL / 60
    last = last.sort_values("S000", ascending=False)
    keep = ["h_cty", "h_name", "w_cty", "w_name", "S000", f"S000_{y0}"] + (["S000_2019"] if 2019 in years else []) + \
           [f"change_{y0}_{yl}", "SE01", "SE02", "SE03", "lowmid_share", "SA01", "SA02", "SA03",
            "miles_oneway", "minutes_freeflow", "route_src", "annual_cost_irs_full", "annual_cost_fuel_only",
            "annual_hours_freeflow"]
    last[keep].head(40).to_csv(os.path.join(OUT, f"top_pairs_{yl}.csv"), index=False)

    # ---- distance bands: separate plausible daily commuters from long-distance (remote / HQ-coded / weekly)
    pd_ = pair[pair.h_cty.str.startswith("06")].merge(rt, on=["h_cty", "w_cty"], how="left")
    pd_["dist_band"] = np.select(
        [pd_.h_cty.isin(BAY), pd_.miles_oneway <= 60, pd_.miles_oneway <= 120],
        ["Bay resident", "Outside 9, <=60 mi", "Outside 9, 60-120 mi"], "Outside 9, >120 mi (not daily-commutable)")
    oos = pair[~pair.h_cty.str.startswith("06")].assign(dist_band="Out of state")
    db = pd.concat([pd_, oos]).groupby(["year", "dist_band"])[BANDS].sum().reset_index()
    tot = db[db.dist_band != "Out of state"].groupby("year")[BANDS].sum()
    for b in BANDS:
        db[f"{b}_share_of_ca_res_bay_jobs"] = db[b] / db.year.map(tot[b])
    db.to_csv(os.path.join(OUT, "bay_jobs_by_distance_band.csv"), index=False)
    # headline: commutable (<=120 mi) outside-9 share vs all outside-9 share, by band, key years
    hl = []
    for y in [y0, 2019, 2020, yl]:
        d = db[db.year == y].set_index("dist_band")
        for b in ["S000", "SE01", "SE02", "SE03", "SA01", "SA02", "SA03"]:
            com = d.loc[["Outside 9, <=60 mi", "Outside 9, 60-120 mi"], b].sum()
            far = d.loc["Outside 9, >120 mi (not daily-commutable)", b]
            t = tot.loc[y, b]
            hl.append(dict(year=y, band=b, band_label=BAND_LABEL[b], bay_jobs_ca_res=t,
                           outside9_commutable_le120mi=com, outside9_far_gt120mi=far,
                           share_commutable=com / t, share_far=far / t, share_all_outside9=(com + far) / t))
    pd.DataFrame(hl).to_csv(os.path.join(OUT, "headline_shares.csv"), index=False)

    # origin-county trend + 'export share' (share of the county's resident CA jobs that are located in the Bay)
    allres = f[(f.part == "main")].groupby(["year", "h_cty"])["S000"].sum().rename("resident_jobs_ca")
    org = nb.groupby(["year", "h_cty"])[["S000", "SE01", "SE02", "SE03"]].sum().join(allres)
    org["bay_job_share_of_residents"] = org.S000 / org.resident_jobs_ca
    org = org.reset_index(); org["h_name"] = org.h_cty.map(names)
    org.to_csv(os.path.join(OUT, "origin_county_trend.csv"), index=False)

    # ---- commute cost line for E3 ledger, by destination metro
    led_rows = []
    for metro, ctys in METROS.items():
        sub = last[last.h_cty.isin(ctys)]
        sub = sub[sub.miles_oneway.notna()]
        for wname, wcol in [("low/middle earners (SE01+SE02)", None), ("all jobs (S000)", "S000")]:
            w = (sub.SE01 + sub.SE02) if wcol is None else sub[wcol]
            mi = np.average(sub.miles_oneway, weights=w)
            mn = np.average(sub.minutes_freeflow, weights=w) if sub.minutes_freeflow.notna().all() else np.nan
            res = org[(org.year == yl) & org.h_cty.isin(ctys)]
            led_rows.append(dict(
                dest_metro=metro, home_counties=";".join(ctys), weight=wname, lodes_year=yl,
                bay_jobs_held=int(sub.S000.sum()), bay_jobs_lowmid=int((sub.SE01 + sub.SE02).sum()),
                bay_jobs_held_2010=int(sub[f"S000_{y0}"].sum()),
                bay_job_share_of_residents=res.S000.sum() / res.resident_jobs_ca.sum(),
                plausible_daily=bool(mi <= 120),
                nearest_bay_county=sub.loc[sub.miles_oneway.idxmin(), "w_name"],
                miles_oneway_min=sub.miles_oneway.min(),
                miles_oneway_weighted=mi, minutes_oneway_freeflow_weighted=mn,
                annual_miles_fulltime=2 * mi * DAYS_FULL,
                annual_commute_cost_irs=2 * mi * DAYS_FULL * IRS_RATE,
                monthly_commute_cost_irs=2 * mi * DAYS_FULL * IRS_RATE / 12,
                annual_commute_cost_fuel_only=2 * mi * DAYS_FULL * AAA_FUEL,
                monthly_commute_cost_fuel_only=2 * mi * DAYS_FULL * AAA_FUEL / 12,
                annual_commute_cost_irs_hybrid3d=2 * mi * DAYS_HYBRID * IRS_RATE,
                annual_hours_freeflow=2 * mn * DAYS_FULL / 60,
                monthly_hours_freeflow=2 * mn * DAYS_FULL / 60 / 12,
                irs_rate_per_mile=IRS_RATE, fuel_rate_per_mile=AAA_FUEL, days_per_year=DAYS_FULL))
    cc = pd.DataFrame(led_rows)
    cc.to_csv(os.path.join(OUT, "commute_cost_for_ledger.csv"), index=False)

    # ---- ledger-adjusted residual: keep the Bay job (Bay OEWS wage), live inland, pay commute
    if os.path.exists(LEDGER):
        L = pd.read_csv(LEDGER)
        L = L[(L.origin == "Bay Area") & (L.wage_source == "OEWS median")]
        cmon = cc[cc.weight.str.startswith("low")].set_index("dest_metro")
        out = []
        for (occ, beds), s in L.groupby(["occ", "beds"]):
            s = s.set_index("scenario")
            bay_gross = s.loc["Stay (in-place)", "gross_monthly"]
            base = dict(occ=occ, occupation=s.occupation.iloc[0], beds=beds, bay_gross_monthly=bay_gross,
                        stay_residual=s.loc["Stay (in-place)", "residual"],
                        rerent_bay_residual=s.loc["Re-rent in Bay (turnover)", "residual"])
            for m in ["Sacramento", "Stockton", "Modesto", "Fresno"]:
                if m not in s.index: continue
                r = s.loc[m]
                out.append(dict(base, dest_metro=m, dest_rent=r.rent,
                                move_local_wage_residual=r.residual,
                                commute_monthly_irs=cmon.loc[m, "monthly_commute_cost_irs"],
                                commute_monthly_fuel=cmon.loc[m, "monthly_commute_cost_fuel_only"],
                                commute_hours_month=cmon.loc[m, "monthly_hours_freeflow"],
                                keep_bay_job_residual_irs=bay_gross - r.rent - cmon.loc[m, "monthly_commute_cost_irs"],
                                keep_bay_job_residual_fuel=bay_gross - r.rent - cmon.loc[m, "monthly_commute_cost_fuel_only"]))
        pd.DataFrame(out).to_csv(os.path.join(OUT, "ledger_with_commute.csv"), index=False)
    jt01_check()
    print("analysis done; latest LODES year", yl, "; aux years", sorted(has_aux))


if __name__ == "__main__":
    main()
