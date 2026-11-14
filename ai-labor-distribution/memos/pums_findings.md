# AI exposure and the distribution of Bay Area wages: worker-level microdata (ACS PUMS)

*Experiment P. Source: ACS 2019-2023 5-Year PUMS (California persons) and ACS 2024 1-Year PUMS. Bay Area = 9 counties, employed persons age 16+ (ESR 1,2,4,5). Every number in this memo is computed by `code/pums_*.py` from the files in `base/`. Standard errors (in parentheses; percentage points for shares) use the 80 successive-difference replicate weights. Cells with fewer than 50 unweighted observations are shown as `s` (suppressed).*

## Three headline numbers

1. **AI-positioned jobs (AI producer + software + data/analytics) are held mostly by Asian workers.** Asian workers are 58.4% of AI-positioned employment against 29.3% of all employment (representation index 1.99, SE 0.02). White workers are 29.9% (index 0.82), Black workers 1.8% (index 0.36), Hispanic workers 5.7% (index 0.24). The AI-positioned set is 8.2% of Bay Area employment (about 324,387 workers); the exposed set (clerical + customer support + exposed professional) is 13.7% (about 543,689 workers).
2. **The prize is large.** Median full-time-year-round wage in AI-positioned classes is $178,416 vs $81,143 in exposed classes, a gap of $97,273 (SE $859), ratio 2.20. Median hourly wage is $81.40 vs $34.84. Wage mass in exposed occupations is $46.6B/yr (11.3% of Bay Area wage and salary mass), against $65.0B (15.8%) in AI-positioned classes (2023 dollars).
3. **Black workers are both more exposed and more shut out of the gains, and the wage gap is widest exactly inside the AI classes.** Black workers' exposed share is 16.2% (index 1.19; Bay Area 13.7%), their AI-positioned share is 2.9%, so the exposed-to-AI-positioned ratio is 5.55 (White 2.09, Asian 0.86, Hispanic 6.00). Inside AI_PRODUCER/SOFTWARE_ENG, Black workers earn 35% less per hour than White workers in the same classes (unadjusted; 30% after controls for age, sex, education, county, nativity); inside the exposed classes the gap is 13% (9% adjusted). Difference in log gaps -0.287 (SE 0.068).

**What does not fit a simple "AI hurts the already-disadvantaged" story** (full list in the disconfirming-evidence section): Hispanic workers are *under*-represented in the exposed classes (index 0.87); Asian and White workers sit at parity with each other on exposure (indices 1.02 and 1.02); exposed workers are *less* likely than average to be self-employed; and White workers, the highest-paid large group, are *under*-represented in AI-positioned jobs (index 0.82).

## 0. Data, definitions, coverage

* **Population.** Bay Area (Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, Solano, Sonoma), persons 16+, ESR in 1,2,4,5. This includes ESR 4/5 (armed forces); military occupations fall in OTHER (see below). Group-quarters persons are in PUMS and retained if employed.
* **Race/ethnicity** (mutually exclusive): Hispanic (HISP>1, any race); among non-Hispanic: White, Black, Asian, AIAN (RAC1P 3,4,5), NHPI (RAC1P 7), Two_or_Other (RAC1P 8 or 9). `Asian` is one aggregate: PUMS RAC1P cannot separate e.g. Indian from Vietnamese or Filipino workers, and the Bay Area Asian category is very heterogeneous. This memo cannot speak to within-Asian dispersion.
* **County.** The 2019-2023 5-year file uses 2020-definition PUMAs (checked in the official data dictionary). PUMA to county built from `tract2puma.txt` (county of the PUMA's tracts; dominant county by tract count). **All 62 Bay Area PUMAs lie entirely inside one county** (every Bay Area PUMA has 100% of tracts in one county), so county assignment introduces zero ambiguity for the Bay Area. Seven PUMAs elsewhere in California span counties; none of them contains a Bay Area worker (0 Bay Area person records fall in a split PUMA). Crosswalk: `base/puma_county_xwalk.csv`.
* **Dollars.** WAGP and PERNP are multiplied by ADJINC/1,000,000. In the 5-year file ADJINC converts each respondent's survey-year income into **2023 dollars** (factors 1.2077 for 2019 down to 1.0195 for 2023 in the dictionary's labels); in the 2024 1-year file the single factor 1.015250 gives **2024 dollars**. Dollar levels in the two files are therefore not directly comparable (only shares are compared in test g).
* **Hourly wage** = adjusted WAGP / (WKHP x WKWN). WKWN in these vintages is the exact count of weeks worked (not the older bracketed WKW), so no bracket midpoint is needed. Wage analyses use wage-and-salary workers (COW 1-5) with WAGP>0, WKHP>0, WKWN>0 and hourly wage between $5 and $500 (the trim drops 3,996 persons of 169,482 wage workers with a computable hourly wage). Note WAGP excludes self-employment income. `ftfy` = WKHP>=35 and WKWN>=50. Annual wage mass uses all employed persons with WAGP>0 (part-year included).
* **Contract flag.** `self_employed` = COW 6 or 7 (own business, unincorporated or incorporated). PUMS cannot isolate 1099 independent contractors or gig work from business owners, so this is an upper bound on contract work and a mix of entrepreneurship and precarity.
* **Weights.** PWGTP for all estimates. The 5-year weights are annualized (average year 2019-2023), so weighted counts are comparable to a single year.

**Sample counts by race/ethnicity (employed Bay Area workers 16+)**

| race_eth | n unweighted (2019-23) | n weighted (2019-23) | share | n unweighted (2024) | n weighted (2024) |
|---|---|---|---|---|---|
| White | 74,319 | 1,447,256 | 36.5% | 14,465 | 1,333,167 |
| Black | 7,070 | 202,832 | 5.1% | 1,374 | 200,915 |
| Asian | 60,625 | 1,162,612 | 29.3% | 13,604 | 1,260,626 |
| Hispanic | 37,278 | 938,186 | 23.6% | 8,049 | 971,625 |
| AIAN | 361 | 6,170 | 0.2% | 90 | 7,181 |
| NHPI | 893 | 21,030 | 0.5% | 148 | 19,114 |
| Two_or_Other | 9,096 | 191,120 | 4.8% | 2,156 | 221,723 |
| All | 189,642 | 3,969,206 | 100.0% | 39,886 | 4,014,351 |


AIAN (n=361) and NHPI (n=893) are small in the 5-year file and nearly unusable in the 2024 file (AIAN n=90, NHPI n=148); most of their class-level cells are suppressed.

### Occupation taxonomy: verification and the OTHER class

The OCCP list (531 codes, identical in the 2019-2023 and 2024 data dictionaries apart from capitalization of three titles) was read from the official Census PUMS data dictionaries (`PUMS_Data_Dictionary_2019-2023.csv` and `PUMS_Data_Dictionary_2024.csv`, downloaded from www2.census.gov). Every OCCP code present in the data exists in the dictionary (asserted in code). Classification starts from the dictionary's own major-group prefixes in each title (MGR, BUS, FIN, CMM, ENG, SCI, CMS, LGL, EDU, ENT, MED, HLS, PRT, EAT, CLN, PRS, SAL, OFF, FFF, CON, EXT, RPR, PRD, TRN, MIL) and then applies explicit code-level overrides; nothing is a guessed numeric range. Full audit table with titles, rule applied and Bay Area counts: `base/occp_crosswalk.csv`.

**OTHER holds 267,550 weighted employed Bay Area workers (6.7%; 13,826 unweighted).** By source group: SCI 89,374, CMS 60,842, ENT 48,928, LGL 45,958, FFF 16,939, MIL 5,509. The 10 largest unclassified codes:

| OCCP | official title | n unw | weighted |
|---|---|---|---|
| 2100 | LGL-Lawyers, And Judges, Magistrates, And Other Judicial Workers | 2,538 | 45,958 |
| 1760 | SCI-Physical Scientists, All Other | 1,795 | 32,238 |
| 6050 | FFF-Other Agricultural Workers | 556 | 13,876 |
| 2014 | CMS-Social Workers, All Other | 587 | 12,708 |
| 1650 | SCI-Other Life Scientists | 603 | 11,329 |
| 2600 | ENT-Artists And Related Workers | 560 | 11,086 |
| 1825 | SCI-Other Psychologists | 527 | 9,092 |
| 2722 | ENT-Coaches and Scouts | 404 | 8,359 |
| 2002 | CMS-Educational, Guidance, And Career Counselors And Advisors | 416 | 7,960 |
| 1970 | SCI-Other Life, Physical, And Social Science Technicians | 367 | 7,547 |


Judgment calls to check: (i) **lawyers (2100)** are in OTHER because the spec lists only paralegals under PROF_EXPOSED; (ii) **scientists and technicians (SCI)**, community/social service (CMS) and arts/media (ENT, other than writers/editors/designers) have no class in the spec; (iii) **farm occupations** and **military** are OTHER; (iv) **0705 Project Management Specialists** is placed in PRODUCT_DESIGN as the nearest separable proxy for product/program managers (it is a generic occupation, so PRODUCT_DESIGN is not a clean "product" group; it is outside both headline sets, so it does not affect the exposure ratio); (v) postal/courier/shipping-receiving clerks (5510, 5530, 5550, 5560, 5610, 5630) are put in FRONTLINE_SERVICE, not CLERICAL_ADMIN, because they are physical logistics work. Sensitivity: moving those six codes into CLERICAL_ADMIN raises the Bay Area exposed share from 13.7% to 14.5% and leaves the ordering of groups unchanged (Black index 1.20, Hispanic 0.90, Asian 1.02, White 1.00; `base/exposure_by_race_altmap.csv`).

**AI_PRODUCER is very small and coarse.** PUMS occupation detail cannot isolate ML engineers: AI_PRODUCER = OCCP 1005 (computer and information research scientists) + 1240 (other mathematical science occupations, which hold data scientists, statisticians and mathematicians; in the 5-year file SOCP for 1240 is the aggregate code 1520XX, so data scientists cannot be split out). It has 1,194 unweighted / 22,045 weighted Bay Area workers (0.56% of employment). Software developers (1021, SOCP 151252 only) cannot be split into ML versus other developers, so they sit in SOFTWARE_ENG. Race-specific AI_PRODUCER results are therefore thin and mostly suppressed; headline tests use the combined AI-positioned set (AI_PRODUCER + SOFTWARE_ENG + DATA_ENG_ANALYTICS), of which SOFTWARE_ENG is 92%.

## 1. Test (a): exposure composition by race/ethnicity

Bay Area, 2019-2023. "Exposed" = CLERICAL_ADMIN + CUSTOMER_SUPPORT + PROF_EXPOSED. "AI-positioned" = AI_PRODUCER + SOFTWARE_ENG + DATA_ENG_ANALYTICS. Shares are of the group's employed workers (SE in pp). Concentration ratio = exposed share / AI-positioned share. Representation index (RI) = group share of the class / group share of all employment (= P(class|group)/P(class)); 1.00 = proportional.

| race_eth | n unw | exposed share (se pp) | AI-positioned share (se pp) | conc. ratio (se) | RI exposed (se) | RI AI-pos (se) | group share of all exposed workers | group share of all AI-pos workers |
|---|---|---|---|---|---|---|---|---|
| White | 74,319 | 14.0% (0.1) | 6.7% (0.1) | 2.09 (0.05) | 1.02 (0.01) | 0.82 (0.01) | 37.3% | 29.9% |
| Black | 7,070 | 16.2% (0.5) | 2.9% (0.2) | 5.55 (0.51) | 1.19 (0.04) | 0.36 (0.03) | 6.1% | 1.8% |
| Asian | 60,625 | 14.0% (0.2) | 16.3% (0.2) | 0.86 (0.01) | 1.02 (0.01) | 1.99 (0.02) | 30.0% | 58.4% |
| Hispanic | 37,278 | 11.9% (0.2) | 2.0% (0.1) | 6.00 (0.25) | 0.87 (0.01) | 0.24 (0.01) | 20.5% | 5.7% |
| AIAN | 361 | s | s | s | s | s | s | s |
| NHPI | 893 | 16.1% (1.6) | s | s | 1.18 (0.12) | s | 0.6% | s |
| Two_or_Other | 9,096 | 15.3% (0.5) | 6.7% (0.3) | 2.27 (0.13) | 1.12 (0.04) | 0.82 (0.03) | 5.4% | 4.0% |
| All | 189,642 | 13.7% (0.1) | 8.2% (0.1) | 1.68 (0.02) | 1.00 (0.00) | 1.00 (0.00) | 100.0% | 100.0% |


**Reading.** Only Black workers (RI 1.19, SE 0.04) and Two_or_Other (RI 1.12) are clearly over-represented in exposed occupations; Asian (1.02) and White (1.02) are at parity; Hispanic workers are **under**-represented (0.87, SE 0.01). That Hispanic under-representation is a real, statistically solid null/negative result for the 'minority workers are more exposed' hypothesis: Hispanic workers are concentrated instead in FRONTLINE_SERVICE (RI 1.68) and SKILLED_TRADE, which this taxonomy treats as not exposed to AI task automation. The group differences in AI-positioning are far larger than in exposure: the ratio of exposed to AI-positioned share runs from 0.86 (Asian) to 6.00 (Hispanic) and 5.55 (Black), driven almost entirely by the denominator.

*Gender.* Women are 67.6% of exposed workers (clerical work is female-dominated) vs 46.0% of all employed workers. Within sex, exposed shares are much closer across race: women White 20.2%, Black 22.0%, Asian 19.7%, Hispanic 19.4%; men White 8.9%, Black 10.6%, Asian 8.8%, Hispanic 5.9% (`base/exposure_by_race_sex.csv`). Among women, exposed shares are within about 3 pp across these four groups; the race differences are larger among men (Hispanic men are the least exposed, Black men the most). Male share of the workforce is similar for Hispanic (54.5%) and White (54.3%) workers (unweighted), so the Hispanic under-exposure is not a sex-composition artifact: it is a lower exposed share among Hispanic men (and slightly among women). Race differences in exposure are small next to the gender difference (women vs men roughly 20% vs 8-9%).

**Full class composition** (share of each group's workers; `s` = fewer than 50 unweighted workers in the cell):

| occ_class | White | Black | Asian | Hispanic | AIAN | NHPI | Two_or_Other | All |
|---|---|---|---|---|---|---|---|---|
| AI_PRODUCER | 0.6% | s | 0.9% | 0.1% | s | s | 0.6% | 0.6% |
| SOFTWARE_ENG | 6.0% | 2.6% | 15.2% | 1.8% | s | s | 6.0% | 7.5% |
| DATA_ENG_ANALYTICS | 0.2% | s | 0.2% | s | s | s | s | 0.1% |
| OTHER_ENGINEERING | 4.0% | 1.6% | 7.3% | 1.5% | s | s | 3.9% | 4.2% |
| PRODUCT_DESIGN | 1.9% | s | 1.7% | 0.7% | s | s | 1.8% | 1.5% |
| CLERICAL_ADMIN | 5.9% | 7.9% | 5.5% | 6.4% | s | 8.3% | 6.7% | 6.0% |
| CUSTOMER_SUPPORT | 1.9% | 3.6% | 2.2% | 2.5% | s | s | 2.7% | 2.3% |
| PROF_EXPOSED | 6.3% | 4.7% | 6.4% | 3.0% | s | s | 5.9% | 5.4% |
| HEALTH_CLINICAL | 7.2% | 12.3% | 11.3% | 6.6% | s | 16.5% | 7.6% | 8.6% |
| EDUCATION | 7.7% | 5.9% | 3.9% | 4.2% | s | s | 6.5% | 5.6% |
| FRONTLINE_SERVICE | 16.0% | 32.2% | 16.2% | 37.5% | 30.3% | 28.8% | 22.5% | 22.4% |
| SKILLED_TRADE | 6.5% | 5.7% | 6.3% | 18.5% | s | 13.1% | 6.6% | 9.3% |
| SALES_BIZ | 7.9% | 4.3% | 4.7% | 3.5% | s | s | 6.2% | 5.6% |
| MANAGEMENT | 19.2% | 10.9% | 13.3% | 8.4% | s | 9.7% | 15.0% | 14.2% |
| OTHER | 8.8% | 7.2% | 5.1% | 5.3% | s | s | 7.9% | 6.7% |


## 2. Test (b): by county

Exposed share (SE in pp) by county and race; `s` = suppressed (<50 unweighted workers in the cell, or group n<50). Full table incl. AI-positioned shares, ratios, RIs and SEs: `base/exposure_by_race_county.csv`.

| county | White | Black | Asian | Hispanic | AIAN | NHPI | Two_or_Other | All |
|---|---|---|---|---|---|---|---|---|
| Alameda | 13.9% (0.3) | 16.6% (1.0) | 14.7% (0.4) | 12.2% (0.5) | s | 16.6% (2.7) | 14.7% (1.1) | 14.1% (0.2) |
| Contra Costa | 15.0% (0.5) | 15.4% (1.3) | 16.2% (0.6) | 11.3% (0.5) | s | s | 16.5% (1.3) | 14.3% (0.3) |
| Marin | 14.3% (0.7) | s | 15.6% (2.0) | 9.1% (1.3) | s | s | s | 13.5% (0.6) |
| Napa | 11.8% (0.9) | s | 16.9% (2.4) | 11.4% (1.1) | s | s | s | 12.5% (0.6) |
| San Francisco | 14.1% (0.5) | 16.7% (2.0) | 16.7% (0.5) | 14.4% (0.7) | s | s | 16.5% (1.6) | 15.3% (0.3) |
| San Mateo | 13.5% (0.5) | s | 16.1% (0.5) | 12.2% (0.7) | s | s | 16.3% (1.7) | 14.2% (0.3) |
| Santa Clara | 13.2% (0.3) | 16.0% (1.6) | 11.1% (0.3) | 11.8% (0.4) | s | s | 12.0% (1.0) | 12.1% (0.2) |
| Solano | 13.8% (0.7) | 17.3% (1.4) | 15.5% (1.0) | 11.9% (0.8) | s | s | 17.5% (2.0) | 14.3% (0.4) |
| Sonoma | 15.1% (0.5) | s | 11.3% (1.5) | 10.4% (0.6) | s | s | 17.0% (2.3) | 13.6% (0.4) |


AI-positioned share (SE in pp):

| county | White | Black | Asian | Hispanic | AIAN | NHPI | Two_or_Other | All |
|---|---|---|---|---|---|---|---|---|
| Alameda | 6.9% (0.2) | 2.2% (0.3) | 16.4% (0.4) | 2.0% (0.2) | s | s | 6.3% (0.7) | 8.5% (0.1) |
| Contra Costa | 4.3% (0.3) | s | 10.9% (0.6) | 1.1% (0.1) | s | s | 4.5% (0.8) | 4.5% (0.2) |
| Marin | 3.8% (0.4) | s | s | s | s | s | s | 3.7% (0.3) |
| Napa | s | s | s | s | s | s | s | 1.7% (0.2) |
| San Francisco | 10.6% (0.4) | s | 11.3% (0.5) | 5.7% (0.6) | s | s | 10.2% (1.1) | 9.8% (0.2) |
| San Mateo | 7.0% (0.4) | s | 12.0% (0.5) | 2.0% (0.2) | s | s | 6.6% (1.0) | 7.3% (0.2) |
| Santa Clara | 10.4% (0.3) | 7.6% (1.4) | 22.8% (0.4) | 2.1% (0.2) | s | s | 9.9% (0.9) | 13.4% (0.2) |
| Solano | 2.0% (0.3) | s | s | s | s | s | s | 2.0% (0.2) |
| Sonoma | 2.5% (0.2) | s | s | s | s | s | s | 2.0% (0.1) |


Exposed / AI-positioned ratio (suppressed when either cell has <50 workers; ratios above ~10 are driven by very small AI-positioned counts):

| county | White | Black | Asian | Hispanic | AIAN | NHPI | Two_or_Other | All |
|---|---|---|---|---|---|---|---|---|
| Alameda | 2.00 | 7.50 | 0.89 | 6.02 | s | s | 2.32 | 1.66 |
| Contra Costa | 3.49 | s | 1.49 | 10.38 | s | s | 3.65 | 3.19 |
| Marin | 3.80 | s | s | s | s | s | s | 3.63 |
| Napa | s | s | s | s | s | s | s | 7.18 |
| San Francisco | 1.34 | s | 1.48 | 2.52 | s | s | 1.62 | 1.56 |
| San Mateo | 1.94 | s | 1.35 | 6.22 | s | s | 2.45 | 1.95 |
| Santa Clara | 1.27 | 2.11 | 0.49 | 5.53 | s | s | 1.21 | 0.90 |
| Solano | 6.91 | s | s | s | s | s | s | 7.21 |
| Sonoma | 5.92 | s | s | s | s | s | s | 6.67 |


**Most exposed county-by-race cells (exposed share, unsuppressed):**

| county | race | n group | n exposed | exposed share (se) | RI |
|---|---|---|---|---|---|
| Solano | Two_or_Other | 644 | 105 | 17.5% (2.0) | 1.23 |
| Solano | Black | 858 | 156 | 17.3% (1.4) | 1.21 |
| Sonoma | Two_or_Other | 531 | 73 | 17.0% (2.3) | 1.25 |
| Napa | Asian | 375 | 57 | 16.9% (2.4) | 1.35 |
| San Francisco | Asian | 7,580 | 1,287 | 16.7% (0.5) | 1.09 |
| San Francisco | Black | 672 | 103 | 16.7% (2.0) | 1.09 |
| Alameda | Black | 2,612 | 436 | 16.6% (1.0) | 1.18 |
| Alameda | NHPI | 321 | 58 | 16.6% (2.7) | 1.18 |


**Least exposed:**

| county | race | n group | n exposed | exposed share (se) | RI |
|---|---|---|---|---|---|
| Sonoma | Asian | 597 | 72 | 11.3% (1.5) | 0.83 |
| Contra Costa | Hispanic | 5,628 | 702 | 11.3% (0.5) | 0.79 |
| Santa Clara | Asian | 22,254 | 2,556 | 11.1% (0.3) | 0.92 |
| Sonoma | Hispanic | 2,684 | 321 | 10.4% (0.6) | 0.76 |
| Marin | Hispanic | 763 | 78 | 9.1% (1.3) | 0.67 |


The county-by-race spread in exposed share is narrow (about 9% to 18%) and many top-ranked cells differ by less than two standard errors, so the ranking among the top cells should not be over-read. The robust county pattern is the contrast in the *AI-positioned* column, not the exposed column.

**Where AI-positioned employment is concentrated** (share of all Bay Area AI-positioned workers; location quotient = county AI-positioned share of its employment / Bay Area share):

| county | n AI-pos unw | share of Bay AI-pos workers (se pp) | LQ AI-pos (se) | share of Bay exposed workers | share of all Bay employment |
|---|---|---|---|---|---|
| Alameda | 3,950 | 22.6% (0.4) | 1.04 (0.02) | 22.3% | 21.8% |
| Contra Costa | 1,269 | 7.9% (0.3) | 0.55 (0.02) | 15.0% | 14.4% |
| Marin | 211 | 1.5% (0.1) | 0.46 (0.04) | 3.2% | 3.2% |
| Napa | 75 | 0.4% (0.0) | 0.21 (0.03) | 1.5% | 1.7% |
| San Francisco | 2,241 | 14.6% (0.3) | 1.20 (0.03) | 13.6% | 12.2% |
| San Mateo | 1,638 | 8.9% (0.2) | 0.89 (0.02) | 10.4% | 10.0% |
| Santa Clara | 6,862 | 41.4% (0.4) | 1.64 (0.02) | 22.2% | 25.2% |
| Solano | 201 | 1.3% (0.1) | 0.24 (0.02) | 5.6% | 5.3% |
| Sonoma | 277 | 1.6% (0.1) | 0.25 (0.02) | 6.2% | 6.3% |


Santa Clara holds 41.4% of Bay Area AI-positioned workers from 25.2% of employment; Santa Clara, Alameda and San Francisco together hold 78.6%. Exposed employment, in contrast, is spread in proportion to employment (Santa Clara actually has a *below*-proportional share of exposed workers). The geography of AI gains is far more concentrated than the geography of exposure. Share of each group's workers living in the five counties where the AI-positioned LQ is below 0.6 (Contra Costa, Marin, Napa, Solano, Sonoma): White 39.1%, Black 38.8%, Asian 14.7%, Hispanic 35.7%, Two_or_Other 34.6%, All 30.9%. Location therefore separates Asian workers (concentrated in the high-AI counties) from everyone else; it does **not** separate Black or Hispanic workers from White workers, whose shares in the low-AI counties are similar.

## 3. Test (c): wages

Wage-and-salary workers, 2023 dollars. Medians are weighted. `s` = fewer than 50 unweighted observations. Full table (medians, means, FTFY annual, ratios to White, SEs, counts): `base/wages_by_occclass_race.csv`.

**Median hourly wage ($) by class group x race** (AIPS2 = AI_PRODUCER + SOFTWARE_ENG):

| class | White | Black | Asian | Hispanic | AIAN | NHPI | Two_or_Other | All |
|---|---|---|---|---|---|---|---|---|
| AIPS2 | 83.5 (0.4) | 52.3 (6.4) | 83.6 (0.1) | 65.6 (2.3) | s | s | 76.1 (2.0) | 82.8 (0.8) |
| AIPOS | 83.2 (0.9) | 52.2 (5.1) | 83.6 (0.1) | 65.0 (2.2) | s | s | 75.7 (2.1) | 81.4 (1.0) |
| AI_PRODUCER | 83.5 (4.7) | s | 69.7 (4.5) | 56.4 (5.8) | s | s | 68.6 (8.3) | 73.0 (1.4) |
| SOFTWARE_ENG | 83.5 (0.4) | 52.2 (4.7) | 83.6 (0.8) | 66.8 (2.2) | s | s | 77.0 (2.3) | 83.3 (0.5) |
| DATA_ENG_ANALYTICS | 59.4 (4.3) | s | 57.1 (1.7) | s | s | s | s | 56.4 (1.8) |
| CLERICAL_ADMIN | 32.0 (0.5) | 31.4 (1.1) | 29.4 (0.2) | 26.2 (0.6) | s | 23.2 (2.6) | 27.0 (1.6) | 29.4 (0.2) |
| CUSTOMER_SUPPORT | 31.3 (1.0) | 24.6 (1.7) | 28.5 (0.6) | 21.7 (0.6) | s | s | 25.5 (2.1) | 26.5 (0.6) |
| PROF_EXPOSED | 52.3 (0.8) | 44.0 (2.1) | 49.0 (0.9) | 39.0 (0.9) | s | s | 49.8 (1.5) | 47.9 (0.9) |
| EXPOSED | 39.1 (0.2) | 32.9 (0.8) | 37.2 (0.5) | 28.4 (0.5) | s | 25.3 (1.7) | 33.4 (1.1) | 34.8 (0.1) |
| FRONTLINE_SERVICE | 23.7 (0.3) | 20.9 (0.3) | 21.4 (0.3) | 19.3 (0.2) | 17.2 (1.8) | 20.4 (1.1) | 20.9 (0.4) | 20.8 (0.2) |
| ALL | 47.6 (0.4) | 30.1 (0.6) | 48.4 (0.5) | 24.5 (0.0) | 28.6 (2.6) | 27.0 (1.3) | 38.2 (0.6) | 38.6 (0.3) |


**Median hourly wage as a ratio to White workers in the same class** (1.00 = parity; SE in parentheses):

| class | White | Black | Asian | Hispanic | AIAN | NHPI | Two_or_Other | All |
|---|---|---|---|---|---|---|---|---|
| AIPS2 | 1.00 | 0.63 (0.08) | 1.00 (0.00) | 0.79 (0.03) | s | s | 0.91 (0.02) | 0.99 (0.01) |
| AIPOS | 1.00 | 0.63 (0.06) | 1.00 (0.01) | 0.78 (0.03) | s | s | 0.91 (0.03) | 0.98 (0.02) |
| AI_PRODUCER | 1.00 | s | 0.83 (0.09) | 0.68 (0.08) | s | s | 0.82 (0.11) | 0.88 (0.05) |
| SOFTWARE_ENG | 1.00 | 0.62 (0.06) | 1.00 (0.01) | 0.80 (0.03) | s | s | 0.92 (0.03) | 1.00 (0.01) |
| DATA_ENG_ANALYTICS | 1.00 | s | 0.96 (0.07) | s | s | s | s | 0.95 (0.06) |
| CLERICAL_ADMIN | 1.00 | 0.98 (0.04) | 0.92 (0.02) | 0.82 (0.02) | s | 0.73 (0.08) | 0.84 (0.05) | 0.92 (0.01) |
| CUSTOMER_SUPPORT | 1.00 | 0.79 (0.06) | 0.91 (0.03) | 0.69 (0.03) | s | s | 0.81 (0.07) | 0.85 (0.03) |
| PROF_EXPOSED | 1.00 | 0.84 (0.04) | 0.94 (0.02) | 0.75 (0.02) | s | s | 0.95 (0.03) | 0.92 (0.02) |
| EXPOSED | 1.00 | 0.84 (0.02) | 0.95 (0.01) | 0.73 (0.01) | s | 0.65 (0.04) | 0.85 (0.03) | 0.89 (0.00) |
| FRONTLINE_SERVICE | 1.00 | 0.88 (0.02) | 0.90 (0.02) | 0.81 (0.01) | 0.72 (0.08) | 0.86 (0.05) | 0.88 (0.02) | 0.88 (0.01) |
| ALL | 1.00 | 0.63 (0.01) | 1.02 (0.01) | 0.52 (0.00) | 0.60 (0.05) | 0.57 (0.03) | 0.80 (0.01) | 0.81 (0.01) |


**Median annual wage, full-time year-round ($):**

| class | White | Black | Asian | Hispanic | AIAN | NHPI | Two_or_Other | All |
|---|---|---|---|---|---|---|---|---|
| AIPS2 | 185,470 | 122,275 | 181,157 | 150,964 | s | s | 172,135 | 179,258 |
| AIPOS | 183,572 | 116,340 | 181,157 | 144,925 | s | s | 169,080 | 178,416 |
| AI_PRODUCER | 183,513 | s | 154,328 | 135,664 | s | s | s | 163,123 |
| SOFTWARE_ENG | 185,470 | 119,384 | 181,157 | 154,328 | s | s | 173,318 | 181,157 |
| DATA_ENG_ANALYTICS | 132,537 | s | 118,714 | s | s | s | s | 118,714 |
| CLERICAL_ADMIN | 74,425 | 68,854 | 67,289 | 57,959 | s | 50,976 | 61,731 | 66,424 |
| CUSTOMER_SUPPORT | 75,347 | 51,932 | 68,840 | 51,009 | s | s | 65,293 | 63,755 |
| PROF_EXPOSED | 120,771 | 94,971 | 108,531 | 85,474 | s | s | 117,245 | 108,531 |
| EXPOSED | 92,251 | 73,029 | 86,661 | 64,009 | s | 57,959 | 79,709 | 81,143 |
| FRONTLINE_SERVICE | 60,544 | 49,497 | 50,976 | 43,412 | s | 47,486 | 54,265 | 48,570 |
| ALL | 118,714 | 71,366 | 118,714 | 57,959 | 70,710 | 65,118 | 97,678 | 95,507 |


**Is the racial wage gap inside the AI classes different from inside the exposed classes?** Weighted regression of log hourly wage on race x {AI classes, exposed classes} interactions with occupation-class fixed effects, on workers in those classes only; "adjusted" adds age, age squared, sex, education, county and foreign-born. The coefficient is the log-point gap vs White workers in the same side; the test is the difference (AI minus exposed) with a replicate-weight SE.

| AI-class definition | spec | race vs White | n AI / n exposed | gap in AI classes (se) | gap in exposed classes (se) | difference (se) | z |
|---|---|---|---|---|---|---|---|
| AI_PRODUCER+SOFTWARE_ENG | unadjusted | Black | 202 / 1,072 | -0.431 (0.061) = -35.0% | -0.144 (0.026) = -13.4% | -0.287 (0.068) | -4.3 |
| AI_PRODUCER+SOFTWARE_ENG | unadjusted | Hispanic | 822 / 4,494 | -0.304 (0.038) = -26.2% | -0.271 (0.015) = -23.7% | -0.033 (0.040) | -0.8 |
| AI_PRODUCER+SOFTWARE_ENG | unadjusted | Asian | 9,370 / 7,931 | -0.027 (0.016) = -2.6% | -0.087 (0.012) = -8.4% | 0.061 (0.018) | 3.3 |
| AI_PRODUCER+SOFTWARE_ENG | unadjusted | Two_or_Other | 600 / 1,228 | -0.095 (0.037) = -9.1% | -0.171 (0.028) = -15.7% | 0.076 (0.049) | 1.6 |
| AI_PRODUCER+SOFTWARE_ENG | adjusted | Black | 202 / 1,072 | -0.361 (0.059) = -30.3% | -0.097 (0.026) = -9.2% | -0.264 (0.066) | -4.0 |
| AI_PRODUCER+SOFTWARE_ENG | adjusted | Hispanic | 822 / 4,494 | -0.211 (0.034) = -19.0% | -0.154 (0.014) = -14.2% | -0.058 (0.037) | -1.6 |
| AI_PRODUCER+SOFTWARE_ENG | adjusted | Asian | 9,370 / 7,931 | -0.055 (0.016) = -5.4% | -0.130 (0.012) = -12.2% | 0.075 (0.018) | 4.2 |
| AI_PRODUCER+SOFTWARE_ENG | adjusted | Two_or_Other | 600 / 1,228 | -0.040 (0.032) = -3.9% | -0.124 (0.029) = -11.6% | 0.084 (0.047) | 1.8 |
| AIPOS3 | unadjusted | Black | 211 / 1,072 | -0.435 (0.059) = -35.3% | -0.144 (0.026) = -13.4% | -0.291 (0.066) | -4.4 |
| AIPOS3 | unadjusted | Hispanic | 857 / 4,494 | -0.302 (0.037) = -26.1% | -0.271 (0.015) = -23.7% | -0.031 (0.038) | -0.8 |
| AIPOS3 | unadjusted | Asian | 9,484 / 7,931 | -0.028 (0.015) = -2.7% | -0.087 (0.012) = -8.4% | 0.059 (0.018) | 3.2 |
| AIPOS3 | unadjusted | Two_or_Other | 616 / 1,228 | -0.096 (0.036) = -9.1% | -0.171 (0.028) = -15.7% | 0.075 (0.048) | 1.6 |
| AIPOS3 | adjusted | Black | 211 / 1,072 | -0.363 (0.057) = -30.4% | -0.097 (0.026) = -9.2% | -0.266 (0.064) | -4.1 |
| AIPOS3 | adjusted | Hispanic | 857 / 4,494 | -0.210 (0.033) = -18.9% | -0.154 (0.014) = -14.3% | -0.056 (0.036) | -1.6 |
| AIPOS3 | adjusted | Asian | 9,484 / 7,931 | -0.056 (0.015) = -5.4% | -0.130 (0.012) = -12.2% | 0.074 (0.018) | 4.2 |
| AIPOS3 | adjusted | Two_or_Other | 616 / 1,228 | -0.039 (0.031) = -3.8% | -0.124 (0.029) = -11.6% | 0.085 (0.046) | 1.8 |


**Finding.** The Black-White gap is much *larger* inside AI_PRODUCER/SOFTWARE_ENG (-30% adjusted) than inside the exposed classes (-9%); the difference is -4.0 SE from zero (Black n=202 in AI classes, enough to be unsuppressed but modest). The Hispanic gap is large in both (-19% vs -14% adjusted) and the difference between them is **not** statistically distinguishable from zero (z=-1.6). Asian workers earn about the same as White workers inside AI classes (-5% adjusted; median ratio 1.00) but less than White workers inside exposed classes (-12% adjusted), so the Asian gap is *narrower* in AI classes. Adjustment for education etc. shrinks the Black gaps in both places but does not remove them. This is observational and cross-sectional: occupation codes are broad (e.g. all 'software developers' are pooled regardless of seniority or employer), so unobserved within-occupation sorting (level, firm, equity compensation) is not controlled.

**Size of the prize: AI-positioned minus exposed classes (wage-and-salary workers):**

| race_eth | median hourly diff $ (se) | median hourly ratio (se) | median FTFY annual diff $ (se) |
|---|---|---|---|
| White | $44.1 (0.9) | 2.13 (0.03) | $91,321 (2,668) |
| Black | $19.3 (5.2) | 1.59 (0.16) | $43,311 (13,990) |
| Asian | $46.4 (0.6) | 2.25 (0.03) | $94,496 (1,517) |
| Hispanic | $36.6 (2.2) | 2.29 (0.08) | $80,917 (7,644) |
| AIAN | s | s | s |
| NHPI | s | s | s |
| Two_or_Other | $42.3 (2.5) | 2.26 (0.10) | $89,371 (8,185) |
| All | $46.6 (1.0) | 2.34 (0.03) | $97,273 (859) |


The prize is large for every group, but it is smallest in dollars for Black workers: for Black workers, the AI-positioned class pays about 1.59x the exposed classes versus 2.13x for White workers. Even Black workers who get in earn much less than their White and Asian peers.

**Are AI gains flowing to groups already at the top of the Bay Area wage distribution?** Overall median hourly wage of each group vs its AI-positioned and exposed representation indices:

| race | median hourly wage, all workers | RI AI-positioned | RI exposed |
|---|---|---|---|
| White | $47.6 | 0.82 | 1.02 |
| Black | $30.1 | 0.36 | 1.19 |
| Asian | $48.4 | 1.99 | 1.02 |
| Hispanic | $24.5 | 0.24 | 0.87 |
| Two_or_Other | $38.2 | 0.82 | 1.12 |

Spearman rank correlation across these five groups (AIAN, NHPI excluded as thin): wage vs RI AI-positioned = 0.90; wage vs RI exposed = 0.10. With five groups this is descriptive only.

## 4. Test (d): wage mass at risk

Annual wage and salary mass (sum of PWGTP x adjusted WAGP, millions of 2023 dollars per year, average over 2019-2023) in exposed occupations, with the same in AI-positioned occupations for contrast. Includes part-year workers; excludes self-employment income. SEs by replicate weights; `s` = suppressed.

| race_eth | total wage mass $M | exposed mass $M (se) | exposed share of group wage mass | exposed share of group wage earners | AI-pos mass $M (se) | AI-pos share of group mass | mean wage, exposed | mean wage, AI-pos |
|---|---|---|---|---|---|---|---|---|
| White | 180,285 | 19,933 (366) | 11.1% | 14.3% | 20,711 (457) | 11.5% | $104,031 | $217,340 |
| Black | 14,694 | 2,385 (121) | 16.2% | 16.6% | 763 (81) | 5.2% | $74,202 | $129,655 |
| Asian | 142,426 | 14,813 (297) | 10.4% | 14.2% | 38,010 (508) | 26.7% | $93,109 | $202,057 |
| Hispanic | 54,743 | 6,785 (148) | 12.4% | 12.4% | 2,949 (148) | 5.4% | $62,324 | $161,298 |
| AIAN | 394 | s | s | s | s | s | s | s |
| NHPI | 1,354 | 214 (36) | 15.8% | 17.1% | s | s | $63,605 | s |
| Two_or_Other | 18,774 | 2,385 (121) | 12.7% | 15.8% | 2,496 (183) | 13.3% | $84,158 | $196,995 |
| All | 412,671 | 46,569 (548) | 11.3% | 14.0% | 65,002 (770) | 15.8% | $88,855 | $202,608 |


In dollars, exposure is smaller than in headcount for the Bay Area as a whole (exposed workers are 14.0% of wage earners but 11.3% of wage mass) and for White and Asian workers, because exposed jobs pay below those groups' average. It is about the same as headcount for Black (16.6% of wage earners, 16.2% of wage mass) and Hispanic workers (12.4% and 12.4%), because for them exposed jobs pay about the group average (Hispanic mean wage in exposed jobs $62,324 vs $62,388 for all Hispanic wage earners; White $104,031 vs $134,558). So on the dollar measure Black (16.2%) and Hispanic (12.4%) workers carry a larger exposed share of their wage mass than White workers (11.1%) or Asian workers (10.4%), even though Hispanic workers are *less* exposed by headcount-share relative to the Bay Area average.

**Exposed wage mass by race x county ($ millions per year; `s` = suppressed; full detail by class in `base/wage_mass_at_risk.csv`):**

| county | White | Black | Asian | Hispanic | AIAN | NHPI | Two_or_Other | All |
|---|---|---|---|---|---|---|---|---|
| Alameda | 3,176 | 919 | 3,580 | 1,381 | s | 80 | 518 | 9,660 |
| Contra Costa | 3,198 | 472 | 1,467 | 1,091 | s | s | 398 | 6,647 |
| Marin | 1,316 | s | 131 | 130 | s | s | s | 1,665 |
| Napa | 270 | s | 60 | 159 | s | s | s | 545 |
| San Francisco | 3,798 | 229 | 2,691 | 677 | s | s | 434 | 7,855 |
| San Mateo | 2,097 | s | 2,106 | 746 | s | s | 252 | 5,338 |
| Santa Clara | 3,876 | 317 | 4,372 | 1,784 | s | s | 377 | 10,774 |
| Solano | 661 | 271 | 314 | 361 | s | s | 143 | 1,774 |
| Sonoma | 1,541 | s | 92 | 457 | s | s | 152 | 2,311 |
| Bay Area | 19,933 | 2,385 | 14,813 | 6,785 | s | 214 | 2,385 | 46,569 |


**Exposed share of each cell's wage mass (race x county; `s` = suppressed):**

| county | White | Black | Asian | Hispanic | AIAN | NHPI | Two_or_Other | All |
|---|---|---|---|---|---|---|---|---|
| Alameda | 10.8% | 17.0% | 11.2% | 12.3% | s | 19.3% | 12.8% | 11.7% |
| Contra Costa | 12.4% | 14.1% | 12.5% | 12.4% | s | s | 15.7% | 12.7% |
| Marin | 11.8% | s | 13.6% | 9.1% | s | s | s | 11.5% |
| Napa | 8.6% | s | 13.7% | 13.0% | s | s | s | 10.6% |
| San Francisco | 11.9% | 16.8% | 15.0% | 12.0% | s | s | 13.7% | 13.0% |
| San Mateo | 10.2% | s | 12.7% | 12.9% | s | s | 12.5% | 11.6% |
| Santa Clara | 9.6% | 16.4% | 7.4% | 12.6% | s | s | 8.9% | 8.9% |
| Solano | 11.8% | 17.6% | 12.4% | 12.1% | s | s | 14.3% | 12.8% |
| Sonoma | 12.8% | s | 10.5% | 13.0% | s | s | 20.5% | 13.2% |


## 5. Test (e): self-employment / contract precarity

Share of workers with COW 6 or 7 (self-employed, own business). Upper bound on independent contracting; see definitions. SE in pp.

| workers in | White | Black | Asian | Hispanic | AIAN | NHPI | Two_or_Other | All |
|---|---|---|---|---|---|---|---|---|
| CLERICAL_ADMIN | 6.0% (0.3) | 2.0% (0.6) | 4.3% (0.4) | 3.2% (0.4) | s | 0.8% (0.7) | 2.3% (0.6) | 4.3% (0.2) |
| CUSTOMER_SUPPORT | 3.2% (0.5) | 0.4% (0.3) | 3.5% (0.6) | 2.5% (0.6) | s | s | 2.3% (0.9) | 2.8% (0.3) |
| PROF_EXPOSED | 15.7% (0.6) | 9.4% (1.9) | 6.4% (0.6) | 7.1% (1.0) | s | s | 8.8% (1.4) | 10.7% (0.3) |
| EXPOSED | 10.0% (0.3) | 3.8% (0.6) | 5.1% (0.3) | 4.0% (0.4) | s | 3.0% (2.2) | 4.8% (0.7) | 6.6% (0.1) |
| FRONTLINE_SERVICE | 13.5% (0.4) | 8.8% (0.8) | 12.1% (0.4) | 11.4% (0.4) | 11.6% (4.5) | 7.7% (2.0) | 13.0% (1.0) | 12.0% (0.2) |
| AIPOS | 4.2% (0.4) | 3.6% (1.0) | 1.4% (0.1) | 2.8% (0.6) | s | s | 3.4% (0.9) | 2.5% (0.2) |
| ALL | 13.1% (0.1) | 7.3% (0.4) | 7.2% (0.1) | 9.6% (0.2) | 9.8% (2.0) | 9.0% (1.2) | 10.2% (0.4) | 10.1% (0.1) |


**Negative result.** Exposed workers are *less* likely to be self-employed than the Bay Area average (6.6% vs 10.1%; FRONTLINE_SERVICE 12.0%). Clerical and customer-support workers are almost all W-2 employees. The exception is PROF_EXPOSED (10.7% overall; accountants, writers, translators, designers and similar occupations have many independents). Within exposed classes, Black (3.8%) and Hispanic (4.0%) workers are less likely to be self-employed than White workers (10.0%). So the data do not support the idea that exposed workers, or exposed minority workers, are disproportionately in contract arrangements. What COW cannot see: 1099 work performed by people who report as wage employees, temp-agency and platform arrangements, or involuntary contract status.

## 6. Test (f): shift-share incidence model. COUNTERFACTUAL ACCOUNTING, NOT A FORECAST

**Assumptions, stated plainly.**

1. Base = employed Bay Area persons with positive wage and salary income (2019-2023 PUMS, 2023 dollars); each person carries PWGTP.
2. A fraction X of workers in CLERICAL_ADMIN and CUSTOMER_SUPPORT lose their jobs, **uniformly** (every such worker, whatever race, county, wage or tenure, has the same probability X). Nothing in the model makes some workers more likely to be cut than others.
3. Scenario R=0: displaced workers have zero wages afterward (no re-employment, no unemployment insurance, no transfers). Scenario R=0.5: half of the displaced are re-employed at a 20% wage cut in the same county (a stylized mid-case; the 50% and the 20% are assumptions, not estimates).
4. A fraction Y wage gain applies to every wage earner in AI_PRODUCER and SOFTWARE_ENG; there is no employment growth in those classes and no spillover to other occupations, prices, rents or other classes' wages. DATA_ENG_ANALYTICS gets no gain (the spec names only AI_PRODUCER/SOFTWARE_ENG).
5. Gains and losses accrue to the same people and are not redistributed (no capital income, equity, taxes, or migration of workers or firms). Any gains to firm owners and investors, which may be the main channel for AI gains, are outside WAGP and outside this model.
6. Static occupational and demographic composition (no worker re-sorting across classes, no entry of new workers into AI jobs).
7. Metrics: (i) *per-capita wage* = (counterfactual wage mass of the group) / (baseline number of wage earners in the group), which counts displaced workers at zero; (ii) *median annual wage of the still-employed*, which is **mechanically** affected by who is removed (removing low-wage clerical workers can raise the median even though those workers are worse off), so treat it as a composition measure, not welfare. The median is also a noisy, step-like statistic (large replicate SEs).
8. Standard errors come from the replicate weights and reflect **sampling error only**, conditional on the assumptions above. They do not reflect uncertainty in the assumptions, which dominates.

**Implied change in the Black-White and Latino-White wage gaps (per-capita wage, ratio to White; change in percentage points of White wage; SE in parentheses; R=0):** a negative change = the gap *widens*.

*Re-employment share R=0.0 (no re-employment)*

| group vs White | X: clerical+CS job cut | Y=5% AI wage gain | Y=10% | Y=20% |
|---|---|---|---|---|
| Black | 5% | -0.33 (0.03) | -0.50 (0.04) | -0.84 (0.07) |
| Black | 10% | -0.49 (0.04) | -0.66 (0.05) | -1.00 (0.08) |
| Black | 20% | -0.81 (0.08) | -0.98 (0.08) | -1.32 (0.10) |
| Hispanic | 5% | -0.22 (0.01) | -0.36 (0.01) | -0.63 (0.03) |
| Hispanic | 10% | -0.30 (0.01) | -0.44 (0.02) | -0.71 (0.03) |
| Hispanic | 20% | -0.47 (0.02) | -0.61 (0.02) | -0.88 (0.03) |
| Asian | 5% | +0.73 (0.02) | +1.43 (0.04) | +2.83 (0.08) |
| Asian | 10% | +0.74 (0.02) | +1.45 (0.04) | +2.84 (0.08) |
| Asian | 20% | +0.76 (0.03) | +1.47 (0.05) | +2.87 (0.08) |


*Re-employment share R=0.5 (displaced re-employed at 80% of prior wage)*

| group vs White | X: clerical+CS job cut | Y=5% AI wage gain | Y=10% | Y=20% |
|---|---|---|---|---|
| Black | 5% | -0.27 (0.02) | -0.44 (0.04) | -0.78 (0.07) |
| Black | 10% | -0.36 (0.03) | -0.54 (0.04) | -0.87 (0.07) |
| Black | 20% | -0.56 (0.05) | -0.73 (0.06) | -1.06 (0.08) |
| Hispanic | 5% | -0.19 (0.01) | -0.33 (0.01) | -0.60 (0.03) |
| Hispanic | 10% | -0.24 (0.01) | -0.38 (0.01) | -0.65 (0.03) |
| Hispanic | 20% | -0.34 (0.01) | -0.47 (0.02) | -0.74 (0.03) |
| Asian | 5% | +0.72 (0.02) | +1.43 (0.04) | +2.82 (0.08) |
| Asian | 10% | +0.73 (0.02) | +1.44 (0.04) | +2.83 (0.08) |
| Asian | 20% | +0.74 (0.03) | +1.45 (0.04) | +2.85 (0.08) |


Baseline per-capita wage ratios to White: Black 0.56, Hispanic 0.46, Asian 0.95 (annual wage of all wage earners, part-year included, so lower than the hourly ratios in test c). Under every cell of the grid the Black-White and Latino-White gaps **widen** on the per-capita measure (by 0.2 to 1.3 pp of White wage), and the Asian-White gap moves in Asian workers' favor by 0.7 to 2.9 pp.
These are small relative to the baseline gaps (44 pp for Black and 54 pp for Hispanic workers), but they are the same sign in every scenario and have sampling SEs far below the estimates. Both sides of the scenario contribute: for Black workers the change is -0.33 pp at X=5%,Y=5%; raising only X to 20% moves it to -0.81 pp and raising only Y to 20% moves it to -0.84 pp. The displacement side widens gaps because exposed jobs are a larger share of Black and Hispanic wage mass than of White wage mass (test d); the AI wage-gain side widens them because AI-class wage mass is concentrated among Asian and White workers (test d). With R=0.5 the widening is smaller but not reversed. None of this is a forecast: it restates the baseline occupational mix under uniform assumptions.

**Median-wage gap (still-employed), R=0:** changes are within replicate noise for almost every cell (SEs of 0.5 to 1.9 pp against estimated changes of -0.6 to +2.4 pp), so the median-based gap results should be read as **no detectable change**:

| group vs White | X | Y=5% | Y=10% | Y=20% |
|---|---|---|---|---|
| Black | 5% | +0.14 (0.55) | +0.14 (0.57) | +0.28 (0.82) |
| Black | 10% | +0.14 (0.60) | +0.14 (0.63) | +0.37 (1.33) |
| Black | 20% | -0.18 (0.67) | -0.12 (0.90) | -0.35 (0.83) |
| Hispanic | 5% | +0.09 (0.50) | +0.21 (0.74) | +0.23 (0.92) |
| Hispanic | 10% | +0.07 (0.54) | +0.21 (0.84) | +0.00 (0.88) |
| Hispanic | 20% | -0.27 (0.52) | -0.14 (0.92) | -0.61 (0.47) |
| Asian | 5% | +0.63 (1.56) | +1.54 (1.40) | +2.35 (1.39) |
| Asian | 10% | +1.54 (1.79) | +2.35 (1.72) | +1.90 (1.31) |
| Asian | 20% | +1.79 (1.22) | +1.66 (1.17) | +2.33 (1.88) |


**Implied change in total wage mass and per-capita wage by race, R=0** (percent of baseline; rows = Y, columns = X; each cell is the change in group wage mass, which equals the per-capita change because the base headcount is fixed). Point estimates only for non-gap quantities; see `base/incidence_grid.csv`.

| race_eth | Y: AI wage gain | X=5% job cut | X=10% | X=20% |
|---|---|---|---|---|
| White | 5% | +0.35% | +0.13% | -0.30% |
| White | 10% | +0.91% | +0.70% | +0.27% |
| White | 20% | +2.04% | +1.83% | +1.40% |
| Black | 5% | -0.24% | -0.74% | -1.74% |
| Black | 10% | +0.01% | -0.49% | -1.48% |
| Black | 20% | +0.52% | +0.02% | -0.97% |
| Asian | 5% | +1.12% | +0.91% | +0.50% |
| Asian | 10% | +2.45% | +2.24% | +1.83% |
| Asian | 20% | +5.10% | +4.89% | +4.48% |
| Hispanic | 5% | -0.13% | -0.52% | -1.31% |
| Hispanic | 10% | +0.13% | -0.26% | -1.04% |
| Hispanic | 20% | +0.66% | +0.27% | -0.52% |
| AIAN | 5% | -0.12% | -0.44% | -1.09% |
| AIAN | 10% | +0.09% | -0.24% | -0.89% |
| AIAN | 20% | +0.49% | +0.17% | -0.48% |
| NHPI | 5% | -0.29% | -0.79% | -1.78% |
| NHPI | 10% | -0.08% | -0.58% | -1.57% |
| NHPI | 20% | +0.33% | -0.17% | -1.16% |
| Two_or_Other | 5% | +0.37% | +0.09% | -0.47% |
| Two_or_Other | 10% | +1.03% | +0.75% | +0.18% |
| Two_or_Other | 20% | +2.34% | +2.06% | +1.50% |
| All | 5% | +0.53% | +0.28% | -0.22% |
| All | 10% | +1.31% | +1.06% | +0.56% |
| All | 20% | +2.87% | +2.62% | +2.12% |


**By county, X=10%, Y=10%, R=0** (change in county wage mass; median of still-employed in parentheses is a composition measure):

| county | baseline wage mass $M | change in wage mass | change in median wage of still-employed |
|---|---|---|---|
| Alameda | 82,744 | +1.05% | +1.54% |
| Contra Costa | 52,390 | +0.19% | +1.30% |
| Marin | 14,480 | +0.13% | +1.80% |
| Napa | 5,127 | -0.39% | +0.00% |
| San Francisco | 60,268 | +1.16% | +0.81% |
| San Mateo | 45,965 | +0.85% | +1.03% |
| Santa Clara | 120,434 | +2.04% | +0.44% |
| Solano | 13,821 | -0.56% | +0.00% |
| Sonoma | 17,442 | -0.34% | +0.00% |
| Bay Area | 412,671 | +1.06% | +1.30% |


Counties with thin AI-positioned employment (Solano, Sonoma, Napa) lose wage mass on net in this scenario (job cuts without a matching AI wage gain), while Santa Clara, San Francisco and Alameda gain. Race x county results for every scenario are in `base/incidence_grid.csv` (level `race_county`; rows with n<50 flagged `suppressed`).

## 7. Test (g): 2024 1-year vs 2019-2023 5-year

Differences in the share of each group's workers in exposed / AI-positioned classes. **Comparability caveats:** (1) the 5-year file averages 2019-2023 (centered on 2021, with pandemic-era employment composition) while 2024 is a single year, so a difference mixes a trend with a level shift between sample designs; (2) the two files are independent samples, so the SE of the difference is sqrt(se1^2+se2^2), using replicate-weight SEs from each; (3) the 2024 file has about one fifth of the observations (Black n=1,374; AIAN n=90; NHPI n=148), so its SEs are about 2.2x larger; (4) with 5 groups x 2 headline metrics, about 10 tests are run, so a single |z| just above 2 is not convincing (Bonferroni threshold about |z|>2.8); (5) OCCP codes are identical across the two vintages, so recoding is not a concern.

| race_eth | class set | 2019-23 share | 2024 share | change pp (se) | z | verdict |
|---|---|---|---|---|---|---|
| White | EXPOSED | 14.0% | 13.5% | -0.48 (0.35) | -1.4 | within noise |
| White | AIPOS | 6.7% | 7.5% | +0.79 (0.28) | 2.8 | real shift (survives Bonferroni) |
| Black | EXPOSED | 16.2% | 14.5% | -1.78 (1.17) | -1.5 | within noise |
| Black | AIPOS | 2.9% | 4.1% | +1.18 (0.71) | 1.7 | within noise |
| Asian | EXPOSED | 14.0% | 12.9% | -1.14 (0.37) | -3.1 | real shift (survives Bonferroni) |
| Asian | AIPOS | 16.3% | 17.9% | +1.65 (0.41) | 4.0 | real shift (survives Bonferroni) |
| Hispanic | EXPOSED | 11.9% | 12.1% | +0.23 (0.47) | 0.5 | within noise |
| Hispanic | AIPOS | 2.0% | 2.5% | +0.52 (0.21) | 2.4 | suggestive (|z|>2, not Bonferroni) |
| AIAN | EXPOSED | 11.6% | 13.3% | +1.73 (4.76) | 0.4 | thin (n<50) |
| AIAN | AIPOS | 2.2% | 7.2% | +5.01 (3.38) | 1.5 | thin (n<50) |
| NHPI | EXPOSED | 16.1% | 24.8% | +8.65 (4.30) | 2.0 | thin (n<50) |
| NHPI | AIPOS | 2.1% | 2.6% | +0.52 (1.44) | 0.4 | thin (n<50) |
| Two_or_Other | EXPOSED | 15.3% | 15.2% | -0.08 (1.07) | -0.1 | within noise |
| Two_or_Other | AIPOS | 6.7% | 5.8% | -0.92 (0.66) | -1.4 | within noise |
| All | EXPOSED | 13.7% | 13.2% | -0.52 (0.21) | -2.5 | suggestive (|z|>2, not Bonferroni) |
| All | AIPOS | 8.2% | 9.3% | +1.10 (0.16) | 6.7 | real shift (survives Bonferroni) |


**Reading.** The Bay-Area-wide exposed share fell 0.5 pp (z=-2.5) and the AI-positioned share rose 1.1 pp (z=6.7). The AI-positioned rise is statistically large and appears for Asian (+1.6 pp, z=4.0), White (+0.8 pp, z=2.8) and Hispanic (+0.5 pp, z=2.4); it is largest in pp for Asian workers, so differences in AI-positioned share between Asian workers and the other groups grew in levels, while the Black change is inside the noise. The decline in exposed share is significant only for Asian workers (z=-3.1, driven by PROF_EXPOSED, z=-3.3). **For Black workers (exposed share 16.2% to 14.5%, z=-1.5), Hispanic workers (z=0.5), White workers (z=-1.4) and Two_or_Other, the change in exposed share is inside the noise.** The Black AI-positioned share rose by 1.2 pp (z=1.7, 2024 cell n=56), also inside the noise. AIAN and NHPI changes are thin and not interpretable (the NHPI exposed jump has an unweighted 2024 numerator of 31 and is flagged). Whether the Asian/White shifts reflect AI-era hiring or the pandemic-centered baseline cannot be separated with these data. Details: `base/change_2024_vs_5yr.csv`.

## 8. Evidence for and against the hypothesis that AI gains flow to groups already at the top

**Consistent with the hypothesis:**

* AI-positioned jobs are overwhelmingly held by the two highest-wage groups: Asian + White workers are 88.3% of AI-positioned employment vs 65.8% of employment. Black and Hispanic workers hold 7.5% of AI-positioned jobs vs 28.7% of employment.
* Across five groups, rank of median wage and rank of AI-positioned representation are correlated (Spearman 0.90).
* The shift-share grid widens Black-White and Latino-White per-capita gaps in every cell and favors Asian workers.
* Black workers face a much bigger wage penalty inside the AI classes than inside exposed classes.

**Contradicting or complicating it:**

* **White workers are the top of the wage distribution among the large groups yet are *under*-represented in AI-positioned jobs** (RI 0.82); the gains flow most to *Asian* workers (RI 1.99), whose overall median hourly wage is about equal to White workers' (1.02 of White, SE 0.015). 'Already at the top' therefore fits Asian workers only on average, and only weakly for the wage-level ranking.
* **Exposure is not concentrated among the lowest-paid groups:** Hispanic workers, the lowest-paid large group, are under-represented in exposed classes (RI 0.87). Hispanic displacement risk in this taxonomy is mostly through *absence* from AI-positioned jobs, not through over-exposure; their high FRONTLINE_SERVICE share (RI 1.68) and SKILLED_TRADE are classed as not exposed.
* **Asian workers are not over-exposed** (RI 1.02), despite being 58% of AI-positioned workers; White workers are at parity as well.
* **Exposed occupations are mid-wage, majority college-educated and female:** exposed workers are 67.6% women (vs 46.0% of all workers); 55.5% hold a bachelor's degree or more (AI-positioned: 90.3%); their median hourly wage ($34.8) is below the Bay Area median ($38.6) but far above FRONTLINE_SERVICE ($20.8). Gender, not race, is the sharper axis of exposure in this taxonomy.
* **No contract-precarity amplification** (test e): exposed workers are less often self-employed than average, and exposed Black and Hispanic workers less than exposed White workers.
* **Wage-gap difference is not uniform:** the larger gap in AI classes holds for Black workers (large, significant) but not detectably for Hispanic workers (z=-1.6), and the Asian gap is narrower in AI classes.
* **2024 vs 5-year:** exposed shares did not move detectably for Black, Hispanic or White workers (inside noise). The only significant exposed-share decline is for Asian workers.
* **Shift-share is not a distributional verdict:** the per-capita gap widening is small (0.2 to 1.3 pp of White wage for Black and Hispanic workers against baseline gaps of about 44 to 54 pp) and the median-based gap changes are inside sampling noise. Capital income and equity compensation (outside WAGP) could dominate who actually captures AI gains.

## 9. Suppressed and thin cells

Rule: a cell is suppressed (shown `s`; value retained in the CSV with `suppressed=True`) if it has fewer than 50 unweighted observations in the numerator cell or the group. Counts of suppressed cells by table: contract_precarity: 8, exposure_by_race: 34, exposure_by_race_county: 667, wage_mass_at_risk: 207, wages_by_occclass_race: 304. The complete list is `base/suppressed_cells.csv`. Patterns:

* Bay-wide composition: AIAN is suppressed in every class except FRONTLINE_SERVICE; NHPI is suppressed in all AI-positioned classes and most small classes; Black is suppressed in AI_PRODUCER and DATA_ENG_ANALYTICS (17 and 9 workers); Hispanic is suppressed in DATA_ENG_ANALYTICS (35).
* County x race, headline classes (EXPOSED or AI-positioned): 61 cells suppressed. Cells: Alameda/AIAN/AIPOS; Alameda/AIAN/EXPOSED; Alameda/NHPI/AIPOS; Contra Costa/AIAN/AIPOS; Contra Costa/AIAN/EXPOSED; Contra Costa/Black/AIPOS; Contra Costa/NHPI/AIPOS; Contra Costa/NHPI/EXPOSED; Marin/AIAN/AIPOS; Marin/AIAN/EXPOSED; Marin/Asian/AIPOS; Marin/Black/AIPOS; Marin/Black/EXPOSED; Marin/Hispanic/AIPOS; Marin/NHPI/AIPOS; Marin/NHPI/EXPOSED; Marin/Two_or_Other/AIPOS; Marin/Two_or_Other/EXPOSED; Napa/AIAN/AIPOS; Napa/AIAN/EXPOSED; Napa/Asian/AIPOS; Napa/Black/AIPOS; Napa/Black/EXPOSED; Napa/Hispanic/AIPOS; Napa/NHPI/AIPOS; Napa/NHPI/EXPOSED; Napa/Two_or_Other/AIPOS; Napa/Two_or_Other/EXPOSED; Napa/White/AIPOS; San Francisco/AIAN/AIPOS; San Francisco/AIAN/EXPOSED; San Francisco/Black/AIPOS; San Francisco/NHPI/AIPOS; San Francisco/NHPI/EXPOSED; San Mateo/AIAN/AIPOS; San Mateo/AIAN/EXPOSED; San Mateo/Black/AIPOS; San Mateo/Black/EXPOSED; San Mateo/NHPI/AIPOS; San Mateo/NHPI/EXPOSED; Santa Clara/AIAN/AIPOS; Santa Clara/AIAN/EXPOSED; Santa Clara/NHPI/AIPOS; Santa Clara/NHPI/EXPOSED; Solano/AIAN/AIPOS; Solano/AIAN/EXPOSED; Solano/Asian/AIPOS; Solano/Black/AIPOS; Solano/Hispanic/AIPOS; Solano/NHPI/AIPOS; Solano/NHPI/EXPOSED; Solano/Two_or_Other/AIPOS; Sonoma/AIAN/AIPOS; Sonoma/AIAN/EXPOSED; Sonoma/Asian/AIPOS; Sonoma/Black/AIPOS; Sonoma/Black/EXPOSED; Sonoma/Hispanic/AIPOS; Sonoma/NHPI/AIPOS; Sonoma/NHPI/EXPOSED; Sonoma/Two_or_Other/AIPOS.

Not suppressed but thin (50 to ~150 unweighted): e.g. Black AI-positioned (n=224) and Black in AI_PRODUCER+SOFTWARE_ENG for the wage test (n=202); Black AI-positioned county cells; 2024 Black AI-positioned (n=56). Treat these as indicative.

## 10. Files

`base/pums_bay.parquet`, `base/pums_bay_2024.parquet`, `base/occp_crosswalk.csv`, `base/puma_county_xwalk.csv`, `base/exposure_by_race.csv`, `base/exposure_by_race_county.csv`, `base/wages_by_occclass_race.csv`, `base/wage_gap_tests.csv`, `base/wage_mass_at_risk.csv`, `base/contract_precarity.csv`, `base/incidence_grid.csv`, `base/incidence_gap_changes.csv`, `base/change_2024_vs_5yr.csv`, `base/ai_concentration_by_county.csv`, `base/exposure_by_race_sex.csv`, `base/exposure_by_race_altmap.csv`, `base/race_counts.csv`, `base/suppressed_cells.csv`. Code: `code/pums_*.py` (run order: puma_county, build, crosswalk, exposure, wages, incidence, extra, memo).
