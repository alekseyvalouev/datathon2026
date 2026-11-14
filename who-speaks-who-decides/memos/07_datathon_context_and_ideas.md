# Memo 7: datathon context and ideas considered

## Event
8th Annual Datathon for Social Good. Two-day event. Submission: project link (repo, notebook or site), slide deck, video of at most five minutes, via the organisers' form.

## Advanced Track checklist (from the Tracks & Guide; the announcement differed)
1. Use at least one provided dataset; outside data optional. (The announcement said two datasets; the guide says one.)
2. Train or fine-tune a predictive or NLP model. Descriptive analysis, a keyword list or an off-the-shelf API used as is does not count.
3. Compare with a simple baseline.
4. Report task-appropriate metrics on a held-out test set not used for training or tuning.
5. Error and fairness analysis across at least three meaningful subgroups, with failure examples.
6. Explain label creation, heavy cleaning or joins, and check a sample by hand.
7. Code that runs from raw data to reported results.
Projects missing a requirement are judged in the other track.

## How this workstream maps to the checklist
| Requirement | Status |
|---|---|
| Provided dataset | Zillow (parts 1 and 3) joined by location. It adds no predictive power, which is a reportable null but a thin use |
| Trained model | Stance classifier; split-vote and drawn-out-hearing models |
| Baseline | Majority class and keyword rule; staff recommendation plus case type |
| Held-out test | Time-based splits throughout |
| Three subgroups | Calendar section, speaker role, comment length, year; neighborhood price tercile, case kind, opposition level, size |
| Hand check | Partial: 14 stalled projects on an intermediate classifier; project examples. No systematic hand check of labels or joins |
| Reproducible code | `code/run_all.sh` |

## Provided datasets as received by this workstream
| Dataset | What arrived |
|---|---|
| Glassdoor, Google Maps Places, Google Maps Reviews, College Affordability, Health Risk | Full files |
| Zillow | Parts 1 and 3; part 2 missing |
| Indeed | 1,000-row sample; about a third located only as "California", some rows from California, Maryland |
| Reddit | 1,000-row sample of unrelated subreddits |

Health Risk is 1,000 patient vital-sign records with a rule-like label, not area-level data.

## Ideas considered
- **Hidden Pay (Indeed + Zillow).** Predict the pay that job postings omit from the description text, then compare with local rents. Feasible and safe; not pursued here. Needs the full Indeed file and a location filter.
- **Clinic review aspects (Google Maps Places + Reviews).** Label complaint types and map them. Hand-labelling is the cost.
- **Reddit moderation fairness audit.** Label creation and dialect fairness are hard to do well in two days.
- **Neighborhood defenders replication (this workstream).** Original plan matched commenters to voter files across Bay Area cities. Dropped the voter-file match: California limits voter-file use to election, scholarly, journalistic, political or governmental purposes and requires an application, and matching named commenters conflicts with the event's ethics guidance. Dropped cross-city scope: Berkeley minutes record only a count of commenters, Oakland posts PDFs, and Legistar cities have no coded positions.
- **Money in local races.** San Francisco's campaign-finance table is strong, but Cal-Access covers state filers only, San Jose has no confirmed export, November 2026 results were uncertified, independent expenditures vary by contest not precinct (tens of observations), and the question is causal while the checklist wants a predictive model. Judged not feasible for the event; details in `research/outside_data_sources_report.md`.

## Suggested centerpiece if this workstream is used
Split-vote model (AUC 0.58 → 0.67 with comments) with the appointing-authority split as its explanation, the stance classifier as the NLP component, and the nulls (remote hearings, hearing cap, agenda position, Zillow price) stated alongside.
