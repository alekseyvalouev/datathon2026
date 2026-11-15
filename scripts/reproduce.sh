#!/usr/bin/env bash
# Rebuild results from raw data. Run from anywhere; data must be set up first (bash scripts/setup_data.sh <downloads>).
#
#   bash scripts/reproduce.sh            model chain: Zillow cache -> movement E2, E6 -> units-leaving-reach (~10 min)
#   bash scripts/reproduce.sh movement   every movement experiment E1-E10 (downloads public data; E4 needs
#                                        sentence-transformers; roughly an hour)
#   bash scripts/reproduce.sh all        movement, then units-leaving-reach
#
# The other workstreams have their own entry points; see the README (Reproducing).
set -euo pipefail
# Single-threaded linear algebra: multithreaded BLAS changes logistic-regression results in the 5th decimal
# from run to run. With this, reruns reproduce every table byte for byte.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DATA="${DATATHON_DATA:-$REPO/data}"
M="$REPO/movement/analysis"
WHAT="${1:-model}"

for f in zillow/Zillow_part1.csv zillow/zillow_part2.csv zillow/zillow_part3.csv; do
  [ -e "$DATA/$f" ] || { echo "missing $DATA/$f: run  bash scripts/setup_data.sh <folder with the datathon downloads>"; exit 1; }
done

step () { echo; echo "==== $1"; }
zillow_cache () {
  if [ -f "$M/cache/zillow.duckdb" ]; then echo "(Zillow cache exists; delete $M/cache/zillow.duckdb to rebuild)"
  else step "movement: raw Zillow CSVs -> cache"; python3 "$M/common/build_zillow.py"; fi
}
movement_all () {
  zillow_cache
  step "movement E1 composition";        bash "$M/e1_composition/run.sh"
  step "movement E5 replacers";          bash "$M/e5_replacers_irs/run.sh"
  step "movement E2 turnover model";     python3 "$M/e2_turnover_model/run_all.py"
  python3 "$M/e2_turnover_model/run_robustness.py"
  step "movement E3 mover ledger";       python3 -I "$M/e3_mover_ledger/run_all.py"
  step "movement E4 exit classifier";    python3 "$M/e4_exit_classifier/run_all.py"
  step "movement E6 unit replacement";   python3 "$M/e6_unit_replacement/run_all.py"
  step "movement E7 pulled in";          python3 "$M/e7_pulled_in/run_all.py"
  step "movement E8 access";             python3 "$M/e8_access/run_all.py"
  step "movement E9 PUMS movers";        python3 "$M/e9_pums_movers/run_all.py"
  step "movement E10 supercommute";      python3 "$M/e10_supercommute/run_all.py"
}
model_inputs () {
  zillow_cache
  step "movement E2 turnover pairs";     python3 "$M/e2_turnover_model/run_all.py"
  step "movement E6 income limits";      python3 "$M/e6_unit_replacement/run_all.py"
}
model () { step "units-leaving-reach"; bash "$REPO/units-leaving-reach/code/run_all.sh"; }

case "$WHAT" in
  model)    model_inputs; model ;;
  movement) movement_all ;;
  all)      movement_all; model ;;
  *) echo "usage: bash scripts/reproduce.sh [model|movement|all]"; exit 1 ;;
esac
echo; echo "done ($WHAT). Compare with the committed tables:  git status --short -- '*.csv' '*.json'"
