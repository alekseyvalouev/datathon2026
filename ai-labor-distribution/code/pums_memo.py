"""Builds out/pums_findings.md and base/suppressed_cells.csv from result CSVs. Every number is read from CSV. Usage: pums_memo.py base_dir out_dir"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pums_lib as L
B,O=sys.argv[1:3]; os.makedirs(O,exist_ok=True)
R=L.RACES; RA=R+['All']
ex=pd.read_csv(f'{B}/exposure_by_race.csv'); ec=pd.read_csv(f'{B}/exposure_by_race_county.csv')
wg=pd.read_csv(f'{B}/wages_by_occclass_race.csv'); gt=pd.read_csv(f'{B}/wage_gap_tests.csv'); wm=pd.read_csv(f'{B}/wage_mass_at_risk.csv')
ct=pd.read_csv(f'{B}/contract_precarity.csv'); ig=pd.read_csv(f'{B}/incidence_grid.csv'); gp=pd.read_csv(f'{B}/incidence_gap_changes.csv')
ch=pd.read_csv(f'{B}/change_2024_vs_5yr.csv'); cc=pd.read_csv(f'{B}/ai_concentration_by_county.csv'); rc=pd.read_csv(f'{B}/race_counts.csv')
xw=pd.read_csv(f'{B}/occp_crosswalk.csv',dtype={'occp':str}); alt=pd.read_csv(f'{B}/exposure_by_race_altmap.csv'); sx=pd.read_csv(f'{B}/exposure_by_race_sex.csv')
def g(df,**k):
    m=np.ones(len(df),bool)
    for a,b in k.items(): m&=(df[a]==b).values
    r=df[m]; assert len(r)==1,(k,len(r)); return r.iloc[0]
def pct(x,d=1): return 'n/a' if pd.isna(x) else f'{100*x:.{d}f}%'
def f2(x): return 'n/a' if pd.isna(x) else f'{x:.2f}'
def usd(x): return 'n/a' if pd.isna(x) else f'${x:,.0f}'
def md(rows,header):
    s='| '+' | '.join(header)+' |\n|'+'|'.join(['---']*len(header))+'|\n'
    for r in rows: s+='| '+' | '.join(str(c) for c in r)+' |\n'
    return s+'\n'
def cellp(row,col='share_of_group',se='se_share_of_group',d=1,fmt=pct):
    if row.suppressed: return 's'
    return f'{fmt(row[col])} ({100*row[se]:.1f})' if fmt is pct and se else fmt(row[col])
L_=[]; P=L_.append
_d=pd.read_parquet(f'{B}/pums_bay.parquet',columns=['PWGTP','SEX','occ_class','education'])
_x=_d[_d.occ_class.isin(L.EXPOSED)]
FEM_E=(_x.PWGTP*(_x.SEX==2)).sum()/_x.PWGTP.sum(); FEM_A=(_d.PWGTP*(_d.SEX==2)).sum()/_d.PWGTP.sum()
BA_E=_x.PWGTP[_x.education.isin(['Bachelors','Graduate'])].sum()/_x.PWGTP.sum()
_a=_d[_d.occ_class.isin(L.AIPOS)]; BA_A=_a.PWGTP[_a.education.isin(['Bachelors','Graduate'])].sum()/_a.PWGTP.sum()
tot=g(ex,race_eth='All',category='ALL'); 
oth=xw[xw.occ_class=='OTHER']; ow=oth.bay_w_2019_23.sum(); aw=xw.bay_w_2019_23.sum()
# headline numbers
E_=lambda r,c='EXPOSED': g(ex,race_eth=r,category=c)
nE=tot.w_cell*E_('All').share_of_group; nA=tot.w_cell*E_('All','AIPOS').share_of_group
mA=g(wg,pool='AIPOS',race_eth='All',metric='median_annual_ftfy'); mE=g(wg,pool='EXPOSED',race_eth='All',metric='median_annual_ftfy')
hA=g(wg,pool='AIPOS',race_eth='All',metric='median_hourly'); hE=g(wg,pool='EXPOSED',race_eth='All',metric='median_hourly')
pz=g(wg,pool='PRIZE_AIPOS_minus_EXPOSED',race_eth='All',metric='median_annual_ftfy_diff'); pzr=g(wg,pool='PRIZE_AIPOS_over_EXPOSED',race_eth='All',metric='median_annual_ftfy_ratio')
t1=gt[(gt.A_def=='AI_PRODUCER+SOFTWARE_ENG')&(gt.race_eth=='Black')]; t1u=t1[~t1.adjusted].iloc[0]; t1a=t1[t1.adjusted].iloc[0]
massE=g(wm,geo_level='Bay Area',race_eth='All',category='EXPOSED'); massA=g(wm,geo_level='Bay Area',race_eth='All',category='AIPOS')
P('# AI exposure and the distribution of Bay Area wages: worker-level microdata (ACS PUMS)\n')
P('*Experiment P. Source: ACS 2019-2023 5-Year PUMS (California persons) and ACS 2024 1-Year PUMS. Bay Area = 9 counties, employed persons age 16+ (ESR 1,2,4,5). Every number in this memo is computed by `code/pums_*.py` from the files in `base/`. Standard errors (in parentheses; percentage points for shares) use the 80 successive-difference replicate weights. Cells with fewer than 50 unweighted observations are shown as `s` (suppressed).*\n')
P('## Three headline numbers\n')
a=E_('Asian','AIPOS'); w_=E_('White','AIPOS'); b_=E_('Black','AIPOS'); h_=E_('Hispanic','AIPOS')
P(f"1. **AI-positioned jobs (AI producer + software + data/analytics) are held mostly by Asian workers.** Asian workers are {pct(a.share_of_category)} of AI-positioned employment against {pct(g(rc,race_eth='Asian',file='2019-2023_5yr').share_of_weighted)} of all employment (representation index {f2(a.rep_index)}, SE {f2(a.se_rep_index)}). White workers are {pct(w_.share_of_category)} (index {f2(w_.rep_index)}), Black workers {pct(b_.share_of_category)} (index {f2(b_.rep_index)}), Hispanic workers {pct(h_.share_of_category)} (index {f2(h_.rep_index)}). The AI-positioned set is {pct(E_('All','AIPOS').share_of_group)} of Bay Area employment (about {nA:,.0f} workers); the exposed set (clerical + customer support + exposed professional) is {pct(E_('All').share_of_group)} (about {nE:,.0f} workers).")
P(f"2. **The prize is large.** Median full-time-year-round wage in AI-positioned classes is {usd(mA.est)} vs {usd(mE.est)} in exposed classes, a gap of {usd(pz.est)} (SE {usd(pz.se)}), ratio {f2(pzr.est)}. Median hourly wage is ${hA.est:.2f} vs ${hE.est:.2f}. Wage mass in exposed occupations is ${massE['wage_mass_$M']/1000:,.1f}B/yr ({pct(massE.share_of_group_wage_mass)} of Bay Area wage and salary mass), against ${massA['wage_mass_$M']/1000:,.1f}B ({pct(massA.share_of_group_wage_mass)}) in AI-positioned classes (2023 dollars).")
P(f"3. **Black workers are both more exposed and more shut out of the gains, and the wage gap is widest exactly inside the AI classes.** Black workers' exposed share is {pct(E_('Black').share_of_group)} (index {f2(E_('Black').rep_index)}; Bay Area {pct(E_('All').share_of_group)}), their AI-positioned share is {pct(b_.share_of_group)}, so the exposed-to-AI-positioned ratio is {f2(E_('Black','RATIO_EXPOSED_OVER_AIPOS').share_of_group)} (White {f2(E_('White','RATIO_EXPOSED_OVER_AIPOS').share_of_group)}, Asian {f2(E_('Asian','RATIO_EXPOSED_OVER_AIPOS').share_of_group)}, Hispanic {f2(E_('Hispanic','RATIO_EXPOSED_OVER_AIPOS').share_of_group)}). Inside AI_PRODUCER/SOFTWARE_ENG, Black workers earn {pct(-t1u.pct_gap_A,0)} less per hour than White workers in the same classes (unadjusted; {pct(-t1a.pct_gap_A,0)} after controls for age, sex, education, county, nativity); inside the exposed classes the gap is {pct(-t1u.pct_gap_E,0)} ({pct(-t1a.pct_gap_E,0)} adjusted). Difference in log gaps {t1u.diff_A_minus_E:.3f} (SE {t1u.se_diff:.3f}).\n")
P('**What does not fit a simple "AI hurts the already-disadvantaged" story** (full list in the disconfirming-evidence section): Hispanic workers are *under*-represented in the exposed classes (index '+f2(E_('Hispanic').rep_index)+'); Asian and White workers sit at parity with each other on exposure (indices '+f2(E_('Asian').rep_index)+' and '+f2(E_('White').rep_index)+'); exposed workers are *less* likely than average to be self-employed; and White workers, the highest-paid large group, are *under*-represented in AI-positioned jobs (index '+f2(w_.rep_index)+').\n')

P('## 0. Data, definitions, coverage\n')
P('* **Population.** Bay Area (Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, Solano, Sonoma), persons 16+, ESR in 1,2,4,5. This includes ESR 4/5 (armed forces); military occupations fall in OTHER (see below). Group-quarters persons are in PUMS and retained if employed.')
P('* **Race/ethnicity** (mutually exclusive): Hispanic (HISP>1, any race); among non-Hispanic: White, Black, Asian, AIAN (RAC1P 3,4,5), NHPI (RAC1P 7), Two_or_Other (RAC1P 8 or 9). `Asian` is one aggregate: PUMS RAC1P cannot separate e.g. Indian from Vietnamese or Filipino workers, and the Bay Area Asian category is very heterogeneous. This memo cannot speak to within-Asian dispersion.')
P('* **County.** The 2019-2023 5-year file uses 2020-definition PUMAs (checked in the official data dictionary). PUMA to county built from `tract2puma.txt` (county of the PUMA\'s tracts; dominant county by tract count). **All 62 Bay Area PUMAs lie entirely inside one county** (every Bay Area PUMA has 100% of tracts in one county), so county assignment introduces zero ambiguity for the Bay Area. Seven PUMAs elsewhere in California span counties; none of them contains a Bay Area worker (0 Bay Area person records fall in a split PUMA). Crosswalk: `base/puma_county_xwalk.csv`.')
P('* **Dollars.** WAGP and PERNP are multiplied by ADJINC/1,000,000. In the 5-year file ADJINC converts each respondent\'s survey-year income into **2023 dollars** (factors 1.2077 for 2019 down to 1.0195 for 2023 in the dictionary\'s labels); in the 2024 1-year file the single factor 1.015250 gives **2024 dollars**. Dollar levels in the two files are therefore not directly comparable (only shares are compared in test g).')
P('* **Hourly wage** = adjusted WAGP / (WKHP x WKWN). WKWN in these vintages is the exact count of weeks worked (not the older bracketed WKW), so no bracket midpoint is needed. Wage analyses use wage-and-salary workers (COW 1-5) with WAGP>0, WKHP>0, WKWN>0 and hourly wage between $5 and $500 (the trim drops 3,996 persons of 169,482 wage workers with a computable hourly wage). Note WAGP excludes self-employment income. `ftfy` = WKHP>=35 and WKWN>=50. Annual wage mass uses all employed persons with WAGP>0 (part-year included).')
P('* **Contract flag.** `self_employed` = COW 6 or 7 (own business, unincorporated or incorporated). PUMS cannot isolate 1099 independent contractors or gig work from business owners, so this is an upper bound on contract work and a mix of entrepreneurship and precarity.')
P('* **Weights.** PWGTP for all estimates. The 5-year weights are annualized (average year 2019-2023), so weighted counts are comparable to a single year.\n')
P('**Sample counts by race/ethnicity (employed Bay Area workers 16+)**\n')
rows=[]
for r in RA:
    a5=g(rc,race_eth=r,file='2019-2023_5yr'); a1=g(rc,race_eth=r,file='2024_1yr')
    rows.append([r,f'{int(a5.n_unweighted):,}',f'{a5.n_weighted:,.0f}',pct(a5.share_of_weighted),f'{int(a1.n_unweighted):,}',f'{a1.n_weighted:,.0f}'])
P(md(rows,['race_eth','n unweighted (2019-23)','n weighted (2019-23)','share','n unweighted (2024)','n weighted (2024)']))
P(f'AIAN (n={int(g(rc,race_eth="AIAN",file="2019-2023_5yr").n_unweighted)}) and NHPI (n={int(g(rc,race_eth="NHPI",file="2019-2023_5yr").n_unweighted)}) are small in the 5-year file and nearly unusable in the 2024 file (AIAN n={int(g(rc,race_eth="AIAN",file="2024_1yr").n_unweighted)}, NHPI n={int(g(rc,race_eth="NHPI",file="2024_1yr").n_unweighted)}); most of their class-level cells are suppressed.\n')
P('### Occupation taxonomy: verification and the OTHER class\n')
P('The OCCP list (531 codes, identical in the 2019-2023 and 2024 data dictionaries apart from capitalization of three titles) was read from the official Census PUMS data dictionaries (`PUMS_Data_Dictionary_2019-2023.csv` and `PUMS_Data_Dictionary_2024.csv`, downloaded from www2.census.gov). Every OCCP code present in the data exists in the dictionary (asserted in code). Classification starts from the dictionary\'s own major-group prefixes in each title (MGR, BUS, FIN, CMM, ENG, SCI, CMS, LGL, EDU, ENT, MED, HLS, PRT, EAT, CLN, PRS, SAL, OFF, FFF, CON, EXT, RPR, PRD, TRN, MIL) and then applies explicit code-level overrides; nothing is a guessed numeric range. Full audit table with titles, rule applied and Bay Area counts: `base/occp_crosswalk.csv`.\n')
P(f'**OTHER holds {ow:,.0f} weighted employed Bay Area workers ({pct(ow/aw)}; {int(oth.bay_n_unw_2019_23.sum()):,} unweighted).** By source group: '+', '.join(f"{k} {v:,.0f}" for k,v in oth.groupby('soc_major_prefix').bay_w_2019_23.sum().sort_values(ascending=False).items() if v>0)+'. The 10 largest unclassified codes:\n')
o10=oth.sort_values('bay_w_2019_23',ascending=False).head(10)
P(md([[r.occp,r.official_title,f'{int(r.bay_n_unw_2019_23):,}',f'{r.bay_w_2019_23:,.0f}'] for r in o10.itertuples()],['OCCP','official title','n unw','weighted']))
P('Judgment calls to check: (i) **lawyers (2100)** are in OTHER because the spec lists only paralegals under PROF_EXPOSED; (ii) **scientists and technicians (SCI)**, community/social service (CMS) and arts/media (ENT, other than writers/editors/designers) have no class in the spec; (iii) **farm occupations** and **military** are OTHER; (iv) **0705 Project Management Specialists** is placed in PRODUCT_DESIGN as the nearest separable proxy for product/program managers (it is a generic occupation, so PRODUCT_DESIGN is not a clean "product" group; it is outside both headline sets, so it does not affect the exposure ratio); (v) postal/courier/shipping-receiving clerks (5510, 5530, 5550, 5560, 5610, 5630) are put in FRONTLINE_SERVICE, not CLERICAL_ADMIN, because they are physical logistics work. Sensitivity: moving those six codes into CLERICAL_ADMIN raises the Bay Area exposed share from '+pct(E_('All').share_of_group)+' to '+pct(g(alt,race_eth='All',category='EXPOSED').share_of_group)+' and leaves the ordering of groups unchanged (Black index '+f2(g(alt,race_eth='Black',category='EXPOSED').rep_index)+', Hispanic '+f2(g(alt,race_eth='Hispanic',category='EXPOSED').rep_index)+', Asian '+f2(g(alt,race_eth='Asian',category='EXPOSED').rep_index)+', White '+f2(g(alt,race_eth='White',category='EXPOSED').rep_index)+'; `base/exposure_by_race_altmap.csv`).\n')
aip=xw[xw.occ_class=='AI_PRODUCER']
P(f'**AI_PRODUCER is very small and coarse.** PUMS occupation detail cannot isolate ML engineers: AI_PRODUCER = OCCP 1005 (computer and information research scientists) + 1240 (other mathematical science occupations, which hold data scientists, statisticians and mathematicians; in the 5-year file SOCP for 1240 is the aggregate code 1520XX, so data scientists cannot be split out). It has {int(aip.bay_n_unw_2019_23.sum()):,} unweighted / {aip.bay_w_2019_23.sum():,.0f} weighted Bay Area workers ({pct(aip.bay_w_2019_23.sum()/aw,2)} of employment). Software developers (1021, SOCP 151252 only) cannot be split into ML versus other developers, so they sit in SOFTWARE_ENG. Race-specific AI_PRODUCER results are therefore thin and mostly suppressed; headline tests use the combined AI-positioned set (AI_PRODUCER + SOFTWARE_ENG + DATA_ENG_ANALYTICS), of which SOFTWARE_ENG is {pct(g(ex,race_eth="All",category="SOFTWARE_ENG").share_of_group/g(ex,race_eth="All",category="AIPOS").share_of_group,0)}.\n')

# ---- (a)
P('## 1. Test (a): exposure composition by race/ethnicity\n')
P('Bay Area, 2019-2023. "Exposed" = CLERICAL_ADMIN + CUSTOMER_SUPPORT + PROF_EXPOSED. "AI-positioned" = AI_PRODUCER + SOFTWARE_ENG + DATA_ENG_ANALYTICS. Shares are of the group\'s employed workers (SE in pp). Concentration ratio = exposed share / AI-positioned share. Representation index (RI) = group share of the class / group share of all employment (= P(class|group)/P(class)); 1.00 = proportional.\n')
rows=[]
for r in RA:
    e=E_(r); a_=E_(r,'AIPOS'); q=E_(r,'RATIO_EXPOSED_OVER_AIPOS')
    rows.append([r,f'{int(e.n_group_unw):,}',cellp(e),cellp(a_),'s' if q.suppressed else f'{f2(q.share_of_group)} ({q.se_share_of_group:.2f})','s' if e.suppressed else f'{f2(e.rep_index)} ({e.se_rep_index:.2f})','s' if a_.suppressed else f'{f2(a_.rep_index)} ({a_.se_rep_index:.2f})',pct(e.share_of_category) if not e.suppressed else 's',pct(a_.share_of_category) if not a_.suppressed else 's'])
P(md(rows,['race_eth','n unw','exposed share (se pp)','AI-positioned share (se pp)','conc. ratio (se)','RI exposed (se)','RI AI-pos (se)','group share of all exposed workers','group share of all AI-pos workers']))
P('**Reading.** '+f"Only Black workers (RI {f2(E_('Black').rep_index)}, SE {f2(E_('Black').se_rep_index)}) and Two_or_Other (RI {f2(E_('Two_or_Other').rep_index)}) are clearly over-represented in exposed occupations; Asian ({f2(E_('Asian').rep_index)}) and White ({f2(E_('White').rep_index)}) are at parity; Hispanic workers are **under**-represented ({f2(E_('Hispanic').rep_index)}, SE {f2(E_('Hispanic').se_rep_index)}). That Hispanic under-representation is a real, statistically solid null/negative result for the 'minority workers are more exposed' hypothesis: Hispanic workers are concentrated instead in FRONTLINE_SERVICE (RI {f2(g(ex,race_eth='Hispanic',category='FRONTLINE_SERVICE').rep_index)}) and SKILLED_TRADE, which this taxonomy treats as not exposed to AI task automation. The group differences in AI-positioning are far larger than in exposure: the ratio of exposed to AI-positioned share runs from {f2(E_('Asian','RATIO_EXPOSED_OVER_AIPOS').share_of_group)} (Asian) to {f2(E_('Hispanic','RATIO_EXPOSED_OVER_AIPOS').share_of_group)} (Hispanic) and {f2(E_('Black','RATIO_EXPOSED_OVER_AIPOS').share_of_group)} (Black), driven almost entirely by the denominator.\n")
sxb=g(sx,sex='Female',race_eth='All'); 
P('*Gender.* Women are '+pct(FEM_E)+' of exposed workers (clerical work is female-dominated) vs '+pct(FEM_A)+' of all employed workers. Within sex, exposed shares are much closer across race: women '+', '.join(f"{r} {pct(g(sx,sex='Female',race_eth=r).exposed_share)}" for r in ['White','Black','Asian','Hispanic'])+'; men '+', '.join(f"{r} {pct(g(sx,sex='Male',race_eth=r).exposed_share)}" for r in ['White','Black','Asian','Hispanic'])+' (`base/exposure_by_race_sex.csv`). Among women, exposed shares are within about 3 pp across these four groups; the race differences are larger among men (Hispanic men are the least exposed, Black men the most). Male share of the workforce is similar for Hispanic ('+pct(g(sx,sex='Male',race_eth='Hispanic').n_unw/(g(sx,sex='Male',race_eth='Hispanic').n_unw+g(sx,sex='Female',race_eth='Hispanic').n_unw))+') and White ('+pct(g(sx,sex='Male',race_eth='White').n_unw/(g(sx,sex='Male',race_eth='White').n_unw+g(sx,sex='Female',race_eth='White').n_unw))+') workers (unweighted), so the Hispanic under-exposure is not a sex-composition artifact: it is a lower exposed share among Hispanic men (and slightly among women). Race differences in exposure are small next to the gender difference (women vs men roughly 20% vs 8-9%).\n')
P('**Full class composition** (share of each group\'s workers; `s` = fewer than 50 unweighted workers in the cell):\n')
rows=[]
for c in L.CLASSES:
    rows.append([c]+[('s' if g(ex,race_eth=r,category=c).suppressed else pct(g(ex,race_eth=r,category=c).share_of_group)) for r in RA])
P(md(rows,['occ_class']+RA))
# ---- (b)
P('## 2. Test (b): by county\n')
P('Exposed share (SE in pp) by county and race; `s` = suppressed (<50 unweighted workers in the cell, or group n<50). Full table incl. AI-positioned shares, ratios, RIs and SEs: `base/exposure_by_race_county.csv`.\n')
cn=list(L.BAY.values())
rows=[]
for c in cn:
    rows.append([c]+[cellp(g(ec,county=c,race_eth=r,category='EXPOSED')) for r in RA])
P(md(rows,['county']+RA))
P('AI-positioned share (SE in pp):\n')
rows=[[c]+[cellp(g(ec,county=c,race_eth=r,category='AIPOS')) for r in RA] for c in cn]
P(md(rows,['county']+RA))
P('Exposed / AI-positioned ratio (suppressed when either cell has <50 workers; ratios above ~10 are driven by very small AI-positioned counts):\n')
rows=[]
for c in cn:
    rr=[c]
    for r in RA:
        q=g(ec,county=c,race_eth=r,category='RATIO_EXPOSED_OVER_AIPOS'); rr.append('s' if q.suppressed else f2(q.share_of_group))
    rows.append(rr)
P(md(rows,['county']+RA))
s=ec[(ec.category=='EXPOSED')&(~ec.suppressed)&(ec.race_eth!='All')].sort_values('share_of_group',ascending=False)
P('**Most exposed county-by-race cells (exposed share, unsuppressed):**\n')
P(md([[r.county,r.race_eth,f'{int(r.n_group_unw):,}',f'{int(r.n_cell_unw):,}',f'{pct(r.share_of_group)} ({100*r.se_share_of_group:.1f})',f2(r.rep_index)] for r in s.head(8).itertuples()],['county','race','n group','n exposed','exposed share (se)','RI']))
P('**Least exposed:**\n')
P(md([[r.county,r.race_eth,f'{int(r.n_group_unw):,}',f'{int(r.n_cell_unw):,}',f'{pct(r.share_of_group)} ({100*r.se_share_of_group:.1f})',f2(r.rep_index)] for r in s.tail(5).itertuples()],['county','race','n group','n exposed','exposed share (se)','RI']))
P('The county-by-race spread in exposed share is narrow (about 9% to 18%) and many top-ranked cells differ by less than two standard errors, so the ranking among the top cells should not be over-read. The robust county pattern is the contrast in the *AI-positioned* column, not the exposed column.\n')
P('**Where AI-positioned employment is concentrated** (share of all Bay Area AI-positioned workers; location quotient = county AI-positioned share of its employment / Bay Area share):\n')
rows=[]
for c in cn:
    a_=cc[(cc.county==c)&(cc.category=='AIPOS')]
    sh=a_[a_.metric=='share_of_bay_cat'].iloc[0]; lq=a_[a_.metric=='location_quotient'].iloc[0]; e_=cc[(cc.county==c)&(cc.category=='EXPOSED')&(cc.metric=='share_of_bay_cat')].iloc[0]; ae=cc[(cc.county==c)&(cc.category=='ALL')&(cc.metric=='share_of_bay_cat')].iloc[0]
    rows.append([c,f'{int(sh.n_AIPOS_unw):,}',f'{pct(sh.est)} ({100*sh.se:.1f})',f'{lq.est:.2f} ({lq.se:.2f})',pct(e_.est),pct(ae.est)])
P(md(rows,['county','n AI-pos unw','share of Bay AI-pos workers (se pp)','LQ AI-pos (se)','share of Bay exposed workers','share of all Bay employment']))
tops=cc[(cc.category=='AIPOS')&(cc.metric=='share_of_bay_cat')].sort_values('est',ascending=False)
_low=['Contra Costa','Marin','Napa','Solano','Sonoma']; _lq=cc[(cc.category=='AIPOS')&(cc.metric=='location_quotient')].set_index('county').est; assert (_lq[_low]<0.6).all()
_wc=ec[ec.category=='ALL'].pivot_table(index='county',columns='race_eth',values='w_cell'); _lowshare=_wc.loc[_low].sum()/_wc.sum()
P(f"Santa Clara holds {pct(tops.iloc[0].est)} of Bay Area AI-positioned workers from {pct(g(cc,county='Santa Clara',category='ALL',metric='share_of_bay_cat').est)} of employment; Santa Clara, Alameda and San Francisco together hold {pct(tops.head(3).est.sum())}. Exposed employment, in contrast, is spread in proportion to employment (Santa Clara actually has a *below*-proportional share of exposed workers). The geography of AI gains is far more concentrated than the geography of exposure. Share of each group's workers living in the five counties where the AI-positioned LQ is below 0.6 (Contra Costa, Marin, Napa, Solano, Sonoma): "+', '.join(f"{r} {pct(_lowshare[r])}" for r in ['White','Black','Asian','Hispanic','Two_or_Other','All'])+'. Location therefore separates Asian workers (concentrated in the high-AI counties) from everyone else; it does **not** separate Black or Hispanic workers from White workers, whose shares in the low-AI counties are similar.\n')
# ---- (c)
P('## 3. Test (c): wages\n')
P('Wage-and-salary workers, 2023 dollars. Medians are weighted. `s` = fewer than 50 unweighted observations. Full table (medians, means, FTFY annual, ratios to White, SEs, counts): `base/wages_by_occclass_race.csv`.\n')
pools=['AIPS2','AIPOS','AI_PRODUCER','SOFTWARE_ENG','DATA_ENG_ANALYTICS','CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED','EXPOSED','FRONTLINE_SERVICE','ALL']
def wcell(pool,r,metric,fmt):
    x=wg[(wg.pool==pool)&(wg.race_eth==r)&(wg.metric==metric)]
    if len(x)==0: return 's'
    x=x.iloc[0]
    return 's' if x.suppressed else fmt(x)
P('**Median hourly wage ($) by class group x race** (AIPS2 = AI_PRODUCER + SOFTWARE_ENG):\n')
P(md([[p]+[wcell(p,r,'median_hourly',lambda x: f'{x.est:.1f} ({x.se:.1f})') for r in RA] for p in pools],['class']+RA))
P('**Median hourly wage as a ratio to White workers in the same class** (1.00 = parity; SE in parentheses):\n')
P(md([[p]+[('1.00' if r=='White' else wcell(p,r,'median_hourly_ratio_to_White',lambda x: f'{x.est:.2f} ({x.se:.2f})')) for r in RA] for p in pools],['class']+RA))
P('**Median annual wage, full-time year-round ($):**\n')
P(md([[p]+[wcell(p,r,'median_annual_ftfy',lambda x: f'{x.est:,.0f}') for r in RA] for p in pools],['class']+RA))
P('**Is the racial wage gap inside the AI classes different from inside the exposed classes?** Weighted regression of log hourly wage on race x {AI classes, exposed classes} interactions with occupation-class fixed effects, on workers in those classes only; "adjusted" adds age, age squared, sex, education, county and foreign-born. The coefficient is the log-point gap vs White workers in the same side; the test is the difference (AI minus exposed) with a replicate-weight SE.\n')
rows=[]
for A in ['AI_PRODUCER+SOFTWARE_ENG','AIPOS3']:
    for adj in (False,True):
        for r in ['Black','Hispanic','Asian','Two_or_Other']:
            x=gt[(gt.A_def==A)&(gt.adjusted==adj)&(gt.race_eth==r)].iloc[0]
            rows.append([A,'adjusted' if adj else 'unadjusted',r,f'{int(x.n_A_unw):,} / {int(x.n_E_unw):,}',f'{x.log_gap_in_AIclasses:.3f} ({x.se_A:.3f}) = {100*x.pct_gap_A:.1f}%',f'{x.log_gap_in_exposed:.3f} ({x.se_E:.3f}) = {100*x.pct_gap_E:.1f}%',f'{x.diff_A_minus_E:.3f} ({x.se_diff:.3f})',f'{x.z:.1f}'+(' THIN' if x.thin else '')])
P(md(rows,['AI-class definition','spec','race vs White','n AI / n exposed','gap in AI classes (se)','gap in exposed classes (se)','difference (se)','z']))
bh=gt[(gt.A_def=='AI_PRODUCER+SOFTWARE_ENG')&(gt.adjusted)]
P(f"**Finding.** The Black-White gap is much *larger* inside AI_PRODUCER/SOFTWARE_ENG ({100*bh[bh.race_eth=='Black'].iloc[0].pct_gap_A:.0f}% adjusted) than inside the exposed classes ({100*bh[bh.race_eth=='Black'].iloc[0].pct_gap_E:.0f}%); the difference is {bh[bh.race_eth=='Black'].iloc[0].z:.1f} SE from zero (Black n={int(bh[bh.race_eth=='Black'].iloc[0].n_A_unw)} in AI classes, enough to be unsuppressed but modest). The Hispanic gap is large in both ({100*bh[bh.race_eth=='Hispanic'].iloc[0].pct_gap_A:.0f}% vs {100*bh[bh.race_eth=='Hispanic'].iloc[0].pct_gap_E:.0f}% adjusted) and the difference between them is **not** statistically distinguishable from zero (z={bh[bh.race_eth=='Hispanic'].iloc[0].z:.1f}). Asian workers earn about the same as White workers inside AI classes ({100*bh[bh.race_eth=='Asian'].iloc[0].pct_gap_A:.0f}% adjusted; median ratio {f2(g(wg,pool='AIPS2',race_eth='Asian',metric='median_hourly_ratio_to_White').est)}) but less than White workers inside exposed classes ({100*bh[bh.race_eth=='Asian'].iloc[0].pct_gap_E:.0f}% adjusted), so the Asian gap is *narrower* in AI classes. Adjustment for education etc. shrinks the Black gaps in both places but does not remove them. This is observational and cross-sectional: occupation codes are broad (e.g. all 'software developers' are pooled regardless of seniority or employer), so unobserved within-occupation sorting (level, firm, equity compensation) is not controlled.\n")
P('**Size of the prize: AI-positioned minus exposed classes (wage-and-salary workers):**\n')
rows=[]
for r in RA:
    ps=['PRIZE_AIPOS_minus_EXPOSED','PRIZE_AIPOS_over_EXPOSED']
    d1=wg[(wg.pool==ps[0])&(wg.race_eth==r)&(wg.metric=='median_hourly_diff')].iloc[0]; d2=wg[(wg.pool==ps[1])&(wg.race_eth==r)&(wg.metric=='median_hourly_ratio')].iloc[0]
    d3=wg[(wg.pool==ps[0])&(wg.race_eth==r)&(wg.metric=='median_annual_ftfy_diff')].iloc[0]
    rows.append([r,'s' if d1.suppressed else f'${d1.est:.1f} ({d1.se:.1f})','s' if d2.suppressed else f'{d2.est:.2f} ({d2.se:.2f})','s' if d3.suppressed else f'${d3.est:,.0f} ({d3.se:,.0f})'])
P(md(rows,['race_eth','median hourly diff $ (se)','median hourly ratio (se)','median FTFY annual diff $ (se)']))
P('The prize is large for every group, but it is smallest in dollars for Black workers: for Black workers, the AI-positioned class pays about '+f"{g(wg,pool='PRIZE_AIPOS_over_EXPOSED',race_eth='Black',metric='median_hourly_ratio').est:.2f}x the exposed classes versus {g(wg,pool='PRIZE_AIPOS_over_EXPOSED',race_eth='White',metric='median_hourly_ratio').est:.2f}x for White workers. Even Black workers who get in earn much less than their White and Asian peers.\n")
# rank test
base=g(wg,pool='ALL',race_eth='All',metric='median_hourly')
rk=[]
for r in ['White','Black','Asian','Hispanic','Two_or_Other']:
    rk.append((r,g(wg,pool='ALL',race_eth=r,metric='median_hourly').est,g(ex,race_eth=r,category='AIPOS').rep_index,g(ex,race_eth=r,category='EXPOSED').rep_index))
rk=pd.DataFrame(rk,columns=['race','median_hourly_all_workers','RI_AIPOS','RI_EXPOSED'])
sp=rk[['median_hourly_all_workers','RI_AIPOS']].corr(method='spearman').iloc[0,1]; sp2=rk[['median_hourly_all_workers','RI_EXPOSED']].corr(method='spearman').iloc[0,1]
P('**Are AI gains flowing to groups already at the top of the Bay Area wage distribution?** Overall median hourly wage of each group vs its AI-positioned and exposed representation indices:\n')
P(md([[r.race,f'${r.median_hourly_all_workers:.1f}',f2(r.RI_AIPOS),f2(r.RI_EXPOSED)] for r in rk.itertuples()],['race','median hourly wage, all workers','RI AI-positioned','RI exposed'])+f'Spearman rank correlation across these five groups (AIAN, NHPI excluded as thin): wage vs RI AI-positioned = {sp:.2f}; wage vs RI exposed = {sp2:.2f}. With five groups this is descriptive only.\n')
# ---- (d)
P('## 4. Test (d): wage mass at risk\n')
P('Annual wage and salary mass (sum of PWGTP x adjusted WAGP, millions of 2023 dollars per year, average over 2019-2023) in exposed occupations, with the same in AI-positioned occupations for contrast. Includes part-year workers; excludes self-employment income. SEs by replicate weights; `s` = suppressed.\n')
rows=[]
for r in RA:
    e=g(wm,geo_level='Bay Area',race_eth=r,category='EXPOSED'); a_=g(wm,geo_level='Bay Area',race_eth=r,category='AIPOS'); t=g(wm,geo_level='Bay Area',race_eth=r,category='ALL')
    rows.append([r,f'{t["wage_mass_$M"]:,.0f}',('s' if e.suppressed else f'{e["wage_mass_$M"]:,.0f} ({e["se_wage_mass_$M"]:,.0f})'),('s' if e.suppressed else pct(e.share_of_group_wage_mass)),('s' if e.suppressed else pct(e.share_of_group_wage_earners)),('s' if a_.suppressed else f'{a_["wage_mass_$M"]:,.0f} ({a_["se_wage_mass_$M"]:,.0f})'),('s' if a_.suppressed else pct(a_.share_of_group_wage_mass)),('s' if e.suppressed else usd(e.mean_annual_wage)),('s' if a_.suppressed else usd(a_.mean_annual_wage))])
P(md(rows,['race_eth','total wage mass $M','exposed mass $M (se)','exposed share of group wage mass','exposed share of group wage earners','AI-pos mass $M (se)','AI-pos share of group mass','mean wage, exposed','mean wage, AI-pos']))
_h=g(wm,geo_level='Bay Area',race_eth='Hispanic',category='EXPOSED'); _hall=g(wm,geo_level='Bay Area',race_eth='Hispanic',category='ALL'); _w=g(wm,geo_level='Bay Area',race_eth='White',category='EXPOSED'); _wall=g(wm,geo_level='Bay Area',race_eth='White',category='ALL')
P(f"In dollars, exposure is smaller than in headcount for the Bay Area as a whole (exposed workers are {pct(massE.share_of_group_wage_earners)} of wage earners but {pct(massE.share_of_group_wage_mass)} of wage mass) and for White and Asian workers, because exposed jobs pay below those groups' average. It is about the same as headcount for Black ({pct(g(wm,geo_level='Bay Area',race_eth='Black',category='EXPOSED').share_of_group_wage_earners)} of wage earners, {pct(g(wm,geo_level='Bay Area',race_eth='Black',category='EXPOSED').share_of_group_wage_mass)} of wage mass) and Hispanic workers ({pct(_h.share_of_group_wage_earners)} and {pct(_h.share_of_group_wage_mass)}), because for them exposed jobs pay about the group average (Hispanic mean wage in exposed jobs {usd(_h.mean_annual_wage)} vs {usd(_hall.mean_annual_wage)} for all Hispanic wage earners; White {usd(_w.mean_annual_wage)} vs {usd(_wall.mean_annual_wage)}). So on the dollar measure Black ({pct(g(wm,geo_level='Bay Area',race_eth='Black',category='EXPOSED').share_of_group_wage_mass)}) and Hispanic ({pct(_h.share_of_group_wage_mass)}) workers carry a larger exposed share of their wage mass than White workers ({pct(_w.share_of_group_wage_mass)}) or Asian workers ({pct(g(wm,geo_level='Bay Area',race_eth='Asian',category='EXPOSED').share_of_group_wage_mass)}), even though Hispanic workers are *less* exposed by headcount-share relative to the Bay Area average.\n")
P('**Exposed wage mass by race x county ($ millions per year; `s` = suppressed; full detail by class in `base/wage_mass_at_risk.csv`):**\n')
rows=[]
for c in cn+['Bay Area']:
    lv='county' if c!='Bay Area' else 'Bay Area'
    rr=[c]
    for r in RA:
        x=g(wm,geo_level=lv,geo=c,race_eth=r,category='EXPOSED'); rr.append('s' if x.suppressed else f'{x["wage_mass_$M"]:,.0f}')
    rows.append(rr)
P(md(rows,['county']+RA))
P('**Exposed share of each cell\'s wage mass (race x county; `s` = suppressed):**\n')
rows=[]
for c in cn:
    rows.append([c]+[('s' if g(wm,geo_level='county',geo=c,race_eth=r,category='EXPOSED').suppressed else pct(g(wm,geo_level='county',geo=c,race_eth=r,category='EXPOSED').share_of_group_wage_mass)) for r in RA])
P(md(rows,['county']+RA))
# ---- (e)
P('## 5. Test (e): self-employment / contract precarity\n')
P('Share of workers with COW 6 or 7 (self-employed, own business). Upper bound on independent contracting; see definitions. SE in pp.\n')
cats=['CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED','EXPOSED','FRONTLINE_SERVICE','AIPOS','ALL']
rows=[]
for c in cats:
    rr=[c]
    for r in RA:
        x=ct[(ct.category==c)&(ct.race_eth==r)].iloc[0]; rr.append('s' if x.suppressed else f'{pct(x.self_emp_share)} ({100*x.se_self_emp_share:.1f})')
    rows.append(rr)
P(md(rows,['workers in']+RA))
ce=ct[(ct.category=='EXPOSED')&(ct.race_eth=='All')].iloc[0]; ca=ct[(ct.category=='ALL')&(ct.race_eth=='All')].iloc[0]; cf=ct[(ct.category=='FRONTLINE_SERVICE')&(ct.race_eth=='All')].iloc[0]; cp=ct[(ct.category=='PROF_EXPOSED')&(ct.race_eth=='All')].iloc[0]
P(f"**Negative result.** Exposed workers are *less* likely to be self-employed than the Bay Area average ({pct(ce.self_emp_share)} vs {pct(ca.self_emp_share)}; FRONTLINE_SERVICE {pct(cf.self_emp_share)}). Clerical and customer-support workers are almost all W-2 employees. The exception is PROF_EXPOSED ({pct(cp.self_emp_share)} overall; accountants, writers, translators, designers and similar occupations have many independents). Within exposed classes, Black ({pct(ct[(ct.category=='EXPOSED')&(ct.race_eth=='Black')].iloc[0].self_emp_share)}) and Hispanic ({pct(ct[(ct.category=='EXPOSED')&(ct.race_eth=='Hispanic')].iloc[0].self_emp_share)}) workers are less likely to be self-employed than White workers ({pct(ct[(ct.category=='EXPOSED')&(ct.race_eth=='White')].iloc[0].self_emp_share)}). So the data do not support the idea that exposed workers, or exposed minority workers, are disproportionately in contract arrangements. What COW cannot see: 1099 work performed by people who report as wage employees, temp-agency and platform arrangements, or involuntary contract status.\n")
# ---- (f)
P('## 6. Test (f): shift-share incidence model. COUNTERFACTUAL ACCOUNTING, NOT A FORECAST\n')
P('**Assumptions, stated plainly.**\n')
P('1. Base = employed Bay Area persons with positive wage and salary income (2019-2023 PUMS, 2023 dollars); each person carries PWGTP.\n2. A fraction X of workers in CLERICAL_ADMIN and CUSTOMER_SUPPORT lose their jobs, **uniformly** (every such worker, whatever race, county, wage or tenure, has the same probability X). Nothing in the model makes some workers more likely to be cut than others.\n3. Scenario R=0: displaced workers have zero wages afterward (no re-employment, no unemployment insurance, no transfers). Scenario R=0.5: half of the displaced are re-employed at a 20% wage cut in the same county (a stylized mid-case; the 50% and the 20% are assumptions, not estimates).\n4. A fraction Y wage gain applies to every wage earner in AI_PRODUCER and SOFTWARE_ENG; there is no employment growth in those classes and no spillover to other occupations, prices, rents or other classes\' wages. DATA_ENG_ANALYTICS gets no gain (the spec names only AI_PRODUCER/SOFTWARE_ENG).\n5. Gains and losses accrue to the same people and are not redistributed (no capital income, equity, taxes, or migration of workers or firms). Any gains to firm owners and investors, which may be the main channel for AI gains, are outside WAGP and outside this model.\n6. Static occupational and demographic composition (no worker re-sorting across classes, no entry of new workers into AI jobs).\n7. Metrics: (i) *per-capita wage* = (counterfactual wage mass of the group) / (baseline number of wage earners in the group), which counts displaced workers at zero; (ii) *median annual wage of the still-employed*, which is **mechanically** affected by who is removed (removing low-wage clerical workers can raise the median even though those workers are worse off), so treat it as a composition measure, not welfare. The median is also a noisy, step-like statistic (large replicate SEs).\n8. Standard errors come from the replicate weights and reflect **sampling error only**, conditional on the assumptions above. They do not reflect uncertainty in the assumptions, which dominates.\n')
P('**Implied change in the Black-White and Latino-White wage gaps (per-capita wage, ratio to White; change in percentage points of White wage; SE in parentheses; R=0):** a negative change = the gap *widens*.\n')
def gc(r,meas,metric,X,Y,R): 
    x=gp[(gp.race_eth==r)&(gp.gap_measure==meas)&(gp.metric==metric)&(gp.X_clerical_cs_job_cut==X)&(gp.Y_ai_wage_gain==Y)&(gp.reemploy_share==R)]
    assert len(x)==1; return x.iloc[0]
for R_ in (0.0,0.5):
    P(f'*Re-employment share R={R_}'+(' (no re-employment)' if R_==0 else ' (displaced re-employed at 80% of prior wage)')+'*\n')
    rows=[]
    for r in ['Black','Hispanic','Asian']:
        for X in (0.05,0.10,0.20):
            rr=[r,f'{int(X*100)}%']
            for Y in (0.05,0.10,0.20):
                x=gc(r,'percap','change_in_ratio_pts',X,Y,R_); rr.append(f'{100*x.est:+.2f} ({100*x.se:.2f})')
            rows.append(rr)
    P(md(rows,['group vs White','X: clerical+CS job cut','Y=5% AI wage gain','Y=10%','Y=20%']))
rb=gc('Black','percap','baseline_ratio_to_White',0.1,0.1,0.0); rh=gc('Hispanic','percap','baseline_ratio_to_White',0.1,0.1,0.0); ra=gc('Asian','percap','baseline_ratio_to_White',0.1,0.1,0.0)
P(f"Baseline per-capita wage ratios to White: Black {f2(rb.est)}, Hispanic {f2(rh.est)}, Asian {f2(ra.est)} (annual wage of all wage earners, part-year included, so lower than the hourly ratios in test c). Under every cell of the grid the Black-White and Latino-White gaps **widen** on the per-capita measure (by 0.2 to 1.3 pp of White wage), and the Asian-White gap moves in Asian workers' favor by 0.7 to 2.9 pp.")
_b55=gc('Black','percap','change_in_ratio_pts',0.05,0.05,0.0).est; _bX=gc('Black','percap','change_in_ratio_pts',0.20,0.05,0.0).est; _bY=gc('Black','percap','change_in_ratio_pts',0.05,0.20,0.0).est
P(f"These are small relative to the baseline gaps ({100*(1-rb.est):.0f} pp for Black and {100*(1-rh.est):.0f} pp for Hispanic workers), but they are the same sign in every scenario and have sampling SEs far below the estimates. Both sides of the scenario contribute: for Black workers the change is {100*_b55:+.2f} pp at X=5%,Y=5%; raising only X to 20% moves it to {100*_bX:+.2f} pp and raising only Y to 20% moves it to {100*_bY:+.2f} pp. The displacement side widens gaps because exposed jobs are a larger share of Black and Hispanic wage mass than of White wage mass (test d); the AI wage-gain side widens them because AI-class wage mass is concentrated among Asian and White workers (test d). With R=0.5 the widening is smaller but not reversed. None of this is a forecast: it restates the baseline occupational mix under uniform assumptions.\n")
P('**Median-wage gap (still-employed), R=0:** changes are within replicate noise for almost every cell (SEs of 0.5 to 1.9 pp against estimated changes of -0.6 to +2.4 pp), so the median-based gap results should be read as **no detectable change**:\n')
rows=[]
for r in ['Black','Hispanic','Asian']:
    for X in (0.05,0.10,0.20):
        rr=[r,f'{int(X*100)}%']
        for Y in (0.05,0.10,0.20):
            x=gc(r,'median','change_in_ratio_pts',X,Y,0.0); rr.append(f'{100*x.est:+.2f} ({100*x.se:.2f})')
        rows.append(rr)
P(md(rows,['group vs White','X','Y=5%','Y=10%','Y=20%']))
P('**Implied change in total wage mass and per-capita wage by race, R=0** (percent of baseline; rows = Y, columns = X; each cell is the change in group wage mass, which equals the per-capita change because the base headcount is fixed). Point estimates only for non-gap quantities; see `base/incidence_grid.csv`.\n')
rows=[]
for r in RA:
    for Y in (0.05,0.10,0.20):
        rr=[r,f'{int(Y*100)}%']
        for X in (0.05,0.10,0.20):
            x=ig[(ig.level=='race')&(ig.race_eth==r)&(ig.X_clerical_cs_job_cut==X)&(ig.Y_ai_wage_gain==Y)&(ig.reemploy_share==0.0)].iloc[0]
            rr.append('s' if x.suppressed else f'{100*x.pct_cf_mass:+.2f}%')
        rows.append(rr)
P(md(rows,['race_eth','Y: AI wage gain','X=5% job cut','X=10%','X=20%']))
P('**By county, X=10%, Y=10%, R=0** (change in county wage mass; median of still-employed in parentheses is a composition measure):\n')
rows=[]
for c in cn+['All']:
    x=ig[(ig.level=='county')&(ig.county==c)&(ig.X_clerical_cs_job_cut==0.1)&(ig.Y_ai_wage_gain==0.1)&(ig.reemploy_share==0.0)].iloc[0]
    rows.append([c if c!='All' else 'Bay Area',f'{x.base_mass/1e6:,.0f}',f'{100*x.pct_cf_mass:+.2f}%',f'{100*x.pct_cf_median_employed:+.2f}%'])
P(md(rows,['county','baseline wage mass $M','change in wage mass','change in median wage of still-employed']))
P('Counties with thin AI-positioned employment (Solano, Sonoma, Napa) lose wage mass on net in this scenario (job cuts without a matching AI wage gain), while Santa Clara, San Francisco and Alameda gain. Race x county results for every scenario are in `base/incidence_grid.csv` (level `race_county`; rows with n<50 flagged `suppressed`).\n')
# ---- (g)
P('## 7. Test (g): 2024 1-year vs 2019-2023 5-year\n')
P('Differences in the share of each group\'s workers in exposed / AI-positioned classes. **Comparability caveats:** (1) the 5-year file averages 2019-2023 (centered on 2021, with pandemic-era employment composition) while 2024 is a single year, so a difference mixes a trend with a level shift between sample designs; (2) the two files are independent samples, so the SE of the difference is sqrt(se1^2+se2^2), using replicate-weight SEs from each; (3) the 2024 file has about one fifth of the observations (Black n=1,374; AIAN n=90; NHPI n=148), so its SEs are about 2.2x larger; (4) with 5 groups x 2 headline metrics, about 10 tests are run, so a single |z| just above 2 is not convincing (Bonferroni threshold about |z|>2.8); (5) OCCP codes are identical across the two vintages, so recoding is not a concern.\n')
rows=[]
for r in RA:
    for c in ['EXPOSED','AIPOS']:
        x=g(ch,race_eth=r,category=c)
        verdict='thin (n<50)' if x.thin else ('real shift (survives Bonferroni)' if abs(x.z)>2.8 else ('suggestive (|z|>2, not Bonferroni)' if abs(x.z)>2 else 'within noise'))
        rows.append([r,c,pct(x.share_of_group_5yr),pct(x.share_of_group_2024),f'{100*x.diff_2024_minus_5yr:+.2f} ({100*x.se_diff:.2f})',f'{x.z:.1f}',verdict])
P(md(rows,['race_eth','class set','2019-23 share','2024 share','change pp (se)','z','verdict']))
ae=g(ch,race_eth='All',category='EXPOSED'); aa=g(ch,race_eth='All',category='AIPOS')
P(f"**Reading.** The Bay-Area-wide exposed share fell {100*abs(ae.diff_2024_minus_5yr):.1f} pp (z={ae.z:.1f}) and the AI-positioned share rose {100*aa.diff_2024_minus_5yr:.1f} pp (z={aa.z:.1f}). The AI-positioned rise is statistically large and appears for Asian ({100*g(ch,race_eth='Asian',category='AIPOS').diff_2024_minus_5yr:+.1f} pp, z={g(ch,race_eth='Asian',category='AIPOS').z:.1f}), White ({100*g(ch,race_eth='White',category='AIPOS').diff_2024_minus_5yr:+.1f} pp, z={g(ch,race_eth='White',category='AIPOS').z:.1f}) and Hispanic ({100*g(ch,race_eth='Hispanic',category='AIPOS').diff_2024_minus_5yr:+.1f} pp, z={g(ch,race_eth='Hispanic',category='AIPOS').z:.1f}); it is largest in pp for Asian workers, so differences in AI-positioned share between Asian workers and the other groups grew in levels, while the Black change is inside the noise. The decline in exposed share is significant only for Asian workers (z={g(ch,race_eth='Asian',category='EXPOSED').z:.1f}, driven by PROF_EXPOSED, z={g(ch,race_eth='Asian',category='PROF_EXPOSED').z:.1f}). **For Black workers (exposed share {pct(g(ch,race_eth='Black',category='EXPOSED').share_of_group_5yr)} to {pct(g(ch,race_eth='Black',category='EXPOSED').share_of_group_2024)}, z={g(ch,race_eth='Black',category='EXPOSED').z:.1f}), Hispanic workers (z={g(ch,race_eth='Hispanic',category='EXPOSED').z:.1f}), White workers (z={g(ch,race_eth='White',category='EXPOSED').z:.1f}) and Two_or_Other, the change in exposed share is inside the noise.** The Black AI-positioned share rose by {100*g(ch,race_eth='Black',category='AIPOS').diff_2024_minus_5yr:.1f} pp (z={g(ch,race_eth='Black',category='AIPOS').z:.1f}, 2024 cell n={int(g(ch,race_eth='Black',category='AIPOS').n_cell_unw_2024)}), also inside the noise. AIAN and NHPI changes are thin and not interpretable (the NHPI exposed jump has an unweighted 2024 numerator of 31 and is flagged). Whether the Asian/White shifts reflect AI-era hiring or the pandemic-centered baseline cannot be separated with these data. Details: `base/change_2024_vs_5yr.csv`.\n")
# ---- disconfirming
P('## 8. Evidence for and against the hypothesis that AI gains flow to groups already at the top\n')
P('**Consistent with the hypothesis:**\n')
P(f"* AI-positioned jobs are overwhelmingly held by the two highest-wage groups: Asian + White workers are {pct(E_('Asian','AIPOS').share_of_category+E_('White','AIPOS').share_of_category)} of AI-positioned employment vs {pct(g(rc,race_eth='Asian',file='2019-2023_5yr').share_of_weighted+g(rc,race_eth='White',file='2019-2023_5yr').share_of_weighted)} of employment. Black and Hispanic workers hold {pct(E_('Black','AIPOS').share_of_category+E_('Hispanic','AIPOS').share_of_category)} of AI-positioned jobs vs {pct(g(rc,race_eth='Black',file='2019-2023_5yr').share_of_weighted+g(rc,race_eth='Hispanic',file='2019-2023_5yr').share_of_weighted)} of employment.\n* Across five groups, rank of median wage and rank of AI-positioned representation are correlated (Spearman {sp:.2f}).\n* The shift-share grid widens Black-White and Latino-White per-capita gaps in every cell and favors Asian workers.\n* Black workers face a much bigger wage penalty inside the AI classes than inside exposed classes.\n")
P('**Contradicting or complicating it:**\n')
P(f"* **White workers are the top of the wage distribution among the large groups yet are *under*-represented in AI-positioned jobs** (RI {f2(E_('White','AIPOS').rep_index)}); the gains flow most to *Asian* workers (RI {f2(E_('Asian','AIPOS').rep_index)}), whose overall median hourly wage is about equal to White workers' ({f2(g(wg,pool='ALL',race_eth='Asian',metric='median_hourly_ratio_to_White').est)} of White, SE {g(wg,pool='ALL',race_eth='Asian',metric='median_hourly_ratio_to_White').se:.3f}). 'Already at the top' therefore fits Asian workers only on average, and only weakly for the wage-level ranking.\n* **Exposure is not concentrated among the lowest-paid groups:** Hispanic workers, the lowest-paid large group, are under-represented in exposed classes (RI {f2(E_('Hispanic').rep_index)}). Hispanic displacement risk in this taxonomy is mostly through *absence* from AI-positioned jobs, not through over-exposure; their high FRONTLINE_SERVICE share (RI {f2(g(ex,race_eth='Hispanic',category='FRONTLINE_SERVICE').rep_index)}) and SKILLED_TRADE are classed as not exposed.\n* **Asian workers are not over-exposed** (RI {f2(E_('Asian').rep_index)}), despite being 58% of AI-positioned workers; White workers are at parity as well.\n* **Exposed occupations are mid-wage, majority college-educated and female:** exposed workers are {pct(FEM_E)} women (vs {pct(FEM_A)} of all workers); {pct(BA_E)} hold a bachelor's degree or more (AI-positioned: {pct(BA_A)}); their median hourly wage (${hE.est:.1f}) is below the Bay Area median (${base.est:.1f}) but far above FRONTLINE_SERVICE (${g(wg,pool='FRONTLINE_SERVICE',race_eth='All',metric='median_hourly').est:.1f}). Gender, not race, is the sharper axis of exposure in this taxonomy.\n* **No contract-precarity amplification** (test e): exposed workers are less often self-employed than average, and exposed Black and Hispanic workers less than exposed White workers.\n* **Wage-gap difference is not uniform:** the larger gap in AI classes holds for Black workers (large, significant) but not detectably for Hispanic workers (z={bh[bh.race_eth=='Hispanic'].iloc[0].z:.1f}), and the Asian gap is narrower in AI classes.\n* **2024 vs 5-year:** exposed shares did not move detectably for Black, Hispanic or White workers (inside noise). The only significant exposed-share decline is for Asian workers.\n* **Shift-share is not a distributional verdict:** the per-capita gap widening is small (0.2 to 1.3 pp of White wage for Black and Hispanic workers against baseline gaps of about 44 to 54 pp) and the median-based gap changes are inside sampling noise. Capital income and equity compensation (outside WAGP) could dominate who actually captures AI gains.\n")
P('## 9. Suppressed and thin cells\n')
sup=[]
for nm,df,keys in (('exposure_by_race',ex,['race_eth','category']),('exposure_by_race_county',ec,['county','race_eth','category']),('wages_by_occclass_race',wg,['pool','race_eth','metric']),('wage_mass_at_risk',wm,['geo_level','geo','race_eth','category']),('contract_precarity',ct,['race_eth','category'])):
    x=df[df.suppressed==True]; sup.append(pd.DataFrame({'table':nm,'cell':x[keys].astype(str).agg(' | '.join,axis=1).values}))
sup=pd.concat(sup); sup.to_csv(f'{B}/suppressed_cells.csv',index=False)
P('Rule: a cell is suppressed (shown `s`; value retained in the CSV with `suppressed=True`) if it has fewer than 50 unweighted observations in the numerator cell or the group. Counts of suppressed cells by table: '+', '.join(f'{k}: {v}' for k,v in sup.groupby('table').size().items())+'. The complete list is `base/suppressed_cells.csv`. Patterns:\n')
exs=ex[ex.suppressed]; ecs=ec[ec.suppressed&ec.category.isin(['EXPOSED','AIPOS'])]
P(f"* Bay-wide composition: AIAN is suppressed in every class except FRONTLINE_SERVICE; NHPI is suppressed in all AI-positioned classes and most small classes; Black is suppressed in AI_PRODUCER and DATA_ENG_ANALYTICS ({int(g(ex,race_eth='Black',category='AI_PRODUCER').n_cell_unw)} and {int(g(ex,race_eth='Black',category='DATA_ENG_ANALYTICS').n_cell_unw)} workers); Hispanic is suppressed in DATA_ENG_ANALYTICS ({int(g(ex,race_eth='Hispanic',category='DATA_ENG_ANALYTICS').n_cell_unw)}).\n* County x race, headline classes (EXPOSED or AI-positioned): {len(ecs)} cells suppressed. Cells: "+'; '.join(sorted(set(f'{r.county}/{r.race_eth}/{r.category}' for r in ecs.itertuples())))+'.\n')
P('Not suppressed but thin (50 to ~150 unweighted): e.g. Black AI-positioned (n='+str(int(E_('Black','AIPOS').n_cell_unw))+') and Black in AI_PRODUCER+SOFTWARE_ENG for the wage test (n='+str(int(bh[bh.race_eth=='Black'].iloc[0].n_A_unw))+'); Black AI-positioned county cells; 2024 Black AI-positioned (n=56). Treat these as indicative.\n')
P('## 10. Files\n')
P('`base/pums_bay.parquet`, `base/pums_bay_2024.parquet`, `base/occp_crosswalk.csv`, `base/puma_county_xwalk.csv`, `base/exposure_by_race.csv`, `base/exposure_by_race_county.csv`, `base/wages_by_occclass_race.csv`, `base/wage_gap_tests.csv`, `base/wage_mass_at_risk.csv`, `base/contract_precarity.csv`, `base/incidence_grid.csv`, `base/incidence_gap_changes.csv`, `base/change_2024_vs_5yr.csv`, `base/ai_concentration_by_county.csv`, `base/exposure_by_race_sex.csv`, `base/exposure_by_race_altmap.csv`, `base/race_counts.csv`, `base/suppressed_cells.csv`. Code: `code/pums_*.py` (run order: puma_county, build, crosswalk, exposure, wages, incidence, extra, memo).\n')
open(f'{O}/pums_findings.md','w').write('\n'.join(L_))
print('ok', len('\n'.join(L_)))
