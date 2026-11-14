# Corrections log

Errors made during this workstream and what replaced them. Read before quoting any number from an earlier draft or from `code/superseded/`.

| # | What was wrong | How it was found | What replaced it | Still affected |
|---|---|---|---|---|
| 1 | First outcome models scored AUC near 0.9. Two features leaked the answer: items continued before testimony have no comments, and item descriptions carry "proposed for continuance" notes. | Feature importance was dominated by comment count and text length. | `04_outcomes_first_hearing.py` restricts to hearings with testimony, drops text length and excludes items carrying the note. The leaky version is `superseded/exp2b.py`. | None known |
| 2 | "Housing project" filter (`housing_kw`) also caught legislation, policy reports and informational briefings, which never get an approve/deny vote. This inflated "no final decision" to 14%. | Pulling example projects. | Site-specific filter in `05_site_projects_and_speakers.py`: has an assessor's lot, not a code amendment or informational item. Corrected share 4.5%, later 5.5% stalled under the final classifier. | `04_outcomes_first_hearing.py` still runs on the looser population; its table in FINDINGS section 4 has not been rerun |
| 3 | First stall classifier read actions such as "Approved with conditions; sponsor to continue working with staff" as continuances. 71 approved projects were counted as stalled, including most "stalled" projects where construction trades had spoken. | Listing the stalled projects for each group. | `08_stalls_corrected.py` classifies on the last clause of the action text. Construction trades and anti-displacement groups no longer show a link to stalls. | `07_build_heard_projects.py` still prints the old stall table; ignore it |
| 4 | A withdrawn discretionary-review request was counted as a stalled project. When the request is withdrawn the project proceeds. | Same listing. | Separate category "review request withdrawn (project proceeds)". | None known |
| 5 | Seven near-identical student-housing conversion cases from one applicant, continued together, counted as seven stalls. | Same listing. | Batches collapsed to one project (1,803 → 1,541). | The batch key is coarse and may over-merge |
| 6 | Reported that opposition rises with neighborhood price (26% / 33% / 38% by tercile, Spearman 0.14). | Splitting by project size. | True across all housing items, driven by small projects. For projects of 10 or more homes it reverses: 37% / 31% / 22%. | Both rest on Zillow parts 1 and 3 only |
| 7 | Reported tenant associations, anti-displacement groups and construction trades all linked to stalls (22.8%, 20.6%, 10.6%). | Correction 3. | Only tenant associations remain (20.0% against 5.2%; 35 projects). | Small sample |
| 8 | Support share appears to fall from 87% (2017) to 54% (2018). | Checking secretary-mark coverage by year. | Recording change: coverage rises from 70% to 91% in 2018. Do not compare support share across that boundary. | Any long-run stance trend |
| 9 | Year coefficient suggested review cases are rising. | Counting review-calendar items by year. | Review cases are nearly absent from parsed data for 2007-2013. | Long-run review trends |
| 10 | Theme trends by period (affordability, housing need and so on rising). | Note length differs by period and written comment exists only 2017-2024. | Treat only the within-period gap between opposing and supporting comments as usable. | `10_trends.py` section D |
| 11 | Early project advice treated the Health Risk dataset as area-level and said joining two datasets was required. | Reading the full Tracks & Guide. | It is 1,000 patient records; the Advanced Track needs one provided dataset, not two. | None |
| 12 | Two commissioners named Johnson are merged, and "Lee" appears under three spellings. | Reading the commissioner table. | Bloc analysis uses only ten clearly identified members. | Per-commissioner tallies in `results/11_…` |

## Not verified

- The final stall classifier has not been hand-checked. An intermediate version had about 2 doubtful cases in a sample of 14.
- Affordability classes come from keyword matches on agenda text plus patchy city unit fields.
- Unit counts parsed from text (`units`) are noisy; the "10+ units" group may include misreads.
- Self-descriptions of unaffiliated speakers ("neighbor", "tenant", "owner") are keyword matches on short notes; "owner" may mean the project's owner.
- Outside-source figures in FINDINGS (per-unit subsidy, rent effects, legal standards) were read from search results, not from full documents.
- Appointing authority is verified for Moore, Imperial and Williams (Board President) and for Koppel's first stint, Diamond, Braun, So, McGarry and Campbell (mayoral). Tanner is coded mayoral but unverified. Earlier commissioners are unverified, and Koppel returned in 2026 in a Board seat, after this dataset ends.
