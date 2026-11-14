import sys;sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
from jobs_lib import *
pd.set_option('display.width',250);pd.set_option('display.max_columns',40)
d=load();c=pd.read_csv(B+'jobs_aihiring_classified.csv')
TPCO={'Coinbase','Miovision','Carrier','Loopio Inc.','Mission','LILT'}
FPCO={'Paraform','Metaview','Listen Labs','Anthropic','Accenture'}
c['ok']=((c.cls=='TP')|c.company.isin(TPCO))&~c.company.isin(FPCO)
d['ai_hiring_ok']=d.jobid.isin(c[c.ok].jobid)
print('orig',d.ai_hiring.sum(),'corrected',d.ai_hiring_ok.sum(),'precision',d.ai_hiring_ok.sum()/d.ai_hiring.sum(),'bay',d[d.bay].ai_hiring.sum(),d[d.bay].ai_hiring_ok.sum())
print('employers w/ corrected hits',d[d.ai_hiring_ok].company_norm.nunique(),'top',d[d.ai_hiring_ok].company.value_counts().head(10).to_dict())
rows=[]
b=d[d.bay]
def blk(x,tag,key):
    for k,g in x.groupby(key):
        s=g[g.sal_ok];p=g[g.ai_hiring_ok];sp=p[p.sal_ok];sn=g[~g.ai_hiring_ok&g.sal_ok]
        rows.append(dict(sample=tag,key=k,n=len(g),orig_rate=g.ai_hiring.mean(),corrected_rate=g.ai_hiring_ok.mean(),n_corrected=len(p),n_orig=int(g.ai_hiring.sum()),
          n_employers=p.company_norm.nunique(),top_emp_share=p.company_norm.value_counts(normalize=True).iloc[0] if len(p) else np.nan,
          corrected_rate_ex_nvidia=g[g.company_norm!='nvidia'].ai_hiring_ok.mean(),
          med_pay_hiringAI=sp.sal_mid.median(),med_pay_other=sn.sal_mid.median(),senior_hiringAI=p.senior.mean(),senior_other=g[~g.ai_hiring_ok].senior.mean(),junior_hiringAI=p.junior.mean(),junior_other=g[~g.ai_hiring_ok].junior.mean(),yrs_hiringAI=p.yrs_min.mean(),yrs_other=g[~g.ai_hiring_ok].yrs_min.mean()))
for tag,x in [('Bay',b),('Bay_unseeded',b[~b.seeded]),('CA',d)]:
    blk(x,tag,'grp');blk(x,tag,'occ');blk(x.assign(a='ALL'),tag,'a')
T=pd.DataFrame(rows);T.to_csv(B+'jobs_ai_hiring.csv',index=False)
print(T[T['sample'].isin(['Bay','Bay_unseeded'])&T.key.isin(['ALL','AI_POSITIONED','EXPOSED','FRONTLINE_SERVICE','CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED','HEALTH_CLINICAL','MANAGEMENT','OTHER'])].round(3).to_string())
# employers Bay
e=b[b.ai_hiring_ok].groupby('company').agg(n=('jobid','size'),med_pay=('sal_mid','median'),top_occ=('grp',lambda z:z.mode().iat[0]),exposed_share=('grp',lambda z:(z=='EXPOSED').mean()),junior=('junior','mean')).sort_values('n',ascending=False)
print(e.head(25).round(3));e.to_csv(B+'jobs_ai_hiring_employers.csv')
# employer-level: share of employers with >=5 bay postings that disclose
print('Bay corrected rate by company size proxy');b2=b.copy();b2['size']=pd.cut(b2.company_reviews.fillna(-1),[-2,-.5,19,199,1999,1e9],labels=['none','1-19','20-199','200-1999','2000+'])
print(b2.groupby('size',observed=True).ai_hiring_ok.agg(['mean','sum','size']))
