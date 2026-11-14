# E6: Who takes the leaver's place? (unit + replacement household)

E2 showed that the same unit re-rents higher after a tenant leaves. E6 asks what else changes for the *household that
replaces the leaver*: the income it needs to pass screening, whether a buyer replaces the renter, and what the
listing's text says about upgrades and move-in deals.

## Reproduce
```bash
python3 analysis/e6_unit_replacement/run_all.py      # ~1 min; writes outputs/run_all.log
```
`run_all.py` downloads any missing files into `raw/`: CA HCD State Income Limits PDFs for 2022–2026 and the Freddie Mac PMMS
CSV. The PDFs are parsed with `python -I`. The script then runs these steps:
- `s00` pulls description, special_offer and similar columns from the raw CSVs into `cache/extra.parquet`. No address columns are kept.
- `s01` parses the income limits.
- `s02` does analysis 1, the income gate.
- `s03` does analysis 2, tenure replacement.
- `s04` does analysis 3, text and concessions.
- `s05` runs the regex hand check, merging the manual verdicts in `hand_check_verdicts.csv`.

The Zillow cache is opened read-only. Turnover pairs are E2's cleaned sample: 23,306 deduplicated pairs with a 1–6 year gap. Pairs with missing beds are dropped, leaving 23,277.

**Income limits source.** HUD's huduser.gov returned an empty page (HTTP 202) to scripted downloads, so I used the
**CA HCD State Income Limits**. These are HUD-based and list "Very Low" (50%), "Low" (80%) and "Median" limits for
1–8-person households by county. I parsed 2022–2026; earlier years were not found at the archived URLs. The values
match HUD where I knew them; for example, Alameda FY2025 4-person Low = $125,050. They are in `outputs/income_limits_bay.csv`.

## Analysis 1: income gate for the replacement household (main result)
**Method.**
- Minimum qualifying income = multiplier × 12 × asking rent.
  - Leaver: the last ask of their tenancy.
  - Newcomer: the first ask after it.
- The multiplier is the one stated in the unit's current description when there is one (3.5% of pairs; precision 20/20 in the hand check), and 3× otherwise.
  - Among distinct descriptions that state one: 3× appears in 581, 2.5× in 281, and 2× in 32. Full counts are in `a1_stated_income_multiplier_dist.csv`.
  - Sensitivity run: 2.5× for every unit.
- Household size = bedrooms + 1, with a studio counted as 1.
- Limits are year-matched: an HCD year applies from June to the following May.
- **Primary sample:** the leaver's last ask is on or after 2022-06, so both dates have a limit. That leaves n = 12,870 pairs, 65% of them re-listed in 2026.
- A unit "lost ≤80% qualifiability" when the leaver's rent was ≤ the Low limit and the newcomer's rent is above it.
- I also report the reverse ("gained") and a turnover-attributable version. In that version the unit would have stayed
  qualifiable if the rent had grown only at AB 1482's 10%/yr maximum over the gap.

**Headline:** **6.4% of turnovers (2022-06 → 2026) priced the unit out of reach of a ≤80% AMI household of the
unit's size.** That is 11.1% of the units that were reachable before the turnover.
- At ≤50% AMI the figure is 2.1% of turnovers, which is 34% of the few units (6%) that were reachable at 50%.
- **Region-wide this is offset:** 6.4% of turnovers moved units *into* reach, because income limits rose about as fast as rents. The net effect is 0.0pp.
- **San Francisco and San Mateo are the exception.** Their shared HMFA limit was flat in 2024→2025 while rents rebounded.
- 2.4% of all turnovers crossed the line only because the jump exceeded what the cap would allow in place. In SF that figure is 9.0%.

| county | n | income needed / AMI, leaver → newcomer | lost ≤80% | gained ≤80% | net | lost, beyond cap | lost ≤50% |
|---|---|---|---|---|---|---|---|
| San Francisco | 1,535 | 0.82 → 0.96 | **20.7%** | 0.7% | **+20.1pp** | 9.0% | 5.7% |
| San Mateo | 1,209 | 0.82 → 0.87 | 13.9% | 2.1% | +11.8pp | 3.5% | 2.0% |
| Santa Clara | 3,198 | 0.73 → 0.74 | 4.4% | 5.4% | −1.0pp | 2.0% | 1.3% |
| Alameda | 3,827 | 0.74 → 0.74 | 3.6% | 8.0% | −4.4pp | 1.0% | 1.9% |
| Contra Costa | 1,434 | 0.71 → 0.71 | 2.0% | 6.6% | −4.7pp | 0.6% | 2.0% |
| Marin / Napa / Solano / Sonoma | 253 / 224 / 575 / 615 | — | 0.8–2.0% | 1.6–17.4% | — | ≤1.3% | ≤0.8% |
| **All** | 12,870 | 0.76 → 0.77 | **6.4%** | 6.4% | 0.0pp | 2.4% | 2.1% |

- **By year re-listed (lost / gained):** 2024 3.8% / 7.3%, 2025 3.6% / 7.6%, **2026 7.8% / 6.0%**.
  - SF 2026 alone: **28.7% lost** vs 0.3% gained, and 13.3% beyond the cap.
- **By beds (lost):** studio 7.2%, 1BR 8.6%, 2BR 6.4%, 3BR 3.5%, 4+ 2.0%. Small units are the ones losing low-income reach.
- **Top ZIPs** (n ≥ 30): all in SF, plus 94080. They lose 25–39% of turnovers; see `a1_income_gate_by_zip.csv`.
- **2.5× sensitivity:** lost 5.0%, gained 4.5%, and lost at ≤50% 4.7%. More units sit near the 50% line at 2.5×.
- An alternative that judges both rents against the *newcomer-year* limit, over all 2023+ re-listings, gives lost 13.6% vs gained 1.2%.
  - This isolates the price move from limit growth.
  - Unit-level rows are in `a1_pairs_primary.parquet`. Figures: `figs/a1_ami_needed_by_county.png` and `figs/a1_lost_qualifiability_by_county.png`.

## Analysis 2: tenure replacement (renter replaced by a buyer or an investor)
**Rent → sale.** A rental tenancy is followed by an arm's-length "Sold" event within 2 years, with no rental listing in between.
- 5,006 events after deduplication and keeping price / annual rent in [5, 60]. 3,412 of them are in 2025–26, because the scrape is heavy on recently sold homes.
- Buyer income is computed with:
  - 20% down;
  - the PMMS 30-year rate in the sale week;
  - tax 1.2% and insurance 0.35%;
  - **no HOA** (data missing, so condo burdens are understated);
  - a 28% front-end DTI, with 36% as a sensitivity.
- It is compared with the prior renter's 3× rent income.

| | n | renter income (median) | buyer income, 28% DTI | buyer/renter ratio (28% / 36%) | buyer >2× renter | cash down |
|---|---|---|---|---|---|---|
| all years | 5,006 | $138k | $248k | **1.73× / 1.35×** | 36% | $195k |
| 2015–2017 | 234 | $87–108k | $123–168k | 1.28–1.43× | 5–12% | |
| 2022–2024 | 477 | $126–137k | $252–282k | 1.93–1.99× | 47–49% | |
| 2026 | 2,493 | $148k | $292k | 1.84× | 43% | $216k |

- **Since 2022, by county:**
  - Santa Clara 2.33× and San Mateo 2.28× are the highest. In both, 65–68% of buyers need more than 2× the prior renter's income.
  - Solano is lowest at 1.35×.
- **As a share of AMI:** the prior renter needed 0.87× AMI and the replacing buyer needs 1.68× AMI.
- The ratio follows mortgage rates: about 1.35–1.56× at the 2020–21 rates near 3%, and about 1.95× at 2022–24 rates near 6.7%.
- **Sale → rent within 12 months** (investor conversion): 5.3% of 47,695 Bay sales between 2015 and Oct-2025, rising from 2–6% before 2022 to **7.7–8.0% in 2022–24**.
  - The conversion share is highest in Santa Clara (8.6%) and Napa (8.5%).
  - The converted units' first rent covers only **0.65–0.73× of an owner's PITI** in 2022–25 (gross yield about 5%).
- **Flips** (two sales 30–365 days apart, from priceHistory): about 5% of sales.
  - Median markup per flip (resale within 12 months) is 19–29% through 2025, and **35% in 2026**. Highest in Solano (39%), Contra Costa and San Mateo (36%).
  - The `is_flipped_within_12_months` column is **not usable**. It is `true` for 75% of all properties, and only 9.5% of those have two sales within 12 months in the history (`a2_flip_flag_vs_history.csv`).

## Analysis 3: renovation / luxury text and concessions (current listing only)
**Regression sample.**
- Pairs whose *next* episode is the unit's current FOR_RENT listing, re-listed in 2025-06 or later, so the text describes the newcomer's listing.
- n = 7,752. Outcome: the annualized turnover jump in percentage points.
- Controls: ZIP fixed effects, beds, gap, log prior rent, previous year and the management flag. SEs are clustered by ZIP.

**Results.**
- **"Remodeled/renovated/new appliances" text is not associated with larger jumps:** coefficient −0.05pp (SE 0.28). Raw medians are 3.9% (flagged) vs 5.0% (not flagged).
  - In non-apartment units (n = 1,235) the coefficient is +0.42pp (SE 0.38).
  - Renovation language looks like marketing, not a measurable driver.
- **"Luxury" text** adds +0.6pp (p = 0.06), and +2.0pp (p = 0.04) among SFR/condo/townhouse units.
- **Management-company listings** add +1.1pp (p = 0.001) and +7.5pp in the probability of being over the cap.

**Concessions** (free weeks or months in the description or special_offer) appear on 27.5% of the 74,343 current Bay FOR_RENT listings. These counts are listing-weighted, so complexes with many floor plans count many times.
- Concentration:
  - 31% of management-company listings vs 5% of individual listings;
  - 39% of buildings from 2015 or later vs 13–17% of older ones;
  - 29% of APARTMENT listings vs 2% of single-family.
  - By tier, 30–31% of listings at or above the ZIP median rent vs 19% below 0.8× the ZIP median.
- The median concession is 4.3 weeks, an 8.3% first-year discount on a 12-month lease.
- **In turnover pairs with a concession** (n = 1,061), the median asking jump is +5.6%/yr but the effective first-year jump is **−0.5%/yr**. The share over the cap falls from 27% to 10%.
  - So for newcomers to new corporate buildings the headline ask overstates the first-year cost.
  - Concessions are absent from older and small-landlord stock, where low-income renters are more likely to land.
  - Caveats: the prior tenancy may also have had a concession (unobserved), and concessions burn off at renewal.

## Hand check (regex precision; `outputs/hand_check_text.csv`; 20 random distinct texts per variable, seed 42; snippets with house numbers masked)
| variable | precision | errors |
|---|---|---|
| stated income multiplier | 20/20 | — |
| remodel / renovation | 19/20 | "meticulously maintained new appliances" |
| luxury | 17/20 | "luxury vinyl plank" flooring, "luxury … ceiling fans", "the luxury of space" |
| concession weeks | 18/20 values exact (detection 20/20) | "up to" values are taken at face value; one "2 + 2 additional weeks" was parsed as 2; one took a larger second mention |

## Analysis 4: unit reclassification
Skipped. Beds and sqft are stored once per zpid, not per episode, so they cannot be compared across tenancies.

## Caveats
- **Asking rent is not the lease rent.** Revenue-managed asks move daily, and some asks are already net-effective.
- **The 3× rule is a convention, not law.** Stated multiples range from 2× to 3.5×. The California Fair Chance / Source-of-Income
  rules (SB 329) and the 2024 voucher-holder rules also limit income screens.
- **Household size = beds + 1** is a convention. Real low-income households often crowd.
- **The income-limit result depends on limit growth.** HUD limits for 2022–26 rose 13–40%, so outside SF/San Mateo, units drifted *into*
  low-income range despite rent jumps. The limits are area-wide, and actual low-income renter incomes did not necessarily rise that fast.
- **Descriptions reflect the current listing only**, so text flags are valid only for the newest episode.
- **APARTMENT zpids may be floor plans**, not units (see E2).
- Buyer income excludes HOA, PMI and other debts, and assumes 20% down. For a first-time buyer, the $195k median cash
  down is the binding constraint and is not captured by the income ratio.
- Rent → sale and sale → rent counts are scrape-weighted toward 2025–26. Yearly rates before 2022 rest on small n.
