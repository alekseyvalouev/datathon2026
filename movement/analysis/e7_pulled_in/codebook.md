# E7 Codebook: "arrival" stories on Reddit (moving TO the Bay Area)

Annotator: an LLM (Claude) working from this codebook. **Not human-verified**; see
`labels/verify_sample.csv`.

Unit = one Reddit post (title + body) or one comment/reply. Label from the item text; the
thread title is context only (to resolve "here"). Bay = the 9 counties (SF, Alameda, Contra
Costa, Marin, Napa, San Mateo, Santa Clara, Solano, Sonoma).

## 1. Label
| code | label | definition |
|---|---|---|
| A | ARRIVED | First-person (I / we / my partner and I) account of having moved **into** the Bay from outside it, and (as far as the text says) still living there. Includes "just moved to Oakland", "new to the Bay", "moved here in 1997", "came back to SF last year". When origin is unstated, a city-level "moved to SF / Oakland / San Jose / the Bay" or "new to the Bay / city" counts. |
| P | PLANNING | First-person concrete upcoming move into the Bay: accepted/received offer, admission, lease/deposit, dated plan, or active serious deliberation ("got an offer in Palo Alto, should I take it?"). Writer currently outside the Bay. |
| W | WITHIN-BAY | First-person move between places inside the Bay (SF→Oakland, Fremont→SSF). Not an arrival. |
| O | OTHER | Everything else: third person ("my friend moved to SF"), advice, visits/trips, vague wishes ("can't wait to move to SF someday"), businesses "new to Oakland", people who arrived and have since **left**, neighbourhood-level "we moved here" with no sign of coming from outside the Bay, non-Bay places with Bay names (Dublin, Ireland; Albany, NY). |

## 2. Fields (A and P only)
| field | codes |
|---|---|
| reasons (multi, `;`) | t = tech/startup/AI job · j = other job, transfer, job offer, residency · s = school/university/grad program · p = partner or family · l = lifestyle/culture/weather/nature · c = returning to the Bay · o = other. Empty = no reason stated. Code only stated/clearly implied reasons. |
| household | s = single/solo · c = couple, no kids mentioned · f = family with kids (incl. pregnant) · r = roommates/shared · u = unknown |
| era | n = recent (≤ ~5 years, "just/recently/new to", or PLANNING) · a = longer ago (> 5 years, e.g. "moved here in 2011") · u = unknown |
| origin | us = other US state · ca = elsewhere in California · ab = abroad · u = unknown |
| dest | Bay city/neighbourhood as written (normalised) |
| occ | t = tech · h = healthcare · a = academic/student · s = service, trades, hourly, arts · f = finance/law/other professional · u = unknown |
| money | stated salary / income / rent budget / home budget as written, e.g. `sal 135k`, `rent 1900`, `hh 150k`, `tc 300k` |

## 3. Procedure
1. Recall-oriented regex pool (`scripts/e7common.py`, tiers A/B/C) over all posts **and** nested comments of the raw Reddit CSV.
2. Stratified sample of 300 (150 tier A, 70 B-implicit, 40 B-place, 40 C), frozen with a seed.
3. Items shown truncated to ~520 characters around the first arrival match.
4. Pass 1: all 300. Pass 2: 80 items re-labeled blind by a separate fresh-context LLM instance given only this codebook (main label only).
