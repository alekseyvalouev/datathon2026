#!/usr/bin/env bash
# E1 pipeline: download -> analyze -> figures -> hand check
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p raw outputs figs
./scripts/download.sh > /dev/null
python3 -I scripts/analyze.py raw outputs
python3 -I scripts/figures.py outputs figs
./scripts/verify_by_hand.sh | tee outputs/verify_by_hand.txt
