# E2 — Turnover "re-entry price" model (Advanced Track headline)

**Question.** When a household leaves a Bay Area rental, what does it cost to re-rent the *same* unit? Zillow
`priceHistory` lets us follow one unit across tenants: the jump from the last asking rent of tenancy *k* to the first
asking rent of tenancy *k+1* is the re-entry price a displaced household faces. California AB 1482 caps in-place
increases at 5% + CPI (max 10%/yr); turnover jumps above 10%/yr are the penalty for moving that the cap cannot touch.

## How to reproduce

```bash
python3 analysis/common/build_zillow.py              # raw Zillow CSVs -> analysis/cache/zillow.duckdb (once; not run here)
python3 analysis/e2_turnover_model/run_all.py         # everything below, from the cache (opened read-only), ~2 min
```
`run_all.py` downloads the two optional external files into `external/` if missing, then runs
`s01_build_sample.py` (sample + features) -> `s02_hand_check.py` (30-unit audit) -> `s03_model.py` (baselines, models,
temporal test, subgroups, failures, ZIP table, figures). Deterministic (fixed seeds, `deterministic=True` LightGBM,
stable sort before dedupe); two consecutive runs give identical metrics. Deps: python3, duckdb, pandas, scikit-learn,
lightgbm 4.7, matplotlib, pyshp, shapely, pyarrow, tabulate (README tables only).

## 1. Data decisions

Unit of analysis = a consecutive pair of rental listing episodes on the same `zpid` (table `turn`). An episode starts
at a "Listed for rent" event; `last_p` = last non-removal price of the episode (≈ rent the unit let at), `next_first`
= first ask of the next episode.

| step | pairs |
|---|---|
| all consecutive listing pairs (turn) | 86,293 |
| 1 <= start_gap_y <= 6 (drop same-vacancy relists & very old pairs) | 37,752 |
| 0.5 <= next_first/last_p <= 2.0 (drop typos/unit swaps) | 37,506 |
| residential homeType (drop LOT/MANUFACTURED/UNKNOWN) | 37,493 |
| has lat/lon/zipcode | 37,137 |
| dedupe identical histories at same location (floor-plan duplicate zpids) | 23,306 |

* **1 ≤ start_gap_y ≤ 6**: gaps under a year are mostly the *same vacancy* relisted (removed, then put back up) rather
  than a new tenant; > 6 years is sparse and spans unobserved tenancies.
* **0.5 ≤ ratio ≤ 2.0**: drops data-entry errors and unit swaps (0.1–99.9th pct of the ratio is 0.38–3.3).
* **Dedupe** removes 37% of rows: many APARTMENT zpids at one complex carry *identical* histories (same lat/lon,
  beds, baths, sqft, dates, prices). These are floor-plan or feed duplicates, not separate tenancies.
  **APARTMENT zpids may be floor plans at a complex, not units.** Two worst failures (94704) are the same building
  with different `beds` that survived the dedupe, and hand-check unit 2053541568 looks like a zpid reused across units.
  Some APARTMENT zpids do have their own sale history (individual condo-like units).
* The **time split** is on `next_start`: train < 2025-07-01 (12,502 pairs), val 2025-07…12 (1,645), **test ≥ 2026-01-01
  (9,159)**. The scrape makes 2026 by far the densest period.
* Management flag / company come from the property's *current* listing (`is_listed_by_management_company`,
  `listing_provided_by.company`), not the historical one, so they are proxies. "Large landlord" = management-company
  listing whose company manages ≥ 200 zpids in the dataset (Greystar, Irvine, Equity Residential, Prometheus, ...).
  Brokerages (Compass, Coldwell Banker) are excluded by the management flag.

### Hand check (30 random units: 15 APARTMENT + 15 other, seed 42)
`s02_hand_check.py` re-parses the raw `priceHistory` JSON in Python, independently of the SQL, and compares. Raw
histories (dates, events and prices only, no addresses) are in `outputs/hand_check_raw.txt`. I read all 30 and added
notes. **30/30 pairs reproduce exactly.** Verdicts: 21 correct, 8 correct-with-caveat, 1 questionable, 0 incorrect.
Recurring issues:
(a) Orphan "Listing removed" events with no price, clustered around Feb–Mar 2021, extend `end_d`. This corrupts
`gap_y` and the prior episode's duration but not the target, so those are **not** used as features.
(b) Revenue-managed complexes re-price daily, so the first ask is noisy (e.g. $3306 → $3631 two days later).
Robustness check: using the next episode's *final* ask gives a test median of 4.5%/yr vs 4.7%, and 22.6% vs 22.7% over the cap.
(c) The unit was sometimes sold between tenancies (2.8% of test pairs), giving the `sold_between` feature.
(d) An APARTMENT zpid can be reused for a different unit.

|       zpid | homeType      | pair                                   |   gap_y | sql_matches_reparse   | verdict             | why                                                                                                                              |
|-----------:|:--------------|:---------------------------------------|--------:|:----------------------|:--------------------|:---------------------------------------------------------------------------------------------------------------------------------|
| 2098824244 | APARTMENT     | 2021-01-21 $1495 -> 2023-12-14 $1495   |    2.89 | True                  | correct             | raw history matches pair; clean listed -> removed -> relisted                                                                    |
|   18451872 | APARTMENT     | 2021-04-04 $1750 -> 2023-01-30 $1850   |    1.82 | True                  | correct             | APARTMENT homeType but has individual sale history -> a real condo-like unit, not a floor plan                                   |
| 2078329446 | APARTMENT     | 2023-04-27 $3032 -> 2026-03-08 $3306   |    2.86 | True                  | correct-with-caveat | revenue-managed complex: next_first $3306 re-priced to $3631 two days later; first ask is noisy                                  |
| 2067349682 | APARTMENT     | 2023-12-17 $3700 -> 2026-03-03 $3780   |    2.21 | True                  | correct             | raw history matches pair; clean listed -> removed -> relisted                                                                    |
| 2070938950 | APARTMENT     | 2025-02-02 $2325 -> 2026-05-29 $2697   |    1.32 | True                  | correct-with-caveat | daily algorithmic price changes in next episode (n_changes>15); first ask then drifts down ~4%                                   |
| 2079225480 | APARTMENT     | 2023-06-28 $2465 -> 2025-01-11 $2512   |    1.54 | True                  | correct-with-caveat | daily algorithmic re-pricing in both episodes                                                                                    |
|  347329456 | APARTMENT     | 2024-04-08 $3625 -> 2026-09-12 $4421   |    2.43 | True                  | correct             | raw history matches pair; clean listed -> removed -> relisted                                                                    |
|   24821200 | APARTMENT     | 2022-08-05 $3900 -> 2026-08-01 $4200   |    3.99 | True                  | correct             | APARTMENT homeType with own sale history (single unit)                                                                           |
| 2053541568 | APARTMENT     | 2024-01-03 $4650 -> 2026-05-28 $3150   |    2.4  | True                  | questionable        | SF APARTMENT zpid: $4650 listed 2 days in 2024, $3150 in 2026; likely a different unit/floor plan or concession reusing the zpid |
| 2059843796 | APARTMENT     | 2023-05-12 $3595 -> 2026-09-03 $3595   |    3.31 | True                  | correct             | raw history matches pair; clean listed -> removed -> relisted                                                                    |
| 2085139243 | APARTMENT     | 2019-04-01 $4830 -> 2020-11-19 $2995   |    1.64 | True                  | correct             | SF $4830 (2019) -> $2995 (Nov 2020): real COVID-era SF rent collapse; same unit relisted at $5700 in 2026                        |
|  439200585 | APARTMENT     | 2024-08-19 $2250 -> 2025-09-11 $2250   |    1.06 | True                  | correct             | raw history matches pair; clean listed -> removed -> relisted                                                                    |
| 2084979225 | APARTMENT     | 2025-04-23 $1900 -> 2026-08-04 $1950   |    1.28 | True                  | correct             | raw history matches pair; clean listed -> removed -> relisted                                                                    |
| 2115433959 | APARTMENT     | 2025-04-01 $1750 -> 2026-09-05 $1750   |    1.43 | True                  | correct             | raw history matches pair; clean listed -> removed -> relisted                                                                    |
| 2095928910 | APARTMENT     | 2019-10-20 $2600 -> 2022-10-23 $2700   |    3.01 | True                  | correct-with-caveat | prior episode spans 521d                                                                                                         |
|   19650996 | SINGLE_FAMILY | 2023-01-23 $4700 -> 2024-05-30 $5500   |    1.35 | True                  | correct             | raw history matches pair; clean listed -> removed -> relisted                                                                    |
|   15740053 | SINGLE_FAMILY | 2018-06-06 $1800 -> 2021-10-21 $2300   |    3.38 | True                  | correct             | raw history matches pair; clean listed -> removed -> relisted                                                                    |
|   15856224 | SINGLE_FAMILY | 2013-07-06 $2400 -> 2017-09-19 $2800   |    4.21 | True                  | correct             | orphan 2021-03-21 removal after pair window; does not affect this pair                                                           |
|   24811992 | SINGLE_FAMILY | 2017-10-14 $4500 -> 2020-02-09 $4500   |    2.32 | True                  | correct             | flat $4500 over 2.3y; orphan 2021-03-24 removal after pair                                                                       |
|  111710903 | CONDO         | 2018-01-04 $4200 -> 2019-06-01 $4495   |    1.4  | True                  | correct             | SF condo $4600 cut to $4200 (2018) -> $4495 (2019); the following pair shows the COVID dip to $3300                              |
|   19580875 | SINGLE_FAMILY | 2024-11-01 $12250 -> 2025-11-03 $13000 |    1    | True                  | correct-with-caveat | luxury SFH $12250 -> $13000 ask, but next episode then cut to $9995: first ask overstates the re-let rent                        |
|  243210774 | SINGLE_FAMILY | 2022-10-12 $3950 -> 2026-07-30 $4500   |    3.8  | True                  | correct-with-caveat | prior episode has no removal; unit sold 2026-07 then relisted (new owner) -> turnover coincides with sale                        |
| 2112421739 | SINGLE_FAMILY | 2013-06-08 $1900 -> 2019-04-16 $2850   |    5.85 | True                  | correct             | raw history matches pair; clean listed -> removed -> relisted                                                                    |
|   19673282 | SINGLE_FAMILY | 2017-08-28 $3295 -> 2021-07-21 $3500   |    3.9  | True                  | correct             | raw history matches pair; clean listed -> removed -> relisted                                                                    |
|   24774183 | SINGLE_FAMILY | 2017-12-09 $4900 -> 2021-04-04 $5500   |    3.32 | True                  | correct-with-caveat | orphan 'Listing removed' (no price) on 2021-03-24 extends end_d; target unaffected, gap_y wrong                                  |
|   15640780 | CONDO         | 2020-08-07 $2300 -> 2022-12-08 $2200   |    2.34 | True                  | correct             | raw history matches pair; clean listed -> removed -> relisted                                                                    |
|  118259306 | SINGLE_FAMILY | 2019-03-30 $3300 -> 2022-08-27 $3595   |    3.41 | True                  | correct-with-caveat | orphan 'Listing removed' 2021-02-16 extends end_d; target unaffected                                                             |
| 2095886874 | TOWNHOUSE     | 2023-03-21 $2500 -> 2026-05-20 $2700   |    3.16 | True                  | correct             | raw history matches pair; clean listed -> removed -> relisted                                                                    |
|   18281200 | SINGLE_FAMILY | 2021-12-23 $2925 -> 2026-07-17 $3460   |    4.56 | True                  | correct             | prior episode cut $3345 -> $2925 before removal; last_p correctly takes the final ask; 4.6y gap                                  |
|   18493903 | SINGLE_FAMILY | 2023-09-18 $3500 -> 2025-07-23 $3500   |    1.85 | True                  | correct             | raw history matches pair; clean listed -> removed -> relisted                                                                    |

## 2. Targets
* Regression: `r = (next_first/last_p)^(1/start_gap_y) − 1`, the annualized turnover rent change. A log-ratio
  variant `log(ratio)/gap` was also trained: test MAE 0.0494 vs 0.0492, no gain, so we report `r`.
* Classification: `r > 0.10`, above the AB 1482 absolute maximum. Prevalence: train+val 10.3%, **test 22.7%** (big drift).

## 3. Features (all known at re-listing time; nothing from the next episode except its date)
Unit: beds, baths, sqft, age, homeType, lat, lon. Tenancy: `start_gap_y`, `log_last_p`, rent/sqft, prior-episode
repricing count `n_changes`, prior in-episode price cut, year of the previous listing, re-listing month, episode
number. Relative price: log rent minus the ZIP median, after removing the county market level, and rent/sqft vs the
ZIP median (both from training rows). Target encodings: ZIP mean r, county mean r, ZIP over-cap rate. These are
smoothed (k = 20) and fit on training rows only, with 5-fold out-of-fold values inside training. Landlord:
management-company flag and large-landlord flag. `sold_between`. **Market index** (from all 146k rental listing
starts): a county × quarter median of log first ask, net of the (ZIP, beds, apartment) cell means estimated
pre-2025-07. From it, `mkt_chg` = the annualized index change from the previous listing to the quarter *before*
re-listing, and `mkt_mom` = trailing 1-year momentum. **External:** Urban Displacement Project SF Bay typology (2018,
github `urban-displacement/displacement-typologies`), joined via point-in-polygon on 2018 TIGER tracts. It downloaded
easily and matched 98.5% of pairs. It is used as a feature (`typ_group`) and as a fairness subgroup.

## 4–6. Baselines, models, held-out temporal test
Tuning on val only: LightGBM grid over objective {l2, huber, l1} × leaves × min_child_samples with early stopping;
Ridge α; logistic C. Classification thresholds were set to maximize F1 on val. The final models are refit on
train+val with the chosen hyper-parameters and **scored once on test**. Picked: LGB regressor l1 objective, 63 leaves,
645 trees (val MAE 0.0402 vs ZIP-median 0.0463); Ridge α = 1000; logistic C = 0.1; LGB classifier val PR-AUC 0.361.

**Regression (test, n = 9,159, 2026 re-listings; r in fractions/yr)**

| model                         |    MAE |   RMSE |    bias |
|:------------------------------|-------:|-------:|--------:|
| Zero change (no jump)         | 0.0719 | 0.1059 | -0.0653 |
| Legal rule: CPI+5% capped 10% | 0.0609 | 0.0841 |  0.0107 |
| County market index change    | 0.059  | 0.0866 | -0.0453 |
| ZIP median of train r         | 0.0593 | 0.0933 | -0.0386 |
| Ridge (regularized linear)    | 0.0491 | 0.0773 | -0.0215 |
| LightGBM                      | 0.0492 | 0.0788 | -0.0273 |

**Classification: r > 10%/yr (test prevalence 22.7%)**

| model                            |   AUC |   PR_AUC |   precision |   recall |    F1 |     thr |
|:---------------------------------|------:|---------:|------------:|---------:|------:|--------:|
| Majority class (never over cap)  | 0.5   |    0.227 |       0     |    0     | 0     | nan     |
| ZIP over-cap rate (train)        | 0.682 |    0.414 |       0.308 |    0.704 | 0.429 |   0.097 |
| Logistic regression (L2)         | 0.814 |    0.611 |       0.547 |    0.561 | 0.554 |   0.188 |
| LightGBM classifier              | 0.815 |    0.592 |       0.578 |    0.531 | 0.554 |   0.156 |
| LightGBM regressor: pred r > 10% | 0.772 |    0.571 |       0.853 |    0.092 | 0.166 |   0.1   |

Honest read:
* **Regression.** Both learned models beat every baseline by about 1pp MAE: −17% vs the ZIP median, −19% vs the legal
  rule. But **Ridge ≈ LightGBM**: the nonlinear model adds nothing on test.
* **Classification.** The learned models roughly double the PR-AUC lift over chance (0.59–0.61 vs prevalence 0.23,
  and vs 0.41 for the ZIP rate), but **logistic regression matches or slightly beats LightGBM**.
* **Drift.** All models under-predict 2026, with bias −2.7pp for LightGBM. Test jumps (mean 6.5%) are about double
  training (3.4%) because of the 2025–26 rent acceleration, most of all the SF rebound. SF units last listed in 2025
  re-listed at a +23.5%/yr median in 2026. Trees cannot extrapolate a level shift.
* **Sensitivity.** Training on train only, without val, gives test MAE 0.0502 and PR-AUC 0.561. Excluding SF, LightGBM
  MAE is 0.0414 vs Ridge 0.0423 vs ZIP median 0.0474.
* Top LightGBM features by gain: market change `mkt_chg`, previous-listing year, gap, ZIP-relative rent, age, rent level.

## 7. Error and fairness (test; `outputs/subgroup_metrics_test.csv`, `figs/subgroup_bias.png`)

| group_set     | group                     |    n |   obs_mean_r |   pred_mean_r |   bias_lgb |   MAE_lgb |   MAE_zipmed |   obs_over_cap |   recall |   AUC |
|:--------------|:--------------------------|-----:|-------------:|--------------:|-----------:|----------:|-------------:|---------------:|---------:|------:|
| county        | Alameda County            | 2770 |        0.046 |         0.027 |     -0.019 |     0.043 |        0.048 |          0.151 |    0.305 | 0.749 |
| county        | Contra Costa County       |  990 |        0.036 |         0.028 |     -0.009 |     0.035 |        0.04  |          0.094 |    0.172 | 0.739 |
| county        | Marin County              |  175 |        0.052 |         0.03  |     -0.022 |     0.048 |        0.05  |          0.154 |    0.222 | 0.679 |
| county        | Napa County               |  152 |        0.014 |         0.016 |      0.003 |     0.045 |        0.049 |          0.046 |    0.429 | 0.772 |
| county        | San Francisco County      | 1052 |        0.171 |         0.074 |     -0.097 |     0.109 |        0.151 |          0.709 |    0.792 | 0.762 |
| county        | San Mateo County          |  932 |        0.083 |         0.05  |     -0.033 |     0.052 |        0.067 |          0.342 |    0.63  | 0.756 |
| county        | Santa Clara County        | 2245 |        0.061 |         0.041 |     -0.02  |     0.04  |        0.045 |          0.184 |    0.36  | 0.741 |
| county        | Solano County             |  425 |        0.025 |         0.026 |      0.001 |     0.029 |        0.035 |          0.031 |    0.077 | 0.804 |
| county        | Sonoma County             |  418 |        0.039 |         0.023 |     -0.016 |     0.038 |        0.039 |          0.096 |    0.225 | 0.693 |
| rent_quartile | Q1 lowest                 | 2189 |        0.059 |         0.038 |     -0.021 |     0.045 |        0.056 |          0.197 |    0.495 | 0.776 |
| rent_quartile | Q2                        | 2770 |        0.063 |         0.039 |     -0.024 |     0.047 |        0.056 |          0.212 |    0.498 | 0.812 |
| rent_quartile | Q3                        | 2469 |        0.065 |         0.039 |     -0.026 |     0.046 |        0.057 |          0.228 |    0.539 | 0.835 |
| rent_quartile | Q4 highest                | 1731 |        0.078 |         0.036 |     -0.042 |     0.062 |        0.071 |          0.285 |    0.593 | 0.831 |
| homeType      | APARTMENT                 | 7195 |        0.07  |         0.04  |     -0.03  |     0.052 |        0.064 |          0.254 |    0.543 | 0.806 |
| homeType      | CONDO                     |  170 |        0.071 |         0.044 |     -0.027 |     0.05  |        0.062 |          0.3   |    0.686 | 0.863 |
| homeType      | MULTI_FAMILY              |   39 |        0.04  |         0.048 |      0.008 |     0.048 |        0.054 |          0.154 |    0.667 | 0.859 |
| homeType      | SINGLE_FAMILY             | 1414 |        0.048 |         0.03  |     -0.018 |     0.039 |        0.043 |          0.116 |    0.378 | 0.794 |
| homeType      | TOWNHOUSE                 |  341 |        0.045 |         0.028 |     -0.017 |     0.035 |        0.039 |          0.085 |    0.345 | 0.816 |
| typ_group     | 1 Low-income/displacement | 1892 |        0.057 |         0.035 |     -0.022 |     0.049 |        0.059 |          0.211 |    0.598 | 0.82  |
| typ_group     | 2 Gentrifying             | 1211 |        0.075 |         0.038 |     -0.037 |     0.059 |        0.076 |          0.296 |    0.56  | 0.785 |
| typ_group     | 3 Moderate/mixed          | 3462 |        0.057 |         0.036 |     -0.021 |     0.043 |        0.049 |          0.18  |    0.364 | 0.77  |
| typ_group     | 4 Exclusive               | 2469 |        0.078 |         0.042 |     -0.036 |     0.054 |        0.066 |          0.268 |    0.615 | 0.864 |
| typ_group     | nan                       |  125 |        0.056 |         0.047 |     -0.009 |     0.039 |        0.054 |          0.248 |    0.935 | 0.946 |
| landlord      | large mgmt co             | 3699 |        0.076 |         0.046 |     -0.031 |     0.053 |        0.067 |          0.29  |    0.543 | 0.796 |
| landlord      | not mgmt co               | 4165 |        0.059 |         0.033 |     -0.026 |     0.046 |        0.054 |          0.181 |    0.508 | 0.837 |
| landlord      | other mgmt co             | 1295 |        0.054 |         0.033 |     -0.021 |     0.049 |        0.056 |          0.193 |    0.552 | 0.784 |

* **Low-rent units.** The level bias is *not* worse for the lowest rent quartile: −2.1pp vs −4.2pp for the highest
  quartile. But the classifier **misses half of the over-cap jumps on low-rent units**: recall 0.50 in Q1 vs 0.59 in Q4.
  The ranking is also weaker for them (AUC 0.78 vs 0.83).
* **Gentrifying areas: yes, the model under-predicts there most.** Gentrifying tracts: bias −3.7pp, MAE 5.9pp. Advanced
  gentrification: −5.0pp on an observed 9.7%/yr. Compare stable moderate/mixed tracts at −2.1pp. Exclusive tracts look
  similar (−3.6pp). Low-income / ongoing-displacement tracts are near the average (−2.2pp).
* **By county:** SF is the big failure, with observed mean 17.1% vs predicted 7.4%. Napa and Solano are well calibrated.
* **By landlord:** large management companies have the highest jumps (7.6% mean, 29% over the cap) and are under-predicted by 3.1pp.
* **Implication:** if used to target tenant assistance, the model would under-allocate to gentrifying tracts and to
  SF/San Mateo. Recalibrate on recent data first (see caveats).

**10 worst failures.** Rents are rounded to $250; no addresses are loaded anywhere; zpids are internal IDs.

|       zpid | county               | homeType_s    |   beds |   last_p |   next_first |   next_last |   start_gap_y |   mgmt | typology                  |    r |   pred_lgb |
|-----------:|:---------------------|:--------------|-------:|---------:|-------------:|------------:|--------------:|-------:|:--------------------------|-----:|-----------:|
|   18412195 | Contra Costa County  | TOWNHOUSE     |      3 |     5000 |        10000 |       10000 |          1.06 |      0 | At risk of exclusive      | 92   |        4.5 |
|  448311698 | Alameda County       | APARTMENT     |      2 |     2250 |         4250 |        4250 |          1.14 |      1 | Low-income/susceptible    | 81.2 |        1.8 |
|  463496508 | Alameda County       | APARTMENT     |      3 |     2250 |         4250 |        4250 |          1.14 |      1 | Low-income/susceptible    | 81.2 |        1.8 |
|  240884988 | Contra Costa County  | TOWNHOUSE     |      2 |     2000 |         3750 |        3750 |          1.13 |      0 | Stable moderate/mixed     | 79.8 |        3.8 |
|   19597930 | Santa Clara County   | SINGLE_FAMILY |      4 |     6750 |        13500 |        9000 |          1.19 |      0 | Stable moderate/mixed     | 79.2 |        4.6 |
| 2119910832 | San Francisco County | APARTMENT     |      0 |     2500 |         4500 |        4000 |          1.18 |      0 | At risk of exclusive      | 61.2 |        5.7 |
|   15518067 | San Mateo County     | SINGLE_FAMILY |      2 |     3750 |         6000 |        5250 |          1.05 |      0 | Becoming exclusive        | 57.9 |        4.2 |
| 2076948333 | San Francisco County | APARTMENT     |      2 |     3500 |         6500 |        6500 |          1.25 |      1 | Stable/advanced exclusive | 63.1 |       14.1 |
| 2083968953 | San Francisco County | APARTMENT     |      0 |     2500 |         4500 |        4500 |          1.3  |      0 | At risk of exclusive      | 54.5 |        5.7 |
|   15080053 | San Francisco County | APARTMENT     |      2 |     9500 |        15000 |       15000 |          1.08 |      0 | At risk of exclusive      | 52.4 |        3.9 |

Profile of the top 2% of errors vs the rest (`outputs/failure_profile_test.csv`): shorter gaps (1.36 vs 2.18 yr), fewer
prior price changes, higher rents, and 82% APARTMENT. Most are near-doublings over about a year. These are likely a
different unit or floor plan under the same zpid, a furnished or short-term re-listing, or a renovation. All are
unpredictable from the features.

## 8. Product: ZIP-level re-entry cost (`outputs/zip_reentry_cost.csv`)
One row per ZIP, built from 2026 turnovers (out-of-sample predictions), 256 ZIPs. `low_n_flag` marks the 123 ZIPs
with fewer than 20 turnovers. Columns:
* Observed and predicted median annualized jump.
* `*_premium_month_vs_cpi`: the median monthly $ a leaver pays to re-rent the same unit, above what a stayer would
  pay if their rent had risen with CPI. It is `next_first − last_p·(1+CPI)^gap`.
* `obs_median_premium_month_vs_legal_max`: the same, vs the *maximum* legal in-place path (5% + CPI). This is a lower bound.
* Observed and predicted share of turnovers above the 10% cap.

Across ZIPs with n ≥ 20, the predicted and observed medians correlate at r = 0.84, and the share over the cap at
r = 0.80, even though the level is under-predicted. Across all 2026 turnovers, the median premium is **+$118/month**
(mean +$262).

Top 10 ZIPs, n ≥ 20 (all San Francisco):

|   zipcode | county               |   n_turnovers |   median_prev_rent |   obs_median_jump_annual |   pred_median_jump_annual |   obs_median_premium_month_vs_cpi |   obs_share_over_10pct_cap |
|----------:|:---------------------|--------------:|-------------------:|-------------------------:|--------------------------:|----------------------------------:|---------------------------:|
|     94107 | San Francisco County |           138 |             3654   |                     22.5 |                       8   |                              1034 |                         87 |
|     94133 | San Francisco County |            26 |             3150   |                     20.6 |                       8.8 |                              1229 |                         85 |
|     94105 | San Francisco County |            88 |             3697.5 |                     19.7 |                       8.7 |                              1337 |                         85 |
|     94131 | San Francisco County |            24 |             3965   |                     19.1 |                       6.7 |                              1585 |                         83 |
|     94158 | San Francisco County |            32 |             3887   |                     17.9 |                       7.9 |                              1171 |                         94 |
|     94115 | San Francisco County |            43 |             2895   |                     16.4 |                       7.8 |                              1186 |                         77 |
|     94103 | San Francisco County |           148 |             3430   |                     16.3 |                       7.8 |                               757 |                         79 |
|     94123 | San Francisco County |            42 |             3445   |                     16.2 |                       6.7 |                              1347 |                         83 |
|     94110 | San Francisco County |            50 |             3400   |                     13.8 |                       6.2 |                               838 |                         64 |
|     94109 | San Francisco County |           170 |             2345   |                     13.4 |                       7.4 |                               629 |                         60 |

Bottom 10:

|   zipcode | county              |   n_turnovers |   median_prev_rent |   obs_median_jump_annual |   pred_median_jump_annual |   obs_median_premium_month_vs_cpi |   obs_share_over_10pct_cap |
|----------:|:--------------------|--------------:|-------------------:|-------------------------:|--------------------------:|----------------------------------:|---------------------------:|
|     94558 | Napa County         |            82 |             2801   |                      1.5 |                       1   |                               -53 |                          0 |
|     95476 | Sonoma County       |            25 |             2900   |                      1.4 |                       1.6 |                               -87 |                          8 |
|     94704 | Alameda County      |           280 |             3200   |                      1.2 |                       1.5 |                               -71 |                         11 |
|     95401 | Sonoma County       |            31 |             2299   |                      1.2 |                       1.8 |                               -37 |                          3 |
|     94702 | Alameda County      |            32 |             2895   |                      1.2 |                       2.1 |                              -126 |                         16 |
|     94577 | Alameda County      |            56 |             2275   |                      0.6 |                       2.6 |                               -55 |                         16 |
|     94530 | Contra Costa County |            22 |             2518   |                      0.4 |                       2.4 |                               -91 |                          5 |
|     94559 | Napa County         |            35 |             2700   |                      0   |                       1.8 |                              -119 |                          6 |
|     94806 | Contra Costa County |            46 |             2232.5 |                      0   |                       3   |                               -61 |                          0 |
|     94709 | Alameda County      |            66 |             2897.5 |                      0   |                       0.6 |                               -91 |                          2 |

Maps: `figs/map_zip_reentry_jump.png` (observed vs predicted) and `figs/map_zip_share_over_cap.png`.

## Caveats
* These are **asking rents**, not signed leases. Concessions are invisible, and "Listing removed" ≠ leased.
* A pair can span unobserved tenancies. Annualizing helps, but the jump is then not a single-turnover move.
* APARTMENT zpids ≈ floor plans, so a "same unit" may be a sibling unit. The dedupe and ratio filter only partly fix this.
* Heavy 2025–26 sampling, and level drift: the 2026 jump is roughly 2× history. Treat the model's level as a lower
  bound; its ranking (AUC 0.81, ZIP correlation 0.84) is more trustworthy. A production version should recalibrate on
  the most recent quarter.
* The CPI series in `common.py` is approximate (rounded SF-area CPI-U). The pre-2020 cap is a counterfactual, since
  AB 1482 started in 2020. Single-family homes owned by individuals are often exempt from AB 1482. The 10% line is a
  benchmark, not a legal violation finding: turnover resets are legal under AB 1482 (vacancy decontrol).
* The management flag reflects the current listing, not the historical one.
* The UDP typology is from 2018 data, so it predates the COVID shock and the 2025–26 rebound.

## Advanced Track checklist
| requirement | where |
|---|---|
| Model | LightGBM regressor + classifier, Ridge, logistic: `s03_model.py` |
| Baseline(s) | zero change, legal rule (CPI+5% ≤ 10%), county market index, ZIP median of train r; majority class, ZIP over-cap rate, logistic: `outputs/metrics_*_test.csv`, `figs/metrics_vs_baselines.png` |
| Held-out evaluation | temporal: train < 2025-07, val 2025-H2 (all tuning and thresholds), test 2026 scored once; MAE/RMSE/bias, AUC/PR-AUC/P/R/F1; plus spatial holdout (leave-one-county-out, ZIP blocks) and bootstrap CIs: Robustness §R2, §R4 |
| ≥3 subgroups + failure examples | county, rent quartile, homeType, UDP displacement typology (coarse + fine), landlord type: `outputs/subgroup_metrics_test.csv`; 10 worst failures `outputs/worst_failures_test.csv` + `failure_profile_test.csv` |
| Data decisions + hand check | §1, `outputs/sample_flow.csv`, `outputs/hand_check.csv` (30 units, verdict and why), `outputs/hand_check_raw.txt` |
| Reproducibility | `run_all.py` single entry point from cache; cache from `analysis/common/build_zillow.py`; deterministic; `outputs/run_log.json`; robustness: `run_robustness.py` (s04–s07) -> `outputs/robustness/`, `figs/robustness/` |
| Robustness | effective-rent target (concessions), spatial holdout, drift features + recalibration, bootstrap/seeds: Robustness section |
| Product output | `outputs/zip_reentry_cost.csv`, `figs/map_zip_*.png` |

## Files
`run_all.py`, `common.py`, `s01_build_sample.py`, `s02_hand_check.py`, `s03_model.py`. In `outputs/`: `sample.parquet`,
`sample_flow.csv`, `hand_check.csv`, `hand_check_raw.txt`, `metrics_regression_test.csv`,
`metrics_classification_test.csv`, `subgroup_metrics_test.csv`, `worst_failures_test.csv`, `failure_profile_test.csv`,
`feature_importance_lgb_reg.csv`, `zip_reentry_cost.csv`, `test_predictions.parquet`, `run_log.json`. In `figs/`:
`map_zip_reentry_jump.png`, `map_zip_share_over_cap.png`, `metrics_vs_baselines.png`, `subgroup_bias.png`,
`calibration_test.png`, `feature_importance.png`. In `external/`: UDP typology CSV and TIGER tracts.

## Robustness (added; `run_robustness.py` -> `outputs/robustness/`, `figs/robustness/`)
`python3 analysis/e2_turnover_model/run_robustness.py` (~4 min, after `run_all.py`) runs `s04_effective_rent.py`,
`s05_spatial_holdout.py`, `s06_drift.py`, `s07_bootstrap.py` (shared helpers in `robustness_common.py`). Nothing above
is overwritten. All hyper-parameters are the val-tuned ones from `outputs/run_log.json` (s06 re-tunes on val for its new
feature set with the same grid). The 2026 test set is only scored, never used for selection. Refitting the s03 models
inside these scripts reproduces `test_predictions.parquet` exactly (asserted in s06).

### R1. Effective-rent target (free-rent concessions; `s04`, `eff_*.csv`, `figs/robustness/eff_vs_ask_subgroups.png`)
Concession weeks are parsed with E6's regex (`analysis/e6_unit_replacement/textflags.py`) from the *current* FOR_RENT
listing's description + special_offer, and attached only when the pair's next episode **is** that current listing
(`ep + 1` = last episode). **Assumption:** 12-month lease, free weeks spread over the year, so effective first-year next
rent = `next_first × (1 − weeks/52)`. The prior tenancy's concession is unobserved (treated as none), and pairs without
current-listing text are treated as no concession, so effective jumps are an upper bound on the true effective jump.
After a 12-month lease the concession burns off, so this is a first-year view.

* **Coverage:** 7,582 of 9,159 test pairs (83%) have their next episode = current listing; **982 (10.7%) carry a parsed
  concession** (median 4.3 weeks). Val: 86 pairs, train: 3, so a concession effect cannot be learned from training data.
* **Headline: ~83% of the measured turnover premium survives on an effective basis.** The mean jump above CPI goes from 3.93
  to 3.25pp/yr (83%). The mean $ premium vs a CPI-indexed stay goes from +$262 to +$232/month (88%). The median premium goes from $118 to $94.
  The share over the 10% cap goes from 22.7% to 20.9%. **In the 982 concession pairs, none survives:** the mean jump goes from 6.6% to 0.3%/yr, the median from
  +5.6% to −0.4%, and over the cap from 26.8% to 10.6%. The mean premium goes from +$154 to −$131/month (E6 reported +5.6% / −0.5% on its slightly different sample).
* **Subgroups:** management-company listings have 17.5% concession pairs vs 2.5% for individuals. Their mean jump goes from 7.1% to 5.9%
  (premium $226 → $175), while individual landlords barely move (5.9% → 5.8%). So on an effective basis the corporate
  "excess" over individual landlords (+1.2pp asking) all but disappears (+0.1pp). Alameda (17.7% concessions; 4.6% → 3.4%) and
  Santa Clara (10%) move most. **SF barely moves (17.1% → 16.7%, only 5% of pairs with concessions): the SF turnover shock is not
  a concession artefact.**

| test MAE (all 9,159) | asking target | effective target | effective, 982 concession pairs |
|---|---|---|---|
| Legal rule | 0.0609 | 0.0640 | 0.0905 |
| ZIP median | 0.0593 | 0.0593 | 0.0648 |
| Ridge (s03) | 0.0491 | 0.0501 | 0.0670 |
| LightGBM (s03) | 0.0492 | 0.0499 | 0.0641 |
| LightGBM + concession flag/weeks (trained on effective target) | 0.0511 | **0.0480** | **0.0505** |
| LightGBM s03 prediction × posted concession (mechanical) | 0.0535 | 0.0488 | 0.0538 |

Classifier AUC barely changes when the target becomes effective over-cap (LightGBM 0.815 → 0.814). Adding concession features
does not improve AUC (0.814), because the flag has almost no training support. The concession is a feature of the new listing,
posted at re-listing time, so it is legitimately known when predicting.

### R2. Spatial holdout (`s05`, `spatial_loco.csv`, `spatial_zipblocks.csv`, `figs/robustness/spatial_loco.png`)
Fit on train+val pairs (re-listed before 2026) of 8 counties and score the 9th county's 2026 pairs. The target encodings
and ZIP-relative rent are refit without the held-out county. The county market index is still computed from the held-out county's own
listing asks (public data, with no turnover outcomes). The "ZIP median" baseline then has no rows for the held-out ZIPs and falls back to the global median of the training counties.

| held out | n | obs mean r | LGB MAE | Ridge MAE | median baseline | legal rule | LGB, county seen (s03) | LGB clf AUC (seen) |
|---|---|---|---|---|---|---|---|---|
| **San Francisco** | 1,052 | 17.1% | 0.1425 | 0.1233 | 0.1481 | **0.1113** | 0.1091 | 0.672 (0.762) |
| San Mateo | 932 | 8.3% | 0.0542 | 0.0516 | 0.0663 | 0.0507 | 0.0516 | 0.763 (0.756) |
| Santa Clara | 2,245 | 6.1% | 0.0427 | 0.0420 | 0.0475 | 0.0450 | 0.0401 | 0.722 (0.741) |
| Alameda | 2,770 | 4.6% | 0.0440 | 0.0432 | 0.0459 | 0.0591 | 0.0431 | 0.738 (0.749) |
| Contra Costa | 990 | 3.6% | 0.0378 | 0.0395 | 0.0375 | 0.0574 | 0.0354 | 0.715 (0.739) |
| Marin / Napa / Solano / Sonoma | 175 / 152 / 425 / 418 | | 0.050 / 0.046 / 0.035 / 0.038 | | 0.050 / 0.047 / **0.029** / 0.038 | 0.06–0.08 | 0.048 / 0.045 / 0.029 / 0.038 | 0.62–0.71 |
| **pooled, all 9** | 9,159 | 6.5% | 0.0548 | 0.0525 | 0.0581 | 0.0609 | 0.0492 | 0.720 (0.815) |
| pooled excl. SF | 8,107 | 5.2% | 0.0434 | 0.0433 | 0.0464 | 0.0543 | 0.0414 | 0.727 (0.770) |
| ZIP blocks (25 KMeans blocks, 5-fold), pooled | 9,159 | | 0.0550 | 0.0524 | 0.0591 | 0.0609 | 0.0492 | 0.722 (0.815) |

* **SF held out is the failure case.** With SF held out, LightGBM's bias is −13.6pp, and it loses to the trivial legal rule (0.111). It even does
  worse than the temporal model that saw SF's history (0.109). Nothing in the other 8 counties anticipates SF's 2026 rebound.
* Outside SF, the spatial penalty is modest: MAE 0.0434 vs 0.0414 with the county seen. The models still beat the median
  baseline (0.0464) and the legal rule (0.0543). But the median baseline wins in Solano (0.029 vs 0.035), and by <0.001 in Contra Costa and Sonoma.
* Ranking degrades more than level: pooled AUC falls from 0.815 to 0.72. Much of the classifier's skill is in the local
  target encodings, which a new area does not have.

### R3. Drift handling (`s06`, `drift_*.csv`, `figs/robustness/calibration_before_after.png`)
(a) **Recent-market features:** trailing 6-month (183-day) median observed jump r of other pairs in the same ZIP (n ≥ 5)
and the same county (n ≥ 10), plus the county share over the cap. They use only pairs re-listed **strictly before** this pair's `next_start`
(a pair's r is known on its own re-listing day). For test rows this is a rolling/online feature, so a Nov-2026 prediction uses realized
May–Oct 2026 jumps. A *frozen* variant computes the test rows' features as of 2026-01-01, using no 2026 outcomes at all.
(b) **Recalibration on 2025-Q4** (n = 802): the base model is fit on pairs re-listed before 2025-10-01. Then OLS `r ~ a + b·pred` (and a
median shift) is fit on the Q4 predictions and applied to test. The classifier uses Platt scaling.

| model (test, n = 9,159) | MAE | bias | clf AUC |
|---|---|---|---|
| LightGBM / LGB clf (s03) | 0.0492 | −0.0273 | 0.815 |
| Ridge (s03) | 0.0491 | −0.0215 | — |
| LightGBM fit < 2025-10, raw → recalibrated on Q4 (linear) | 0.0500 → 0.0491 | −0.0270 → −0.0219 | 0.801 (Platt: Brier 0.167 → 0.157) |
| LightGBM + recent-market (rolling) | 0.0468 | −0.0217 | **0.837** |
| **Ridge + recent-market (rolling)** | **0.0455** | **−0.0098** | 0.826 (logistic) |
| LightGBM / Ridge + recent-market (frozen at 2026-01-01) | 0.0481 / 0.0475 | −0.0270 / −0.0192 | 0.836 |
| LightGBM + recent, fit < 2025-10, recalibrated on Q4 | 0.0469 | −0.0157 | 0.822 |

* **Recalibration on the last val quarter barely helps.** 2025-Q4 itself was calm (mean r 3.6%, vs a model mean of 3.2%), so the map
  it learns (intercept +0.2pp, slope 1.08) cannot anticipate the 2026 jump to 6.5%. The calibration plot moves only slightly
  toward the diagonal, and the top decile is still under-predicted by about 6pp.
* **The recent-market feature helps more** (val MAE 0.0396 vs 0.0402 when tuning). On test, Ridge+recent cuts the MAE by 0.0036
  (95% CI −0.0040 to −0.0032) and the bias from −2.2 to −1.0pp. About 40–45% of the gain remains in the frozen variant, so
  part of it comes from information that is genuinely *earlier* than 2026, and part from rolling 2026 data.
* **Fairness gap (bias in Gentrifying tracts):** LightGBM −3.75pp → −2.80pp (rolling recent) → −2.35pp (recent + Q4 recal).
  Ridge −3.87 → −2.19pp. Advanced gentrification goes from −5.05 to −3.67pp (LGB recent + recal) and −2.62pp (Ridge recent). **The absolute under-prediction
  shrinks**, but the gap vs stable moderate/mixed tracts only partly closes: LGB −1.66 → −1.14 to −1.39pp, Ridge −2.48 → −1.67pp.
  Gentrifying tracts remain the most under-predicted typology group for Ridge+recent (Exclusive is slightly worse for LGB+recent). SF bias goes from −9.7 to −8.3pp (LGB recent) and −2.7pp (Ridge recent).

### R4. Uncertainty (`s07`, `bootstrap_ci_test.csv`, `seed_variability_test.csv`, `figs/robustness/bootstrap_ci.png`)
95% percentile CIs from B = 2,000 row resamples and B = 1,000 ZIP-cluster resamples (pairs in a ZIP share a market, so the cluster CIs are the honest ones).

| test metric | estimate | row CI | ZIP-cluster CI |
|---|---|---|---|
| MAE LightGBM (s03) | 0.0492 | 0.0479–0.0505 | 0.0447–0.0541 |
| MAE Ridge (s03) | 0.0491 | 0.0479–0.0503 | 0.0448–0.0536 |
| MAE ZIP median | 0.0593 | 0.0579–0.0608 | 0.0529–0.0669 |
| MAE legal rule | 0.0609 | 0.0597–0.0621 | 0.0568–0.0652 |
| MAE Ridge + recent (s06) | 0.0455 | 0.0444–0.0466 | 0.0424–0.0488 |
| Δ MAE LightGBM − ZIP median | −0.0101 | −0.0107 to −0.0096 | −0.0129 to −0.0077 |
| Δ MAE LightGBM − Ridge | +0.0001 | −0.0003 to +0.0006 | −0.0008 to +0.0009 |
| AUC LightGBM clf (s03) | 0.815 | 0.804–0.825 | 0.786–0.842 |
| AUC ZIP over-cap rate | 0.682 | 0.668–0.695 | 0.622–0.733 |
| Δ AUC LightGBM clf − ZIP rate | +0.133 | 0.120–0.146 | 0.099–0.177 |
| Δ AUC LGB clf + recent − LGB clf | +0.022 | 0.017–0.027 | 0.013–0.030 |

The gain over the best baselines is clearly significant even with ZIP clustering. LightGBM vs Ridge is a tie. Across 6
LightGBM seeds (same hyper-parameters), test MAE is 0.0490 ± 0.0002 and AUC 0.812 ± 0.004 (sd).

### Robustness takeaways
1. On an effective (concession-net) basis about 83% of the turnover premium survives region-wide. For concession pairs
   (mostly corporate, newer buildings) it vanishes in year one, and the SF shock is untouched.
2. The model does not transfer to an unseen county with a different trajectory: with SF held out it loses to the legal rule.
   Elsewhere it transfers with a small penalty.
3. Recalibrating on the most recent *validation* quarter cannot fix a level shift that had not yet happened. A no-leak trailing
   recent-market feature is the most effective drift fix (MAE −7%, bias halved for Ridge), and it shrinks, but does not remove,
   the under-prediction in gentrifying tracts.
4. Headline metrics are stable to resampling and seeds; Ridge ≈ LightGBM throughout.
