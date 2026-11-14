# Memo 2: outcomes, delay and stalls [H4, H5, H8, H9]

## Filtering before the vote [H4]
- Population: regular and discretionary-review calendar items since 2005 with a coded action.
- Staff recommendation distribution among decided items: approve with conditions 50%, approve 36%, missing 12%, disapprove 1.7%.
- Direction agreement between staff and Commission: 97.3% of 4,156 items.
- Discretionary review: of 529 items with a coded direction the Commission took review in 256 (48%), including 145 of 406 where staff advised against. Seven of 1,140 review items were disapproved.

## First-hearing outcome models [H5]
- Unit: project (`id_parent`) at its first regular or review hearing with at least one public comment and no "proposed for continuance" note. 3,439 projects first heard 2005-2023.
- Features. Baseline: staff recommendation code, review flags, case-type dummies, housing/demolition/new-construction flags, items on the calendar that day, prior appearances. Size: units, stories and square feet parsed from the description. Comments at that hearing: counts by position, opposition share, counts from neighborhood associations, project team, review team, interest groups and email. Zillow: median price per square foot of the 30 nearest sales and median rent of the 30 nearest rentals.
- Models: logistic regression baseline; gradient boosting (depth 3, 250 trees) for the rest. Train first hearings through 2016, test 2017-2023. Bootstrap (1,000 resamples) on the AUC difference.
- Population caveat: this run predates the site-specific filter and includes legislation and policy items.

## Stall classifier [H8]
- Unit: 1,803 site-specific projects with testimony, first heard by 2023; 1,541 after collapsing batches.
- Each action text is classified on its last clause: approve-type words, disapprove, withdraw, continue, or a failed motion. "Motion of intent" clauses are not final. Final state is the last decisive action; otherwise indefinite continuance, continuance, or none.
- Stalled = withdrawn (not a withdrawn review request), continued indefinitely, continued and never returned, or deadlocked.
- City record status for stalled projects is mostly "Closed", which does not confirm or refute.
- Group presence is measured at the first hearing with testimony so that later hearings cannot inflate it.
- Adjusted model: logistic regression (C=10) with group indicators, log unaffiliated opposition and support, review flag, log units, units-missing flag, demolition flag, year; 500 bootstrap resamples for intervals.

## Rates by opposition at first hearing (older run, looser population) [H5]

| Opposing comments | Projects | Not decided that day | Two or more further hearings | Modified | Disapproved |
|---|---|---|---|---|---|
| 0 | 2,055 | 18% | 9% | 30% | 2.5% |
| 1-2 | 766 | 23% | 10% | 36% | 2.3% |
| 3-5 | 295 | 22% | 11% | 46% | 3.4% |
| 6-10 | 183 | 33% | 20% | 46% | 7.7% |
| 11+ | 140 | 31% | 18% | 43% | 13.6% |

"Modified" is a keyword match on the action text (modif, as amended, revis, reduc, setback, eliminat) or review taken; it misses some changes and catches non-substantive amendments.

## Which buildings [H9]
See FINDINGS section 6. Zoning, district and scope of work are regex matches on the agenda description. Adjusted odds ratios are from one logistic model per outcome with 300 bootstrap resamples; only coefficients whose interval excludes 1 are printed.
