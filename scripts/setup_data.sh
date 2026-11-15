#!/usr/bin/env bash
# Link the datathon downloads into the layout every workstream expects. Nothing is copied and nothing is committed:
# data/ is in .gitignore.
#
# Usage: bash scripts/setup_data.sh <folder holding the downloads>
#
# The folder must contain the unzipped "[For Students] 8th Datathon For Social Good" pack (at any depth up to 3)
# and the large CSVs distributed separately (zillow_part2*.csv, indeed_job_listings*.csv, reddit_posts*.csv),
# with whatever numeric suffix the download gave them. Result (override the location with DATATHON_DATA):
#
#   data/
#     datathon_pack/              -> the unzipped pack (google maps, glassdoor, college, health, READMEs, ...)
#     zillow/Zillow_part1.csv     -> pack/zillow housing dataset/Zillow_part1.csv
#     zillow/zillow_part2.csv     -> zillow_part2*.csv
#     zillow/zillow_part3.csv     -> pack/zillow housing dataset/zillow_part3.csv
#     indeed_job_listings.csv     -> indeed_job_listings*.csv
#     reddit_posts.csv            -> reddit_posts*.csv
#     glassdoor_reviews.csv       -> pack/glassdoor reviews dataset/glassdoor_reviews.csv
set -euo pipefail
SRC="$(cd "${1:?usage: bash scripts/setup_data.sh <folder holding the datathon downloads>}" && pwd)"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DATA="${DATATHON_DATA:-$REPO/data}"
mkdir -p "$DATA/zillow"
missing=0

link () {   # link <target> <link path> <what>
  if [ -n "$1" ] && [ -e "$1" ]; then ln -sfn "$1" "$2"; echo "ok       ${2#$REPO/}"
  else echo "MISSING  $3"; missing=1; fi
}
first () { find "$SRC" -maxdepth 3 -type f -name "$1" -not -path "$DATA/*" | sort | head -1; }

PACK="$(find "$SRC" -maxdepth 3 -type d -name "*8th Datathon For Social Good" -not -path "$DATA/*" | sort | head -1)"
if [ -z "$PACK" ]; then
  echo "No unzipped '[For Students] 8th Datathon For Social Good' folder under $SRC. Unzip the pack's .zip parts there first."
  exit 1
fi
link "$PACK" "$DATA/datathon_pack" "datathon pack folder"
link "$PACK/zillow housing dataset/Zillow_part1.csv" "$DATA/zillow/Zillow_part1.csv" "Zillow_part1.csv (in the pack)"
link "$(first 'zillow_part2*.csv')" "$DATA/zillow/zillow_part2.csv" "zillow_part2*.csv"
link "$PACK/zillow housing dataset/zillow_part3.csv" "$DATA/zillow/zillow_part3.csv" "zillow_part3.csv (in the pack)"
link "$(first 'indeed_job_listings*.csv')" "$DATA/indeed_job_listings.csv" "indeed_job_listings*.csv"
link "$(first 'reddit_posts*.csv')" "$DATA/reddit_posts.csv" "reddit_posts*.csv"
link "$PACK/glassdoor reviews dataset/glassdoor_reviews.csv" "$DATA/glassdoor_reviews.csv" "glassdoor_reviews.csv (in the pack)"
[ "$missing" = 0 ] && echo "Data ready in ${DATA}." || { echo "Some files are missing; the workstreams that need them will stop."; exit 1; }
