# Forward test: do 2018 conditions predict market pressure after 2018? (E4, E5, E6)

Scripts: `code/e0_extract_zillow.py`, `code/e4_zillow_tract_join.py`, `code/e4b_geometry_crosscheck.py`, `code/e5_forward_test.py`, `code/e6_forward_fairness.py`.

This test predicts **market pressure** (flipping, price appreciation, rent growth). These can lead to displacement; they are not displacement. Census data that could measure post-2018 displacement was not available in the analysis environment.

## Zillow-to-tract join (E4)
- 148,005 properties (74,343 for rent, 61,606 recently sold, 12,056 for sale). 147,210 have coordinates (99.5%).
- Point-in-polygon into 2010-vintage tract polygons (`cb_2018_06_tract_500k`, shipped in the UDP repository; 1,582 Bay Area polygons). 147,194 points fell inside a polygon; 14 within about 250 m were assigned to the nearest tract; 797 stayed unmatched. 144,661 properties are in one of the 1,550 study tracts.
- **Hand check:** 30 randomly drawn properties, assigned tract's county against the listing's own county field: 30 of 30 agree (`results/e4_hand_check_30.csv`). Over all 147,208 matched rows, 12 disagree (11 on the Santa Clara / San Mateo line, 1 on Napa / Solano).
- Cross-check against the UDP GeoPackage: all 1,550 tract ids are in both sources; polygons overlap almost exactly for 90.7% of tracts and differ for the rest (minimum IoU 0.38). The join used the Census shapefile; whether the GeoPackage shapes would move any property was not tested.
- Coverage: 1,543 tracts have at least one property; 1,479 have at least 10 sold homes; only 735 have at least 10 rental listings.
- Sales cleaning: "Sold" events above $50,000, lots excluded, duplicate dates dropped; resale pairs need at least one month between sales and a price change between -80% and +400%. Result: 181,805 sales and 107,657 resale pairs.

## Design (E5)
- Outcomes use only events dated 2019 or later:
  - flip share of resales (1,319 tracts with at least 15 resales);
  - same-home appreciation for homes bought 2019+ and held 24+ months (729 tracts with at least 8 pairs);
  - same-unit asking-rent growth (549 tracts with at least 5 units).
- Target: top quartile of each outcome, threshold set on development tracts.
- Features: 22 UDP variables for 2012/2018, plus 14 Zillow features built only from events dated before 2019 (own and neighbor flip share, 2012-18 appreciation, price per square foot).
- Test set: whole 0.1-degree grid cells, 25% of each county's cells.
- Baselines: UDP `vul_gent_18`, `hotmarket_18`, typology groups, and persistence (the tract's own pre-2019 value).

## Results
| Target (test n, positives) | Census only | Census + Zillow | Gain [95% bootstrap] | vul_gent_18 | hotmarket_18 | Persistence |
|---|---|---|---|---|---|---|
| Flipping hot spot (320, 95) | 0.769 | 0.798 | +0.029 [0.005, 0.057] | 0.641 | 0.434 | 0.690 |
| High appreciation (170, 44) | 0.780 | 0.816 | +0.036 [-0.010, 0.080] | 0.384 | 0.446 | 0.550 |
| High rent growth (125, 23) | 0.728 | 0.737 | +0.009 [-0.068, 0.084] | 0.379 | 0.531 | 0.682 |

- Leave-one-county-out AUC for the combined model: flips 0.793 (n=1,319), appreciation 0.718 (n=729), rent 0.743 (n=549).
- The three outcomes are nearly uncorrelated across tracts (Spearman flip vs appreciation 0.09, flip vs rent -0.13).
- **Null.** Zillow history adds nothing detectable for appreciation or rent growth.
- **Reversal.** The UDP vulnerability flag ranks appreciation and rent growth backwards (0.38).

**Disclosure.** A first random draw of grid cells contained no San Francisco tract, so the split was redrawn within county after the first results had been seen. On the first draw the flip result was similar (0.746 to 0.790, gain +0.044 [0.015, 0.076]) but the rent result was not (+0.097 [0.026, 0.170]). The rent finding is unstable.

## Fairness and failures (E6)
Flipping model, spatial test set (n=320), one regional threshold.

| Group (2018) | n | Positives | AUC | Recall | False-positive rate |
|---|---|---|---|---|---|
| Majority people of color | 211 | 84 | 0.760 | 0.69 | 0.28 |
| Majority white | 109 | 11 | 0.635 | 0.09 | 0.01 |
| Low-income third | 118 | 57 | 0.709 | 0.70 | 0.30 |
| Middle-income third | 111 | 24 | 0.853 | 0.71 | 0.20 |
| High-income third | 91 | 14 | 0.728 | 0.14 | 0.01 |
| UDP low-income typologies | 85 | 43 | 0.682 | 0.74 | 0.33 |
| UDP moderate typologies | 125 | 26 | 0.831 | 0.54 | 0.13 |
| UDP high-income typologies | 110 | 26 | 0.774 | 0.50 | 0.11 |

- The model ranks worst inside the group it flags most.
- The appreciation model found none of the 4 high-appreciation tracts in the low-income third (n=49).
- **Coverage gap.** A flip outcome could be computed for 72% of low-income-typology tracts against 90% of high-income ones, 78% of renter-majority against 89% of owner-majority tracts, and 76% of San Francisco tracts against 99% of Sonoma tracts.

Named failures (hot-spot threshold 9.6% flip share). Full list in `results/e6_failure_tracts.csv`.

| Tract | Place | Model rank | Outcome | Likely reason (interpretation) |
|---|---|---|---|---|
| 06001433104 | San Leandro | bottom 9% | 3 flips in 16 resales | Few sales; rests on 3 events |
| 06013303204 | Brentwood | bottom 13% | 9 of 78 | Outer suburb with low past flipping nearby |
| 06013346102 | Alamo | bottom 19% | 8 of 77 | Affluent; model learned flips happen where college share is low |
| 06001409600 | Oakland | top 1% | 3 of 33 (9.1%) | Heavy pre-2019 flipping; just under the threshold |
| 06001408700 | Oakland | top 1% | 2 of 41 | Flipping cooled |
| 06085504102 | San Jose | top 5% | 2 of 26 | Profile matched, outcome did not |

## Limits
- Zillow histories exist only for homes listed or sold recently: 45,480 of the sales are from 2026 and 18,860 from 2025, against roughly 4,000 a year before. Pre-2019 features describe the past of today's market sample.
- Top-quartile targets are relative: a tract is a hot spot at 9.7% and not at 9.1%.
- San Francisco has 8 tracts in the flipping test set.
- Rent-growth outcomes exist for only 549 tracts.
