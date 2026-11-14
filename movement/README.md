# movement/

Workstream on displacement and migration in the Bay Area: following people, homes and flows rather than places. Start with **[FINDINGS.md](FINDINGS.md)**.

## Layout
```
movement/
  FINDINGS.md            synthesis: headline claims, nulls, limits
  analysis/
    common/build_zillow.py   raw Zillow CSVs -> analysis/cache/zillow.duckdb (shared by E2, E3, E6, E8)
    e1_composition/ ... e10_supercommute/
      README.md          methods, results, hand checks, caveats (Advanced Track checklist where relevant)
      run_all.py | run.sh   single entry point: raw data -> outputs
      scripts/ or s0*.py
      outputs/           result tables (CSV/JSON) and run logs
      figs/              charts (PNG)
      labels/            (E4, E7) hand/LLM labels + verify_sample.csv for human checking
  site/
    follow-the-people.html   findings page (self-contained HTML)
    template.html            page source with a __DATA__ placeholder
    build_data.py            collects numbers from analysis/*/outputs into data.json
```

## Data (not committed)
Bulk inputs are excluded (see the repo `.gitignore`). To reproduce, put the datathon pack and the three large CSVs at the `movement/` root, the same layout the scripts expect:
```
movement/
  data/[For Students] 8th Datathon For Social Good/   (unzipped datathon pack)
  zillow_part2-005.csv
  reddit_posts-003.csv
  indeed_job_listings-004.csv
```
The external sources each experiment needs (IRS SOI migration, ACS PUMS, LEHD LODES8, BLS OEWS, Zillow ZORI, California HCD income limits, Urban Displacement Project tracts, Freddie Mac PMMS) are downloaded by its own entry point into a `raw/` or `external/` folder.

## Run order
1. `python3 analysis/common/build_zillow.py`: builds the shared Zillow cache.
2. Indeed and Reddit caches: E3 and E4 write their own loaders from the raw CSVs. See each README.
3. Any experiment: `python3 analysis/<exp>/run_all.py`, or `./run.sh` for E1 and E5. E2's robustness checks: `python3 analysis/e2_turnover_model/run_robustness.py`.
4. Findings page: `python3 site/build_data.py <us-atlas counties-10m.json>`, then substitute `site/data.json` into `site/template.html` at `__DATA__`.
   - The county shapes come from https://cdn.jsdelivr.net/npm/us-atlas@3.0.1/counties-10m.json.

Requirements: Python 3.11+, `duckdb`, `pandas`, `numpy`, `scikit-learn`, `lightgbm`, `matplotlib`, `pyarrow`; E4 also needs `sentence-transformers`.

## Before presenting
- Hand-verify `analysis/e4_exit_classifier/labels/verify_sample.csv` (50 items) and `analysis/e7_pulled_in/labels/verify_sample.csv` (30 items). Those labels were produced by a language model.
- No addresses or usernames appear in any output. Keep it that way.
