"""Shared paths/constants for E2 (turnover re-entry price model)."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DB = os.path.join(ROOT, "analysis/cache/zillow.duckdb")   # built by analysis/common/build_zillow.py
OUT = os.path.join(HERE, "outputs")
FIG = os.path.join(HERE, "figs")
EXT = os.path.join(HERE, "external")
SAMPLE = os.path.join(OUT, "sample.parquet")
SEED = 42

# Temporal split on the date the unit is re-listed (next_start)
TRAIN_END = "2025-07-01"
VAL_END = "2026-01-01"

# Approximate CPI-U San Francisco-Oakland-Hayward, annual % change (BLS; rounded, approximate).
# AB 1482 cap = min(5% + CPI, 10%). Pre-2020 the law did not exist; we apply the same rule as a counterfactual.
CPI = {2012: 2.7, 2013: 2.2, 2014: 2.8, 2015: 2.6, 2016: 3.0, 2017: 3.2, 2018: 3.9, 2019: 3.0, 2020: 1.7,
       2021: 3.2, 2022: 5.2, 2023: 3.9, 2024: 2.6, 2025: 2.6, 2026: 2.6}
def ab1482_cap(year):
    return min(0.05 + CPI.get(int(year), 2.6) / 100, 0.10)

CAP = 0.10  # classification threshold: annualized jump above AB 1482's absolute maximum
