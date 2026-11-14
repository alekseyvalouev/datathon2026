# Experiment A: Asset / capital-capture channel, San Francisco Bay Area (9 counties)

All numbers computed in this session from: PUMS ACS 2019-2023 5-year (CA person + household files), Zillow (all three parts, 148,005 Bay records), Indeed base v2 (45,850 Bay postings, 2024-12 to 2026-09). Scripts: `code/asset_*.py`. Tables: `base/asset_*.csv`.

## Three most important numbers

1. **Capital income is far more concentrated than employment, and the skew is by race.** Non-Hispanic White adults are 36.5% of Bay employed workers but receive **70.7% (SE 0.56) of all interest/dividend/net-rental income (INTP)**, a capital/employment ratio of 1.94. Hispanic adults are 23.6% of workers and get 5.3% (ratio 0.23). Black adults are 5.1% of workers and get 1.2% (ratio 0.24). Asian adults are 29.4% of workers and get 19.6% (ratio 0.67).
2. **The affordability wedge is stark at the median posting.** Bay-wide median posted salary: AI_PRODUCER $214,000, SOFTWARE_ENG $208,000 vs CLERICAL_ADMIN $57,200, CUSTOMER_SUPPORT $61,360, FRONTLINE_SERVICE $44,720. The median CLERICAL_ADMIN job affords local median rent at the 30% threshold in **0 of 25 cities** (under both rent measures); CUSTOMER_SUPPORT 0 of 22; FRONTLINE_SERVICE 0 of 66; AI_PRODUCER affords it in 16 of 23 (Zestimate rent) or 23 of 23 (asking rent).
3. **Housing equity is the larger, more widely held asset, and it splits Black/Hispanic households from White and Asian ones.** Homeownership: White 63.0%, Asian 61.5%, Hispanic 41.3%, Black 36.3%. Bay owner-occupied housing value is $1.90 trillion (self-reported, gross of mortgages). Black households are 5.9% of households but hold 2.6% of that value; Hispanic 18.3% vs 9.5%; White 44.4% vs 52.8%; Asian 26.3% vs 31.0%.

## Data notes (read first)

- **Zillow sample.** The three parts have zero overlapping zpid and together contain 148,005 records. The prompt said the file is statewide and homeStatus is mostly "OTHER"; neither is true here. Every record has state=CA and a county field naming one of the 9 Bay counties (Santa Clara 38,559; Alameda 34,588; Contra Costa 19,512; San Francisco 15,652; San Mateo 13,702; Sonoma 10,216; Solano 8,442; Marin 4,474; Napa 2,860). homeStatus is FOR_RENT 74,343, RECENTLY_SOLD 61,606, FOR_SALE 12,056. I used all three parts because they are disjoint slices of the same population and part 2 alone (78,424 rows) would have been thin for city cells.
- **County match rate.** Zillow's own `county` field is populated for 100% of rows (`countyFIPS` only for 51.5%, so I did not use it). Via the Census place-name crosswalk, 99.43% of rows match a Bay place name; of those, 97.9% agree with Zillow's county field. Disagreements are mainly the duplicate place name "Mountain View" (the crosswalk has a Contra Costa CDP of that name; 2,903 rows are really Santa Clara). I used Zillow's county field and the city name; the crosswalk is validation only.
- **Zestimate coverage.** zestimate on 70,894 rows, rentZestimate on 72,026 (FOR_RENT rows mostly have neither; their `price` is the asking rent). `zestimate_history` (monthly, in $ thousands, 2017-01 onward) exists for 47.5% of rows. Its latest value matches the record's zestimate (median ratio 1.000), which supports reading it as the Zestimate series. The `priceHistory` "Sold" events (189,533) are about 4,000 a year before 2025 and 66,000 in 2025-26, so they cannot support a city price index; I used the Zestimate history instead.
- **PUMS.** Definitions checked against the official 2019-2023 data dictionary (`ext/dict/PUMS_Data_Dictionary_2019-2023.csv`). ADJINC differs by record (five factors, 1.019518 for 2023 up to 1.207712 for 2019; the dictionary says to apply it to INTP, WAGP, PINCP, HINCP etc.). I multiplied every income variable by ADJINC/1,000,000, so all dollars are 2023 dollars. VALP is not adjusted (ADJHSG covers housing costs, not VALP); it is the owner's self-reported value in the survey year, pooled over 2019-2023. Householder = RELSHIPP == 20 (all 139,704 occupied Bay housing units matched exactly one). Race_eth: Hispanic if HISP>1; else RAC1P 1 White, 2 Black, 3/4/5 AIAN, 6 Asian, 7 NHPI, everything else Two-or-Other. Adults = 18+. Employed = ESR in 1,2,4,5. Bay PUMAs (62) are all contained in a single county, so no county-assignment ambiguity (the 7 CA PUMAs that span counties are all outside the Bay). Weights PWGTP/WGTP; standard errors use the 80 replicate weights (successive-difference, variance = 4/80 x sum of squared deviations). Medians have no SE; unweighted counts are reported and cells under 50 are flagged `thin_lt50`.
- **Limit of INTP.** INTP is interest + dividends + net rental income received in the year. It excludes capital gains, RSUs, options, unrealized equity, retirement-account balances and business equity, which is where most Bay Area AI-era equity wealth sits. It is a direct but partial measure of capital income. Top 1% of adults hold 55.9% of net INTP; top 10% hold 99.5%.

## TEST 1: Who holds capital income (MEASURED)

Bay Area adults (n = 306,435 unweighted; 6.11M weighted). INTP total = $35.3 bn vs wages $422.6 bn vs total personal income $536.3 bn, so INTP is 6.6% of personal income. In aggregate, wages dominate; the claim is about who gets the capital slice.

| race_eth | n adults | % with INTP>0 | median INTP, holders | mean INTP, holders | mean INTP, everyone | INTP % of own personal income | **share of capital income (SE)** | share of wage income | **share of employed workers** | capital share / employment share |
|---|---|---|---|---|---|---|---|---|---|---|
| White | 127,601 | 25.1% | $8,682 | $42,604 | $10,656 | 9.7% | **70.7% (0.56)** | 43.9% | 36.5% | **1.94** |
| Asian | 93,233 | 17.9% | $3,623 | $22,303 | $3,956 | 4.2% | **19.6% (0.44)** | 34.3% | 29.4% | **0.67** |
| Hispanic | 56,015 | 6.1% | $2,415 | $22,820 | $1,386 | 2.8% | **5.3% (0.31)** | 13.3% | 23.6% | **0.23** |
| Black | 13,918 | 6.3% | $1,899 | $19,620 | $1,219 | 2.2% | **1.2% (0.13)** | 3.6% | 5.1% | **0.24** |
| Two/Other | 13,492 | 14.1% | $4,233 | $27,955 | $3,931 | 4.6% | 3.0% (0.22) | 4.6% | 4.8% | 0.63 |
| AIAN | 739 | 7.1% | $5,796 | $51,352 | $3,657 | 7.2% | 0.12% (0.04) | 0.10% | 0.16% | 0.77 |
| NHPI | 1,437 | 5.1% | $1,691 | $11,727 | $571 | 1.1% | 0.05% (0.02) | 0.33% | 0.53% | 0.10 |
| All Bay | 306,435 | 17.1% | $5,796 | $33,905 | $5,781 | 6.6% | 100% | 100% | 100% | |

Wage shares and worker shares sum to 100%. The gap between the last two columns is the answer to "who captures gains that flow to capital". AIAN and NHPI cells have under 1,500 observations; treat them as indicative only.

**Not a pure income effect.** Participation among adults with personal income of $100k+ is White 37.4%, Asian 31.2%, Hispanic 20.3%, Black 17.2%; among $50-100k, White 25.6%, Asian 18.6%, Hispanic 8.6%, Black 8.2%; under $50k, White 14.3%, Asian 8.3%, Hispanic 2.7%, Black 2.8%. Part of the raw gap is age (65+ participation is 41.1% for White vs 11.3% for Black), which is a wealth-accumulation difference, not a separate cause.

**Nuance that cuts against a simple "asset holders vs workers" story:** Asian adults are over-represented in wages (34.3% of wage income, 29.4% of workers) and under-represented in INTP (19.6%). They are the most wage-dependent large group (wages are 86.9% of their personal income vs 72.1% for White). Their equity gains, if any, would come through RSUs or housing, which INTP does not capture (see Tests 2 and 5).

By county (full table in `asset_capital_income_by_race_county.csv`; thin cells flagged). Columns: White share of county capital income vs White share of county workers; Black and Hispanic capital/employment ratio.

| county | White capital share | White worker share | White ratio | Asian ratio | Black ratio | Hispanic ratio |
|---|---|---|---|---|---|---|
| Alameda | 61.0% | 29.8% | 2.05 | 0.75 | 0.30 | 0.31 |
| Contra Costa | 75.9% | 39.7% | 1.91 | 0.66 | 0.19 | 0.21 |
| Marin | 92.1% | 67.2% | 1.37 | 0.43 | 0.11 | 0.17 |
| Napa | 86.6% | 49.1% | 1.76 | 0.71 | 0.56 | 0.13 |
| San Francisco | 67.5% | 42.0% | 1.61 | 0.69 | 0.30 | 0.33 |
| San Mateo | 71.3% | 35.3% | 2.02 | 0.58 | 0.24 | 0.26 |
| Santa Clara | 60.7% | 28.1% | 2.16 | 0.74 | 0.41 | 0.21 |
| Solano | 72.6% | 35.1% | 2.07 | 0.84 | 0.43 | 0.20 |
| Sonoma | 89.4% | 59.4% | 1.51 | 0.71 | 0.08 | 0.13 |

The pattern holds in every one of the 9 counties: White ratio 1.37-2.16, Black and Hispanic 0.08-0.56 (Napa Black 0.56 is based on 136 adults and SE 0.89 on a 0.93% share). County-level capital income participation ranges from 9.1% (Solano) to 25.8% (Marin); mean INTP per adult from $2,393 (Solano) to $15,126 (Marin). Thin cells (under 50 adults): Marin AIAN and NHPI, Napa AIAN and NHPI, San Mateo AIAN.

## TEST 2: Homeownership (MEASURED)

Occupied housing units, householder race (RELSHIPP=20), n = 139,704. Value is gross VALP, not net of mortgage (65.7% of White owners and 77.2% of Black owners have a mortgage, TEN=1).

| householder race | n HH | homeownership | median VALP (owners) | owner value held ($bn) | share of owner value (SE) | share of households | value share / HH share | owners in unit 10+ yrs | owners in unit 20+ yrs |
|---|---|---|---|---|---|---|---|---|---|
| White | 67,358 | 63.0% (0.22) | $990,000 | 1,004 | **52.8% (0.23)** | 44.4% | 1.19 | 64.9% | 42.8% |
| Asian | 38,621 | 61.5% (0.32) | $1,000,000 | 588 | **31.0% (0.22)** | 26.3% | 1.18 | 51.3% | 27.0% |
| Hispanic | 20,570 | 41.3% (0.42) | $700,000 | 181 | **9.5% (0.14)** | 18.3% | 0.52 | 63.7% | 37.3% |
| Black | 6,191 | 36.3% (0.72) | $670,000 | 50 | **2.6% (0.08)** | 5.9% | 0.44 | 68.5% | 46.8% |
| Two/Other | 6,180 | 49.1% (0.81) | $900,000 | 72 | 3.8% (0.12) | 4.5% | 0.83 | 52.6% | 29.3% |
| AIAN | 329 | 42.6% (3.32) | $500,000 | 1.7 | 0.09% | 0.19% | 0.47 | 58.5% | 40.6% |
| NHPI | 455 | 41.8% (2.68) | $725,000 | 4.0 | 0.21% | 0.40% | 0.53 | 63.2% | 32.4% |
| All Bay | 139,704 | 56.3% (0.17) | $925,000 | 1,900 | | | | 60.4% | 37.1% |

Median year-moved-in (MV) is a bracket variable; the median owner of every group falls in the "10-19 years" bracket, which is uninformative, so I report the shares in the unit 10+ and 20+ years. Black owners have the longest tenure (46.8% 20+ years), so they captured appreciation per unit despite owning less. Asian owners are the newest (27.0% 20+ years), consistent with recent purchases at high prices and, probably, lower accumulated equity per dollar of value than the value share implies (mortgage balances not measured).

Counties: homeownership is San Francisco 38.6%, Alameda 53.9%, Santa Clara 55.1%, San Mateo 59.2%, Sonoma 62.4%, Solano 62.7%, Marin 63.7%, Napa 65.2%, Contra Costa 67.5%. Black homeownership by county ranges 22.6% (Marin, only 54 households) to 63.5% (Napa, 31 households); the larger cells are Alameda 33.0%, Contra Costa 46.3%, Santa Clara 29.7%, Solano 44.9%. Full race-by-county rows in `asset_homeownership_by_race_county.csv` (14 of 63 race-by-county cells under 50 households, flagged).

**Contradiction to the simple hypothesis:** Asian households own at the same rate as White households and hold housing value above their population share. The housing-equity gap is mainly Black and Hispanic households vs everyone else; it is not White vs everyone else.

## TEST 3: AI job density vs local housing cost (cross-section; NOT causal)

**Limitation, stated up front:** this is a cross-section of 69 cities. Silicon Valley cities were expensive long before generative AI. AI-positioned job share is largely a proxy for "is a Santa Clara/San Mateo/SF tech hub". Nothing here identifies an effect of AI on housing. City set: Indeed cities with at least 50 postings (70 cities; "san francisco bay area" excluded as a non-city), then at least 30 Zillow sale-side Zestimates (drops Stanford, 13). Napa and San Francisco each contribute one city, so their county fixed effects absorb them. Per-city table: `asset_city_jobs_housing.csv` (postings, AI-positioned share, exposed share, median salary by class with n>=10, Zillow medians, appreciation). AI-positioned share ranges 0%-49% (median 4.5%); highest are Mountain View 49%, Sunnyvale 44%, Cupertino 38%, Palo Alto 35%, Menlo Park 32%.

Correlations of AI-positioned share across cities: with log median Zestimate r=0.58 (Spearman 0.60); with log median rentZestimate r=0.50; with log median asking rent r=0.49. Exposed-job share is uncorrelated with home value (r=-0.03) and negatively with AI share (r=-0.41). Within-county (demeaned) correlation with log Zestimate drops to r=0.24.

OLS, HC3 standard errors. Coefficient = change in log housing measure per +10 percentage points of AI-positioned share:

| dependent variable | bivariate | + log sqft, bedrooms | + county FE only | + sqft, beds, county FE |
|---|---|---|---|---|
| log median Zestimate | 0.254 (SE 0.051), p<0.001 | 0.252 (0.040), p<0.001 | 0.105 (0.064), **p=0.10** | 0.132 (0.051), p=0.009 |
| log median rentZestimate | 0.099 (0.020), p<0.001 | 0.099 (0.016), p<0.001 | 0.035 (0.018), **p=0.055** | 0.047 (0.015), p=0.002 |
| log median asking rent | 0.105 (0.019), p<0.001 | 0.104 (0.017), p<0.001 | 0.033 (0.027), **p=0.21** | 0.037 (0.026), **p=0.15** |

Reading: the raw association is strong (+10pp AI share goes with roughly +29% home value). Once county fixed effects are in, it shrinks by half or more and is not significant at the 5% level in four of the six county-FE specifications (Zestimate with county FE only, rentZestimate with county FE only, asking rent in both forms). With sqft/bedroom controls added, the Zestimate and rentZestimate coefficients remain positive and significant (+14% and +5% per 10pp), but asking rent shows nothing distinguishable from zero. **Most of the cross-city relationship is between-county location, not AI job density within a county.** R-squared with county FE alone is 0.56 for home value and 0.55-0.62 for rent.

### 3b. Price change, same-home Zestimate panel (WEAK DESIGN)

Window: Jan 2017 to the last Zestimate month on each record (median end Sept 2026; ends vary Aug-Nov 2026; records must have a final value from June 2026 or later). Same-home balanced panel: homes with both a start and an end value, so composition is fixed. 2023-01 to end: 24,547 / 16,573 / 13,303 homes in high/low/mid terciles. The Zestimate is a model estimate and is smoothed; this is not a transaction price index. Terciles are by AI-positioned share (cutoffs 1.7% and 11.3%); the "high" group is Mountain View, Sunnyvale, Cupertino, Palo Alto, SF, San Mateo, San Jose etc.

| period | high AI-share tercile | mid | low |
|---|---|---|---|
| median same-home change 2017-01 to 2022-12 | +28.1% | +32.2% | +38.0% |
| median same-home change 2023-01 to end (about 3.7 yrs) | **+15.5%** | +4.7% | +4.8% |
| median same-home change 2017-01 to end | +50.1% | +39.5% | +45.6% |
| ratio of median home value, high / low | 1.97 (2017-01), 2.00 (2022-01), 1.88 (2023-01), **2.16 (end)** | | |

The AI-dense premium narrowed during 2017-2022 (high-tercile homes appreciated less), dipped to 1.88 in Jan 2023 (post-rate-shock tech correction), then widened to 2.16 by 2026. So in the raw terciles the premium did widen over 2023-2026. **But this does not survive controls:** city-level regressions of log change on AI share (per +10pp) give 2023-2026: +0.027 bivariate (p<0.001), **+0.004 with county FE (p=0.64)**, +0.008 with controls (p=0.37). For 2017-2022 the coefficient is negative: -0.030 bivariate, -0.025 with county FE (p=0.002). I.e. within a county, AI-dense cities did not appreciate faster in 2023-2026; the widening is a between-county effect (SF 37% value-weighted appreciation, San Mateo 28%, Santa Clara 21%, Marin 21%; vs Alameda 12%, Contra Costa 8%, Sonoma 8%, Solano 7%, Napa 9%). It also coincides with a post-2023 rebound that would have occurred with or without AI. I do not attribute it to AI.

## TEST 4: Affordability wedge (MEASURED medians; ASSUMPTIONS flagged)

Rent burden = annual rent / median posted gross salary. Posted salary is Indeed `sal_mid` (hourly annualized at 2,080 hours; posting midpoint, base pay only, no equity or bonus). Two rent measures: (R1) median rentZestimate of homes in the city/county, which is skewed to houses and condos that sold or are for sale; (R2) median asking rent on FOR_RENT listings (74,305 Bay listings), which is the better proxy for what a renter actually faces. Bay medians: R1 $4,197/mo, R2 $3,108/mo. Cells need at least 10 salaried postings, otherwise they are excluded as thin. City counts use the 70 cities with at least 50 postings that have Zillow rent data.

Cities where the median posted salary clears 30% of income for the local median rent:

| class | cities with usable data | median salary across cities | affords rent, R1 | affords rent, R2 | median burden R1 | median burden R2 | median salary shortfall R1 | shortfall R2 | needed salary / posted, R1 | R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| AI_PRODUCER | 23 | $210,500 | 16 | 23 | 29% | 20% | $0 | $0 | 0.97x | 0.67x |
| SOFTWARE_ENG | 23 | $199,588 | 9 | 22 | 30% | 21% | $2,085 | $0 | 1.01x | 0.70x |
| DATA_ENG_ANALYTICS | 10 | $179,984 | 4 | 10 | 32% | 23% | $10,248 | $0 | 1.05x | 0.75x |
| PROF_EXPOSED | 24 | $102,675 | 0 | 3 | 58% | 39% | $87,028 | $29,013 | 1.92x | 1.31x |
| CLERICAL_ADMIN | 25 | $58,287 | **0** | **0** | 91% | 60% | $119,120 | $63,836 | 3.04x | 2.01x |
| CUSTOMER_SUPPORT | 22 | $59,157 | **0** | **0** | 83% | 56% | $112,970 | $57,660 | 2.78x | 1.87x |
| FRONTLINE_SERVICE | 66 | $43,696 | **0** | **0** | 119% | 84% | $132,470 | $77,935 | 3.96x | 2.80x |
| AI_DATA_WORK | 1 | $156,000 | 0 | 0 | 47% | 30% | | | | |

AI_DATA_WORK: **do not interpret.** 125 of 143 salaried Bay postings are one vendor (DataAnnotation) at a flat $75/hour; 94% are hourly, 89% contract, 87% part-time. Annualizing at 2,080 hours gives $156,000, which is not an attainable annual income for a part-time contractor. Only 1 city (SF) has enough postings, and its burden is borderline either way. At a county level with n>=10 it affords R1 in 2 of 5 counties and R2 in 4 of 5, but that is an annualization artifact. At half-time hours ($78,000) the Bay-wide burden would be 65% (R1) or 48% (R2).

Bay-wide gap, median posting vs median rent (needed salary at 30%: **$167,880** under R1, **$124,320** under R2):

| class | median posted salary | burden R1 | burden R2 | shortfall R1 | shortfall R2 | AI_PRODUCER salary as multiple of class |
|---|---|---|---|---|---|---|
| AI_PRODUCER | $214,000 | 23.5% | 17.4% | $0 | $0 | 1.0x |
| SOFTWARE_ENG | $208,000 | 24.2% | 17.9% | $0 | $0 | 1.03x |
| CUSTOMER_SUPPORT | $61,360 | 82.1% | 60.8% | $106,520 | $62,960 | 3.5x |
| CLERICAL_ADMIN | $57,200 | 88.0% | 65.2% | $110,680 | $67,120 | 3.7x |
| FRONTLINE_SERVICE | $44,720 | 112.6% | 83.4% | $123,160 | $79,600 | 4.8x |

County x class matrix (R1 and R2 burdens, salaries, n) is in `asset_rent_burden_matrix.csv` (`level` = county or city; `thin_lt10` flags cells to ignore). Example: San Mateo CLERICAL_ADMIN burden 111% (R1) / 79% (R2); Santa Clara SOFTWARE_ENG 27% / 20%; San Francisco FRONTLINE_SERVICE 141% / 91%. The best case for non-AI workers is Solano: CUSTOMER_SUPPORT 67% (R1) / 51% (R2), FRONTLINE 86% / 65%; still above 30%. 

**Caveats:** (i) posted salary is a posting midpoint for a flow of new postings, not the wage of current workers; many Indeed postings are in the city of the employer, while workers may live elsewhere. (ii) Single-earner, gross-pay, full-time assumption; households pool incomes and pay rent from after-tax income, so true burdens are higher on a net basis and lower for dual-earner households. (iii) A median rent for the median listing is not the rent for a small unit. The 30% line is a convention. Even under the more favorable measure (R2), no county median for CLERICAL_ADMIN, CUSTOMER_SUPPORT, FRONTLINE_SERVICE or PROF_EXPOSED reaches 30%, and PROF_EXPOSED does so in only 3 cities. Health clinical (Solano 28%, Sonoma 30%) and a few small design/education cells are the only other non-AI cells near the line.

**Combining with Test 2 (stated plainly):** The groups positioned to be paid in appreciating assets are White and Asian households (63.0% and 61.5% owners, holding 52.8% and 31.0% of owner-occupied value) and, for non-housing capital income, White adults above all (70.7% of INTP). The groups positioned to pay rent to them are Black and Hispanic households (63.7% and 58.7% renters; 5.9% and 18.3% of households but 2.6% and 9.5% of owner value), and workers in the clerical, customer support and frontline classes whose median posted pay cannot meet median rent anywhere in the Bay at the 30% standard. This is a statement about positions in asset and rental markets. The data here do not show which individuals fill which jobs by race (that is a labor-side experiment), and PUMS race by occupation is not combined with Indeed postings in this experiment.

## TEST 5: Home-equity capture accounting estimate (ASSUMED; not causal, not attributable to AI)

**What this is.** An accounting identity: owner-occupied housing value held by each race group (Test 2, PUMS VALP by county) x measured county Zestimate appreciation from Jan 2023 to about Sept 2026 (3.67 years). It is unrealized, gross of mortgage debt, and says nothing about causes. A rising market since 2023 may or may not be connected to AI; this estimate cannot say.

**Assumptions (each a source of error):**
1. PUMS VALP (self-reported, pooled 2019-2023) is treated as the Jan 2023 value. Owners probably under- or over-state value; the pooled survey midpoint is mid-2021, and I did not model the 2021-2023 change (same-home Zestimates rose about 2% in the high-AI tercile and about 8% in the low tercile over 2021-01 to 2023-01), so the base may be slightly understated.
2. All groups in a county experience that county's appreciation rate. Within-county neighborhood differences are not modeled (PUMS does not give city), so if Black or Hispanic owners live in slower-appreciating neighborhoods their gain is overstated here, and vice versa.
3. County appreciation comes from the same-home Zestimate panel (homes sold or for sale, so skewed to the market segment that trades). Scenario A uses value-weighted growth (Bay-wide +19.2%); scenario B uses the median home's growth (a conservative bound, roughly half).
4. Gross value, not equity: mortgage balances are not netted (70% of Bay owners have a mortgage). Wage comparison uses the annual wage bill of all adults 18+ (2023 dollars), as a level, not a wage gain.
5. Wages are PUMS 2019-2023 pooled in 2023 dollars, so this compares annualized appreciation to a wage level; wage growth over the same period is not measured here.

County appreciation, Jan 2023 to end (value-weighted / median home): San Francisco +37.1% / +23.9%; San Mateo +28.2% / +15.4%; Marin +20.8% / +11.5%; Santa Clara +20.7% / +13.3%; Alameda +11.8% / +6.0%; Napa +8.9% / +2.6%; Sonoma +8.4% / +5.5%; Contra Costa +7.7% / +3.4%; Solano +6.6% / +4.1%.

Scenario A (value-weighted), Bay owner-occupied value $1,900 bn; estimated gross appreciation $357 bn total, $97 bn per year; annual wage bill $423 bn:

| race_eth | owner value ($bn) | est. appreciation 2023-26 ($bn) | per year ($bn) | annual wage income ($bn) | annual appreciation / annual wages (SE) | share of appreciation | share of wages | share of households | appreciation per owner HH per yr | wage per employed worker per yr |
|---|---|---|---|---|---|---|---|---|---|---|
| White | 1,004 | 186.0 | 50.7 | 185.3 | **0.27** (0.002) | 52.1% | 43.8% | 44.4% | $65,144 | $128,822 |
| Asian | 588 | 118.2 | 32.2 | 144.8 | **0.22** (0.003) | 33.1% | 34.3% | 26.3% | $71,498 | $125,019 |
| Hispanic | 181 | 31.4 | 8.6 | 56.3 | **0.15** (0.003) | 8.8% | 13.3% | 18.3% | $40,679 | $60,601 |
| Black | 50 | 7.1 | 1.9 | 15.2 | **0.13** (0.005) | 2.0% | 3.6% | 5.9% | $32,386 | $75,129 |
| Two/Other | 72 | 13.3 | 3.6 | 19.3 | 0.19 (0.007) | 3.7% | 4.6% | 4.5% | $58,478 | $102,101 |
| All Bay | 1,900 | 357 | 97.4 | 422.6 | **0.23** | | | | $62,055 | $107,179 |

Scenario B (median-home growth): Bay appreciation $210 bn total, $57 bn/yr, ratio to annual wages 0.14; White 0.16, Asian 0.13, Hispanic 0.09, Black 0.07. Shares of appreciation barely change (White 51.7%, Asian 33.7%, Hispanic 8.7%, Black 1.9%).

Reading (scale): across the Bay, estimated unrealized housing appreciation (owner-occupied, gross) is equivalent to about 14%-23% of the annual wage bill each year over the window. For an owner household the gain per year ($65k White, $71k Asian, $41k Hispanic, $32k Black) is about half to the same size as one worker's wages ($129k, $125k, $61k, $75k); for Black owner households it is 43% of a worker's mean wage, for Asian 57%, White 51%, Hispanic 67%. **Wages remain the larger flow in aggregate for every race group (ratios all below 0.3).** What differs by race is the add-on: the housing gain is the same order as earned income for owners, while it is zero for renters (Black 63.7% and Hispanic 58.7% of households). Per household (spreading over renters too) the annual gain is $44k Asian, $41k White, $28.7k Two/Other, $16.8k Hispanic, $11.8k Black. County-level race x county rows, including thin flags, are in `asset_equity_capture.csv`; San Francisco and San Mateo ratios run 0.3-0.5 for White households (SF 0.33, San Mateo 0.51), Contra Costa and Solano 0.12 and 0.09.

## Solid vs fragile

**Solid (direct measurement, large samples, SEs small):** the INTP concentration by race (Test 1); homeownership and owner-value shares by race (Test 2, except AIAN/NHPI and thin county cells); the rent-burden pattern for clerical/support/frontline vs software/AI-producer jobs (Test 4) at the Bay and county level; the raw correlation of AI job share with housing cost (Test 3a, bivariate).

**Fragile or assumption-driven:** AI-density effects within county (Test 3a with county FE; 3b), which are statistically weak or null; the appreciation dollar estimates (Test 5: VALP-as-2023-value, county-uniform appreciation, Zestimate model values, gross not net); the AI_DATA_WORK affordability (annualization artifact); city-level class medians outside SF, San Jose, Santa Clara and a few others (n>=10 postings, often 10-30); Indeed posted salaries as wages.

## What contradicts or complicates "asset holders capture more than workers"

- In aggregate, wages dwarf measured capital income: INTP is $35 bn vs wages $423 bn (6.6% of personal income). The capture asymmetry is about who holds the capital slice, not about capital being larger than labor.
- Estimated housing appreciation is 14-23% of the annual wage bill, below it in every race group. Gains from housing are meaningful but do not exceed wages in aggregate.
- Asian households own homes at White rates (61.5% vs 63.0%) and hold more owner-occupied value than their population share (1.18x), while receiving little INTP (0.67x). The "asset-poor" group on the housing side is Black and Hispanic households, not Asian.
- AI job density does not reliably predict housing costs within a county: asking-rent coefficients are not distinguishable from zero (p=0.15-0.21 with county FE), Zestimate with county FE alone is p=0.10, and 2023-2026 appreciation is unrelated to AI share within county (p=0.64).
- The premium in AI-dense cities did widen in raw terciles in 2023-2026 (ratio 1.88 to 2.16), but it narrowed in 2017-2022 and the widening is explained by which counties (SF, San Mateo, Santa Clara) rebounded; I do not claim an AI effect.
