"""Block-level LODES OD -> county x county flows, with duckdb (streams the gz CSV, no pandas load).
Output: outputs/county_flows.csv  (year, jt, part, h_cty, w_cty, S000..SI03)
part = 'main' (CA home, CA work) or 'aux' (out-of-state home, CA work; h_cty = 2-digit state FIPS + '000')."""
import os, glob, re, duckdb, pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, OUT = os.path.join(HERE, "raw"), os.path.join(HERE, "outputs")
COLS = ["S000","SA01","SA02","SA03","SE01","SE02","SE03","SI01","SI02","SI03"]

def main():
    con = duckdb.connect()
    frames = []
    files = sorted(glob.glob(os.path.join(RAW, "ca_od_*_JT0*_*.csv.gz")))
    for f in files:
        m = re.search(r"ca_od_(main|aux)_(JT0\d)_(\d{4})\.csv\.gz$", f)
        part, jt, yr = m.group(1), m.group(2), int(m.group(3))
        sums = ", ".join(f"SUM({c})::BIGINT AS {c}" for c in COLS)
        hexpr = "substr(h_geocode,1,5)" if part == "main" else "substr(h_geocode,1,2) || '000'"
        q = f"""SELECT {hexpr} AS h_cty, substr(w_geocode,1,5) AS w_cty, {sums}
                FROM read_csv(?, header=true, compression='gzip',
                    types={{'w_geocode':'VARCHAR','h_geocode':'VARCHAR'}})
                GROUP BY 1,2"""
        df = con.execute(q, [f]).df()
        df.insert(0, "part", part); df.insert(0, "jt", jt); df.insert(0, "year", yr)
        frames.append(df); print(f"aggregated {os.path.basename(f)}: {df.S000.sum():,} jobs")
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(os.path.join(OUT, "county_flows.csv"), index=False)

if __name__ == "__main__":
    main()
