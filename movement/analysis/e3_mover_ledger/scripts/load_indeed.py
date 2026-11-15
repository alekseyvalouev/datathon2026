"""Reproducible loader: raw Indeed CSV -> DuckDB table `i` (all varchar).
Builds the shared cache analysis/cache/indeed.duckdb (also read by E7) with --rebuild, or automatically the first
time it is needed. A private copy at e3_mover_ledger/cache_indeed.duckdb, if present, takes precedence.
"""
import os, sys, duckdb
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DATA_DIR = os.environ.get("DATATHON_DATA") or os.path.join(os.path.dirname(ROOT), "data")   # see scripts/setup_data.sh
RAW_CSV = os.path.join(DATA_DIR, "indeed_job_listings.csv")
SHARED = os.path.join(ROOT, "analysis", "cache", "indeed.duckdb")
PRIVATE = os.path.join(HERE, "..", "cache_indeed.duckdb")
COLS = "jobid, company_name, date_posted_parsed, job_title, description_text, job_type, location, salary_formatted, job_location"


def build(path=SHARED):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = duckdb.connect(path)
    con.execute(f"""create or replace table i as select * from read_csv('{RAW_CSV}', header=true, all_varchar=true,
        max_line_size=30000000, ignore_errors=true, parallel=false)""")
    print("rows:", con.execute("select count(*) from i").fetchone()[0])
    con.close()


def load_df():
    path = PRIVATE if os.path.exists(PRIVATE) else SHARED
    if not os.path.exists(path):
        build(SHARED)
    con = duckdb.connect(path, read_only=True)
    df = con.execute(f"select {COLS} from i").df()
    con.close()
    return df


if __name__ == "__main__":
    if "--rebuild" in sys.argv:
        build()
    print(load_df().shape)
