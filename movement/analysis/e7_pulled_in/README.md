# E7: Who is pulled in? Relocation recruiting (Indeed) and arrival stories (Reddit)

**Question.** E3 and E4 show low-wage workers being priced out. Who is being pulled in to
replace them, and what do newcomers say about themselves?

> **Reddit labels were made by an LLM annotator (Claude), not by humans.** The team must
> hand-check `labels/verify_sample.csv` (30 items, with the human columns left blank)
> before presenting the Reddit results.

## Run
```bash
python3 run_all.py            # uses the cached arrival pool and the saved labels (~1 min)
python3 run_all.py --rescan   # also re-scans the raw 5.2 GB Reddit CSV (~2 min)
```
| step | script | what |
|---|---|---|
| 1 | `scripts/01_scan_reddit.py` | Streams `reddit_posts-003.csv` with duckdb (all_varchar, max_line_size=30000000, ignore_errors, parallel=false). Flattens posts and **nested comments** using the same walk as E4: 230,520 posts and 3,413,197 comments. Applies the arrival regex and keeps **1,368** de-duplicated candidates. Usernames are never selected. |
| 2 | `scripts/02_relocation_flags.py` | Adds relocation, degree, remote/hybrid and broad-occupation flags to E3's `postings_with_pay.parquet`. E3's parsed hourly pay, county/metro and low-wage occupation groups are reused unchanged. |
| 3 | `scripts/03_relocation_analysis.py` | Relocation tables and figures |
| 4 | `scripts/04_sample_for_labeling.py` | Frozen stratified 300-item annotation sample (not re-run by `run_all`) |
| 5 | `scripts/05_arrivals_analysis.py` | Compiles the labels, measures regex precision, profiles arrivals, validates the money extractor, compares with E4 leavers and writes the verify sample |
| 6 | `scripts/06_agreement.py` | Agreement between the two blind labeling passes |
| – | `scripts/annot_tools.py`, `codebook.md` | Annotation display helper and codebook |

---------------------------------------------------------------------------------------
## 1. Relocation recruiting (Indeed, California, 140,816 postings)

**Flag.** A posting counts as offering relocation if either:
- Indeed's structured benefit tag says "Relocation assistance" (2,224 postings), or
- a description sentence offers relocation help (2,411 postings): relocation assistance, package, bonus, stipend, reimbursement or allowance; "relocation available/provided"; "offer relocation"; "eligible for … relocation".

A posting is not counted if the sentence is negated ("no relocation", "relocation is not available", field-style "Relocation Benefits: NO" or "Not Authorized"). A benefit tag is overridden if the text explicitly refuses relocation and never offers it.

That gives **4,635 postings in total**, of which 4,571 have a known region. The flag counts **conditional** offers too ("may be available", "might be eligible"). `relo_firm` keeps only the 1,611 un-hedged offers.

Note: an earlier draft of the regex matched 3,635 postings. That draft missed Apple's "might be eligible … as well as relocation" boilerplate and counted field-style "Relocation: No" as an offer. Both were fixed after hand-check round 1.

**Hand checks** (`outputs/relocation_hand_checks.csv`; the agent read each snippet):
- **Round 1 (development):**
  - 30 hits: 29 were true offers. The one false positive was a field-style negation split across a newline; this is now fixed.
  - 20 non-hits that mention "relocat": 15 were correct non-offers. These were mostly Indeed's "Ability to relocate: … (Required)" screening question, which asks the worker to move without offering help. The other 5 were missed conditional offers (Apple ×4, "relocation or living-out allowance"); both patterns were added.
- **Round 2 (fresh 30 hits, drawn after the fixes): 30/30 are real offers.** However, **15 of the 30 are conditional**, and 11 of those 30 are Apple's single boilerplate sentence.

**Pay tiers** use E3's *posted* hourly-equivalent midpoint (`pay_mid`), not imputed pay. Unknown-location postings are dropped.

| posted pay | Bay: n | Bay: any offer | Bay: firm only | Bay: company-balanced | Rest of CA: any offer |
|---|---|---|---|---|---|
| < $25/h | 7,291 | **0.10%** (7 postings) | 0.05% | 0.16% | 0.10% (31 / 29,527) |
| $25–40/h | 7,276 | 1.2% | 0.6% | 1.0% | 1.2% |
| $40–60/h | 5,445 | 3.5% | 1.9% | 3.0% | 4.0% |
| $60+/h | 20,449 | **8.4%** (1,720) | 2.4% | 4.8% | 9.3% |
| no posted pay | 7,629 | 1.9% | 0.6% | 1.1% | 1.0% |

**Headline: Bay employers offer relocation help on 8.4% of $60+/h postings, against 0.10% of under-$25/h postings (7 of 7,291), roughly 90×.**
- The gradient survives every check, though the ratio shrinks:
  - **Firm offers only:** 2.4% vs 0.05%.
  - **Company-balanced** (each employer weighted equally, which neutralises Apple, the source of 928 of the Bay's 2,144 relocation postings): 4.8% vs 0.16%.
  - **Dropping the top 5 relocation posters statewide** (Apple, Northrop Grumman, OpenAI, Genentech, Hadrian): 3.4% vs 0.10%.
- **Within a pay tier, the Bay is not more generous than the rest of CA.** The Bay's higher overall rate (4.5% vs 2.7%) comes from its pay mix: 51% of Bay postings with posted pay are $60+/h, compared with 21% in the rest of CA.

**Profile: relocation vs non-relocation postings, Bay only** (`outputs/relocation_profile.csv`):

| | relocation postings | other postings |
|---|---|---|
| Median posted pay | $102/h | $57.5/h |
| Share at $60+/h | 86% | 49% |
| Share under $25/h | 0.3% | 19% |
| Mentions a bachelor's degree or higher | 48% | 30% |
| Mentions a master's or PhD | 31% | 15% |
| Mentions a PhD | 16% | 8% |

**By occupation group** (`relocation_by_occupation.csv`, `figs/relocation_by_occupation.png`). Groups come from a title regex; E3's 10 low-wage groups are pooled.

| occupation group (Bay) | offer rate |
|---|---|
| Physicians / clinicians | 16.8% |
| Engineering / science | 9.0% |
| RN / therapists | 7.2% |
| Tech / software / data | 6.8% |
| Management | 3.7% |
| **E3's low-wage groups** (cashier, crew, cook, warehouse, janitor, caregiver, driver, security, medical assistant, CNA) | **0.12%** (5 of 4,176) |

**By work mode.** Remote postings almost never offer relocation (1.2%). Hybrid postings (4.9%) and onsite/unstated postings (4.5%) offer it at similar rates.

**By degree.** The offer rate rises with the degree mentioned: none 3.3%, bachelor's 5.4%, master's 8.2%, PhD 8.8%.
- The degree regex flags *mentions*, including "preferred". `degree_req_sentence` marks mentions that sit in a sentence containing required/minimum/must.

**Reading.** Employers pay to bring in degree-holding, $60+/h workers (clinicians, engineers, ML/tech staff) and almost never pay to bring in the low-wage workers E3 shows being priced out. Low-wage postings recruit locally. They often add the screening question "Ability to relocate: … (Required)", which hands the cost of the move to the worker.

---------------------------------------------------------------------------------------
## 2. Arrival stories (Reddit)

**Pool.** Regex tiers, recall-oriented:
- **A:** first-person subject + move verb + "to/into" + a Bay place.
- **B-place:** "new to / transplant to / just arrived in" + a Bay place.
- **B-implicit:** "just moved here / recent transplant / new to the area", in Bay subreddits only.
- **C:** offer / admission / position in a Bay place, plus a move word.

This gives 1,368 items. 1,279 of them are from Bay subreddits, because people rarely name the Bay as a destination in finance or jobs subreddits.

**Labels.**
- **Sample:** 300 items stratified by tier (150 A / 70 B-implicit / 40 B-place / 40 C).
- **Annotation:** labeled by the agent (an LLM) using `codebook.md`. Labels are ARRIVED / PLANNING / WITHIN_BAY / OTHER, plus reasons, household, era, origin, occupation, stated money and destination.
- **Result:** ARRIVED 161 · PLANNING 54 · WITHIN_BAY 18 · OTHER 67.
- **Consistency check:** a separate fresh-context LLM instance given only the codebook re-labeled 80 items blind. **κ = 0.90 for 4 classes** (raw agreement 94%), and κ = 0.88 for arrival vs not. Of the 5 disagreements, 3 are PLANNING→OTHER on vague plans. This is one model checking itself; it says nothing about validity against human judgment.

**Regex precision** (share labeled ARRIVED or PLANNING, `arrival_regex_tier_precision.csv`): A 0.68, B-implicit 0.84, B-place 0.85, C 0.50. Weighting each tier's precision by its pool size gives an estimated **~1,000 arrival items in the pool**.
- **No classifier was trained.** The labels come from a regex-filtered pool with 72% positives. A held-out test of about 60 items would say little beyond the tier precision above, so the analysis stays descriptive.

**Who arrives?** Counts are among the 215 arrival items. "Recent newcomers" are the 154 items that are recent (about 5 years or less) or planning.

| field | recent newcomers (n = 154) |
|---|---|
| Stated reason | **none stated 60%**, other job / transfer / offer 26%, school 6%, returning 6%, tech/startup explicitly 3%, partner/family 2% |
| Household | unknown 54%, couple 18%, single 18%, family with kids 8%, roommates 2% |
| Origin | unknown 60%, **another US state 27%**, abroad 6%, elsewhere in CA 6% |
| Occupation (when stated) | unknown 82%; student 6%, tech 5%, service/trades/hourly 5% |
| Destination (all 215) | East Bay 34% (mostly Oakland/Berkeley), SF 29%, South Bay 17%, unspecified 17%, Peninsula 2% |

**Money.**
- Only **10% of arrival items state any money figure.**
- **Stated annual pay or income** (9 items): $79k, 135k, 140k, 150k (household), 170k, 200k, 300k (TC), 360k (household), 380k. The median works out to about **$82/h**, and only one figure is below $60/h ($79k, about $38/h).
- **Stated rent budgets** (11 items): $1,500–5,000/month, median $2,000. Several are rooms with roommates.
- A few arrivals describe low-wage or hourly work: an airport wheelchair agent transferring in with a $1,900 studio, a barista, an electrician-helper offer three hours away, and a Job Corps fleet mechanic. They are the exception.
- **The rule-based money extractor** (`extract_money`), scored against the LLM labels: salary precision 0.57 and recall 0.89; rent precision 0.36 and recall 0.36. It is **not reliable enough for pool-level money statistics**, so money results come from the labels only.

**Arrivals vs E4 leavers** (`reasons_arrivals_vs_leavers.csv`, `figs/reasons_arrivals_vs_leavers.png`). Shares are multi-label; arrivals n = 215, E4 gold exits n = 142.

| reason | arrivals | leavers (E4) |
|---|---|---|
| Job / career | **24%** | 10% |
| Housing cost | **0%** | 12% |
| Other cost of living | 0% | 11% |
| Safety / quality of life vs lifestyle | <1% | 15% |
| Partner / family | 2% | 7% |
| Returning to the Bay | 5% | – |
| No reason stated | 66% | 47% |

- **Arrivals talk about jobs; leavers talk about cost and quality of life.**
- **No arrival cited housing cost as a reason.** Cost does come up as a *problem* after arrival (rent budgets, sticker shock), just not as a reason for coming.
- E4's "other" category (16%) bundles school, college, health, visa and retirement, so the school row cannot be compared directly.

---------------------------------------------------------------------------------------
## 3. Neighbourhood amenity change (Google Maps): **not done**
Skipped for time. The optional ZIP-level comparison of Google Maps price levels, category mix and review language between high- and low-premium E2 ZIPs was not attempted.

## Caveats
- **Indeed is posting-level, not hire-level.** The relocation rate counts offers, not moves. Many offers are conditional boilerplate, and one employer (Apple) dominates the Bay count, which is why the firm-only and company-balanced versions are reported. Pay is the *posted* midpoint: E3's parser, with "From/Up to" values as single points.
- **Occupation and degree flags are regex-based.** The broad-occupation rules are unvalidated, apart from E3's low-wage rules, which were hand-checked in E3.
- **The Reddit results are a selection on a selection.** Reddit users are not a random sample of arrivals, and the regex pool misses arrivals told without move or place words. Most items state no reason, income or occupation, so the shares rest on small numbers: 9 stated salaries.
- **The labels are LLM labels.** Human verification is still to do.
- **E4 comparison:** the codebooks differ (arrival reasons were coded with different categories), so the comparison is indicative only.

## Ethics
- No usernames are ever read.
- Outputs contain item IDs, codes and the agent's paraphrases, not quotes.
- `labels/verify_sample.csv`, `labels/sample_to_label.csv` and `data/arrival_pool.parquet` contain post text for verification only. **Do not quote them in slides.**
- Company names in the Indeed tables are employers, not people.
