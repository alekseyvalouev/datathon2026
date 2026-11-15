#!/usr/bin/env bash
# units-leaving-reach: every reported number and the map page. About 2 minutes once its inputs exist.
# Inputs (see code/common.py): three tables rebuilt by the movement workstream, three committed result tables of
# displacement-early-warning and ai-labor-distribution. From the repo root, the movement steps are:
#   python3 movement/analysis/common/build_zillow.py         # raw Zillow CSVs -> movement/analysis/cache/zillow.duckdb
#   python3 movement/analysis/e2_turnover_model/run_all.py   # same-unit turnover pairs + UDP tract join
#   python3 movement/analysis/e6_unit_replacement/run_all.py # CA HCD income limits 2022-2026
# or simply: bash scripts/reproduce.sh
set -euo pipefail
# Single-threaded linear algebra: multithreaded BLAS changes logistic-regression results in the 5th decimal
# from run to run. With this, reruns reproduce every table byte for byte.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
cd "$(dirname "$0")"
REPO=../..
for f in movement/analysis/cache/zillow.duckdb \
         movement/analysis/e2_turnover_model/outputs/sample.parquet \
         movement/analysis/e6_unit_replacement/outputs/income_limits_bay.csv \
         displacement-early-warning/results/e5_tract_table.csv \
         displacement-early-warning/results/e2_predictions.csv \
         ai-labor-distribution/results/asset_city_jobs_housing.csv; do
  [ -f "$REPO/$f" ] || { echo "missing input: $f (see the header of this script)"; exit 1; }
done
python3 s01_build.py
python3 s02_hand_check.py
python3 s03_model.py
python3 s04_robustness.py
# Map page (site/out-of-reach-atlas.html): projections 2027-2031, county outlines, inline build
[ -f ../external/cb_2018_us_county_500k.zip ] || { mkdir -p ../external && curl -sSfL -o ../external/cb_2018_us_county_500k.zip https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_county_500k.zip; }
python3 s05_project.py
python3 -I s06_geo.py
python3 s07_build_page.py
