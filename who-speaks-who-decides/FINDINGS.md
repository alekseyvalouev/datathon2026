# Who speaks, who decides: public comment and housing approvals at the San Francisco Planning Commission

**Question.** When a housing project goes before the San Francisco Planning Commission, who shows up to speak, and does it change what happens to the project?

**Thesis.**
- Outright denial is rare (about 4% of site-specific projects). Opposition shows up as divided votes, extra hearings and modifications, not as refusals.
- Staff recommendation explains most outcomes. Public comment adds clear predictive power for only two outcomes: a non-unanimous vote and a drawn-out hearing sequence.
- The speakers are not one public. Parties to a case (sponsors, review requestors) and advocacy groups hold fixed positions; neighborhood and tenant groups vary by project; three quarters of comments carry no recorded affiliation and mostly come from people who appear once.
- Since 2020 the Commission intervenes less and hears fewer large projects. The data cannot separate state law, membership change and the market slump as causes.

Every number below traces to a table in `results/` produced by a script in `code/`; tags such as [H8] point to the Methods table at the end. Methods, hand checks and caveats are in `memos/`. A log of errors made and fixed during the work is in `memos/06_corrections_log.md` and should be read before quoting anything.

**Scope.** One city, one commission. Nothing here is Bay Area-wide. All relationships are associations in observational records, not causal estimates.

**Data.**
- Alexander Sahn, *San Francisco Planning Commission Public Comment* (GitHub `alexandersahn/sf-planning-public-comment-data`, data CC BY 4.0): 1,252 meetings, 25,560 agenda items, 73,002 comments, January 1998 to March 2026. Cite: Sahn, "Public Comment and Public Policy," *AJPS* 69(2), 2025.
- Zillow property extract from the datathon pack, **parts 1 and 3 only** (69,581 of about 148,000 Bay Area rows; 7,410 in San Francisco, 3,428 usable sales). Part 2 was never available to this workstream.
- No other datathon dataset is used.

---

## Headline numbers

| | Finding | Experiment |
|---|---|---|
| **90% / 3.8% / 5.5%** | Share of 1,803 site-specific projects with testimony (first heard 2005-2023) that end approved / disapproved / stalled (continued and never returned, continued indefinitely, withdrawn or deadlocked) | H8 |
| **0.58 → 0.67** | Test AUC for predicting a split Commission vote, staff recommendation and case type alone against the same plus comment counts (1,569 items 2018-2026, 345 split; gain 95% interval +0.06 to +0.13) | H11 |
| **38% vs 90%** | Share of votes cast on the pro-project side in 235 split votes since March 2020: three Board-President appointees against seven commissioners coded as mayoral appointees (six verified) | H13 |
| **54% → 35%** | Share of discretionary-review cases where the Commission took review: 2014-17 against 2024-26 | H13 |
| **0.55 vs 0.23** | Macro-F1 for classifying a spoken comment as support / oppose / neutral from the clerk's note: TF-IDF logistic model against majority class (7,387 human-marked test comments, 2021 onward) | H2 |
| **97%** | Share of decided items where the Commission's direction matches the staff recommendation (4,156 items) | H4 |

---

## 1. What the data is, and what it is not [H1]

- 62,735 spoken comments parsed from minutes (1998 onward) and 10,267 written comments from hearing packets (2017-2024).
- **Three label sources.** Positions come from the commission secretary's own mark (37,612 comments), a classifier trained on those marks (6,119), speaker role (854) and LLM coding of written comment (10,267). Only the secretary's marks are human labels.
- **Spoken text is the secretary's summary, not a transcript.** Half of spoken comments with text are five words or fewer. Written comments are real prose (median 276 words) but 43% belong to organised letter campaigns.
- **Affiliation is sparse.** Only 23% of support/oppose comments on site-specific projects carry a role label. The organisation's name is recorded on 2% of neighborhood-association comments.
- **The "housing" keyword flag is loose.** It catches legislation, informational briefings, hotels and chain stores. Analyses from section 3 on use a stricter "site-specific" filter (2,915 projects). See corrections log.

## 2. Stance of a comment is hard to read from the clerk's note [H2, H3]

Train on comments through 2019, test on 2021 onward, secretary-marked rows only.

| Model | Accuracy | Macro-F1 |
|---|---|---|
| Always "support" | 0.530 | 0.231 |
| Keyword rule | 0.586 | 0.324 |
| TF-IDF word + character n-grams, logistic regression | 0.645 | 0.549 |
| Same, explicit stance words removed | 0.623 | 0.529 |
| + speaker role, calendar section, case type | 0.643 | 0.551 |
| + project description text, comment length, speaking order | 0.658 | 0.561 |
| Context only, no comment text | 0.512 | 0.415 |
| Support vs oppose only (neutral dropped), full model | 0.793 | 0.780 |

- **No label leakage.** Only 20% of test comments contain an explicit stance word and removing those words costs 0.02 macro-F1.
- **Context adds almost nothing** (+0.01 macro-F1). This is a null result: the project description and speaker role do not rescue short notes such as "Family housing".
- **Subgroups.** Accuracy 0.83 on discretionary-review items against 0.63 on the regular calendar; 0.46 for neighborhood-association speakers and 0.40 for tenant-association speakers; falls from 0.69 (2021) to 0.57 (2025) with the text-only model.
- **Cross-channel.** The spoken-comment model agrees with the LLM labels on 81% of 5,877 non-campaign written comments, but macro-F1 is 0.54 because it predicts a "neutral" class the written labels do not contain. Those labels are not human, so this is agreement between two models.
- **Not done:** no transformer was trained, and no written comments were hand-labelled.

## 3. Denial is rare because projects are filtered elsewhere [H4, H8]

- **Staff rarely bring a "no".** Staff recommended disapproval on 1.7% of decided items since 2005. The Commission's direction matched staff on 97.3% of 4,156 items. Of 124 disapprovals, 76 went against a staff approval recommendation; of 83 staff disapproval recommendations, the Commission approved 35.
- **Final state of 1,803 site-specific projects with testimony** (corrected classifier): approved 90.0%; disapproved 3.8%; continued and never returned 2.3%; continued indefinitely 1.8%; withdrawn 1.2%; no action recorded 0.4%; review request withdrawn, project proceeds 0.3%; deadlocked vote 0.2%.
- **Large housing is almost never refused.** Among about 350 projects of 10 or more homes, one was disapproved; 4-6% stalled. Small non-review projects have the highest disapproval rate (5.3%).
- **What gets disapproved is discretionary.** Of 142 disapproved agenda items: 78 conditional-use requests, 19 code amendments, 15 variances. Projects that merge, remove or convert existing homes are disapproved 9.1% of the time against 2.5% for the rest.
- **Most stalls are not Commission decisions.** Of 85 stalled projects (after collapsing duplicate batches), 47 ended on the continuance calendar (postponements scheduled in advance), 28 were continued or withdrawn from the regular calendar with no recorded hearing, and 10 were heard and then continued. The records do not say who asked for each postponement.
- **Legal context (outside sources, not tested here).** Under the state Housing Accountability Act a city can refuse a zoning-compliant housing project only with written findings of a specific, unmitigable health or safety impact ([CalHDF explainer](https://calhdf.org/?p=18962)). Before a hearing, sponsors must hold a pre-application meeting and respond to the Planning Department's plan check letter ([SF Planning project application packet](https://sfplanning.org/sites/default/files/forms/PRJ_InfoPacket.pdf)). Pre-hearing attrition is outside this dataset.
- **Limit.** The stall classifier was rebuilt twice (see corrections log). A hand check of 14 stalled projects on an intermediate version found about two doubtful; the final version was not hand-checked.

## 4. Opposition buys delay and division, not denial [H5, H8, H11]

**Predicting outcomes from the first hearing with testimony** (3,439 projects; train through 2016, test 2017-2023, n=1,365). Baseline is logistic regression on staff recommendation and case type.

| Target | Test rate | Baseline AUC | + size | + size + comments | Gain from comments (95% interval) |
|---|---|---|---|---|---|
| Two or more further hearings | 11% | 0.62 | 0.61 | 0.70 | +0.05 to +0.11 |
| Not decided at first hearing | 23% | 0.75 | 0.77 | 0.80 | 0.00 to +0.05 |
| Over 90 days or never decided | 20% | 0.77 | 0.80 | 0.80 | −0.02 to +0.03 |
| Never reached a final vote | 10% | 0.79 | 0.84 | 0.84 | −0.02 to +0.03 |
| Modified or review taken | 34% | 0.70 | 0.73 | 0.72 | −0.04 to +0.02 |
| Disapproved | 3% | 0.72 | 0.75 | 0.80 | −0.01 to +0.11 |

- **Comments matter for drawn-out hearings only.** Four of six targets are nulls.
- **Zillow neighborhood price adds no predictive power for any target.** Null.
- **Limit.** This table was run on the looser population that still includes legislation and policy items, and its "never reached a final vote" and "modified" targets use the first-generation classifier. It has not been rerun on site-specific projects.
- **Where the delay model fails.** AUC 0.62 on discretionary-review cases against 0.79 on other housing; 0.68 for projects with six or more opponents against 0.87 with none; at one threshold it catches 26% of slow projects in the priciest third of neighborhoods and 44% in the cheapest.

**Split votes** (4,206 decided items with a recorded vote; 22% not unanimous).

| Opposing comments | Items | Split vote | Two or more nays | Disapproved |
|---|---|---|---|---|
| 0 | 2,805 | 18.5% | 8.1% | 1.7% |
| 1-2 | 753 | 23.4% | 8.9% | 2.7% |
| 3-5 | 335 | 33.1% | 13.1% | 3.3% |
| 6-10 | 174 | 38.5% | 21.8% | 8.6% |
| 11+ | 139 | 48.2% | 30.2% | 15.8% |

- Density-bonus projects split 46.5% of the time (n=86) against 21.8% for other items.
- Predicting a split vote: AUC 0.575 (staff recommendation and type) → 0.671 with comment counts; comments alone 0.616.

**Stalls and unaffiliated opposition** (1,541 projects after collapsing batches): stall rate 3.7% with no unaffiliated opponents at the first hearing, 9.1% with one or two, 7.9% with three to five, 8.4% with six or more. Adjusted odds ratio per log-unit of unaffiliated opposition 1.61 (1.21-2.07); per log-unit of unaffiliated support 0.43 (0.27-0.66). Projects where the sponsor team spoke at the first hearing have odds ratio 0.31 (0.17-0.54) of stalling.

## 5. Who speaks [H6, H7, H9]

13,413 support/oppose comments on 2,915 site-specific projects.

| Speaker type | Comments | Support share | Gap vs others on the same project |
|---|---|---|---|
| No affiliation recorded | 10,290 | 59% | −1 point |
| Project team (sponsor, architect) | 1,227 | 98% | +40 |
| Discretionary-review requestors | 561 | 2% | −33 |
| Neighborhood associations | 431 | 26% | −25 |
| Construction trades | 229 | 86% | +15 |
| Pro-housing advocacy, YIMBY, SPUR | 251 | 94% | +21 |
| Tenant associations | 136 | 43% | −6 |
| Anti-displacement and identity groups | 114 | 27% | −15 |

- **Review requestors and project teams are parties, not opinion samples.** Their stance follows from their role. A review requestor is the neighbor or organisation that asked the Commission to take a second look at an otherwise permitted building permit ([SF Planning DR packet](https://sfplanning.org/sites/default/files/forms/DRP_InfoPacket.pdf)).
- **Fixed versus conditional positions.** Pro-housing groups support 81-98% across every project type. Neighborhood associations support 17% of the time on large mixed-income projects and 43% on large projects with no affordability mention; 16% in the priciest third of neighborhoods and about 30% elsewhere. Tenant associations support 27% where demolition is involved and 52% where it is not. Several cells rest on 15-50 comments.
- **Review requestors are one-time participants; neighborhood associations are a small set of regulars.**

| | Review requestors | Neighborhood associations |
|---|---|---|
| Comments | 563 | 467 |
| Projects (of 1,897 with comments) | 405 | 292 |
| Distinct people | 416 | 82 |
| People seen on one project only | 91% | 40% |
| Comments from people on 3+ projects | 10% | 84% |

- **The unaffiliated majority** (10,706 comments, about 6,200 identifiable people): 37% of comments come from people who appear once in 28 years, 19% have no usable name, 8% come from people with 21 or more comments. 86% of identifiable people commented on one project only. In the clerk's note, 27% mention living nearby (54% support), 4% identify as tenants (31%), 4% as property owners (35%); two thirds give no cue. 48% of these comments fall on 123 of 1,423 projects.
- **Some unaffiliated turnout is organised.** Campaign emails are 88% supportive against 43% for other emails; several of the highest-turnout projects are 89-94% supportive.
- **Repeat speakers are more supportive, not less.** Unaffiliated people with 6-20 comments support 68% of the time against 60% for one-time speakers. The research notes report the opposite pattern in Boston-area towns.
- **Limit.** People join groups that match their views, so affiliation marks a stake more than it causes a stance. 298 people carry an organisation label on some comments and none on others; they support 49% of the time when labelled and 59% when not.

## 6. Which projects draw review requests, associations and heavy opposition [H9]

1,541 site-specific projects with testimony (deduplicated). These are shares of projects that reached the Commission; without all building permits citywide there is no rate per permit.

- **Review cases** (316) are small: 89% involve one or two homes or have no unit count. They make up 38% of heard projects in one-family zoning, 30% in two-family, 12% in multi-family and 5% in downtown and mixed-use districts. Adjusted odds ratios: vertical addition 2.7 (1.8-3.9), roof deck 2.7 (1.7-4.5), one-family zoning 2.6 (1.3-8.1); cheapest third of neighborhoods 0.56 (0.38-0.83). Supervisor Districts 2 and 7 are highest (54%), District 6 lowest (4%). 91% of review cases end approved.
- **Heavy opposition** (six or more opposing comments, 204 projects) is a different profile: density-bonus projects 39% against 12% (adjusted odds 3.0, 1.5-6.0); new construction 21% against 11% (2.3, 1.6-3.6). Districts 8, 9 and 3 are highest.
- **Neighborhood associations** appear on 25% of projects with 10 or more homes against 11% of one- or two-home projects; new construction odds ratio 1.9 (1.3-2.6).
- **Two geographies.** Review requests concentrate in pricier, low-density areas. For projects of 10 or more homes the pattern reverses: opposition share is 37% in the cheapest third of neighborhoods (251 projects), 31% in the middle (149) and 22% in the priciest (95). Across all housing items the raw correlation between opposition share and neighborhood price was weakly positive (Spearman 0.14), driven by small projects. See corrections log.
- **Limit.** Review cases are nearly absent from the parsed data for 2007-2013, so the positive year coefficient for review cases is an artifact.

## 7. Tenant associations are the one group linked to projects not going ahead [H8]

Presence measured at the first hearing with testimony; 1,541 projects after collapsing batches.

| Group present | Projects | Stalled | When absent | Disapproved | When absent |
|---|---|---|---|---|---|
| Tenant associations | 35 | 20.0% | 5.2% | 20.0% | 3.3% |
| Anti-displacement and identity groups | 33 | 9.1% | 5.4% | 9.1% | 3.5% |
| Construction trades | 88 | 2.3% | 5.7% | 2.3% | 3.7% |
| Neighborhood associations | 176 | 4.5% | 5.6% | 6.2% | 3.3% |
| Pro-housing groups | 116 | 5.2% | 5.5% | 1.7% | 3.8% |
| Review requestors | 259 | 3.9% | 5.9% | 3.9% | 3.6% |

- Adjusted odds ratios for tenant-association presence: stalled 3.6 (1.05-10.1); disapproved 9.6 (2.1-32); three or more hearings 2.9 (1.2-6.5). Neighborhood associations: three or more hearings 1.5 (1.05-2.2); stalled 0.66 (0.27-1.16).
- **Nulls.** Construction trades, pro-housing groups, anti-displacement groups and neighborhood associations show no detectable link to stalling. An earlier table that showed one for construction trades and anti-displacement groups was a classifier error.
- **Why tenant groups.** They oppose more than they support (46% support). Where the tenant group opposed (21 projects) 29% were disapproved; where it supported (14) 7% were. A quarter of their projects involve merging or removing homes against 12% overall. Those cases need a conditional use authorization under Planning Code Section 317 ([ordinance text](https://sfbos.org/sites/default/files/o0064-24.pdf)), so the Commission has room to refuse.
- **Limit.** 35 projects, seven stalls, seven disapprovals. One or two reclassified cases would move this. In review cases a "support" mark may mean support for the requestor, not the project.

## 8. Affordable units: compliance and extra building size, not a path to approval [H6, H7]

- **Most large projects are market-rate with a minority of below-market homes.** Of 339 projects of 10 or more homes with unit counts in city records (33,429 proposed homes), 16% of homes are recorded as affordable: 164 projects show none on site, 120 show up to 20%, 27 show 21-99% and 28 are 100% affordable. "None recorded" can mean a fee was paid or the field is empty.
- **Shares bunch at set levels** (24 projects near 12%, 31 near 15%), consistent with a requirement. The city's inclusionary ordinance covers market-rate projects of 10 or more units and allows on-site units, off-site units or a fee ([SF Planning code summary](https://sfplanning.org/sites/default/files/documents/legis/code-summaries/2023-005422PCA-Code-Summary.pdf)).
- **Density bonus use has grown.** No project of 10 or more homes invoked the state density bonus or HOME-SF before 2013; 51% of those first heard since 2020 do. The state law trades on-site affordable units for extra density and waivers ([HCD fact sheet](https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/density-bonus-law.pdf)).
- **No sign that on-site units smooth approval.** Approval is 91% with none recorded and 96% with 1-20% (about 15 non-approvals in total). Projects with on-site units draw more opposition (4.3 against 1.1 opposing comments). After adjusting for size, year and neighborhood price, density-bonus projects draw 5.6 more opposing comments (0.9-10.1). Effect on three or more hearings: not detectable.
- **Outside context, not tested here.** 100% affordable projects are publicly financed; a 2026 city Budget and Legislative Analyst report put average funding at $954,127 per unit for tax-credit projects in 2024 ([BLA report](https://media.api.sf.gov/documents/BLA_Financing_Affordable_Housing_060526.pdf)). A San Francisco study estimated rents 1.2-2.3% lower within 500 m of new market-rate buildings and displacement risk about 17% lower, with more higher-income arrivals ([Pennington 2021](https://gwern.net/doc/economics/georgism/2021-pennington.pdf)). The dataset has no developer names or finances.

## 9. Trends since 2014 [H10, H12, H13]

- **The Commission takes review less often.** 54% of review cases in 2014-17 (n=219), 56% in 2018-19 (97), 39% in 2020-23 (150), 35% in 2024-26 (37). Before 2018, three or more opponents raised the chance by 22 points (72% against 50%); since 2020 the gap is gone (41% against 38%).
- **Departures from staff fell.** Decisions more negative than staff recommended: 2.8% of items in 2015-19, 1.2% in 2020-26.
- **Voting splits follow appointing authority.** On 235 split votes since March 2020, the three verified Board-President appointees (Moore, Imperial, Williams) were on the pro-project side 38% of the time and seven commissioners coded as mayoral appointees 90% (Koppel, Diamond, Braun, So, McGarry and Campbell verified; Tanner unverified); the Board group was the less pro-project of the two on 82% of split items. Any action needs four votes, so a 3-3 vote fails (see `memos/research/commission_structure.md`).
- **The docket is shrinking.** Decided regular and review items fell from 75-85 per half-year in 2021 to 31-56 in 2024-26. Projects of 10 or more homes first heard fell from 8-10 per half-year in 2021 to 0-4. Median meeting length fell from 6.3 hours (2015-19) to 3.6 (2023 onward).
- **Candidate causes, not separated here.** State Housing Crisis Act effective 1 January 2020; San Francisco subject to SB 423 ministerial approval from 28 June 2024; city Constraints Reduction Ordinance signed December 2023; commission membership change; the 2022-24 market slump. Dates are in `memos/research/law_and_procedure_timeline.md`.

**Nulls in this section.**
- **Remote hearings did not change the mix.** Support share among secretary-marked spoken comments: 57.4% in person (January 2018 to February 2020), 58.0% fully remote, 56.4% hybrid, 57.1% after remote comment ended on 1 January 2024. Comments per commented item: 7.3, 7.4, 6.5, 6.6. Unnamed speakers rose from 13% to 32% when hearings went remote.
- **The five-hearing cap shows no visible effect.** Projects of 10 or more homes with six or more hearing dates: 8.4% in 2015-19 (n=131), 9.5% in 2020-23 (n=74).
- **No agenda-position effect.** Odds ratio for continuance by relative position on the calendar 1.15 (0.91-1.45). Continuance rate rises with meeting length (10% under four hours, 18% over eight) but long meetings also carry heavier agendas.

**Do not compare support share across 2018.** Among secretary-marked comments it is 87% in 2017 and 54% in 2018, exactly when the share of comments carrying a mark rises from 70% to 91%. That is a change in recording.

## 10. What other workstreams should take from this

- **Hearings are not where housing is stopped.** Any synthesis that treats public opposition as the mechanism blocking Bay Area housing has to contend with a 90% approval rate and a staff-agreement rate of 97% in the region's most contested city. The cost is time and division.
- **Opposition to large projects is higher in cheaper neighborhoods.** This lines up with the displacement workstream's finding that pressure and vulnerability sit in different places, but it is one city and based on partial Zillow data.
- **Tenant and anti-displacement groups mostly oppose market-rate and mixed-income projects** in this record (27-46% support), and show support on 100% affordable projects (a handful of comments).
- **Zillow price near a project predicts nothing about its outcome** once staff recommendation is known.
- **Limits that travel with every number.** One city; observational; sparse affiliation labels; Zillow part 2 missing; a stall classifier that needed two rebuilds.

---

## Methods table

| Tag | Script in `code/` | Result table in `results/` | What it does |
|---|---|---|---|
| H0 | `00_zillow_extract_sf.py` | `00_zillow_extract_sf.txt` | Pulls San Francisco rows from the Zillow part files |
| H1 | `01_eda.py` | `01_eda.txt` | Profiles comments and agenda items; label sources; outcome distributions |
| H2 | `02_stance_baseline.py` | `02_stance_baseline.txt` | Stance classifier baselines, leakage test, subgroups, cross-channel check |
| H3 | `03_stance_with_context.py` | `03_stance_with_context.txt` | Adds role, section, case type and project text to the stance model |
| H4 | `superseded/funnel1.py` | (not in `run_all.sh`) | Staff recommendation against action; first funnel. Its 14% "no final decision" figure is superseded by H8 |
| H5 | `04_outcomes_first_hearing.py` | `04_outcomes_first_hearing.txt` | Project-level outcome models from first-hearing features, with bootstrap intervals and subgroups |
| H6 | `05_site_projects_and_speakers.py` | `05_site_projects_and_speakers.txt` | Site-specific filter, affordability classes, stance by role, themes, Zillow terciles |
| H7 | `06_affordability_unaffiliated_roles.py` | `06_affordability_unaffiliated_roles.txt` | Affordable share against outcomes; profile of unaffiliated speakers; same-project stance gaps |
| H8 | `07_build_heard_projects.py`, `08_stalls_corrected.py` | `07_…txt`, `08_stalls_corrected.txt` | Builds the heard-projects table; corrected stall classifier; group presence against stalls and disapprovals. The stall table printed by 07 is superseded by 08 |
| H9 | `09_which_buildings.py` | `09_which_buildings.txt` | Which projects draw review requests, associations and heavy opposition |
| H10 | `10_trends.py` | `10_trends.txt` | Yearly participation, hearings per project, themes, deference to staff |
| H11 | `11_votes_and_agenda.py` | `11_votes_and_agenda.txt` | Split votes, split-vote model, commissioner tallies, agenda position, meeting length |
| H12 | `12_remote_hearings.py` | `12_remote_hearings.txt` | Secretary-mark coverage and support share by year; participation by quarter |
| H13 | `13_blocs_responsiveness_volume.py` | `13_blocs_responsiveness_volume.txt` | Votes by appointing authority, responsiveness by era, docket volume, hearing-format comparison |
| H14 | `14_examples.py` | (not committed) | Prints project histories used for `memos/05_project_examples.md` |
