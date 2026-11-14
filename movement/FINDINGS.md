# Movement: follow the people, not the place

**Question.** When households leave the Bay Area, what happens to them, to the homes they leave, and to the people who replace them, and what do regional averages hide?

**Thesis.** When a household leaves, two things happen that a regional average can't show:
- Its home is re-priced for a smaller, better-paid household, often one that employers pay to bring in.
- The household that leaves, especially one moving to the Central Valley, trades rent for a heavier rent burden, long commutes and lower pay.

In county averages, leavers and arrivals largely cancel out, so both stories disappear. The predictive models we built are weakest on the most vulnerable groups.

Findings page: `site/follow-the-people.html`, published at https://claude.ai/artifact/JraxL9nN6yHcT9kYw15wof (private; share access from the page). Each experiment folder under `analysis/` has its own README with methods, hand checks and caveats.

---

## Headline claims (with the limit stated beside each)

### 1. Averages hide two moves that cancel (E1, E5)
- From 2011 to 2021, average income per tax return in the 9-county region rose from $100.8k to $213.0k.
  - Removing lower-income leavers contributed **+$6.6k**.
  - Adding arrivals contributed **−$15.5k**.
  - Net from migration: **−8%** of the rise. San Francisco: −24%. Santa Clara: −11%.
- Removing leavers raised the average in 8 of 9 counties. The exception is SF, whose 2019–21 leavers earned more than its stayers.
- Arrivals look poorer per return ($144k vs $210k for leavers, region, 2021) mainly because they file smaller returns. People per return: arrivals 1.46, leavers 1.70, stayers 1.93.
  - Per person, arrivals' income is 80% of leavers' rather than 69%.
  - Statewide, 62% of arrivals file before age 35, vs 31% of non-movers. Arrivals' incomes grow faster after the move.
- *Limits:*
  - Tax returns are not households, and the dollars are nominal averages pulled up by top earners.
  - The age breakdown exists only for California as a whole.
  - The 2022–23 files use a new IRS method and are excluded from the main results.
- **Null / reversal:** the simple story that exits inflate the averages is false in the job-centre counties. Arrivals outweigh it.

### 2. A turnover re-prices the home (E2, E6)
- 23,306 pairs of consecutive listings on the same unit, 1–6 years apart.
  - Median rent jump at turnover: about 4%/yr overall and **6.5%/yr in 2026**.
  - **23%** of 2026 turnovers exceed the 10%/yr AB 1482 maximum. San Francisco: 17%/yr.
- About **83%** of the premium survives after subtracting move-in deals ("weeks free"). Where a deal exists, the effective first-year jump is near zero.
- Income needed to qualify (3× rent) against 80% of area median income:
  - **San Francisco:** 20.7% of turnovers went out of low-income reach, 0.7% came into reach. In 2026: 28.7% out of reach.
  - **Region-wide:** 6.4% lost vs 6.4% gained, a net of zero. The limits rise with area incomes, which migration itself moves.
- A buyer of a former rental needs 1.7× the last renter's income, plus a $195k down payment.
- *Limits:*
  - These are asking rents, not signed leases.
  - Some apartment listings stand for a floor plan rather than one unit.
  - The 3×-rent rule is a convention.
  - Zillow's `is_flipped_within_12_months` flag is unusable: it is true for 75% of properties.

### 3. Employers recruit the replacements (E7)
- Relocation help appears on **8.4% of Bay postings paying $60+/h** vs **0.1% under $25/h**: 1,720 of 20,449 postings vs 7 of 7,291.
- The gap holds for firm offers only (2.4% vs 0.05%) and with each employer weighted equally (4.8% vs 0.16%). Apple posted 928 of the Bay's 2,144 offers.
- **Null:** the Bay is not more generous than the rest of California within a pay tier.
- Reddit arrival stories cite jobs as the reason 24% of the time, vs 10% for leavers. They cite housing cost 0% of the time, vs 12% for leavers.
  - *Limit:* these labels were made by a language model. `e7_pulled_in/labels/verify_sample.csv` needs a human check.

### 4. Leavers trade rent for burden, distance and lower pay (E3, E9, E10)
- ACS PUMS 2022–24 compares leavers with stayers who match them on characteristics fixed before the move. Central Valley leavers vs matched stayers:
  - Homeownership: **+5.4 pts**
  - Paying ≥50% of income in rent: **+16.0 pts**
  - Commuting 60+ minutes: **+9.3 pts**
  - Wages: **−$26.2k**
- Leavers without a bachelor's degree: +14.7 pts below 200% of the poverty line.
- *Limits:*
  - Outcomes are measured after the move, so these are comparisons, not causal estimates.
  - The window is one year, and only 212 Black leavers are in the sample, too few to report.
- **Reversal vs. the California Policy Lab:** out-of-state leavers are *less* likely to own a home (−3.5 pts). CPL finds +4 pts after 1 year. The likely difference is the one-year window, but this is unresolved.
- Census LODES commute data:
  - Workers living outside the 9 counties hold 18.5% of Bay jobs, up from 14.8% in 2010.
  - San Joaquin residents hold 41,799 Alameda jobs, up from 25,088 in 2010.
  - Much of the growth after 2019 comes from LA and San Diego residents, which is likely remote work or headquarters reporting, not commuting.
- Monthly budget, full-time pay minus 1-bedroom rent:
  - Re-renting in the Bay is the worst option for every one of 10 low-wage jobs.
  - Caregiver: −$197/mo after re-renting in the Bay. Living in Stockton and keeping the Bay job: +$596 counting fuel only, −$1,108 at the IRS full car cost.
  - At full car cost, keeping a Bay job from an inland city leaves less than nothing in **35 of 40** job × city cases.

### 5. Staying in the Bay costs less access than leaving (E8)
- Units a low-income household can still rent outside the high-cost areas are **1.8× farther from a clinic**. 86% are within 400 m of a bus stop, vs 97% in the high-cost areas.
- **Null:** within each county, the affordable units are *not* the isolated ones.
  - Comparing similar buildings in the same county, those with a unit an extremely low-income household (≤50% of area median income) can afford are less likely to be service deserts (odds ratio 0.43).
  - Service deserts are mostly pricier rentals at the suburban edge.
- *Limits:* the Google Maps places data is incomplete, and distances are straight lines.

### 6. The models miss the most vulnerable (E2, E8, E9)
| Model | Test result | Where it fails |
|---|---|---|
| Rent jump at turnover (E2) | Ridge with a recent-trend feature, MAE 0.046 vs 0.059 for the ZIP-median baseline; AUC 0.83 | Under-predicts most in gentrifying tracts (−2.2 to −3.7 pts). Loses to the legal-cap rule when SF is held out. |
| Who leaves (E9) | Gradient boosting, AUC 0.71 | Catches 41% of White leavers vs 25–28% of Asian, Black and Latino leavers in the top 10% of scores. |
| Service desert (E8) | AUC 0.92 vs 0.83 for the distance rule | Finds 31% of deserts among the cheapest units vs 69% among the priciest. |
| Reddit exit stories (E4) | Macro-F1 0.53 vs 0.44 for the keyword rule | Too few positives; classifying "considering leaving" barely works. |

- Reddit exit stories are 91% moves out of state. Among CPL's low-income leavers, only 48% leave the state.
  - *Limit:* Reddit users are not a sample of low-income movers, and the labels need a human check (`e4_exit_classifier/labels/verify_sample.csv`).

---

## Nulls and negative results (do not drop these when synthesizing)
- Migration lowered region-wide average income over 2011–21 rather than inflating it (E1).
- Region-wide, turnovers move as many units into low-income reach as out of it. The net loss is concentrated in SF and San Mateo (E6).
- The Bay is not more generous with relocation help than the rest of California at the same pay (E7).
- Within each county, affordable units are not more isolated from services (E8).
- Out-of-state leavers lose homeownership in the first year, which is the opposite of CPL's direction (E9).
- LightGBM is no better than Ridge for the rent-jump model, and re-tuning on recent data did not fix the 2026 level shift (E2).
- The Reddit classifier is weak, and online exit stories mostly miss the Central Valley moves of low-income households (E4).

## Data-quality notes for other workstreams
- No public dataset follows the same person over time. These results approximate it with flows (IRS, LODES), one-year migration questions (ACS PUMS) and same-unit histories (Zillow).
- The Zillow price histories are heavily weighted toward 2025–26 because of when the data was collected.
- The Indeed extract has unreliable posting dates (see `ai-labor-distribution/FINDINGS.md`). E3 and E7 use it only cross-sectionally.

## Experiments
| # | Folder | Question |
|---|---|---|
| E1 | `analysis/e1_composition` | How much do moves change county average income? |
| E2 | `analysis/e2_turnover_model` | How much does rent jump when the same unit turns over? (main Advanced Track model, plus robustness checks) |
| E3 | `analysis/e3_mover_ledger` | What does a low-wage worker keep after rent in each scenario? Includes a salary model. |
| E4 | `analysis/e4_exit_classifier` | What do Reddit exit stories say? |
| E5 | `analysis/e5_replacers_irs` | Who replaces the leavers? |
| E6 | `analysis/e6_unit_replacement` | Does turnover price units out of low-income reach? |
| E7 | `analysis/e7_pulled_in` | Who do employers recruit in? |
| E8 | `analysis/e8_access` | Where can low-income households still rent, and what services are nearby? |
| E9 | `analysis/e9_pums_movers` | How do leavers fare compared with similar stayers? |
| E10 | `analysis/e10_supercommute` | Do leavers keep their Bay jobs, and what does the commute cost? |
