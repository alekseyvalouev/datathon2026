# E10: Super-commuting into the Bay (LODES)

**Question.** Many workers who leave the 9-county Bay keep their Bay jobs, so for them the cost of exit shows up as a long commute. How many Bay jobs are held by people who live outside the 9 counties? Is that number growing, and for whom? What does the commute cost, compared with the rent saved (E3 ledger)?

**Run it.** `python3 -I run_all.py`. Options: `--skip-fetch` reuses `raw/`; `--skip-aggregate` reuses `outputs/county_flows.csv`. A full run with data already downloaded takes about 40 s. Downloads are about 1.6 GB.

## Layout
| path | what |
|---|---|
| `run_all.py` | single entry point |
| `scripts/fetch.py` | LODES8 CA OD `main` JT00 2010–2024, `aux` JT00 2010–2024 (out-of-state residents with CA jobs), `main` JT01 for 2010/2019/2024, and the Census 2020 county centers of population (`CenPop2020_Mean_CO06.txt`) → `raw/` |
| `scripts/fetch_extra.py` | OSRM public demo server `table` call: driving distance and free-flow time from every CA county's population center to the 9 Bay county centers (`raw/osrm_table.json`); BLS CPI-U (CUUR0000SA0) through the public v1 API |
| `scripts/aggregate.py` | duckdb streams each block-level gz CSV and aggregates it to home county × work county (substr of the 15-digit geocode) → `outputs/county_flows.csv` |
| `scripts/analyze.py` | all tables below |
| `scripts/figs.py` | figures |
| `scripts/hand_check.py` | independent recount of one pair using plain `gzip`+`csv`, no duckdb |

Bay work counties: 06001, 013, 041, 055, 075, 081, 085, 095, 097. "Exurban ring" (11 counties named in the brief): San Joaquin, Stanislaus, Sacramento, Merced, Yolo, Placer, El Dorado, San Benito, Santa Cruz, Monterey, Lake. Unless stated otherwise, the denominator is **Bay-workplace jobs held by CA residents** (the `main` file). `aux` adds out-of-state residents.

## Outputs
| file | content |
|---|---|
| `county_flows.csv` | every home county × work county, all years, JT00/JT01, main/aux, all S/SA/SE/SI columns |
| `bay_inflows_by_county_pair.csv` | the rows of that table with a Bay workplace, with county names |
| `bay_jobs_outside_share_by_band.csv` | by year × band: Bay jobs, jobs held by Bay / ring / other-CA / out-of-state residents, and shares |
| `growth_decomposition.csv` | change in outside-9 holders, 2010–19, 2019–24 and 2010–24, by earnings and age band |
| `earnings_mix_nominal_check.csv` | low/middle share (SE01+SE02) of outside-9 holders vs Bay-resident holders; CPI drift of the $3,333 threshold |
| `bay_jobs_by_distance_band.csv`, `headline_shares.csv` | outside-9 holders split by one-way drive distance (≤60, 60–120, >120 mi) |
| `top_pairs_2024.csv` | top 40 outside-9 → Bay county pairs with 2010/2019 counts, earnings mix, miles, minutes, annual cost |
| `origin_county_trend.csv` | per origin county: Bay jobs held, and the share of the county's residents' CA jobs that are in the Bay |
| `county_drive_distances.csv` | OSRM miles and minutes, CA county → each Bay county |
| **`commute_cost_for_ledger.csv`** | for E3: by destination metro (Sacramento, Stockton, Modesto, Fresno, Merced), the LODES-weighted one-way miles, minutes, and annual/monthly commute cost and hours |
| `ledger_with_commute.csv` | E3 ledger rows (Bay origin, OEWS) with a new scenario: "live inland, keep the Bay job" |
| `jt01_primary_job_check.csv`, `hand_check.csv` | robustness check and verification |

Figures: `figs/fig1_share_outside_by_earnings.png`, `fig2_share_outside_by_age.png`, `fig3_outside_count_index_by_earnings.png`, `fig4_top_pairs.png`, `fig5_ledger_with_commute.png`, `fig6_distance_bands.png`.

## Results

### 1. Level and trend
| | 2010 | 2019 | 2024 |
|---|---|---|---|
| Bay jobs held by CA residents | 3,145,389 | 4,009,184 | 4,007,292 |
| held by residents outside the 9 counties | 465,333 (**14.8%**) | 617,721 (**15.4%**) | 743,084 (**18.5%**) |
| of which, exurban ring (11) | 276,831 (8.8%) | 356,529 (8.9%) | 404,464 (10.1%) |
| of which, ≤120 mi drive ("commutable") | 249,642 (7.9%) | 326,315 (8.1%) | 366,557 (9.1%) |
| of which, >120 mi (LA, San Diego, Orange, Fresno…) | 215,691 (6.9%) | 291,406 (7.3%) | 376,527 (9.4%) |
| out-of-state residents (aux), share of all Bay jobs | 14,284 (0.45%) | 31,609 (0.78%) | 34,318 (0.85%) |
| outside 9 incl. out-of-state, share of all Bay jobs | 15.2% | 16.1% | 19.2% |

Most of the increase came after 2019. Between 2010 and 2019 the share rose only 0.6 pp, while the Bay added 864k jobs. From 2019 to 2024 it rose 3.1 pp with flat Bay employment. More than half of that post-2019 rise is in the >120 mi group, which cannot be daily commuting. It most likely reflects remote or hybrid workers attached to a Bay establishment, plus multi-site employers reporting at headquarters (see caveats). For example, Los Angeles → San Francisco grew from 14,477 (2010) to 21,531 (2019) to 33,540 (2024) at 383 miles.

### 2. By earnings and age band (share of Bay jobs in the band held by outside-9 CA residents)
| band | 2010 | 2019 | 2024 | Δ 2010–19 (pp) | Δ 2019–24 (pp) |
|---|---|---|---|---|---|
| SE01 ≤ $1,250/mo | 15.7% | 16.6% | 18.4% | +0.97 | +1.82 |
| SE02 $1,251–3,333 | 16.7% | 18.4% | 19.6% | **+1.72** | +1.15 |
| SE03 > $3,333 | 13.5% | 14.1% | 18.3% | +0.61 | **+4.25** |
| Age ≤29 | 18.3% | 17.5% | 20.9% | −0.80 | +3.37 |
| Age 30–54 | 14.3% | 15.1% | 18.7% | +0.75 | +3.61 |
| Age 55+ | 12.4% | 14.4% | 16.6% | +1.94 | +2.17 |

Restricted to ≤120 mi commutable origins (`headline_shares.csv`): SE02 went 9.0% → 9.9% → 10.3%, SE03 went 7.2% → 7.4% → 8.8%, and SE01 went 8.4% → 8.9% → 9.6%.

**Is growth concentrated in low/middle earners?** The answer depends on the period.
- **2010–2019: yes, in share.** The outside-9 share of middle-band jobs (SE02) rose almost 3× as fast as the share of high-band jobs. In raw *counts*, SE03 accounts for 87.5% of the increase in outside-9 holders, but that mostly reflects nominal band drift: Bay SE03 jobs grew 53% while SE01 jobs fell 3.5%. Normalizing by Bay jobs in each band, which is what the shares do, gives the reverse picture.
- **2019–2024: no.** The jump is concentrated in SE03 and spread across all ages, which points to remote and hybrid work. Low and middle earners still became *more* likely to live outside the 9 counties (+1.8 / +1.1 pp), even though their absolute counts fell (SE01 −15.9k, SE02 −28.0k) along with the shrinking nominal low bands.
- **Composition.** Outside-9 holders were more low/middle-earning than Bay-resident holders. The gap was +5.6 pp in 2010, peaked at +7.4 pp in 2014, was +6.5 pp in 2019, and fell to **+1.1 pp in 2024** (`earnings_mix_nominal_check.csv`). Inflation drift affects both groups about equally, so this gap is the cleanest band comparison available. The pre-2020 super-commuter was disproportionately lower-paid. Since 2020 the pool has been diluted by high earners.

**Nominal bands.** The LODES thresholds have been fixed since 2002. Using annual CPI-U, $3,333 in 2024 equals **$2,317 in 2010 dollars (−30%)**. So workers drift into SE03 without any real raise, and SE01/SE02 counts shrink mechanically. That is why the analysis uses within-band shares and the outside-vs-Bay gap, not counts.

### 3. Top pairs, distances, cost (2024; `top_pairs_2024.csv`, fig 4)
- San Joaquin → Alameda: **41,799** jobs (25,088 in 2010; 37,106 in 2019). 57 mi one-way, 68 min free-flow.
- San Joaquin → Santa Clara: 24,351 (75 mi). Sacramento → Alameda: 22,664 (101 mi). Santa Cruz → Santa Clara: 22,177 (33 mi). Sacramento → Santa Clara: 20,676 (128 mi). Stanislaus → Alameda: 16,762 (72 mi). Monterey → Santa Clara: 16,123 (66 mi).
- Several of the largest *pairs* start in LA, San Diego or Orange County. These are not commutes (see above).
- **Origin dependence on the Bay** (share of the county's resident CA jobs located in the Bay, 2010 → 2024): San Benito 30.9% → 33.7%, Santa Cruz 27.8% → 32.3%, **San Joaquin 26.4% → 30.0%**, Tuolumne 16.7% → 21.5%, Stanislaus 17.2% → 19.2%, Yolo 16.3% → 19.1%, Monterey 14.7% → 18.3%, Merced 13.1% → 15.3%, Sacramento 13.6% → 14.1%, Fresno 5.0% → 5.2%.

### 4. Commute cost line for E3 (`commute_cost_for_ledger.csv`)
Distance is the average of the OSRM county-center → Bay-county-center drive, weighted by the 2024 flows of SE01+SE02 jobs from the metro's home counties (an all-jobs weighting is also in the file). Annual figures assume 250 round trips per year.

| metro (home counties) | Bay jobs held 2024 (2010) | one-way mi | free-flow min | $/mo fuel only | $/mo IRS full | h/mo | plausibly daily? |
|---|---|---|---|---|---|---|---|
| Sacramento (Sac, Placer, El Dorado, Yolo) | 157,564 (114,315) | 97.7 | 121 | 529 | 3,093 | 84 | yes (≤120 mi) |
| Stockton (San Joaquin) | 101,638 (61,106) | 64.9 | 82 | 352 | 2,056 | 57 | yes |
| Modesto (Stanislaus) | 44,706 (30,342) | 86.3 | 106 | 467 | 2,732 | 74 | yes |
| Merced | 17,279 (10,505) | 116.5 | 153 | 631 | 3,688 | 106 | marginal |
| Fresno | 21,633 (16,040) | 168.8 | 204 | 914 | 5,344 | 142 | **no** |

Cost sources:
- **Upper bound:** the IRS business standard mileage rate, **$0.76/mi** for Jul 1–Dec 31 2026 (irs.gov/tax-professionals/standard-mileage-rates; IR-2026-29; it was 70¢ in 2025 and 67¢ in 2024). It is a full cost of ownership: depreciation, insurance, fuel and maintenance.
- **Lower bound:** fuel only, at AAA *Your Driving Costs* 2025, "average fuel cost … 13.00 cents per mile" (newsroom.aaa.com/2025/09/aaa-new-vehicle-costs-drop-to-11577/).
- The true *marginal* cost of extra miles for someone who already owns a car lies between the two.
- A 3-day hybrid version (`annual_commute_cost_irs_hybrid3d`) is in the file.
- The time column uses OSRM free-flow durations, so it **understates peak-hour time**. It is not monetized: the USDOT value-of-time guidance page returned 403 and could not be verified.

**Ledger-adjusted residual** (1-BR, Bay OEWS median wage kept, inland rent from E3; `ledger_with_commute.csv`, fig 5):
- **Caregiver:** re-renting in the Bay leaves **−$197/mo**. Living in Stockton and keeping the Bay job leaves **+$596** with fuel-only cost, or **−$1,108** at the IRS rate. Moving to Stockton for the local wage leaves +$813.
- **Cashier:** re-rent $246. Stockton keeping the Bay job: $1,039 (fuel) or −$665 (IRS). Stockton at the local wage: $980.
- **Pattern:** at fuel-only cost, the "keep the Bay job" scenario beats re-renting in the Bay for every occupation and metro. At the full IRS cost it is negative in 35 of 40 occupation × metro cells (1-BR). The rent saved against the Bay re-rent is about $1,140–1,460/mo (1-BR). That is the same size as the full cost of a 65–100-mile daily drive, before counting 57–84 hours per month on the road.

## Verification
- **Hand check** (`hand_check.csv`): San Joaquin (06077) → Alameda (06001), 2024 JT00, was recounted from the raw block file with Python's `gzip`+`csv` and no duckdb. S000 = 41,799, SE01 = 4,131, SE02 = 6,672 and SE03 = 30,996 all match the pipeline exactly. That pair covers 39,380 block pairs.
- **Multiple jobs** (`jt01_primary_job_check.csv`): with JT01 (primary jobs only), the outside-9 share is 14.8% / 15.4% / 18.6% for 2010 / 2019 / 2024, against 14.8% / 15.4% / 18.5% for JT00. Second jobs do not drive the result.
- **ACS cross-check:** not done. When E9 produces ACS travel-time or place-of-work tables, compare the San Joaquin → Bay share and the mean commute time against the OSRM free-flow times here, which should be lower than ACS.

## Caveats
- **Jobs, not people.** JT00 counts all jobs. The JT01 check above shows little difference.
- **Workplace geography.** Some multi-establishment employers report all workers at one address, such as headquarters, and remote workers are coded to their employer's establishment. This is the most likely reason for the large and fast-growing >120 mi group (LA → SF, San Diego → Santa Clara) and for part of the 2020+ SE03 jump. The ≤120 mi split is the conservative "real commuter" measure.
- **Residence** comes from administrative records (UI wage records linked to federal address data). It can lag a move, which biases recent exits toward appearing as Bay residents.
- **Nominal earnings bands** (see above). The bands are also monthly earnings for that job, so part-time work lands in SE01 regardless of hourly wage.
- **Remote work 2020+.** LODES cannot tell remote from in-person. Commute costs assume daily trips, which overstates cost for hybrid workers (see the hybrid column).
- **Year-to-year noise.** There is a visible dip in 2015 in all outside-9 shares, about −0.8 pp, which reverses in 2016. It is likely an input or processing artifact, not behavior. Trend statements use 2010, 2019 and 2024.
- **Distances** are between county *population centers*, not actual home and work addresses. For large counties (Sacramento, Santa Clara) the error can be ±20 mi or more. OSRM is a public demo server (OpenStreetMap). If it is unavailable, the code falls back to haversine × 1.2, which is an assumption.
- **Not done:** tract-level aggregation on the work side, and monetizing commute time.
