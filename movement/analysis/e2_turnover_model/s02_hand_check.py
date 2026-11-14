"""Step 2: hand-check 30 random sampled pairs against the raw Zillow priceHistory JSON.
An independent Python re-parse of the raw JSON is compared with the SQL-built pair, and semantic red flags are
listed. Raw histories are written to outputs/hand_check_raw.txt (dates/events/prices only; no addresses) for
manual reading; the verdict table is outputs/hand_check.csv."""
import duckdb, json, pandas as pd, numpy as np, os
from common import *

def reparse(ph):
    ev = sorted(json.loads(ph), key=lambda e: (e.get("date"), 0 if e.get("event") == "Listed for rent" else 1))
    rent = [e for e in ev if e.get("postingIsRental")]
    eps, cur = [], None
    for e in rent:
        if e["event"] == "Listed for rent":
            cur = {"start": e["date"], "first": e.get("price"), "last": None, "events": []}; eps.append(cur)
        if cur is not None:
            cur["events"].append(e)
            if e.get("price") is not None and e["event"] != "Listing removed": cur["last"] = e.get("price")
    return ev, eps

# Notes from manually reading outputs/hand_check_raw.txt (seed 42 sample). Keys are zpids.
MANUAL = {
 "2053541568": ("questionable", "SF APARTMENT zpid: $4650 listed 2 days in 2024, $3150 in 2026; likely a different unit/floor plan or concession reusing the zpid"),
 "2085139243": ("correct", "SF $4830 (2019) -> $2995 (Nov 2020): real COVID-era SF rent collapse; same unit relisted at $5700 in 2026"),
 "2078329446": ("correct-with-caveat", "revenue-managed complex: next_first $3306 re-priced to $3631 two days later; first ask is noisy"),
 "2070938950": ("correct-with-caveat", "daily algorithmic price changes in next episode (n_changes>15); first ask then drifts down ~4%"),
 "2079225480": ("correct-with-caveat", "daily algorithmic re-pricing in both episodes"),
 "24774183": ("correct-with-caveat", "orphan 'Listing removed' (no price) on 2021-03-24 extends end_d; target unaffected, gap_y wrong"),
 "118259306": ("correct-with-caveat", "orphan 'Listing removed' 2021-02-16 extends end_d; target unaffected"),
 "15856224": ("correct", "orphan 2021-03-21 removal after pair window; does not affect this pair"),
 "24811992": ("correct", "flat $4500 over 2.3y; orphan 2021-03-24 removal after pair"),
 "243210774": ("correct-with-caveat", "prior episode has no removal; unit sold 2026-07 then relisted (new owner) -> turnover coincides with sale"),
 "18281200": ("correct", "prior episode cut $3345 -> $2925 before removal; last_p correctly takes the final ask; 4.6y gap"),
 "19580875": ("correct-with-caveat", "luxury SFH $12250 -> $13000 ask, but next episode then cut to $9995: first ask overstates the re-let rent"),
 "18451872": ("correct", "APARTMENT homeType but has individual sale history -> a real condo-like unit, not a floor plan"),
 "24821200": ("correct", "APARTMENT homeType with own sale history (single unit)"),
 "111710903": ("correct", "SF condo $4600 cut to $4200 (2018) -> $4495 (2019); the following pair shows the COVID dip to $3300"),
}

def main():
    s = pd.read_parquet(SAMPLE)
    rng = np.random.default_rng(SEED)
    pick = pd.concat([s[s.homeType == "APARTMENT"].sample(15, random_state=SEED),
                      s[s.homeType != "APARTMENT"].sample(15, random_state=SEED)])
    con = duckdb.connect(DB, read_only=True)
    rows, txt = [], []
    for _, p in pick.iterrows():
        ph = con.execute("select priceHistory from z where zpid=? limit 1", [p.zpid]).fetchone()[0]
        ev, eps = reparse(ph)
        k = int(p.ep) - 1
        a, b = eps[k], eps[k + 1]
        match = (a["start"] == p.start_d and b["start"] == p.next_start and a["last"] == p.last_p and b["first"] == p.next_first)
        flags = []
        sale = [e for e in ev if not e.get("postingIsRental") and e.get("event") == "Sold" and a["start"] < e["date"] < b["start"]]
        if sale: flags.append("sold between tenancies (new owner)")
        removed = any(e["event"] == "Listing removed" for e in a["events"])
        if not removed: flags.append("no 'Listing removed' in prior episode (rent-up not confirmed)")
        after_rm = False; seen_rm = False
        for e in a["events"]:
            if e["event"] == "Listing removed": seen_rm = True
            elif seen_rm and e["event"] == "Price change": after_rm = True
        if after_rm: flags.append("price change after removal inside same episode")
        dur = (pd.Timestamp(a["events"][-1]["date"]) - pd.Timestamp(a["start"])).days
        if dur > 180: flags.append(f"prior episode spans {dur}d")
        if p.ratio > 1.5 or p.ratio < 0.7: flags.append(f"extreme ratio {p.ratio:.2f}")
        if not match: verdict = "incorrect"
        elif any(f.startswith(("price change after", "prior episode spans", "extreme")) for f in flags): verdict = "correct-with-caveat"
        else: verdict = "correct"
        rows.append(dict(zpid=p.zpid, homeType=p.homeType, county=p.county, ep=int(p.ep), n_rental_episodes=len(eps),
                         prev_start=p.start_d, prev_last_p=p.last_p, next_start=p.next_start, next_first=p.next_first,
                         gap_y=round(p.start_gap_y, 2), r=round(p.r, 3), sql_matches_reparse=match, flags="; ".join(flags), verdict=verdict))
        txt.append(f"=== zpid {p.zpid} {p.homeType} {p.county} | pair ep{int(p.ep)}->{int(p.ep)+1}: "
                   f"{p.start_d} last_p={p.last_p:.0f} -> {p.next_start} next_first={p.next_first:.0f} r={p.r:.3f}")
        for e in ev:
            txt.append(f"   {e['date']}  {'R' if e.get('postingIsRental') else 'S'}  {e.get('event'):<16} {e.get('price')}")
    con.close()
    out = pd.DataFrame(rows)
    out["manual_note"] = out.zpid.map(lambda z: MANUAL.get(z, ("", ""))[1])
    out["verdict"] = [MANUAL[z][0] if z in MANUAL else v for z, v in zip(out.zpid, out.verdict)]
    out.to_csv(os.path.join(OUT, "hand_check.csv"), index=False)
    open(os.path.join(OUT, "hand_check_raw.txt"), "w").write("\n".join(txt))
    print(out[["zpid", "homeType", "prev_last_p", "next_first", "gap_y", "sql_matches_reparse", "verdict", "flags"]].to_string(index=False))
    print(out.verdict.value_counts())

if __name__ == "__main__":
    main()
