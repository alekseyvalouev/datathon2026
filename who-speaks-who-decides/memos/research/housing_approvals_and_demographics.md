# Housing approvals, permits and neighborhood demographics: public data sources for the 9-county Bay Area (as of 14 Nov 2026)

Method note for the report writer: findings under "Cited Findings" were read from the linked pages on 14 Nov 2026. Direct API calls (curl) to data.ca.gov / data.sfgov.org were blocked from the research sandbox, and data.sf.gov / data.sfgov.org pages could not be fetched, so column-level schemas for the San Francisco datasets were NOT verified; they are flagged in Gaps. Anything in "Inferences" is my reasoning or unverified background knowledge and should be labelled as such.

## 1. California HCD Annual Progress Report (APR) data: tables, fields, years, addresses/APNs and approval dates

### Takeaway
The HCD APR dataset on data.ca.gov is the single best cross-jurisdiction, project-level source: 12 bulk CSV tables (A, A2, C, D, E, F, F2, G, H, I, K, L) with data dictionaries, last updated 23 Oct 2026, raw data from reporting year 2018 onward. Table A (applications) and Table A2 (entitlements/permits/completions) carry APN, street address, local tracking ID, units by income, and approved/disapproved status, which is what is needed to join to hearing comments. It is self-reported by jurisdictions, and Table A's outcome field is a status label, not a hearing record.

### Cited Findings
- Dataset name: "Housing Element Annual Progress Report (APR) Data by Jurisdiction and Year"; publisher California Department of Housing and Community Development; first published 28 Jul 2022; last updated 23 Oct 2026. Content is what local jurisdictions reported to HCD on APR forms required by Government Code 65400. — [catalog.data.gov mirror of data.ca.gov](https://catalog.data.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year)
- 24 resources: 12 CSV tables + 12 DOCX data dictionaries. Bulk CSV URLs (dataset UUID 81b0841f-2802-403e-b48e-2ef4b751f77c): — [catalog.data.gov](https://catalog.data.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year)
  - Table A: https://publish.data.ca.gov/dataset/81b0841f-2802-403e-b48e-2ef4b751f77c/resource/c78b769d-cc02-4050-91ef-79ded665b5a8/download/tablea.csv
  - Table A2: https://publish.data.ca.gov/dataset/81b0841f-2802-403e-b48e-2ef4b751f77c/resource/fe505d9b-8c36-42ba-ba30-08bc4f34e022/download/tablea2.csv
  - Table C: .../resource/a07dcd90-56bd-4a5e-9ce6-809e1f3fc121/download/tablec.csv
  - Table D: .../resource/37724925-2014-4646-ade8-3ba9f3ff9fb8/download/tabled.csv
  - Table E: .../resource/ec5124e6-a6ce-435d-82b1-0c963aaf15dd/download/tablee.csv
  - Table F: .../resource/d8eb9333-7e85-4007-a96a-1fb06387b2e2/download/tablef.csv
  - Table F2: .../resource/16e640ab-c7e1-433c-8e4d-aa5a0a1270d1/download/tablef2.csv
  - Table G: .../resource/f68020cc-f245-43e1-a8ec-d7d2d6e42eae/download/tableg.csv
  - Table H: .../resource/8e0e9d86-9a8a-4b3c-8089-8262404d9401/download/tableh.csv
  - Table I: .../resource/575fe458-9e90-4a15-bca6-91e2bbcc463a/download/tablei.csv
  - Table K: .../resource/c1407d6d-adc5-4f32-9cc9-1f022c4e2deb/download/tablek.csv
  - Table L: .../resource/d3cda976-bffc-403d-a693-7eb1873e951a/download/tablel.csv
  - Table A data dictionary: .../resource/198bded5-7a17-4e1e-bea5-688dbb439c6d/download/annualprogressreport_tablea_datadictionary-1.docx
  - Table A2 data dictionary: .../resource/354a375a-821d-4d4e-97ab-4d79c2925fce/download/annualprogressreport_tablea2_datadictionary-2.docx
- Licence: the catalog page states no licence, only `accessLevel: public`. — [catalog.data.gov](https://catalog.data.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year)
- HCD's dashboard page says raw data "from 2018 onwards" is downloadable from the California Open Data Portal, that the prior year's data is incomplete until 30 June, and that the dashboard itself is Power BI (not a download). APRs cover development applications, entitlements, building permits and completions. — [HCD APR Dashboard](https://hcd.ca.gov/housing-open-data-tools/apr-dashboard)
- Each APR covers 1 Jan to 31 Dec of the prior calendar year and is due 1 April. — [HCD APR Instructions PDF](https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/housing-element-annual-progress-report-instructions.pdf)
- Table A ("Housing Development Applications Submitted") fields per HCD instructions: Prior APN (optional), Current APN (required), Street Address (required), Project Name (optional), Local Jurisdiction Tracking ID (required); Unit Type (SFA, SFD, 2-4, 5+, ADU, MH); Tenure (R/O); Date Application Submitted (the date deemed complete); Proposed Units by income category split deed-restricted / non-deed-restricted; Total Proposed Units; Total Approved Units; Total Disapproved Units; Streamlining Provision (NONE, SB 9 duplex, SB 9 lot split, AB 2011, SB 6, SMAP, SB 4); Historic Designation; Density Bonus Requested; Density Bonus Approved; Application Status (Approved, Pending, Disapproved, Withdrawn); Project Type (Ministerial or Discretionary); Notes. Only applications deemed complete within the reporting year are included. — [HCD APR Instructions PDF](https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/housing-element-annual-progress-report-instructions.pdf)
- Table A2 ("Annual Building Activity Summary") fields: same project identifiers (Prior APN, Current APN, Street Address, Project Name, Tracking ID); Unit Category; Tenure; Entitlement units by affordability, Entitlement Date Approved, Units Issued Entitlements; Building-permit units by affordability, Building Permit Date Issued, Units Issued Building Permits; Certificate-of-occupancy units by affordability, CO Date Issued, Units Issued Certificates; Streamlining Provision; Historic Designation; Infill (Y/N); Assistance Programs (LIHTC, HOME, CDBG, MHP, etc.); Deed Restriction Type (INC, DB, Other); affordability-without-subsidy justification; Term of Affordability; Demolished/Destroyed Units; Density-bonus detail (total bonus %, number and type of incentives, parking waiver); Notes. — [HCD APR Instructions PDF](https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/housing-element-annual-progress-report-instructions.pdf)
- Dates in A2 are populated only if the event fell within that reporting year; a project appears in multiple years' APRs (one row per year with an entitlement, permit or CO). Group quarters (dorms, student housing) are excluded. — [HCD APR Instructions PDF](https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/housing-element-annual-progress-report-instructions.pdf)
- Income bands used: acutely low (to 15% AMI), extremely low (15-30%), very low (30-50%), low (50-80%), moderate (80-120%), above moderate (>120%). — [HCD APR Instructions PDF](https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/housing-element-annual-progress-report-instructions.pdf)
- A related data.ca.gov dataset "RHNA Progress Report" exists. — [lab.data.ca.gov](https://lab.data.ca.gov/dataset/rhna-progress-report)
- ABAG hosts a technical-assistance page for the same HCD dashboard. — [ABAG](https://abag.ca.gov/technical-assistance/housing-element-implementation-annual-progress-report-apr-data-dashboard)

### Inferences
- Join keys: Table A to Table A2 on (jurisdiction, Local Jurisdiction Tracking ID) or (jurisdiction, Current APN); the tracking ID is normally the city's own planning case number, so it is the bridge to city datasets (e.g. SF "PRJ" record numbers) and to hearing agendas/comment letters that cite case numbers. APN (up to 40 chars, free text) and street address allow geocoding to tract; there is no lat/lon or tract field in the form, so the team must geocode (the Census batch geocoder returns tract GEOIDs).
- An entitlement timeline can be approximated as Table A "date application submitted" to Table A2 "entitlement date approved" for the same tracking ID across report years; A2 to building-permit date gives the post-entitlement lag.
- "Disapproved" in Table A is the nearest statewide machine-readable denial flag, but there is no hearing date, hearing body, appeal, or delay field. "Delayed" must be derived from date gaps or "Pending" status persisting.
- Feasibility for a 2-day event: high. Twelve flat CSVs, no key, no login. Filter by the 9 county names / 101 jurisdictions. Expect messy free-text APNs/addresses and uneven reporting quality since data are self-reported.
- Whether every Bay Area jurisdiction is present for every year depends on whether each filed its APR; non-filers will simply be missing.

### Gaps
- I could not open the CSVs or data dictionaries, so exact CSV column names (e.g. the jurisdiction / county / year column labels), row counts, and the latest reporting year present (expected to be 2025 reports, given the 23 Oct 2026 update) are unconfirmed.
- Completeness by Bay Area jurisdiction and year was not measured.
- What Tables C through L contain was not verified on a source page beyond F2 (moderate-income conversions) and K (tenant preference ordinances); the catalog page describes only those two.
- No explicit licence statement found.

## 2. City open-data portals (San Francisco, Oakland, San Jose, Berkeley, others): dataset names, IDs, endpoints, and whether discretionary review / appeals / hearing outcomes are recorded

### Takeaway
San Francisco is by far the strongest city source: three Socrata datasets cover planning project records (qvu5-m3a2), all non-project and child records from the same Accela system (y673-d69b, the place to look for discretionary review, conditional use, CEQA and appeal case types), and the quarterly development pipeline (6jgi-cpb4). For Oakland and San Jose I found only weekly PDF application lists and web maps, not confirmed bulk project-outcome datasets; Berkeley was not confirmed.

### Cited Findings
San Francisco
- "Planning Department Records - Projects": Socrata ID qvu5-m3a2; landing https://data.sf.gov/d/qvu5-m3a2; development projects drawn from PRJ records in the Planning Department's Accela permitting database; supplemental applications are child records linked through a CHILD_ID column; updated nightly; first published 10 Feb 2026; last updated 11 Nov 2026; formats JSON, XML, CSV; licence listed as US government works. — [catalog.data.gov](https://catalog.data.gov/dataset/planning-department-records-projects)
- "Planning Department Records - Non-Projects": Socrata ID y673-d69b; landing https://data.sf.gov/d/y673-d69b; nightly export from Accela of all Planning records except PRJ, including child records (supplemental applications) linked to parent PRJ records; column metadata at https://data.sf.gov/api/views/y673-d69b/columns.json; CSV at https://data.sf.gov/api/v3/views/y673-d69b/export.csv; first published 10 Feb 2026; last modified 28 Oct 2026. The page does not itemise record types and points to sfplanning.org/resource/project-suffixes-and-descriptions-case-numbers for the list of case-number suffixes. — [catalog.data.gov](https://catalog.data.gov/dataset/planning-department-records-non-projects)
- The older "SF Planning Permitting Data" (ID kncr-c6jw) is marked deprecated, data last modified 6 Jun 2024, and replaced by the two datasets above. Teams should not use it for current data. — [catalog.data.gov](https://catalog.data.gov/dataset/sf-planning-permitting-data)
- "San Francisco Development Pipeline": Socrata ID 6jgi-cpb4; landing https://data.sf.gov/d/6jgi-cpb4; quarterly snapshot combining Planning project data with Department of Building Inspection permit data to show movement from filing to construction; each record is a project or permit with address, block/lot, case number, geometry and scope description; current snapshot is end of 2026 Q2, last modified 28 Aug 2026; formats CSV, JSON, XML, KML, KMZ, GeoJSON (base https://data.sf.gov/api/v3/views/6jgi-cpb4/ plus export.csv or query.geojson); licence CC0 1.0; earlier quarterly snapshots are being retired and must be requested from the owner; data dictionary at https://sfplanninggis.s3.amazonaws.com/SF+Quarterly+Developement+Pipeline+Data+Definition+12212023.xlsx. — [catalog.data.gov](https://catalog.data.gov/dataset/san-francisco-development-pipeline)
- A further dataset "Planning Department Project Application Review metrics" exists in the catalog (not opened). — [catalog.data.gov](https://catalog.data.gov/dataset/planning-department-project-application-review-metrics)
- SF Board of Appeals publishes hearing agendas and periodic "Case Report" PDFs (e.g. 3 Nov 2026 and 13 Oct 2026) and annual reports, i.e. documents rather than an open dataset as far as found. — [Board of Appeals Case Report 11/3/26](https://media.api.sf.gov/documents/Board_of_Appeals_Case_Report_11_3_26.pdf); [BOA annual reports](https://www.sf.gov/resource/2021/board-appeals-annual-reports)

Oakland
- The City publishes weekly "Applications on file" PDF lists (applications requiring public noticing), archived by year for 2022 to 2026, e.g. "Applications-on-file-week-ending-October-30-2026.pdf"; Planning Commission agendas are separate. No bulk open-data link was visible on the fetched portion of the page. — [Oakland Active Planning and Zoning Applications](https://www.oaklandca.gov/Planning-Building/Planning-Zoning/Active-Planning-and-Zoning-Applications)
- Oakland also maintains "Major Development Projects" web pages and an archive of select completed projects (narrative pages, not a dataset). — [Oakland Major Development Projects](https://www.oaklandca.gov/Planning-Building/Major-Development-Projects)

San Jose
- The Planning Division "Development Data" page lists: a weekly "New Planning Applications" listing archived from 2017 to present; a "Planning Permits Map" (open planning permits and those from the last 180 days); a "Building Permits Map" (active permits and last 30 days); annual permit tables since 1980; ADU dashboards since 2015; a Key Economic Development Projects map with housing and affordable-housing categories. — [San Jose Development Data](https://www.sanjoseca.gov/your-government/departments-offices/planning-building-code-enforcement/planning-division/development-data)
- San Jose's CKAN portal data.sanjoseca.gov has a dataset "Building Permits Under Inspection". — [data.sanjoseca.gov](https://data.sanjoseca.gov/dataset/building-permits-under-inspection)
- A San Jose ArcGIS REST planning layer exists at geo.sanjoseca.gov (PLN_Geocortex_Public_PRD MapServer layer 152; contents not verified). — [geo.sanjoseca.gov](https://geo.sanjoseca.gov/server/rest/services/PLN/PLN_Geocortex_Public_PRD/MapServer/152/iteminfo)

### Inferences
- SF Socrata API pattern (standard Socrata SODA, not verified live from this sandbox): `https://data.sfgov.org/resource/qvu5-m3a2.json?$limit=50000&$where=...` and `.csv`; the catalog lists the newer `https://data.sf.gov/api/v3/views/<id>/export.csv` route. No key is required for modest volumes.
- For the "who objects" question in SF: discretionary review requests (case suffix DRP), conditional use authorisations (CUA), CEQA/environmental cases (ENV) and appeals are separate Accela record types, so they should be in the Non-Projects dataset (y673-d69b) as children of a PRJ parent. Counting DR/appeal child records per PRJ gives a ready-made opposition indicator that does not depend on scraping comment letters. This rests on my prior knowledge of SF Planning case suffixes; the suffix list page was not fetched.
- Join keys within SF: PRJ record number to child records via CHILD_ID / parent ID; block/lot (APN) and address link Planning records to the Development Pipeline, to DBI building permits, and to HCD APR rows for San Francisco (APR tracking ID is likely the Planning or DBI permit number).
- Scope recommendation for 2 days: use SF as the deep case study (nightly structured data with case types and dates), and HCD APR Table A/A2 for the cross-city comparison. Oakland and San Jose would require PDF parsing or ArcGIS layer discovery, which is risky in the time available.
- DataSF also has long-standing DBI "Building Permits" and Planning Commission-related fields, but I did not verify IDs this session.

### Gaps
- Column lists for qvu5-m3a2, y673-d69b and 6jgi-cpb4 could not be fetched (data.sf.gov / data.sfgov.org blocked in the research environment). Unverified: whether fields include hearing date, hearing body, decision/outcome, close date, unit counts, affordable units. The team should open `columns.json` for each first.
- Whether any SF dataset records Planning Commission hearing outcomes or public comment counts explicitly is unconfirmed. Board of Appeals data appears to be PDF only.
- Oakland: no confirmed data.oaklandca.gov (Socrata) dataset ID for planning cases or building permits; searches returned only city web pages. Oakland's Accela Citizen Access portal is the likely record-level source but bulk export was not confirmed.
- San Jose: exact URLs/formats of the weekly planning applications and of any planning-permit CKAN or ArcGIS dataset not confirmed.
- Berkeley and other cities (Palo Alto, Mountain View, Fremont, Santa Rosa, etc.): not researched; no dataset confirmed.
- No dataset recording CEQA appeals as such was confirmed for any city.

## 3. Regional and advocacy sources: MTC/ABAG, Terner Center, Urban Displacement Project, Othering & Belonging Institute, YIMBY Law / CalHDF, HCD Housing Accountability Unit

### Takeaway
MTC/ABAG republishes HCD APR permit data on its Socrata portal (data.bayareametro.gov: xegb-bunf for 2014-2022, 47gz-f4yn for 2023), which is a Bay-Area-only, pre-cleaned alternative to the statewide files. HCD's Housing Accountability Unit has a weekly-updated dashboard and a searchable enforcement-letters page (from 1 Jan 2020) that identify contested projects, but no bulk download was found. The O&B Institute zoning shapefiles (March 2020 snapshot, all Bay Area jurisdictions) are on GitHub.

### Cited Findings
- MTC Vital Signs "Housing Permits" indicator (page updated July 2025) uses CIRB Construction Review data for permit counts (1967-2024; county totals from 1967, cities from 1990) and the ABAG-MTC Housing Permits Database for affordability (2014-2023). — [MTC Vital Signs](https://vitalsigns.mtc.ca.gov/indicators/housing-permits)
- MTC Socrata datasets: "HCD Annual Progress Report Permits (2014-2022)" ID xegb-bunf at https://data.bayareametro.gov/Development/HCD-Annual-Progress-Report-Permits-2014-2022-/xegb-bunf/about_data; "HCD Annual Progress Report Permits (2023)" ID 47gz-f4yn at https://data.bayareametro.gov/Development/HCD-Annual-Progress-Report-Permits-2023-/47gz-f4yn/about_data. — [MTC Vital Signs](https://vitalsigns.mtc.ca.gov/indicators/housing-permits)
- ABAG's Housing Policy & Data Explorer offers housing policies by jurisdiction, residential building permits issued by Bay Area jurisdictions, county permit reports, and downloads for housing units permitted, housing element sites and housing policies; explorer at http://housing.abag.ca.gov/ and the policy viewer (Bay Area Housing and Land Use Viewer) at http://housing.abag.ca.gov/#policy. — [ABAG](https://abag.ca.gov/tools-resources/data-tools/housing-policy-data-explorer)
- ABAG published a "2015-2019 Bay Area Permit Activity Report". — [ABAG](https://abag.ca.gov/technical-assistance/2015-2019-bay-area-permit-activity-report)
- HCD "Housing Accountability Dashboard": tracks Housing Accountability Unit actions with a headline metric of housing units "unlocked" after HCD intervention; coverage starts 1 Jan 2020; updated weekly; links to a searchable Technical Assistance and Enforcement Letters dashboard at https://www.hcd.ca.gov/hau/enforcement-letters; no data download mentioned. — [HCD Housing Accountability Dashboard](https://hcd.ca.gov/housing-open-data-tools/housing-accountability-dashboard)
- Othering & Belonging Institute "San Francisco Bay Area Residential Zoning Dataset": shapefiles classifying land as single-family residential, multi-family residential or non-residential for all 100 municipalities plus unincorporated areas of the nine counties; snapshot of zoning as of March 2020; released 2020; data and methodology at https://github.com/OtheringBelonging/BayAreaZoning; no licence stated on the page. — [O&B Institute](https://belonging.berkeley.edu/about-our-bay-area-land-use-data-sources)
- YIMBY Law launched a "Housing Element Dashboard" tracking housing-element compliance and production (press coverage dated Aug 2024). — [YIMBY Law press release](https://www.yimbylaw.org/press/housing-element-dashboard)
- Urban Displacement Project publishes SF Bay Area gentrification and displacement maps/typologies. — [Urban Displacement Project](https://www.urbandisplacement.org/?p=601)

### Inferences
- The MTC datasets should be queryable with the usual Socrata pattern (`https://data.bayareametro.gov/resource/xegb-bunf.csv?$limit=...`); the 2014-2022 file extends back before HCD's own 2018 start, so it is useful for longer timelines. Whether it has address/APN and lat/lon per permit was not confirmed, though MTC's permit database has historically been geocoded.
- HAU enforcement letters name the jurisdiction and usually the project address, so a small hand-coded list of Bay Area letters (2020 to 2026) could serve as a "state intervened" outcome label; this is manual work, feasible only for a few dozen records in 2 days.
- O&B single-family zoning share by tract (spatial overlay) is a ready covariate for "exclusionary" neighbourhoods but is 6+ years stale; post-2020 upzonings (SB 9, housing element rezonings) are not reflected.

### Gaps
- Terner Center: no downloadable dataset confirmed (not searched in depth; the Terner California Residential Land Use Survey exists per my background knowledge but access terms were not verified).
- Urban Displacement Project: download location, vintage and format of Bay Area typology data not confirmed (I believe tract-level typology files are on the UDP GitHub, unverified).
- YIMBY Law / CalHDF: no public machine-readable tracker of denied projects or HAA lawsuits was confirmed; only the Housing Element Dashboard announcement was found.
- MTC datasets: fields, record level (permit vs jurisdiction aggregate) and licence not verified; no 2024 or 2025 MTC permit file was identified.
- MTC/ABAG regional zoning dataset and opendata.mtc.ca.gov items not verified.
- HAU letters: no CSV/API; structure of the letters dashboard not inspected.

## 4. Demographics: ACS 5-year via Census API, ZIP/ZCTA-to-tract crosswalks, CalEnviroScreen, TCAC/HCD Opportunity Maps; latest ACS 5-year release in November 2026

### Takeaway
The latest ACS 5-year in the Census API as of Nov 2026 is the 2024 vintage (2020-2024 estimates) at api.census.gov/data/2024/acs/acs5, with detailed tables to block group and subject/profile tables to tract. CalEnviroScreen 5.0 (published 30 Jun 2026) and the adopted 2026 CTCAC/HCD Opportunity Map (plus a 2027 draft) are both bulk-downloadable tract-level indices. HUD's USPS ZIP crosswalk needs a free account login.

### Cited Findings
- Census lists 2024 (2020-2024) as the latest ACS 5-year dataset; endpoints: Detailed Tables `api.census.gov/data/2024/acs/acs5`, Subject Tables `.../acs5/subject`, Data Profiles `.../acs5/profile`, Comparison Profiles `.../acs5/cprofile`; example `api.census.gov/data/2024/acs/acs5?get=NAME,group(B01001)&for=us:1&key=YOUR_KEY`. Detailed tables go down to block group; subject tables and data profiles to tract; comparison profiles do not support tracts. ZCTAs are among ACS 5-year geographies. The Census page headers describe coverage as "American Community Survey 5-Year Data (2009-2024)". — [Census ACS 5-year API page](https://www.census.gov/data/developers/data-sets/acs-5year.html)
- HUD-USPS ZIP Code Crosswalk: twelve file types, six ZIP-to-geography (tract, county, county subdivision, CBSA, CBSA division, congressional district) and six geography-to-ZIP; the two directions are not inverses, so moving tract data to ZIPs requires the TRACT-ZIP file, and moving ZIP data to tracts requires ZIP-TRACT; the download app shows a login form with registration. — [HUD USPS crosswalk](https://huduser.gov/apps/public/uspscrosswalk/home)
- CalEnviroScreen 5.0: catalog entry first published 30 Jun 2026, updated 30 Jul 2026; ArcGIS Hub at https://gis.data.ca.gov/datasets/OEHHA::calenviroscreen-5-0; ArcGIS REST FeatureServer at https://services1.arcgis.com/PCHfdHz4GlDNAhBb/arcgis/rest/services/calenviroscreen50results_F_070126_gdb/FeatureServer/2; other formats via https://data.ca.gov/dataset/calenviroscreen-5-0; new indicators in 5.0 are Small Air Toxic Sites and Diabetes Prevalence. — [catalog.data.gov](https://catalog.data.gov/dataset/calenviroscreen-5-0-8e575)
- OEHHA has a CalEnviroScreen 5.0 report page and a report PDF dated June 2026. — [OEHHA](https://oehha.ca.gov/calenviroscreen/report/calenviroscreen-50)
- CTCAC/HCD Opportunity Maps: the 2026 map was adopted December 2025; downloads are a statewide summary table https://www.treasurer.ca.gov/sites/default/files/2025-11/summary_file.zip and shapefile https://www.treasurer.ca.gov/sites/default/files/2025-11/shapefile.zip, plus Neighborhood Change Map table https://www.treasurer.ca.gov/sites/default/files/2025-11/final-neighborhood-change-map-statewide-summary-table.xlsx and shapefile https://www.treasurer.ca.gov/sites/default/files/2025-11/neighborhood-change-map-shapefile.zip. A 2027 draft (not yet adopted) is also posted: https://treasurer.ca.gov/sites/default/files/ctcac/final_opp_2027_public.xlsx and https://treasurer.ca.gov/sites/default/files/ctcac/om-shapefile.zip. Mapping tools are hosted at belonging.berkeley.edu. — [CTCAC Opportunity Maps](https://www.treasurer.ca.gov/CTCAC/opportunity.asp)
- A 2026 Opportunity Map methodology PDF is published. — [CTCAC 2026 methodology](https://www.treasurer.ca.gov/ctcac/opportunity/2026/2026-OM-Methodology.pdf)

### Inferences
- The 2021-2025 ACS 5-year is normally released in December, so it is probably not yet out on 14 Nov 2026; the team should use the 2024 vintage. (Release timing is my expectation from past practice, not confirmed for 2026.)
- Suggested ACS detailed tables (standard table IDs from background knowledge, not checked against the 2024 variable list): B19013 median household income; B25003 tenure (owner/renter); B03002 race by Hispanic origin; B01001 sex by age and B01002 median age; B25077 median home value; B25064 median gross rent; B15003 educational attainment; B25070 rent burden; B25034 year structure built; B07003/B25038 residential mobility/tenure length. Tract call pattern for the 9 counties: `...acs5?get=NAME,B19013_001E&for=tract:*&in=state:06&in=county:001,013,041,055,075,081,085,095,097&key=...` (FIPS: Alameda 001, Contra Costa 013, Marin 041, Napa 055, San Francisco 075, San Mateo 081, Santa Clara 085, Solano 095, Sonoma 097).
- Join strategy: because the team's Zillow data and (after geocoding) project addresses have lat/lon, a spatial join of points to 2020 tract polygons (TIGER/Line) is cleaner than any ZIP crosswalk; tract GEOID (11 digits) then joins ACS, CalEnviroScreen and Opportunity Map directly. For ZIP-only joins, pull ACS at ZCTA level directly (`for=zip code tabulation area:*`) and avoid the HUD login step; ZCTA is not identical to USPS ZIP but is adequate for a datathon.
- Opportunity Map categories (Highest/High/Moderate/Low Resource) give a one-column "neighbourhood advantage" label well suited to the wealth-versus-opposition question; CalEnviroScreen is more pollution-oriented and less directly relevant.
- Zillow price/rent data can be aggregated to tract or ZIP as an additional wealth measure and cross-checked against B25077/B25064.

### Gaps
- Exact release date of 2020-2024 ACS 5-year and the scheduled date for 2021-2025 not confirmed from a Census schedule page.
- Whether ZCTA is supported in each ACS table type for 2024 not confirmed on the fetched page.
- HUD crosswalk: latest quarter available, field names (I recall RES_RATIO, BUS_RATIO, OTH_RATIO, TOT_RATIO), tract vintage and API token procedure not confirmed. An account is needed, which is quick but is a login step.
- CalEnviroScreen 5.0 tract vintage (2020 tracts expected), socioeconomic indicator list and licence not confirmed.
- Opportunity Map geographic unit (tract, with block groups in rural areas per my recollection) and field names not confirmed.

## 5. Academic datasets on California entitlement timelines (CALES and similar) and public availability

### Takeaway
CALES (O'Neill, Biber, Gualco-Nelson, Marantz) is the key academic project-level entitlement dataset, but I found only the reports, not a public data download; treat it as a literature and methods reference rather than a data source for the datathon.

### Cited Findings
- "Examining Entitlement in California to Inform Policy and Process: Advancing Social Equity in Housing Development Patterns" by Moira O'Neill, Eric Biber, Giulia Gualco-Nelson and Nicholas Marantz is the final report for the California Air Resources Board's Comprehensive Assessment of Land Use Entitlements Study (CALES); written Sept 2021, posted Nov 2021, revised Apr 2022. — [SSRN](https://papers.ssrn.com/abstract=3956250)
- Key findings: local land-use authority and regulation are identified as the largest barriers to infill and affordable housing; fewer than 3% of approvals in their data faced litigation, with no notable infill/exurban difference. — [SSRN](https://papers.ssrn.com/abstract=3956250)
- The SSRN page carries no data availability statement or download link. — [SSRN](https://papers.ssrn.com/abstract=3956250)
- CARB hosts a project page for the same study. — [CARB](https://ww2.arb.ca.gov/node/41351)

### Inferences
- CALES findings (low litigation rates; local discretionary process as the main source of delay) supply a baseline hypothesis and a variable template (application date, approval date, approval pathway, CEQA pathway, appeals, litigation) the team can mirror using SF Accela records and HCD APR dates.
- HCD APR Table A's Ministerial/Discretionary flag and streamlining field are a rough public substitute for CALES's approval-pathway coding.

### Gaps
- Whether CALES project-level data can be downloaded (I recall a CALES website with a data portal run by the authors, but did not find or verify it this session) and under what terms.
- Other academic hearing-comment datasets (e.g. Einstein, Glick and Palmer's work on meeting participants, which is Massachusetts; any California equivalent) were not searched.
- Terner Center entitlement or land-use survey data availability not verified.
