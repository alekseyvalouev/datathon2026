"""E2 entry point. Runs everything from the cached DuckDB (analysis/cache/zillow.duckdb, opened read-only).
The cache is built from the raw Zillow CSVs by:  python3 analysis/common/build_zillow.py
External (optional) inputs in external/: Urban Displacement Project SF Bay typology CSV + 2018 TIGER CA tracts;
fetch_external() downloads them if missing (the typology join is skipped if unavailable).
Usage:  python3 analysis/e2_turnover_model/run_all.py"""
import os, sys, subprocess, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import EXT, OUT, FIG

URLS = {"SanFrancisco_typology_output.csv": "https://raw.githubusercontent.com/urban-displacement/displacement-typologies/main/data/outputs/typologies/SanFrancisco_typology_output.csv",
        "tl_2018_06_tract.zip": "https://www2.census.gov/geo/tiger/TIGER2018/TRACT/tl_2018_06_tract.zip"}

def fetch_external():
    os.makedirs(EXT, exist_ok=True)
    for f, u in URLS.items():
        p = os.path.join(EXT, f)
        if not os.path.exists(p):
            try: urllib.request.urlretrieve(u, p); print("downloaded", f)
            except Exception as e: print("could not download", f, e)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True); os.makedirs(FIG, exist_ok=True)
    fetch_external()
    for s in ["s01_build_sample.py", "s02_hand_check.py", "s03_model.py"]:
        print(f"\n===== {s}"); subprocess.run([sys.executable, os.path.join(HERE, s)], check=True, cwd=HERE)
