import sys,re,pandas as pd,numpy as np
from scipy import stats
import statsmodels.api as sm
S=sys.argv[1]; sys.path.insert(0,S+'/code')
from voice_gd_text import *
ca=pd.read_pickle(S+'/base/_gd_ca_text.pkl')
out=open(S+'/out/_gd_numbers.txt','w')
def P(*a):
    print(*a); print(*a,file=out)
R7=['rating_overall','rating_compensation_benefits','rating_career_opportunities','rating_senior_leadership','rating_work_life','rating_culture_values','rating_diversity_inclusion']
for _c in R7[1:]: ca.loc[ca[_c]==0,_c]=np.nan
P('zero sub-ratings treated as missing: share by column',{c:round(float((pd.read_pickle(S+'/base/_gd_ca_text.pkl')[c]==0).mean()),3) for c in R7[1:]})
cons=ca.review_cons.fillna('')
ca['has_cons']=cons.str.len()>0
for nm,rx in [('t_layoff',LAYOFF),('t_staffing',STAFFING),('t_workload',WORKLOAD_ANY),('t_ai_mention',AI_MENTION),('t_ai_threat',AI_THREAT),('t_offshore_broad',OFFSHORE),('t_offshore',OFFSHORE_DISPLACE)]:
    ca[nm]=cons.str.contains(rx)
ca['t_layoff_and_staffing']=ca.t_layoff&(ca.t_staffing|ca.t_workload)
ca['cons_len']=cons.str.len()
GR={'AI_POSITIONED':['AI_PRODUCER','SOFTWARE_ENG','DATA_ENG_ANALYTICS'],'EXPOSED':['CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED'],'IN_PERSON':['FRONTLINE_SERVICE','SKILLED_TRADE','HEALTH_CLINICAL','EDUCATION']}
def grp(c):
    for k,v in GR.items():
        if c in v: return k
    return 'OTHER_GROUPS'
ca['occ_group']=ca.occ_class.map(grp)
# ---- save parquet (no free text)
keepc=['review_id','rating_date','month','company_name','company_norm','employee_location','city','bay_area','employee_job_title','occ_class','occ_group','occ_rule','employee_status','employee_type','status_current','tenure_code']+R7+['has_cons','cons_len','t_layoff','t_staffing','t_workload','t_ai_mention','t_ai_threat','t_offshore','t_offshore_broad','t_layoff_and_staffing','overview_id','glassdoor_employer_id']
ca[keepc].to_parquet(S+'/base/glassdoor_ca.parquet',index=False)
# ---- profile
P('ALL ROWS 175138; CA-filtered (employee_location endswith ", CA"):',len(ca),'; unique companies',ca.company_name.nunique(),'; unique company_norm',ca.company_norm.nunique())
P('bay area reviews',int(ca.bay_area.sum()),'share',round(ca.bay_area.mean(),4))
P('has cons text',int(ca.has_cons.sum()))
P('months range',ca.month.min(),ca.month.max()); P(ca.month.value_counts().sort_index().to_string())
P('top companies'); P(ca.company_name.value_counts().head(20).to_string())
P('top titles'); P(ca.employee_job_title.value_counts().head(15).to_string())
P('class counts'); vc=ca.occ_class.value_counts(); P(pd.DataFrame({'n':vc,'share':(vc/len(ca)).round(4)}).to_string())
cov=(~ca.occ_class.isin(['OTHER','MISSING_TITLE'])).mean(); P('coverage non-OTHER non-missing',round(cov,4),'| missing/anon title',int((ca.occ_class=="MISSING_TITLE").sum()),'| OTHER',int((ca.occ_class=="OTHER").sum()))
P('top OTHER titles'); P(ca[ca.occ_class=='OTHER'].employee_job_title.value_counts().head(15).to_string())
P('group counts'); P(ca.occ_group.value_counts().to_string())
# ---- class ratings table
rows=[]
def summarize(d,label,kind):
    r={'label':label,'kind':kind,'n':len(d)}
    for c in R7:
        r['mean_'+c.replace('rating_','')]=d[c].mean(); r['sd_'+c.replace('rating_','')]=d[c].std(); r['n_'+c.replace('rating_','')]=int(d[c].notna().sum())
    r['mean_career_minus_overall']=(d.rating_career_opportunities-d.rating_overall).mean(); r['mean_comp_minus_overall']=(d.rating_compensation_benefits-d.rating_overall).mean()
    for t in ['t_layoff','t_staffing','t_workload','t_ai_mention','t_ai_threat','t_offshore']:
        dd=d[d.has_cons]; r['rate_'+t]=dd[t].mean() if len(dd) else np.nan
    r['n_with_cons']=int(d.has_cons.sum())
    return r
for c,d in ca.groupby('occ_class'): rows.append(summarize(d,c,'class'))
for c,d in ca.groupby('occ_group'): rows.append(summarize(d,c,'group'))
rows.append(summarize(ca,'ALL_CA','all'))
cr=pd.DataFrame(rows); cr.to_csv(S+'/base/glassdoor_class_ratings.csv',index=False)
pd.set_option('display.width',250)
P(cr[['label','n']+['mean_'+c.replace('rating_','') for c in R7]].round(3).to_string())
# ---- AIP vs EXP comparison
sub=ca[ca.occ_group.isin(['AI_POSITIONED','EXPOSED'])].copy(); sub['exposed']=(sub.occ_group=='EXPOSED').astype(int)
def cohend(a,b):
    a=a.dropna(); b=b.dropna(); n1,n2=len(a),len(b); sp=np.sqrt(((n1-1)*a.var()+(n2-1)*b.var())/(n1+n2-2)); d=(a.mean()-b.mean())/sp
    se=np.sqrt((n1+n2)/(n1*n2)+d*d/(2*(n1+n2))); return d,d-1.96*se,d+1.96*se
def fe_ols(d,y,xcols,fe='company_norm'):
    d=d.dropna(subset=[y]+xcols).copy()
    # drop singleton FE groups
    g=d.groupby(fe)[y].transform('size'); d=d[g>1]
    X=d[xcols].astype(float); Y=d[y].astype(float)
    Xd=X-X.groupby(d[fe]).transform('mean'); Yd=Y-Y.groupby(d[fe]).transform('mean')
    m=sm.OLS(Yd.values,Xd.values).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(d[fe])[0]})
    return m,xcols,len(d),d[fe].nunique()
# controls
sub['cur']=sub.status_current.astype(float); sub['bay']=sub.bay_area.astype(float)
tdum=pd.get_dummies(sub.tenure_code.fillna(-1).astype(int),prefix='ten',drop_first=True).astype(float); mdum=pd.get_dummies(sub.month,prefix='m',drop_first=True).astype(float)
sub=pd.concat([sub,tdum,mdum],axis=1); ctrl=['cur','bay']+list(tdum.columns)+list(mdum.columns)
sub['career_gap']=sub.rating_career_opportunities-sub.rating_overall; sub['comp_gap']=sub.rating_compensation_benefits-sub.rating_overall
res=[]
for y in R7+['career_gap','comp_gap']:
    a=sub[sub.exposed==0][y]; b=sub[sub.exposed==1][y]
    d,lo,hi=cohend(a,b)  # positive = AI-positioned higher
    t=stats.ttest_ind(a.dropna(),b.dropna(),equal_var=False); mw=stats.mannwhitneyu(a.dropna(),b.dropna())
    m,xc,nobs,ng=fe_ols(sub,y,['exposed']+ctrl)
    m2,xc2,nobs2,ng2=fe_ols(sub,y,['exposed']+ctrl,fe='company_norm') if False else (None,None,None,None)
    # OLS without company FE (controls only)
    d2=sub.dropna(subset=[y]); X=sm.add_constant(d2[['exposed']+ctrl].astype(float)); mo=sm.OLS(d2[y].astype(float),X).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(d2.company_norm)[0]})
    res.append({'outcome':y,'mean_AI_POSITIONED':a.mean(),'mean_EXPOSED':b.mean(),'diff_AIP_minus_EXP':a.mean()-b.mean(),'cohens_d':d,'d_ci_lo':lo,'d_ci_hi':hi,'welch_p':t.pvalue,'mannwhitney_p':mw.pvalue,'n_AIP':int(a.notna().sum()),'n_EXP':int(b.notna().sum()),
      'adj_coef_exposed_controls':mo.params['exposed'],'adj_p_controls':mo.pvalues['exposed'],'companyFE_coef_exposed':m.params[0],'companyFE_se':m.bse[0],'companyFE_p':m.pvalues[0],'companyFE_nobs':nobs,'companyFE_ncompanies':ng})
rs=pd.DataFrame(res); rs.to_csv(S+'/base/glassdoor_aip_vs_exposed.csv',index=False)
P(rs.round(4).to_string())
# pairwise class vs ALL others d for each class on career & comp & overall
pw=[]
for c in ca.occ_class.unique():
    a=ca[ca.occ_class==c]; b=ca[ca.occ_class!=c]
    for y in ['rating_overall','rating_compensation_benefits','rating_career_opportunities']:
        d,lo,hi=cohend(a[y],b[y]); pw.append({'class':c,'outcome':y,'n':len(a),'diff_vs_rest':a[y].mean()-b[y].mean(),'d':d,'lo':lo,'hi':hi})
pw=pd.DataFrame(pw); pw.to_csv(S+'/base/glassdoor_class_vs_rest.csv',index=False)
P(pw.pivot(index='class',columns='outcome',values='d').round(3).to_string())
# ---- trends
ca['t']=(pd.to_datetime(ca.month+'-01')-pd.Timestamp('2025-01-01')).dt.days/30.4
ca['q']=pd.PeriodIndex(pd.to_datetime(ca.month+'-01'),freq='Q').astype(str)
tr=ca[ca.occ_group.isin(['AI_POSITIONED','EXPOSED','IN_PERSON'])].groupby(['q','occ_group']).agg(n=('review_id','size'),**{c.replace('rating_',''):(c,'mean') for c in R7}).reset_index()
tr['small_cell']=tr.n<300
tr.to_csv(S+'/base/glassdoor_class_trend_quarterly.csv',index=False)
P(tr.round(3).to_string())
trm=ca[ca.occ_group.isin(['AI_POSITIONED','EXPOSED'])].groupby(['month','occ_group']).agg(n=('review_id','size'),career=('rating_career_opportunities','mean'),comp=('rating_compensation_benefits','mean'),overall=('rating_overall','mean')).reset_index(); trm['small_cell']=trm.n<100
trm.to_csv(S+'/base/glassdoor_class_trend_monthly.csv',index=False); P('monthly cells <100:',int(trm.small_cell.sum()),'of',len(trm),'; min n',trm.n.min())
# slope interaction models (company FE, clustered)
sub2=sub.copy(); sub2['t']=(pd.to_datetime(sub2.month+'-01')-pd.Timestamp('2025-01-01')).dt.days/30.4; sub2['exp_t']=sub2.exposed*sub2.t
ctrl2=['cur','bay']+list(tdum.columns)
for y in ['rating_overall','rating_compensation_benefits','rating_career_opportunities','career_gap','comp_gap','rating_work_life','rating_senior_leadership']:
    m,xc,nobs,ng=fe_ols(sub2,y,['exposed','t','exp_t']+ctrl2)
    P(f'TREND {y}: slope/month AIP={m.params[1]:.4f} (p={m.pvalues[1]:.3f}); extra slope EXPOSED={m.params[2]:.4f} se={m.bse[2]:.4f} p={m.pvalues[2]:.3f} (n={nobs}, companies={ng})')
# half-year means with CI
ca['half']=np.where(ca.month<'2025-07','2025H1',np.where(ca.month<'2026-01','2025H2',np.where(ca.month<'2026-07','2026H1','2026H2(Jul-Nov)')))
hh=ca[ca.occ_group.isin(['AI_POSITIONED','EXPOSED'])].groupby(['half','occ_group']).agg(n=('review_id','size'),overall=('rating_overall','mean'),career=('rating_career_opportunities','mean'),comp=('rating_compensation_benefits','mean'),ccgap=('rating_career_opportunities','mean')).reset_index()
P(hh.round(3).to_string())
# ---- text analysis by class
cc=ca[ca.has_cons]
rows=[]
for c,d in list(cc.groupby('occ_class'))+list(cc.groupby('occ_group')):
    r={'label':c,'n_cons':len(d)}
    for t in ['t_layoff','t_staffing','t_workload','t_ai_mention','t_ai_threat','t_offshore','t_layoff_and_staffing']:
        k=int(d[t].sum()); n=len(d); p=k/n; se=1.96*np.sqrt(p*(1-p)/n); r[t]=p; r[t+'_ci']=se
    rows.append(r)
tx=pd.DataFrame(rows); tx.to_csv(S+'/base/glassdoor_text_rates_by_class.csv',index=False); P(tx.round(4).to_string())
# regression: text flag ~ exposed within AIP/EXP and also vs IN_PERSON, company FE cluster
sub3=cc[cc.occ_group.isin(['AI_POSITIONED','EXPOSED','IN_PERSON'])].copy()
sub3['exposed']=(sub3.occ_group=='EXPOSED').astype(float); sub3['inperson']=(sub3.occ_group=='IN_PERSON').astype(float); sub3['cur']=sub3.status_current.astype(float); sub3['bay']=sub3.bay_area.astype(float)
for t in ['t_layoff','t_staffing','t_workload','t_ai_mention','t_ai_threat','t_offshore','t_layoff_and_staffing']:
    sub3[t+'_f']=sub3[t].astype(float)
    m,xc,nobs,ng=fe_ols(sub3,t+'_f',['exposed','inperson','cur','bay'])
    P(f'TEXT LPM company-FE {t}: EXPOSED vs AIP: {m.params[0]*100:+.2f}pp (se {m.bse[0]*100:.2f}, p={m.pvalues[0]:.3g}); IN_PERSON vs AIP: {m.params[1]*100:+.2f}pp (p={m.pvalues[1]:.3g}); n={nobs}, companies={ng}')
# conditional on layoff mention: share also staffing/workload by group
for g,d in cc[cc.t_layoff].groupby('occ_group'):
    P('among layoff-mentioning cons:',g,'n=',len(d),'also staffing',round(d.t_staffing.mean(),4),'also workload',round(d.t_workload.mean(),4),'also staffing|workload',round((d.t_staffing|d.t_workload).mean(),4))
for g,d in cc[~cc.t_layoff].groupby('occ_group'):
    P('among NON-layoff cons:',g,'n=',len(d),'staffing',round(d.t_staffing.mean(),4),'workload',round(d.t_workload.mean(),4))
# time: text rates by half and group
tt=cc[cc.occ_group.isin(['AI_POSITIONED','EXPOSED','IN_PERSON'])].groupby(['half','occ_group']).agg(n=('review_id','size'),layoff=('t_layoff','mean'),staffing=('t_staffing','mean'),workload=('t_workload','mean'),ai_mention=('t_ai_mention','mean'),ai_threat=('t_ai_threat','mean'),offshore=('t_offshore','mean')).reset_index()
tt.to_csv(S+'/base/glassdoor_text_rates_by_half.csv',index=False); P(tt.round(4).to_string())
# bay area only subset
bay=cc[cc.bay_area]
P('BAY AREA subset n',len(bay)); P(bay.groupby('occ_group').agg(n=('review_id','size'),layoff=('t_layoff','mean'),staffing=('t_staffing','mean'),ai_mention=('t_ai_mention','mean'),ai_threat=('t_ai_threat','mean'),career=('rating_career_opportunities','mean'),comp=('rating_compensation_benefits','mean'),overall=('rating_overall','mean')).round(3).to_string())
# ---- company table
g=ca.groupby('company_norm')
comp=pd.DataFrame({'company_name':g.company_name.agg(lambda s:s.value_counts().index[0]),'n_reviews':g.size(),'n_names_merged':g.company_name.nunique(),'n_bay_area':g.bay_area.sum(),'n_with_cons':g.has_cons.sum(),'first_month':g.month.min(),'last_month':g.month.max()})
for c in R7: comp['mean_'+c.replace('rating_','')]=g[c].mean()
comp['share_ai_positioned']=g.occ_group.apply(lambda s:(s=='AI_POSITIONED').mean()); comp['share_exposed']=g.occ_group.apply(lambda s:(s=='EXPOSED').mean()); comp['share_in_person']=g.occ_group.apply(lambda s:(s=='IN_PERSON').mean())
cg=ca[ca.has_cons].groupby('company_norm')
for t in ['t_layoff','t_staffing','t_workload','t_ai_mention','t_ai_threat','t_offshore']: comp['rate_'+t[2:]]=cg[t].mean()
comp['n_reviews_2026']=ca[ca.month>='2026-01'].groupby('company_norm').size(); comp['n_reviews_2026']=comp.n_reviews_2026.fillna(0).astype(int)
comp=comp.reset_index().sort_values('n_reviews',ascending=False); comp.to_csv(S+'/base/glassdoor_company.csv',index=False)
P('company table rows',len(comp),'companies with >=10 reviews',int((comp.n_reviews>=10).sum()),'>=30',int((comp.n_reviews>=30).sum()),'names merged >1:',int((comp.n_names_merged>1).sum()))
P(comp.head(10)[['company_norm','company_name','n_reviews','mean_overall','mean_career_opportunities']].round(3).to_string())
