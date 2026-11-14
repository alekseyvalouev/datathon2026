# EXPERIMENT M: predictive models and fairness audit (Bay Area postings x PUMS)

Data: `base/indeed_base_v3.parquet` (134,595 CA postings; 45,850 Bay Area, of which 36,587 unseeded) joined to raw `description_text` on `jobid`. Seed 42 everywhere. All figures below were computed by `code/model_*.py` (`code/model_run_all.sh` runs everything end to end). Every held-out number is **company-grouped** (no employer appears in both train and test). Tidy metrics: `base/model_metrics.csv`.

## 0. Headline metrics (model vs baselines)

**Model 1: occupation class from text** (labels = regex `occ` != OTHER, n=106,934, noisy and rule-derived from `job_title`; 20% company-held-out test n=22,508)

| model | macro-F1 | accuracy | note |
|---|---|---|---|
| majority class | 0.022 | 0.217 | |
| title-keyword linear (baseline) | 0.970 | 0.987 | **circular**: labels ARE a function of the title, so this only re-learns the regex |
| title + description | 0.951 | 0.985 | circular for the same reason |
| **description only** | **0.767** | 0.836 | the honest number: how much occupation is recoverable from text alone |
| description only, naive random-row split | 0.861 | 0.872 | **+9.4 macro-F1 points of leakage**; 80.7% of random-split test rows have their employer in train |
| description only, 5-fold company OOF (all labelled) | 0.761 | 0.830 | |
| desc-only on seeded / unseeded test rows | 0.743 / 0.769 | 0.807 / 0.843 | seeded rows are NOT inflated here; if anything they are slightly worse |
| desc-only, test rows whose exact title is not in train | 0.736 | 0.811 | |

**Model 2: log posted salary** (disclosers with usable pay, n=113,916 CA / 38,502 Bay; 5-fold company-held-out, every prediction from a model that never saw that employer)

| model | RMSE log | MAE log | RMSE $ | MAE $ | R2 |
|---|---|---|---|---|---|
| global median | 0.645 | 0.552 | 80,010 | 54,974 | -0.02 |
| occupation-class median | 0.460 | 0.344 | 60,273 | 37,033 | 0.48 |
| OLS, structured features only | 0.344 | 0.254 | 50,055 | 28,357 | 0.71 |
| LightGBM, structured only | 0.317 | 0.229 | 47,318 | 26,057 | 0.75 |
| ridge on TF-IDF text only | 0.261 | 0.193 | 39,999 | 21,803 | 0.83 |
| **text stack (ridge OOF -> LightGBM + structured)** | **0.237** | **0.170** | **37,019** | **19,755** | **0.86** |
| (Bay only: occ-median / OLS / text stack) | 0.466 / 0.339 / 0.243 | 0.351 / 0.256 / 0.178 | 68,719 / 54,976 / 42,879 | 45,492 / 35,003 / 25,615 | |

Text stack cuts RMSE 49% vs the occupation-median baseline and 31% vs structured OLS. Median absolute error is 0.126 log (13%); 66% of CA predictions (63% Bay) land within 20% of the posted figure vs 39% (37%) for the occupation median. 80% prediction intervals (cross-conformal, by class) have 79.8% coverage overall and 79.4-80.0% in every class.

**Model 3: who has no posted pay** (company-held-out 5-fold; positive class = no salary; Bay n=45,850, base rate 15.3%)

| model | AUC | avg precision | precision / recall at F1-optimal threshold |
|---|---|---|---|
| majority ("always has salary") | 0.500 | 0.153 | 0 / 0 (accuracy 84.7%) |
| logistic, structured only | 0.710 | 0.380 | 0.364 / 0.414 |
| LightGBM, structured only | 0.707 | 0.442 | 0.429 / 0.426 |
| text logistic (full text) | 0.833 | 0.565 | 0.497 / 0.572 |
| text logistic, pay words masked (salary/range/hour/SALNUM/etc. removed) | 0.788 | 0.488 | not computed |
| LightGBM structured + text OOF | 0.813 | 0.584 | 0.579 / 0.516 |

Caveat: the text gain is partly mechanical. Descriptions that quote a pay range usually coincide with the salary field being filled, so even after scrubbing dollar figures the model can see "a pay range was here". Masking pay vocabulary still leaves AUC 0.79, so some non-pay-word text signal remains, but the interpretable "who" answer is the structured model (AUC about 0.71, i.e. modest).

## 1. The three most important substantive results

1. **Reallocating OTHER (19.2% of Bay postings; 19.9% unseeded) barely changes the study's exposure/AI ratio but does raise both shares.** Using the model-reassigned classes, unseeded Bay AI_POSITIONED (AI_PRODUCER+SOFTWARE_ENG+DATA_ENG_ANALYTICS) goes from 18.85% to 21.47% and EXPOSED (CLERICAL_ADMIN+CUSTOMER_SUPPORT+PROF_EXPOSED) from 8.35% to 9.42%. The AI:exposed ratio is 2.26 before and 2.28 after, so the relative picture is unchanged; the level shift is the OTHER bucket shrinking from 19.9% to 9.9% (the remainder is left unresolved on purpose, see hand-validation). Full Bay sample: AI_POSITIONED 21.27% -> 24.11%, EXPOSED 7.83% -> 8.85%. FRONTLINE_SERVICE (+2.4 pts), HEALTH_CLINICAL (+1.6) and SOFTWARE_ENG (+1.8) absorb (unseeded Bay) most of the reassigned mass.
2. **Salary text model beats baselines decisively, and its errors do not disadvantage exposed or low-wage occupations; they under-predict AI-positioned pay.** Bay bias (mean predicted minus actual, expressed as % of pay; negative = under-prediction): AI_POSITIONED -4.7% (SE 0.3 log pts), EXPOSED -1.1% (SE 0.4), FRONTLINE -0.9% (SE 0.2), contract +1.1% (SE 1.0), part-time -0.6%. The model compresses the distribution: conditional on actual pay, the lowest quintile is over-predicted (+10.4 log points) and the top quintile under-predicted (-16.4 log points), while conditional on predicted pay bias is near zero (-0.9 to -1.9 log points). So imputed values for low-wage roles lean slightly high and imputed values for top-paying roles lean low.
3. **Non-disclosure is not concentrated in exposed occupations once you control for posting format.** Raw Bay unseeded no-pay rates: CLERICAL_ADMIN 24.0%, SALES_BIZ 23.6%, PROF_EXPOSED 20.4%, SOFTWARE_ENG 20.0%, AI_PRODUCER 16.6%, CUSTOMER_SUPPORT 13.4%, FRONTLINE_SERVICE 12.8%, HEALTH_CLINICAL 11.4%. Group level: EXPOSED 19.9%, AI_POSITIONED 18.3%, FRONTLINE 12.7%. After adjusting (Bay unseeded logit, company-clustered bootstrap CIs, base = MANAGEMENT), exposed classes are not distinguishable from management (CLERICAL 1.10 [0.84, 1.55], PROF_EXPOSED 0.96 [0.73, 1.21]; CUSTOMER_SUPPORT is *less* opaque, 0.73 [0.55, 0.94]) and the AI-positioned classes also are not (AI_PRODUCER 1.10, SOFTWARE_ENG 1.07). Skilled trade (0.48), health (0.53), legal (0.44), education (0.54) and frontline (0.62) are significantly *less* opaque. The strongest drivers are format features: each log-unit of description length cuts the odds to 0.35; remote postings 1.74x odds of no pay; postings from companies with no rating 1.64x; part-time 0.52x; contract 0.64x. The people shown a pay-less ad are disproportionately in remote, short-description, unrated-employer, white-collar postings (sales, clerical, software, analytics), not in the study's "exposed" group specifically.

## 2. NEGATIVE and cautionary results (read these)

- **Title-based models "work" only because the labels are title-derived.** Title-only macro-F1 0.970 and title+desc 0.951 are the regex re-learned, not evidence of accuracy. The informative figure is description-only 0.767, and the naive random split overstates it by 9.4 points.
- **Description-only macro-F1 is poor for exactly the classes the study cares about.** CLERICAL_ADMIN F1 0.826, PROF_EXPOSED 0.750 (recall 0.694), CUSTOMER_SUPPORT 0.740 (recall 0.667) versus HEALTH 0.921, EDUCATION 0.919, FRONTLINE 0.906. AI_DATA_WORK F1 0.00 (7 test rows). AI_PRODUCER vs SOFTWARE_ENG are swapped constantly (129 SOFTWARE_ENG predicted AI_PRODUCER, 115 the reverse). MANAGEMENT is a sink: FRONTLINE->MANAGEMENT 169, PROF_EXPOSED->MANAGEMENT 140, PRODUCT_DESIGN->MANAGEMENT 97, SALES->MANAGEMENT 97. **The AI_PRODUCER/SOFTWARE_ENG boundary should be treated as unresolvable from text; use their sum.**
- **Model-predicted MANAGEMENT on OTHER postings is almost always wrong** (1 of 19 correct in the hand sample), so it is never used to reassign OTHER.
- **AI_DATA_WORK cannot be learned out-of-company.** 419 of its 447 labelled rows are one employer (DataAnnotation). A company-held-out fold removes the whole class, so the model scatters those postings: AI_PRODUCER 264, SOFTWARE_ENG 114, OTHER_ENGINEERING 30, PROF_EXPOSED 10, PRODUCT_DESIGN 1. **The text model does NOT correctly group them.** In the v3 regex, however, all 419 DataAnnotation postings are already labelled AI_DATA_WORK (every one has "AI Trainer" in the title), so the title-scatter across CLERICAL/PROF_EXPOSED/SOFTWARE_ENG that was expected did not occur in this table. The regex is right on all 15 DataAnnotation cases I read (three "AI Trainer" rows came up in the random disagreement draw, 12 more added). Overrides are disabled for this class.
- **Worst salary errors are source-data errors, not model failures.** All 16 worst residuals (8 over, 8 under; `base/model_salary_failures.csv`) are implausible posted pay: physicians/pharmacists/dentist at $10,917-$24,000 "per year/month" (model predicts $140k-$370k), and $540k-$1.08M for "Entry Level Manager", "Integration Specialist", "Strategic Relationship Manager" (pay-period or annualisation mis-parse; month/week/day rows are annualised by multiplying, which blows up when the quoted figure was already annual). Drivers for each are listed in the CSV (title tokens such as physician, anesthesiologist, pharmacist, dentist for over-predictions; "chief", "relationship manager", "entry level account" for under-predictions). Hourly row "Cadet" at $760,074 is $365/h annualised, probably a day rate. The `sal_mid` column needs a plausibility screen by period, especially month/week/day (n=206/174/80 in the Bay test set; their errors are 2-3x larger: RMSE 0.44/0.37/0.71 log).
- **Imputation barely moves class-level pay, and the model cannot see selection on unobservables.** See section 4.

## 3. Model 1 details: hand validation and reallocation

**Hand validation (single rater, me, not blinded to model output; ambiguity labelled).** Verdicts: c = clearly correct class, a = defensible but not clearly best, w = wrong. Files: `base/model_handcheck_*_verdicts*.csv`.

| check | n | strict (c only) | lenient (c + a) |
|---|---|---|---|
| Random Bay OTHER postings, all predictions, no filter | 110 | **54.5%** | **75.5%** |
| of which model predicted MANAGEMENT | 19 | 5.3% | 10.5% |
| of which predicted non-MANAGEMENT with p >= 0.6 (the rule below) | 62 | 72.6% | 96.8% |
| **Fresh random sample, rule applied (non-MANAGEMENT, p >= 0.6), disjoint from the first** | 45 | **80.0%** | **100%** (0 wrong) |
| Hand accuracy by confidence bin (sample 1; strict): p<=0.4 / 0.4-0.6 / 0.6-0.8 / 0.8-0.9 / >0.9 | 24/13/27/13/33 | 29% / 54% / 59% / 31% / 79% | 50% / 69% / 85% / 77% / 88% |

The reallocation rule (chosen using sample 1, validated on the fresh sample 2): assign the model class to a regex-OTHER posting only if the model's class is not MANAGEMENT and p >= 0.6. This resolves 4,438 of 8,818 Bay OTHER postings (50.3%); 4,380 stay OTHER ("unresolved"). Statewide 14,453 of 27,661 CA OTHER postings are reassigned. Many remaining OTHER postings genuinely fit no class in the taxonomy (scientists, pilots, postdocs, geologists, chief engineers etc. were routinely forced into AI_PRODUCER/PROF_EXPOSED/MANAGEMENT by the model; I counted those as wrong). Probabilities come from a temperature-scaled (T=3.63) softmax of company-grouped OOF SVM margins; treat them as rank-ordering, not calibrated frequencies. Reassigned Bay mass: FRONTLINE 19.7%, SOFTWARE_ENG 18.6%, HEALTH 15.0%, AI_PRODUCER 7.5%, SKILLED_TRADE 7.1%, OTHER_ENGINEERING 6.7%, SALES 6.6%.

**Regex-vs-model disagreements.** 18,135 of 106,934 labelled rows (17.0%) disagree under company-held-out OOF prediction (this includes ordinary model error). Of these, 7,538 are confident (model p >= 0.7 and model prob of the regex label < 0.15). I read 67: 55 random confident disagreements plus 12 DataAnnotation. Among the 52 non-DataAnnotation random cases: **model right 23, regex right 8, both defensible 19, neither 2**. Among the 15 DataAnnotation cases the regex was right in all 15. Systematic regex errors found:
- keyword collisions on "chief / lead / controller / manager": Traffic Controller, Lead Generation Specialist, Survey Party Chief, Hotel Chief Engineer all -> MANAGEMENT (really trades/sales/survey crews);
- "nursing / nursery" -> HEALTH_CLINICAL: Garden/Nursery Retail Sales Associate, Skilled Nursing Transportation Driver;
- "full stack" -> SOFTWARE_ENG for a turbomachinery hardware engineer; "Attorney II - Construction" -> SKILLED_TRADE; "Dermatologist" -> FRONTLINE_SERVICE; "X-Ray Technician" and "Behavioral Health Technician" -> SKILLED_TRADE; "Behavior Support Specialist (ABA)" -> CUSTOMER_SUPPORT; "MarTech Principal" -> EDUCATION;
- AI_PRODUCER is over-broad: "Technical Marketing Specialist (AI & Digital Marketing)", "Principal Research Scientist - PK/PD modeling", "Laser Postdoctoral Researcher" were all labelled AI_PRODUCER.
- AI_PRODUCER vs SOFTWARE_ENG (118 AI_PRODUCER->SOFTWARE_ENG and 107 the reverse among Bay overrides) is a coin-flip boundary in both directions.

**Conservative override of regex labels** (applied in `consensus`): model OOF p >= 0.9 and model prob of regex label < 0.05, model class not MANAGEMENT, regex class not AI_DATA_WORK. 2,508 CA rows (985 Bay) are overridden. Hand check of 30 random overrides: regex wrong / model right 16, regex right 2, both defensible 12 (mostly the AI_PRODUCER/SOFTWARE_ENG swap). Largest Bay override flows: AI_PRODUCER->SOFTWARE_ENG 118, SOFTWARE_ENG->AI_PRODUCER 107, MANAGEMENT->SOFTWARE_ENG 58, MANAGEMENT->AI_PRODUCER 46, OTHER_ENGINEERING->SOFTWARE_ENG 39, MANAGEMENT->FRONTLINE 39, CLERICAL->FRONTLINE 37. Overrides move the headline shares by well under a point; the OTHER reallocation is the larger effect.

**Bay distribution (unseeded, n=36,587)**: see `base/model_occ_bay_distribution.csv`. Key shares regex -> consensus: SOFTWARE_ENG 9.3% -> 11.1%, AI_PRODUCER 8.5% -> 9.3%, DATA_ENG 1.0% -> 1.1%, CLERICAL 3.2% -> 3.6%, CUSTOMER_SUPPORT 2.3% -> 2.5%, PROF_EXPOSED 2.9% -> 3.3%, FRONTLINE 13.5% -> 15.9%, HEALTH 6.8% -> 8.3%, MANAGEMENT 14.3% -> 13.7%, OTHER 19.9% -> 9.9%. Coordinator reference figures (18.8% / 8.3%) reproduce exactly on the regex labels.

`base/model_occ_reassigned.csv` columns: `jobid`; `regex_occ` (original rule label); `predicted_class` and `predicted_prob` (for regex-labelled rows these are the company-grouped out-of-fold prediction from the description-only model, for regex-OTHER rows the full-data description-only model; probabilities are temperature-scaled softmax scores); `consensus` (final class to use); `consensus_source` in {regex_kept, regex_overridden_by_model, OTHER_reassigned_by_model, OTHER_unresolved}; `pred_source`. Unseeded flag is in the base table (`seeded`).

## 4. Model 2 details

**Design.** Target: log(sal_mid) (annualised). Features: structured fields (consensus class, county, top-60 cities, job_type, flags, years, degree flags, desc length, Glassdoor rating/reviews, AI flags, **sal_period, parttime**) + ridge on TF-IDF of title and description (dollar amounts scrubbed to a SALNUM token to prevent leakage) stacked into LightGBM using inner company-grouped OOF. Training excludes AI_DATA_WORK and every DataAnnotation row (445 disclosers), pay outside $15k-$1M, and sal_hi/sal_lo > 5. 113,916 usable of 115,067 disclosers.

**Pay-period artifact check (requested).** Bay bias, pred minus actual, main model: hourly-posted -1.1% (SE 0.2), annual-posted -2.7% (SE 0.2), week +1.5% (SE 2.8), month -0.2% (SE 3.1), day +16.7% (SE 7.8, n=80). RMSE: hourly 0.217, annual 0.251. The difference between hourly and annual bias is real but small (1.6 pts). The AI-positioned under-prediction survives inside annual-posted rows only (year|AI_POSITIONED -4.9%, n=8,679, vs year|EXPOSED -0.8%, year|FRONTLINE +0.7%), and AI_POSITIONED is overwhelmingly annual-posted (8,679 of 9,136), so it is not driven by pay period. Hourly-posted part-time rows are not systematically biased (part-time -0.6%).

**Robustness (requested).** (Biases in this paragraph are in log points x 100.) A literal "log hourly-equivalent pay" target (sal_mid/2080) differs from log(sal_mid) by a constant and cannot change residuals or bias, so I instead ran two substantive variants: (i) separate models for hourly-posted and other rows, (ii) a part-time-adjusted target in which part-time hourly pay is annualised at 1,040 rather than 2,080 hours. Bay bias by group, main / separate-period / part-time-adjusted:
AI_POSITIONED -4.8% / -4.3% / -4.8%; EXPOSED -1.1% / -1.2% / -1.0%; FRONTLINE -0.9% / -0.7% / -0.8%; contract +1.1% / +2.3% / +1.0%. **The subgroup conclusions survive both changes.** Overall RMSE log: 0.2425 main, 0.2380 separate, 0.2496 on the part-time-adjusted target (not directly comparable, different target).

**Subgroup error table** (`base/model_subgroup_errors.csv`: Bay and CA scopes, six model variants, by occupation class, county, group3, seniority, employment type, pay period, part-time, seeded, and period x group3). Bay highlights for the main model (bias %; RMSE log): SOFTWARE_ENG -5.1% (0.247), AI_PRODUCER -4.4% (0.257), OTHER_ENGINEERING -4.4%, EDUCATION -3.7%, PRODUCT_DESIGN -3.3%; CLERICAL -1.3% (0.186), CUSTOMER_SUPPORT -1.5% (0.199), PROF_EXPOSED -0.7% (0.228), FRONTLINE -1.0% (0.180), SKILLED_TRADE -0.3%; SALES_BIZ +0.9% (0.319, largest error). Counties: Santa Clara -3.5%, Marin -3.8%, Alameda -1.3%, San Francisco -1.1%, San Mateo -1.5%, Sonoma -0.1%. Seniority: junior -0.7%, senior -2.5%. Employment: contract +1.1% (RMSE 0.326, the noisiest group), full-time -1.9%, unspecified -3.7%. The occupation-median baseline by contrast under-predicts exposed roles badly (CUSTOMER_SUPPORT -32, CLERICAL -18, PROF_EXPOSED -20 log points, Bay), because it ignores within-class variation in pay period and part-time mix; the text model removes that.

**Imputation payoff** (`base/model_salary_imputation_by_class_Bay_unseeded.csv`, `..._Bay_all.csv`). 7,015 Bay no-pay postings imputed (AI_DATA_WORK and DataAnnotation excluded: not imputed, flagged `not_imputed_flag`). Respecting pay period: a hourly-vs-other classifier (company-held-out AUC 0.978) sets the period feature; 33.8% of imputed postings are predicted hourly (disclosed hourly share 38.5%). Class pay is reported in hourly-equivalent (annual/2080) so hourly and annual postings are comparable; "FTE annual" is that times 2,080 and does **not** imply the part-time hourly worker earns that annually. Median hourly-equivalent, disclosed-only -> disclosed + imputed, unseeded Bay: AI_PRODUCER $105.26 -> $103.37 (-1.8%), SOFTWARE_ENG $99.28 -> $94.59 (-4.7%), DATA_ENG $84.14 -> $80.77 (-4.0%), PRODUCT_DESIGN -3.2%, OTHER_ENGINEERING -3.6%, PROF_EXPOSED -4.0%, MANAGEMENT -1.3%, CLERICAL -1.5%, CUSTOMER_SUPPORT +3.7%, SALES_BIZ +4.5%, HEALTH +2.2%, EDUCATION +2.5%, FRONTLINE +0.4%. **No class changes by more than 4.7% and the class ranking by median pay is essentially unchanged** (largest rank moves are adjacent: CUSTOMER_SUPPORT 15 -> 14 and CLERICAL 14 -> 15). Imputation does not change the pay picture, a mild negative result.

**Selection.** Predicted pay of non-disclosing postings vs disclosing ones, same class x county, unseeded Bay: non-disclosers are predicted **3.8% lower** (log gap -0.039, company-cluster bootstrap 95% CI [-0.066, -0.011]). This is heterogeneous: SOFTWARE_ENG -17.9% in logs within county, DATA_ENG -16.3%, PRODUCT_DESIGN -13.4%, PROF_EXPOSED -12.5%, OTHER_ENGINEERING -10.1% (non-disclosers look like cheaper roles in tech/white-collar classes), but HEALTH_CLINICAL +11.1% and CUSTOMER_SUPPORT +12.7% (non-disclosers look better paid). These gaps use model predictions on observed features for both groups, so they speak only to observables; selection on unobservables is not identified. The model assumes missing-at-random conditional on features; **imputed values carry all of the model's biases** (compression toward the mean, -4.7% for AI-positioned, 80% interval coverage is a property of disclosers). Imputed PI80 median width factor is 1.75x (hi/lo), identical to disclosers.

## 5. Model 3 details

Company concentration: of 2,103 employers with at least 10 postings, 3.9% never show pay, 51.6% always show pay, 44.5% are mixed, so most non-disclosure is within-employer posting-level variation, not a few bad employers. Top structured drivers (LightGBM mean |SHAP|): log reviews 0.41, desc length 0.39, job_type 0.25, occupation 0.20, city 0.17, rating 0.16, county 0.07. Direction: remote (+), short description (+), missing/low company rating (+), part-time (-), junior (-), hybrid (-), contract (-). Text words most associated with no pay: resume, send resume, email resume, fax, "hiring range" (a range named but not shown), casino, university systems (ucsf, csu), volunteer; words most associated with pay shown: pay/salary/range/compensation/hour. Audit AUCs by Bay class range from 0.62 (CLERICAL, the hardest to predict; AI_DATA_WORK 0.45 on n=145) to 0.90 (LEGAL); by county from 0.69 (Napa) to 0.88 (Marin). Files: `model_opacity_audit.csv`, `model_opacity_bay_adjusted_OR_clean.csv`, `model_opacity_text_words.csv`, `model_opacity_shap.csv`. (`model_opacity_bay_adjusted_OR.csv` is a noisier first version with hundreds of job_type dummies; use the `_clean` file.)

**Plain statement.** The workers most likely to be shown an ad with no pay are those applying to remote, short-text postings at employers with no Glassdoor profile, in sales, clerical, software and analytics roles (raw rates 18-24%), in San Francisco (20.4% unseeded vs 11-16% elsewhere). Raw rates are higher in the exposed group (19.9%) than in frontline roles (12.7%), but that gap is largely explained by posting format and is not significant for CLERICAL or PROF_EXPOSED after adjustment; the concentration is on format and location, not specifically on exposed occupations. In-person occupations (trades, health, education, frontline, legal) are the least opaque.

## 6. Model 4: demand-weighted demographic incidence (INCIDENCE ACCOUNTING, NOT A FORECAST, NOT A CAUSAL CLAIM)

Inputs: unseeded Bay postings (n=36,587) with consensus classes (primary; seeded-inclusive n=45,850 in the CSV as a sensitivity, results differ by under 0.5 pts), mapped to PUMS classes (AI_DATA_WORK -> AI_PRODUCER; LEGAL_PROF -> PUMS OTHER); `pums_bay.parquet` (ACS 2019-2023, PWGTP weights), county-specific class race composition with Bay-wide fallback where county-class cells have under 40 records. "High-paying AI-positioned" = AI_PRODUCER/SOFTWARE_ENG/DATA_ENG postings with disclosed-or-imputed annualised FTE pay >= $150,000 (n=6,652; 5,660 with disclosed pay). Each posting is assigned its class's incumbent race composition and the counts are summed.

**Identifying assumptions, loudly:** (1) postings are vacancy FLOW, PUMS is employment STOCK from 2019-2023; (2) the posting sample is not a random sample of Bay vacancies (Indeed extract, two-crawl structure, not all employers post there, imputation covers the no-pay minority); (3) the racial composition of an occupation's incumbents need not be the composition of who is hired into new AI-positioned roles, and the table says nothing about discrimination, hiring or barriers; (4) race shares inherit PUMS sampling error that is NOT in the intervals shown (bootstrap CIs resample postings only and are therefore tiny); (5) the model-side classes and imputed pay carry the biases above. This is arithmetic on two marginal distributions.

Bay Area (9 counties), race shares (White / Black / Asian / Hispanic; remaining groups in the CSV):

| measure | White | Black | Asian | Hispanic |
|---|---|---|---|---|
| (a) high-pay AI-positioned demand, class incumbent composition | 33.2% | 1.9% | 53.9% | 6.1% |
| (a2) same, composition of incumbents earning >= $150k | 36.6% | 1.1% | 53.8% | 3.9% |
| PUMS stock: AI-positioned employment | 29.9% | 1.8% | 58.4% | 5.7% |
| (b) exposed-occupation demand, posting-weighted | 36.5% | 6.3% | 29.8% | 21.2% |
| PUMS stock: exposed employment base | 37.3% | 6.1% | 30.0% | 20.5% |
| all postings, incumbent composition | 37.3% | 4.6% | 33.1% | 19.5% |
| all employed workers (PUMS) | 36.5% | 5.1% | 29.3% | 23.6% |

By county (unseeded, `base/model_demand_incidence.csv`; (a) high-pay AI-positioned demand | (b) exposed demand; White / Black / Asian / Hispanic):
- Santa Clara (n 3,401 | 884): (a) 22.0 / 1.8 / 68.1 / 4.0 | (b) 30.5 / 3.1 / 38.8 / 23.5
- San Francisco (2,278 | 865): (a) 46.8 / 1.4 / 38.3 / 8.9 | (b) 37.0 / 4.2 / 37.5 / 15.2
- San Mateo (597 | 410): (a) 35.3 / 0.8 / 54.4 / 5.6 | (b) 32.3 / 1.8 / 37.2 / 21.8
- Alameda (306 | 577): (a) 28.3 / 2.4 / 56.8 / 5.9 | (b) 28.7 / 10.7 / 34.0 / 20.2
- Contra Costa (48 | 318): (a) 45.7 / 1.1 / 41.3 / 7.4 | (b) 39.1 / 9.7 / 20.9 / 23.4
- Marin, Napa, Solano, Sonoma: fewer than 10 high-pay AI-positioned postings, not estimated; exposed (b): Marin 67.9 / 2.0 / 7.1 / 15.5, Napa 42.4 / 3.0 / 9.3 / 37.2, Solano 33.0 / 15.2 / 18.2 / 23.3, Sonoma 63.9 / 1.7 / 4.0 / 24.0.

Read: relative to the all-employed workforce, high-pay AI-positioned demand carries about 1.8x the Asian share and 0.37x the Black share (1.9% vs 5.1%) and 0.26x the Hispanic share (6.1% vs 23.6%). The exposed-occupation base looks like the overall workforce except it is more Black than the AI-positioned base by a factor of 3.3 and more Hispanic by 3.5. Cutting incumbents to those earning >= $150k pushes Black and Hispanic shares of the AI-positioned base lower again (1.1% and 3.9%). Disclosed-pay-only and seeded-inclusive versions change shares by under 1 pt Bay-wide (county versions in the CSV; SF White share moves from 46.8% to 54.3% if only >= $150k incumbents are used).

## 7. What this means for the working hypothesis

Supports: (i) high-pay AI-positioned demand is, by incumbent composition, very Asian and White and very small in Black and Hispanic shares; (ii) the model learns that AI-positioned and software roles carry the highest pay (SOFTWARE_ENG $99/h, AI_PRODUCER $105/h median hourly-equivalent vs $21/h frontline, $27/h clerical); (iii) EXPOSED classes are lower paid than AI_POSITIONED by 3-4x.

Does not support, or complicates: (1) reallocating OTHER leaves the AI:exposed posting ratio unchanged at about 2.3, so the posting-side balance does not depend on how OTHER is handled; (2) the model does not under-predict pay for exposed or low-wage classes (bias about -1%); the larger under-prediction is for AI-positioned roles (-4.7%), so any "inherited and amplified inequality" worry is in the opposite direction from the hypothesis (imputed pay for top roles is understated); (3) pay opacity is not concentrated in exposed occupations once format and location are controlled; (4) imputing pay changes no class median by more than 4.7%; (5) the "AI_DATA_WORK" class is a single employer (DataAnnotation, 419 of 447 CA rows) whose posted annualised pay is not a real wage, and should not be used as a class-level pay or incidence estimate; (6) the regex is wrong in recognisable ways (chief/lead/controller -> MANAGEMENT, nursery/nursing -> HEALTH, AI_PRODUCER over-broad), which mostly shifts mass between MANAGEMENT and operational classes and inside the AI-positioned group, not between AI-positioned and exposed.

## 8. Files

Code (`scratchpad/code/`): model_lib.py, model_00_extract.py, model_01a/b/c/d/e/f, model_02_salary.py, model_03_opacity.py, model_03b_opacity_extra.py, model_04_incidence.py, model_05_m2_payoff.py, model_06_assemble.py, model_run_all.sh. Data (`scratchpad/base/`): model_occ_reassigned.csv, model_salary_predictions.csv (OOF predictions for disclosers, final-model imputations for non-disclosers, PI80, `period_used`, `p_hourly`, `pred_hourly_equiv`, `imputed`, `not_imputed_flag`), model_metrics.csv, model_subgroup_errors.csv, model_demand_incidence.csv, plus model_occ_perclass.csv, model_occ_confusion_*.csv, model_occ_bay_distribution.csv, model_handcheck_*.csv, model_salary_failures.csv, model_salary_imputation_by_class_*.csv, model_salary_selection_gap.csv, model_opacity_*.csv, model_text.parquet (raw text cache, 288 MB). Models are not saved. Hand-check verdicts are manual annotations hard-coded in model_01d_handverdicts.py and model_01f_finalize_occ.py and rest on one unblinded rater.
