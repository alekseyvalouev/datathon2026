# Unit turnover: will this rental be listed for a new tenant this year?

Companion to `units-leaving-reach`. That model scores what happens to the rent *if* a unit turns over; this one
scores *whether* it turns over. The atlas currently assumes a flat 20% a year for every unit.

## Run

```
python3 code/s01_build.py     # unit x year panel -> results/panel.parquet
python3 code/s02_model.py     # baselines, LightGBM, 2025 test, subgroups -> results/s02_*
```

Needs `movement/analysis/cache/zillow.duckdb`, the E2 tract files and `displacement-early-warning/results/e5_tract_table.csv`.

## Design

- **Row:** one unit on 1 January of year Y, for a unit already seen listed for rent before that date.
- **Label:** a new tenancy listing starts during Y. Listings within 180 days of the previous listing are the same
  vacancy and are merged.
- **Population:** units with Zillow status FOR_RENT at the 2026 crawl, residential, floor-plan duplicates dropped:
  11,748 units, 35,854 unit-years.
- **Split:** train 2019–2023 (16,839 rows), validation 2024 (7,267), test 2025 (11,748).
- **Why not 2026:** these units are in the data because they were listed in 2026, so almost all of them "turn
  over" in 2026 by construction. 2026 is excluded from training and testing.
- **Features (known on 1 January):** time since the last listing, the unit's earlier turnovers, the last listing
  (rent, price cuts, days listed), unit and landlord type, county rent index at the last listing and since, ZIP
  turnover rate, 2018 tract characteristics.
- **Model:** LightGBM, same settings and tuning grid as the rent model (15 leaves, 91 trees chosen on validation).

## Result on the 2025 test year (turnover rate 32.2%)

| Model | AUC [95%] | PR-AUC | Brier | Mean prediction |
|---|---|---|---|---|
| Flat rate for every unit (atlas assumption) | 0.500 | 0.322 | 0.223 | 0.252 |
| Lease-clock rule: rate by time since last listing | 0.569 [0.557, 0.579] | 0.363 | 0.219 | 0.263 |
| Own-history rule: the unit's past turnovers per year | 0.510 [0.500, 0.521] | 0.330 | 0.281 | 0.417 |
| Logistic, all features | 0.597 [0.586, 0.608] | 0.394 | 0.214 | 0.299 |
| **LightGBM** | **0.627 [0.617, 0.638]** | 0.424 | 0.209 | 0.297 |

LightGBM beats the lease-clock rule by 0.059 AUC [0.049, 0.068]. The lowest-scored tenth of units turned over 14%
of the time, the highest-scored tenth 45%. Most of the signal is time since the last listing and how the last
listing went; tract features add nothing.

## Who it misses

- **Under-predicts in low-income tracts:** predicted 30.0% against 34.9% actual (ratio 0.86); high-income tracts 0.97.
- **Under-predicts long tenancies:** four or more years since the last listing, predicted 18.1% against 24.1%.
- **Weakest for houses, condos and townhouses:** AUC 0.589 against 0.622 for apartments.
- **Solano and Sonoma:** predictions run about 22% low.

## Limits

- **Ranking is modest.** AUC 0.63 separates units, but far less sharply than the rent model (0.90).
- **Levels are overstated for the rental stock as a whole.** The sample is units that came to market in 2026, which
  over-represents units that turn over often. The measured rate also climbs toward the crawl (21% in 2019, 32% in
  2025), which is partly this selection, so the 2025 level should not be read as the Bay Area turnover rate.
- **A listing is a proxy for a tenant leaving.** Units re-let without a Zillow listing count as no turnover.
- **Apartment records may be floor plans.** Half the FOR_RENT records were dropped as floor-plan duplicates; some
  remaining apartment records may still stand for a unit type, which would inflate their turnover.
- **Not hand-checked.** No listing histories were read by hand to confirm the 180-day rule.
- **Operating-point columns in `s02_test_metrics.csv` are not comparable across models:** the validation-set
  threshold for "riskiest 20%" flags 50% of 2025 units for LightGBM because scores shifted up.
- **Not wired into the atlas.** The atlas still uses the flat-rate slider.
