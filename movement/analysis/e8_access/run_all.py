"""E8 entry point: where can a displaced low-income household re-rent inside the Bay, and what access do they give up?
Inputs (raw): Google Maps places CSV (+ reviews CSV), analysis/cache/zillow.duckdb (built from the raw Zillow CSVs by
analysis/common/build_zillow.py; opened read-only), E6's parsed HCD income limits (analysis/e6_unit_replacement/
outputs/income_limits_bay.csv; rebuild with analysis/e6_unit_replacement/run_all.py), E2's UDP typology + TIGER tract
files (analysis/e2_turnover_model/external/, downloaded by analysis/e2_turnover_model/run_all.py) and E2's
zip_reentry_cost.csv. Usage: python3 analysis/e8_access/run_all.py  (~4 min; log -> outputs/run_all.log)"""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import OUT, ensure_dirs

if __name__ == "__main__":
    ensure_dirs()
    with open(os.path.join(OUT, "run_all.log"), "w") as log:
        for s in ["s01_places.py", "s02_access.py", "s03_compare.py", "s04_model.py"]:
            print(f"===== {s}", flush=True); log.write(f"\n===== {s}\n"); log.flush()
            r = subprocess.run([sys.executable, "-W", "ignore", os.path.join(HERE, s)], cwd=HERE, capture_output=True, text=True)
            log.write(r.stdout + r.stderr); log.flush(); print(r.stdout[-3000:])
            if r.returncode: print(r.stderr[-3000:]); sys.exit(f"{s} failed")
