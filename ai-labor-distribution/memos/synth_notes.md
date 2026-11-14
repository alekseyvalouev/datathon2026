# Synthesis notes (owner: lead) — integrative tests not owned by any single experiment

## Base table provenance
- `base/indeed_base_v3.parquet` — 134,595 deduped CA postings (140,816 raw), 45,850 Bay Area.
  Adds to v2: `keyword_search`, `seeded`.
- Occupation taxonomy: ordered regex on job_title. Bay OTHER = 19.2% after v2 refinement (was 26%).

## CRITICAL DATA-QUALITY FINDINGS (apply to all posting-side results)
1. **`date_posted_parsed` is the CRAWL date, not the posting date.** True posting date reconstructed as
   crawl - N days from the relative `date_posted` string. 55.8% of rows are censored at "30+ days ago".
   Crawl concentrated Feb-Sep 2026. => NO clean 2024->2026 trend is possible from this dataset.
2. **The crawl is two crawls.** 82.6% from a generic location-only crawl; 17.4% from 908 keyword-seeded
   searches skewed to tech/AI titles. Occupation SHARES must use `seeded == False` (Bay n=36,587).
   Effect is modest: AI_POSITIONED/EXPOSED posting ratio 2.72 (full) -> 2.26 (unseeded).
3. **Annualizing hourly pay at 2080h overstates low-wage and part-time classes.** Bay salaried postings
   split 23,266 annual-posted / 14,968 hourly-posted. Part-time share among hourly-posted: 8% SKILLED_TRADE
   -> 48% FRONTLINE_SERVICE -> 93% AI_DATA_WORK. Report hourly-posted roles as hourly rates.
4. **AI_DATA_WORK is one employer.** 125 of 143 Bay postings with salary are DataAnnotation (425 of 451
   statewide). Median posted rate $75/hr, 93% part-time, 89% contract, 76% remote. The annualized
   $156k median is an ARTIFACT. The only annual-posted figure in the class was $20,800-$41,600/yr.

## TEST S1 — Demand index: vacancy flow vs incumbent employment stock
Indeed unseeded Bay postings vs PUMS 2019-23 Bay employed workers, same class names.
demand_index = (class share of postings) / (class share of employment).

| group | post share | emp share | demand index |
|---|---|---|---|
| AI_POSITIONED (AI_PRODUCER+SOFTWARE_ENG+DATA_ENG_ANALYTICS) | 19.1% | 8.2% | **2.33** |
| EXPOSED (CLERICAL_ADMIN+CUSTOMER_SUPPORT+PROF_EXPOSED) | 8.4% | 13.7% | **0.62** |

=> Bay Area hiring demand is ~3.8x more intense, relative to existing headcount, in AI-positioned
occupations than in exposed ones. Per-class: CLERICAL_ADMIN 0.54, PROF_EXPOSED 0.53, EDUCATION 0.35,
FRONTLINE_SERVICE 0.61, SKILLED_TRADE 0.51; MANAGEMENT 1.01, CUSTOMER_SUPPORT 1.02.

**DO NOT report the per-class AI_PRODUCER demand index (15.45) — it is a definitional artifact.**
PUMS AI_PRODUCER is only OCCP 1005 + 1240 (CS research scientists, data scientists/statisticians;
22,045 weighted Bay workers). ACS codes working ML engineers as 1021 Software Developers, while the
postings-side AI_PRODUCER rule captures any ML/AI title. The boundary differs between the two datasets.
The POOLED AI_POSITIONED index (2.33) is robust because it pools across that boundary on both sides.
Same logic: prefer pooled EXPOSED (0.62) over its per-class components.

## TEST S2 — Entry wage ratio: posted new-hire pay vs incumbent full-time median
Posted median sal_mid (unseeded, Bay, salary-disclosing) / weighted median annual wage of
full-time/full-year Bay incumbents in the same class (PUMS, n=130,215). Classes with inc_n>=100.

| occupation class | incumbent median | posted median | ratio |
|---|---|---|---|
| DATA_ENG_ANALYTICS | 118,714 | 180,000 | **1.52** |
| PRODUCT_DESIGN | 127,440 | 189,850 | 1.49 |
| AI_PRODUCER | 162,796 | 219,687 | 1.35 |
| SOFTWARE_ENG | 180,445 | 210,000 | 1.16 |
| HEALTH_CLINICAL | 86,825 | 100,000 | 1.15 |
| SKILLED_TRADE | 60,386 | 68,640 | 1.14 |
| OTHER_ENGINEERING | 148,393 | 167,550 | 1.13 |
| MANAGEMENT | 150,964 | 167,100 | 1.11 |
| SALES_BIZ | 113,525 | 115,000 | 1.01 |
| FRONTLINE_SERVICE | 48,308 | 44,439 | 0.92 |
| PROF_EXPOSED | 108,531 | 99,018 | **0.91** |
| CUSTOMER_SUPPORT | 62,948 | 56,160 | **0.89** |
| CLERICAL_ADMIN | 66,204 | 56,488 | **0.85** |
| EDUCATION | 81,561 | 66,560 | 0.82 |

Monotone ordering: AI-positioned classes advertise ABOVE what incumbents earn; exposed classes
advertise BELOW. Repricing runs in both directions at once.

**Direction of the bias matters and strengthens the exposed finding.** PUMS wages are in 2023-adjusted
dollars; postings are 2026 nominal. So every ratio is an UPPER bound: the sub-1.0 exposed ratios are
worse in real terms than shown, and part of the AI-positioned premium is just three years of inflation.

Other limits: posted range midpoint is advertised, not realized, pay; new-hire pay vs all-incumbent pay
confounds tenure; within-class composition differs between the two sources. Treat as descriptive
repricing evidence, not a causal estimate.

Outputs: `base/synth_demand_index.csv`, `base/synth_entry_vs_incumbent.csv`.
