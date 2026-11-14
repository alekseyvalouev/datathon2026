#!/usr/bin/env bash
# Download IRS SOI county migration files (inflow/outflow) + users guides into raw/
set -u
cd "$(dirname "$0")/../raw"
for y in 1112 1213 1314 1415 1516 1617 1718 1819 1920 2021 2122 2223; do
  for d in inflow outflow; do
    f=county${d}${y}.csv
    [ -s "$f" ] || curl -sSfL --retry 3 -o "$f" "https://www.irs.gov/pub/irs-soi/$f" || echo "FAILED $f"
  done
  g=${y}inpublicmigdoc.pdf
  [ -s "$g" ] || curl -sSfL --retry 2 -o "$g" "https://www.irs.gov/pub/irs-soi/$g" || echo "FAILED $g"
done
ls -la
