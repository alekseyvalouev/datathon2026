#!/usr/bin/env bash
# E5 pipeline: download gross-migration files -> analyze -> figures -> hand check
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p raw outputs figs
./scripts/download.sh
python3 -I scripts/analyze.py ../e1_composition/raw raw outputs
python3 -I scripts/acs.py raw/acs outputs > /dev/null
python3 -I scripts/figures.py outputs figs
./scripts/verify_by_hand.sh | tee outputs/verify_by_hand.txt
