"""Independent re-count of one county pair from the raw block file using only gzip+csv (no duckdb),
compared with outputs/county_flows.csv. Writes outputs/hand_check.csv."""
import os, gzip, csv, sys
import pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, OUT = os.path.join(HERE, "raw"), os.path.join(HERE, "outputs")

def check(year, h, w):
    fn = os.path.join(RAW, f"ca_od_main_JT00_{year}.csv.gz")
    cols = ["S000", "SE01", "SE02", "SE03"]; tot = dict.fromkeys(cols, 0); nblk = 0
    with gzip.open(fn, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["h_geocode"].startswith(h) and r["w_geocode"].startswith(w):
                nblk += 1
                for c in cols: tot[c] += int(r[c])
    f = pd.read_csv(os.path.join(OUT, "county_flows.csv"), dtype={"h_cty": str, "w_cty": str})
    a = f[(f.year == year) & (f.jt == "JT00") & (f.part == "main") & (f.h_cty == h) & (f.w_cty == w)].iloc[0]
    rows = [dict(year=year, h_cty=h, w_cty=w, measure=c, raw_python_csv=tot[c], duckdb_pipeline=int(a[c]),
                 match=tot[c] == int(a[c]), n_block_pairs=nblk) for c in cols]
    return rows

if __name__ == "__main__":
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    rows = check(year, "06077", "06001")
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "hand_check.csv"), index=False)
    print(pd.DataFrame(rows).to_string(index=False))
