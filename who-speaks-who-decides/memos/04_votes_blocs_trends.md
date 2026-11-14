# Memo 4: votes, blocs and trends [H10-H13]

## Vote parsing
AYES and NAYES fields are split into surnames. Items kept if at least three ayes and at most seven names in total: 10,952 items, 13.7% split. Decided regular and review items: 4,206, 22.3% split. Most common tallies: 6-0, 7-0, 5-0, 4-0, 5-1, 6-1, 4-2, 5-2. Variance items heard by the Zoning Administrator carry no commissioner vote by design.

## Split-vote model
Train through 2017 (2,637 items), test 2018-2026 (1,569; 345 split). Gradient boosting, depth 3. Features as in FINDINGS section 4. Bootstrap interval on the AUC gain from comment counts: +0.056 to +0.133.

Split rate by case type: mandatory review 32%, code amendments 28%, conditional use 20%, public-initiated review 17%, environmental 13%, variance-linked 11%. Staff recommended disapproval: 54% split (n=79).

## Appointing authority
"Pro-project side" = aye when the action is an approval, nay when it is a disapproval. Since March 2020, 235 split items. Board-President appointees 38.3% (530 votes); coded mayoral 89.5% (768); other or unverified 79.4% (218). On 98 of 235 items the two groups were entirely on opposite sides. Before 2020 appointing authority is unverified, so no earlier comparison is made.

## Responsiveness by era

| Era | Split rate, 0 opponents | 1-5 | 6+ | Disapproved, 0 opponents | 1-5 | 6+ |
|---|---|---|---|---|---|---|
| 2005-17 | 19% (2,043) | 31% (497) | 44% (97) | 2.0% | 4.2% | 15.5% |
| 2018-23 | 14% (616) | 22% (488) | 38% (187) | 1.1% | 1.4% | 9.1% |
| 2024-26 | 23% (146) | 26% (103) | 69% (29) | 1.4% | 2.9% | 17.2% |

The 2024-26 cells are small.

## Participation by hearing format (spoken comments)

| Period | Meetings | Comments per meeting | Per commented item | Unnamed | First-ever appearance | Support | Org-affiliated |
|---|---|---|---|---|---|---|---|
| Jan 2018 - Feb 2020, in person | 86 | 70.7 | 7.3 | 12.6% | 48.9% | 57.4% | 26.0% |
| Apr 2020 - Mar 2022, remote | 80 | 54.7 | 7.4 | 31.7% | 43.0% | 58.0% | 32.3% |
| Apr 2022 - Dec 2023, hybrid | 62 | 44.0 | 6.5 | 29.0% | 41.8% | 56.4% | 38.2% |
| Jan 2024 - Mar 2026, no remote comment | 77 | 35.9 | 6.6 | 24.9% | 49.5% | 57.1% | 39.7% |

Format dates come from `research/law_and_procedure_timeline.md` (remote hearing confirmed 16 April 2020; hybrid by 28 April 2022; remote comment suspended 1 January 2024). Comments per meeting fall because meetings carry fewer items.

## Hearings per project
Mean hearing dates per site-specific project by first-heard year stay near 2.0-2.3 from 2015 to 2021, then 1.9 (2022) and 1.5 (2023). The later cohorts have had less time to accumulate hearings.

## Agenda position
Regular and review items with a coded action at meetings with at least six such items. Continuance rate by quarter of the calendar: 13.8%, 18.1%, 18.8%, 18.5%. Logistic model with relative position, log comments, review flag, meeting hours and year: position odds ratio 1.15 (0.91-1.45); hours 1.03 per hour (0.99-1.07). Meeting length is known for 642 of 1,252 meetings.

## Comparison with published work
From `research/participation_literature.md` (figures read from working-paper versions by an automated reader; recheck before quoting):
- One-time speakers dominating headcount is documented in Boston-area towns and California councils.
- A Boston follow-up found online meetings left participation essentially unchanged.
- No published hearing-level study was found for the tenant-association link, the two-geography split, stalls, or agenda-order effects.
- The dataset's author reports opposition share falling as unit counts rise, which needs a size-controlled check against the density-bonus finding here.
