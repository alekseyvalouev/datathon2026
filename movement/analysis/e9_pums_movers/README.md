# E9: Following people with ACS PUMS (Bay leavers vs. comparable stayers)

Theme: *Exit hides inequality: follow people, not places.* CPL's "Priced Out of the Bay" (2026) credit-panel
study finds Bay leavers gain homeownership but end up in poorer neighborhoods and weaker school districts. Here
we use ACS PUMS microdata, the closest public stand-in for following people, to compare adults who lived in
the Bay one year ago and left with comparable adults who stayed. We look at outcomes CPL does not measure:
rent burden, overcrowding, commute, employment, wages and poverty.

## Run

```
python3 -m pip install xlrd   # only extra dependency (reads the IPUMS .xls crosswalks)
python3 -I run_all.py         # downloads ~2.5 GB, then runs everything (~2 min after download)
```

`run_all.py` runs, in order, `src/01_download_extract.py` (downloads the US person and housing 1-year files for
2022–2024 plus the IPUMS crosswalks into `raw/`; streams the zips and keeps only people who live in CA now or
lived in CA one year ago, saving them to `data/*.parquet`), `02_build.py`, `03_estimate.py`, `04_exit_model.py`,
`05_figures.py` and `06_verify.py`. Set `E9_YEARS` to change the years. Only 2022+ is supported without changes,
because those years share 2020 PUMA and MIGPUMA codes.

## Data and definitions

- **ACS 1-year PUMS 2022, 2023, 2024, full US person and housing files.** These include every out-of-state
  destination, not just a subset. 2020 is skipped as required. 2021 is skipped because it uses 2010 PUMAs.
- **Bay origin.** The 2020 MIGPUMAs from the IPUMS `county_migpuma_pwpuma_2022.xls` and
  `puma_migpuma1_pwpuma00_2020.xls` files. Each of the 9 counties is its own MIGPUMA: Alameda 00100,
  Contra Costa 01300, Marin 04100, Napa 05500, SF 07500, San Mateo 08100, Santa Clara 08500, Solano 09500,
  Sonoma 09700. The code checks that no MIGPUMA mixes Bay and non-Bay counties.
- **Population.** Adults 18–64 living in households (not group quarters) who lived in the Bay one year ago.
  Movers from abroad (MIG=2) are excluded.
- **Groups.** These are pooled 2022–24 counts. Unweighted n is the number of survey records; "/yr" is the
  weighted number of people per year. See `outputs/group_sizes.csv`.

  | group | definition | unweighted n | weighted/yr |
  |---|---|---|---|
  | stay_same | same house (MIG=1), PUMA in the Bay | 118,561 | ~4.00M |
  | stay_moved_bay | moved, origin and current PUMA both in the Bay | 12,174 | ~452k |
  | left_saccv | now in Sacramento region or Central Valley (counties 007,011,017,019,021,029,031,039,047,061,067,077,089,099,101,103,107,113,115) | 1,156 | ~45k |
  | left_othca | now elsewhere in CA | 1,521 | ~53k |
  | left_ca | now in another state | 2,739 | ~105k |

  Stayers are stay_same plus stay_moved_bay. Top out-of-state destinations (weighted share): TX 12.0%,
  NY 9.7%, WA 8.4%, OR 6.3%, NV 5.5%, FL 5.4%, AZ 4.2%. See `outputs/left_ca_destination_states.csv`.
- **Outcomes.** All are measured after the move.
  - Homeownership: TEN 1–2.
  - Rent burden: GRPIP ≥30 and ≥50, renters only.
  - Overcrowding: NP/RMSP > 1.
  - Long commute: JWMNP ≥60, plus the mean. Commuters only; people who work from home have no JWMNP.
  - Work from home: JWTRNS=11.
  - Employed: ESR 1, 2, 4 or 5.
  - Wage: earners only. Adjusted with ADJINC and then CPI-U to 2024 dollars.
  - Below 200% of poverty: POVPIP < 200.
- **Low-income focus.** There are two versions:
  - POVPIP < 200. This is measured after the move, so it conditions on an outcome.
  - No bachelor's degree. Education is set before the move, so this is the cleaner version.
- There is also a householders-only sample (RELSHIPP=20) and an age 25–64 robustness check that drops
  college-age movers.

## Estimation

- **Weighted means.** Weighted with PWGTP. Standard errors use the 80 ACS replicate weights:
  SE = sqrt(4/80 · Σ(θr − θ)²). The 3 years are pooled with their replicate weights.
- **IPW (ATT).** A logistic propensity of leaving, estimated on:
  - age and age²
  - sex
  - race/ethnicity (5 groups)
  - education (4 groups)
  - foreign-born
  - married
  - disability
  - household type and children present
  - survey year
  - origin county

  Stayers are reweighted by p/(1−p). The propensity model is **re-fit under each of the 80 replicate weights**,
  so the CIs include the uncertainty from estimating it.
  - Balance after weighting is good: the largest absolute standardized difference falls from
    0.32–1.01 (unweighted) to ≤0.046 (weighted) in every sample. See `outputs/contrast_samples_meta.csv` and `outputs/balance_*.csv`.
  - The control effective sample size is ≥1,758 in every contrast.
- **Hand check.** `06_verify.py` recomputes one estimate independently in DuckDB SQL from the raw extracts:
  the homeownership share among out-of-state leavers is 0.4348 (SE 0.0136, n=2,739). This matches the pipeline
  exactly. See `outputs/hand_verification.txt`.

## Results (adults 18–64, IPW leaver minus matched stayer, percentage points, 95% CI)

From `outputs/leaver_vs_stayer_contrasts.csv`. CI = estimate ± 1.96·SE.

| outcome | Left CA (n=2,739) | Sac/Central Valley (n=1,156) | Other CA (n=1,521) |
|---|---|---|---|
| Owns home | −3.5 (−6.0, −1.0) | **+5.4 (+1.6, +9.1)** | −5.2 (−8.3, −2.0) |
| Rent burden ≥30% (renters) | +0.7 (−4.1, +5.5) | **+17.0 (+10.7, +23.2)** | +13.6 (+9.0, +18.2) |
| Rent burden ≥50% (renters) | +3.2 (+0.2, +6.3) | **+16.0 (+9.0, +23.0)** | +12.1 (+6.9, +17.2) |
| Overcrowded | −3.1 (−4.3, −1.9) | −1.9 (−4.6, +0.8) | +0.4 (−1.6, +2.4) |
| Commute ≥60 min (commuters) | −4.6 (−6.3, −3.0) | **+9.3 (+4.8, +13.8)** | +2.6 (−0.7, +5.8) |
| Mean commute (min) | −3.6 (−5.0, −2.1) | **+7.9 (+3.8, +11.9)** | +0.6 (−1.6, +2.9) |
| Employed | −5.7 (−7.5, −3.8) | −4.9 (−8.2, −1.7) | −6.3 (−9.6, −3.1) |
| Wage, earners (2024 $) | −$15.6k (−21.7k, −9.5k) | −$26.2k (−32.9k, −19.5k) | −$14.8k (−21.7k, −7.8k) |
| Below 200% poverty | +8.6 (+6.5, +10.7) | +9.2 (+5.7, +12.8) | +12.2 (+9.1, +15.4) |

Pooling all leavers, compared with matched stayers:
- Homeownership: −2.2 (−3.8, −0.7)
- Rent burden ≥30%: +7.5 (+4.2, +10.9)
- Rent burden ≥50%: +8.3 (+5.6, +10.9)
- Overcrowding: −1.9 (−2.7, −1.0)
- Employment: −5.7 (−7.3, −4.0)

The raw, unadjusted gaps are larger for homeownership (−13.0) because leavers are younger, more often single,
and more often renters.

**Reading.** The Sacramento/Central Valley leavers are the clearest case of "exit hides inequality." They are
the only destination group with a homeownership gain (+5.4 pp), which matches CPL. They also have much more
rent burden: 62% of renters pay ≥30% of income, against 45% of matched stayers. They have more 60+ minute
commutes (21.7% against 12.4%) and lower wages, which fits people who keep Bay jobs from a distance.
Out-of-state leavers commute less and are less crowded, but they work less and are poorer one year after the
move.

**Age 25–64 robustness.** This drops students. The Sac/CV pattern holds: own +7.5 (SE 2.3), rent burden ≥30%
+11.6 (SE 3.5), commute ≥60 +12.1 (SE 2.7).

**Lower-education leavers (no BA, n=2,210 leavers)** compared with matched stayers:
- Rent burden ≥50%: +13.6 (+9.1, +18.1)
- Below 200% poverty: +14.7 (+11.9, +17.5)
- Employed: −5.5 (−8.5, −2.4)
- Overcrowding: −2.5 (−4.1, −0.9)

Among those without a BA who moved to Sac/CV, rent burden ≥50% is +19.2 (SE 4.6).

**Subgroups (any leaver, IPW within the subgroup).** See `outputs/subgroup_contrasts_left_any.csv` and fig3.
- Rent burden ≥30% rises most for Asian/PI leavers (+13.8, SE 3.0, n=1,251) and Other/Multi leavers
  (+17.6, SE 4.3). It rises +7.1 (SE 2.2) for White leavers. It is not significant for Latino (+3.1, SE 3.2)
  or Black leavers (−2.6, SE 6.2). The Black estimate rests on only n=212 leavers and is imprecise for every
  outcome.
- Homeownership falls for Asian/PI leavers (−10.9, SE 1.7) and BA+ leavers (−5.4, SE 1.0). It is flat or
  slightly positive for Latino leavers (+3.4, SE 1.7) and for leavers without a BA.
- Leaving raises the poverty share by about 14–15 pp for the HS/GED and some-college groups, against 5.5 for
  BA+.

## Exit model (who leaves?): Advanced Track

- **Setup.** The target is any Bay leaver against stayers. The features are the pre-move proxies listed above.
  The split is stratified 70/30 (test n=40,846, of which 1,625 are leavers; prevalence 4.0%). Training uses
  PWGTP weights. CIs are from 300 bootstrap resamples of the test set. See `outputs/exit_model_*.csv` and
  `outputs/exit_model_bootstrap_ci.json`.

| model | ROC-AUC [95% CI] | PR-AUC [95% CI] | recall @ top-10% risk | precision @ top-10% |
|---|---|---|---|---|
| Base-rate baseline | 0.500 | 0.040 (= prevalence) | n/a | n/a |
| Logistic regression | 0.691 [0.679, 0.703] | 0.110 [0.100, 0.122] | 0.30 | 0.12 |
| Gradient boosting (HistGB) | **0.706** [0.694, 0.718] | **0.136** [0.122, 0.152] | 0.31 | 0.12 |

- Gradient boosting beats logistic regression by 0.008–0.024 AUC (bootstrap CI). Both beat the baseline
  clearly: PR-AUC is about 3.4 times prevalence.
- Leaving is only modestly predictable from demographics.
- **Who is at highest risk.** Weighted one-year exit rates (`outputs/exit_rates_by_group.csv`, fig5):
  - By age: 18–24 is 7.9% and 25–34 is 6.6%, against 2.4–2.5% for ages 45–64.
  - By household type: nonfamily households 9.1%, living alone 7.2%, married couples 3.4%.
  - By race/ethnicity: White 5.8%, Other/Multi 5.8% and Black 4.9%, against Latino 3.5% and Asian/PI 3.1%.
  - By education: BA+ 4.9%, against <HS 2.1%.
- **Fairness on the test set, gradient boosting** (`outputs/exit_model_fairness.csv`).
  - AUC: Asian/PI 0.72, Latino 0.71, Other 0.72, White 0.68, Black 0.66 (n=1,449, of which 71 are leavers).
  - Recall at the global top-decile threshold is much higher for White leavers (0.41) than for Asian/PI (0.25),
    Black (0.26) and Latino (0.28) leavers. It is 0.05 for <HS and 0.004 for ages 55–64.
  - Calibration ratios (mean predicted ÷ observed) range from 0.81 (Other/Multi) to 1.19 (HS/GED).
  - A risk score built on these features would under-flag older, less-educated and Latino/Asian leavers.
- **Failure examples** (`outputs/exit_model_failure_examples.csv`).
  - The most confident false positives are 19–20-year-old single people with some college in nonfamily
    households who in fact stayed.
  - The most confident false negatives are middle-aged and older, married, foreign-born Latino and Asian
    leavers, often with less than high school. Several of them moved to Sac/CV.
  - 36% of Sac/CV leavers score below the median predicted risk, against 20–21% of other leavers
    (`outputs/exit_model_missed_leavers_by_destination.csv`). The model is worst at spotting the group with
    the worst post-move outcomes.
- The logistic odds ratios in `exit_model_logistic_odds_ratios.csv` come from an L2-regularized model with all
  one-hot levels included, so they are collinear. Use the exit-rate table for interpretation.

## Advanced Track checklist

- [x] Public microdata at scale: ACS PUMS 2022–24, full US person and housing files (all states scanned;
  136,151 analytic records).
- [x] Documented geography crosswalk (IPUMS 2020 MIGPUMA files), with a check that Bay MIGPUMAs are pure.
- [x] Survey-correct inference: 80 replicate weights, with the propensity re-fit in each replicate.
- [x] Causal-style adjustment: IPW (ATT) with balance diagnostics, effective sample size, and robustness
  samples (no-BA, poverty, householders, age 25–64).
- [x] Predictive model against a baseline on a held-out test set: base-rate, logistic regression and gradient
  boosting, with AUC, PR-AUC, Brier score and top-decile recall/precision, plus bootstrap CIs.
- [x] Fairness across 3 or more subgroup dimensions (race/ethnicity, education, age group): AUC, PR-AUC,
  calibration and recall at a common threshold.
- [x] Failure analysis: confident false positives and false negatives, and missed leavers by destination.
- [x] Hand verification of one weighted estimate against independent SQL.
- [x] Single entry point (`run_all.py`) and unweighted n reported for every leaver cell.

## Caveats

- **Not causal.** IPW balances observed pre-move proxies only. Leavers may differ on things we cannot see:
  job loss, eviction, family events. The lower employment among leavers may be partly the reason for the move.
- **All outcomes are post-move, including income.** Rent burden and poverty one year after a move may reflect
  a temporary disruption to income. Results for the POVPIP<200 sample condition on an outcome; the no-BA
  sample is the cleaner low-income cut.
- **Some covariates are not strictly pre-determined.** Household type, children, marital status and disability
  are observed after the move, and household type can change because of the move.
- **One-year migration window.** This is the first year after a move, not long-run outcomes. People who moved
  more than once in the year are classified by where they were one year ago and where they are now.
- **Coarse geography.** Bay origin is resolved only to county MIGPUMAs. Destination is the current PUMA, and
  PUMAs can span urban and rural areas. "Sac/Central Valley" is a county-based definition we chose.
- **Leavers abroad are not observed.** People who moved abroad are out of scope for the ACS, so the "exit rate"
  is leavers ÷ (leavers + stayers) observed in the US.
- **Sample sizes.** Black leavers n=212 and <HS leavers n=259 give wide CIs. Destination-by-subgroup cells are
  thinner still.
- **Pooled years.** 2022–24 are pooled with their replicate weights, and weighted totals are summed over 3
  years (divide by 3 for an annual figure). The years are post-pandemic, and remote work is high among leavers.

## Files

- `run_all.py`: entry point. Pipeline scripts are in `src/`. Raw downloads are in `raw/` (untrusted, never
  executed). Slim extracts are in `data/`.
- `outputs/`:
  - `leaver_vs_stayer_contrasts.csv` (all samples × destinations × outcomes; raw and IPW, SE, CI)
  - `subgroup_contrasts_left_any.csv`
  - `group_sizes.csv`
  - `left_ca_destination_states.csv`
  - `balance_*.csv`
  - `contrast_samples_meta.csv`
  - `exit_model_metrics.csv`, `exit_model_bootstrap_ci.json`, `exit_model_fairness.csv`
  - `exit_model_failure_examples.csv`, `exit_model_missed_leavers_by_destination.csv`
  - `exit_model_logistic_odds_ratios.csv`
  - `exit_rates_by_group.csv`
  - `hand_verification.txt`
  - `run_log.txt`
- `figs/`:
  - `fig1_ipw_by_destination.png`
  - `fig2_ipw_low_income_samples.png`
  - `fig3_subgroup_contrasts.png`
  - `fig4_exit_model_curves.png`
  - `fig5_exit_rates_by_group.png`
  - `fig6_destination_states.png`
