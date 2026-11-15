# units-leaving-reach

Predicts, at re-listing, whether a Bay Area rental that a household at 80% of area median income could still afford will be re-priced out of that household's reach. This is the Advanced Track model that ties the other three workstreams together:

- **movement:** turnover pairs and income limits
- **displacement-early-warning:** tract features and the backtest risk score
- **ai-labor-distribution:** city job mix

Results, nulls and limits are in **[FINDINGS.md](FINDINGS.md)**. The label and join audit is in [memos/hand_check.md](memos/hand_check.md).

## Reproduce
From the repo root, after `bash scripts/setup_data.sh <downloads folder>` (see the repo README):
```bash
bash scripts/reproduce.sh      # Zillow cache -> movement E2, E6 -> this workstream (~10 min)
```
That runs, in order:
```bash
python3 movement/analysis/common/build_zillow.py          # raw Zillow CSVs -> movement/analysis/cache/zillow.duckdb
python3 movement/analysis/e2_turnover_model/run_all.py    # same-unit turnover pairs + UDP tract join
python3 movement/analysis/e6_unit_replacement/run_all.py  # CA HCD income limits 2022-2026
bash units-leaving-reach/code/run_all.sh                  # this workstream (~2 min)
```
Tract features and the backtest risk score (`displacement-early-warning/results/`) and the city job mix (`ai-labor-distribution/results/asset_city_jobs_housing.csv`) are read from those workstreams’ committed result tables.

Dependencies: `requirements.txt` at the repo root. The pipeline is deterministic: fixed seeds, `deterministic=True` LightGBM and stable row order. Two independent rebuilds from raw data inside this repo produced byte-identical tables.

## Map page
`site/out-of-reach-atlas.html` (built by `code/s05_project.py` → `s06_geo.py` → `s07_build_page.py`, all run by `run_all.sh`) is a year slider over a map of the 9,403 tracked units:
- **2022–2026:** what the listings recorded.
- **2027–2031:** model projections under two rent scenarios and an adjustable annual turnover rate.

The deployment model is refit on all observed pairs; held-out evaluation stays in `s03`. Projection assumptions are listed in the header of `s05_project.py` and on the page.
