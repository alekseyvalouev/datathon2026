# Backtest: can year-2000 conditions predict loss of low-income households by 2018? (E1, E2, E2b, E3)

Scripts: `code/e1_udp_landscape.py`, `code/e2_backtest.py`, `code/e2b_strict_label.py`, `code/e3_backtest_fairness.py`. Seed 42 everywhere.

## Data decisions
- Source: `SanFrancisco_typology_output.csv` from the UDP repository (2,109 tracts, 306 columns, 13 counties).
- Kept the nine Bay Area county FIPS codes and `pop00flag == 1`: **1,550 tracts**. GEOID zero-padded to 11 characters; infinities set to missing (28 missing feature cells, median-imputed inside the model pipeline).
- Label `lostli_18` equals `ch_all_li_count_00_18 < 0` for all 1,550 tracts (checked). 292 positives (18.8%).
- **Leakage check.** Every Ongoing Displacement and Becoming Exclusive tract has `lostli_18 = 1`; every Low-Income/Susceptible tract has 0. The 2018 typology and all 2012/2018 columns are excluded from features.
- Features: 19 census variables for 1990 and 2000 (low-income share, non-white share, renter share, college share, real rent, home value and income, and 1990-2000 changes).

## Design
- 25% test split (388 tracts, 73 positives), stratified by county and label, drawn before modelling and never used for tuning.
- Hyper-parameters chosen on the other 1,162 tracts with county-held-out 5-fold cross-validation.
- Leave-one-county-out predictions for all 1,550 tracts, used for the county results and the map.
- Baselines: UDP flags computed for 2000 (`vul_gent_00`, `hotmarket_00`, `gent_90_00`, `lostli_00`) and renter share alone.

## Results
| Model | CV AUC (dev) | Test AUC [95% bootstrap] | Test AP | Precision = recall at top 73 |
|---|---|---|---|---|
| Logistic regression, C=0.1 (selected) | 0.782 | 0.777 [0.715, 0.831] | 0.465 | 0.479 |
| Random forest | 0.771 | 0.788 [0.730, 0.841] | 0.467 | 0.397 |
| Gradient boosting | 0.764 | 0.794 [0.739, 0.843] | 0.508 | 0.466 |
| Renter share 2000 alone | 0.702 | 0.661 [0.583, 0.728] | 0.315 | 0.329 |
| UDP rule: vul_gent_00 + hotmarket_00 | 0.562 | 0.524 | 0.202 | 0.192 |
| UDP vul_gent_00 flag | 0.549 | 0.520 [0.467, 0.580] | 0.195 | 0.178 |
| UDP lostli_00 | 0.484 | 0.481 | 0.184 | 0.137 |

- Random ranking has AP 0.188. The three models overlap; logistic regression was selected on dev CV and is used downstream.
- Leave-one-county-out AUC 0.783 (AP 0.459), from 0.670 in Solano (7 positives) to 0.787 in Alameda.
- **Calibration.** Raw scores overstate risk because classes were re-weighted. After isotonic recalibration on dev folds the five test quintiles read 4.1 / 7.7 / 12.2 / 21.6 / 51.8% predicted against 3.8 / 6.5 / 15.4 / 22.1 / 46.2% observed. Brier 0.1305 against 0.1527 for the base rate.
- **Drivers** (permutation importance on test, AUC drop): low-income share 2000 (0.090), home value 2000 (0.046), college share 2000 (0.041), non-white share 2000 (0.041; the coefficient is negative, so a higher non-white share lowers the predicted risk).
- **Null.** Loss in 1990-2000 does not predict loss in 2000-2018 (AUC 0.48).

## Label robustness (E2b)
Same split and features; C re-chosen by dev CV for each label.

| Label | Positives (all / test) | Logistic test AUC [95%] | Test AP | UDP flag AUC |
|---|---|---|---|---|
| Any loss (`lostli_18`) | 292 / 73 | 0.777 [0.715, 0.831] | 0.465 | 0.520 |
| Lost 10% or more of year-2000 low-income households | 147 / 30 | 0.796 [0.721, 0.864] | 0.235 | 0.452 |
| Low-income share of households fell 5+ points | 128 / 30 | 0.818 [0.720, 0.889] | 0.325 | 0.615 |

- 145 of the 292 base positives lost under 10%. 34 tracts meet the share label without a count loss, and 198 base positives do not meet it.
- With only 30 test positives the intervals are wide; the ranking result holds, the precision figures are weak.

## Fairness and failures (E3)
One regional threshold: flag the top share of tracts equal to the base rate. Test set, leave-one-county-out in brackets.

| Group | n | Positives | AUC | Recall | False-positive rate |
|---|---|---|---|---|---|
| Majority renter (2000) | 138 | 39 | 0.782 | 0.72 [0.71] | 0.29 [0.29] |
| Majority owner | 250 | 34 | 0.741 | 0.21 [0.20] | 0.04 [0.05] |
| Low-income third | 130 | 25 | 0.780 | 0.60 [0.64] | 0.21 [0.18] |
| Middle-income third | 134 | 29 | 0.771 | 0.45 [0.40] | 0.08 [0.08] |
| High-income third | 124 | 19 | 0.799 | 0.37 [0.40] | 0.08 [0.09] |
| Majority people of color | 165 | 26 | 0.747 | 0.42 [0.48] | 0.09 [0.09] |
| Majority white | 223 | 47 | 0.789 | 0.51 [0.51] | 0.15 [0.14] |
| Near rail | 137 | 36 | 0.790 | 0.64 [0.65] | 0.26 [0.22] |
| No rail | 251 | 37 | 0.738 | 0.32 [0.33] | 0.06 [0.07] |

- By county (leave-one-county-out): 0 of 7 losses caught in Solano, 0 of 8 in Napa, 6 of 33 in San Mateo; San Francisco recall 0.80 with a 39% false-positive rate.
- Flagging the 292 highest leave-one-county-out scores gives 146 caught, 146 missed and 146 false alarms.

Named failures (test set; score is the calibrated probability). Full list in `results/e3_failure_tracts.csv`.

| Tract | Place | Model | Outcome | Likely reason (interpretation) |
|---|---|---|---|---|
| 06081601700 | South San Francisco | 6% | Lost 14 of 338 low-income households | 16% renters; owner-suburb profile |
| 06001442100 | Fremont | 6% | Lost 17 of 217 | High income, 11% renters |
| 06001440331 | Union City | 8% | Lost 2 of 261 | Loss under 1%: the label flips on noise |
| 06001402800 | Oakland | 66% | Gained 379 | Households doubled; low-income share fell 90% to 57% but the count rose |
| 06075010100 | San Francisco | 66% | Gained 256 | 86% renters, rail, high values: the classic profile, yet low-income households increased |
| 06085511609 | Palo Alto | 66% | Gained 423 | 99% renters, very low incomes, households 163 to 1,731: looks like student housing |

## Limits
- The label counts low-income households. Rising incomes, students, new construction and tract growth move it; it does not observe a move.
- One historical period of 18 years. It shows what was predictable then.
- The UDP flags were built to classify neighborhood stages, not to forecast this label.
- Race is available only as a non-white share.
- Subgroup thresholds are regional; group-specific thresholds were not explored.
