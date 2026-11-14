# E3: The mover's ledger

**Question.** A Bay Area worker in a common low-wage job has four options: stay put (rent capped by AB 1482), re-rent somewhere else in the Bay at today's turnover rent, move inland (Sacramento, Stockton, Modesto, Fresno), or leave the state (Phoenix, Las Vegas, Reno, Boise, Dallas, Houston, Portland). How much of the paycheck is left after rent in each case? And what does the move cost in things that don't show up on the ledger?

**Run it.** `python3 -I run_all.py` (add `--rebuild-indeed` to rebuild the Indeed DuckDB from the raw CSV, or `--skip-model` to reuse the imputed postings). A full run takes about 10 minutes, most of it the ridge model.

## Layout
| path | what |
|---|---|
| `run_all.py` | single entry point |
| `scripts/load_indeed.py` | raw Indeed CSV → DuckDB (`read_csv all_varchar, max_line_size=30000000, ignore_errors, parallel=false`). By default it reads the shared `analysis/cache/indeed.duckdb` read-only |
| `scripts/fetch_external.py` | downloads into `raw/`: ZORI, Census ZCTA→county file, BLS OEWS via API |
| `scripts/geo.py` | Indeed `location` → county → metro/region |
| `scripts/salary_parser.py`, `scripts/hand_checks.py` | salary parser and its 50 hand-checked rows |
| `scripts/occupations.py` | title-normalization regex rules (documented in the file) |
| `scripts/salary_model.py` | TF-IDF + ridge pay model, baselines, imputation, missing-pay shares |
| `scripts/ledger.py` | rents, turnover premium, wages, ledger |
| `scripts/figs.py` | figures |
| `raw/` | downloaded data only |

## Data decisions
- **Salary parser.** Converts `salary_formatted` to an hourly equivalent: year/2080, month/(2080/12), week/40, day/8. English and Spanish forms are handled ("por hora", "Desde", "Hasta"…). A range becomes low/high/mid; "From X" and "Up to X" become a single point with a kind flag. Pay per mile, session, class, order or trip is left unconverted. Values are dropped when the midpoint is below $10/h or above $300/h, or when the range's high/low ratio is above 4 (e.g. "$100,000 – $1,000,000"). Result: 119,194 of 140,816 postings have a usable hourly value.
- **Hand checks.** `outputs/parser_hand_checks.csv` holds 50 rows: 2 random rows from each of the 20 most common string patterns, plus 10 from rarer patterns. The expected values were written by hand as arithmetic in `scripts/hand_checks.py`. **All 50 match.** Two rows are flagged as semantically doubtful even though the arithmetic is right: "$500 a week" (probably part-time) and "$84.64–$122.73 a day" (probably a short-shift rate). The 40 h/week and 8 h/day assumptions under-state hourly pay for these.
- **Geography.** A CA ZIP in the location string maps to a county through the Census 2020 ZCTA→county file (largest land overlap). With no ZIP, the city name maps to the most common county among Indeed rows for that city that do have a ZIP. "X County" strings and a few names such as "SF Bay Area" and "East Bay" are handled by hand. 2,305 postings stay Unknown, mostly the bare string "California".
  - Bay = the 9 counties.
  - Sacramento = Sacramento, Placer, El Dorado and Yolo counties.
  - Stockton = San Joaquin. Modesto = Stanislaus. Fresno = Fresno.
- **Occupations.** There are 10 groups, assigned by regex with first match winning. Titles containing manager, supervisor, lead, RN, engineer, software, analyst and similar words are excluded. Rules and SOC codes are in `scripts/occupations.py`. Pharmacy tech is classified but left out of the ledger because it has too few postings: 41 in the Bay, 2 in Fresno.

  Postings per group (Bay / Sacramento / Stockton / Modesto / Fresno):

  | Group | Bay | Sac | Stk | Mod | Fre |
  |---|---|---|---|---|---|
  | Cashier | 1050 | 264 | 85 | 97 | 112 |
  | Crew | 698 | 188 | 45 | 53 | 100 |
  | Cook | 442 | 96 | 30 | 25 | 30 |
  | Warehouse | 436 | 151 | 89 | 39 | 57 |
  | Janitor | 435 | 110 | 30 | 18 | 34 |
  | Caregiver | 417 | 83 | 17 | 13 | 16 |
  | Driver | 340 | 73 | 26 | 18 | 24 |
  | Security | 122 | 30 | 7 | 7 | 6 |
  | Med. asst | 117 | 23 | 11 | 4 | 27 |
  | CNA | 78 | 18 | 6 | 4 | 6 |
- **Bay rents** come from current Zillow FOR_RENT listings (`zillow.duckdb` table `z`). The 1-BR median is $2,895 for the Bay and $3,892 for SF; the 2-BR median is $3,431 for the Bay and $5,334 for SF.
  - **In-place ("stay")** = that median, as specified in the brief. This is a proxy: listings are asking rents, not what sitting tenants pay.
  - **Stay +1 year** = in-place × 1.08. That is the largest AB 1482 increase, min(5% + CPI, 10%), using an *assumed* CPI of 3%.
  - **Re-rent in the Bay** = in-place × the county turnover premium. The premium is the median `next_first/last_p` on the same unit in table `turn`, with `start_gap_y` between 1 and 6 and the next listing starting in 2025 or later. Bay-wide it is **1.10** (listing-weighted). By county: SF 1.27, San Mateo 1.16, Santa Clara 1.10, Alameda 1.06, Napa 1.00. Over all years the median is 1.08 (n = 37,752). This jump compares two *listing* prices. The previous tenant's actual rent may have risen during the tenancy, so the premium over a sitting tenant could be smaller.
- **Destination rents.** Zillow ZORI by metro for September 2026 (latest available), downloaded successfully, so the HUD FMR fallback was not used. (HUD's xlsx endpoint also returned empty responses.) ZORI is an all-unit index, so it is scaled by a bedroom factor: k = the Bay's median listing ÷ the Bay's county-matched ZORI. That gives k₁ = 0.84 and k₂ = 1.01, and assumes destinations have the same bedroom-to-typical-rent ratio as the Bay.
- **Wages.** Monthly gross = hourly × 173.
  - **OEWS:** BLS OEWS May 2025 metro *median* hourly wage, fetched through the public BLS API. The bulk zip download returned 403. All 13 metros × 13 SOC codes were returned. The Bay uses the SF–Oakland–Fremont MSA.
  - **Indeed posted:** median midpoint among postings with pay. A destination cell with fewer than 15 such postings falls back to a pooled Stockton+Modesto+Fresno figure (flagged in `ledger_long.csv`). The CNA cells for the Central Valley are missing even after pooling.
  - Indeed covers California only. **There are no Indeed wages for out-of-state destinations**, so the headline ledger uses OEWS everywhere for consistency, with Indeed as a check for the California scenarios.
  - Across the 39 occupation × CA-metro cells with at least 15 postings, the Indeed posted median runs **$0.96/h above OEWS on average** (median +$0.32, r = 0.83; fig 4).

## Salary model (the ML component)
**Setup.**
- Target: log hourly pay (midpoint).
- Features: title as word 1–2-grams and character 3–5-grams, the first 4,000 characters of the description as 1–2-gram TF-IDF, and one-hot county, region and job type. Model: ridge regression, with alpha = 1 chosen on an inner split grouped by company.
- Test split: **GroupShuffleSplit by company, 80/20**. Train has 94,087 postings from 24,680 companies; test has 25,107 postings from 6,170 companies, with no company in both.

| model (company-held-out test, n = 25,107) | MAE $/h | RMSE | R² | MAPE | R² (log) |
|---|---|---|---|---|---|
| B1: median by county | 21.85 | 32.18 | 0.19 | 48.8% | 0.22 |
| B2: median by normalized title × region | 16.45 | 26.51 | 0.45 | 36.6% | 0.50 |
| **TF-IDF + location ridge** | **9.49** | **16.75** | **0.78** | **18.1%** | **0.86** |

**Subgroups** (`outputs/salary_model_subgroups.csv`, fig 5):
- **By region**, ridge MAE ranges from $5.6 (Inland Empire) to $12.9 (Bay Area), and ridge beats B2 in every region. The Bay is hardest because it has the most high-wage tech postings.
- **By wage tier**, ridge MAE is <$20: $3.6, $20–30: $4.0, $30–50: $6.9, $50+: $17.7. Ridge under-predicts the $50+ tier on average (bias −$10.4) and over-predicts below $30 (+$2.4 to +$3.0). That is regression to the mean.
- **Important caveat for this experiment:** on the 10 low-wage occupation groups pooled (n = 3,387), **the simple title × region median (MAE $2.64) beats the ridge ($2.95)**. Ridge loses on cashier, crew, medical assistant, caregiver and warehouse, and wins on CNA, security, driver, cook and janitor. The ridge earns its keep on heterogeneous, higher-paid postings. For homogeneous low-wage titles, a grouped median is as good or better. That is why the ledger uses *observed* posted pay, not imputed pay. Imputed pay appears only in `postings_with_pay.parquet` and the `med_with_imputed` column.

**Failure examples** (`outputs/salary_model_failures*.csv`):
- Unit errors in the source, e.g. "Entry Level Manager" at "$45,000 – $50,000 a month" and "Data Entry Operator" at "$32,000 – $40,000 a month". These are probably annual figures labeled as monthly.
- Physician salaries ($400k–$800k a year), which the model shrinks toward about $70/h.
- Day rates for owner-operators, e.g. a dry-van driver at "$1,500 – $1,700 a day".
- Before the high/low ratio filter was added, ranges like "$165,000 – $1,750,000" dominated the error list.
- Title rules that leak: "Adjunct Faculty – CNA" ($76/h) is counted as a CNA, and "Field Sales Associate – Urology" ($35/h) as a cashier.

**Missing pay** (`outputs/pay_missing_share.csv`, fig 6). Under SB 1162, California employers with 15+ employees must post pay ranges. Still, **14.5% of postings carry no salary text at all, and 15.4% have no usable hourly figure.** By region: Bay 15.2% with no text, LA/Orange 13.7%, Central Valley 14.0%, Sacramento 13.4%, Unknown location 24.6%. By occupation, delivery drivers (23.7%), pharmacy techs (25.4%) and fast-food crew (17.8%) are the worst. Caregivers (6.8%) and medical assistants (7.4%) are the best.

## Ledger results
Results use a 1-BR, a single full-time worker, Bay origin and OEWS wages. Full tables are in `outputs/ledger_burden_1br_*.csv`, `ledger_residual_1br_*.csv` and `ledger_long.csv` (which includes 2-BR, the SF origin and Indeed wages). Figures 1–3 and S1–S2.

| Occupation (OEWS Bay median) | Stay | Stay +1y max cap | Re-rent Bay | Sacramento | Fresno | Phoenix | Houston |
|---|---|---|---|---|---|---|---|
| CNA ($26.96) | 62% | 67% | 68% | 48% | 46% | 38% | 44% |
| Caregiver / HHA ($17.28) | **97%** | 105% | 107% | 67% | 60% | 47% | 71% |
| Medical assistant ($28.75) | 58% | 63% | 64% | 37% | 45% | 37% | 39% |
| Cashier ($19.84) | 84% | 91% | 93% | 62% | 59% | 50% | 56% |
| Janitor / housekeeper ($21.24) | 79% | 85% | 87% | 55% | 55% | 48% | 54% |
| Warehouse ($23.27) | 72% | 78% | 79% | 50% | 53% | 39% | 44% |

The cells are rent burden, meaning rent as a share of gross wage. Residual income after rent for a caregiver is **$94/month** if staying in the Bay, **−$197** to re-rent, $949 in Sacramento, and $1,626 in Phoenix.

- **SF origin.** Using SF-county rents with the same metro wages, every group except medical assistant and CNA is at or above 92% of gross pay just to stay. Re-renting in SF, where the turnover premium is 1.27, costs 99–165% of gross pay.
- **Family version (2-BR, one earner).** Staying costs 69–115% of gross pay. Sacramento costs 45–81%, Phoenix 45–61%.
- **Indeed posted wages** (California only) give the same picture. A CNA pays 64% to stay, 71% to re-rent and 48% in Sacramento. A cashier pays 85% to stay, 94% to re-rent, 61% in Sacramento and 57% in Fresno.
- **The ranking is consistent across all 10 groups.** Re-renting in the Bay is always the worst. Out-of-state metros usually leave the most money, with Portland giving the highest residual for 8 of 10 groups. Modesto is highest for crew and Sacramento for medical assistants. Even so, every inland and out-of-state burden stays above 30% (the lowest is 32%), which still counts as "burdened".
- **The cap, in perspective.** For the Bay as a whole, the turnover premium (+10%) is about one year of the largest raise AB 1482 allows (+8%). The rent cap protects stayers most in SF and San Mateo, where the premiums are 1.27 and 1.16.

## What the ledger does not count (California Policy Lab, "Priced Out of the Bay", July 2026, https://capolicylab.org/priced-out-of-the-bay/, figures as summarized in the team brief)
- **Rent differences: our numbers are larger than CPL's.** CPL finds that people who move from the Bay to other parts of California land in places with 27% lower rents, and out-of-state movers in places with 38% lower rents. Our metro-median comparison gives larger gaps: inland CA is 29–40% below the Bay 1-BR median (median 37%), and out-of-state is 40–52% below (median 50%). One likely reason is that real movers pick neighborhoods and units that differ from metro medians.
- **Neighborhood income.** Out-of-state movers land among neighbors with about 23% lower incomes.
- **Schools.** Movers' new schools score 2–4 points lower.
- **Where low-income movers actually go.** 75% stay in the Bay and only 8% go to the Central Valley. The "move inland" row is the exception, not the norm. Most low-income movers end up in the "re-rent in Bay" row, which is the worst one in the ledger.
- **Lost social and job ties.** A higher residual in Fresno or Phoenix does not count lost networks, childcare from family, health-care continuity, or the job-search time needed to actually land the destination wage.

## Caveats
- **Posted ≠ earned.** Indeed shows advertised midpoints, and "From/Up to" values are single points. OEWS medians are survey wages for all workers, not new hires. Neither reflects actual hours: many of these jobs are part-time, and 173 h/month is the best case.
- **Listings ≠ sitting-tenant rents.** The "stay" rent is a current *asking* median. Long-tenure tenants usually pay less, so the stay burden is overstated for them and the move gain understated. The turnover premium compares listing to listing.
- **Destination bedroom rents assume the Bay's bedroom-to-ZORI ratio.** The AB 1482 CPI of 3% is an assumption.
- **Not included:** taxes (no state income tax in NV, TX or WA differs from CA and OR), commute, car ownership, childcare, utilities, moving costs and deposits, and benefits.
- **The occupation regexes are imperfect** (see the failures above). The CNA cells are thin (78 Bay postings, under 15 with pay in each Central Valley metro).
- **CPL figures are cited as given in the brief; we did not re-verify them.** CPL measures where movers land, not what they earn, so their numbers and ours aren't directly comparable.
