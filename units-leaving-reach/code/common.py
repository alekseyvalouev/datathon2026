"""Shared paths and constants for the units-leaving-reach workstream.

Upstream inputs, all inside this repo (paths relative to the repo root):
  movement/analysis/cache/zillow.duckdb                             raw Zillow events (movement/analysis/common/build_zillow.py)
  movement/analysis/e2_turnover_model/outputs/sample.parquet        same-unit turnover pairs + tract join (movement E2, s01)
  movement/analysis/e6_unit_replacement/outputs/income_limits_bay.csv  CA HCD income limits 2022-26 (movement E6, s01)
  displacement-early-warning/results/e5_tract_table.csv             2018 census + pre-2019 Zillow tract features (committed)
  displacement-early-warning/results/e2_predictions.csv             backtest risk score per tract (committed)
  ai-labor-distribution/results/asset_city_jobs_housing.csv         city job mix from Indeed postings (committed)
The first three are rebuilt from raw data by the movement workstream (see the repo README); the last three are
committed result tables of the other workstreams.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)                                  # datathon2026/units-leaving-reach
ROOT = os.path.dirname(WS)                                  # repo root (datathon2026/)
MOVE = os.path.join(ROOT, "movement", "analysis")
E2_SAMPLE = os.path.join(MOVE, "e2_turnover_model/outputs/sample.parquet")
LIMITS = os.path.join(MOVE, "e6_unit_replacement/outputs/income_limits_bay.csv")
DB = os.path.join(MOVE, "cache/zillow.duckdb")
DEW = os.path.join(ROOT, "displacement-early-warning/results")
AIL = os.path.join(ROOT, "ai-labor-distribution/results")
RES = os.path.join(WS, "results"); FIG = os.path.join(WS, "figs")
DATA = os.path.join(RES, "pairs.parquet")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)
SEED = 42
TRAIN_END, VAL_END = "2025-07-01", "2026-01-01"   # temporal split on re-listing date, same as movement E2
MULT = 3.0        # income-to-rent screening rule: monthly rent x 12 x 3 <= household income
