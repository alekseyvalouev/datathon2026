# Units leaving reach: which affordable rentals will a turnover price out of low-income reach?

**Question.** When a tenant leaves a Bay Area rental that a low-income household could still qualify for, can we predict, at the moment the unit is re-listed, whether the next rent will put it out of reach?

**Why it matters.** AB 1482 caps rent increases for sitting tenants but not the rent on a vacant unit. Each turnover is therefore the moment a unit can leave the low-income stock. Acquisition programmes like San Francisco's Small Sites, tenant organisations and right-of-first-refusal laws all need to know *which* units are about to go, not just which neighborhoods are at risk.

**This workstream joins the other three:**
- **Unit and market features and the label:** `movement` (E2 turnover pairs, E6 income limits).
- **Tract features and the backtest risk score:** `displacement-early-warning`.
- **City job mix:** `ai-labor-distribution`.

**Thesis.**
- **Most of the signal is simple arithmetic about headroom.** A model predicts loss of reach well (test AUC 0.90) and beats the best published-rule baseline by +0.05 AUC.
- **The UDP neighborhood typology ranks it backwards** (AUC 0.46). The affordable units most likely to go are the last ones in affluent tracts, which sit just under the line.
- **The model is again weakest where the stakes are highest.** At a fixed outreach budget it catches fewer losses in renter-majority, low-income and gentrifying tracts, and in apartments run by large managers. There, 2026 rents rose faster than anything in the training years.

Every number below traces to a CSV in `results/` written by a script in `code/`. Hand check: `memos/hand_check.md`.

---

## Headline numbers
| | Finding | Source |
|---|---|---|
| **0.90 vs 0.85** | Test AUC, LightGBM 0.900 [0.891, 0.909] against the legal-max rule 0.848 [0.838, 0.860]. Gain +0.051 [0.045, 0.058], 6,808 pairs re-listed in 2026 | `s03_test_metrics`, `s03_comparisons` |
| **914 vs 819** | Of 1,403 units that left reach in 2026, how many each method catches when both flag the same 20% of units (1,361) | `s03_test_predictions` |
| **0.46** | Test AUC of the UDP "low-income or gentrifying tract" rule. It ranks loss of reach backwards | `s03_test_metrics` |
| **0.62 vs 0.79** | Share of losses caught at a 20% budget in low-income vs exclusive UDP tracts; with a separate 20% list per typology group, 0.76 vs 0.65 | `s03_subgroups`, `s04_budget_allocation` |

## 1. The label [s01, hand check]
- **Population.** Movement E2's 23,306 same-unit turnover pairs, restricted to re-listings from June 2022 on (the first year of parsed income limits). We keep the 12,011 units whose previous rent a household at **80% of area median income** could qualify for. Qualifying means income ≥ 3× rent, with household size = bedrooms + 1, using the CA HCD limit in force at re-listing.
- **Label.** The unit **left reach** if the next tenancy's **settled asking rent** is above that same limit. Holding the limit fixed isolates the price move.
  - The settled ask is the last ask of the re-listing episode, after any cuts.
  - The hand check found first asks that crossed the line and were cut back below it within weeks, so the first ask is only a robustness check.
- **Rates.** 18.9% overall (2,275 of 12,011; 20.5% under the first-ask label). Train (re-listed before July 2025) 17.8%, n=4,061. Validation (second half of 2025) 13.1%, n=1,142. **Test (2026) 20.6%, n=6,808.**
- **By county:** San Francisco 55% and San Mateo 37% in 2026, against 7–11% in Contra Costa, Napa, Marin, Solano and Sonoma.
- **Hand check (30 pairs).**
  - Every price, label and join reproduces from the raw events (30/30).
  - By reading: 22 correct, 5 correct with caveats, 3 questionable. All 3 questionable are very large jumps that look like zpid reuse.
  - Dropping jumps above 30%/yr leaves the result unchanged (§5).

## 2. Model against baselines [s03]
Validation was used to tune the models and set thresholds. Final models were refit on train + validation and scored **once** on 2026.

| Model | Test AUC [95%] | PR-AUC | Recall at 20% budget | Precision at 20% budget |
|---|---|---|---|---|
| Majority class (never leaves) | 0.500 | 0.206 | — | — |
| UDP typology rule (low-income or gentrifying tract) | **0.456** [0.442, 0.470] | 0.194 | — | — |
| ZIP-trend rule (ZIP median turnover change vs growth needed to cross) | 0.844 [0.833, 0.855] | 0.608 | 0.593 | 0.564 |
| **Legal-max rule** (would cross if rent rose 10%/yr, the AB 1482 maximum) | 0.848 [0.838, 0.860] | 0.625 | 0.604 | 0.583 |
| Logistic, headroom only | 0.862 [0.852, 0.872] | 0.616 | 0.594 | 0.597 |
| Logistic (L2), all features | 0.893 [0.885, 0.902] | 0.703 | 0.661 | 0.636 |
| LightGBM, unit + headroom + market | 0.896 [0.888, 0.905] | 0.699 | 0.713 | 0.599 |
| LightGBM, + tract features | 0.901 [0.892, 0.909] | 0.720 | 0.709 | 0.625 |
| **LightGBM, + tract + city jobs (main)** | **0.900** [0.891, 0.909] | 0.717 | 0.721 | 0.605 |

- **How the budget columns were set.** "Budget" columns use a threshold at the 80th percentile of *validation* scores. Because 2026 scores shifted, that flags 21–25% of test units depending on the model. At exactly 20% of test units, the model catches 914 losses and the rule 819.
- **Gains against baselines** (paired bootstrap, 1,000 draws):
  - vs legal-max rule: +0.051 [0.045, 0.058]
  - vs headroom-only logistic: +0.038 [0.033, 0.044]
  - vs logistic with all features: +0.007 [0.002, 0.011]
- **What the model uses.** Shuffling a feature group drops test AUC by:
  - headroom (how far below the line and the yearly growth needed to cross): 0.26
  - market (county rent index, ZIP turnover history): 0.030
  - tract: 0.013
  - unit: 0.008
  - city jobs: 0.002
- **Calibration is poor in 2026.** In the top decile, mean prediction is 0.62 against 0.81 observed; deciles 5–7 under-predict by 2–3×. Validation prevalence (13%) was lower than test (21%), so recalibrating on validation cannot fix this. **Use the score as a ranking, not a probability.**

## 3. Cross-workstream features add little, and which one helps is not stable [s03, s04 R5]
| | Mean test AUC over 10 seeds | Spread |
|---|---|---|
| Unit + headroom + market | 0.897 | sd 0.002 |
| + tract features (displacement-early-warning) | 0.899 | gain +0.003 ± 0.002 |
| + city job mix (ai-labor-distribution) | 0.900 | gain +0.001 ± 0.002 |
| Both groups together | | **+0.004 ± 0.002**, positive in 10 of 10 seeds |

- **This is a null worth stating.** On the s03 seed with a different row order, the credit went to city jobs instead of tract features. The bootstrap intervals in s03 cover test sampling, not training randomness.
- **It agrees with the other workstreams.** displacement-early-warning found Zillow history adds little to census data. ai-labor-distribution found AI job density does not predict housing costs within a county.

## 4. Fairness and failures [s03 subgroups, s04]
**Ranking quality is even across groups; budget recall is not.**

| Group (2026 test) | n | Leave rate | AUC | Recall at 20% budget, model | Same, legal-max rule | Mean prediction ÷ leave rate |
|---|---|---|---|---|---|---|
| UDP low-income | 1,474 | 15.1% | 0.895 | 0.62 | 0.52 | 0.54 |
| UDP gentrifying | 971 | 18.8% | 0.913 | 0.62 | 0.54 | 0.47 |
| UDP moderate | 2,647 | 19.4% | 0.895 | 0.73 | 0.63 | 0.67 |
| UDP exclusive | 1,640 | 28.5% | 0.905 | 0.79 | 0.64 | 0.64 |
| Majority-renter tract | 4,402 | 21.8% | 0.912 | 0.67 | 0.53 | 0.50 |
| Majority-owner tract | 2,330 | 18.3% | 0.903 | 0.83 | 0.77 | 0.85 |
| Low-income tract (2018 tercile) | 2,742 | 12.6% | 0.896 | 0.63 | 0.56 | 0.58 |
| High-income tract | 1,737 | 36.1% | 0.899 | 0.81 | 0.63 | 0.61 |
| Majority people of color | 4,899 | 19.9% | 0.907 | 0.71 | 0.60 | 0.59 |
| Majority white | 1,833 | 22.5% | 0.886 | 0.74 | 0.62 | 0.66 |
| Apartment | 5,648 | 19.2% | 0.910 | 0.67 | 0.53 | 0.54 |
| House / condo / townhouse | 1,160 | 27.2% | 0.881 | 0.88 | 0.85 | 0.90 |
| Large manager (200+ units) | 2,690 | 24.9% | 0.897 | 0.68 | 0.53 | 0.50 |

- **The gap comes from under-prediction, not worse ranking.** In 2026, rents in apartments, renter-majority tracts and large-manager buildings rose further than the training years suggested. The model predicts about half the observed rate there, against 85–90% for houses and owner-majority tracts. One regional list therefore spends its budget where the model is confident: houses and affluent tracts.
- **The model still beats the rule inside every group above.**
- **Two budget policies** (s04 R4; thresholds from validation quantiles):

| Policy | Units flagged | Losses caught | Recall: low-income / gentrifying / moderate / exclusive |
|---|---|---|---|
| One regional top-20% list | 1,672 | 1,011 (72%) | 0.62 / 0.62 / 0.73 / 0.79 |
| Top 20% inside each UDP group | 1,490 | 938 (67%) | **0.76 / 0.68** / 0.64 / 0.65 |

Per-group lists even out recall at a cost of 73 losses caught and lower precision in low-income tracts (0.46 vs 0.55). That trade-off is a policy choice; the model doesn't settle it.

**Where it fails** (`results/s03_failures.csv`):
- **Missed losses:** units sitting 30–65% below the line whose rent jumped 40–90% in one or two years. Mostly apartments at large managers in Oakland 94612, Berkeley 94704 and Santa Clara.
  - Two Berkeley misses are units in the same building with identical histories. That's the floor-plan duplication movement E2 already flagged in 94704.
  - Some of these are probably zpid reuse rather than real jumps (see the hand check). The rest are lease-ups or repositioned buildings the features cannot see.
- **False alarms:** houses and townhouses 2–9% below the line whose owners held the rent flat or cut it. Examples: Fremont 4-bed $4,000 → $3,000; Napa 3-bed $3,800 → $3,800. Small landlords who don't raise rent at turnover look like risky units on paper.

## 5. Robustness [s04]
| Check | Test n | Leave rate | Model AUC | Rule AUC | Gain [95%] |
|---|---|---|---|---|---|
| Main | 6,808 | 20.6% | 0.900 | 0.848 | +0.051 [0.044, 0.057] |
| First ask instead of settled ask | 6,808 | 21.0% | 0.901 | 0.856 | +0.045 [0.040, 0.051] |
| Drop jumps > 30%/yr (likely unit swaps) | 6,680 | 19.8% | 0.907 | 0.868 | +0.039 [0.035, 0.044] |
| 50% AMI line (very low income) | 1,113 | 55.9% | 0.795 | 0.747 | +0.048 [0.030, 0.068] |
| 2.5× income rule | 8,193 | 10.8% | 0.949 | 0.878 | +0.071 [0.061, 0.080] |
| Units never seen in train or validation | 4,966 | 22.3% | 0.901 | 0.860 | +0.041 [0.035, 0.048] |

**Leave-one-county-out:** the county is excluded from training *and* from the ZIP and county history encodings, then tested on its 2026 pairs.
- **Model ahead:** Alameda +0.016 [0.007, 0.024], Marin +0.048 [0.006, 0.104], San Francisco +0.038 [0.024, 0.052].
- **Ahead, but not clearly:** San Mateo +0.015, Santa Clara +0.007, Solano +0.032, Napa +0.072 (8 positives). Each interval touches or crosses zero.
- **Model behind:** Contra Costa −0.014 [−0.027, −0.002] and Sonoma −0.017 [−0.039, 0.005].

In outer counties the one-line rule is as good as the model, which is the same weakness displacement-early-warning found (0 of 7 losses caught in Solano, 0 of 8 in Napa).

## Nulls and negatives (keep these in any synthesis)
- **The UDP typology ranks loss of reach backwards** (AUC 0.46). Units still under the line in exclusive tracts sit closer to it (median 21% below vs 28–30% in low-income and gentrifying tracts), so they cross more often (28.5% vs 15.1%). This agrees with displacement-early-warning's finding that post-2018 rent growth moved to affluent tracts.
- **Tract and city job features add +0.004 AUC together**, and the split between them is not stable across seeds.
- **Tree models add +0.007 over a logistic model** with the same features. Most of the gain over the rule comes from combining headroom with market history, not from model complexity.
- **Probabilities are not calibrated for 2026.** The model under-predicts most for apartments and large managers.
- **In two outer counties the legal-max rule beats the model** out of county.

## Advanced Track checklist
| Requirement | Where |
|---|---|
| Train a predictive model | LightGBM and logistic classifiers (`code/s03_model.py`) |
| Baseline | Majority class, AB 1482 legal-max rule, ZIP-trend rule, UDP typology rule, headroom-only logistic |
| Held-out test | 2026 re-listings scored once; tuning and thresholds on the second half of 2025 |
| ≥3 subgroups and failure examples | 8 groupings (typology, county, tenure, race, income, home type, landlord, headroom); 24 named failures; leave-one-county-out |
| Labels, joins, hand check | Label defined from HCD limits; 30-pair hand check against raw events; tract and city join checks (`memos/hand_check.md`) |
| Reproducible | `code/run_all.sh` (about 1 min after upstream steps); deterministic; reruns reproduce every CSV |

## Limits
1. **Asking rents, not signed leases.** The settled ask is the closest proxy. 2026 episodes may still be open, so their settled ask is the current ask; that is a definition drift between train and test.
2. **Some APARTMENT zpids are floor plans or are reused across units** (movement E2). That inflates some large jumps; the robustness drop of >30%/yr jumps handles the worst.
3. **Income qualification is a convention.** The 3× rule is tested at 2.5×, household size is assumed from bedrooms, and limits are county-wide.
4. **The units are those Zillow saw listed twice**, mostly since 2024. Rent-controlled pre-1979 buildings in SF, Oakland and Berkeley are subject to vacancy decontrol under Costa-Hawkins, so they are in scope. Units that never come back to market are not.
5. **Tract features are from 2018 and city job mix is a 2026 cross-section.** Neither is time-varying within the sample.
6. **Prediction only.** Nothing here says why a landlord re-prices or what an intervention would change.

## Files
- `code/`: `s01_build.py` (population, label, joins), `s02_hand_check.py`, `s03_model.py` (baselines, models, test, subgroups, failures, figures), `s04_robustness.py`, `modlib.py`, `run_all.sh`
- `results/`: every table cited above; `run_all.log` is the last full run
- `figs/`: `roc_pr_test.png`, `subgroup_budget_recall.png`, `calibration_test.png`
- `memos/hand_check.md`
