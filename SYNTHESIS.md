# Synthesis: the boom moves people out through rents, out of sight

**Thesis.** The Bay Area is not losing people through a visible AI bust. It is losing them through an unequally shared boom that reaches lower-income households through housing prices. Regional averages, the standard displacement typology and our own models are all weakest exactly where those households are.

Every number below is taken from a workstream’s `FINDINGS.md`, where it appears with its source table, method and caveat. Tags name the workstream: **[AI]** `ai-labor-distribution`, **[MOV]** `movement`, **[DEW]** `displacement-early-warning`, **[WSWD]** `who-speaks-who-decides`, **[ULR]** `units-leaving-reach`.

## Act 1. The engine is an unequal boom, not a bust [AI]
- AI-positioned work pays a median **$178k** against **$81k** in AI-exposed clerical, support and junior professional work. Relative to current headcount, AI-positioned occupations hire **3.8×** as intensely.
- **Repricing runs both ways.** New postings offer 1.16–1.52× incumbent pay in AI classes and 0.85–0.91× in exposed ones.
- **Two channels of capture.** White households hold **70.7%** of capital income but are under-represented in AI jobs (index 0.82). Asian workers are the mirror image: AI-job index 1.99, capital-income index 0.67, and the most wage-dependent group. Black and Hispanic workers sit at 0.22–0.36 in both.
- **No measurable bust.** Layoff notices have no trend over 13 quarters (p = 0.66), the entry-level rung is not thinner in exposed jobs, and worker AI-displacement talk is falling. These are among 17 documented nulls.
- **The link to housing.** The median posted salary covers median rent at 30% of income in **0 of 25** cities for clerical work, 0 of 22 for customer support and 0 of 66 for frontline service, against **16 of 23** for AI-producer roles.

## Act 2. The pressure travels through turnover [MOV, DEW]
- **Rent at turnover.** Across 23,306 same-unit turnover pairs, **23%** of 2026 turnovers rose faster than AB 1482’s 10%/yr cap. The cap covers sitting tenants, not vacant units. About 83% of that premium survives move-in concessions.
- **San Francisco loses affordable units at turnover.** 20.7% of turnovers moved a unit out of reach of an 80%-of-median household and 0.7% moved one in. Region-wide the two net to zero.
- **Employers recruit the replacements.** Relocation help appears on 8.4% of postings paying $60+/hr and on 0.1% of those under $25/hr. Arrivals are younger, smaller households (1.46 people per tax return vs 1.70 for leavers).

## Act 3. The pressure lands where the standard map doesn’t look [DEW]
- **Loss was predictable.** Year-2000 census data predicts which tracts lost low-income households by 2018 at AUC 0.78. The UDP vulnerability flag scores 0.52.
- **After 2018 the pressure split.** Flipping stayed in lower-income tracts while price and rent growth moved to affluent ones. The UDP flag ranks those two backwards (AUC 0.38).
- **Rents are already out of reach** where incomes are lowest: median asking rent is 51–62% of tract income in low-income typologies.

## Act 4. What happens to the people who leave [MOV]
- **Central Valley leavers vs matched stayers:** +5.4 points homeownership, but +16.0 points paying half their income in rent, +9.3 points commuting an hour or more, and −$26.2k in wages.
- **Commuting back doesn’t pay.** At full car cost, keeping a Bay job from an inland city leaves a negative budget in 35 of 40 job × city cases.
- **Access shrinks.** Units still affordable outside high-cost areas are 1.8× farther from a clinic.

## Act 5. Why it stays invisible [MOV, WSWD]
- **Averages cancel.** Net migration accounts for −8% of the region’s 2011–21 rise in income per tax return (San Francisco −24%): lower-income leavers raise the average, younger arrivals lower it.
- **The bottleneck is not the hearing room.** The San Francisco Planning Commission approved 90% of 1,803 contested projects and followed staff 97% of the time. Opposition buys delay and split votes, not denials.

## The pattern: our models fail the people they’re meant to protect
| Model | Where it fails |
|---|---|
| Tract displacement backtest [DEW] | Recall 0.72 in renter-majority tracts vs 0.21 in owner-majority; 0 of 7 losses caught in Solano |
| Flipping forecast [DEW] | AUC 0.68 in low-income typologies vs 0.83 in moderate ones |
| Who leaves [MOV E9] | Top-10% flag catches 41% of White leavers vs 25–28% of Asian, Black and Latino leavers |
| Service deserts [MOV E8] | Finds 31% of deserts among the cheapest units vs 69% among the priciest |
| Comment stance [WSWD] | 0.40 accuracy on tenant-association speakers |
| Units leaving reach [ULR] | At a 20% budget, catches 0.62 of losses in low-income tracts vs 0.79 in exclusive ones |

## The model that joins them [ULR]
- **Question.** When a rental a household at 80% of area median income could still afford is re-listed, will the next settled asking rent put it out of reach? 12,010 units, 18.9% leave reach.
- **Features from three workstreams:**
  - the unit and its market [MOV];
  - its tract, including the backtest risk score [DEW];
  - its city’s job mix [AI].
- **Result.** On 2026 re-listings scored once, the model reaches AUC **0.900**, against **0.848** for a rule built on the AB 1482 cap and **0.456** for the UDP typology. At the same 20% budget it catches 913 of 1,402 losses vs 818.
- **Nulls.** The cross-workstream features add only +0.004 AUC. Probabilities under-predict 2026. Two outer counties prefer the simple rule.
- **Projection.** Run forward under stated assumptions, 1,964 tracked units out of reach by 2026 become 2,428–2,882 by 2031, depending on whether rents freeze or keep their 2026 pace (`units-leaving-reach/site/out-of-reach-atlas.html`).

## Nulls that constrain this story
- No measurable AI job loss [AI].
- Within a county, AI job density does not predict home prices (p = 0.64) [AI].
- Capital income is only 6.6% of personal income [AI].
- Zillow price history adds almost nothing as a feature [DEW, ULR].
- Region-wide, as many units move into low-income reach at turnover as out of it [MOV].
- Remote hearings did not change who comments [WSWD].

## Tensions not yet reconciled
- [DEW] E8 finds large re-listing jumps equally common in high- and low-income typologies (17.7% vs 17.6%). [MOV] E2 finds its rent model under-predicts in gentrifying tracts.
- [MOV] E9 finds out-of-state leavers *less* likely to own a home (−3.5 points), the opposite of the California Policy Lab’s direction. The one-year window is the likely reason.
- [MOV] E4 and E7 labels were made by a language model and still need the human checks listed in the README.
