# Memo 3: speakers, affiliations and affordability [H6, H7]

## Population
Site-specific projects: has an assessor's block and lot in the agenda text; case type is not a code amendment, policy item, zoning map change or informational presentation; carries the housing keyword. 2,915 projects since 2005; 1,897 have at least one support/oppose comment.

## Role labels
Roles come from the dataset's `role_long`, assigned by rules (case role, attendance roster, curated rosters, stated organisation, propagation across a speaker's testimony). Groups used here:
- pro-housing = YIMBY, Pro-Housing Advocacy, SPUR
- anti-displacement and identity = Anti-Displacement, Race/Immigration/LGBTQ Groups
- neighborhood = Neighborhood Association, Slow Growth, Historic Preservation
- construction = Construction, Labor
- project team = Project Team, Legal

## Stance by project type
- Support share: 46% on discretionary-review cases; 58% on small non-review projects; 70% on large mixed-income; 77% on large projects with no affordability mention; 70% on 100% affordable (276 comments).
- On large mixed-income projects: neighborhood associations 17% support (78 comments), anti-displacement groups 20% (20), identity groups 8% (24), affordable-housing developers 7% (15).

## Themes in the note (keyword match; share of comments with text)

| Theme | In opposing | In supporting |
|---|---|---|
| Light, shadow, views, privacy | 26.0% | 18.5% |
| Neighborhood character, historic | 19.1% | 19.6% |
| Height, bulk, scale | 18.2% | 15.9% |
| Parking, traffic | 15.6% | 13.4% |
| Affordability, who it is for | 13.7% | 15.0% |
| Process, notice, outreach | 12.3% | 5.2% |
| Displacement, tenants, eviction | 8.8% | 7.6% |
| Housing need, supply | 2.9% | 13.6% |
| Jobs, labor | 2.3% | 4.5% |

## Affordability classes
From agenda text plus city unit fields. "100% affordable" if the text says so or city records show at least 90% affordable units; "mixed" if it mentions inclusionary, below-market, density bonus, HOME-SF or affordable units. 61% of proposed homes are in projects with no affordability mention, which reflects what agendas say, not what was built.

Among 339 projects of 10+ homes with city unit fields, affordable share of proposed homes by first-heard period: 20.5% (2005-2012), 19.0% (2013-2017), 9.3% (2018-2026). Field completeness may differ by period.

## Does on-site affordability relate to approval?

| On-site affordable share | Projects | Approved | Mean opposing comments | Three or more hearings | Uses bonus |
|---|---|---|---|---|---|
| None recorded | 164 | 91% | 1.1 | 27% | 1% |
| 1-20% | 120 | 96% | 4.3 | 34% | 30% |
| 21-99% | 27 | 96% | 13.8 | 11% | 67% |
| 100% | 28 | 93% | 2.8 | 21% | 0% |

Size-matched (25-200 homes, 2012 onward, not 100% affordable): none recorded 93% approved (n=58), some on site 98% (n=88). Bootstrap logistic models on 311 projects: on-site units and three or more hearings, log-odds 0.13 (−0.43 to 0.74); density bonus and opposing comments, +5.6 (0.9 to 10.1).

## Repeat speakers
Among people with five or more comments on these projects: unaffiliated 63 always support, 19 always oppose, 59 mixed; neighborhood associations 1 / 8 / 12; pro-housing 11 / 0 / 2. 79 people with ten or more comments account for 14% of all comments.

## Limits
- Three quarters of comments have no role label; the role table describes organised speakers.
- Themes and self-descriptions are keyword matches on the secretary's summary.
- Comment positions here include model-imputed and LLM-coded labels, not only the secretary's marks.
