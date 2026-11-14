# EXPERIMENT W: California WARN notices and Bay Area labor-market exposure

Source: EDD WARN reports (3 PDFs FY2023-24 to FY2025-26 + current xlsx, received dates 2023-07-03 to 2026-11-09). 5,392 notice rows parsed, 5,390 in CA (2 out-of-state rows, Clark NV and Dallas TX, retained in warn_ca.* but dropped from analysis). 297,696 affected employees. All figures below are computed from the parse (scripts in code/warn_*.py). Time axis = EDD received/processed date (the field the reports are filtered on), not the employer notice date.

## Three most surprising results

1. **No rising Bay Area trend over the window.** Across the 13 full quarters 2023Q3-2026Q3, Bay Area affected employees per 10,000 resident workers have a slope of -0.17 per quarter (HAC se 0.39, p=0.66; Spearman rho -0.04). Bay Area notice COUNT is drifting down (-2.8 notices/qtr, p=0.08). The Bay Area share of California WARN employees has no trend (+0.2 pp/qtr, p=0.78). The Bay Area peak was 2024Q1 (28.4 per 10k), not recent.
2. **The "recent surge" is lumpy and is a few firms, not a broad trend.** 2026Q2 (Bay 9,889 employees, 24.6 per 10k, 3.6x the rest of CA's intensity) is 66% flagged core-tech (Meta alone 2,212 + 338 + 313 + 252 in late May 2026, plus Intuit 493, LinkedIn 352, Oracle 310). The next quarter fell back to 18.9 per 10k. Meta Platforms is the largest Bay employer in the window (4,023 employees across 19 notices). Tech share of Bay WARN employees: 23.1% FY23-24, 21.6% FY24-25, 47.0% FY25-26, 26.6% FY26-27 so far.
3. **The cleanest direct customer-support read is essentially empty.** The xlsx Call Center Relocations sheet holds exactly ONE record in 2023-2026 (American General Life, Woodland Hills, Los Angeles Co., 163 employees, received 2023-03-02, i.e. before our window, not Bay Area, no destination stated). The PDFs contain no call-center section. Name-matching finds only Charter Communications Customer Contact Center (San Bernardino, 430, closure, 2024-06), Sky Chefs Customer Service Center (14), and two Conduent (BPO) layoffs (Orange 51; San Francisco 64, Oct 2026). WARN therefore gives no evidence of a customer-support offshoring wave in the Bay Area.

## Headline numbers

Bay Area (9 counties) vs rest of CA, whole window: 97,753 Bay employees vs 199,943 rest. Bay = 32.8% of CA WARN employees vs 20.7% of CA workers (ACS 2024 employed residents), so Bay intensity is 243.5 vs 130.0 per 10,000 workers, ratio 1.87x. This level gap is persistent (ratio ranged 0.76-3.58 by quarter; see table) and driven by large tech/biotech/hardware single-site notices.

### Quarterly series (a)
Denominator: employed residents by county from ACS 2024 1-year PUMS (Bay 4,014,351; rest 15,382,398; CA 19,396,749). 2026Q4 is partial (40 of 92 days) so its raw numbers are not comparable; the per-92-day-equivalent is in out/warn_quarterly_bay_vs_rest.csv.

| Quarter (by received date)    |   Bay notices |   Bay employees |   Rest-CA notices |   Rest-CA employees | Bay share of CA employees   |   Bay per 10k workers |   Rest per 10k workers |   Bay/Rest ratio |
|:------------------------------|--------------:|----------------:|------------------:|--------------------:|:----------------------------|----------------------:|-----------------------:|-----------------:|
| 2023Q3                        |           117 |            5250 |               171 |                9313 | 36.1%                       |                 13.08 |                   6.05 |             2.16 |
| 2023Q4                        |           143 |            7209 |               288 |               15384 | 31.9%                       |                 17.96 |                  10    |             1.8  |
| 2024Q1                        |           169 |           11401 |               400 |               19437 | 37.0%                       |                 28.4  |                  12.64 |             2.25 |
| 2024Q2                        |           196 |           10604 |               330 |               15591 | 40.5%                       |                 26.42 |                  10.14 |             2.61 |
| 2024Q3                        |            87 |            6630 |               173 |               11019 | 37.6%                       |                 16.52 |                   7.16 |             2.31 |
| 2024Q4                        |           115 |            5843 |               339 |               15293 | 27.6%                       |                 14.56 |                   9.94 |             1.46 |
| 2025Q1                        |           127 |            6633 |               233 |               12029 | 35.5%                       |                 16.52 |                   7.82 |             2.11 |
| 2025Q2                        |           179 |            5942 |               251 |               29881 | 16.6%                       |                 14.8  |                  19.42 |             0.76 |
| 2025Q3                        |           136 |            6577 |               245 |               13707 | 32.4%                       |                 16.38 |                   8.91 |             1.84 |
| 2025Q4                        |           124 |            5405 |               290 |               14378 | 27.3%                       |                 13.46 |                   9.35 |             1.44 |
| 2026Q1                        |           116 |            5342 |               260 |               15857 | 25.2%                       |                 13.31 |                  10.31 |             1.29 |
| 2026Q2                        |           100 |            9889 |               322 |               10593 | 48.3%                       |                 24.63 |                   6.89 |             3.58 |
| 2026Q3                        |           112 |            7585 |               224 |                8934 | 45.9%                       |                 18.9  |                   5.81 |             3.25 |
| 2026Q4 (partial: Oct 1-Nov 9) |            39 |            3443 |               104 |                8527 | 28.8%                       |                  8.58 |                   5.54 |             1.55 |

### Fiscal-year and like-for-like comparison
Full fiscal years (FY26-27 is only 4.3 months old):

| fiscal_year   |   notices_bay |   employees_bay |   employees_rest |   bay_per10k |   rest_per10k | bay_share   |
|:--------------|--------------:|----------------:|-----------------:|-------------:|--------------:|:------------|
| FY2023-24     |           625 |           34464 |            59725 |        85.85 |         38.83 | 36.6%       |
| FY2024-25     |           508 |           25048 |            68222 |        62.4  |         44.35 | 26.9%       |
| FY2025-26     |           476 |           27213 |            54535 |        67.79 |         35.45 | 33.3%       |
| FY2026-27     |           151 |           11028 |            17461 |        27.47 |         11.35 | 38.7%       |

Like-for-like window July 1 - Nov 9 each year (the only fair comparison with FY26-27 to date):

| fiscal_year   |   notices_bay |   employees_bay |   employees_rest |   bay_per10k |   rest_per10k | bay_share   |
|:--------------|--------------:|----------------:|-----------------:|-------------:|--------------:|:------------|
| FY2023-24     |           176 |            8258 |            16466 |        20.57 |         10.7  | 33.4%       |
| FY2024-25     |           145 |            9825 |            17927 |        24.48 |         11.65 | 35.4%       |
| FY2025-26     |           229 |           10574 |            24443 |        26.34 |         15.89 | 30.2%       |
| FY2026-27     |           151 |           11028 |            17461 |        27.47 |         11.35 | 38.7%       |

Reading: Bay per-10k intensity in the like-for-like window rises 20.6 -> 24.5 -> 26.3 -> 27.5 (+33% FY23-24 to FY26-27) and the Bay share is 38.7% in FY26-27, the highest of four years. That is the one place the data lean toward "elevated." It is fragile: FY26-27's Bay total includes two notices of 1,605 (AEG Management Oakland, Oct 30, a venue operator) and 1,279 (Covenant Aviation Security, SF Sep 28), neither tech. Excluding all notices of 1,000+ employees, the FY26-27 Bay share falls to 31.8% (FY23-24 36.4%, FY24-25 35.4%, FY25-26 30.2%), i.e. NOT elevated. The top 10 rows make up 45.7% of FY26-27 Bay employees vs 17-21% in earlier years. Bay notice counts in the same window are 176, 145, 229, 151 (FY26-27 is lowest except FY24-25). Conclusion: Bay Area layoff intensity is NOT clearly elevated relative to FY23-24; the quarterly trend is flat; the FY26-27 like-for-like uptick is within single-notice noise.

Median Bay notice size is 18-33 employees; 62-67% of Bay rows are under 50 employees (CA overall 66%, and rows <50 account for only 14.9% of affected employees). So volume is dominated by a few large rows while the count is dominated by small sites.

### By county (b)
Employees by received-date fiscal year, and per 10,000 resident workers (full file: base/warn_bay_county_quarter.csv has county x quarter notices, employees, per-10k):

| county        |   FY2023-24 |   FY2024-25 |   FY2025-26 |   FY26-27 Jul1-Nov9 |   FY2023-24_per10k |   FY2024-25_per10k |   FY2025-26_per10k |
|:--------------|------------:|------------:|------------:|--------------------:|-------------------:|-------------------:|-------------------:|
| Alameda       |        6520 |        4719 |        4349 |                3055 |               74.1 |               53.6 |               49.4 |
| Contra Costa  |        2512 |        1829 |         641 |                 471 |               44.1 |               32.1 |               11.3 |
| Marin         |         326 |         308 |         154 |                 118 |               25.1 |               23.7 |               11.8 |
| Napa          |         397 |         777 |         430 |                  91 |               59.9 |              117.2 |               64.9 |
| San Francisco |        5692 |        5471 |        3667 |                2464 |              118.7 |              114.1 |               76.5 |
| San Mateo     |        4867 |        2598 |        5737 |                1412 |              119.9 |               64   |              141.3 |
| Santa Clara   |       13031 |        8183 |       10672 |                2950 |              127   |               79.7 |              104   |
| Solano        |         630 |         420 |        1160 |                  38 |               29.9 |               19.9 |               55   |
| Sonoma        |         489 |         743 |         403 |                 429 |               19.8 |               30.1 |               16.4 |

Like-for-like Jul 1 - Nov 9 employees by county:

|    | county        |   FY2023-24 |   FY2024-25 |   FY2025-26 |   FY2026-27 |
|---:|:--------------|------------:|------------:|------------:|------------:|
|  0 | Alameda       |        1886 |        2069 |        1712 |        3055 |
|  1 | Contra Costa  |         708 |         744 |         205 |         471 |
|  2 | Marin         |          54 |         146 |          61 |         118 |
|  3 | Napa          |         217 |         408 |         348 |          91 |
|  4 | San Francisco |        1460 |        1224 |        1105 |        2464 |
|  5 | San Mateo     |         649 |         495 |        1474 |        1412 |
|  6 | Santa Clara   |        3017 |        4042 |        5337 |        2950 |
|  7 | Solano        |         150 |           0 |         202 |          38 |
|  8 | Sonoma        |         117 |         697 |         130 |         429 |

Santa Clara and San Mateo carry the large, lumpy tech/biotech notices (Santa Clara 13,031 in FY23-24, 8,183, 10,672; San Mateo 4,867, 2,598, 5,737). San Francisco is falling per worker (118.7 -> 114.1 -> 76.5) with a jump in FY26-27 to date driven by Covenant (1,279). Contra Costa fell sharply (44.1 -> 11.3 per 10k). Small counties (Marin, Napa, Solano, Sonoma) are noise-dominated and should not be read for trend.

### Top 30 Bay Area employers by affected employees, whole window (c)
Employer = company name with parentheticals / "- site" / "dba" suffix stripped, so site-level notices roll up (company_norm in warn_ca is the strict name; this roll-up is a separate analysis key). TECH = software/internet/semiconductor/IT firms per a hand-curated list (not NAICS; NAICS exists only for FY26-27). Amazon is flagged tech but includes fulfillment/retail sites. Top 30 = 40.4% of 97,753 Bay employees across 647 employer groups.

| employer                               |   employees |   notices | counties                                                                            | flag                                     | first      | last       |
|:---------------------------------------|------------:|----------:|:------------------------------------------------------------------------------------|:-----------------------------------------|:-----------|:-----------|
| Meta Platforms, Inc.                   |        4023 |        19 | Alameda, San Francisco, San Mateo, Santa Clara                                      | TECH                                     | 2025-10-23 | 2026-05-26 |
| Cisco Systems, Inc.                    |        2668 |        14 | San Francisco, Santa Clara                                                          | TECH                                     | 2023-09-12 | 2026-06-24 |
| Tesla, Inc.                            |        2589 |        16 | Alameda, Santa Clara                                                                | tech-adjacent (EV/AV/hardware/solar mfg) | 2024-04-25 | 2024-05-13 |
| Jabil Inc.                             |        2479 |        13 | Alameda, Santa Clara, Solano                                                        | tech-adjacent (EV/AV/hardware/solar mfg) | 2023-07-26 | 2026-08-21 |
| Intel Corporation                      |        2399 |        61 | Santa Clara                                                                         | TECH                                     | 2023-07-11 | 2026-09-18 |
| Amazon                                 |        1696 |        34 | San Francisco, Santa Clara                                                          | TECH                                     | 2023-12-05 | 2026-08-31 |
| AEG Management Oakland LLC             |        1605 |         1 | Alameda                                                                             |                                          | 2026-10-30 | 2026-10-30 |
| Oracle America, Inc.                   |        1578 |        13 | Alameda, San Mateo, Santa Clara                                                     | TECH                                     | 2025-08-13 | 2026-09-15 |
| Walmart                                |        1564 |        23 | Alameda, San Mateo, Santa Clara                                                     |                                          | 2024-05-01 | 2026-06-23 |
| Broadcom Inc.                          |        1514 |         2 | Santa Clara                                                                         | TECH                                     | 2024-01-03 | 2025-10-20 |
| Cruise LLC                             |        1483 |        27 | San Francisco, San Mateo, Santa Clara                                               | tech-adjacent (EV/AV/hardware/solar mfg) | 2024-01-19 | 2025-10-01 |
| LinkedIn Corporation                   |        1475 |        13 | San Francisco, Santa Clara                                                          | TECH                                     | 2023-07-24 | 2026-05-15 |
| Covenant Aviation Security, LLC        |        1279 |         1 | San Francisco                                                                       |                                          | 2026-09-28 | 2026-09-28 |
| Genentech, Inc.                        |        1121 |         7 | San Mateo                                                                           |                                          | 2024-04-09 | 2026-07-01 |
| eBay Inc.                              |         979 |         6 | San Francisco, Santa Clara                                                          | TECH                                     | 2024-02-01 | 2026-10-21 |
| Intuit Inc.                            |         927 |         3 | San Francisco, Santa Clara                                                          | TECH                                     | 2024-07-10 | 2026-05-21 |
| Workday Inc.                           |         913 |         3 | Alameda                                                                             | TECH                                     | 2025-02-05 | 2026-09-29 |
| Cepheid                                |         910 |        31 | Alameda, Santa Clara                                                                |                                          | 2024-01-25 | 2026-11-03 |
| Kaiser Foundation Hospitals            |         890 |        90 | Alameda, Contra Costa, Marin, San Francisco, San Mateo, Santa Clara, Solano, Sonoma |                                          | 2023-10-03 | 2025-10-16 |
| Chevron                                |         879 |         5 | Contra Costa                                                                        |                                          | 2025-04-02 | 2026-07-08 |
| Gate Gourmet, Inc.                     |         835 |         1 | San Francisco                                                                       |                                          | 2025-03-12 | 2025-03-12 |
| Safeway                                |         810 |        13 | Alameda, Contra Costa, San Francisco, Santa Clara, Solano, Sonoma                   |                                          | 2023-10-13 | 2026-10-20 |
| Apple Inc.                             |         761 |        11 | Santa Clara                                                                         | TECH                                     | 2024-04-02 | 2026-08-21 |
| BILL Operations, LLC                   |         681 |         5 | Santa Clara                                                                         | TECH                                     | 2024-01-16 | 2026-06-24 |
| Salesforce, Inc.                       |         677 |         6 | San Francisco                                                                       | TECH                                     | 2024-02-05 | 2026-08-05 |
| Visa                                   |         613 |         5 | San Francisco, San Mateo                                                            |                                          | 2024-11-01 | 2026-07-31 |
| PayPal                                 |         562 |         2 | Santa Clara                                                                         | TECH                                     | 2024-02-05 | 2026-09-01 |
| Republic National Distributing Company |         546 |         4 | Alameda, Santa Clara                                                                |                                          | 2025-01-09 | 2025-07-02 |
| Gilead Sciences, Inc.                  |         512 |         7 | San Mateo                                                                           |                                          | 2023-11-03 | 2026-05-01 |
| Amys Kitchen, Inc.                     |         505 |         3 | Sonoma                                                                              |                                          | 2024-10-08 | 2026-09-17 |

Tech-flagged employers in the top 30: Meta, Cisco, Intel, Amazon, Oracle, Broadcom, LinkedIn, eBay, Intuit, Workday, Apple, BILL, Salesforce, PayPal (14), plus tech-adjacent Tesla, Jabil, Cruise. Biotech/healthcare (Genentech, Cepheid, Kaiser, Gilead), retail/food (Walmart, Safeway, Amy's) and venue/security (AEG, Covenant, Gate Gourmet) make up most of the rest.

Bay Area tech share of affected employees:

| fiscal_year   |   total |   tech_core |   tech_adj |   naics51_xlsx |   core_share |   core+adj_share |
|:--------------|--------:|------------:|-----------:|---------------:|-------------:|-----------------:|
| FY2023-24     |   34464 |        7962 |       4787 |              0 |        0.231 |            0.37  |
| FY2024-25     |   25048 |        5402 |       1970 |              0 |        0.216 |            0.294 |
| FY2025-26     |   27213 |       12799 |       1003 |              0 |        0.47  |            0.507 |
| FY2026-27     |   11028 |        2929 |        382 |            963 |        0.266 |            0.3   |

### Layoff type mix (d)
Permanent share of affected employees, by fiscal year (False = rest of CA, True = Bay):

| fiscal_year   | bay   |   Not Identified |   Permanent |   Temporary |   perm_share |
|:--------------|:------|-----------------:|------------:|------------:|-------------:|
| FY2023-24     | False |              137 |       52682 |        6906 |         88.2 |
| FY2023-24     | True  |                0 |       33257 |        1207 |         96.5 |
| FY2024-25     | False |              424 |       62669 |        5129 |         91.9 |
| FY2024-25     | True  |              106 |       23825 |        1117 |         95.1 |
| FY2025-26     | False |              615 |       47744 |        6176 |         87.5 |
| FY2025-26     | True  |              151 |       26389 |         673 |         97   |
| FY2026-27     | False |               87 |       12332 |        5042 |         70.6 |
| FY2026-27     | True  |                0 |       10332 |         696 |         93.7 |

Closure share of affected employees:

| fiscal_year   | bay   |   Closure |   Layoff |   Unknown |   closure_share |
|:--------------|:------|----------:|---------:|----------:|----------------:|
| FY2023-24     | False |     24241 |    35484 |         0 |            40.6 |
| FY2023-24     | True  |      8580 |    25884 |         0 |            24.9 |
| FY2024-25     | False |     41178 |    27044 |         0 |            60.4 |
| FY2024-25     | True  |      6483 |    18565 |         0 |            25.9 |
| FY2025-26     | False |     26363 |    28172 |         0 |            48.3 |
| FY2025-26     | True  |      5872 |    21341 |         0 |            21.6 |
| FY2026-27     | False |      8494 |     8820 |       147 |            48.6 |
| FY2026-27     | True  |      2580 |     8448 |         0 |            23.4 |

The Bay mix is NOT shifting toward permanent: permanent share is 96.5%, 95.1%, 97.0%, 93.7% (essentially saturated from the start; quarterly Bay permanent share ranges 86%-100% with no trend). The mix is NOT shifting toward layoffs-vs-closures either: Bay closure share is a stable 22-26% of employees (rest of CA 41-60%), so Bay notices are overwhelmingly permanent partial layoffs (consistent with white-collar restructuring), not site closures. Temporary layoffs are minor (2.5-6.3% of Bay employees by fiscal year). Rest-of-CA permanent share drops to 70.6% in FY26-27 to date (a 5,042 temporary-layoff block).

### Call-center relocations (e)
Full list of Call Center Relocations Report rows (xlsx, covers 2023-01-01 to 2026-11-09): 1 record. American General Life Insurance Company, Los Angeles County (Woodland Hills), 163 employees, Layoff Permanent, notice 2023-02-27, received 2023-03-02, effective 2023-05-01. FY2022-23: 1 notice, 163 employees; FY2023-24 through FY2026-27: 0. Destination not given (the report has no destination column). Saved to base/warn_call_centers.csv. Bay Area call-center relocation notices: 0. Name-matched customer-contact sites (not official relocations): Charter Communications Customer Contact Center (San Bernardino, 430, closure, rec'd 2024-06-13), Sky Chefs' Customer Service Center (San Bernardino, 14, 2026-03-10), Conduent (Orange, 51, 2026-07-14), Conduent State & Local Solutions (San Francisco, 64, 2026-10-23). Haas Automation (Ventura, 73+74) appears as a "Relocation Permanent" type in the main report but is machine-tool manufacturing, not a call center. Caveat: one record cannot support any inference about trend; it is a null result for this mechanism, not proof of no offshoring (notices are only required for 50+ job losses at one site).

### Industry (f)
NAICS "Related Industry" exists ONLY in the current xlsx (FY26-27, Jul 1 - Nov 9 2026, 479 notices, 100% populated); the PDFs have no industry field, so no multi-year industry trend is possible. Bay Area FY26-27-to-date, employees by sector:

| ind                                                                |   employees |   notices |   share |
|:-------------------------------------------------------------------|------------:|----------:|--------:|
| 31-33 Manufacturing                                                |        2243 |        31 |    20.3 |
| 56 Administrative and Support and Waste Management and Remediation |        2084 |        12 |    18.9 |
| 71 Arts Entertainment and Recreation                               |        1713 |         2 |    15.5 |
| 54 Professional Scientific and Technical Services                  |        1048 |        18 |     9.5 |
| 51 Information                                                     |         963 |         9 |     8.7 |
| 52 Finance and Insurance                                           |         744 |         5 |     6.7 |
| 44-45 Retail Trade                                                 |         705 |        11 |     6.4 |
| 72 Accommodation and Food Services                                 |         364 |         4 |     3.3 |
| 11 Agriculture Forestry Fishing Hunting                            |         344 |         2 |     3.1 |
| 62 Healthcare and Social Assistance                                |         306 |        27 |     2.8 |
| 48-49 Transportation and Warehousing                               |         217 |         5 |     2   |
| 21 Mining Quarrying Oil and Gas Exraction                          |         180 |         1 |     1.6 |
| 92 Public Administration                                           |          82 |        19 |     0.7 |
| 61 Educational Services                                            |          28 |         1 |     0.3 |
| 42 Wholesale Trade                                                 |           7 |         4 |     0.1 |

Within these 4.3 months Bay monthly totals are 2,042 / 1,962 / 3,581 / 3,028 / 415 (Jul..Nov 1-9, noisy). Information (NAICS 51) is 8.7% (963 employees, 9 notices: Netflix 227, Airtable 190, Workday 142, Synopsys 128...). Note NAICS labels are the filer/EDD assignment and look noisy (e.g., Oracle America tagged 31-33 Manufacturing; eBay tagged Retail Trade; PayPal/Visa Finance), so sector shares understate tech. Professional/Scientific/Technical is 9.5%. Manufacturing 20.3% and Administrative & Support (largely the Covenant security notice) 18.9% lead.

## What WARN can and cannot support (Task 3, honest limits)

- **No occupations, no job titles.** WARN carries company, site address, county, headcount, layoff/closure type, dates, and (FY26-27 xlsx only) a coarse NAICS sector. Nothing in this analysis identifies support, clerical, engineering or any other occupation. Do not read these results as "support/clerical exposure." Any occupation split would have to come from elsewhere (e.g., postings, OEWS, firm announcements).
- **Coverage.** Cal-WARN applies to employers with 75+ employees and mass layoffs/closures/relocations (50+ at a covered establishment in 30 days). It misses contractor/vendor non-renewals (the likeliest channel for outsourced support work), attrition and hiring freezes, rolling cuts below the thresholds, and small employers. Despite the threshold, 66% of parsed rows are under 50 employees (these are typically sites of a multi-site notice or partial counts), so the data are site-fragmented and "notices" are not a count of firm events.
- **Eligible employment share.** I could not derive this from the data here (no establishment-size data was fetched). Stated ASSUMPTION, not a result: roughly 40-60% of Bay Area private employment sits at establishments/employers over the 75-employee line (to be replaced with Census CBP/SUSB size-class tables for the nine counties). On that assumption WARN could only ever see layoffs concentrated in half the employment base, and only the portion that is a mass event. Observed scale: Bay WARN employees per year are 0.86% (FY23-24, 34,464/4.01M), 0.62% (FY24-25) and 0.68% (FY25-26) of resident workers; actual job loss from all causes is far larger.
- **Timing/geography.** WARN notices are 60 days ahead of effective dates and the quarter is assigned by received date; they are worksite-based while the denominator is residence-based (commuting mismatch across Bay counties and into the Bay from the Central Valley). Remote employees are attributed to an assigned site, so SF/Santa Clara counts may be inflated or misplaced.
- **Notice type.** Rescinded or revised notices and duplicate/updated filings are not netted out. 8 rows (1,044 employees) are exact duplicates of other rows (kept, <0.4% of employees).

## What would change AI-exposure interpretation
WARN shows large-firm tech white-collar restructuring is real and lumpy (Meta, Cisco, Intel, Oracle, LinkedIn, Intuit), concentrated in a few firms and weeks, with no sustained upward trend in Bay intensity. It cannot attribute any of that to AI, cannot see support/clerical roles, and structurally misses contractor/BPO channels. The absence of a call-center-relocation signal and a flat Bay trend is a null result for "AI is visibly driving mass layoffs in covered Bay establishments," not evidence about AI exposure of occupations.

## Parse quality
- PDFs parsed with pdfplumber table extraction (pypdf text wrapped long company names across lines and mangled columns). Every PDF's own "Summary by Month" page was used as an independent check: all 39 month and total lines (12 months x 3 PDFs + 3 totals) match exactly on notice count and employee count. Totals: FY2023-24 1,814 notices / 94,189 employees; FY2024-25 1,506 / 93,273; FY2025-26 1,593 / 81,748; FY2026-27 (to 11/9/2026, xlsx) 479 / 28,489. No fiscal year failed.
- 10 random rows hand-checked against raw pypdf text: 10/10 field matches (dates, company, county, headcount, type, address).
- 100% of rows have a county (56 CA counties in the data, plus 2 out-of-state rows flagged) and a positive integer employee count; city is derived from a zip->city map learned from double-space-delimited addresses (99.5% populated; PDFs collapse the street/city double space, so city is a derived field, less reliable than county). 
- The PDFs begin with notices dated Apr-Jun 2023 received July 2023 onward; FY assignments use the received date.
- Not available: pre-July-2023 history (only the single 2023-03 call-center record), industry for PDF years, call-center section in the PDFs.
- Denominators: BLS LAUS (laucnty23/24/25.txt) returned HTTP 403 Access Denied even with a browser user agent. Census county population (co-est2024-alldata.csv) downloaded fine and is saved (POPESTIMATE2023/2024 in base/warn_county_denominators.csv), but the memo uses employed residents (ACS 2024 1-year PUMS, ESR in 1,2,4,5, summed over PUMAs allocated to counties by 2020 tract share) because "per 10,000 workers" was requested. Multi-county PUMAs split by tract count; single-year denominator applied to all years.
