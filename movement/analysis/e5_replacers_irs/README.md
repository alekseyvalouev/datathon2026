# E5: Who replaces the leavers?

**The puzzle from E1.** In the IRS county migration files, Bay Area in-movers report *lower* AGI per return than out-movers. In TY2021 Santa Clara in-movers averaged $184k, out-movers $245k and stayers $268k. Yet Zillow shows that replacement tenants in the same units pay much higher rents. E5 asks who the replacers are and whether this gap is real.

**Short answer.** The gap is real in the tax data, but it **does not mean poorer replacers**. Four things produce it:
1. **Foreign arrivals:** ruled out. They are almost absent from the IRS matched data.
2. **Origin geography:** ruled out. The gap persists like-for-like.
3. **Household structure:** fewer persons per return.
4. **Age and career stage:** replacers are young, and their incomes are rising fast.

Items 3 and 4 explain roughly half or more of the gap. The rest is concentrated in SF, Santa Clara and San Mateo from 2017 on, and it is driven by very high-AGI leavers rather than low-income arrivals.

**Reproduce:** `./run.sh`. It downloads the IRS state gross-migration files and the ACS bulk tables into `raw/`, then runs `scripts/analyze.py`, `scripts/acs.py`, `scripts/figures.py` and `scripts/verify_by_hand.sh`. County IRS files are read in place from `../e1_composition/raw/`. All Python runs with `python3 -I`.

## Data and definitions
- **IRS SOI county inflow/outflow, files 2011-12 … 2022-23.** AGI and n2 come from the **year-2 return**, so file `2122` holds TY2021. TY2022 (file 2223) uses the new IRS matching method (about +5% returns, new suppression rules) and is flagged everywhere with `method_break`.
- **Origin types** use the IRS summary rows:
  - `96/000`: all movers.
  - `97/000`: US (domestic).
  - `97/001`: same state.
  - `97/003`: different state.
  - `98/000`: foreign. Per users guide note [4], this covers PR, USVI, APO/FPO and overseas addresses.
  - Other Bay counties are the sum of named Bay rows. **No Bay–Bay row is suppressed in any year.**
  - Rest of CA = same state minus other Bay counties. This includes suppressed small flows.
  - **Region:** intra-Bay moves count as staying, exactly as in E1. The pipeline reproduces E1's region and county means to the dollar (asserted in `analyze.py`).
- **n2 (persons per return).** Up to the 2018-19 file it is "number of exemptions". From the **2019-20 file (TY2019)** it is "number of individuals", based on filing status and dependents (2019-20 users guide, section B). The level series has a break at TY2019. **All comparisons here are within one file** (in vs out vs stay), so they are robust to the break.
- **Gross migration file `{YYZZ}inmigall.csv` (state level only).** For non-migrants, out-migrants, in-migrants and same-state movers it gives returns, n2, **year-1 and year-2 AGI** by six age bands of the primary taxpayer and seven year-2 AGI classes. In and out refer to state borders, and foreign/other areas are excluded (note [5]). Returns with negative AGI are excluded.
- **ACS 2018-22 5-year, B07010/B07013.** These come from the keyless Census *table-based summary file* bulk download (`www2.census.gov/.../table-based-SF/data/5YRData/`). They are person-level, with individual income in 2022 dollars, by mobility status at the current residence.

## Results

### Q1. Where in-movers come from (`outputs/flows_by_origin_type.csv`, `figs/fig1_region_origins_and_agi.png`)
For the 9-county region (intra-Bay moves internal), each year 2011–2021 has about **39–44% of in-moving returns from the rest of California, 56–61% from other states, and 0.3–3.0% foreign.**

| TY | in: rest CA $ | out: rest CA $ | in: other states $ | out: other states $ | in: foreign (n, $) | stayers $ |
|---|---|---|---|---|---|---|
| 2011 | 56,400 | 61,500 | 80,400 | 83,100 | 2,357 · 106,057 | 101,900 |
| 2016 | 76,500 | 86,900 | 101,900 | 121,100 | 475 · 50,044 | 138,100 |
| 2019 | 83,800 | 117,200 | 110,200 | 179,100 | 429 · 58,142 | 161,100 |
| 2021 | 123,100 | 167,900 | 159,100 | 242,700 | 347 · 65,501 | 215,400 |
| 2022* | 94,700 | 125,700 | 127,800 | 160,300 | 2,530 · 153,761 | 184,100 |

**Foreign or part-year arrivals do not drive the low in-mover mean.**
- Foreign returns are at most 3% of IRS in-movers. From TY2016 to TY2021 the county files contain **no "Foreign – Overseas" row at all**, only APO/FPO (about 0.3–0.4%). Overseas rows reappear in 2022-23.
- Where foreign arrivals are visible (2011–2015, 2022), their mean AGI is **above** the domestic in-mover mean.
- Domestic-only in/out ratios are identical to the all-mover ratios in almost every cell (`replacement_ratios.csv`, `cat=domestic` vs `all`).
- The ACS shows that arrivals from abroad are a real group of replacers: **16.8% of 15+ in-movers to Bay counties** (summing county-level flows), and 34% of them report no income. The IRS matched-return data structurally miss them, because they have no year-1 US return. They are *unseen* replacers, not the cause of the IRS gap.

### Q2. Household size: families replaced by singles (`figs/fig3_persons_per_return.png`)
Persons per return in the region:

| | Stayers | Out-movers | In-movers |
|---|---|---|---|
| TY2011 | 2.16 | 1.77 | 1.71 |
| TY2021 | 1.93 | 1.70 | **1.46** |

In TY2021 every one of the 9 counties had in-movers with fewer persons per return than stayers. In SF the figures are 1.22 for in-movers, 1.44 for out-movers and 1.63 for stayers. Out-movers are larger households than in-movers in 6 of 9 counties; in Contra Costa, Marin and Solano the two are about equal (in-movers 1.59–1.78, out-movers 1.59–1.77).

Dividing AGI by persons (`agi_per_person`) removes a large part of the gap:

| Region | per-return in/out | per-person in/out |
|---|---|---|
| TY2019 | 0.66 | 0.75 |
| TY2020 | 0.61 | 0.71 |
| TY2021 | 0.69 | 0.80 |

The ACS points the same way: in-movers are **59–73% renters versus 37% of same-house residents** (B07013, region sums). This fits single filers and roommates replacing owner families. A unit rented by two single in-movers is two IRS returns, so per-return AGI understates what the unit can pay. That reconciles the IRS gap with the higher Zillow rents. It is an inference: IRS data cannot link returns to dwellings.

### Q3. Like-for-like replacement ratios (`outputs/replacement_ratios.csv`, `replacement_ratio_partner_matched.csv`, `region_state_pairs_pooled_2011_2021.csv`, `figs/fig2_replacement_ratio_heatmap.png`)
The **replacement ratio** is in-mover mean AGI divided by out-mover mean AGI, both per return and domestic only.
- **Below 1 in the job-centre counties since 2016–17.**
  - SF: 0.74, 0.83, 0.73, 0.64, 0.56, 0.67 for TY2016–21.
  - Santa Clara: 0.96, 0.79, 0.76, 0.70, 0.76, 0.75.
  - San Mateo: below 0.9 for TY2019–21.
  - Region: 0.87 → 0.61 (TY2020) → 0.69.
- **Roughly 1 or above elsewhere.** Alameda 0.9–1.04, Contra Costa and Solano about 1.0, Marin, Sonoma and Napa mostly 1.1–1.95. In these counties arrivals out-earn leavers.
- **The geography of origins explains little.** Reweighting in-movers' county-of-origin means to the out-movers' destination mix (over partner counties named in both files) gives these median ratios for 2011–2022:

  | County | partner-matched | raw |
  |---|---|---|
  | SF | 0.79 | 0.80 |
  | Santa Clara | 0.84 | 0.87 |
  | Alameda | 0.91 | 0.98 |

- **State-for-state pairs, region, pooled TY2011–21** (in-movers from X vs out-movers to X): NY 0.89, WA 0.82, IL 0.80, MA 0.79, TX 0.66, CO 0.60, FL 0.54, NV 0.48. Leavers to low-tax and Sun Belt states are the high earners. Arrivals from those states are not.
- **Bay ↔ Bay moves** are the cleanest like-for-like test. SF's other-Bay ratio is 0.62–0.93 after 2015, so SF loses higher-AGI filers to its neighbours. Marin, Napa, Sonoma and Contra Costa mostly gain richer filers from them (typically 1.1–1.9; Napa reached 2.5 in TY2020).

### Q4. California statewide: age and AGI class (`outputs/ca_age_profile.csv`, `ca_agi_class_profile.csv`, `ca_in_vs_out_age_standardised.csv`, `figs/fig4_ca_age_profile.png`)
**This section is statewide and interstate only. It is not Bay-specific.**
- **In-migrants are younger.** Primary taxpayers under 35 make up **61.7% of in-migrant returns in TY2021**, against 49.2% of out-migrants and 30.7% of non-migrants. In-migrants were the youngest group in every year 2011–2022, at 58–63% under 35.
- **At the same age, AGI is similar for the young and diverges for older filers.**
  - Ages 26–34, TY2021 year-2 mean AGI: in-migrants $95.6k, out-migrants $94.9k, non-migrants $77.3k.
  - Ages 55–64: out-migrants $255k, in-migrants $188k. Leavers include high-AGI late-career filers.
- **Reweighting in-migrants to the out-migrant age mix** raises the in/out ratio:

  | TY | raw | age-standardised |
  |---|---|---|
  | 2021 | 0.85 | 0.95 |
  | 2020 | 0.69 | 0.77 |
  | 2019 | 0.79 | 0.87 |
  | 2016 | 0.93 | 1.01 |

- **Rising income.** In-migrants' AGI grew faster from year 1 to year 2 than non-migrants' AGI in 10 of 11 years (TY2011–2021; the exception is TY2014).
  - All ages, TY2019: in-migrants +10.2%, non-migrants +4.8%.
  - Ages 26–34, TY2019: +21.0% vs +15.0%.
  - TY2021: +39% vs +22%.

  This is consistent with a "young, rising-income" replacement story, and with year-2 AGI understating arrivals' steady-state earnings.
- **AGI class, TY2021.** In-migrants are slightly more often below $25k (24.4% vs 22.4% of out-migrants) and less often above $200k (9.5% vs 12.3%).

### Q5. ACS mobility by income and tenure (`outputs/acs_2018_22_mobility_income_tenure.csv`)
Person-level individual income, region sums for 2018–22. The share earning $75k or more, among those with income:

| Group | Share $75k+ |
|---|---|
| In-movers from other states | 43.6% |
| In-movers from other CA counties | 41.2% |
| Same-house residents | 39.1% |
| Movers from abroad | 30.8% |

**Per person, domestic in-movers are not poorer than stayers.** The IRS per-return gap comes from how incomes are packaged into returns and from the timing of the move. B07010's top bin is only $75k+, so this is coarse. County sums double-count intra-Bay moves under "other CA county". MOEs are in the raw files and are not propagated.

## Puzzle status
**Largely resolved, and sharpened.** The low per-return mean of IRS in-movers is not driven by foreign or abroad arrivals, which the IRS data barely contain. It is not driven by origin geography either. The mechanical sources are:
- smaller filing units (1.46 vs 1.70 persons per return, region TY2021);
- younger primary filers;
- part-year and early-career year-2 incomes that then grow quickly.

These are what the rent data see as high-paying single and roommate renters.

What remains is a genuine **SF, Santa Clara and San Mateo pattern from 2017 to 2021**. Out-movers, especially those going to TX, NV, FL and CO and those aged 55–64 statewide, report AGI well above both arrivals and stayers. That is a **high-income exit** that pulls the place mean down.

## Caveats
- **Filers are not households or people.** Returns are tax units; roommates are separate returns. n2 changes definition at TY2019, and only within-year comparisons are made.
- **Year-2 AGI is part-year with respect to the move.** In-movers' AGI includes pre-arrival income, and out-movers' AGI includes income earned before leaving. Only *matched* returns are included: first-time filers count only if they were dependents in year 1; immigrants without a prior US return and deaths are excluded.
- **Suppression.** County cells under 20 returns (under 10 before 2018-19) are deleted or pooled. Named partner rows cover about 70% of the region's other-state in-movers, so the state pairs use named counties only. Bay–Bay rows are never suppressed.
- **Means, not medians, in nominal dollars.** TY2021 has a capital-gains spike. AGI is not welfare, and there is no cost-of-living adjustment.
- **Missing foreign rows.** The county files from 2016-17 to 2021-22 have no "Foreign – Overseas" row (only APO/FPO), so the foreign share is not comparable across that break.
- **The gross-migration age bands are statewide CA**, interstate and US-only. They cannot be applied to the Bay directly.

## Verification
`scripts/verify_by_hand.sh` (output in `outputs/verify_by_hand.txt`) recomputes the Santa Clara TY2021 domestic replacement ratio with `awk` on the raw CSV rows `97/000`:
- In: 45,074 returns, $8,297,899k, which is **$184,095 per return** and 1.484 persons per return.
- Out: 57,531 returns, $14,131,374k, which is **$245,631 per return** and 1.737 persons per return.
- Ratio **0.7495**, which matches the pipeline.

It also checks the CA TY2021 in-migrant under-35 share from `raw/2122inmigall.csv`: (57,085 + 99,986) / 254,427 = **0.6174**, which matches the pipeline.

## Files
- `run.sh`; `scripts/download.sh`, `analyze.py`, `acs.py`, `figures.py`, `verify_by_hand.sh`
- `outputs/flows_by_origin_type.csv`: unit × year × direction × origin type, with n1, n2, AGI, mean, persons per return, AGI per person and share
- `outputs/replacement_ratios.csv`, `replacement_ratio_partner_matched.csv`, `named_partner_flows.csv`, `other_state_flows_named.csv`, `region_state_pairs_pooled_2011_2021.csv`
- `outputs/ca_gross_migration_long.csv`, `ca_age_profile.csv`, `ca_agi_class_profile.csv`, `ca_in_vs_out_age_standardised.csv`
- `outputs/acs_2018_22_mobility_income_tenure.csv`, `verify_by_hand.txt`
- `figs/fig1_region_origins_and_agi.png`, `fig2_replacement_ratio_heatmap.png`, `fig3_persons_per_return.png`, `fig4_ca_age_profile.png`
