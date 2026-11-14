#!/usr/bin/env bash
# Raw data -> reported results. Scripts live apart from data and run with `python3 -I`.
# Requirements: pandas numpy scipy scikit-learn shapely pyshp (geopandas only for the optional e4b cross-check).
# Inputs:  ZILLOW_RAW  folder with Zillow_part1.csv zillow_part2.csv zillow_part3.csv (read only)
#          UDP_REPO    clone of github.com/urban-displacement/displacement-typologies containing
#                      data/outputs/typologies, data/inputs/shp/SanFrancisco and data/downloads_for_public
# Outputs: $RESULTS (default <workstream>/results) and $RESULTS/logs
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$HERE")"
export UDP_REPO="${UDP_REPO:-$ROOT/data/udp}" ZILLOW_WORK="${ZILLOW_WORK:-$HOME/work}" RESULTS="${RESULTS:-$ROOT/results}"
ZILLOW_RAW="${ZILLOW_RAW:-$HOME/mnt/Downloads/datathon/zillow}"
LOGS="$RESULTS/logs"; mkdir -p "$LOGS" "$RESULTS" "$ZILLOW_WORK"
if [ ! -f "$UDP_REPO/data/outputs/typologies/SanFrancisco_typology_output.csv" ]; then
  git clone -q --filter=blob:none --sparse --depth 1 https://github.com/urban-displacement/displacement-typologies "$UDP_REPO"
  git -C "$UDP_REPO" sparse-checkout set data/outputs/typologies data/inputs/shp/SanFrancisco data/downloads_for_public
fi
if [ ! -f "$ZILLOW_WORK/slim_3.csv" ]; then   # about 60 s with the three files in parallel
  python3 -I "$HERE/e0_extract_zillow.py" "$ZILLOW_RAW/Zillow_part1.csv" 1 "$ZILLOW_WORK" &
  python3 -I "$HERE/e0_extract_zillow.py" "$ZILLOW_RAW/zillow_part2.csv" 2 "$ZILLOW_WORK" &
  python3 -I "$HERE/e0_extract_zillow.py" "$ZILLOW_RAW/zillow_part3.csv" 3 "$ZILLOW_WORK" &
  wait
fi
for s in e1_udp_landscape e2_backtest e2b_strict_label e3_backtest_fairness e4_zillow_tract_join e5_forward_test e6_forward_fairness \
         e7_flip_sensitivity e8_rent_turnover e9_price_trajectories e10_affordability; do
  echo "== $s"; python3 -I "$HERE/$s.py" > "$LOGS/${s%%_*}.log" 2>&1
done
python3 -I "$HERE/e4b_geometry_crosscheck.py" > "$LOGS/e4b.log" 2>&1 || echo "e4b skipped (needs geopandas)"
# optional: map shapes and the findings page (needs shapely + pyshp)
python3 -I "$HERE/map_geometry.py" > "$LOGS/map.log" 2>&1 && python3 "$ROOT/site/build.py" > "$LOGS/site.log" 2>&1 || echo "page not rebuilt"
echo done
