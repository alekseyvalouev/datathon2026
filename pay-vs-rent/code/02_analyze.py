"""Pay vs rent burden by occupation class, Bay Area, ACS 1-year PUMS 2018-2024.

Question: pay rose, so did renting get easier? For each of the 17 occupation classes used in
ai-labor-distribution (results/occp_crosswalk.csv) we compare 2018-19 with 2023-24:
  * median annual wage of full-time, year-round wage/salary workers (nominal dollars;
    the pooled figure is the mean of the two single-year medians)
  * among those workers who live in a cash-rent household, the share whose household pays
    30%+ (and 50%+) of its income in gross rent (GRPIP)
Standard errors use the 80 ACS replicate weights (successive-difference replication).
The two-year pools were fixed before looking at class-level results, to halve sampling noise.

Outputs: results/pay_rent_by_class.csv, results/region_by_year.csv
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA, RES = os.path.join(BASE, "data"), os.path.join(BASE, "results")
XWALK = os.path.join(os.path.dirname(BASE), "ai-labor-distribution", "results", "occp_crosswalk.csv")
YEARS = [2018, 2019, 2021, 2022, 2023, 2024]
PRE, POST = [2018, 2019], [2023, 2024]
REPS = [f"PWGTP{i}" for i in range(1, 81)]
GROUPS = {
    "ALL": None,
    "AI_POSITIONED": ["AI_PRODUCER", "SOFTWARE_ENG", "DATA_ENG_ANALYTICS"],
    "EXPOSED": ["CLERICAL_ADMIN", "CUSTOMER_SUPPORT", "PROF_EXPOSED"],
}
SINGLE = ["PRODUCT_DESIGN", "OTHER_ENGINEERING", "MANAGEMENT", "SALES_BIZ", "HEALTH_CLINICAL",
          "PROF_EXPOSED", "CLERICAL_ADMIN", "CUSTOMER_SUPPORT", "EDUCATION", "SKILLED_TRADE",
          "FRONTLINE_SERVICE", "OTHER"]


def wq(v, w, q=0.5):
    v, w = np.asarray(v, float), np.asarray(w, float)
    o = np.argsort(v)
    c = np.cumsum(w[o])
    return v[o][np.searchsorted(c, q * c[-1])]


def load():
    p = pd.concat([pd.read_parquet(f"{DATA}/p_{y}.parquet") for y in YEARS], ignore_index=True)
    h = pd.concat([pd.read_parquet(f"{DATA}/h_{y}.parquet") for y in YEARS], ignore_index=True)
    x = pd.read_csv(XWALK, dtype={"occp": str})
    x["OCCP"] = x.occp.astype(int)
    p = p.merge(x[["OCCP", "occ_class"]], on="OCCP", how="left")
    p["wage"] = p.WAGP * p.ADJINC / 1e6
    # full year: 50+ weeks. 2018 only has the bracketed WKW (1 = 50-52 weeks).
    full_year = np.where(p.YEAR == 2018, p.WKW == 1, p.WKWN >= 50)
    h["rent"] = h.GRNTP * h.ADJHSG / 1e6
    h["hinc"] = h.HINCP * h.ADJINC / 1e6
    w = p[p.ESR.isin([1, 2]) & p.COW.isin([1, 2, 3, 4, 5]) & (p.WKHP >= 35) & full_year & (p.wage > 0)]
    w = w.merge(h[["SERIALNO", "YEAR", "TEN", "rent", "GRPIP"]], on=["SERIALNO", "YEAR"], how="left")
    assert w.occ_class.notna().all(), "unmapped OCCP codes"
    return w, h


def class_stats(d, r, col):
    s = {}
    for tag, yrs in [("pre", PRE), ("post", POST)]:
        rr = r[r.YEAR.isin(yrs)]
        s[f"burden30_{tag}"] = np.average(rr.GRPIP >= 30, weights=rr[col])
        s[f"burden50_{tag}"] = np.average(rr.GRPIP >= 50, weights=rr[col])
        s[f"pay_{tag}"] = np.mean([wq(d[d.YEAR == y].wage, d[d.YEAR == y][col]) for y in yrs])
        s[f"renter_pay_{tag}"] = np.mean([wq(r[r.YEAR == y].wage, r[r.YEAR == y][col]) for y in yrs])
    s["pay_growth"] = s["pay_post"] / s["pay_pre"] - 1
    s["renter_pay_growth"] = s["renter_pay_post"] / s["renter_pay_pre"] - 1
    s["burden30_change"] = s["burden30_post"] - s["burden30_pre"]
    s["burden30_ratio"] = s["burden30_post"] / s["burden30_pre"]
    s["burden50_change"] = s["burden50_post"] - s["burden50_pre"]
    return pd.Series(s)


def main():
    os.makedirs(RES, exist_ok=True)
    w, h = load()
    rows = []
    for g, members in {**GROUPS, **{c: [c] for c in SINGLE}}.items():
        d = w if members is None else w[w.occ_class.isin(members)]
        r = d[(d.TEN == 3) & (d.rent > 0)]
        est = class_stats(d, r, "PWGTP")
        rep = pd.DataFrame([class_stats(d, r, c) for c in REPS])
        se = np.sqrt(4 / 80 * ((rep - est) ** 2).sum())
        row = {"occ_class": g, "n_workers_pre": int(d.YEAR.isin(PRE).sum()), "n_workers_post": int(d.YEAR.isin(POST).sum()),
               "n_renters_pre": int(r.YEAR.isin(PRE).sum()), "n_renters_post": int(r.YEAR.isin(POST).sum()), **est.to_dict()}
        for k in ["pay_growth", "burden30_change", "burden30_ratio", "burden50_change"]:
            row[f"se_{k}"] = se[k]
        row["z_burden30_change"] = est["burden30_change"] / se["burden30_change"]
        for y in YEARS:
            row[f"pay_{y}"] = wq(d[d.YEAR == y].wage, d[d.YEAR == y].PWGTP)
            row[f"burden30_{y}"] = np.average(r[r.YEAR == y].GRPIP >= 30, weights=r[r.YEAR == y].PWGTP)
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(f"{RES}/pay_rent_by_class.csv", index=False)

    # Region by year: all cash-rent households, and those who moved in within 12 months (MV == 1)
    rr = h[(h.TEN == 3) & (h.rent > 0)]
    reg = []
    for y in YEARS:
        a = rr[rr.YEAR == y]
        m = a[a.MV == 1]
        ft = w[w.YEAR == y]
        reg.append({"year": y, "median_ft_pay": wq(ft.wage, ft.PWGTP),
                    "median_gross_rent_all_renters": wq(a.rent, a.WGTP),
                    "median_gross_rent_moved_in_past_year": wq(m.rent, m.WGTP),
                    "median_renter_household_income": wq(a.hinc, a.WGTP),
                    "renter_households_burden30": np.average(a.GRPIP >= 30, weights=a.WGTP),
                    "renter_households_burden50": np.average(a.GRPIP >= 50, weights=a.WGTP),
                    "n_renter_households": len(a), "n_recent_movers": len(m), "n_ft_workers": len(ft)})
    reg = pd.DataFrame(reg)
    reg.to_csv(f"{RES}/region_by_year.csv", index=False)

    pd.set_option("display.width", 220)
    show = out.set_index("occ_class")[["n_renters_pre", "n_renters_post", "pay_pre", "pay_post", "pay_growth",
                                       "burden30_pre", "burden30_post", "burden30_change", "se_burden30_change",
                                       "z_burden30_change", "burden50_pre", "burden50_post"]]
    print(show.round(3).to_string())
    print(reg.round(3).to_string(index=False))
    r2 = reg.set_index("year")
    for c in reg.columns[1:5]:
        print(f"{c}: 2018-19 -> 2023-24 {r2.loc[POST, c].mean() / r2.loc[PRE, c].mean() - 1:+.1%}")


if __name__ == "__main__":
    main()
