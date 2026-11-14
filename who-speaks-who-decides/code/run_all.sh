#!/usr/bin/env bash
# Reproduce every reported result from the raw files.
# Run from the workstream folder (who-speaks-who-decides/).
# Usage: code/run_all.sh <path to Sahn repo public/ folder> <folder holding the Zillow part CSVs>
set -euo pipefail
PUBLIC=${1:?path to sf-planning-public-comment-data/public}
ZILLOW_DIR=${2:?folder containing the Zillow *part*.csv files}
export WORK_DIR=${WORK_DIR:-work}
mkdir -p "$WORK_DIR" results
PY="python3 -W ignore"
run () { echo ">> $1" >&2; shift; "$@" 2>&1 | grep -v -i "warn" ; }
run 00 $PY code/00_zillow_extract_sf.py "$ZILLOW_DIR"/*part*.csv "$WORK_DIR/zillow_sf.csv"            > results/00_zillow_extract_sf.txt
run 01 $PY code/01_eda.py "$PUBLIC"                                                                   > results/01_eda.txt
run 02 $PY code/02_stance_baseline.py "$PUBLIC"                                                       > results/02_stance_baseline.txt
run 03 $PY code/03_stance_with_context.py "$PUBLIC"                                                   > results/03_stance_with_context.txt
run 04 $PY code/04_outcomes_first_hearing.py "$PUBLIC" "$WORK_DIR/zillow_sf.csv" "$WORK_DIR/projects_first_heard.csv" > results/04_outcomes_first_hearing.txt
run 05 $PY code/05_site_projects_and_speakers.py "$PUBLIC" "$WORK_DIR/zillow_sf.csv" "$WORK_DIR/site_projects.csv" "$WORK_DIR/site_comments.csv" > results/05_site_projects_and_speakers.txt
run 06 $PY code/06_affordability_unaffiliated_roles.py "$PUBLIC"                                      > results/06_affordability_unaffiliated_roles.txt
run 07 $PY code/07_build_heard_projects.py "$PUBLIC"                                                  > results/07_build_heard_projects.txt
run 08 $PY code/08_stalls_corrected.py "$PUBLIC"                                                      > results/08_stalls_corrected.txt
run 09 $PY code/09_which_buildings.py "$PUBLIC"                                                       > results/09_which_buildings.txt
run 10 $PY code/10_trends.py "$PUBLIC"                                                                > results/10_trends.txt
run 11 $PY code/11_votes_and_agenda.py "$PUBLIC"                                                      > results/11_votes_and_agenda.txt
run 12 $PY code/12_remote_hearings.py "$PUBLIC"                                                       > results/12_remote_hearings.txt
run 13 $PY code/13_blocs_responsiveness_volume.py "$PUBLIC"                                           > results/13_blocs_responsiveness_volume.txt
echo "done. Tables are in results/. Optional: python3 code/14_examples.py $PUBLIC $WORK_DIR/projects_first_heard.csv 0  (prints project histories; do not commit its output)"
