import sys;sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
from jobs_lib import *
def md(df,fmt=None):
    df=df.copy()
    for c in df.columns:
        if df[c].dtype.kind=='f':
            df[c]=df[c].map(lambda v:'' if pd.isna(v) else (f'{v:,.0f}' if abs(v)>=1000 else (f'{v:.3f}' if abs(v)<10 else f'{v:.1f}')))
    h='| '+' | '.join(map(str,df.columns))+' |\n|'+'---|'*len(df.columns)+'\n'
    return h+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in df.values)+'\n'
cs=pd.read_csv(B+'jobs_class_summary.csv')
t1=cs[(cs['sample']=='BayArea')&(cs.level=='occ')][['cls','n','share_all','share_unseeded','share_sal','med','p25','p75','p90','med_lo','med_hi']].rename(columns={'cls':'class','share_all':'share_postings_all','share_unseeded':'share_postings_unseeded','share_sal':'share_with_salary','med':'median_annualized','med_lo':'median_sal_lo','med_hi':'median_sal_hi'})
t1h=cs[(cs['sample']=='BayArea')&(cs.level=='occ')][['cls','n_sal','share_sal_hourly','n_hourly','med_hourly_rate','p25_rate','p75_rate','pt_share_hourly','n_annual_posted','med_annual_posted_only']].rename(columns={'cls':'class','share_sal_hourly':'share_of_salaried_posted_hourly','med_hourly_rate':'median_hourly_rate','pt_share_hourly':'parttime_share_of_hourly_posted','med_annual_posted_only':'median_annual_posted_only'})
t1g=cs[(cs['sample']=='BayArea_unseeded')&(cs.level=='grp')][['cls','n','share_unseeded','n_sal','med','p25','p75','p90']]
E=pd.read_csv(B+'jobs_entry_requirements.csv');Eg=E[(E['sample']=='Bay_unseeded')&(E.level=='grp')]
t3a=Eg[['cls','n','entry_share','ba_share','nodeg_share','yrs_known','yrs_med','yrs_mean','yrs_ge3','share_of_all_postings','share_of_all_entry']]
t3b=Eg[['cls','n_junior','jr_yrs_known','jr_yrs_mean','jr_yrs_med','jr_yrs_ge2','jr_ba','jr_ai_strict_share','n_jr_ai','jr_ai_yrs_mean','jr_noai_yrs_mean','jr_ai_ba','jr_noai_ba']]
Eo=E[(E['sample']=='Bay_unseeded')&(E.level=='occ')][['cls','n','entry_share','ba_share','nodeg_share','yrs_med','n_junior','jr_yrs_mean','jr_ba']]
reg=pd.read_csv(B+'jobs_ai_premium_regressions.csv')
AI=['ai_build','ai_use','ai_brand','ai_strict']
def regtab(specs):
    r=reg[reg.spec.isin(specs)&reg['var'].isin(AI)].copy()
    r['est (se)']=r.apply(lambda x:f"{x.coef:+.3f} ({x.se:.3f}){'*' if x.p<.05 else ''}",axis=1)
    p=r.pivot_table(index='spec',columns='var',values='est (se)',aggfunc='first');n=r.groupby('spec').n.first()
    p=p.reindex(specs);p['n']=n.reindex(specs).values;return p[[c for c in AI if c in p.columns]+['n']].reset_index()
S1=['Bay|all|no FE no controls','Bay|all|occ FE only','Bay|all|occ+city FE|ai_build/use/brand','Bay|all|occ+city+COMPANY FE (within-firm)','Bay|all, unseeded only|occ+city FE','Bay|all, annual-posted only|occ+city FE','CA|all|occ+city FE|ai_build/use/brand']
S2=['Bay|within AI_POSITIONED|occ+city FE','Bay|within AI_POSITIONED|occ+city+COMPANY FE','Bay|within EXPOSED|occ+city FE','Bay|within EXPOSED|occ+city+COMPANY FE','Bay|within EXPOSED, unseeded only|occ+city FE','Bay|within EXPOSED, annual-posted only|occ+city FE','Bay|within EXPOSED, firms <30% AI_POSITIONED postings|occ+city FE','Bay|within EXPOSED, firms >=30% AI_POSITIONED postings|occ+city FE','Bay|within FRONTLINE_SERVICE|occ+city FE','Bay|within occ=CLERICAL_ADMIN|city FE','Bay|within occ=CUSTOMER_SUPPORT|city FE','Bay|within occ=PROF_EXPOSED|city FE','Bay|within occ=SOFTWARE_ENG|city FE','Bay|within occ=AI_PRODUCER|city FE','CA|within EXPOSED|occ+city FE','CA|within EXPOSED|occ+city+COMPANY FE']
tr=pd.read_csv(B+'jobs_transparency.csv')
t5a=tr[tr.dim=='grp'][['key','n','omit_rate','n_sal','width_med','width_p90','share_width_ge2','share_width_eq1']]
t5b=tr[tr.dim.isin(['size_proxy_company_reviews'])][['key','n','omit_rate','width_med','share_width_ge2']]
t5c=tr[tr.dim=='county'][['key','n','omit_rate','width_med']]
t5d=tr[(tr.dim=='occ')][['key','n','omit_rate','width_med','width_p90']]
emp=tr[tr.dim=='EMPLOYER']
t5e=emp[emp.n>=30].sort_values('omit_rate',ascending=False).head(12)[['name','n','omit_rate','n_sal','top_occ']]
t5f=emp[emp.n_sal>=30].sort_values('width_med',ascending=False).head(12)[['name','n','n_sal','omit_rate','width_med','width_p90','share_width_ge2','top_occ']]
ah=pd.read_csv(B+'jobs_ai_hiring.csv')
t6=ah[(ah['sample']=='Bay')&ah.key.isin(['ALL','AI_POSITIONED','EXPOSED','CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED','FRONTLINE_SERVICE','HEALTH_CLINICAL','MANAGEMENT','OTHER'])][['key','n','orig_rate','corrected_rate','n_corrected','n_employers','top_emp_share','corrected_rate_ex_nvidia','med_pay_hiringAI','med_pay_other','senior_hiringAI','senior_other','junior_hiringAI','junior_other']]
emp6=pd.read_csv(B+'jobs_ai_hiring_employers.csv').head(15)
adw=pd.read_csv(B+'jobs_aidatawork.csv')[['group','n','n_companies','top_company_share','n_hourly','share_hourly_posted','med_hourly_rate','med_annualized_2080','n_annual_posted','med_annual_posted','contract','parttime','fulltime','remote','deg_ba','deg_grad','no_deg']]
fo=pd.read_csv(B+'jobs_aitrainer_former_occ.csv')
J=pd.read_csv(B+'jobs_warn_firm_join.csv').sort_values('warn_employees',ascending=False).head(25)[['company','warn_employees','warn_emp_bay','n_notices','n_postings','pos_share','exp_share','fl_share','top_occ','med_pay']]
BT=pd.read_csv(B+'jobs_warn_mix_bootstrap.csv')
C=pd.read_csv(B+'jobs_county_table.csv')
c1=C[['rank_pos_share_unseeded','county','n','n_unseeded','pos_share_unseeded','pos_share_all','exp_share_unseeded','fl_share_unseeded','pos_to_exp_plus_fl_unseeded','med_pay_unseeded','med_pay','med_AI_POSITIONED','med_EXPOSED','med_FRONTLINE_SERVICE','n_sal_EXPOSED','n_sal_AI_POSITIONED','ai_strict_share','remote_share']]
tr_m=pd.read_csv(B+'jobs_monthly_uncensored.csv')
TB=dict(t1=t1,t1h=t1h,t1g=t1g,t3a=t3a,t3b=t3b,Eo=Eo,r1=regtab(S1),r2=regtab(S2),t5a=t5a,t5b=t5b,t5c=t5c,t5d=t5d,t5e=t5e,t5f=t5f,t6=t6,emp6=emp6,adw=adw,fo=fo,J=J,BT=BT,c1=c1,tr=tr_m.reset_index())
M={k:md(v) for k,v in TB.items()}
open(S+'/code/jobs_tables.txt','w').write('\n'.join(f'###{k}\n'+md(v) for k,v in dict(t1=t1,t1h=t1h,t1g=t1g,t3a=t3a,t3b=t3b,Eo=Eo,r1=regtab(S1),r2=regtab(S2),t5a=t5a,t5b=t5b,t5c=t5c,t5d=t5d,t5e=t5e,t5f=t5f,t6=t6,emp6=emp6,adw=adw,fo=fo,J=J,BT=BT,c1=c1).items()))
print('ok')
memo=f'''# Experiment J: Labor-demand recomposition (Indeed postings, Bay Area)

Source: base/indeed_base_v3.parquet (n=134,595 CA postings; 45,850 Bay Area). All numbers below were computed by scripts `code/jobs_*.py`; tables are saved as `base/jobs_*.csv`. AI_POSITIONED = AI_PRODUCER + SOFTWARE_ENG + DATA_ENG_ANALYTICS; EXPOSED = CLERICAL_ADMIN + CUSTOMER_SUPPORT + PROF_EXPOSED.

## Read this first: three data cautions that shape every result

1. **No time trend is claimed.** 55.8% of rows are censored at "30+ days ago" (post_date = crawl - 30d). Uncensored Bay rows dated May-Aug 2026 are the only usable time slice, and that slice is a biased subsample (fast-filling or freshly posted roles). See "Time" section: the apparent rise in AI_POSITIONED share across months is a crawl-seeding artifact. Treat as **uninterpretable**.
2. **Crawl seeding (v3).** 20.2% of Bay rows came from keyword-seeded searches skewed to tech/AI titles. All SHARE/MIX claims use the unseeded subsample (Bay n=36,587) as primary, full sample alongside. Pay-within-class, regression, requirement and transparency results are much less sensitive; `seeded` is a control in the regressions.
3. **Hourly annualization is not innocent.** Salary is annualized at 2080 hours. Bay salaried postings split 23,347 annual-posted / 14,995 hourly-posted; part-time share of hourly-posted is 48% in FRONTLINE_SERVICE, 28% in EXPOSED, 93% in AI_DATA_WORK. Annualizing overstates realized annual pay for the hourly, part-time-heavy classes, which *shrinks* the apparent gap between AI_POSITIONED and the rest. Class pay is therefore reported both ways below. Sample for pay: postings with usable salary (10k-1.5M annualized after trimming; 530 CA rows dropped).

## The headline numbers

1. **Posted pay gap.** Bay median posted pay (annualized) for AI_POSITIONED is **$210,000** vs **$72,800** for EXPOSED: ratio **2.88x** (bootstrap 95% CI 2.81-2.99), gap **$137,200**; vs FRONTLINE_SERVICE ($44,720) 4.70x, gap $165,280. On the unseeded sample the EXPOSED ratio is 3.04x. Holding pay *type* fixed the gap is smaller: annual-posted only, POS $213,000 vs EXPOSED $109,874 = **1.94x**; hourly-posted only, $109,897 vs $52,000 = **2.11x**. So the honest range is roughly 1.9x-2.9x; the pooled 2.9x is partly a pay-type composition effect.
2. **Class explains about half of posted-wage variance.** Between-occupation-class share of var(log sal_mid) in the Bay = **48.6%** (17 classes; 50.0% unseeded; 47.8% for the 13-group collapse); 51.4% is within class. Dropping AI_POSITIONED postings lowers the Bay median posted pay from $125,000 to **$95,000** (unseeded: $119,000 to $90,000); AI_POSITIONED is 21.1% of salaried Bay postings.
3. **Labor demand mix.** AI_POSITIONED = **18.8%** of unseeded Bay postings vs EXPOSED 8.3% (ratio **2.26**; full sample 21.3% vs 7.8%, 2.72). By county, AI_POSITIONED share runs from 27.3% (Santa Clara) and 24.9% (San Francisco) to 0.4% (Napa), 0.9% (Sonoma).
4. **The AI premium is real in cross-section but it is not an AI_POSITIONED-only story and it mostly disappears within firm for "AI use".** With occupation and city FE (cluster by company, n=38,691): ai_build +0.144 (se 0.014), ai_use +0.074 (0.025), ai_brand +0.128 (0.018) log points. Inside EXPOSED occupations the ai_use premium is **+0.126 (0.036)**, larger than inside AI_POSITIONED (+0.014, se 0.022). But adding company FE, EXPOSED ai_use falls to **+0.029 (0.037), not distinguishable from zero**: AI-using exposed roles are at higher-paying employers, not paid more than that employer's other exposed roles.

**Also notable (contradicts parts of the working hypothesis):** the entry rung in EXPOSED is *not* thinner (23.9% of unseeded Bay exposed postings are entry-level vs 4.2% in AI_POSITIONED); exposed postings are not notably more opaque on pay; and AI-use does not carry a negative premium in exposed roles.

## TEST 1: The prize (Bay Area, posted pay by class)

Annualized (hourly x 2080), all Bay postings; share_with_salary = usable salary.

{M['t1']}
Same classes in posted-hourly terms (hourly-posted subset only) and annual-posted-only medians:

{M['t1h']}
Collapsed groups, unseeded Bay sample (for mix-sensitive comparison):

{M['t1g']}
Notes. AI_DATA_WORK's $156,000 "median" is an artifact (see Test 4): do not use the P/AI_DATA_WORK ratio (1.35x, gap $54,000) as a finding. California contrast: POS $194,400 vs EXPOSED $57,902 (3.36x), FRONTLINE $42,640; CA overall median $78,000 and $70,000 without AI_POSITIONED. The variance decomposition uses log(sal_mid) of salaried postings; "occupation x city" cells explain 57.7% but that is an upper bound inflated by small cells.

## TEST 2: The AI premium, properly identified

OLS on log(sal_mid), controls: seeded, senior, junior, fulltime, contract, remote, deg_ba, yrs_min (0 if missing + missing dummy), log desc_len; occupation-class (17) and city FE (cities with <30 salaried postings pooled); SEs clustered by company_norm; * = p<0.05. Coefficients are log points (0.10 = about 10.5%). **This is a cross-sectional association with selection on unobservables, not a causal estimate.**

All Bay postings (and CA):

{M['r1']}
Where does it sit (Bay unless labelled):

{M['r2']}
Reading:
- **AI premium is not an AI_POSITIONED phenomenon.** Within AI_POSITIONED only ai_build pays (+0.078); ai_use (+0.014) and ai_brand (+0.008) are ~0, and with company FE ai_use is slightly negative (-0.016, se 0.009). Within EXPOSED all three are positive and larger (build +0.199, use +0.127, brand +0.214), also within clerical (ai_use +0.293, se 0.055) and PROF_EXPOSED (+0.088, se 0.044), but ~0 in CUSTOMER_SUPPORT (+0.049, se 0.062).
- **Is AI fluency a wage-sorting device for clerical/support?** Between firms, yes: exposed postings that ask for AI use sit at higher-paying employers (and tech-intensive firms; only 220 of 2,920 salaried exposed postings, 158 firms, mention AI use; 113 of those are at firms >=30% AI_POSITIONED). Within firm, no: ai_use +0.029 (se 0.037) and, for CA, -0.006 (0.027). The **negative-premium hypothesis (absorbing AI tools unpaid) is not supported**: the sign is positive between firms and zero within firm; the within-firm zero is compatible with "asked to use AI, not paid more for it" but cannot distinguish it from no effect. ai_build and ai_brand keep a within-firm exposed premium (+0.140 se 0.068; +0.088 se 0.043), and the exposed premium is larger at low-tech firms (<30% AI_POSITIONED): ai_use +0.117 (0.049).
- Robust to unseeded-only and annual-posted-only samples; the all-Bay ai_use coefficient falls to +0.039 (p=0.10) on annual-posted-only.
- Fragile: exposed ai_use rests on 220 postings; within-firm estimates identified only from multi-posting firms.

## TEST 3: The entry rung (Bay, unseeded sample for shares)

"Entry-level" = junior flag. years known = share of postings with a parsed years-of-experience figure (low for frontline, so yrs stats there are selected). Caveat: yrs_min picks up any "N years" mention, so junior-flagged roles with yrs_min>=2 may reflect other sentences.

{M['t3a']}
Within entry-level postings, and AI vs no-AI entry roles:

{M['t3b']}
By detailed class:

{M['Eo']}
Findings.
- **Bottom rung of exposed occupations is not thinner: it is thicker.** Entry-level share: EXPOSED 23.9% (CLERICAL 36.3%, CUSTOMER_SUPPORT 19.3%, PROF_EXPOSED 13.6%) vs FRONTLINE 18.4%, HEALTH 19.3%, SKILLED_TRADE 8.1%, AI_POSITIONED 4.2%. EXPOSED holds 16.3% of all entry postings but 8.3% of all postings. This is a stock of posted roles, not a change over time; it cannot show hollowing-out.
- **Experience floor** among entry-flagged roles: EXPOSED mean 3.3 yrs (73% >=2 yrs; BA required in 30.5%) vs FRONTLINE 2.2 (34%; 5.8%) vs AI_POSITIONED 4.4 (82%; 39.5%). The exposed entry floor is above frontline and below AI_POSITIONED; PROF_EXPOSED entry roles require BA in 65%.
- **AI-mentioning entry roles have a higher floor**: Bay (unseeded) junior roles: mean yrs_min 4.09 (AI, n=435) vs 3.23 (no AI); BA 42.3% vs 23.1%. In EXPOSED junior roles: AI 4.04 vs 3.27 (n_ai=45; all-Bay regression among exposed junior roles with years known, ai_use +1.11 yrs, se 0.48, n=305; all classes +0.40, se 0.28, n.s.). Small n in exposed; suggestive only. Only 6.2% of exposed entry roles mention AI vs 58.1% in AI_POSITIONED entry roles.

## TEST 4: AI_DATA_WORK (the "new contract underclass")

**This class is one platform.** Bay n=145 postings, 125 (86%) from DataAnnotation; statewide 447 postings, 419 (94%) DataAnnotation. It is not a market segment, and no market-wide median should be quoted.

{M['adw']}
- **Pay in hourly terms only.** DataAnnotation posts $50-$100 an hour (91 of 125 Bay postings carry the identical range, so the "median $75/hr" is the midpoint of a posted range, not an observed rate). 100% of DataAnnotation Bay postings are contract and part-time, 85% remote. The annualized figure ($156,000 = $75 x 2080) is **invalid**: hours are not guaranteed. Annual earnings are indeterminate. (Pure arithmetic, not an estimate: at 1,040 hours it would be $78,000.) The Bay non-DataAnnotation hourly postings (n=9) have median $30/hr.
- **Contrast.** The CA postings that quoted an annual figure for this class include a contract "AI Training Specialist (Data Annotation)" at $20,800-$41,600 (Remote Talent Cloud, non-Bay), alongside salaried human-data jobs at OpenAI/Anthropic/Apple ($145k-$385k): the class label mixes gig and elite roles.
- **vs AI_PRODUCER and FRONTLINE**: AI_PRODUCER posts annual salary (96% annual-posted, median $215,950; its 127 hourly-posted median $60/hr). FRONTLINE median $21/hr, 48% part-time. Posted rate is in tech-contractor territory; the contract/part-time/no-guaranteed-hours structure is gig work. It is paid like neither on terms we can verify.
- **Geography.** Bay AI_DATA_WORK by county: Santa Clara 43, San Francisco 29, Alameda 28, Contra Costa 25, San Mateo 13, Napa 4, Sonoma 2, Solano 1; cities are spread across many small places ("Remote in Richmond/Pleasanton/San Ramon"). 74.5% of Bay postings are remote; the posting location is nominal for a remote platform, so the Bay may be capturing little of this employment.
- **Titling pattern: whose occupations are being recruited to train AI?** DataAnnotation titles take the form "<former occupation> - AI Trainer". Of {int(fo[(fo['sample']=='CA')&(fo.level=='top')].n.sum())} CA such titles ({int(fo[(fo['sample']=='Bay')&(fo.level=='top')].n.sum())} Bay), prefix mapped through the occupation taxonomy (+ hand-assigned buckets for 124 unmatched prefixes):

{M['fo']}
  In California: EXPOSED-type former occupations (clerical, support, PROF_EXPOSED incl. accountants/bookkeepers/proofreaders/copywriters, + analyst-like roles) = **85 of 417 (20%)**; taxonomy-only EXPOSED = 64 (15%). AI_POSITIONED-type (software, ML, data) = **191 (46%)**, taxonomy-only 159 (38%). Quantitative/statistical (23, 6%), other engineering, science, teaching etc. the rest. Bay: 26 of 125 exposed-type (21%), 60 AI_POSITIONED-type (48%). **The solicited occupations skew technical, not exposed.** The claim "exposed professionals are being recruited to train their own replacements" is supported for a fifth of titles (accountants, bookkeepers, AR/AP, proofreaders, copywriters, bank clerks) but not as the dominant pattern.

## TEST 5: Pay transparency

Omission = no usable posted salary in the structured field (so includes parse failures; a different definition from "violates SB 1162"). Range width = sal_hi/sal_lo among salaried. Size proxy = Indeed `company_reviews` count (crude; "no reviews listed" is 25% of postings and mixes small firms with missing profiles). Employer minimum: 30 postings (30 salaried for width).

By class group (Bay):

{M['t5a']}
By detailed class:

{M['t5d']}
By company-size proxy:

{M['t5b']}
By county:

{M['t5c']}
Highest omission, employers with >=30 Bay postings:

{M['t5e']}
Widest posted ranges, employers with >=30 salaried Bay postings:

{M['t5f']}
Findings.
- **Overall Bay omission is 15.6%** (unseeded 16.9%). **Negative result:** EXPOSED omit at 18.7% vs AI_POSITIONED 16.5%, FRONTLINE 12.5%, SALES_BIZ 21.9%; in a cluster-robust linear probability model (class, county, size, seeded, remote, contract, part-time) the EXPOSED coefficient vs OTHER is -0.008 (se 0.018), i.e. no excess opacity for exposed work. (CLERICAL_ADMIN alone is 23.1%, the highest of the exposed classes.) Saved in `jobs_transparency_lpm.csv`.
- **Opacity falls on small/unprofiled employers, not on a class:** 28.5% omission with no reviews listed vs 8.2% at firms with 2,000+ reviews. A few large employers omit almost everything: AMD 99.5% of 199 postings, Costco 97% of 202, UCSF 89% of 189, Oracle 97% of 35.
- **Wide ranges are a tech/consulting/gig pattern.** Median width 1.45 for AI_POSITIONED sub-classes vs 1.08 for FRONTLINE; 12.7% of AI_POSITIONED postings have hi/lo >= 2 vs 2.0% FRONTLINE. Accenture (median 3.2x, 89% of 267 postings >= 2x), PwC (2.3x, 100% >=2x), Wipro, Tesla (2.1x, 449 postings), ByteDance/TikTok, HPE. DataAnnotation posts 2.0x on everything. Formal compliance with limited information: a 2-3x range cannot be a pay decision.

## TEST 6: AI as gatekeeper (ai_hiring)

**The flag as built is noisy; corrected rates are lower.** I extracted the regex match context for all 1,977 ai_hiring postings in the file (1,570 Bay) from the source text. A random hand-read of 40 Bay matches found 32 genuine employer disclosures (80%); the 8 false positives were candidate-side rules ("the use of AI or recording tools during live interviews is not permitted", Adobe 391 postings; Sofar). A full template audit of all 120 employers' boilerplate (grouping matches by company, then hand-classifying each template; script `jobs_t6b.py`, `jobs_t6c.py`) gives **posting-weighted precision 65% overall (1,291 of 1,977) and 64% in the Bay (1,008 of 1,570)**. The 40-posting hand sample (80%, wide CI around +/-13 pts) is higher because NVIDIA's genuine boilerplate is 35% of all matches. False positives: DICK'S, Marvell, Air Apps, CBRE, Foot Locker, Savers, Micron, Everlaw, Pfizer, Carter's ("does not use AI"), etc. All of these are interview/application conduct rules. Residual error remains in the "corrected" flag (regex-based plus hand-resolved edge cases), and **recall is unknown** (the regex is narrow; many disclosures phrased differently are missed, so rates are floors).

Corrected disclosure (Bay): rate = share of postings with a genuine employer AI-in-hiring disclosure.

{M['t6']}
Top Bay employers (corrected flag):

{M['emp6']}
Findings.
- Corrected Bay rate **2.2%** (orig. 3.4%). **Hypothesis not supported by these data:** disclosure is concentrated in AI_POSITIONED (4.7%) and management (2.6%); EXPOSED 0.6%, FRONTLINE 0.7%, CLERICAL 0.1%. Only 51 employers (Bay) account for all disclosures, and **NVIDIA alone is 68% of Bay corrected matches** (rate excluding NVIDIA 0.7% overall). These are rates of *disclosure*, which depends on state disclosure norms and big-company legal boilerplate, not on how many applicants are actually screened by algorithm. High-volume applicant pools may be screened without disclosure.
- Disclosing postings are senior and high-paid: median posted pay $219,750 vs $122,500 for other postings; senior 71% vs 39%; entry-level 2.4% vs 11.7%. That mostly reflects who discloses (NVIDIA, eBay, Block, Pinterest), not who is screened. Compass Group affiliates (Epicurean Group 15, Levy 7, FISD 6 Bay postings) disclose an AI recruiting assistant, which is most of the frontline disclosures.

## TEST 7: Firm-level recomposition (postings x WARN)

Join: exact match on company_norm; WARN file = warn_ca.csv (5,392 notices 2023-04 to 2026-11; 2,741 firms; 1,760 notices in the 9 Bay counties by notice county, 922 firms).

| match definition | % Bay postings matched | Bay posting firms matched | WARN firms with any Bay posting | WARN employees covered |
|---|---|---|---|---|
| any CA WARN | **14.1%** (6,484 / 45,850) | 226 of 11,869 | 226 / 2,741 = 8.2% | 19.8% |
| Bay-county WARN | **12.5%** (5,745) | 170 | 170 / 922 = 18.4% | 37.7% |
| Bay-county WARN since 2025-01 | 5.3% (2,450) | 97 | 97 / 600 = 16.2% | 29.5% |

**Limits (honest).** (a) company_norm is a fuzzy exact key: a parent's WARN may not correspond to the posting entity (Walmart: 16 WARN notices, 37.5% closures, while its 160 Bay postings are 43% AI_POSITIONED, so the notices and the postings plausibly concern different parts of the company; Optum: 3 Bay layoff employees vs 11 Bay postings); subsidiaries match only if the name coincides (LinkedIn has 15 notices but 1 posting under that name). (b) Matching is mostly large employers: only 226 of 11,869 firms and only 18% of Bay-county WARN filers have a posting at all; 108 matched firms have >=5 postings. (c) Postings are 2026; WARN spans 2023-2026, so the layoff and the posting are not simultaneous. (d) Postings are not hires, and WARN employees are counts at a site, not occupations cut. (e) The crawl was seeded toward tech, which inflates AI_POSITIONED in both groups. The matched subset supports a descriptive mix comparison, not a "cutting X while hiring Y" claim for any individual firm.

Mix of postings at matched vs non-matched firms (Bay, unseeded sample; difference in share of postings, WARN minus non-WARN; 95% CI from a firm-cluster bootstrap):

{M['BT']}
- **WARN-filing firms post more AI_POSITIONED roles**: Bay-county WARN firms 31.1% vs 17.1% of unseeded postings (+14.0 pts, CI +4.3 to +20.7); full sample +18.5 pts (CI +9.1 to +26.7). They post fewer EXPOSED (-3.5 pts, CI -5.2 to -1.1) and fewer FRONTLINE (-7.9, CI -12.0 to -1.1) roles. Using any-CA-WARN: +15.2 pts (CI +4.3 to +22.1).
- **But WARN filers are large firms, and large firms are tech-heavy.** Restricting to firms with >=30 Bay postings, WARN firms are 41.5% AI_POSITIONED vs 30.4% (posting-weighted; 13 vs 26 firms with >=100 postings: 44.6% vs 33.0%). Gap shrinks to ~11 pts and rests on 35 matched firms. Dropping the five biggest matched posters (Apple, Google, Tesla, TikTok, Accenture): 27.2% vs 18.6%.
- Median posted pay (salaried): POS roles at WARN firms $214,000 vs $205,000 elsewhere; EXPOSED roles $114,250 vs $70,304 (small n; mostly big-tech support roles).
- **Verdict:** descriptively consistent with recomposition (firms cutting staff are tilted to AI_POSITIONED hiring), but not evidence of within-firm substitution; the pattern may simply be that big tech both files notices and hires engineers. This supports "layoffs and AI-technical hiring coexist" at firms such as Tesla (449 postings, 48% AI_POSITIONED; 2,589 Bay layoff employees), Cisco (166; 45%; 2,668), Intuit (115; 44%; 927), eBay (61; 49%; 951), Salesforce (136; 46%; 677), Apple (866; 43%).

Top matched firms by WARN employees (any CA notice; Bay-county employees beside):

{M['J']}
Glassdoor linkage: `base/glassdoor_company.csv` did **not exist** at the time of writing (checked repeatedly), so the WARN-vs-employee-subrating test was **not run**.

## TEST 8: Geography (Bay Area counties; sorted by AI_POSITIONED share of unseeded postings)

{M['c1']}
Ranking (unseeded AI_POSITIONED share): 1 Santa Clara 27.3%, 2 San Francisco 24.9%, 3 San Mateo 17.5%, 4 Alameda 7.8%, 5 Contra Costa 2.6%, 6 Marin 1.6%, 7 Solano 1.5%, 8 Sonoma 0.9%, 9 Napa 0.4%. Santa Clara, SF and San Mateo are AI-positioned (ratio of AI_POSITIONED to EXPOSED+FRONTLINE 1.77, 1.73, 0.68); every other county is dominated by frontline and exposed demand (Napa: FRONTLINE 38.6%, AI_POSITIONED 0.4%; Sonoma 29.6% frontline; Solano 28.5%; Contra Costa 28.3%). Median posted pay follows: $157,500 (Santa Clara) and $160,000 (SF) vs $49,920 (Napa). EXPOSED median posted pay is $93,600 in San Francisco, $79,140 Santa Clara, $72,800 San Mateo, $68,557 Alameda vs $49,400-57,200 in Napa, Sonoma, Solano, Contra Costa and Marin: even the pay of exposed work is geographic. Small cells: AI_POSITIONED salaried postings are 2-11 in Napa, Sonoma, Solano and Marin, so those pay figures are not reliable; shares are. Full per-class medians in `base/jobs_county_class_pay.csv` and class-mix columns in `jobs_county_table.csv`.

## Time (uncensored rows only; labelled ~May-Aug 2026; DO NOT READ AS A TREND)

Bay rows with censored==False and post_date in Feb-Sep 2026 (n=17,382; 98% fall in May-Aug; Feb/Apr/Sep cells have 11-234 postings). Uncensored postings are a biased subsample of fast-filling/fresh roles, and the "month" of a posting is nearly collinear with the crawl batch.

{M['tr']}
Composition check: AI_POSITIONED share rises from 20.6% (May) to 31.1% (Aug) on the full uncensored sample, but the **seeded share of those rows climbs from 5% (May) to 82% (Aug)**; on unseeded rows only, AI_POSITIONED falls (25.2% June, 20.1% July, 11.0% Aug, n=762) and EXPOSED rises (4.7% to 10.6%). The two readings point in opposite directions; the trend is a crawl artifact. Uncensored ai_strict share is 22% vs 19.7% for censored (uncensored also has 88.6% salary posted vs 81.5%). **Null/uninterpretable trend; cross-section is the finding.**

## What is solid, what is fragile

Solid: pay gap by class and its approximate size (1.9x-2.9x depending on how pay type is handled); class explains about half of variance; county gradient in AI_POSITIONED share (unseeded and full agree); entry-level thickness of exposed occupations; no excess omission in exposed classes; DataAnnotation dominance of AI_DATA_WORK.
Fragile: ai_use premium inside exposed (220 postings; zero within firm); AI vs non-AI entry floor in exposed (n=45); WARN comparison (mostly big firms, 3-14% of postings); ai_hiring (precision 64-65%, recall unknown, 68% NVIDIA).
Not run: Glassdoor sub-rating test (file absent).
'''
open(O+'jobs_findings.md','w').write(memo);print(len(memo))
