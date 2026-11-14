import sys;sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
from jobs_lib import *
import statsmodels.api as sm
d=load()
AI=['ai_build','ai_use','ai_brand']
CT=['seeded','senior','junior','fulltime','contract','remote','deg_ba','yrs_min_f','yrs_missing','ldesc']
def prep(x):
    x=x[x.sal_ok&x.company_norm.notna()&(x.company_norm!='')].copy()
    x['yrs_missing']=x.yrs_min.isna().astype(float);x['yrs_min_f']=x.yrs_min.fillna(0);x['ldesc']=np.log1p(x.desc_len)
    for c in ['seeded','senior','junior','fulltime','contract','remote','deg_ba']+AI+['ai_strict']:x[c]=x[c].astype(float)
    vc=x.city.value_counts();x['city']=x.city.where(x.city.map(vc)>=30,'_small')
    return x
def fit(x,xcols,fe_occ=True,fe_city=True,company_fe=False,label=''):
    X=x[xcols].astype(float).copy()
    if fe_occ and x.occ.nunique()>1: X=X.join(pd.get_dummies(x.occ,prefix='o',drop_first=True,dtype=float))
    if fe_city and x.city.nunique()>1: X=X.join(pd.get_dummies(x.city,prefix='c',drop_first=True,dtype=float))
    X=X.loc[:,X.std()>0]
    y=x.lsal
    if company_fe:
        g=x.company_norm
        y=y-y.groupby(g).transform('mean');X=X-X.groupby(g).transform('mean');X=X.loc[:,X.abs().sum()>1e-9]
    else: X=sm.add_constant(X)
    m=sm.OLS(y,X).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(x.company_norm)[0]})
    rows=[]
    for c in xcols:
        if c in m.params.index: rows.append(dict(spec=label,var=c,coef=m.params[c],se=m.bse[c],p=m.pvalues[c],n=int(m.nobs),n_clusters=x.company_norm.nunique(),r2=m.rsquared))
    return rows
R=[]
b=prep(d[d.bay]);c=prep(d)
for nm,x in [('Bay',b),('CA',c)]:
    R+=fit(x,AI+CT,label=f'{nm}|all|occ+city FE|ai_build/use/brand')
    R+=fit(x,['ai_strict']+CT,label=f'{nm}|all|occ+city FE|ai_strict only')
    R+=fit(x,AI+CT,fe_occ=True,fe_city=False,label=f'{nm}|all|occ FE only')
    R+=fit(x,AI,fe_occ=False,fe_city=False,label=f'{nm}|all|no FE no controls')
    R+=fit(x,AI+CT,company_fe=True,label=f'{nm}|all|occ+city+COMPANY FE (within-firm)')
    for g in ['AI_POSITIONED','EXPOSED','FRONTLINE_SERVICE','OTHER_REST']:
        xs=x[x.grp==g] if g!='OTHER_REST' else x[~x.grp.isin(['AI_POSITIONED','EXPOSED','FRONTLINE_SERVICE'])]
        R+=fit(xs,AI+CT,label=f'{nm}|within {g}|occ+city FE')
    # sub-class within EXPOSED
    for o in EXP+POS:
        R+=fit(x[x.occ==o],AI+CT,fe_occ=False,label=f'{nm}|within occ={o}|city FE')
    # exposed company FE
    R+=fit(x[x.grp=='EXPOSED'],AI+CT,company_fe=True,label=f'{nm}|within EXPOSED|occ+city+COMPANY FE')
    R+=fit(x[x.grp=='AI_POSITIONED'],AI+CT,company_fe=True,label=f'{nm}|within AI_POSITIONED|occ+city+COMPANY FE')
# interaction spec
for nm,x in [('Bay',b)]:
    x=x.copy();cols=[]
    for g,tag in [('AI_POSITIONED','POS'),('EXPOSED','EXP'),('FRONTLINE_SERVICE','FL')]:
        for a in AI:
            x[f'{a}_x_{tag}']=x[a]*(x.grp==g);cols.append(f'{a}_x_{tag}')
    for a in AI: x[f'{a}_x_REST']=x[a]*(~x.grp.isin(['AI_POSITIONED','EXPOSED','FRONTLINE_SERVICE']));cols.append(f'{a}_x_REST')
    R+=fit(x,cols+CT,label='Bay|interacted ai x group|occ+city FE')
res=pd.DataFrame(R);res.to_csv(B+'jobs_ai_premium_regressions.csv',index=False)
pd.set_option('display.width',250);pd.set_option('display.max_rows',500)
t=res[res['var'].isin(AI+['ai_strict'])|res['var'].str.contains('_x_')].copy()
t['coef']=t.coef.round(4);t['se']=t.se.round(4);t['p']=t.p.round(3)
print(t[['spec','var','coef','se','p','n','n_clusters']].to_string())
# prevalence
for g,x in b.groupby('grp'):
    if g in ['AI_POSITIONED','EXPOSED','FRONTLINE_SERVICE']: print(g,len(x),x[AI+['ai_strict']].mean().round(3).to_dict(), 'n_ai_use',int(x.ai_use.sum()))
print(res[res.spec=='Bay|all|occ+city FE|ai_build/use/brand'][['var','coef','se']])
