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
Bulk inputs are excluded (see the repo `.gitignore`). The scripts read them from the repo-level `data/` folder (or `$DATATHON_DATA`), which `bash scripts/setup_data.sh <downloads folder>` fills with links. See the repo README:
```
data/datathon_pack/          unzipped datathon pack (Google Maps places and reviews for E7, E8)
data/zillow/*.csv            Zillow parts 1-3 (shared cache, E6 text columns)
data/indeed_job_listings.csv E3, E7
data/reddit_posts.csv        E4, E7
```
The external sources each experiment needs (IRS SOI migration, ACS PUMS, LEHD LODES8, BLS OEWS, Zillow ZORI, California HCD income limits, Urban Displacement Project tracts, Freddie Mac PMMS) are downloaded by its own entry point into a `raw/` or `external/` folder.

## Run order
`bash scripts/reproduce.sh movement` (from the repo root) runs everything below in order. By hand:
1. `python3 movement/analysis/common/build_zillow.py`: builds the shared Zillow cache `analysis/cache/zillow.duckdb`.
2. The shared Indeed cache `analysis/cache/indeed.duckdb` (E3, E7) is built from the raw CSV the first time E3 needs it, or with `python3 movement/analysis/e3_mover_ledger/scripts/load_indeed.py --rebuild`. E4 and E7 stream the raw Reddit CSV directly.
3. Experiments in this order, since some reuse earlier outputs: E1, E5 (reuses E1’s downloads), E2, E3, E4, E6, E7 (reuses E3, E4), E8 (reuses E2, E6), E9, E10. Each is `python3 analysis/<exp>/run_all.py`, or `bash analysis/<exp>/run.sh` for E1 and E5. E2’s robustness checks: `python3 analysis/e2_turnover_model/run_robustness.py`.
4. Findings page: `python3 site/build_data.py <us-atlas counties-10m.json>`, then substitute `site/data.json` into `site/template.html` at `__DATA__`.
   - The county shapes come from https://cdn.jsdelivr.net/npm/us-atlas@3.0.1/counties-10m.json.

Requirements: Python 3.11+, `duckdb`, `pandas`, `numpy`, `scikit-learn`, `lightgbm`, `matplotlib`, `pyarrow`; E4 also needs `sentence-transformers`.

## Before presenting
- Hand-verify `analysis/e4_exit_classifier/labels/verify_sample.csv` (50 items) and `analysis/e7_pulled_in/labels/verify_sample.csv` (30 items). Those labels were produced by a language model.
- No addresses or usernames appear in any output. Keep it that way.
