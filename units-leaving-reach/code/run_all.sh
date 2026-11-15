#!/usr/bin/env bash
# units-leaving-reach: raw data -> every reported number. ~2 minutes after the upstream steps exist.
# Upstream (run once, each from raw data; see their READMEs):
#   python3 analysis/common/build_zillow.py                 # raw Zillow CSVs -> analysis/cache/zillow.duckdb
#   python3 analysis/e2_turnover_model/run_all.py           # same-unit turnover pairs + UDP tract join
#   python3 analysis/e6_unit_replacement/run_all.py         # CA HCD income limits 2022-2026
#   bash datathon2026/displacement-early-warning/code/run_all.sh   # tract features + backtest risk score
#   ai-labor-distribution/code (asset_t3.py)                # city job mix from Indeed postings
set -euo pipefail
cd "$(dirname "$0")"
UP=../../..
for f in analysis/e2_turnover_model/outputs/sample.parquet analysis/e6_unit_replacement/outputs/income_limits_bay.csv \
         datathon2026/displacement-early-warning/results/e5_tract_table.csv \
         datathon2026/displacement-early-warning/results/e2_predictions.csv \
         datathon2026/ai-labor-distribution/results/asset_city_jobs_housing.csv; do
  [ -f "$UP/$f" ] || { echo "missing upstream input: $f (see header of this script)"; exit 1; }
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
