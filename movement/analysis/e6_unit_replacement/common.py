"""Shared paths/constants for E6 (what replaces the leaver: unit + household)."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DB = os.path.join(ROOT, "analysis/cache/zillow.duckdb")
E2_SAMPLE = os.path.join(ROOT, "analysis/e2_turnover_model/outputs/sample.parquet")
OUT = os.path.join(HERE, "outputs"); FIG = os.path.join(HERE, "figs")
RAW = os.path.join(HERE, "raw"); CACHE = os.path.join(HERE, "cache")
SEED = 42
BAY = {"001": "Alameda County", "013": "Contra Costa County", "041": "Marin County", "055": "Napa County",
       "075": "San Francisco County", "081": "San Mateo County", "085": "Santa Clara County",
       "095": "Solano County", "097": "Sonoma County"}
