# units-leaving-reach

Predicts, at re-listing, whether a Bay Area rental that a household at 80% of area median income could still afford will be re-priced out of that household's reach. This is the Advanced Track model that ties the other three workstreams together:

- **movement:** turnover pairs and income limits
- **displacement-early-warning:** tract features and the backtest risk score
- **ai-labor-distribution:** city job mix

Results, nulls and limits are in **[FINDINGS.md](FINDINGS.md)**. The label and join audit is in [memos/hand_check.md](memos/hand_check.md).

## Reproduce
```bash
# upstream, once (each from raw data):
python3 analysis/common/build_zillow.py
python3 analysis/e2_turnover_model/run_all.py
python3 analysis/e6_unit_replacement/run_all.py
bash datathon2026/displacement-early-warning/code/run_all.sh
# ai-labor-distribution/code/asset_t3.py writes results/asset_city_jobs_housing.csv

# this workstream (~1 min):
bash datathon2026/units-leaving-reach/code/run_all.sh
```
Dependencies: python3, pandas, numpy, scikit-learn 1.7, lightgbm 4.7, duckdb, matplotlib, pyarrow. The pipeline is deterministic: fixed seeds, `deterministic=True` LightGBM, and stable row order.

## Map page
`site/out-of-reach-atlas.html` (built by `code/s05_project.py` → `s06_geo.py` → `s07_build_page.py`, all run by `run_all.sh`) is a year slider over a map of the 9,404 tracked units:
- **2022–2026:** what the listings recorded.
- **2027–2031:** model projections under two rent scenarios and an adjustable annual turnover rate.

The deployment model is refit on all observed pairs; held-out evaluation stays in `s03`. Projection assumptions are listed in the header of `s05_project.py` and on the page.
