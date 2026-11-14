# AI's distributional effect on the Bay Area

**Who captures AI-era gains, and who is exposed?**
Six linked experiments on job postings, layoff notices, worker microdata, housing, and worker voice.

Region: the 9 Bay Area counties (Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, Solano, Sonoma).

> One workstream in this repo. For synthesis across workstreams, the claims most likely to connect to other lines of work are **§4 (the two channels of capture)**, **§5 (affordability)** and the **17 null results** — the nulls constrain what any combined story can claim about displacement.

---

## The short answer

1. **The prize is real and very large.** Bay Area AI-positioned work pays a median of **$178,416** (incumbent full-time workers) against **$81,143** in exposed clerical/support/junior-professional work — a **$97,273** gap. On the posting side the gap is 1.9×–2.9× depending on how hourly pay is treated.
2. **Hiring demand is lopsided.** Relative to existing headcount, AI-positioned occupations have a demand index of **2.33** and exposed occupations **0.62** — roughly **3.8× more hiring intensity** per incumbent worker.
3. **Wages are repricing in both directions at once.** New postings advertise **1.16×–1.52×** incumbent pay in AI-positioned classes but only **0.85×–0.91×** in clerical, customer support and junior professional work.
4. **"Equity holders" and "engineers" are not the same people.** White households hold **70.7%** of Bay Area capital income while being *under*-represented in AI-positioned jobs (index 0.82). Asian workers are the mirror image: **1.99** index in AI jobs, **0.67** in capital income, and the most wage-dependent group (86.9% of personal income from wages).
5. **Black and Hispanic workers are excluded from both channels** — indices of 0.22–0.36 on each.
6. **But almost none of the "AI is destroying jobs" story shows up.** Layoffs are flat, worker displacement talk is falling, the entry rung is not thinner, pay opacity is not concentrated on exposed workers, and the measured exposure shift since 2019-23 is statistically undetectable.

The honest summary: **this is a story about an unequally distributed boom, not a measurable bust.** The distributional action is in who gets access to an extraordinarily well-paid and geographically concentrated set of jobs, and in who already owned the assets — not in observable displacement.

---

## Data built

| Source | Scale | Provenance |
|---|---|---|
| Indeed postings | 134,595 deduped CA postings; 45,850 Bay Area (36,587 unseeded) | datathon pack |
| CA EDD WARN notices | 5,392 notices, FY2023-24 → Nov 2026 | fetched (3 PDFs + live xlsx) |
| ACS PUMS persons | 189,642 Bay Area employed workers (3.97M weighted) | fetched (2019-23 5-yr + 2024 1-yr) |
| ACS PUMS households | Bay Area, tenure + property value | fetched |
| Zillow | 148,005 Bay Area property records | datathon pack |
| Glassdoor | 95,464 California reviews | datathon pack |
| Reddit | 230,520 posts; 14,914 Bay Area | datathon pack |

A 17-class occupation taxonomy was applied consistently across postings and PUMS, so the vacancy flow and the employment stock are directly comparable. `AI_POSITIONED` = AI_PRODUCER + SOFTWARE_ENG + DATA_ENG_ANALYTICS. `EXPOSED` = CLERICAL_ADMIN + CUSTOMER_SUPPORT + PROF_EXPOSED.

---

## Three data-quality traps (each would have produced a confident wrong answer)

1. **`date_posted_parsed` is the crawl date, not the posting date.** True dates must be reconstructed from relative strings ("30+ days ago"), and **55.8% are censored**. The crawl concentrates Feb–Sep 2026. **No clean 2024→2026 trend is possible from this dataset.** An apparent rise in AI-positioned share from 20.6% to 31.1% over May–Aug 2026 is pure artifact: the keyword-seeded share of those rows rises from 5% to 82%, and on unseeded rows the share *falls*.
2. **The crawl is two crawls.** 83% generic location sweep; 17% from 908 keyword-seeded searches skewed to tech/AI titles. All composition claims use the unseeded subsample. Effect is modest but real: the AI:exposed posting ratio is 2.72 full vs **2.26 unseeded**.
3. **Annualizing hourly pay at 2080h inflates low-wage, part-time-heavy classes.** Part-time share among hourly-posted runs 8% (trades) → 48% (frontline) → 93% (AI data work). This *shrinks* the apparent AI-vs-exposed gap, so the pooled 2.88× is a lower bound on true annual-earnings inequality.

---

## Positive findings

### 1. The prize, and its geography

Median posted pay (Bay): AI-positioned **$210,000** vs exposed **$72,800** = **2.88×** (CI 2.81–2.99), gap $137,200; frontline $44,720 = 4.70×. Within pay type the ratio is 1.94× (annual-posted) and 2.11× (hourly-posted), so **1.9×–2.9× is the defensible range**.

Occupation class explains **48.6%** of Bay posted-wage variance. Dropping AI-positioned postings cuts the Bay median from $125,000 to $95,000.

AI-positioned share of postings by county: Santa Clara 27.3%, SF 24.9%, San Mateo 17.5%, Alameda 7.8%, Contra Costa 2.6%, Marin 1.6%, Solano 1.5%, Sonoma 0.9%, **Napa 0.4%**. Santa Clara holds **41.4%** of Bay AI-positioned workers on 25.2% of employment; the top three counties hold 78.6%. This is a boom in three counties.

### 2. Demand index: vacancy flow vs employment stock

| group | posting share | employment share | demand index |
|---|---|---|---|
| AI_POSITIONED | 19.1% | 8.2% | **2.33** |
| EXPOSED | 8.4% | 13.7% | **0.62** |

Per class: clerical 0.54, prof-exposed 0.53, education 0.35, frontline 0.61, skilled trade 0.51; management 1.01, customer support 1.02.

*Do not* use the per-class AI_PRODUCER index (15.4) — it is a definitional artifact. ACS codes working ML engineers as software developers (OCCP 1021) while title rules capture any ML/AI title. The **pooled** index is robust because it pools across that boundary on both sides.

### 3. Entry wage ratio: new postings vs incumbent pay

Posted median ÷ incumbent full-time median, same class:

| class | incumbent | posted | ratio |
|---|---|---|---|
| DATA_ENG_ANALYTICS | 118,714 | 180,000 | **1.52** |
| PRODUCT_DESIGN | 127,440 | 189,850 | 1.49 |
| AI_PRODUCER | 162,796 | 219,687 | 1.35 |
| SOFTWARE_ENG | 180,445 | 210,000 | 1.16 |
| HEALTH_CLINICAL | 86,825 | 100,000 | 1.15 |
| MANAGEMENT | 150,964 | 167,100 | 1.11 |
| FRONTLINE_SERVICE | 48,308 | 44,439 | 0.92 |
| PROF_EXPOSED | 108,531 | 99,018 | **0.91** |
| CUSTOMER_SUPPORT | 62,948 | 56,160 | **0.89** |
| CLERICAL_ADMIN | 66,204 | 56,488 | **0.85** |
| EDUCATION | 81,561 | 66,560 | 0.82 |

**The bias direction strengthens the exposed finding.** PUMS is 2023-adjusted dollars, postings 2026 nominal, so every ratio is an *upper* bound: the sub-1.0 ratios are worse in real terms, and part of the AI premium is just three years of inflation.

### 4. The two channels of capture (the central result)

| group | employment | AI-job index | capital-income index | capital÷labor |
|---|---|---|---|---|
| White | 36.5% | **0.82** | **1.94** | 2.36 |
| Asian | 29.3% | **1.99** | **0.67** | 0.34 |
| Hispanic | 23.6% | 0.24 | 0.22 | 0.93 |
| Black | 5.1% | 0.36 | 0.24 | 0.66 |

White adults are 36.5% of workers and receive **70.7%** of net interest, dividend and rental income (SE 0.56). Among adults earning $100k+, 37.4% of White adults have positive capital income vs 17.2% of Black and 20.3% of Hispanic adults — so this is not merely an income effect.

Homeownership: White 63.0%, Asian 61.5%, Hispanic 41.3%, Black 36.3%. Black households are 5.9% of households and hold **2.6%** of the $1.90T in owner-occupied value.

**Load-bearing caveat:** ACS `INTP` excludes capital gains, RSUs, options and retirement balances — precisely how Bay Area engineers are paid equity. If RSU income were observable the two channels would converge to an unknown degree. The divergence above is an **upper bound** on how separate they are.

### 5. Affordability: the wedge that does the real work

The median posted salary affords median local rent at the 30% threshold in:
- **0 of 25** cities for clerical
- **0 of 22** for customer support
- **0 of 66** for frontline
- **16 of 23** for AI-producer roles (23 of 23 on asking rent)

Required salary at the 30% line: $167,880 (rentZestimate) or $124,320 (asking rent). The shortfall for non-AI classes is $63k–$123k, or **1.9×–4.0×** their pay.

### 6. Who holds the high-paying demand (incidence accounting)

High-pay (≥$150k) AI-positioned demand, by the incumbent racial composition of those occupations: **53.9% Asian, 33.2% White, 6.1% Hispanic, 1.9% Black** — 1.8× the Asian share of all employed workers, 0.37× the Black share, 0.26× the Hispanic share. Restricting to incumbents already earning ≥$150k pushes Black and Hispanic shares lower still (1.1%, 3.9%).

Santa Clara high-pay AI demand is **68.1% Asian**; SF is 46.8% White / 38.3% Asian. Solano's exposed base is **15.2% Black** against 5.1% Bay-wide.

*This is arithmetic on two marginal distributions — vacancy flow against employment stock — not a forecast, and it says nothing about who is actually hired.*

### 7. Wage gaps are worse inside the winning sector

The Black-White wage gap is **−30%** (adjusted) inside AI_PRODUCER/SOFTWARE_ENG but only **−9%** inside exposed classes. Difference in log gaps −0.264 (SE 0.066, z=−4.0). Black n=202 in AI classes — solid but modest. Asian workers show the reverse (−5% in AI vs −12% in exposed, z=4.2).

**Access to the sector is not access to its pay.**

### 8. Firms hire AI roles while cutting staff

WARN-filing Bay Area firms post **+14.0 points** more AI-positioned roles than non-filers (31.1% vs 17.1%, bootstrap CI +4.3 to +20.7), and fewer exposed (−3.5) and frontline (−7.9) roles. Among firms with 30+ postings the gap narrows to ~11 points on 35 firms, so firm size confounds it. Company-name join matches only 14.1% of postings — descriptive only, not within-firm substitution.

### 9. Job enlargement, weakly

Exposed-class Glassdoor reviews mention understaffing at 1.30% vs 0.46% for AI-positioned, and workload at 3.80% vs 1.66% — both surviving company fixed effects (+0.30pp, p=0.033; +1.27pp, p=3e-6). Among reviews mentioning layoffs, 5.6% of exposed also mention workload vs 1.5%. **But AI is named as the cause in only 0.14% of exposed reviews (22 reviews).** The enlargement is real; the AI attribution is not established.

### 10. Entry-level job search friction

Entry-level-context Reddit posts carry **2.4×** the application-volume discourse (11.7% vs 4.9%) and 1.7× any friction (21.6% vs 12.7%). Median stated application count: **200**. Of all AI-and-work discourse, **61.6% is about AI in hiring and job search** rather than job loss.

---

## Negative and null findings

These matter as much as the positives, and several kill plausible hypotheses outright.

### N1. Layoffs show no trend at all
Over 13 quarters, Bay Area WARN employees per 10k workers have a slope of **−0.17 per quarter (p=0.66)**. The Bay share of California layoffs is flat (p=0.78). Notice counts drift *down* (p=0.08). The Bay runs 1.87× California's layoff intensity (243.5 vs 130.0 per 10k) — but it did before generative AI too. The FY2026-27 uptick is two non-tech notices (AEG Oakland 1,605; Covenant Aviation Security 1,279); excluding all 1,000+ notices, the Bay share is *not* elevated.

Parse validated exactly against EDD's own monthly summary pages across all 39 month-lines.

### N2. No call-center relocation signal whatsoever
The official call-center relocation sheet contains **one** record for 2023–2026: a Los Angeles insurer, 163 employees, March 2023 — before the window, outside the Bay Area. Name-matching finds only three other customer-service-center layoffs statewide. The cleanest available read on offshoring/automation of customer support is **empty**.

### N3. The entry rung is not thinner in exposed occupations
**23.9%** of exposed postings are entry-level (clerical **36.3%**) versus **4.2%** in AI-positioned and 18.4% in frontline. Exposed work is 8.3% of postings but **16.3% of all entry-level postings**. The "AI removes the bottom rung" story does not appear in this cross-section.

### N4. Pay opacity is not an exposed-occupation phenomenon
Raw no-pay rates are higher for exposed classes (19.9% vs 12.7% frontline), but after adjustment clerical (OR 1.10, CI 0.84–1.55) and prof-exposed (0.96) are indistinguishable from management, and **customer support is less opaque** (0.73). Opacity tracks posting *format and employer*: description length (OR 0.35 per log unit), remote (1.74×), no company rating (1.64×). Omission is 28.5% at unprofiled employers vs 8.2% at firms with 2,000+ reviews. Worst offenders are large and specific: AMD 99.5%, Costco 97%, UCSF 89%.

### N5. "AI as hiring gatekeeper" largely evaporated under validation
Hand-checking gave 65% posting-weighted precision; false positives are *candidate-side* rules ("do not use AI in interviews"). Corrected Bay rate 3.4% → **2.2%**, and **NVIDIA alone is 68% of matches** — excluding it, 0.7%. By class: AI-positioned 4.7%, exposed 0.6%, clerical 0.1%. This measured one firm's disclosure boilerplate, not screening practice.

### N6. The AI-use wage premium in exposed roles is a firm effect
Between firms, exposed postings mentioning AI use pay +0.126 log points. **Within firm: +0.029 (SE 0.037) — zero.** Exposed roles mentioning AI are at higher-paying employers, not better paid by the same employer. (A within-firm zero cannot distinguish "asked to use AI unpaid" from no effect.)

### N7. Worker displacement discourse is falling, and names the wrong occupations
AI-and-work share of general work-subreddit posts: 4.2% → 4.3% → 4.3% → **3.4%**; subreddit-FE logit trend **−1.3% odds/month (p=0.037)**. Only 2.2% (20 posts) of that discourse is actual displacement.

Among 67 displacement/fear posts with identifiable occupation: **software engineering 39%** (26), junior professional/creative 27% (18), clerical **2**, customer support **0**, frontline 2, trades 7 *as a refuge*. The workers who talk about AI threatening their jobs are disproportionately the supposed winners. (Reddit skews tech-employed; only 4 of 67 are strict displacement reports.)

**There is no Bay Area worker-voice signal at all**: 26 of 14,914 Bay posts (0.17%), and not one first-person displacement report.

### N8. Glassdoor ratings are not diverging
AI-positioned classes out-rate exposed ones raw (compensation d=0.25, career d=0.20, p<1e-40), but with company fixed effects the **compensation gap vanishes** (+0.04, p=0.15) and career shrinks to 0.08. The differential time slope is insignificant (career p=0.62, compensation p=0.15), and the gap actually *narrowed* across half-years (0.27 → 0.39 → 0.16 → 0.22).

### N9. Layoff-filing firms are not rated worse
Among 134 Bay WARN firms with 10+ reviews vs 1,229 non-filers: overall rating +0.031 raw, **−0.012 adjusted** — a null. Only senior leadership is lower (−0.12, robust across size bands and samples). WARN firms score *higher* on compensation (+0.22) and work-life (+0.18), almost certainly composition.

### N10. AI job density does not predict housing costs once county is controlled
Raw correlation of city AI job share with log home value is 0.58. With county fixed effects, **four of six specifications are insignificant** (p=0.10 value, 0.055 rentZestimate, 0.21 asking rent). Within-county appreciation is unrelated to AI share (+0.004 per 10 points, **p=0.64**), and over 2017–22 the relationship was *negative* (−0.025, p=0.002). The apparent "AI cities are expensive" effect is **between-county** (SF +37%, San Mateo +28%, Santa Clara +21% vs Contra Costa +8%, Solano +7%). Silicon Valley was expensive first.

### N11. Capital does not outweigh labor in aggregate
Bay Area capital income is **$35bn against $423bn in wages** — 6.6% of personal income. Estimated housing appreciation is 14–23% of the annual wage bill and below it for every racial group. The finding is about *who holds the slice*, not capital swamping wages. This materially tempers the "equity holders capture the gains" framing.

### N12. Exposed workers are not in contract arrangements
Exposed workers are **less** often self-employed (6.6%) than the Bay average (10.1%) or frontline workers (12.0%). Exposed Black (3.8%) and Hispanic (4.0%) workers are less often self-employed than exposed White workers (10.0%). The "contract roles" exposure channel does not appear. (COW self-employment is an upper-bound proxy for contract work.)

### N13. Hispanic workers are under-exposed, not over-exposed
Index **0.87** (SE 0.01) — below parity. Their risk is *absence* from AI-positioned work (index 0.24), not task automation. They concentrate in frontline service (1.68), which this taxonomy treats as insulated.

### N14. Nothing has measurably moved yet
2024 vs 2019-23: exposed shares did not change detectably for Black (z=−1.5), Hispanic (z=0.5), White (z=−1.4) or multiracial workers. The only clear decline is Asian (−1.1pp, z=−3.1). The Bay AI-positioned share rose 1.1pp (z=6.7). The two files differ in design (5-year centered on 2021 vs single-year 2024), so AI-era hiring cannot be separated from baseline drift.

### N15. The shift-share effect is second-order
Black-White and Latino-White per-capita gaps widen in **all 18** counterfactual scenarios — but by only **0.2–1.3 percentage points** against baseline gaps of **44** and **54** points. Even aggressive assumptions (20% exposed-employment loss, 20% AI wage gain) move the racial wage gap by a few percent of its existing size.

### N16. Gender is a sharper exposure axis than race
Women are **67.6%** of exposed workers against 46.0% of all workers, and among women the exposed share is within ~3 points across all four large racial groups. Exposed workers are mid-wage and **55.5% college-educated** — not the bottom of the distribution.

### N17. Modeling nulls
- Reallocating the 19.9% `OTHER` bucket with a text classifier leaves the AI:exposed posting ratio **unchanged** (2.26 → 2.28). The headline does not depend on taxonomy residual.
- Imputing pay for the 15% of postings that omit it changes **no class median by more than 4.7%**, and leaves the class ranking essentially unchanged.
- Salary-model bias runs **opposite** to the fairness concern: it under-predicts AI-positioned pay (−4.8%) and is near-neutral for exposed (−1.1%) and frontline (−0.9%). The model compresses toward the mean (lowest actual-pay quintile +10.4%, top quintile −16.4%).

---

## Models (Advanced-Track requirements)

All held-out evaluation is **company-grouped** — no employer appears in both train and test.

| Model | Baseline | Result |
|---|---|---|
| **M1 occupation from text** | majority 0.022 macro-F1 | **description-only 0.767**; title-only 0.970 is *circular* (labels derive from titles) |
| | | naive random-row split gives 0.861 → **9.4 points of leakage**; 80.7% of random-split rows share an employer with train |
| **M2 log posted salary** | global median 0.645 log / $80,010 | occ-median 0.460; OLS 0.344; ridge-text 0.261; **text stack 0.237 log / $37,019, R²=0.86** |
| | | −49% RMSE vs occupation median; 80% prediction intervals cover 79.8% |
| **M3 no-posted-pay** | majority AUC 0.50 | structured 0.71; **text 0.83** (masking pay words → 0.79) |

Hand validation (single unblinded rater): on 110 random `OTHER` postings the classifier was 54.5% clearly correct / 75.5% defensible; restricting to non-MANAGEMENT predictions with p≥0.60 gave **80.0% clearly correct and 0 wrong** on a fresh disjoint sample of 45. MANAGEMENT predictions were correct 1 of 19 times and are never used.

**Classes that are unreliable from text:** AI_DATA_WORK (F1 0.00), CUSTOMER_SUPPORT (0.74, recall 0.67), PROF_EXPOSED (0.75, recall 0.69), CLERICAL_ADMIN (0.83) — i.e. precisely the classes the study cares about. **AI_PRODUCER vs SOFTWARE_ENG is a coin flip; always use their sum.**

**The hand-audit found real errors in my own regex taxonomy**: "chief/lead/controller" → MANAGEMENT (Traffic Controller, Survey Party Chief); "nursery/nursing" → HEALTH (Nursery Retail Sales Associate); AI_PRODUCER over-broad (AI marketing specialist, PK/PD research scientist, laser postdoc). On 52 confident disagreements: model right 23, regex right 8, both defensible 19, neither 2. These shift mass between MANAGEMENT and operational classes and *within* the AI-positioned group — not between AI-positioned and exposed, so headline conclusions survive.

---

## The AI data-work layer: a measurement trap worth documenting

`AI_DATA_WORK` is **one employer**: DataAnnotation is 125 of 143 salaried Bay postings (419 of 447 statewide). 91 of the 125 carry the *identical* "$50 – $100 an hour" range. All 125 are contract and part-time; 85% remote.

The annualized **$156,000** median is an artifact — these are piecework postings with no guaranteed hours. The one posting in the class that quoted an annual figure offered **$20,800–$41,600**.

The platform recruits by the applicant's *former* occupation ("Remote Accountant – AI Trainer", "Bookkeeper – AI Trainer", "Proofreader – AI Trainer"). I initially flagged this as a "training your own replacement" pattern; **parsing all 417 such titles shows it is weaker than that** — only ~20% are exposed-type occupations, while **46% are AI-positioned-type** (engineers, scientists, quants). The solicited occupations skew technical. The pattern is real for about a fifth of titles.

---

## What this evidence cannot establish

- **No causal identification anywhere.** Every result is cross-sectional association or accounting arithmetic. The posting data cannot support a time trend at all.
- **WARN has no occupations.** It cannot speak to occupational exposure, and it covers only 75+ employee mass events — missing contractor non-renewals, attrition and hiring freezes, which is exactly how AI-driven support/clerical reduction would appear.
- **Postings are vacancy flow; PUMS is employment stock** (2019-23). Linking them is an accounting exercise.
- **Incumbent racial composition ≠ hiring composition.** Nothing here measures discrimination or hiring barriers.
- **Reddit and Glassdoor are self-selected** and have no race variable. They corroborate mechanism, never incidence.
- **"Asian" is a single ACS aggregate**, hiding large within-group dispersion — a real limitation given this group's centrality to the findings.
- **The equity channel is measured without equity.** `INTP` excludes capital gains, RSUs and options.

---

## Files

- `memos/` — the six experiment memos plus integrative notes (`synth_notes.md`)
- `results/` — 33 tidy result tables (every number in this document traces to one)
- `code/` — 71 scripts, raw data → reported results

**Data is deliberately not in this repo.** The linked analysis datasets (`indeed_base_v3.parquet`, 17 MB; `pums_bay.parquet`, 23 MB; `warn_ca.csv`, the parsed layoff panel) live outside it. `code/build_indeed_v2.py`, `code/pums_build.py` and `code/warn_parse.py` rebuild them from the original sources.

Datathon-pack sources used: Indeed postings, Zillow, Glassdoor, Reddit. External sources fetched: CA EDD WARN (FY2023-24 → FY2026-27), ACS PUMS 2019-2023 5-Year and 2024 1-Year California person + household files, Census tract→PUMA and place→county crosswalks.
