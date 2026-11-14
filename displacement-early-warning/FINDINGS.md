# Displacement early warning: predictable, but not one thing

**Question.** Can census data and housing-market signals flag Bay Area neighborhoods at risk of displacement earlier, and more fairly, than the Urban Displacement Project (UDP) rule-based typology?

**Thesis.**
- A simple model on year-2000 census data picks out the tracts that went on to lose low-income households far better than the UDP vulnerability flag.
- Since 2019 market pressure has split: house flipping stayed in lower-income tracts while price and rent growth moved to affluent ones. One risk score hides that.
- Every model here is weakest for some of the places it is meant to protect: owner-heavy suburbs, outer counties and low-income typologies.

Findings page: `site/index.html`, published at https://claude.ai/artifact/2LyTDtDBo2k5R54ZmaxEGE (private; share access from the page). Methods, hand checks and caveats per experiment are in `memos/`. Every number below traces to a table in `results/` produced by a script in `code/`; tags such as [E2] point to the Methods table.

Data: Zillow property extract from the datathon pack (148,005 properties) and the UDP typology output for the Bay Area (1,550 tracts in nine counties). No other datathon dataset is used.

---

## Headline numbers

| | Finding | Experiment |
|---|---|---|
| **0.78 vs 0.52** | Test AUC for predicting which tracts lost low-income households 2000-2018 from 1990/2000 census data: logistic model 0.777 against the UDP vulnerability flag 0.520 (388 held-out tracts, 73 positives) | E2 |
| **0.80 vs 0.64** | Test AUC for predicting post-2018 flipping hot spots: census + pre-2019 Zillow model 0.798, census only 0.769, UDP vul_gent_18 flag 0.641 (320 spatially held-out tracts) | E5 |
| **72% vs 21%** | Share of true loss tracts the backtest model catches in majority-renter against majority-owner tracts at one regional threshold | E3 |
| **51-62% vs 29%** | Median asking rent as a share of tract household income (2018 dollars) in low-income UDP typologies against Stable/Advanced Exclusive tracts | E10 |

## 1. One in five tracts lost low-income households while the region gained them [E1]

- 1,550 tracts in nine counties. 292 (18.8%) had fewer low-income households in 2018 than in 2000.
- The region gained a net 228,345 low-income households; the 292 losing tracts lost 24,521.
- Share of tracts with a loss: San Francisco 41.9%, Alameda 26.3%, San Mateo 21.2%, Napa 20.0%, Marin 15.4%, Contra Costa 9.8%, Santa Clara 9.7%, Sonoma 8.1%, Solano 7.4%.
- Leakage check: every Ongoing Displacement and Becoming Exclusive tract has the loss flag and no Low-Income/Susceptible tract does, so the 2018 typology cannot be a feature for a 2000-2018 label.

## 2. Conditions in 2000 predicted the loss; the UDP flags did not [E2, E2b]

Label: `lostli_18`. Features: 19 census variables from 1990 and 2000. 25% of tracts (388) were set aside before modelling; tuning used county-held-out cross-validation on the other 1,162.

| Model | CV AUC (dev) | Test AUC [95% interval] | Test average precision |
|---|---|---|---|
| Logistic regression (selected) | 0.782 | 0.777 [0.715, 0.831] | 0.465 |
| Random forest | 0.771 | 0.788 [0.730, 0.841] | 0.467 |
| Gradient boosting | 0.764 | 0.794 [0.739, 0.843] | 0.508 |
| Renter share 2000 alone | 0.702 | 0.661 [0.583, 0.728] | 0.315 |
| UDP vul_gent_00 flag | 0.549 | 0.520 [0.467, 0.580] | 0.195 |
| UDP lostli_00 (lost 1990-2000) | 0.484 | 0.481 | 0.184 |

- The three models are statistically indistinguishable on this test set.
- After isotonic recalibration the riskiest fifth of test tracts was predicted at 51.8% and observed at 46.2%.
- Strongest drivers: low-income share, home value, college share and non-white share in 2000.
- The UDP flags were built to classify neighborhood stages, not to forecast this label.

Label robustness, same split and features [E2b]:

| Label | Positives (all / test) | Logistic test AUC [95% interval] | UDP flag test AUC |
|---|---|---|---|
| Any loss (base) | 292 / 73 | 0.777 [0.715, 0.831] | 0.520 |
| Lost 10% or more of low-income households | 147 / 30 | 0.796 [0.721, 0.864] | 0.452 |
| Low-income share fell 5+ points | 128 / 30 | 0.818 [0.720, 0.889] | 0.615 |

## 3. After 2018, different pressures landed in different places [E5, E7, E9]

The forward test predicts market pressure, not displacement. Outcomes use only Zillow events dated 2019 or later; the target is the top quarter of tracts. Features: 22 UDP variables for 2012/2018 plus 14 Zillow features dated before 2019. Whole 0.1-degree grid cells were held out.

| Target (test n, positives) | Census only | Census + Zillow | Gain [95% interval] | UDP vul_gent_18 flag |
|---|---|---|---|---|
| Flipping hot spot (320, 95) | 0.769 | 0.798 | +0.029 [0.005, 0.057] | 0.641 |
| High appreciation (170, 44) | 0.780 | 0.816 | +0.036 [-0.010, 0.080] | 0.384 |
| High rent growth (125, 23) | 0.728 | 0.737 | +0.009 [-0.068, 0.084] | 0.379 |

- Zillow history adds a detectable gain for flipping only.
- The UDP flag points the right way for flipping and the wrong way for appreciation and rent growth.
- Disclosure: the first random draw of test cells had no San Francisco tract and was redrawn after results were seen. The flipping result held on both draws; the rent result did not.

Flipping [E7]: 3,337 of 57,552 resales in 2019-2026 were flips (resold within 18 months at a 20%+ markup), 5.8%. At Risk of Gentrification tracts have the highest share (10.3%) under all nine definitions tested; Stable/Advanced Exclusive tracts 4.5%. Zip-level flip share in 2009-18 correlates with 2019-26 at 0.55.

Price trajectories [E9]: price per square foot in At Risk of Gentrification tracts grew 16.7% a year to 2017-19 and 2.7% a year since; in Stable/Advanced Exclusive tracts 8.4% then 5.0%. Zip-level correlation between the periods is -0.24 with non-overlapping windows.

## 4. Asking rents are out of reach where incomes are lowest [E10, E8]

| UDP typology | Tracts | Median asking rent | Rent / income | Tracts where rent exceeds half of income |
|---|---|---|---|---|
| Ongoing Displacement | 19 | $2,950 | 62% | 84% |
| At Risk of Gentrification | 50 | $2,090 | 61% | 72% |
| Low-Income/Susceptible | 191 | $2,425 | 51% | 54% |
| Stable Moderate/Mixed | 377 | $3,068 | 35% | 11% |
| Stable/Advanced Exclusive | 84 | $3,844 | 29% | 4% |

- Income is in 2018 dollars and covers all households, so ratios overstate burden to an unknown degree.
- Re-listed units [E8]: median change +3.0% a year across 36,320 pairs; 16.2% rose more than 10% a year (San Francisco 36.6%, San Mateo 31.1%). Houses, condos and townhomes only: 8.1%.
- California AB 1482 caps increases for sitting tenants and does not limit the rent of a vacant unit, so these jumps are legal.

## 5. Where the models are weakest [E3, E6]

Backtest model, test set:

| Group | n | Losses | Recall | False-positive rate |
|---|---|---|---|---|
| Majority renter | 138 | 39 | 0.72 | 0.29 |
| Majority owner | 250 | 34 | 0.21 | 0.04 |
| Low-income third | 130 | 25 | 0.60 | 0.21 |
| High-income third | 124 | 19 | 0.37 | 0.08 |
| Near rail | 137 | 36 | 0.64 | 0.26 |
| No rail | 251 | 37 | 0.32 | 0.06 |
| Majority people of color | 165 | 26 | 0.42 | 0.09 |
| Majority white | 223 | 47 | 0.51 | 0.15 |

- Leave-one-county-out: 0 of 7 loss tracts caught in Solano, 0 of 8 in Napa; San Francisco recall 0.80 with a 39% false-positive rate.
- Flipping model: AUC 0.68 inside UDP low-income typologies against 0.83 in moderate ones; one in three low-income-typology tracts that are not hot spots gets flagged.
- Coverage: a flip outcome exists for 72% of low-income-typology tracts against 90% of high-income ones.
- 17 failure tracts are listed in `results/e3_failure_tracts.csv` and `results/e6_failure_tracts.csv`.

## Nulls, reversals and unstable results

Stated here so that a synthesis does not overstate.

- **Zillow price history adds nothing detectable for price appreciation or rent growth.** Gains of +0.036 [-0.010, 0.080] and +0.009 [-0.068, 0.084] in test AUC over census-only features. Only flipping shows a gain (+0.029 [0.005, 0.057]) [E5].
- **The rent-growth model is unstable.** A first draw of test blocks gave a gain of +0.097; the redraw gave +0.009. Treat it as no reliable gain [E5].
- **Past loss does not predict future loss.** Losing low-income households 1990-2000 scores AUC 0.48 for losing them 2000-2018 [E2].
- **Fast-rising neighborhoods did not keep rising.** Zip-level correlation between pre- and post-2019 price growth is -0.24 with non-overlapping windows [E9].
- **The UDP vulnerability flag ranks post-2018 price and rent growth backwards** (AUC 0.38 for both) [E5].
- **The three pressure outcomes are nearly uncorrelated** across tracts (flip vs appreciation 0.09, flip vs rent growth -0.13) [E5].
- **No stable gap by race in the backtest.** Recall 0.42 vs 0.51 on the test set; 0.48 vs 0.51 under leave-one-county-out with equal AUC [E3].
- **Large rent jumps at re-listing are as common in high-income typologies as low-income ones** (17.7% vs 17.6% above 10% a year); low-income tracts have more declines (28% vs 19%) [E8].
- **The tree models are not better than logistic regression** on 1,550 tracts; intervals overlap [E2].
- **The appreciation model is unusable in low-income tracts:** it found none of the 4 high-appreciation tracts in the low-income third of the test set [E6].

## Cross-workstream notes

- `movement/` E2 reports 23% of 2026 rental turnovers above 10% a year. Our E8 gives 20.4% for pairs ending 2025-26 and 16.2% across all years, using a simpler pair definition (consecutive "Listed for rent" events on the same listing id, 1-6 years apart). The two agree in direction; use `movement/` E2 for the turnover claim.
- Both workstreams find their models weakest for the most vulnerable groups.
- The outcome here (tract count of low-income households) cannot see anyone move. `movement/` follows people and flows; the two are complements.

## Methods

| # | Question | Main result | Script |
|---|---|---|---|
| E1 | What does the UDP landscape look like? | 18.8% of tracts lost low-income households | `code/e1_udp_landscape.py` |
| E2 | Can 1990/2000 data predict loss by 2018? | Test AUC 0.777-0.794; UDP flag 0.520 | `code/e2_backtest.py` |
| E2b | Does that hold under stricter labels? | 0.796 and 0.818 | `code/e2b_strict_label.py` |
| E3 | For whom does the backtest fail? | Recall 0.72 renter against 0.21 owner tracts | `code/e3_backtest_fairness.py` |
| E4 | Can Zillow homes be placed in tracts? | 99.5% matched; 30 of 30 hand check | `code/e4_zillow_tract_join.py` |
| E5 | Do 2018 conditions predict later pressure? | Zillow adds to census for flipping only | `code/e5_forward_test.py` |
| E6 | For whom does the forward model fail? | AUC 0.68 inside low-income typologies | `code/e6_forward_fairness.py` |
| E7 | Is the flipping pattern robust? | Same ranking under nine definitions | `code/e7_flip_sensitivity.py` |
| E8 | How much does rent jump at re-listing? | Median +3.0%/yr; 16.2% above 10% | `code/e8_rent_turnover.py` |
| E9 | Did fast-rising areas keep rising? | No; correlation -0.24 to -0.32 | `code/e9_price_trajectories.py` |
| E10 | How affordable are asking rents? | 51-62% of income in low-income typologies | `code/e10_affordability.py` |

## Advanced Track checklist

| Requirement | Status |
|---|---|
| Train a predictive model | Done: three model types on two tasks (E2, E5) |
| Baseline or published rule | Done: UDP flags, typology groups, one-variable and persistence baselines |
| Held-out test metrics | Done: stratified test (E2) and spatial-block test (E5), with one disclosed redraw |
| Three or more subgroups, with failures | Done: six groupings, 17 named tracts (E3, E6) |
| Labels, cleaning, joins, hand check | Done: label tested three ways (E2b); join documented and checked (E4) |
| Code runs from raw data to results | Done: full re-run reproduced all 21 E4-E10 tables exactly; E1-E3 matched |

## Limitations

1. The outcome counts low-income households; rising incomes, students and new construction move it, and it does not observe anyone moving out.
2. The backtest covers one 18-year period.
3. The forward test predicts market pressure; whether that displaced anyone needs newer census data.
4. Zillow histories exist only for homes listed or sold recently.
5. Rents are asking rents, and most rental events date from 2024-26.
6. A flip is defined from price and timing alone.
7. Several groups have fewer than ten positives, including San Francisco in the E5 flipping test set.
8. Race is available only as a non-white share.
9. Tree-based models differ in the fourth decimal between machines; logistic results reproduce exactly.
10. Eviction notices and building permits are not included. Open-data portals were not reachable from the analysis environment; a San Francisco case study is the planned next step.

## Sources

- Urban Displacement Project, displacement-typologies repository: https://github.com/urban-displacement/displacement-typologies
- Zillow property extract supplied for the datathon by Bright Data (The Bright Initiative)
- City and County of San Francisco, summary of AB 1482: https://sf.gov/information/california-tenant-protection-act-2019-ab-1482
