import sys
S=sys.argv[1]
t=open(S+'/out/_tables.md').read()
def sec(n):
    a=t.index('## '+n+'\n')+len(n)+4
    rest=t[a:]; b=rest.find('\n## ')
    return rest if b<0 else rest[:b]
S_,C_,A_,T_,P_=[sec(x) for x in ['SERIES','CLASSRATINGS','AIPEXP','TEXT','PREC']]
memo=f'''# Experiment V: worker voice (Reddit + Glassdoor). Findings memo

Scope: independent validation layer for the Bay Area AI/labor study. These sources corroborate mechanism. They do not measure incidence. Everything below is aggregated to subreddit scope, month, company, or occupation class; no individual is reported.

## Lead results (three most important)

1. **AI-displacement discourse is NOT rising in worker-voice Reddit. It is flat to slightly falling, and it is essentially absent from Bay Area subreddits.** In the general work subreddits (WORK_GEN: r/recruitinghell, antiwork, careerguidance, jobs, jobsearchhacks, jobsearch, usajobs; 22,442 posts) the share of posts discussing AI in relation to work or hiring is 4.2% (Jan-Jun 2025), 4.3% (Jul-Dec 2025), 4.3% (Jan-Jun 2026) and 3.4% (Jul-Oct 2026). A logit trend with subreddit fixed effects is -1.3% odds per month (p=0.037): mildly down, not up. The crawl is very uneven (1,756 posts in Jan 2025 vs 25,055 in Jul 2026 for the whole file; WORK_GEN 281 vs 2,284), so raw counts rise about 8x from volume alone; every trend claim here uses shares. In the Bay Area subreddits (14,914 posts) only 26 posts (0.17%) are AI-and-work discourse, and none is a first-person displacement report.
2. **What workers talk about is job-search friction, not displacement.** Of the 924 AI-and-work posts in WORK_GEN+BAY, 569 (61.6%) are about AI in hiring or job search (AI screening, AI interviews, AI resume tools), 254 (27.5%) are fear/anticipation of displacement, 81 (8.8%) are AI as a workplace tool, and only 20 (2.2%) are strict first-person or close-network reports of actual displacement. Entry-level job-search posts show 2.4x the application-volume talk and 1.7x the any-friction rate of other job-search posts (below).
3. **Occupations named under displacement/exposure partly match the quantitative flags, but software dominates and clerical and customer support are barely named.** Among the 67 displacement/fear posts where the occupation is reliably identified (self-ID or title; hand-checked precision 80%), 26 (39%) name software engineers, 18 (27%) PROF_EXPOSED roles (marketing, writing, design, accounting, HR/recruiting), 2 clerical/admin, 0 customer support, and 2 frontline service. In-person trades appear 7 times, as a refuge ("AI-proof"), not as victims. On Glassdoor, **exposed classes are NOT diverging** from AI-positioned classes on career or compensation ratings (negative result, below).

## Negative and null results (stated plainly)

- Reddit AI-displacement discourse: no upward trend through Oct 2026. The any-AI-term share (recall-independent) is also flat: 9.6%, 10.8%, 11.4%, 10.1% across the same four periods; its subreddit-FE logit trend is +0.4%/month, p=0.31.
- Bay Area subreddits: no usable worker-voice signal on AI and jobs (26 posts). AI terms appear in 3.0% of Bay posts (444 posts), rising from 2.5% (2025) to 4.4% (Jul-Oct 2026), but that is AI industry, housing and culture talk, not worker displacement. Do not cite Reddit as Bay-specific corroboration of displacement.
- Glassdoor: AI-positioned vs exposed rating gaps are not widening over 2025-2026. Time-by-class slope interactions (company fixed effects, clustered by company): career opportunities +0.0015 pts/month for exposed relative to AI-positioned (p=0.62); compensation +0.0038 (p=0.15); overall +0.0054 (p=0.12). The AI-positioned minus exposed career gap was 0.27 (2025H1), 0.39 (2025H2), 0.16 (2026H1), 0.22 (2026H2, Jul-Nov): if anything it narrowed.
- The raw AI-positioned vs exposed gap (career d=0.20, comp d=0.25) is mostly between-company sorting (AI-positioned reviewers sit at Google, Meta, Apple, etc.). With company fixed effects the compensation gap vanishes (exposed +0.04, p=0.15) and the career gap shrinks to -0.08 points (d about -0.06, p=0.048).
- AI/automation as a cause of job loss is almost never named in Glassdoor cons: strict "AI replace/cut" mentions are 22 reviews (0.14%) in exposed classes vs 35 (0.22%) in AI-positioned classes.

## Subreddit scope decision (Task 1a)

The file holds 230,520 posts in 793 communities (2025-01-01 to 2026-11-14). It is mostly NOT Bay Area (only 6.5% of posts are from Bay subs). Scope classes:

| scope | posts | decision |
|---|---|---|
| BAY (city/region subs: sanfrancisco 4,004; bayarea 3,658; SanJose 2,303; BayAreaRealEstate 1,151; oakland 977; OaklandCA 790; berkeley 653; eastbay 510; berkeleyca 454; plus 17 small ones; 26 subs total) | 14,914 | Bay Area analysis. Sports-team, food, news-aggregator and entertainment subs excluded even when place-named (SanJoseSharks, OaklandAthletics, OaklandFood, ...). |
| WORK_GEN (recruitinghell 6,210; antiwork 4,047; careerguidance 3,812; jobs 3,634; jobsearchhacks 1,712; usajobs 1,366; jobsearch 1,100; few small) | 22,442 | General worker-voice sample. NOT Bay Area; label it "general English-language work subreddits, US-skewed". |
| JOBS_OTHER_NICHE_OR_INTL (UKJobs, ausjobs, Germany_Jobs, singaporejobs, WebDeveloperJobs, DesignJobs, ...) | 28,566 | Side comparison only (AI-work share 2.8%). Not in headline series. |
| AI_TOPIC_SUBS (AIJobs, AIdaily_news, ...) | 1,406 | Excluded (topic-selected; would inflate AI share). |
| GENERAL_OTHER (personalfinance, UKPersonalFinance, AITA, worldnews, ...) | 163,192 | Excluded from headline series (AI-work share 0.28%; not work-focused, many non-US). |

## Task 1(b) Measure and hand-checked precision

Definition: a post counts as AI-and-work discourse if title+description (first 6,000 chars) contains an AI term (AI, ChatGPT, LLM, OpenAI, Claude, Copilot, etc.) in the title or at least twice in the text, AND matches a rule for one of four types. Rule order: (ii) actual displacement, (iii) AI in hiring/job search, (i) fear/anticipation, (iv) AI as workplace tool. The keyword candidate set was refined over four rounds of hand-checked samples. The first-round rules were too loose (on the "actual displacement" class only 4 of 9 hand-checked posts were right, because generic claims such as "jobs are being replaced by AI" matched). I tightened it to first-person or close-network reports ("I was laid off ... replaced by AI", "my friend's company replaced the team with AI"), which is why that class is small (20 posts in WORK_GEN+BAY).

Final hand-check (single coder, me; no inter-rater reliability, so approximate). Stratified sample of 104 posts from WORK_GEN+BAY (all 20 "actual" posts, 28 each for the other three classes):
- **Relevance** (post genuinely discusses AI in relation to jobs/work/hiring): 93.2% prevalence-weighted (actual 20/20, fear 24/28, tool 26/28, hiring 27/28). An earlier uniform random sample of 70 (before the final tightening of the "actual" rule) gave 90.0% relevance and 80.0% category-correct.
- **Category correct**: 87.9% prevalence-weighted. By class: hiring 92.9%, fear 85.7%, actual 70.0% (14/20), tool 64.3% (18/28; "tool" is a residual bucket whose errors are mostly really fear or displacement). Treat the actual/tool split as indicative.
- Precision is high; recall is lower (strict rules miss some displacement stories and a single passing AI mention is dropped by design). Counts are lower bounds: safe for trend and composition, not for levels.

Counts in WORK_GEN / BAY: hiring/search 558 / 11; fear/anticipation 243 / 11; tool 77 / 4; actual displacement 20 / 0.

## Task 1(c) Monthly series (share of posts in scope that are AI-and-work discourse)

"fixed-mix share" re-weights each month to the pooled subreddit mix of the seven core WORK_GEN subs, removing composition drift (the mix shifts a lot: r/usajobs goes from about 15 posts/month to over 200 in 2026). Raw and fixed-mix series agree. Monthly cells are small early on (Jan-Apr 2025: 231-318 posts, 8-16 AI-work posts per month, so about +/-2 points of sampling error). 2026-11 is a partial month (55 posts); do not read it.

{S_}
Trend tests (WORK_GEN, Jan 2025 - Oct 2026, 22,387 posts): pooled logit slope -1.9%/month odds (p=0.002); with subreddit fixed effects -1.3%/month (p=0.037). Interpretation: flat to mildly declining. The Feb 2026 spike (8.0%) and the Jun-Sep 2026 dip are within noise. The crawl composition changes massively: whole file x14 from Jan 2025 to Jul 2026, WORK_GEN x8, GENERAL_OTHER x15, BAY x15 at its Apr 2026 peak; any raw-count trend would be an artifact.

## Task 1(d) Occupation attribution (the key test)

Pool: displacement + fear posts in WORK_GEN+BAY (n=274: 20 strict-actual, 254 fear). Rules: own occupation from tight first-person patterns ("I'm a / I work as / laid off as ..."), else an occupation named in the title; a third fallback (first occupation named in the body) is low confidence and is NOT used for conclusions (hand-checked precision 35%, 9/26).

High-confidence attribution (self-ID or title; n=67 of 274; hand-checked precision 80%, 36/45):

| class | posts | share of 67 |
|---|---|---|
| SOFTWARE_ENG | 26 | 38.8% |
| PROF_EXPOSED (marketing, writing, design, accounting, HR/recruiting, analysts) | 18 | 26.9% |
| SKILLED_TRADE (mostly "AI-proof career" seekers, not displaced) | 7 | 10.4% |
| HEALTH_CLINICAL | 3 | 4.5% |
| SALES_BIZ | 3 | 4.5% |
| CLERICAL_ADMIN | 2 | 3.0% |
| DATA_ENG_ANALYTICS | 2 | 3.0% |
| EDUCATION | 2 | 3.0% |
| FRONTLINE_SERVICE | 2 | 3.0% |
| AI_DATA_WORK | 1 | 1.5% |
| PRODUCT_DESIGN | 1 | 1.5% |
| CUSTOMER_SUPPORT, AI_PRODUCER, OTHER_ENGINEERING, MANAGEMENT | 0 | 0% |

Grouped: AI-positioned (AI_PRODUCER, SOFTWARE_ENG, DATA_ENG) 42% (28); exposed (CLERICAL, CUSTOMER_SUPPORT, PROF_EXPOSED) 30% (20); in-person (FRONTLINE, TRADE, HEALTH) 18% (12). Only 4 of the 67 are strict actual-displacement posts (3 PROF_EXPOSED, 1 SOFTWARE_ENG), so actual-displacement attribution is anecdotal. Across all 20 strict-actual posts, occupation-bearing ones (including the weak body fallback) are PROF_EXPOSED 6, software 2, clerical 2, sales 2, data 1, health 1, none identifiable 6: directionally marketing/creative/translation/admin, low confidence.

Mention-rate view (any mention in displacement/fear posts vs any mention across all WORK_GEN posts; lift = ratio): software 30.7% vs 7.1% (4.3x), data 6.6% vs 1.3% (5.0x), AI_PRODUCER 1.5% vs 0.2% (7.8x), PROF_EXPOSED 30.3% vs 27.2% (1.1x), clerical 6.9% vs 4.6% (1.5x), customer support 3.3% vs 2.9% (1.1x), frontline 8.0% vs 9.0% (0.9x), trades 6.9% vs 2.4% (2.9x), health 9.1% vs 5.1% (1.8x).

Reading: (a) supports "junior professional/creative" exposure: PROF_EXPOSED is the second most named class (writers, marketers, designers, translators, accountants, recruiters). (b) Does not support clerical and customer support as what workers say they fear or experience: both are barely named (clerical 3%, support 0% of high-confidence posts; mention lift 1.1-1.5x). (c) Supports "not frontline in-person": frontline is named in 2 of 67 and is not over-represented (0.9x); trades appear as a refuge. Caveat: Reddit is young/tech/online, so software engineers are over-represented by construction; the lift column is the fairer comparison. Clerical and customer-support workers are probably under-sampled here, so their absence is weak evidence.

## Task 1(e) Job-search friction (WORK_GEN n=22,442 posts; BAY n=14,914 shown for scope)

| measure (hand-checked precision) | WORK_GEN share of all posts | BAY |
|---|---|---|
| ghosting / ghost jobs / fake postings (100%, 24/24) | 5.5% | 0.4% |
| application-volume talk: "N applications", "hundreds of applicants" (95.8%, 23/24) | 5.6% | 0.1% |
| ATS / AI screening / auto-reject / one-way or AI interview (87.5%, 21/24) | 5.0% | 0.2% |
| any of the three | 13.7% | 0.7% |
| entry-level / new-grad / intern context flag (70.8%, 17/24; noisiest) | 10.4% | 1.4% |

Entry-level job-search context vs other WORK_GEN posts (n=2,325 vs 20,117): ghosting 8.6% vs 5.1%; application-volume talk 11.7% vs 4.9% (2.4x); AI-screening 6.1% vs 4.8%; any friction 21.6% vs 12.7% (1.7x). AI-and-work discourse is 5.3% of entry-level-context posts vs 3.9% of the rest, and fear posts are 2.5% vs 0.9% (2.7x). Where applicants state a number, the median is 200 applications (IQR 74-500; 922 mentions; self-reported and selected). The AI-in-hiring share of WORK_GEN posts fell from 3.3% (Jan-Jun 2025) to 1.9% (Jul-Oct 2026); ghosting and volume talk are roughly flat at 4-7% a month. Friction talk is a stable feature of these subreddits, not a rising one.

## Task 2: Glassdoor

**(a) California filter.** The extracted file holds 175,138 reviews worldwide (not CA-only; the ~100k description does not match it). I kept rows whose `employee_location` ends in ", CA" (US state code): 95,464 reviews, 14,548 company names (14,500 after normalisation), Jan 2025 to 11 Nov 2026. Excluded: "Baja California", ", MD", ", PA" and other non-California codes. 42,311 (44.3%) are in a Bay Area city (9-county city list). Monthly volume is uneven: 8,787 in Oct 2025 vs 1,811 in Oct 2026. Top companies: Google 3,439; Meta 2,324; Apple 1,615; Amazon 1,519; Tesla 1,224; Starbucks 971; McDonald's 880; Target 787; Walmart 710; Northrop Grumman 652. Top titles: Software Engineer 4,710; Sales Associate 1,669; Senior Software Engineer 1,620; Manager 1,087; Cashier 1,009.

**Data issue found and handled.** Every sub-rating except `rating_overall` is coded 0 for "not rated" in 28-29% of reviews (about 27-32% per month through Jul 2026, falling to 2% in Sep 2026 and 0% in Oct-Nov 2026: a schema change). Treating 0 as a rating biases every sub-rating mean down (raw means look like 2.4 vs 3.6 overall) and fakes a late-2026 jump. I treat 0 as missing everywhere. Reviewers with sub-ratings may differ from those without; the post-Aug-2026 change in missingness is another reason to rely on within-period group comparisons.

**(b) Title classification.** Ordered keyword rules on `employee_job_title`, plus a tech-company rule for bare "Engineer". Coverage: 85.1% classified to a specific class; 3,340 (3.5%) missing/anonymous titles; 10,842 (11.4%) fell to OTHER (top: Intern 805, Associate 703, Internship 250, Senior Associate 211, Scientist 137, Specialist 120, Member of Technical Staff variants, Buyer, Contractor). Hand-checked class precision 92% (92/100 random classified reviews; errors such as "Quality Assurance", "Customer Success Manager", "Instructional Assistant"; two of those rules were patched after the check). Judgement calls: "Consultant" goes to SALES_BIZ, not PROF_EXPOSED; non-data "Analyst" goes to PROF_EXPOSED; retail "Sales Associate" is FRONTLINE_SERVICE; explicit annotator/rater/AI-trainer titles are AI_DATA_WORK (only 99 reviews); "Content Moderator" is PROF_EXPOSED. MANAGEMENT is the largest class (15.4%).

Class sizes (reviews): MANAGEMENT 14,674; SOFTWARE_ENG 13,083; FRONTLINE_SERVICE 11,882; OTHER 10,842; PROF_EXPOSED 9,995; SALES_BIZ 8,308; OTHER_ENGINEERING 6,267; CLERICAL_ADMIN 3,349; MISSING 3,340; HEALTH_CLINICAL 2,784; PRODUCT_DESIGN 2,498; CUSTOMER_SUPPORT 2,231; DATA_ENG_ANALYTICS 2,104; SKILLED_TRADE 1,717; EDUCATION 1,333; AI_PRODUCER 958; AI_DATA_WORK 99. Groups: AI-POSITIONED = AI_PRODUCER+SOFTWARE_ENG+DATA_ENG_ANALYTICS (16,145); EXPOSED = CLERICAL_ADMIN+CUSTOMER_SUPPORT+PROF_EXPOSED (15,575); IN_PERSON = FRONTLINE+TRADE+HEALTH+EDUCATION (17,716).

**(c) Sub-ratings by class** (means; 0 treated as missing; rating_overall is 1-5):

{C_}
**AI-positioned vs exposed**: effect sizes and tests. "diff" is AI-positioned minus exposed; Cohen's d is positive when AI-positioned is higher; the last two columns are the exposed-class coefficient (Exposed minus AI-positioned) after controls (current/former, tenure, Bay Area, month) and then with company fixed effects (SEs clustered by company). career_gap and comp_gap are (sub-rating minus overall rating), a within-reviewer measure that strips out general happiness.

{A_}
Reading: the raw gap is real but small-to-moderate (comp d=0.25, career d=0.20, overall d=0.17; all p<1e-40) and mostly between-company sorting, since the controlled and fixed-effect estimates are small or reversed in sign. Within company, exposed-class reviewers rate career opportunities 0.08 points lower (d about -0.06, p=0.048) and overall 0.06 lower (p=0.017), but compensation 0.04 points higher (p=0.15), and compensation relative to overall rating is higher for exposed (+0.07, p=0.01). So the data do not show exposed-class workers seeing their careers or pay diverge from AI-positioned peers; they show a modest within-firm career-opportunity deficit. Class-vs-all-other-classes effect sizes (Cohen's d, base/glassdoor_class_vs_rest.csv) for career / compensation: AI_PRODUCER +0.29 / +0.36; SOFTWARE_ENG +0.22 / +0.25; DATA_ENG +0.16 / +0.23; PROF_EXPOSED +0.07 / +0.08; CUSTOMER_SUPPORT -0.13 / -0.13; CLERICAL_ADMIN -0.11 / -0.17; FRONTLINE_SERVICE -0.24 / -0.34; AI_DATA_WORK -0.65 / -0.43 (n=99). So raw differences rank AI producers and software engineers highest, clerical and support below average, and PROF_EXPOSED (the "junior professional" class) at or slightly above average: pay level and seniority, not AI exposure, drive these rankings (frontline is lowest of the big classes).

**(d) Trends within 2025-2026.** Quarterly group cells are 326 to 3,814 reviews; monthly group cells are 96 to 1,632 (1 of 46 below 100), so I display quarters and half-years (base/glassdoor_class_trend_quarterly.csv, _monthly.csv). Findings: overall ratings of AI-positioned classes fell (3.88 in 2025H1 to 3.68 in 2026H1; slope -0.009/month with company FE, p=0.016) while exposed ones were flatter (3.63 to 3.60). Career and compensation slopes for AI-positioned are slightly negative (-0.004/month, p=0.08 and p=0.04) with no differential for exposed. Senior-leadership ratings of AI-positioned classes fell faster (-0.012/month, p=0.001; extra exposed slope +0.007, p=0.09). The only divergence is AI-positioned classes getting a bit less happy, which runs against an "exposed fare worse" story. Oct-Nov 2026 cells are partial and affected by the schema change.

**(e) Text analysis of review_cons** (denominator: all 95,464 reviews; every review has cons text). Rates by class, %:

{T_}
Hand-checked precision (single coder): layoffs/restructuring 90.6% (29/32); understaffing/work-of-two 91.4% (32/35); workload 93.8% (30/32; counts any workload mention including neutral ones); AI/automation mention 94.3% (33/35; a mention, not a threat); strict AI replace/cut 57.1% strict, 67.1% with half credit for ambiguous cases (n=35; low, treat as a rough upper bound); offshoring/outsourcing (displacement-oriented rule) 87.5% (28/32).

**Job-enlargement test.** Hypothesis: exposed workers absorb more work rather than being fired. Results:
- Understaffing / "work of two": 1.30% of exposed reviews vs 0.46% of AI-positioned (2.8x). With company fixed effects the exposed-minus-AIP gap is +0.30pp (se 0.14, p=0.033). In-person classes are higher still (2.93%; health clinical 4.85%), so understaffing is not specific to AI-exposed white-collar work.
- Workload: 3.80% exposed vs 1.66% AI-positioned (+1.27pp with company FE, p=3e-6); clerical 4.84%, customer support 4.08%, health 4.27%.
- Layoff mentions run the other way: 7.39% AI-positioned vs 5.16% exposed vs 0.87% in-person; exposed minus AIP with company FE +0.39pp, p=0.42 (not different).
- "Survivor workload": among reviews that mention layoffs, 5.6% of exposed also mention workload (45 of 804) vs 1.5% of AI-positioned (18 of 1,193); workload or understaffing together 6.6% (53) vs 2.6% (31). Layoff-and-workload/staffing co-mention is +0.18pp for exposed (company FE, p=0.049).
- Verdict: directionally consistent with job enlargement (heavier staffing and workload complaints in exposed classes; layoff-linked workload 2.5-4x higher than for software workers), but small in absolute terms (1-4% of reviews), shared with in-person classes, and not attributable to AI: only 0.14% of exposed reviews cite AI as a replacement or cut mechanism, and AI/automation is mentioned in 0.81% of exposed-class reviews vs 2.17% of AI-positioned ones (rising: AI-positioned 1.0% in 2025H1 to 3.6% in 2026H1; exposed 0.4% to 1.3% to 2.2% in Jul-Nov 2026). Weak, non-specific support for job enlargement; no support for AI-attributed enlargement.
- Offshoring/outsourcing: 0.48% AI-positioned, 0.32% exposed, 0.58% customer support, 0.01% in-person; exposed vs AIP gap -0.13pp, p=0.22. It is mostly a software/tech complaint here.
- Bay Area reviews only (n=42,311): layoffs 7.8% AI-positioned vs 6.2% exposed; understaffing 0.4% vs 1.0%; AI mention 2.4% vs 1.4%; career rating 3.66 vs 3.45; compensation 3.87 vs 3.65. Same pattern as statewide.

**(f) Company table.** `base/glassdoor_company.csv`: one row per `company_norm` (14,500 rows; 1,363 companies with >=10 reviews, 506 with >=30; 47 normalised keys merge two or more spellings). `company_norm` rule, exactly: lowercase; delete "." and apostrophes; replace every other non-alphanumeric run with a space; drop whole tokens in {{inc, llc, corp, co, ltd, group, holdings, the}} wherever they appear; join the remaining tokens with no separator. Examples: "AT&T Inc." -> att; "The Home Depot" -> homedepot; "McDonald's" -> mcdonalds; "Kaiser Permanente, Inc." -> kaiserpermanente. Implementation: scratchpad/code/voice_norm.py, function `company_norm`. Columns: review counts (all, Bay Area, 2026), first/last month, means of the seven ratings (0 treated as missing), class-mix shares, cons-text mention rates. Most companies have fewer than 10 reviews; join on company_norm but threshold or weight by n_reviews.

## Hand-checked precision, all measures

Single coder (me), random samples, 95% Wilson intervals. Reddit AI-work classes were checked on the final rule set (the n=70 uniform sample predates the final tightening of the "actual" rule); Glassdoor text rules were checked on the final regexes, except understaffing, checked just before a small fix that removed false matches on "little people skills".

{P_}
## Task 3: What these sources can and cannot establish

- Both are self-selected. Reddit skews young, tech, online and US/UK/Canada/India; the work subreddits (recruitinghell, antiwork) are venues for grievance, so shares of 3-5% are not population rates. Glassdoor reviewers skew very happy or very unhappy (rating_overall: 28,788 five-star vs 9,710 one-star, with only 9,362 two-star), cover employers Glassdoor tracks, and carry no worker weights. Neither source has race, so nothing here speaks to racial distribution of exposure.
- They corroborate mechanism (which friction, which occupations workers name, whether reviewers describe job enlargement). They do not measure incidence of layoffs, displacement or wage loss, and cannot be scaled to the Bay Area workforce.
- Reddit is not Bay Area (6.5% of posts are from Bay subs, and those carry almost no work-and-AI content). Glassdoor "California" is by reviewer location string; 44% are in Bay cities. Any Bay-specific statement must use the Bay-only Glassdoor rows or acknowledge n=26 on Reddit.
- Occupation attribution on Reddit is thin (67 reliable posts) and keyword-based. Glassdoor titles are self-reported and 14.9% were unclassifiable (OTHER or missing).
- Keyword measures have measured precision but unmeasured recall. Group and time comparisons assume wording does not vary by group (it may: frontline workers rarely write "restructuring").
- Single-coder hand checks; no inter-rater reliability.
- No individual is reported; outputs are aggregated to subreddit scope, month, company or occupation class. The posts file carries pseudonymous post IDs and classifications only, with no text and no author fields.

## Which quantitative hypotheses this evidence supports or contradicts

- Supports: (1) AI entering through hiring and job-search friction (the largest AI-and-work theme; entry-level posters report 2.4x the application-volume talk); (2) junior professional/creative exposure (PROF_EXPOSED is the second most-named class among displacement/fear posts); (3) heavier workload and understaffing complaints in exposed classes (weak, not specific to AI).
- Contradicts or does not support: (1) a rising trend in worker AI-displacement talk (flat to down, Jan 2025 - Oct 2026); (2) clerical and customer support as the classes workers name themselves (3% and 0% of reliably attributed posts; these workers are probably under-sampled on Reddit); (3) exposed classes' career/pay ratings diverging from AI-positioned classes (no divergence; the gap narrowed in 2026); (4) any Bay-specific Reddit signal. Consistent with the quantitative side: frontline in-person work is not where workers locate AI displacement.
- Cannot test: incidence, wage effects, race, causal firm-level links (the company table is provided for joining to postings and WARN notices).

## Files

base/reddit_ai_posts.csv (2,267 AI-and-work posts across all scopes with scope/month/category/occupation fields; filter scope to WORK_GEN or BAY), base/reddit_monthly.csv (by scope and month, incl. friction counts), base/reddit_monthly_reweighted.csv, base/glassdoor_ca.parquet (95,464 CA reviews; no free text), base/glassdoor_company.csv, base/glassdoor_class_ratings.csv. Supporting: base/glassdoor_aip_vs_exposed.csv, glassdoor_class_vs_rest.csv, glassdoor_class_trend_quarterly.csv and _monthly.csv, glassdoor_text_rates_by_class.csv and _by_half.csv, voice_precision_handchecks.csv. Code: scratchpad/code/voice_*.py.
'''
open(S+'/out/voice_findings.md','w').write(memo)
print(len(memo))
