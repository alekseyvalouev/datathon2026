# displacement-early-warning/

Workstream on predicting displacement risk at census-tract level: does a fitted model beat the Urban Displacement Project (UDP) typology, what do Zillow price histories add, and for whom do the models fail? Start with **[FINDINGS.md](FINDINGS.md)**.

## Layout
```
displacement-early-warning/
  FINDINGS.md     synthesis: headline claims, nulls, limits, Advanced Track checklist
  memos/          per-experiment write-ups: methods, hand checks, caveats
    backtest_findings.md   E1, E2, E2b, E3  (UDP landscape, 2000 -> 2018 backtest, fairness)
    forward_findings.md    E4, E5, E6       (Zillow-to-tract join, post-2018 forward test, fairness)
    market_findings.md     E7, E8, E9, E10  (flipping, rent at re-listing, price trajectories, affordability)
  results/        result tables (CSV) and map_geometry.json; every number in FINDINGS.md traces to one
  code/           one script per experiment, common.py, run_all.sh, requirements.txt, udp_eda.ipynb
  site/           index.html findings page; build.py + template.html rebuild it from results/
```

## Data (not committed)
- **Zillow**: `Zillow_part1.csv`, `zillow_part2.csv`, `zillow_part3.csv` from the datathon pack (7.4 GB). Point `ZILLOW_RAW` at the folder that holds them.
- **UDP**: `run_all.sh` clones github.com/urban-displacement/displacement-typologies (typology output, codebook, tract shapes) into `data/udp` if `UDP_REPO` is not set.

## Reproduce
```bash
pip install -r code/requirements.txt
ZILLOW_RAW=/path/to/zillow bash code/run_all.sh
```
`e0_extract_zillow.py` first writes slim property and price-history tables to `$ZILLOW_WORK` (default `~/work`, about 60 s with the three files in parallel). The full run takes about four minutes on a laptop and writes `results/` plus `results/logs/`. A full re-run from the raw files on 2026-11-14 reproduced every E4-E10 table exactly and matched E1-E3; tree-based models differ in the fourth decimal between machines.

`results/e4_property_tract.csv.gz` (property id to tract, with coordinates) is produced by E4 and needed by E5-E10. It is not committed; coordinates in `e4_hand_check_30.csv` are rounded to three decimals.

## Not included
San Francisco eviction notices and building permits were planned as a case study and are not in this version.
