#!/usr/bin/env bash
# Downloads IRS SOI state gross-migration files (age x AGI class) into raw/. County files are read from ../e1_composition/raw.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p raw
for y in 1112 1213 1314 1415 1516 1617 1718 1819 1920 2021 2122 2223; do
  [ -s raw/${y}inmigall.csv ] || curl -sSf -A "Mozilla/5.0" -o raw/${y}inmigall.csv "https://www.irs.gov/pub/irs-soi/${y}inmigall.csv"
done
# ACS 2018-2022 5-year table-based summary file (keyless bulk download), Bay county rows only
mkdir -p raw/acs
B="https://www2.census.gov/programs-surveys/acs/summary_file/2022/table-based-SF/data/5YRData"
for t in b07010 b07013; do
  if [ ! -s raw/acs/bay_$t.dat ]; then
    curl -sSf "$B/acsdt5y2022-$t.dat" | awk -F'|' 'NR==1 || $1 ~ /^0500000US060(01|13|41|55|75|81|85|95|97)$/' > raw/acs/bay_$t.dat
  fi
done
