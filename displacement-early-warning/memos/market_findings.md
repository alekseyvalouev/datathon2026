# Market signals: flipping, rent at re-listing, price trajectories, affordability (E7, E8, E9, E10)

Scripts: `code/e7_flip_sensitivity.py`, `code/e8_rent_turnover.py`, `code/e9_price_trajectories.py`, `code/e10_affordability.py`. All use the tract join from E4 and the cleaned sales and resale pairs from `code/common.py`.

## E7 Flipping
- Base definition: resale within 18 months at a markup of 20% or more. 3,337 of 57,552 resales that closed 2019-2026 were flips (5.8%), median markup 47%. In 2009-2018 the share was 8.0% (2,146 of 26,710).

| UDP typology | Resales 2019-26 | Flip share (base) | Range across 9 definitions |
|---|---|---|---|
| At Risk of Gentrification | 1,302 | 10.3% | 7.5-13.0% |
| Low-Income/Susceptible | 8,018 | 7.1% | 5.2-8.8% |
| Stable Moderate/Mixed | 21,724 | 5.9% | 3.7-7.9% |
| Ongoing Displacement | 451 | 5.8% | 4.2-9.5% |
| At Risk of Becoming Exclusive | 10,838 | 5.7% | 3.8-7.6% |
| Advanced Gentrification | 2,269 | 4.9% | 2.7-6.7% |
| Stable/Advanced Exclusive | 9,874 | 4.5% | 2.3-6.5% |

- At Risk of Gentrification ranks first in all nine combinations of 12/18/24 months and 10/20/30% markup. Tract rankings are stable (Spearman 0.84-0.96 against the base definition).
- By county: Solano 7.5%, San Mateo 6.7%, Alameda 6.4%, Santa Clara 6.1%, Contra Costa 6.0%, Napa 5.0%, San Francisco 4.8%, Sonoma 3.8%, Marin 3.4%.
- Highest zip codes with at least 80 resales: 94116 San Francisco 17.1%, 94580 San Lorenzo 16.4%, 94112 San Francisco 16.4%, 95148 San Jose 15.5%, 94603 Oakland 15.1%.
- Persistence: zip-level Spearman between 2009-18 and 2019-26 flip share 0.55 (n=193); tract level 0.42 (n=711).
- 89% of flips are single-family homes against 68% of all resales. Across 1,319 tracts flip share correlates with college share at -0.33 and non-white share at +0.29.
- *Limit:* a flip is defined from price and timing alone. Renovation spending, new construction on the same parcel and non-arm's-length sales cannot be separated out.

## E8 Rent at re-listing
- 36,320 pairs of consecutive "Listed for rent" events on the same listing id, 1-6 years apart (26,402 ids).
- Median change +3.0% a year; 16.2% of pairs rose more than 10% a year and 22.1% fell. Pairs ending 2025-26: 20.4% above 10% (n=24,180).
- Share above 10% a year: San Francisco 36.6% (n=4,188), San Mateo 31.1% (3,727), Santa Clara 13.9%, Alameda 11.7%, Contra Costa 7.5%, Solano 6.4%.
- Houses, condos and townhomes only: 8.1% above 10% (n=10,048). Apartment ids can cover a whole building, so this is the cleaner figure.
- **Null.** By typology group the share above 10% is the same (low-income 17.6%, high-income 17.7%); low-income tracts have more declines (28% against 19%).
- California AB 1482 limits yearly increases for sitting tenants to 5% plus regional CPI, or 10%, whichever is lower, and places no limit on the initial rent of a vacant unit (San Francisco government summary). A jump above 10% between listings is legal.
- *Limits:* asking rents, not signed leases; most rental events date from 2024-26. `movement/` E2 models the same quantity with a stricter episode definition; prefer it for the turnover claim.

## E9 Price trajectories
Pooled median sale price per square foot.

| UDP typology | 2012-14 | 2017-19 | 2025-26 | Growth/yr to 2017-19 | Growth/yr after |
|---|---|---|---|---|---|
| At Risk of Gentrification | $141 | $305 | $372 | 16.7% | 2.7% |
| Early/Ongoing Gentrification | $272 | $542 | $534 | 14.8% | -0.2% |
| Low-Income/Susceptible | $197 | $368 | $443 | 13.3% | 2.5% |
| Advanced Gentrification | $450 | $736 | $755 | 10.4% | 0.3% |
| Stable Moderate/Mixed | $298 | $497 | $665 | 10.8% | 3.9% |
| Stable/Advanced Exclusive | $459 | $687 | $990 | 8.4% | 5.0% |

- Same-home repeat sales held 24+ months agree: before 2019 the median was 17.9% a year in At Risk of Gentrification (n=85 pairs) and 11.3% in Low-Income/Susceptible (510) against 8.9% in Stable/Advanced Exclusive (599); for homes bought since 2019 it is 1.3% (255), 1.8% (1,900) and 3.2% (2,432).
- **Reversal.** Zip-level Spearman between pre- and post-2019 growth is -0.32 (204 zips with at least 15 sales per era). The middle period sits in both rates, so noise alone could create a negative value; with four non-overlapping windows it is -0.24 (198 zips).
- Examples: Oakland 94606 +23.0% a year then -2.2%; Oakland 94607 +13.8% then -2.7%; San Francisco 94103 +9.1% then -3.4%. Fastest after 2019: Atherton 94027 (+12.4%), Saratoga 95070 (+8.5%).
- *Limit:* living area and home type are today's values applied to past sales.

## E10 Affordability
982 tracts have at least 5 current asking rents (70,920 listings). Income is the tract median household income from UDP in 2018 dollars, not inflated.

| UDP typology | Tracts | Median asking rent | Median income (2018 $) | Rent / income | Tracts above 50% | Asking vs 2018 census rent |
|---|---|---|---|---|---|---|
| Ongoing Displacement | 19 | $2,950 | $56,146 | 62% | 84% | 2.39x |
| At Risk of Gentrification | 50 | $2,090 | $43,709 | 61% | 72% | 1.76x |
| Low-Income/Susceptible | 191 | $2,425 | $59,172 | 51% | 54% | 1.70x |
| Stable Moderate/Mixed | 377 | $3,068 | $104,500 | 35% | 11% | 1.52x |
| Stable/Advanced Exclusive | 84 | $3,844 | $163,618 | 29% | 4% | 1.42x |

- Sensitivity (an assumption, not data): if every tract's income were 30% higher than in 2018, asking rent would still exceed 30% of income in 90% of Low-Income/Susceptible tracts and 96% of At Risk of Gentrification tracts, against 13% of Stable/Advanced Exclusive tracts.
- Rent-to-value on the same home (annual Zillow rent estimate over value estimate): At Risk of Gentrification 7.0% (n=1,393 homes), Low-Income/Susceptible 6.3% (8,117), Stable Moderate 5.0% (23,283), Stable/Advanced Exclusive 3.9% (9,427).
- *Limits:* income covers all households, owners included, while asking rents are for vacant units; ratios overstate burden to an unknown degree. No CPI adjustment was applied.
