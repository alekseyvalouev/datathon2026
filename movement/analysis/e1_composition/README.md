# E1: How much of the Bay Area's rising AGI per return is composition?

**Question.** When county average income rises, how much is because *the same people got richer*, and how much is because of *who left and who arrived*?

**Data.** IRS SOI county-to-county migration files `countyinflowYYZZ.csv` and `countyoutflowYYZZ.csv`, 2011-12 through 2022-23 (12 file pairs, all downloaded OK), plus the IRS users guides (`raw/YYZZinpublicmigdoc.pdf`).

**Reproduce:** `./run.sh` downloads to `raw/`, runs `scripts/analyze.py`, then `scripts/figures.py`, then `scripts/verify_by_hand.sh`. All Python runs with `python3 -I`.

## Which year's income is in each file?

The users guide (2021-22, sections E.3/E.4) says **"The number of individuals and AGI are based on the year 2 tax return."** That holds for the inflow file, the outflow file and the non-migrant rows alike. File `YYZZ` matches returns filed in calendar years 20YY and 20ZZ, so its AGI is for **tax year 20ZZ−1**. For example, `2122` holds TY2021 income filed in 2022. Every series below is labelled by that tax year (TY2011 … TY2022).

So inside one file, stayers, in-movers and out-movers are all measured in the same income year (year 2):
- **Stayers** S (non-migrant row, `y1 = y2 = county`): year-2 AGI.
- **In-movers** I (inflow file, row `96/000` "Total Migration-US and Foreign"): year-2 AGI, earned **at or after arrival**.
- **Out-movers** O (outflow file, row `96/000`): year-2 AGI, i.e. what leavers earned **after they left** (at their destination).

For the **9-county region**, moves between two Bay counties count as staying. Stayers are the county non-migrants plus the intra-Bay rows of the inflow file. In-movers and out-movers are the county `96/000` totals minus the intra-Bay rows.

## The identity

Notation, for one geography, with means in $ per return:

- `M_t = (A_S,t + A_I,t) / (N_S,t + N_I,t)` is the **place mean**: everyone living in the county at the end of the file whose year-2 is TY t.
- `M*_{t+1} = (A_S,t+1 + A_O,t+1) / (N_S,t+1 + N_O,t+1)` is the **people mean**: everyone who lived in the county at t, followed wherever they went, at their TY t+1 income. These are the stayers plus the out-movers of file (t, t+1).
- `S̄_{t+1} = A_S,t+1 / N_S,t+1` is the stayers' mean.

Then, exactly:

```
M_{t+1} − M_t =  [M*_{t+1} − M_t]          people effect: residents at t followed to t+1 (income growth of the same population)
              + [S̄_{t+1} − M*_{t+1}]       exit effect:   removing out-movers (valued at their t+1 income)
              + [M_{t+1} − S̄_{t+1}]        entry effect:  adding in-movers (at their t+1 income)
composition = exit + entry = M_{t+1} − M*_{t+1}   ("place mean minus people mean", same income year)
```

Period changes are sums of the annual terms, and the place means telescope. **Composition share = Σcomposition / Σchange.**

**Why this approximation is defensible.** IRS never gives the same stayers' AGI in both years. Every composition term therefore compares groups **within one file and one income year**, so it contains no income growth and no year-to-year changes in method. Everything that crosses files goes into the people effect. That includes real income growth, ageing, differences between the matched populations of adjacent files (new filers and deaths are not in either file), ZIP-to-county codebook revisions, and the 2022-23 change in matching. Exit is computed before entry. That ordering is a choice, but the composition total does not depend on it.

## Results (nominal dollars)

### 1. Group means, 9-county region (`outputs/groups_by_unit_year.csv`)

| TY | stayers N | in N | out N | stayers $ | in-movers $ | out-movers $ |
|---|---|---|---|---|---|---|
| 2011 | 2,816,693 | 108,136 | 97,441 | 101,908 | 70,967 | 74,511 |
| 2016 | 3,027,524 | 133,067 | 162,358 | 138,080 | 91,854 | 105,147 |
| 2019 | 3,095,700 | 100,016 | 159,470 | 161,134 | 98,986 | 151,076 |
| 2020 | 3,067,764 | 97,366 | 170,450 | 170,719 | 106,307 | 175,366 |
| 2021 | 3,129,843 | 109,477 | 152,086 | 215,379 | 143,825 | 209,766 |
| 2022* | 3,163,399 | 108,679 | 136,648 | 184,101 | 114,973 | 147,213 |

\*2022-23 uses the new IRS method.

For TY2011–2021, the region's out-movers had a lower mean than stayers in 9 of 11 years (median −16%). In-movers were lower still (median −33%). Out-movers' mean is below stayers' in **all 11 years** in Alameda, Marin, Napa, San Mateo and Solano, but in only 8/11 in SF (above stayers in TY2019–2021) and 9/11 in Santa Clara.

### 2. Decomposition, TY2011 → TY2021 (`outputs/decomposition_period.csv`)

| Geography | mean 2011 | mean 2021 | change | people | exit | entry | composition | **comp. share** |
|---|---|---|---|---|---|---|---|---|
| Bay region (9 co.) | 100,764 | 212,961 | 112,197 | 121,124 | +6,598 | −15,526 | −8,928 | **−8.0%** |
| San Francisco | 109,486 | 264,795 | 155,309 | 191,875 | −4,057 | −32,510 | −36,567 | **−23.5%** |
| Santa Clara | 116,527 | 263,302 | 146,775 | 162,987 | +11,632 | −27,844 | −16,212 | **−11.0%** |
| Alameda | 79,968 | 159,860 | 79,892 | 81,802 | +9,172 | −11,081 | −1,910 | **−2.4%** |
| San Mateo | 132,450 | 325,174 | 192,724 | 192,783 | +32,521 | −32,580 | −59 | **−0.0%** |
| Contra Costa | 95,218 | 160,743 | 65,525 | 63,910 | +12,960 | −11,345 | +1,615 | **+2.5%** |
| Marin | 143,900 | 317,140 | 173,241 | 149,046 | +38,831 | −14,637 | +24,194 | **+14.0%** |
| Napa | 75,882 | 139,796 | 63,914 | 47,933 | +15,202 | +779 | +15,981 | **+25.0%** |
| Solano | 62,581 | 87,917 | 25,336 | 26,323 | +10,050 | −11,036 | −986 | **−3.9%** |
| Sonoma | 66,130 | 118,353 | 52,223 | 45,973 | +3,974 | +2,276 | +6,250 | **+12.0%** |

Reading the table:
- **Exit effect.** Lower-income leavers raised the mean in 8 of 9 counties and in the region. That is the "exit hides inequality" mechanism, and it is real: for the region it accounts for +5.9% of the rise, for Marin +22%, Napa +24%, Contra Costa +20% and Solano +40%.
- **Net composition.** In the large job-centre counties (SF, Santa Clara, the region) the net effect is negative. In-movers report much lower year-2 AGI and outweigh the exit effect. Composition adds to the measured rise only in Marin, Napa, Sonoma and Contra Costa.
- **SF's exit term is negative.** SF's TY2019–2021 leavers (the COVID out-migration) had *higher* AGI than the people who stayed.
- **Including TY2022** (new method), the region's composition share is −12.0% and SF's is −42.9%. The TY2021→22 step is a large fall in the people term (the TY2021 capital-gains peak plus the method break). Treat this column as indicative only. TY2016→2021 gives the same pattern (region −9.1%, SF −27.6%).

### 3. Where out-movers go (`outputs/destinations_*.csv`; pooled files 2011-12..2021-22, AGI after the move)

| Origin | stayers $ | → Central Valley | → rest of CA | → other Bay | → out of state |
|---|---|---|---|---|---|
| San Francisco | 167,538 | 76,495 (−54%, 2.9% of leavers) | 147,663 (−12%) | 169,540 (+1%) | 183,717 (+10%, 25.6%) |
| Santa Clara | 177,194 | 72,581 (−59%, 11.0%) | 125,383 (−29%) | 180,517 (+2%) | 165,154 (−7%, 26.5%) |
| Alameda | 112,294 | 68,388 (−39%, 12.5%) | 91,441 (−19%) | 110,268 (−2%) | 110,302 (−2%, 22.6%) |

The flows with the lowest AGI go to the Central Valley. From Santa Clara: Merced $52k (−71% vs stayers), Stanislaus $55k (−69%), Fresno $62k, Sacramento $82k, San Joaquin $85k (19.8k returns, its 5th-largest destination). From Alameda: San Joaquin (34.7k returns, $74k, −34%), Sacramento (−40%) and Stanislaus (−51%). Out-of-state movers from SF are richer than SF's stayers (NY +21%, WA +23%, TX +28%). Movers from Santa Clara and Alameda to OR, AZ and NV are at or below their stayers. Figure: `figs/c_top_destinations.png`.

**Verification.** `scripts/verify_by_hand.sh` recomputes SF TY2020→2021 with `awk` directly on the raw CSVs. It gives change +71,743 = people +81,111, exit −3,623, entry −5,745, which matches the pipeline to the dollar (`outputs/verify_by_hand.txt`). The script also checks that non-migrant rows are identical in the inflow and outflow files for every county-year.

## Caveats
- **AGI is not welfare.** These are tax-filer means in nominal dollars, dominated by the top tail (capital gains: note the TY2021 spike). IRS publishes no medians. A mean can rise with no change for typical households. AGI is not household income, ignores cost of living, and leaves out non-filers.
- **Filers are not people.** These are returns (n1); exemptions (n2) are in the CSVs. Only returns matched across two consecutive years are included, so first-time filers, deaths and non-filers are excluded.
- **Movers' AGI is year-2 income**, partly a part-year amount. In-movers' AGI may include income earned before arrival. Out-movers' AGI is earned partly at the destination, so it shows their **post-move** outcome. The data cannot show whether that outcome improved or worsened. That would need person-level panels such as the California Policy Lab credit data.
- **Suppression.** County-to-county cells below 20 returns (below 10 before 2018-19) are pooled into "Other flows" or deleted (−1). Totals (`96/000`) are complete, so the decomposition is unaffected. Named-county destinations cover 92–93% of out-movers for SF, Santa Clara and Alameda, but only 71–79% for Napa, Marin, Solano and Sonoma (`outputs/destinations_coverage.csv`). Suppressed Bay rows per file are listed in `outputs/suppression_counts.csv`.
- **2022-23 methodology change:** about 5% more matched returns and new dominance and suppression rules. It contaminates the TY2021→22 people term. Within-file composition terms are less affected.
- **Codebook revisions** (ZIP→county) move returns between non-migrant totals across years. They land in the people effect.
- **Mailing address ≠ residence**, and some moves happen after the tax year.

## Not done
- **ACS B07010/B07411 (optional):** the Census API now redirects key-less requests to `missing_key.html` (HTTP 302), so the out-mover vs stayer comparison from ACS was not run. It needs a free API key.

## Files
- `scripts/download.sh`, `scripts/analyze.py`, `scripts/figures.py`, `scripts/verify_by_hand.sh`, `run.sh`
- `outputs/groups_by_unit_year.csv`, `decomposition_annual.csv`, `decomposition_period.csv`, `destinations_county.csv`, `destinations_out_of_state.csv`, `destinations_by_group.csv`, `destinations_coverage.csv`, `suppression_counts.csv`, `verify_by_hand.txt`
- `figs/a_region_means_by_status.png`, `figs/b_decomposition_by_county.png`, `figs/c_top_destinations.png`
