# Precinct-level election results and precinct boundary data for Bay Area local elections (as of 14 Nov 2026)

Research note on method: pages were read through a fetch tool that summarises page content; several target sites (sfelections.org results pages, pastresults.contracostavote.gov, nature.com) were blocked by the session allowlist and could not be opened. Items marked "NOT VERIFIED" come from search-result titles/URLs or were not opened at all. Nothing below was downloaded or opened as a data file; file contents (column layouts, precinct ID formats) are unverified unless stated.

## 1. UC Berkeley Statewide Database (SWDB): which elections, which geography files, local contests, latest vintage

### Takeaway
SWDB is the single best source for this project: for every county it publishes precinct-level Statement of Vote (SOV) CSVs, precinct shapefiles (SRPREC, MPREC) and precinct-to-2020-census-block crosswalks, and since the 2022 primary it also publishes local candidate contests (county, city, school district, community college, special district) at precinct level. Local ballot measures are NOT in the local SOV files. The latest election on the site is the June 2026 primary (still being updated county by county in Oct-Nov 2026); the November 2026 general is not there.

### Cited Findings
- Precinct-level SOV for statewide and district races (Assembly, Congress, State Senate, Board of Equalization) goes back to the 2000 primary; 1992-2000 is on a separate page. Statement of Registration (SOR) files come in REG, ABS, MAIL (2012+), POLLV, VOTE, NONVOTE (2012+) variants. Precinct types are sv, sr (formerly ss), rg, rr; only the sr precinct is common to both SOV and SOR data. SOV codebooks are county- and election-specific (candidate columns differ by county). — [SWDB precinct data metadata](https://statewidedatabase.org/info/metadata/precinct_data.html)
- FAQ is internally inconsistent on local races: one answer says SWDB "only receives funding to process statewide races and does not collect data for local races like city council and mayor"; a later answer says "Starting with the 2022 Primary Election, local contests were added to the published SOV datasets" at county, city, school district, community college district and special district levels, and "Local measures are not included in the local SOV dataset." — [SWDB FAQ](https://statewidedatabase.org/faq.html)
- FAQ precinct definitions: MPREC = geographic "map precinct" built by SWDB to reflect county registration precincts; RR = non-geographic version of MPREC (aggregated RG precincts); SR = geographic consolidation containing whole RR and SV precincts (SS and SR are equivalent names); SV = voting precincts; SOV results are available by SV and SR. Precinct-to-block conversion files are built by geocoding total registrants and carry fields such as BLKREG and PCTBLK for proportional allocation. — [SWDB FAQ](https://statewidedatabase.org/faq.html)
- Licence: no formal licence stated; FAQ says "The Statewide Database is a free public resource" and "All items ready for download via this website are free." — [SWDB FAQ](https://statewidedatabase.org/faq.html)
- 2024 general (G24) data page lists, statewide and per county: SOV by SV precinct and SR precinct; "SOV Local" files for county, city, school, CCD, special district, each by SV and SR precinct; Registration, All_VBM, All_Poll and Voters files by RG, RR, SR precinct and by 2020 census block. SOV by census block is not offered (block files exist only for registration/VBM/poll/voters). CSV for everything; DBF for all but local SOV. — [SWDB G24 data](https://statewidedatabase.org/d20/g24.html)
- G24 URL patterns: statewide zips `https://statewidedatabase.org/pub/data/G24/state/state_g24_[dataset]_by_g24_[geography].zip`; county files `https://statewidedatabase.org/pub/data/G24/c###/c###_g24_[dataset]_by_g24_[geography].csv`; local SOV `.../c###/c###_g24_sov_local_[city|school|ccd|special|county]_by_g24_[svprec|srprec].csv`; county codebooks `###.codes`. — [SWDB G24 data](https://statewidedatabase.org/d20/g24.html)
- G24 caveats: precincts with fewer than ten voters are masked (asterisks in CSV, zeros in DBF); 2024 precinct files "currently include artifacts that will be removed in an update"; state-level SOVs may be posted before local SOVs; "no data yet" = still processing, "unavailable" = county did not provide. Local SOV availability varies by county. — [SWDB G24 data](https://statewidedatabase.org/d20/g24.html)
- G24 geography: statewide shapefiles `https://statewidedatabase.org/pub/data/G24/state/srprec_state_g24_v01_shp.zip` and `mprec_state_g24_v01_shp.zip`; per county `https://statewidedatabase.org/pub/data/G24/cNNN/srprec_NNN_g24_v01_shp.zip` (also `.gpkg.zip`, `.geojson.zip`, and the same for `mprec_`). — [SWDB G24 geography and conversion files](https://statewidedatabase.org/d20/g24_geo_conv.html)
- G24 conversion files (statewide and per county, CSV): SRPREC to 2020 BLK (`state_g24_sr_blk_map.csv` / `cNNN_g24_sr_blk_map.csv`), RGPREC to 2020 BLK (`..._rg_blk_map.csv`), 2020 BLK to MPREC (`blk_mprec_NNN_g24_v01.csv`), RG to RR to SR to SVPREC (`cNNN_rg_rr_sr_svprec_g24.csv`), MPREC to SRPREC (`mprec_srprec_NNN_g24.csv`), SRPREC to CITY (`cNNN_g24_srprec_to_city.csv`). — [SWDB G24 geography and conversion files](https://statewidedatabase.org/d20/g24_geo_conv.html)
- Bay Area county codes used in file names: Alameda 001, Contra Costa 013, Marin 041, Napa 055, San Francisco 075, San Mateo 081, Santa Clara 085, Solano 095, Sonoma 097. — [SWDB G24 geography and conversion files](https://statewidedatabase.org/d20/g24_geo_conv.html)
- Caveat on that page: descriptive text still says "2010 BLK" while download links are labelled "2020 BLK"; share-of-precinct values in the BLK-to-MPREC file are flagged as unreliable. — [SWDB G24 geography and conversion files](https://statewidedatabase.org/d20/g24_geo_conv.html)
- Equivalent geography/conversion pages exist for other cycles, e.g. 2021 recall [s21](https://statewidedatabase.org/d20/s21_geo_conv.html), 2020 general [g20](https://statewidedatabase.org/d10/g20_geo_conv.html), 2020 primary [p20](https://statewidedatabase.org/d10/p20_geo_conv.html), 2016 general [g16](https://statewidedatabase.org/d10/g16_geo_conv.html), and a November 2025 special-election data page [s25](https://statewidedatabase.org/d20/s25.html) (the s25 page was not opened; existence only).
- Latest vintage: the home page's update log is all 2026 primary (P26) county updates — 11/12/2026 Napa and Tulare; 10/30/2026 Kern, Mono, Santa Barbara, Santa Cruz, Solano, Trinity; 10/8/2026 includes Sonoma. No 2026 general election data or announcement. — [SWDB home page](https://www.statewidedatabase.org)
- P26 page: Alameda (001), Contra Costa (013) and Marin (041) show linked SOV, registration, VBM, poll and voter files with codebooks; the statewide row shows "no data yet"; local SOV files carry contest/candidate info inside the file (no separate codebook). — [SWDB P26 data](https://statewidedatabase.org/d20/p26.html)

### Inferences
- Join recipe: county local SOV (by SRPREC) -> `cNNN_g24_sr_blk_map.csv` (SRPREC to 2020 block with registrant-share weights) -> aggregate blocks to tracts (first 11 digits of block GEOID) or to ZCTAs via a Census block-to-ZCTA relationship file. Alternatively, spatially join Zillow lat/lon points directly into the SRPREC shapefile. This is achievable in hours.
- Usable multi-cycle panel of local candidate contests from SWDB alone: P22, G22, P24, G24, and P26 for counties already posted (5 elections at most). G26 will not be on SWDB for months, judging by P26 (June) still being updated in mid-November.
- SRPREC codes are election-specific; panels across elections must go through census blocks, not precinct IDs.
- For a spending-vs-vote-share design, the absence of local measures in SWDB means measure results must come from county registrar SOVs.

### Gaps
- P26 status for Napa, San Francisco, San Mateo, Santa Clara, Solano, Sonoma was not readable (page truncated); the home-page log implies Napa, Solano and Sonoma were updated in Oct-Nov 2026.
- Whether local SOV files exist for all nine Bay Area counties in each of P22/G22/P24/G24 was not checked county by county.
- Exact column layout of local SOV files and whether RCV contests (SF, Oakland, Berkeley, San Leandro, Albany) appear as first-choice counts only: not verified.
- The 2022 primary/general pages (d20/p22, d20/g22) were not opened; local-contest availability from P22 rests on the FAQ statement.

## 2. San Francisco Department of Elections: SOV, cast vote records, DataSF precinct shapefiles

### Takeaway
San Francisco has the deepest archive in the region: a results index listing every election back to 1995, with per-election result pages hosted on sfelections.org, plus precinct boundary datasets on DataSF. The per-election result pages (where the SOV spreadsheets and cast vote record downloads would be) could not be opened in this session, so file formats there are unverified.

### Cited Findings
- Results index lists all elections 1995-2026, including Nov 2024, Mar 2024, Nov 2022, Jun 2022, Feb and Apr 2022 specials, Nov 2020, Nov 2019, Nov 2018, Jun 2018, back to Nov 1995; the Nov 3, 2026 entry links to `https://www.sfelections.org/results/20261103w/index.html`. — [SF results index](https://www.sf.gov/results)
- November 2026 reporting schedule: four election-night reports; daily preliminary updates at about 4 p.m. Nov 4-13 (except Nov 11); updates continue afterwards as ballots are counted. For ranked-choice contests, Reports 1 and 4 include round-by-round results. — [SF results reporting timeline](https://www.sf.gov/news-the-department-of-elections-announces-results-reporting-timeline-for-the-november-3-2026-consolidated-general-election)
- Preliminary results reports numbered up to at least 11 had been issued for the November 2026 election. — [SF Report 10 news item](https://www.sf.gov/news-the-department-of-elections-releases-preliminary-results-report-10-and-update-on-the-number-of-remaining-ballots-to-count-for-the-november-3-2026-consolidated-general-election); [SF Report 11 news item (zh-hant)](https://www.sf.gov/zh-hant/news-the-department-of-elections-releases-preliminary-results-report-11-and-update-on-the-number-of-remaining-ballots-to-count-for-the-november-3-2026-consolidated-general-election) (titles only; pages not opened)
- Election page for Nov 2026 names the Board of Education contest, links the local Voter Information Pamphlet (`https://media.api.sf.gov/documents/N26_EN_VIP.pdf`) and a polling place spreadsheet (`https://api.sf.gov/documents/63956/Polling_Place_List_Nov_3_2026_as_of_09_29_2026.xlsx`). — [SF Nov 3, 2026 election page](https://www.sf.gov/november-3-2026-consolidated-general-election)
- DataSF "Election Precincts - Current, Defined 2022", dataset id d6x4-hefw (`https://data.sf.gov/d/d6x4-hefw`): precincts redefined in 2022 on 2020 Census geography (with exceptions); formats JSON, XML, CSV, KML, KMZ, GeoJSON; first published 25 Aug 2023, updated 13 Mar 2024. — [Data.gov catalog entry](https://catalog.data.gov/dataset/election-precincts-current-defined-2022)
- Historical precinct layers also exist: "Election Precincts - Historical, Defined 2012" and a 2002-defined layer. — [Data.gov: Historical, Defined 2012](https://catalog.data.gov/dataset/election-precincts-historical-defined-2012); [Data.gov: 2002 election precincts](https://catalog-beta.data.gov/dataset/2002-election-precincts) (titles only)

### Inferences
- SF precinct lines are stable within a decade (2012-defined lines for 2012-2021 elections, 2022-defined lines from 2022), which makes SF the easiest county for a multi-cycle precinct panel. Which 2022 election first used the new lines was not confirmed.
- SWDB local SOV plus SRPREC shapefile for county 075 is a ready-made fallback if the SF result pages are awkward to parse.

### Gaps
- Could not open sfelections.org result pages: the formats of the SF Statement of Vote (commonly Excel/PDF) and the cast vote record downloads (Dominion CVR JSON zip), and the years for which CVRs are posted, are NOT VERIFIED here. Team should open `https://www.sfelections.org/results/20241105w/index.html`-style pages directly (URL pattern inferred from the 2026 link; unverified).
- Whether DataSF hosts tabular election-result datasets (as opposed to boundaries) was not confirmed.
- Licence of DataSF precinct layers not stated on the catalog page.
- List of SF local contests on the Nov 2026 ballot not retrieved.

## 3. County registrars: Alameda, Santa Clara, San Mateo, Contra Costa, Marin, Sonoma, Solano, Napa

### Takeaway
Alameda, San Mateo and Marin post machine-readable precinct canvasses (XLSX or CSV) alongside PDFs; Santa Clara posts Statement of Vote files (Excel or PDF, varying by election) back to 2000. Contra Costa and Sonoma run searchable past-results sites that could not be opened here. Alameda's cast vote records are by request form, not direct download.

### Cited Findings
**Alameda**
- Per-election pages follow `https://acvote.alamedacountyca.gov/election-information/elections?id=NNN` (id=259 is the June 2, 2026 primary; id=252 is the Nov 5, 2024 general). — [ACVote June 2026 page](https://acvote.alamedacountyca.gov/election-information/elections?id=259); [ACVote id=252](https://acvote.alamedacountyca.gov/election-information/elections?id=252)
- June 2026 downloads: Statement of Vote (precinct canvass) PDF and XLSX — `https://acvote.alamedacountyca.gov/acvote-assets/02_election_information/PDFs/20260602/Results/PrecinctCanvassJun02.xlsx` — plus District Canvass PDF/XLSX; certified results web page at `https://alamedacountyca.gov/rovresults/259/`. — [ACVote June 2026 page](https://acvote.alamedacountyca.gov/election-information/elections?id=259)
- Cast vote record is not a direct download; the page links to a request form (Airtable). — [ACVote June 2026 page](https://acvote.alamedacountyca.gov/election-information/elections?id=259)
- Special-election SOVs are posted as PDFs under `/acvote-assets/02_election_information/SOV/YYYYMMDD/`, e.g. the April 15, 2025 Oakland special election. — [ACVote Oakland special SOV PDF](https://acvote.alamedacountyca.gov/acvote-assets/02_election_information/SOV/20250415/Statement%20of%20Vote%20-%20Oakland%20Special%20Election.pdf) (title only)

**Santa Clara**
- Past results listed from 2000 onward; each election has Summary Results and a Statement of Vote, sometimes labelled xls and/or PDF (e.g. Nov 2, 2021 has both); "Precinct Consolidation(s)" files in xls/PDF for some elections (e.g. Nov 8, 2022). No shapefiles on that page. — [Santa Clara past election information and results](https://vote.santaclaracounty.gov/elections/past-election-information-and-results)

**San Mateo**
- Past results listed individually from 1991, with decade PDFs back to the 1950s. — [San Mateo past elections results](https://smcacre.gov/elections/past-elections-results)
- Nov 5, 2024 page offers: results CSV (`https://smcacre.gov/media/7580/download?attachment`), Statement of the Vote PDF, Precinct Turnout PDF, Precinct Consolidations PDF, and a results portal whose Reports tab exports contest or precinct reports as CSV or PDF (`https://www.livevoterturnout.com/ENR/sanmateocaenr/16/en/buXnk_Index_16.html`). — [San Mateo Nov 5, 2024 results](https://smcacre.gov/elections/november-5-2024-election-results)
- That election covers council/mayor races in 19 cities, many school boards, a Board of Supervisors seat, and dozens of local measures. — [San Mateo Nov 5, 2024 results](https://smcacre.gov/elections/november-5-2024-election-results)
- San Mateo certified Nov 2024 on Dec 5, 2024 and the Nov 2025 special on Dec 4, 2025. — [SMC news, Nov 2024 certification](https://smcacre.gov/elections/news/results-certified-november-5-2024-presidential-general-election); [SMC news, Nov 2025 certification](https://smcacre.gov/elections/news/results-certified-november-4-2025-statewide-special-election) (titles only)

**Marin**
- Nov 4, 2025 special: "Statement of votes cast (precinct breakdown)" in PDF and Excel (`11-25_SOVC.Final_.xlsx`). — [Marin Nov 4, 2025 results](https://www.marincounty.gov/departments/elections/november-4-2025-special-election/election-results-110425)

**Contra Costa**
- A past-results site exists at `pastresults.contracostavote.gov` with contest search and precinct-granularity views (URLs of the form `/eng/contests/search/file_id:53/show_granularity_dt_id:7/`). — [Contra Costa past results (search hit)](https://pastresults.contracostavote.gov/eng/contests/search/file_id:53/show_granularity_dt_id:7/.pdf) (NOT VERIFIED; site blocked in this session)

**Sonoma**
- A similar site exists at `electionstats.sonomacounty.ca.gov`. — [Sonoma ElectionStats (search hit)](https://electionstats.sonomacounty.ca.gov/contests/get_source_documentation/1446/1) (NOT VERIFIED; not opened)

### Inferences
- The Contra Costa and Sonoma URL structures (`/contests/search/`, `/contests/get_source_documentation/`, `/voter_stats/view/`) match the ElectionStats platform, which normally offers per-contest precinct tables with CSV download; treat as likely but confirm.
- For a 2-day event, hand-harmonising nine counties' SOV layouts across several cycles is too expensive. Practical scope: SWDB local SOV for candidates in all nine counties, plus registrar XLSX/CSV for measures in two or three counties (Alameda, San Mateo, San Francisco).
- Santa Clara's "Precinct Consolidation" spreadsheets and San Mateo's consolidation PDFs are the keys for mapping reporting precincts back to base precincts.

### Gaps
- Solano and Napa: no sources found or opened; where and in what format they post precinct results is unknown.
- Alameda RCV: whether round-by-round tables and ballot-level CVRs for Oakland/Berkeley/San Leandro are posted for download anywhere other than the request form was not established. The Nov 2024 page (id=252) and the Nov 2026 page were not opened.
- Santa Clara: direct file URLs not captured; whether recent SOVs (2022-2024) are Excel was not confirmed.
- Marin: archive depth and URL paths unknown.
- County precinct shapefiles from county GIS/open-data portals were not researched; SWDB shapefiles are the documented substitute.
- Voting-system vendor per county (Dominion, Hart, ES&S) not verified.

## 4. Aggregators: OpenElections, MEDSL, Redistricting Data Hub, VEST, CEDA, Ballotpedia, American Local Government Elections Database

### Takeaway
CEDA and the American Local Government Elections Database give contest-level (not precinct-level) local results and are the realistic sources for a many-contest spending regression. The national precinct aggregators could mostly not be verified in this session and are not known from this research to add Bay Area local contests beyond what SWDB already has.

### Cited Findings
- CEDA is a joint project of the Center for California Studies and the Institute for Social Research at Sacramento State with the Secretary of State; covers city, county, school district and local ballot measure elections 1995 through 2025; annual reports are completed each July for the prior calendar year; the SOS page lists PDFs only, e.g. `https://elections.cdn.sos.ca.gov/county-city-school-district-election-results/2025/county.pdf`, `.../2025/city.pdf`, `.../2025/school-district.pdf`. — [CA SOS: County, City, School District & Ballot Measure Election Results](https://www.sos.ca.gov/elections/county-city-school-district-ballot-measure-election-results)
- The Secretary of State does not certify or compile local election results. — [CA SOS: CEDA page](https://www.sos.ca.gov/elections/county-city-school-district-ballot-measure-election-results)
- American Local Government Elections Database: about 78,000 candidates in 57,000 contests over the last three decades, seven local offices, most medium and large US cities and counties, with candidate partisanship and demographics and electoral outcomes; replication data on OSF at `https://doi.org/10.17605/OSF.IO/MV5E6`. — [de Benedictis-Kessner publication page](https://jdbk.scholars.harvard.edu/publication/american-local-government-elections-database)
- Redistricting Data Hub hosts general-election results joined to precinct boundaries from partners MGGG, PGP and VEST for all 50 states for 2016, 2018 and 2020, as shapefiles; a year selector also lists 2022, 2023, 2024 and 2026 (state coverage per year not stated). Underlying results come from Secretaries of State, MEDSL and OpenElections. — [RDH: Precinct boundaries and election results](https://redistrictingdatahub.org/aboutourdata/precinct-boundaries-and-election-results/)
- A University of Florida Election Lab page hosts "CA 2020 precinct-level election results" (VEST). — [UF Election Lab: CA 2020](https://election.lab.ufl.edu/dataset/ca-2020-precinct-level-election-results/) (title only)
- MEDSL published a write-up of its 2024 precinct project. — [MEDSL: Inside the 2024 precinct project](https://electionlab.mit.edu/articles/inside-2024-precinct-project) (title only)

### Inferences
- VEST/RDH California files are derived from SWDB and carry statewide contests; they are unlikely to add local contests. Go to SWDB directly.
- CEDA plus campaign-finance totals gives a contest-level panel (1995-2025) with far more observations than a precinct design; precinct data then serves for within-city heterogeneity (demographics, housing values) rather than for identifying spending effects, since spending varies at contest level, not precinct level.
- The November 2026 contests will not be in CEDA until about July 2027, given the stated annual schedule.

### Gaps
- OpenElections California (`github.com/openelections/openelections-data-ca`): repository not opened; coverage and whether local contests are included unknown.
- MEDSL precinct returns: years, California coverage and office scope not verified.
- VEST Harvard Dataverse entries not opened; years and licence unverified.
- CEDA machine-readable (Excel) files: the SOS page shows PDFs only; whether Sacramento State distributes spreadsheets (csus.edu) was not confirmed.
- ALGED exact year range, office list, population threshold and licence not verified (Nature article blocked).
- Ballotpedia: not researched beyond a search hit for [Municipal elections in Santa Clara County (2024)](https://ballotpedia.org/Municipal_elections_in_Santa_Clara_County,_California_(2024)); no bulk download identified.
- RDH account requirement, terms and API not confirmed.

## 5. Status of the November 3, 2026 general election results

### Takeaway
As of 14 November 2026 the election is uncertified and results are preliminary and still changing. San Francisco's stated certification deadline is December 3, 2026 (earliest possible November 25). Final precinct-level SOVs for November 2026 should not be expected during a mid-November datathon; SWDB has nothing for it.

### Cited Findings
- "State law requires the Department to certify the election by December 3, 2026"; the Department may need the full 30 days California law allows; vote-by-mail ballots postmarked by Election Day and received within seven days are counted. — [SF: An accurate and complete vote count takes time](https://www.sf.gov/an-accurate-and-complete-vote-count-takes-time)
- Earliest SF certification date is Wednesday, November 25, 2026; daily preliminary reports ran Nov 4-13. — [SF results reporting timeline](https://www.sf.gov/news-the-department-of-elections-announces-results-reporting-timeline-for-the-november-3-2026-consolidated-general-election)
- SWDB's newest election is the June 2026 primary, still receiving county updates on 11/12/2026. — [SWDB home page](https://www.statewidedatabase.org)
- Precedent for timing: Alameda's June 2, 2026 primary shows certified results with zero unprocessed ballots as of June 25, 2026, with SOV in PDF and XLSX. — [ACVote June 2026 page](https://acvote.alamedacountyca.gov/election-information/elections?id=259)

### Inferences
- The 30-day canvass implies the same December 3, 2026 deadline for all nine counties; this was confirmed only on the San Francisco page.
- Use November 2024 and November 2022 (and June 2026 where posted) as the analysis cycles; treat November 2026 as out of scope or as preliminary contest-level totals only.

### Gaps
- Whether any Bay Area county has already posted preliminary precinct-level files for November 2026 was not verified (SF result page blocked; Alameda Nov 2026 page not located).
- Secretary of State's own statement of county canvass and state certification dates for 2026 was not opened.

## 6. Practical issues: consolidation, vote-by-mail precincts, joins to tracts/zip, ranked-choice

### Takeaway
Precinct identifiers are not stable across elections, small precincts are masked, and SWDB allocates precincts to blocks by registrant share; all cross-election or demographic joins should run through 2020 census blocks. Ranked-choice contests need separate handling.

### Cited Findings
- SWDB distinguishes registration precincts (RG/RR/MPREC) from voting precincts (SV) and builds SR precincts as consolidations containing whole RR and SV precincts; crosswalk `cNNN_rg_rr_sr_svprec_g24.csv` links them. — [SWDB FAQ](https://statewidedatabase.org/faq.html); [SWDB G24 geography and conversion files](https://statewidedatabase.org/d20/g24_geo_conv.html)
- Precinct-to-block conversion is based on geocoded total registrants (fields such as BLKREG, PCTBLK), so block-level vote estimates are proportional allocations, not observed counts. — [SWDB FAQ](https://statewidedatabase.org/faq.html)
- Precincts under ten voters are masked in SWDB files. — [SWDB G24 data](https://statewidedatabase.org/d20/g24.html)
- SWDB publishes separate All_VBM and All_Poll voter files by precinct and block. — [SWDB G24 data](https://statewidedatabase.org/d20/g24.html)
- An SRPREC-to-city file exists per county (`cNNN_g24_srprec_to_city.csv`), useful for restricting to a city's contest. — [SWDB G24 geography and conversion files](https://statewidedatabase.org/d20/g24_geo_conv.html)
- Counties publish their own consolidation tables per election (Santa Clara xls/PDF; San Mateo PDF). — [Santa Clara past results](https://vote.santaclaracounty.gov/elections/past-election-information-and-results); [San Mateo Nov 5, 2024 results](https://smcacre.gov/elections/november-5-2024-election-results)
- SF precincts were redrawn in 2022 on 2020 Census geography, with earlier 2012 and 2002 vintages. — [Data.gov: Election Precincts - Current, Defined 2022](https://catalog.data.gov/dataset/election-precincts-current-defined-2022)
- SF publishes round-by-round RCV results in selected reports. — [SF results reporting timeline](https://www.sf.gov/news-the-department-of-elections-announces-results-reporting-timeline-for-the-november-3-2026-consolidated-general-election)

### Inferences
- Zip-code joins: precinct -> block -> ZCTA is approximate (ZCTAs are not USPS zip codes); with Zillow lat/lon, a point-in-polygon join to SRPREC polygons is cleaner than going via zip.
- County registrar precinct IDs (reporting precincts) will not match SWDB SRPREC codes directly; mixing registrar measure results with SWDB geography needs the RG/RR/SR/SV crosswalk or the county consolidation table, which is a real time risk in two days.
- For RCV cities, use first-choice vote share as the outcome for comparability with plurality contests; ballot-level CVR analysis is a stretch goal.
- Because independent-expenditure totals vary by contest and not by precinct, precinct-level outcomes add statistical power only for interaction questions (e.g. spending effect by neighbourhood income), not for the main effect.

### Gaps
- How each Bay Area county reports vote-by-mail ballots (assigned to home precinct vs separate VBM precincts) was not verified per county.
- No source was found quantifying how much SRPREC boundaries changed between G22, G24 and P26 in Bay Area counties.
