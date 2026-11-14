# E4 Codebook: Bay Area / California "exit stories" on Reddit

Annotator: an LLM (Claude) working from this codebook. The labels have **not** been
human-verified; see `labels/verify_sample.csv`.

Unit = one item: a Reddit **post** (title + body) or one **comment/reply**. Label
using only the item text. The thread title is shown as context only, to resolve
what "here" or "there" refers to. Do not label from the thread title alone.

## 1. Main label (`label`)

| label | definition |
|---|---|
| **LEFT** | First-person (I / we / my family / my partner and I) account of **having already moved out** of the Bay Area **or** out of California, where the move happened while the writer lived there as an adult or with their household. Includes "we left SF for Sacramento in 2023", "moved to Texas last year, best decision", and "I got priced out of Oakland and now live in Stockton". |
| **CONSIDERING** | First-person, **concrete, serious** plan or deliberation about leaving the Bay/CA: "we are moving to Boise in June", "seriously thinking about leaving the Bay, where should we go?", "lease is up, can't afford it, looking at Sacramento". The writer must currently live in the Bay/CA. Must be more than a passing gripe. |
| **OTHER** | Everything else. |

### OTHER explicitly includes these hard negatives
* Moving **to** the Bay/CA, or moving **within** a county or city (SF to Oakland counts as a move between Bay counties, see below).
* Third-person or aggregate talk: "everyone is leaving", "my friend moved to Texas", news, statistics, the A's / Warriors relocation, companies relocating HQs.
* Advice to others ("you should just move to Sacramento"), hypotheticals without personal intent ("if rents keep rising I'd leave someday"), jokes, sarcasm.
* People who left and **came back** and now live in the Bay, unless they are leaving again. (Exception: a "we left, then came back" story is OTHER, because the person did not stay out.)
* People who grew up in CA and left as a child with their parents.
* Non-Bay/CA origins, such as moving out of NYC, or San Jose, Costa Rica.
* Moves inside the Bay. "We moved from SF to Antioch because of rent" is a
  displacement story but **not** an exit, so it is labeled OTHER. It is flagged
  with `within_bay=1` so it can be analysed separately.

Edge rules
* Origin can be implicit. In a Bay subreddit, "we moved to Reno last year" = LEFT.
* Leaving the **Bay** for elsewhere in CA (Sacramento, Central Valley, LA) counts as an exit.
* Mixed or ambiguous tense ("moving to Texas next month, already sold the house") = CONSIDERING unless the move is complete.
* Use the most recent state: if a person "was planning to leave and now left", label LEFT.
* If an item mentions both a friend's exit and the writer's own plan, label the writer's own plan.

## 2. Reason tags (`reasons`, multi-label, `;`-separated; LEFT/CONSIDERING only)
Tag only reasons the writer states or clearly implies. Leave the field empty if no reason is given.

| tag | cues |
|---|---|
| housing_cost | rent, mortgage, home prices, "couldn't afford a house", eviction, rent increase, priced out |
| jobs_wages | layoff, job offer elsewhere, low wages, tech downturn, career |
| cost_of_living_other | taxes, gas, childcare, groceries, general "too expensive" without housing specified |
| family | being near parents/kids, caring for relatives, partner, divorce |
| schools | school quality, school district |
| safety_quality_of_life | crime, homelessness, traffic, weather/fire smoke, politics, "quality of life", burnout, space |
| remote_work | went remote, WFH, "work from anywhere" |
| other | any other stated reason (retirement, health, military, school/college) |

## 3. Destination (`dest_text`, `dest_bucket`; LEFT/CONSIDERING only)
`dest_text` = the destination as the writer states it, normalised (e.g. "Sacramento", "Texas", "Portugal").
For CONSIDERING items with several candidate destinations, use the first one named.

| dest_bucket | rule |
|---|---|
| other_bay_county | Exit from one Bay county to another Bay county. Rare, because those items are OTHER/within_bay. This bucket is kept for comparability with CPL. |
| sacramento_central_valley | Sacramento, Placer (Roseville, Rocklin), Yolo (Davis), El Dorado, San Joaquin (Stockton, Tracy, Manteca, Lodi), Stanislaus (Modesto), Merced, Fresno, Kern (Bakersfield), "Central Valley" |
| other_ca | LA, San Diego, Orange County, Central Coast, Sierra foothills, Tahoe (CA side), North Coast, Inland Empire, "SoCal" |
| out_of_state | any other US state. Record the state in `dest_state` (two-letter code) |
| abroad | outside the US |
| unknown | not stated |

## 4. Auxiliary fields
* `within_bay` (0/1): a first-person move inside the 9-county Bay, usually toward cheaper areas. It is not an exit and is kept for E3/E1 cross-reference.
* `notes`: short annotator note, never containing usernames or long quotes.

## 5. Procedure
1. The pool was built by a broad regex (see `scripts/common.py`). The sample is
   stratified by subreddit group × post/comment × naive-regex hit, plus random
   "hard negatives" (items that match move + place terms but not the naive rule).
2. Items are shown truncated to about 700 characters around the first move/place match.
3. Pass 1: all items. Pass 2: 100 items re-labeled blind from their text (with the
   pass 1 labels hidden). Cohen's kappa is reported.
