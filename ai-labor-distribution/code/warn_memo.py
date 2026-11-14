import pandas as pd
S='/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad'
q=pd.read_csv(S+'/out/warn_quarterly_bay_vs_rest.csv')
qt=q[['quarter','notices_bay','employees_bay','notices_rest','employees_rest','bay_share_emp','bay_per10k','rest_per10k','bay_to_rest_intensity_ratio']].copy()
qt.columns=['Quarter (by received date)','Bay notices','Bay employees','Rest-CA notices','Rest-CA employees','Bay share of CA employees','Bay per 10k workers','Rest per 10k workers','Bay/Rest ratio']
qt['Bay share of CA employees']=(qt['Bay share of CA employees']*100).round(1).astype(str)+'%'
qt=qt.round(2); qt.loc[qt.index[-1],'Quarter (by received date)']='2026Q4 (partial: Oct 1-Nov 9)'
lfl=pd.read_csv(S+'/out/warn_like_for_like_jul1_nov9.csv')[['fiscal_year','notices_bay','employees_bay','employees_rest','bay_per10k','rest_per10k','bay_share']]
lfl['bay_share']=(lfl.bay_share*100).round(1).astype(str)+'%'
fy=pd.read_csv(S+'/out/warn_fy_bay_vs_rest.csv')[['fiscal_year','notices_bay','employees_bay','employees_rest','bay_per10k','rest_per10k','bay_share']]
fy['bay_share']=(fy.bay_share*100).round(1).astype(str)+'%'
cf=pd.read_csv(S+'/out/warn_bay_county_fy.csv')
cf=cf[['county','FY2023-24','FY2024-25','FY2025-26','FY26-27 Jul1-Nov9','FY2023-24_per10k','FY2024-25_per10k','FY2025-26_per10k']].round(1)
cl=pd.read_csv(S+'/out/warn_bay_county_lfl.csv')
t30=pd.read_csv(S+'/out/warn_bay_top30_employers.csv')
t30['flag']=t30.apply(lambda r:'TECH' if r.tech_core else ('tech-adjacent (EV/AV/hardware/solar mfg)' if r.tech_adjacent else ''),axis=1)
t30=t30[['employer','employees','notices','counties','flag','first','last']]
tm=pd.read_csv(S+'/out/warn_type_mix_fy.csv'); tm['perm_share']=(tm.perm_share*100).round(1)
tk=pd.read_csv(S+'/out/warn_kind_mix_fy.csv'); tk['closure_share']=(tk.closure_share*100).round(1)
ind=pd.read_csv(S+'/out/warn_bay_industry_fy2627.csv'); ind['share']=(ind.share*100).round(1)
ts=pd.read_csv(S+'/out/warn_bay_tech_share_fy.csv')
M=lambda d: d.to_markdown(index=False)
doc=f"""# EXPERIMENT W: California WARN notices and Bay Area labor-market exposure

Source: EDD WARN reports (3 PDFs FY2023-24 to FY2025-26 + current xlsx, received dates 2023-07-03 to 2026-11-09). 5,392 notice rows parsed, 5,390 in CA (2 out-of-state rows, Clark NV and Dallas TX, retained in warn_ca.* but dropped from analysis). 297,696 affected employees. All figures below are computed from the parse (scripts in code/warn_*.py). Time axis = EDD received/processed date (the field the reports are filtered on), not the employer notice date.

## Three most surprising results

1. **No rising Bay Area trend over the window.** Across the 13 full quarters 2023Q3-2026Q3, Bay Area affected employees per 10,000 resident workers have a slope of -0.17 per quarter (HAC se 0.39, p=0.66; Spearman rho -0.04). Bay Area notice COUNT is drifting down (-2.8 notices/qtr, p=0.08). The Bay Area share of California WARN employees has no trend (+0.2 pp/qtr, p=0.78). The Bay Area peak was 2024Q1 (28.4 per 10k), not recent.
2. **The "recent surge" is lumpy and is a few firms, not a broad trend.** 2026Q2 (Bay 9,889 employees, 24.6 per 10k, 3.6x the rest of CA's intensity) is 66% flagged core-tech (Meta alone 2,212 + 338 + 313 + 252 in late May 2026, plus Intuit 493, LinkedIn 352, Oracle 310). The next quarter fell back to 18.9 per 10k. Meta Platforms is the largest Bay employer in the window (4,023 employees across 19 notices). Tech share of Bay WARN employees: 23.1% FY23-24, 21.6% FY24-25, 47.0% FY25-26, 26.6% FY26-27 so far.
3. **The cleanest direct customer-support read is essentially empty.** The xlsx Call Center Relocations sheet holds exactly ONE record in 2023-2026 (American General Life, Woodland Hills, Los Angeles Co., 163 employees, received 2023-03-02, i.e. before our window, not Bay Area, no destination stated). The PDFs contain no call-center section. Name-matching finds only Charter Communications Customer Contact Center (San Bernardino, 430, closure, 2024-06), Sky Chefs Customer Service Center (14), and two Conduent (BPO) layoffs (Orange 51; San Francisco 64, Oct 2026). WARN therefore gives no evidence of a customer-support offshoring wave in the Bay Area.

## Headline numbers

Bay Area (9 counties) vs rest of CA, whole window: {97753:,} Bay employees vs {199943:,} rest. Bay = 32.8% of CA WARN employees vs 20.7% of CA workers (ACS 2024 employed residents), so Bay intensity is 243.5 vs 130.0 per 10,000 workers, ratio 1.87x. This level gap is persistent (ratio ranged 0.76-3.58 by quarter; see table) and driven by large tech/biotech/hardware single-site notices.

### Quarterly series (a)
Denominator: employed residents by county from ACS 2024 1-year PUMS (Bay 4,014,351; rest 15,382,398; CA 19,396,749). 2026Q4 is partial (40 of 92 days) so its raw numbers are not comparable; the per-92-day-equivalent is in out/warn_quarterly_bay_vs_rest.csv.

{M(qt)}

### Fiscal-year and like-for-like comparison
Full fiscal years (FY26-27 is only 4.3 months old):

{M(fy.round(2))}

Like-for-like window July 1 - Nov 9 each year (the only fair comparison with FY26-27 to date):

{M(lfl.round(2))}

Reading: Bay per-10k intensity in the like-for-like window rises 20.6 -> 24.5 -> 26.3 -> 27.5 (+33% FY23-24 to FY26-27) and the Bay share is 38.7% in FY26-27, the highest of four years. That is the one place the data lean toward "elevated." It is fragile: FY26-27's Bay total includes two notices of 1,605 (AEG Management Oakland, Oct 30, a venue operator) and 1,279 (Covenant Aviation Security, SF Sep 28), neither tech. Excluding all notices of 1,000+ employees, the FY26-27 Bay share falls to 31.8% (FY23-24 36.4%, FY24-25 35.4%, FY25-26 30.2%), i.e. NOT elevated. The top 10 rows make up 45.7% of FY26-27 Bay employees vs 17-21% in earlier years. Bay notice counts in the same window are 176, 145, 229, 151 (FY26-27 is lowest except FY24-25). Conclusion: Bay Area layoff intensity is NOT clearly elevated relative to FY23-24; the quarterly trend is flat; the FY26-27 like-for-like uptick is within single-notice noise.

Median Bay notice size is 18-33 employees; 62-67% of Bay rows are under 50 employees (CA overall 66%, and rows <50 account for only 14.9% of affected employees). So volume is dominated by a few large rows while the count is dominated by small sites.

### By county (b)
Employees by received-date fiscal year, and per 10,000 resident workers (full file: base/warn_bay_county_quarter.csv has county x quarter notices, employees, per-10k):

{M(cf)}

Like-for-like Jul 1 - Nov 9 employees by county:

{cl.to_markdown()}

Santa Clara and San Mateo carry the large, lumpy tech/biotech notices (Santa Clara 13,031 in FY23-24, 8,183, 10,672; San Mateo 4,867, 2,598, 5,737). San Francisco is falling per worker (118.7 -> 114.1 -> 76.5) with a jump in FY26-27 to date driven by Covenant (1,279). Contra Costa fell sharply (44.1 -> 11.3 per 10k). Small counties (Marin, Napa, Solano, Sonoma) are noise-dominated and should not be read for trend.

### Top 30 Bay Area employers by affected employees, whole window (c)
Employer = company name with parentheticals / "- site" / "dba" suffix stripped, so site-level notices roll up (company_norm in warn_ca is the strict name; this roll-up is a separate analysis key). TECH = software/internet/semiconductor/IT firms per a hand-curated list (not NAICS; NAICS exists only for FY26-27). Amazon is flagged tech but includes fulfillment/retail sites. Top 30 = 40.4% of 97,753 Bay employees across 647 employer groups.

{M(t30)}

Tech-flagged employers in the top 30: Meta, Cisco, Intel, Amazon, Oracle, Broadcom, LinkedIn, eBay, Intuit, Workday, Apple, BILL, Salesforce, PayPal (14), plus tech-adjacent Tesla, Jabil, Cruise. Biotech/healthcare (Genentech, Cepheid, Kaiser, Gilead), retail/food (Walmart, Safeway, Amy's) and venue/security (AEG, Covenant, Gate Gourmet) make up most of the rest.

Bay Area tech share of affected employees:

{M(ts.round(3))}

### Layoff type mix (d)
Permanent share of affected employees, by fiscal year (False = rest of CA, True = Bay):

{M(tm)}

Closure share of affected employees:

{M(tk)}

The Bay mix is NOT shifting toward permanent: permanent share is 96.5%, 95.1%, 97.0%, 93.7% (essentially saturated from the start; quarterly Bay permanent share ranges 86%-100% with no trend). The mix is NOT shifting toward layoffs-vs-closures either: Bay closure share is a stable 22-26% of employees (rest of CA 41-60%), so Bay notices are overwhelmingly permanent partial layoffs (consistent with white-collar restructuring), not site closures. Temporary layoffs are minor (2.5-6.3% of Bay employees by fiscal year). Rest-of-CA permanent share drops to 70.6% in FY26-27 to date (a 5,042 temporary-layoff block).

### Call-center relocations (e)
Full list of Call Center Relocations Report rows (xlsx, covers 2023-01-01 to 2026-11-09): 1 record. American General Life Insurance Company, Los Angeles County (Woodland Hills), 163 employees, Layoff Permanent, notice 2023-02-27, received 2023-03-02, effective 2023-05-01. FY2022-23: 1 notice, 163 employees; FY2023-24 through FY2026-27: 0. Destination not given (the report has no destination column). Saved to base/warn_call_centers.csv. Bay Area call-center relocation notices: 0. Name-matched customer-contact sites (not official relocations): Charter Communications Customer Contact Center (San Bernardino, 430, closure, rec'd 2024-06-13), Sky Chefs' Customer Service Center (San Bernardino, 14, 2026-03-10), Conduent (Orange, 51, 2026-07-14), Conduent State & Local Solutions (San Francisco, 64, 2026-10-23). Haas Automation (Ventura, 73+74) appears as a "Relocation Permanent" type in the main report but is machine-tool manufacturing, not a call center. Caveat: one record cannot support any inference about trend; it is a null result for this mechanism, not proof of no offshoring (notices are only required for 50+ job losses at one site).

### Industry (f)
NAICS "Related Industry" exists ONLY in the current xlsx (FY26-27, Jul 1 - Nov 9 2026, 479 notices, 100% populated); the PDFs have no industry field, so no multi-year industry trend is possible. Bay Area FY26-27-to-date, employees by sector:

{M(ind)}

Within these 4.3 months Bay monthly totals are 2,042 / 1,962 / 3,581 / 3,028 / 415 (Jul..Nov 1-9, noisy). Information (NAICS 51) is 8.7% (963 employees, 9 notices: Netflix 227, Airtable 190, Workday 142, Synopsys 128...). Note NAICS labels are the filer/EDD assignment and look noisy (e.g., Oracle America tagged 31-33 Manufacturing; eBay tagged Retail Trade; PayPal/Visa Finance), so sector shares understate tech. Professional/Scientific/Technical is 9.5%. Manufacturing 20.3% and Administrative & Support (largely the Covenant security notice) 18.9% lead.

## What WARN can and cannot support (Task 3, honest limits)

- **No occupations, no job titles.** WARN carries company, site address, county, headcount, layoff/closure type, dates, and (FY26-27 xlsx only) a coarse NAICS sector. Nothing in this analysis identifies support, clerical, engineering or any other occupation. Do not read these results as "support/clerical exposure." Any occupation split would have to come from elsewhere (e.g., postings, OEWS, firm announcements).
- **Coverage.** Cal-WARN applies to employers with 75+ employees and mass layoffs/closures/relocations (50+ at a covered establishment in 30 days). It misses contractor/vendor non-renewals (the likeliest channel for outsourced support work), attrition and hiring freezes, rolling cuts below the thresholds, and small employers. Despite the threshold, 66% of parsed rows are under 50 employees (these are typically sites of a multi-site notice or partial counts), so the data are site-fragmented and "notices" are not a count of firm events.
- **Eligible employment share.** I could not derive this from the data here (no establishment-size data was fetched). Stated ASSUMPTION, not a result: roughly 40-60% of Bay Area private employment sits at establishments/employers over the 75-employee line (to be replaced with Census CBP/SUSB size-class tables for the nine counties). On that assumption WARN could only ever see layoffs concentrated in half the employment base, and only the portion that is a mass event. Observed scale: Bay WARN employees per year are 0.86% (FY23-24, 34,464/4.01M), 0.62% (FY24-25) and 0.68% (FY25-26) of resident workers; actual job loss from all causes is far larger.
- **Timing/geography.** WARN notices are 60 days ahead of effective dates and the quarter is assigned by received date; they are worksite-based while the denominator is residence-based (commuting mismatch across Bay counties and into the Bay from the Central Valley). Remote employees are attributed to an assigned site, so SF/Santa Clara counts may be inflated or misplaced.
- **Notice type.** Rescinded or revised notices and duplicate/updated filings are not netted out. 8 rows (1,044 employees) are exact duplicates of other rows (kept, <0.4% of employees).

## What would change AI-exposure interpretation
WARN shows large-firm tech white-collar restructuring is real and lumpy (Meta, Cisco, Intel, Oracle, LinkedIn, Intuit), concentrated in a few firms and weeks, with no sustained upward trend in Bay intensity. It cannot attribute any of that to AI, cannot see support/clerical roles, and structurally misses contractor/BPO channels. The absence of a call-center-relocation signal and a flat Bay trend is a null result for "AI is visibly driving mass layoffs in covered Bay establishments," not evidence about AI exposure of occupations.

## Parse quality
- PDFs parsed with pdfplumber table extraction (pypdf text wrapped long company names across lines and mangled columns). Every PDF's own "Summary by Month" page was used as an independent check: all 39 month and total lines (12 months x 3 PDFs + 3 totals) match exactly on notice count and employee count. Totals: FY2023-24 1,814 notices / 94,189 employees; FY2024-25 1,506 / 93,273; FY2025-26 1,593 / 81,748; FY2026-27 (to 11/9/2026, xlsx) 479 / 28,489. No fiscal year failed.
- 10 random rows hand-checked against raw pypdf text: 10/10 field matches (dates, company, county, headcount, type, address).
- 100% of rows have a county (56 CA counties in the data, plus 2 out-of-state rows flagged) and a positive integer employee count; city is derived from a zip->city map learned from double-space-delimited addresses (99.5% populated; PDFs collapse the street/city double space, so city is a derived field, less reliable than county). 
- The PDFs begin with notices dated Apr-Jun 2023 received July 2023 onward; FY assignments use the received date.
- Not available: pre-July-2023 history (only the single 2023-03 call-center record), industry for PDF years, call-center section in the PDFs.
- Denominators: BLS LAUS (laucnty23/24/25.txt) returned HTTP 403 Access Denied even with a browser user agent. Census county population (co-est2024-alldata.csv) downloaded fine and is saved (POPESTIMATE2023/2024 in base/warn_county_denominators.csv), but the memo uses employed residents (ACS 2024 1-year PUMS, ESR in 1,2,4,5, summed over PUMAs allocated to counties by 2020 tract share) because "per 10,000 workers" was requested. Multi-county PUMAs split by tract count; single-year denominator applied to all years.
"""
open(S+'/out/warn_findings.md','w').write(doc)
print(len(doc))
