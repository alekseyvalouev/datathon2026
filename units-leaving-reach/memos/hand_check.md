# Hand check: labels and joins

`code/s02_hand_check.py` draws 30 pairs (seed 42; 15 labelled "left reach", 15 "stayed in reach"). For each one it:

- re-reads the raw Zillow rental events from `analysis/cache/zillow.duckdb`;
- re-derives the previous rent, the first ask and the settled ask by a separate code path;
- looks up the HCD 80% AMI limit again;
- recomputes the label;
- checks that the tract's county code matches the listing county.

The raw histories it prints (`results/s02_hand_check_raw.txt`) were read by hand.

## Machine checks (30/30)
| Check | Pass |
|---|---|
| Previous rent (`last_p`) matches the raw events | 30/30 |
| First ask at re-listing matches | 30/30 |
| Settled ask (last ask of the re-listing episode) matches | 30/30 |
| Label recomputed from the raw numbers and limit table | 30/30 |
| Tract county = listing county | 30/30; 99.97% across all 11,878 joined pairs |

## Decision made because of the hand check
The first draw used the **first ask** as the label. Reading its 15 positive histories, 3 were first asks that crossed the line and were then cut back below it within weeks. Examples: $3,195 → $2,795 against a $3,126 line, and $3,300 → $2,550 against $3,021. The label was therefore changed to the **settled ask**: the last ask of the re-listing episode, which is the closest the data gets to the rent the unit let at.

Across the population, 347 first-ask positives become negatives and 155 go the other way. The first-ask label is kept as robustness check R1; the model's gain over the rule is the same (+0.045 vs +0.051).

## Verdicts on the final 30 (settled-ask label)
| Verdict | n | Notes |
|---|---|---|
| Correct | 22 | All 15 negatives. Positives include SF 1-bed $2,395 (Dec 2020 COVID low) → $3,495; Santa Clara house $3,995 → $5,550; San Mateo 2-bed $4,000 → $5,000 |
| Correct with caveat | 5 | Two positives sit within 2% of the line on daily algorithmic repricing (Alameda $3,467 vs $3,394 line). Two baselines are COVID-era lows. One pair has an orphan "Listing removed" event that stretches the previous tenancy (known movement E2 issue; it does not affect the label) |
| Questionable | 3 | All positives with very large jumps that look like a different unit or floor plan reusing the zpid: SF 1-bed $3,334 → $4,859 in 13 months; SF 2-bed $3,987 → $6,946; Alameda 1-bed $2,087 → $3,104 |

**Implication:** label precision on positives is at least 12/15 on this draw, and the errors come from implausibly large jumps. Robustness check R1 drops all pairs with jumps above 30%/yr (128 test pairs). Test AUC rises to 0.907 and the gain over the rule stays at +0.039 [0.035, 0.044].

## Join checks
- **Tract join:** point-in-polygon on 2018 TIGER tracts (done in movement E2). Matches 98.9% of pairs to a tract with displacement-workstream features; 76 test pairs are unmatched and reported as their own subgroup.
- **City join** to ai-labor-distribution's city job table: on lower-cased city name, for cities with 30+ postings. 96.4% of pairs matched.
- **Income limits:** CA HCD State Income Limits 2022-2026, parsed and validated in movement E6 (`s01_income_limits.py` checks that 27 county × level rows exist per year and rise with household size). Household size = bedrooms + 1, studio = 1.
