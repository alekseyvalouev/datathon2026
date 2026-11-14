"""E9 single entry point: download ACS PUMS (2022-2024 1-year, US person+housing), build, estimate, model, plot, verify.

Usage:  python3 -I run_all.py            (set E9_YEARS=2022,2023,2024 to change years; 2022+ share 2020 PUMAs)
Requires: pandas, pyarrow, duckdb, scikit-learn, matplotlib, xlrd (python3 -m pip install xlrd).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ["01_download_extract.py", "02_build.py", "03_estimate.py", "04_exit_model.py", "05_figures.py",
         "06_verify.py"]

if __name__ == "__main__":
    for s in STEPS:
        print(f"=== {s}", flush=True)
        subprocess.run([sys.executable, "-I", os.path.join(HERE, "src", s)], check=True, cwd=HERE)
