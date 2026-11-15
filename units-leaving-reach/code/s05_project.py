"""Step 5: data for the map page. Observed status 2022-2026 per unit, and model projections 2027-2031.

Observed: a unit (zpid in the s01 population) counts as priced out in year Y if its latest observed re-listing left
80% AMI reach (y = 1) and happened in or before Y. Units whose latest re-listing stayed in reach form the stock
that is projected forward.

Projection: refit the main LightGBM (s03 settings) on ALL 12,011 observed pairs (deployment model; test-set
evaluation stays in s03). For each in-reach unit and each year Y = 2027..2031, build the pair "previous tenancy =
the unit's latest observed listing, re-listed on 1 July Y" and score P(leaves reach | it turns over in Y).
Assumptions, all shown on the page:
  - income limits grow at each county's 2022-26 average rate, capped at 6%/yr;
  - county rent index either frozen at its last observed quarter, or continuing its trailing 1-year trend;
  - unit, tract and city features unchanged; no sale between tenancies.
The page combines these with an annual turnover rate h: P(out of reach by Y) = 1 - prod_t (1 - h * p_t).
Writes results/viz/units.json and results/s05_projection_summary.csv."""
import os, sys, json, numpy as np, pandas as pd, duckdb
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modlib import *

YEARS = list(range(2027, 2032))
VIZ = os.path.join(RES, "viz"); os.makedirs(VIZ, exist_ok=True)

def market_index():
    """Copy of movement E2 s01_build_sample.market_index (same cell-mean cut-off), so projected market features are
    built exactly like the training features: county x quarter median of log first ask net of (ZIP, beds, apartment)
    cell means estimated before 2025-07."""
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
    return idx[idx["size"] >= 20]["median"]

def extend_index(idx, scenario, until=pd.Period("2031Q4", "Q")):
    d = idx.to_dict(); out = dict(d)
    for c in idx.index.get_level_values(0).unique():
        qs = sorted(q for (cc, q) in d if cc == c); last = qs[-1]
        prev = next((d.get((c, last - k)) for k in range(4, 8) if (c, last - k) in d), d[(c, last)])
        mom = d[(c, last)] - prev
        q = last + 1
        while q <= until:
            out[(c, q)] = d[(c, last)] + (mom * (q - last).n / 4 if scenario == "trend" else 0.0)
            q += 1
    return out

def get(d, c, q):
    for k in range(4):
        v = d.get((c, q - k))
        if v is not None: return v
    return np.nan

def main():
    df, hist = load()
    cfg = json.load(open(os.path.join(RES, "s03_config.json")))
    p, n = cfg["lgb_params"]["+ tract + city jobs (all workstreams)"]

    # ---- deployment model on all observed pairs
    fit_e, _ = add_encodings(df, [], hist, "2100-01-01")
    model = fit_lgb(fit_e[ALL], fit_e.y, p, n)

    # ---- unit table: latest observed re-listing per unit
    df["year"] = pd.to_datetime(df.next_start).dt.year
    last = df.sort_values(["next_start", "ep"]).groupby("zpid").tail(1).copy()
    stock = last[last.y == 0].copy()

    # ---- projected pairs
    il = pd.read_csv(LIMITS)
    g = {}
    for lev in ["LI", "MED"]:
        w = il[il.level == lev].set_index("county")
        for c in w.index.unique():
            a, b = w[w.year == 2022].loc[c], w[w.year == 2026].loc[c]
            for k in range(1, 9):
                g[(lev, c, k)] = (b[f"p{k}"], min((b[f"p{k}"] / a[f"p{k}"]) ** 0.25 - 1, 0.06))
    idx = market_index()
    base = stock.assign(start_d=stock.next_start, last_p=stock.next_last, first_p=stock.next_first,
                        n_changes=stock.next_n_changes, ep=stock.ep + 1, sold_between=0)
    sd = pd.to_datetime(base.start_d)
    base["prev_year"] = sd.dt.year + sd.dt.dayofyear / 366
    base["prev_cut"] = np.log(base.last_p / base.first_p)
    base["log_last_p"] = np.log(base.last_p)
    base["ppsf"] = np.where(base.sqft > 100, base.last_p / base.sqft, np.nan)
    base["age"] = np.where(base.yearBuilt > 1800, sd.dt.year - base.yearBuilt, np.nan)
    q0 = pd.PeriodIndex(sd, freq="Q")
    probs = {}
    for scen in ["frozen", "trend"]:
        ext = extend_index(idx, scen)
        for Y in YEARS:
            d = base.copy()
            ns = pd.Timestamp(f"{Y}-07-01")
            d["next_start"] = str(ns.date()); d["next_month"] = 7
            d["start_gap_y"] = (ns - sd).dt.days / 365.25
            for lev, col in (("LI", "LIy"), ("MED", "MEDy")):
                d[col] = [g[(lev, c, h)][0] * (1 + g[(lev, c, h)][1]) ** (Y - 2026) for c, h in zip(d.county, d.hh)]
            d["thr"] = d.LIy / (12 * MULT)
            d["headroom"] = np.log(d.thr / d.last_p)
            d["req_growth"] = (d.thr / d.last_p) ** (1 / d.start_gap_y) - 1
            d["ami_share0"] = 12 * MULT * d.last_p / d.MEDy
            q1 = pd.Period(ns, "Q") - 1
            a = np.array([get(ext, c, q) for c, q in zip(d.county, q0)])
            b = np.array([get(ext, c, q1) for c in d.county])
            b4 = np.array([get(ext, c, q1 - 4) for c in d.county])
            d["mkt_chg"] = (b - a) / d.start_gap_y; d["mkt_lvl0"] = a; d["mkt_mom"] = b - b4
            d = static_features(d)
            _, (d_e,) = add_encodings(df, [d], hist, "2100-01-01")
            probs[(scen, Y)] = model.predict_proba(d_e[ALL])[:, 1]
            probs[(scen, Y, "thr")] = d.thr.values

    # ---- summary for the write-up
    rows = []
    for scen in ["frozen", "trend"]:
        for Y in YEARS:
            pp = probs[(scen, Y)]
            rows.append(dict(scenario=scen, year=Y, mean_p_if_turnover=pp.mean(),
                             share_p_over_50=(pp > 0.5).mean(), median_line=np.median(probs[(scen, Y, "thr")])))
    s = pd.DataFrame(rows); s.round(4).to_csv(os.path.join(RES, "s05_projection_summary.csv"), index=False)
    print(s.round(3).to_string(index=False))
    print("observed 2026 leave rate:", df[df.year == 2026].y.mean().round(3),
          "| in-sample mean prediction 2026:", model.predict_proba(fit_e[ALL])[:, 1][df.year.values == 2026].mean().round(3))

    # ---- page payload: cells of ~110 m (lat/lon rounded to 3 decimals) so no single listing is pinpointed
    last["cell_lat"] = last.lat.round(3); last["cell_lon"] = last.lon.round(3)
    last["lost_year"] = np.where(last.y == 1, last.year, 0)
    pr = {k: v for k, v in probs.items() if len(k) == 2}
    pos = {z: i for i, z in enumerate(stock.zpid)}
    units = []
    for r in last.itertuples():
        u = [round(r.cell_lon, 3), round(r.cell_lat, 3), r.county.replace(" County", ""), int(r.beds),
             int(round(r.next_last)), int(r.lost_year), int(r.year)]
        if r.y == 0:
            i = pos[r.zpid]
            u.append([[round(float(pr[(s_, Y)][i]), 3) for Y in YEARS] for s_ in ("frozen", "trend")])
        units.append(u)
    lines = {c.replace(" County", ""): {str(Y): {str(h): round(g[("LI", c, h)][0] * (1 + g[("LI", c, h)][1]) ** (Y - 2026) / 36)
                                                  for h in range(1, 6)} for Y in [2026] + YEARS} for c in COUNTIES}
    obs_by_year = df.groupby("year").agg(relistings=("y", "size"), left_reach=("y", "sum")).reset_index().to_dict("records")
    meta = dict(years_obs=[2022, 2023, 2024, 2025, 2026], years_proj=YEARS, n_units=len(last), n_stock=len(stock), n_pairs=len(df),
                lines=lines, obs_by_year=obs_by_year,
                fields=["lon", "lat", "county", "beds", "latest_rent", "lost_year", "latest_relist_year", "p[scenario][year]"])
    json.dump(dict(meta=meta, units=units), open(os.path.join(VIZ, "units.json"), "w"), separators=(",", ":"))

    # ---- per-unit table for the neighbourhood roll-up (s09): exact coordinates stay local, never go on the page
    ut = last[["zpid", "county", "city", "zipcode", "tract", "lat", "lon", "beds", "homeType", "next_last", "thr", "y", "year"]].copy()
    for si, s_ in enumerate(("frozen", "trend")):
        for Y in YEARS:
            ut[f"p_{s_}_{Y}"] = ut.zpid.map(dict(zip(stock.zpid, pr[(s_, Y)])))
            ut[f"thr_{Y}"] = ut.zpid.map(dict(zip(stock.zpid, probs[(s_, Y, "thr")])))
    ut.to_parquet(os.path.join(RES, "s05_unit_projections.parquet"), index=False)
    print("units", len(units), "stock", len(stock), "json KB", os.path.getsize(os.path.join(VIZ, "units.json")) // 1024)

if __name__ == "__main__":
    main()
