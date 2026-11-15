# datathon2026

8th Annual Datathon for Social Good · San Francisco Bay Area · Advanced Track.

**The story in one line:** the Bay Area’s boom does not push people out through layoffs; it pushes them out through rents. Regional averages, the standard displacement map and our own models are all weakest exactly where the people being pushed out are. The full narrative, built from five workstreams, is in **[SYNTHESIS.md](SYNTHESIS.md)**.

| Output | Where |
|---|---|
| Unified narrative across workstreams | [`SYNTHESIS.md`](SYNTHESIS.md) |
| Advanced Track model (unit-level, held-out 2026 test, fairness audit) | [`units-leaving-reach/FINDINGS.md`](units-leaving-reach/FINDINGS.md) |
| Interactive map, 2022 → 2031 projections | `units-leaving-reach/site/out-of-reach-atlas.html` (open locally) |
| Movement findings page | `movement/site/follow-the-people.html` |
| Displacement findings page | `displacement-early-warning/site/index.html` |
| Slide deck source | [`deck/`](deck/) |

## Workstreams

| Folder | Question | Entry point |
|---|---|---|
| [`ai-labor-distribution/`](ai-labor-distribution/) | Who captures AI-era gains (equity holders, engineers) and who is exposed (support, clerical, contract roles)? Job postings, WARN layoffs and occupation microdata linked to wages by race and county. 6 experiments, 17 documented nulls. | scripts in `code/` (see *Known gaps*) |
| [`movement/`](movement/) | When households leave, what happens to them, to the homes they leave and to the people who replace them? IRS migration, same-unit Zillow turnovers, ACS PUMS movers, LODES commutes, Reddit exit stories. 10 experiments. | `bash scripts/reproduce.sh movement` |
| [`displacement-early-warning/`](displacement-early-warning/) | Can census data and Zillow price histories flag tracts at risk earlier, and more fairly, than the Urban Displacement Project typology? 2000→2018 backtest, post-2018 forward test, fairness audit. 11 experiments. | `code/run_all.sh` |
| [`who-speaks-who-decides/`](who-speaks-who-decides/) | Who speaks at the San Francisco Planning Commission, and does it change what happens to housing projects? 73,002 public comments, 1998–2026. | `code/run_all.sh` |
| [`units-leaving-reach/`](units-leaving-reach/) | At re-listing, which still-affordable rentals will a turnover price out of reach of a household at 80% of area median income? Joins the workstreams; Advanced Track centerpiece. | `bash scripts/reproduce.sh` |

## Reproducing

Bulk data is **not** committed (`data/`, `*.csv` downloads, `*.parquet`, `*.duckdb`, downloaded `raw/` and `external/` folders are all in `.gitignore`). Every committed result table is rebuilt by code in this repo.

### 1. Environment
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
Tested with Python 3.13 on macOS. `sentence-transformers` is only needed for movement E4.

### 2. Data
Download the datathon pack and unzip its parts into one folder, next to the large CSVs distributed separately (`zillow_part2*.csv`, `indeed_job_listings*.csv`, `reddit_posts*.csv`). Then:
```bash
bash scripts/setup_data.sh /path/to/that/folder
```
This creates symlinks only, in `data/` (or `$DATATHON_DATA`):
```
data/
  datathon_pack/            the unzipped "[For Students] 8th Datathon For Social Good" folder
  zillow/Zillow_part1.csv   zillow/zillow_part2.csv   zillow/zillow_part3.csv
  indeed_job_listings.csv   reddit_posts.csv          glassdoor_reviews.csv
```
Public sources (IRS SOI migration, ACS PUMS, LEHD LODES, BLS OEWS, CA HCD income limits, CA EDD WARN, Census boundaries, the UDP typology repository) are downloaded by the scripts that use them.

### 3. Run
```bash
bash scripts/reproduce.sh            # model chain: Zillow cache -> movement E2, E6 -> units-leaving-reach (~10 min)
bash scripts/reproduce.sh movement   # all ten movement experiments (~1 hour, downloads public data)
bash scripts/reproduce.sh all        # both
```
Then check that nothing changed: `git status --short`. The model chain is deterministic: two independent rebuilds from raw data, each with a fresh cache, produced byte-identical output in all 69 result files (2026-11-14). Two fixes made that true: same-day Zillow price events are ordered by their position in the listing’s history (`movement/analysis/common/build_zillow.py`), and rows are sorted before averaging and linear algebra runs single-threaded (`scripts/reproduce.sh`).

The other workstreams run on their own:
```bash
ZILLOW_RAW=data/zillow bash displacement-early-warning/code/run_all.sh
cd who-speaks-who-decides && bash code/run_all.sh <sf-planning-public-comment-data>/public ../data/zillow
```
`units-leaving-reach` reads three committed result tables from those workstreams (`displacement-early-warning/results/e5_tract_table.csv`, `e2_predictions.csv`, `ai-labor-distribution/results/asset_city_jobs_housing.csv`), so it does not need them re-run.

### Known gaps
- **`ai-labor-distribution/code` is not runnable as committed.** 43 scripts hard-code paths on the author’s machine (a temporary scratch folder and `~/Desktop/Datathon/...`) and there is no single entry point. Its result tables are committed and are what the synthesis cites.
- **Human checks still owed:** `movement/analysis/e4_exit_classifier/labels/verify_sample.csv` (50 items) and `movement/analysis/e7_pulled_in/labels/verify_sample.csv` (30 items) were labelled by a language model.
- **who-speaks-who-decides** used Zillow parts 1 and 3 only; with part 2 its Zillow-based numbers will change (its README says so).

## Convention for adding a workstream

One folder per workstream, named for the question rather than the method. Inside it:

```
<workstream>/
  FINDINGS.md     synthesis — headline claims, positive AND negative, with the numbers inline
  memos/          per-experiment write-ups, including methods and limitations
  results/        tidy result tables; every number in FINDINGS.md should trace to one
  code/           scripts that run raw data -> reported results
```

Two things that make cross-workstream synthesis possible:

1. **Report nulls as prominently as positives.** A workstream that only reports what it confirmed cannot be combined with one that reports honestly — the synthesis will overstate. `ai-labor-distribution` documents 17 null results and they materially constrain what the combined story can claim.
2. **State the limits where the claim appears,** not in a footnote. Several results here are cross-sectional associations or accounting arithmetic that look causal if quoted without their caveat.

New code should read raw data from `$DATATHON_DATA` (default `data/`, the layout above) and never from an absolute path.

## Cross-workstream notes

Findings that other workstreams may need to reconcile with:

- **Displacement does not show up in the measurable record.** Bay Area WARN layoff intensity has no trend across 13 quarters (slope −0.17/quarter, p=0.66); there is no call-center relocation signal; worker AI-displacement discourse is flat to falling; the entry-level rung is not thinner in exposed occupations. Any claim that AI is visibly destroying Bay Area jobs needs to contend with this.
- **The job-postings data cannot support a time trend.** Posting dates are reconstructed from relative strings and 55.8% are censored; the crawl is also partly keyword-seeded toward tech titles. Anyone else using this Indeed extract should read `ai-labor-distribution/FINDINGS.md` §"data-quality traps" first.
- **Gains and assets flow to different groups.** White households hold 70.7% of Bay Area capital income while being under-represented in AI-positioned jobs; Asian workers are the mirror image. A single "winners" category will not fit the data.
- **A fitted model beats the UDP vulnerability flag, but "risk" is not one thing.** On held-out tracts, 1990/2000 census data predicts loss of low-income households by 2018 at AUC 0.78 against 0.52 for the UDP flag. After 2018 that flag ranks flipping correctly (0.64) and price and rent growth backwards (0.38). Anyone using UDP typology as a risk measure should read `displacement-early-warning/FINDINGS.md` first.
- **Unit-level loss of affordability is predictable, but mostly from headroom arithmetic.** On 2026 re-listings, a model predicts which units leave 80%-of-area-median reach at AUC 0.90, against 0.85 for the AB 1482 legal-max rule and 0.46 for the UDP typology, which ranks it backwards. Tract and city-job features from the other workstreams add only +0.004 together. At a fixed budget the model under-serves renter-majority and low-income tracts and large-manager apartments. See `units-leaving-reach/FINDINGS.md`.
- **Zillow price history adds little beyond census data.** It gives a detectable gain for predicting flipping only (+0.03 AUC); nothing detectable for price or rent growth. Its value is in building outcomes, not features.
- **Hearings are not where housing is stopped.** In San Francisco 90% of contested projects were approved and the Commission followed staff 97% of the time; opposition buys delay and split votes. See `who-speaks-who-decides/FINDINGS.md`.
