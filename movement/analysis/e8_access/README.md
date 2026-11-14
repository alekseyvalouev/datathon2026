# E8: Where can a displaced low-income household still re-rent in the Bay, and what access does it give up?

California Policy Lab finds that 75% of low-income movers stay in the Bay Area. E8 takes every current Zillow FOR_RENT
listing, asks whether a low-income household could pass the income screen for it (E6 method), and measures
straight-line access from it to essential services in the Google Maps Places data. It compares the units a
low-income household can qualify for with the rest of the market and with the high-turnover "origin" areas, then trains
a spatially validated model that flags rental buildings in service deserts using Zillow-only information.

## Reproduce
```bash
python3 analysis/e8_access/run_all.py      # about 2.5 min; full log in outputs/run_all.log
```
**Inputs.**
- Raw `google_maps.csv` and `google_maps_reviews.csv`.
- `analysis/cache/zillow.duckdb`, opened read-only. It is built from the raw Zillow CSVs by `analysis/common/build_zillow.py`.
- Files from earlier experiments:
  - E6's HCD income-limit table, `analysis/e6_unit_replacement/outputs/income_limits_bay.csv`;
  - E2's downloaded UDP typology and 2018 TIGER tracts, in `analysis/e2_turnover_model/external/`;
  - E2's `zip_reentry_cost.csv`.

**Steps.**
- `s01_places.py`: categorizes places and runs the hand check.
- `s02_access.py`: listings, income gate, tract and typology join, BallTree distances and counts.
- `s03_compare.py`: group comparisons and maps.
- `s04_model.py`: label, spatial split, baselines, models, subgroups and failures.

**Privacy.** No street addresses are read or written, and outputs carry no coordinates. Failure examples are aggregated to city and ZIP.

## Data decisions (documented and hand-checked)

**Places → service categories** (`outputs/places_category_rules.csv`, `places_category_counts.csv`).
- Data used: 147,429 places with unique `place_id`. Dropping permanently or temporarily closed places leaves 132,217 open.

| service | rule (main `category`) | open places |
|---|---|---|
| grocery | Grocery store, Supermarket, Produce market, ethnic grocery/supermarket types; name excludes gas/liquor/smoke/"food mart"/"mini mart"/convenience/distributor | 2,429 |
| clinic (general, urgent or community care) | Community health center, Urgent care, Walk-in clinic, Free clinic, Medical Center, Hospital, ER, Pediatric clinic; **plus** Medical clinic / Clinic / Women's health clinic / Family practice physician **only if the name signals general care** (urgent, community, family, primary, health center, medical group, Kaiser, Sutter, county, …); cosmetic, spa and other non-care names excluded | 2,635 |
| clinic_broad (sensitivity) | same categories without the name requirement | 8,953 |
| pharmacy | Pharmacy, excluding specialty, compounding, infusion and long-term-care | 1,082 |
| transit | Bus stop, Transport hub (these rows are stop names like "Park Blvd:Everett Av"), Transit station | 21,842 |
| food bank | Food bank, Foodbank, Soup kitchen, or an `all_categories` tag of food bank or food pantry | 461 |
| bank vs alternative financial services (AFS) | Bank and credit unions vs check cashing, pawn shops and money transfer | 1,731 vs 1,816 |

**Hand checks of the category rules.** There were two rounds of 30 rows each.
- **Round 1, v1 rules** (`hand_check_round1_v1rules.csv`): 23/30 correct.
  - Grocery 3/5: a gas-station mart and a distributor were wrong.
  - Clinic 4/5: a hair-removal business was wrong.
  - Pharmacy 4/5: a long-term-care pharmacy was wrong.
  - Food bank 3/5.
  - These errors led to the grocery and pharmacy name exclusions.
- **Interim look at 6 clinic rows under v2:** 2/6 were care facilities (a cannabis-card office, a counselor, …). I replaced the clinic rule with the precision-oriented v3 rule.
- **Final round, v3 rules** (seed 43; `outputs/hand_check_places.csv`, verdicts in `hand_check_verdicts_final.csv`):
  - **27/30 correct** for the category in general.
  - **18/30 under a strict reading**: a supermarket of the type USDA counts, general or urgent care rather than a specialist, and a food site open to the public.
  - Clinic 6/6 general, 3/6 strict. Grocery 6/6 general, 2/6 strict (small ethnic and produce grocers). Pharmacy 4/6 (two pharmacist-name records).
  - Food bank 4/5 general, 2/5 strict. Transit 4/4. Bank/AFS 3/3.

**Distances.**
- Method: haversine BallTree on distinct listing coordinates.
- Check: on 300 random locations, a brute-force haversine matches the BallTree to within 1e-12 m (`outputs/distance_check.csv`).
- Also computed:
  - counts of each service within 400 m, 800 m and 1.6 km;
  - the rating of the nearest clinic. Rating 0 or no reviews is treated as unrated, which applies to 39% of clinics. `mean_rating_clinics_3km` is also reported.
- The reviews dataset covers only 2.4% of clinics, so the Places `rating` field is used.

**Listings and income gate.**
- 73,747 FOR_RENT listings in the 9 counties, with coordinates, rent in $500–30,000 and beds known. They sit at **10,541 distinct coordinates ("buildings")**.
- Large complexes list many floor plans or units at one point, so every comparison is reported both listing-weighted and building-weighted.
- Income gate, reusing E6's method and limit table:
  - minimum income = 3 × 12 × rent;
  - household size = beds + 1;
  - limits are the **HCD 2026** limits, because the snapshot runs to 2026-11-13 and the 2026 limits are in force June 2026 to May 2027.
- Shares that qualify: 67.7% of listings at ≤80% AMI ("LI-reachable"), **6.8% at ≤50% AMI ("VLI-reachable")**, and 87.7% at ≤80% AMI under a 2.5× screen.
- 80% AMI in 2026 is a high bar, so the ≤50% group is the policy-relevant "low-income" group here.
- The UDP typology joined for 97.8% of listings.

**Origin areas.** These are San Francisco County, San Mateo County, and E2's top-10 ZIPs by observed turnover jump among n ≥ 20; all ten are in SF.

## Findings: comparing access (`outputs/headline.csv`, `access_compare_*.csv`)

**1. Leaving the high-premium core means giving up access** (listing-weighted, medians).

| | units in origin areas (n = 14,574) | rest of Bay, ≤80% AMI-reachable (42,884) | rest of Bay, ≤50% AMI-reachable (4,328) |
|---|---|---|---|
| nearest clinic | 338 m | 609 m (**1.80×**) | 560 m (**1.66×**) |
| nearest grocery | 281 m | 428 m (1.52×) | 355 m (1.26×) |
| bus stop within 400 m | 97.1% | 86.3% (**−11%**) | 90.1% (**−7%**) |
| service desert (definition below) | 3.3% | 4.5% | 2.9% |

Building-weighted, the ratios are similar: clinic distance 1.61× and 1.50×, bus stop within 400 m 95.0% → 82.9% and 86.8%.

**Headline.** A household priced out of SF or San Mateo that re-rents a unit it can qualify for elsewhere in the Bay ends up about 1.7–1.8× farther from a clinic. It is 7–11% less likely to have a bus stop within 400 m.

**2. Within the rest of the Bay, affordability does not predict isolation. If anything it predicts better access.**

Region-wide comparison (median distances):

| comparison | weighting | clinic distance ratio | bus stop within 400 m |
|---|---|---|---|
| ≤80% AMI-reachable vs not | listing | 1.26× farther | 87.9% vs 92.1% |
| ≤80% AMI-reachable vs not | building | 0.87× | 84.8% vs 76.5% |
| ≤50% AMI-reachable vs not | listing | 0.91× | 91.3% vs 89.1% |
| ≤50% AMI-reachable vs not | building | 0.83× | 88.6% vs 80.2% |

- The listing-weighted LI gap is a county-mix effect. **Within counties** the median clinic-distance ratio is 1.00 (listing) and 0.75 (building).
- Desert rates (building-weighted): 6.6% for LI-reachable vs 15.3% for not reachable; 5.0% for VLI-reachable vs 10.7% for not.
- Logit with county fixed effects and block-clustered SEs (`affordability_vs_desert_logit.csv`):
  - higher median building rent → *more* likely a desert, OR 2.7 per log-rent unit, p < 0.001;
  - a building with a ≤50% AMI-reachable unit has OR 0.43 (p < 0.001).
- The cheap stock is in dense, older, transit-served cores. The deserts are mostly pricier single-family and townhouse rentals at the suburban edge (Contra Costa, Solano, Napa, Marin).

**Exceptions** (`access_compare_county_vli_listing.csv`), comparing VLI-reachable with other listings in the same county:
- Santa Clara: 73% of VLI-reachable listings have a bus stop within 400 m vs 86% of other listings.
- Contra Costa: nearest clinic 772 m vs 654 m.
- San Mateo: nearest clinic 795 m vs 609 m.
- Sonoma: nearest clinic 940 m vs 794 m.

**Other measures.**
- Ratings of the nearest rated clinic barely differ between groups (3.8–4.0).
- Banks per AFS outlet within 1.6 km: 2.36 in origin areas vs 1.36 for LI-reachable units elsewhere, and 1.39 for VLI-reachable units. Movers trade toward fringe-finance-heavy areas.

Figures: `figs/map_clinic_distance_and_vli_units.png`, `figs/county_access_vli_vs_not.png` and `figs/ecdf_clinic_origin_vs_dest.png`.

## Model: flag rental buildings in service deserts from Zillow-only information (`s04_model.py`)

**Label.** `desert` = 1 if any of the following holds (straight line):
- nearest grocery > **1.6 km**. This is the USDA Food Access Research Atlas urban low-access line of 1 mile.
- nearest clinic > **3.2 km** (2 miles). There is no federal walk standard for clinics, so this is set at twice the grocery line, about a 40-minute walk.
- nearest transit stop > **800 m**. This is the standard half-mile transit walkshed used for California "major transit stop" and TOD buffers.

Prevalence is 10.2% of buildings and 4.3% of listings. Requiring all three or two of three is too rare in the Bay: 0.8% of listings meet two of three. That stricter version is reported descriptively as `share_desert_2of3`.

**Unit and features.**
- The unit is one building, n = 10,541.
- Zillow features:
  - median, min and max rent, rent per sqft, rent per person;
  - beds, baths, sqft, year built;
  - homeType shares, management-company share, days on Zillow, number of listings;
  - LI and VLI-reachable shares, minimum AMI needed, rent relative to the county median;
  - county.
- M2 adds Zillow-derived context: the count of Zillow properties of any status within 1 km and 3 km, and the log distance to the nearest of 20 big-city downtowns.
- No Places data is used in any feature.

**Spatial held-out test.**
- The region is cut into 0.05° blocks; 348 contain listings.
- 25% of blocks (seed 42) form the test set: 87 blocks, 3,302 buildings, prevalence 8.3%. They were never used for training, tuning or picking the threshold.
- Hyperparameters (a 6-config LightGBM grid, selected on AP) and the max-F1 threshold come from 5-fold GroupKFold over the training blocks.
- The AUC confidence intervals are a 500-rep block bootstrap on the test set.

| model (test, building level) | AUC [95% CI] | AP | F1 | precision | recall | AUC / AP listing-weighted |
|---|---|---|---|---|---|---|
| B0 county prior | 0.765 [0.640, 0.846] | 0.196 | 0.299 | 0.184 | 0.788 | 0.832 / 0.131 |
| B1 logit on distance to nearest downtown (rule baseline) | 0.826 [0.728, 0.894] | 0.302 | 0.379 | 0.287 | 0.555 | 0.721 / 0.081 |
| M1 LightGBM, listing attributes + county | 0.859 [0.800, 0.897] | 0.407 | 0.429 | 0.333 | 0.602 | 0.834 / 0.230 |
| **M2 = M1 + Zillow density/downtown context** | **0.920 [0.875, 0.953]** | **0.596** | **0.572** | 0.542 | 0.606 | 0.906 / 0.467 |
| M3 = M2 + raw lat/lon | 0.929 [0.887, 0.959] | 0.623 | 0.571 | 0.641 | 0.515 | 0.909 / 0.448 |

- AUC(M2) − AUC(B1) = +0.092, block-bootstrap 95% CI [+0.033, +0.177].
- M2 roughly doubles average precision over the rule baseline.
- The top M2 features by gain are Zillow property density within 3 km and 1 km, sqft, downtown distance and county (`model_feature_importance_M2.csv`).
- Rent and income-gate features carry little weight, consistent with finding 2.

### Subgroup / fairness analysis (`outputs/model_subgroup_metrics_test.csv`; M2 at the CV threshold)

**County.**
- AUC is high in Alameda (0.96), Napa (0.98), Solano (0.93) and Sonoma (0.95), and weaker in Contra Costa (0.73), Marin (0.65) and Santa Clara (0.77).
- Contra Costa has the most deserts (117 of 359 test buildings) and the highest false-positive rate (26%).
- SF and San Mateo test blocks have no deserts. San Mateo still gets a 4.6% false-alarm rate.

**UDP typology.** AUC is 0.96 in low-income/displacement tracts, 0.89 in moderate/mixed and 0.88 in exclusive tracts. Recall is about 0.6 in all three.

**Rent tier** (train-set quartiles of building median rent). **Recall is 0.31 in the cheapest quartile vs 0.69 in the priciest.**
- Precision is 0.38 vs 0.58. AUC is about 0.91 in every tier.
- The model learns "desert = expensive suburban edge", so it **misses deserts among cheap units**: the cases that matter most for displaced low-income households.
- The same holds for buildings with a ≤50% AMI-reachable unit: recall 0.36 vs 0.63 for buildings without one.
- The B1 rule baseline has a smaller gap (0.44 vs 0.60).

### Where the model fails (`model_failures_by_area_test.csv`, `model_error_profile_test.csv`; city and ZIP aggregates)

**Missed deserts (FN, 108 buildings).**
- Medians: rent $3,200, 67 Zillow properties within 1 km, 9.5 km from a downtown.
- They sit just over a threshold: median grocery 1.61 km, clinic 1.60 km, transit 824 m.
- Clusters:
  - San Ramon 94582: 14 buildings, all over the transit threshold.
  - Antioch 94531: 12 buildings, all over the transit threshold.
  - Dublin 94568: 6 buildings, grocery about 2.9 km.
  - Moraga 94556: 4 buildings, clinic about 3.8 km.
  - Fairfax and San Anselmo: clinic 3.0–3.6 km.
- These are suburban places dense enough in Zillow to look urban, where the binding gap is transit or a clinic.

**False alarms (FP, 140 buildings).**
- Medians: rent $3,970, low Zillow density (49 within 1 km), 11 km from a downtown, yet actually served (grocery 846 m, clinic 996 m, transit 321 m).
- Clusters: Danville 94506 (11), Rio Vista 94571 (9; small-town centers with their own services), Antioch, San Ramon, Milpitas, Vallejo, Bay Point and Lafayette.

**Product.** `model_flagged_zips_li_units_test.csv` ranks held-out ZIPs by the predicted desert share of buildings with ≤80% AMI-reachable units.
- Top: Solano 94571 (predicted 0.71, observed 0), Sonoma 95446, Solano 94585 (observed 0.90, n = 10 buildings / 95 listings), Contra Costa 94565 and 94556.
- Figures: `figs/model_roc_pr_test.png`, `figs/model_test_errors_map.png` and `figs/map_desert_label.png`.

## Advanced Track checklist
| requirement | where |
|---|---|
| Model | LightGBM M1 / M2 / M3 (`s04_model.py`), tuned by spatial GroupKFold |
| Baseline | B0 county prior; B1 logistic rule on distance to nearest big-city downtown |
| Held-out test | Spatial block hold-out: 87 of 348 blocks, never used for training or tuning. AUC, AP, F1, precision, recall, Brier, block-bootstrap CI (`model_metrics_test.csv`) |
| ≥3 subgroups + failure examples | County, UDP typology, rent tier and ≤50% AMI building (`model_subgroup_metrics_test.csv`); FN/FP aggregates by city and ZIP (`model_failures_by_area_test.csv`) |
| Data decisions + hand check | Category rules (`places_category_rules.csv`); two 30-row hand checks (round 1 23/30 → rules revised; final 27/30, strict 18/30); BallTree vs brute-force distance check; listing flow (`listing_flow.csv`, `places_flow.csv`); income gate reused from E6 (validated there) |
| Reproducible | `python3 analysis/e8_access/run_all.py`, raw CSV / DuckDB → every number above; seeds fixed (42, plus 43 for the hand-check sample) |

## Caveats
- **Places coverage is incomplete.** The data was keyword-scraped: for example, 179 open-and-closed Safeway "Grocery store" rows.
  - Precision errors (small grocers, specialists) make access look *better* than it is.
  - The strict clinic rule drops real small practices, which makes clinic access look *worse*. With `clinic_broad`, median clinic distances shrink; see `med_d_clinic_broad_m`.
  - The Places bounding box covers Santa Cruz and the edges of neighboring counties. Those places count as services near the county edges.
- **Straight-line distance is not travel time.** Hills, freeways, the Bay and transit frequency are ignored. A bus stop within 400 m says nothing about service frequency or where the route goes.
- **A listing snapshot is not where movers actually go.** These are asking rents on current listings, not leases signed by displaced households.
- **The 3× rule and household size = beds + 1 are conventions** (see E6).
- **≤80% AMI reach is very common** under 2026 limits (68% of listings), which is why the ≤50% group is emphasized.
- **Hospitals and Kaiser facilities count as clinics** even when access requires membership.
- **Listings cluster in large complexes** (73,747 listings at 10,541 points). Listing-weighted shares are driven by big corporate buildings. Building-weighted results are given alongside.
- **The desert label has hard thresholds.** Missed deserts sit close to a threshold (median grocery 1.61 km, transit 824 m), so a continuous access index would be a natural extension.
