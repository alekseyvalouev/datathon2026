"""Step 2: hand-check sample. For 30 random pairs (seed 42, stratified 15 positive / 15 negative):
 (a) re-read the raw Zillow rental events from the cache and confirm last_p (last priced event of the previous
     tenancy), next_first (first ask at re-listing) and next_last (settled ask: last priced event of the re-listing
     episode, before the following re-listing);
 (b) re-look-up the HCD 80% AMI limit from the CSV by an independent path and recompute the label;
 (c) check the tract join is in the stated county (GEOID county FIPS vs county name).
Writes results/s02_hand_check.csv (machine checks) and results/s02_hand_check_raw.txt (event histories, no addresses)
for a human to read; verdicts are recorded in memos/hand_check.md."""
import os, sys, duckdb, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

FIPS = {"001": "Alameda County", "013": "Contra Costa County", "041": "Marin County", "055": "Napa County",
        "075": "San Francisco County", "081": "San Mateo County", "085": "Santa Clara County",
        "095": "Solano County", "097": "Sonoma County"}

def main():
    df = pd.read_parquet(DATA)
    s = pd.concat([df[df.y == 1].sample(15, random_state=SEED), df[df.y == 0].sample(15, random_state=SEED)])
    il = pd.read_csv(LIMITS).set_index(["year", "county", "level"])
    con = duckdb.connect(DB, read_only=True)
    rows, raw = [], []
    for r in s.itertuples():
        ev = con.execute("select d, event, p from ev where zpid=? and rental order by d", [str(r.zpid)]).df()
        prev = ev[(ev.d >= r.start_d) & (ev.d <= r.end_d) & ev.p.notna() & (ev.event != "Listing removed")]
        nxt = ev[(ev.d == r.next_start) & (ev.event == "Listed for rent")]
        raw_last = prev.p.iloc[-1] if len(prev) else np.nan
        raw_next = nxt.p.iloc[0] if len(nxt) else np.nan
        later = ev[(ev.d > r.next_start) & (ev.event == "Listed for rent")]
        stop = later.d.iloc[0] if len(later) else "9999"
        ep2 = ev[(ev.d >= r.next_start) & (ev.d < stop) & ev.p.notna() & (ev.event != "Listing removed")]
        raw_settled = ep2.p.iloc[-1] if len(ep2) else np.nan
        d = pd.Timestamp(r.next_start); y = d.year if d.month >= 6 else d.year - 1
        hh = int(min(r.beds, 7) + 1)
        li = il.loc[(y, r.county, "LI"), f"p{hh}"]
        lab = int(raw_settled * 36 > li) if not np.isnan(raw_settled) else -1
        fips = str(r.tract).zfill(11)[2:5] if pd.notna(r.tract) else None
        rows.append(dict(zpid=r.zpid, county=r.county, homeType=r.homeType, beds=r.beds, start_d=r.start_d,
                         end_d=r.end_d, next_start=r.next_start, last_p=r.last_p, raw_last=raw_last,
                         next_first=r.next_first, raw_next=raw_next,
                         next_last=r.next_last, raw_settled=raw_settled, y_first=r.y_first, limit_year=y, hh=hh, LI=li, thr=round(li / 36),
                         y=r.y, y_recomputed=lab, last_ok=raw_last == r.last_p, next_ok=raw_next == r.next_first,
                         settled_ok=raw_settled == r.next_last,
                         label_ok=lab == r.y, tract_county_ok=(FIPS.get(fips) == r.county) if fips else None,
                         typology=r.udp_typ))
        raw.append(f"--- zpid {r.zpid} | {r.county} | {r.homeType} {r.beds:.0f}bd | pair {r.start_d}..{r.end_d} -> "
                   f"{r.next_start} | last_p {r.last_p:.0f} next_first {r.next_first:.0f} settled {r.next_last:.0f} | thr {li/36:.0f} | y={r.y}\n"
                   + ev[(ev.d >= str(pd.Timestamp(r.start_d) - pd.Timedelta(days=60))[:10])].to_string(index=False))
    con.close()
    out = pd.DataFrame(rows); out.to_csv(os.path.join(RES, "s02_hand_check.csv"), index=False)
    open(os.path.join(RES, "s02_hand_check_raw.txt"), "w").write("\n\n".join(raw))
    print(out[["last_ok", "next_ok", "settled_ok", "label_ok", "tract_county_ok"]].mean().round(3))
    print(out[~(out.last_ok & out.next_ok & out.settled_ok & out.label_ok)].to_string())
    # Whole-table join check
    fips = df.tract.dropna().astype(np.int64).astype(str).str.zfill(11).str[2:5].map(FIPS)
    print("tract county matches listing county:", (fips.values == df.loc[df.tract.notna(), "county"].values).mean().round(4))

if __name__ == "__main__":
    main()
