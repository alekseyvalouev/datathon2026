"""Test (c): wages by occ_class x race, within-class gaps, AIPOS vs EXPOSED, regression gap test. Usage: pums_wages.py base_dir"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pums_lib as L
B=sys.argv[1]; MIN_N=50
d=pd.read_parquet(f'{B}/pums_bay.parquet')
n0=len(d)
ws = d[d.wage_salary_worker & d.hourly_wage.notna()]
ws = ws[(ws.hourly_wage>=5)&(ws.hourly_wage<=500)].reset_index(drop=True)
print('employed',n0,'wage/salary w/ valid hourly in [5,500]:',len(ws), 'dropped for hourly outside [5,500]:', int(((d.wage_salary_worker & d.hourly_wage.notna()) & ((d.hourly_wage<5)|(d.hourly_wage>500))).sum()))
POOLS = {c:[c] for c in L.CLASSES}
POOLS.update({'EXPOSED':L.EXPOSED,'AIPOS':L.AIPOS,'AIPS2':['AI_PRODUCER','SOFTWARE_ENG'],'ALL':L.CLASSES})
RACES=L.RACES+['All']
cls=ws.occ_class.values; rce=ws.race_eth.values
cell_idx={}
for pn,members in POOLS.items():
    pm=np.isin(cls,members)
    for r in RACES:
        m=pm&(np.ones(len(ws),bool) if r=='All' else rce==r)
        cell_idx[(pn,r)]=np.where(m)[0]
hr=ws.hourly_wage.values; an=ws.annual_wage_adj.values; ft=ws.ftfy.values
def stat_fn(df,w):
    W=df[w].values; out={}
    for (pn,r),ix in cell_idx.items():
        if len(ix)==0: continue
        out[(pn,r,'median_hourly')]=L.wmedian(hr[ix],W[ix])
        out[(pn,r,'mean_hourly')]=np.average(hr[ix],weights=W[ix]) if W[ix].sum()>0 else np.nan
        f=ix[ft[ix]]
        out[(pn,r,'median_annual_ftfy')]=L.wmedian(an[f],W[f]) if len(f) else np.nan
        out[(pn,r,'mean_annual_ftfy')]=np.average(an[f],weights=W[f]) if len(f) and W[f].sum()>0 else np.nan
    s=pd.Series(out)
    # ratios to White in same pool; differences AIPOS-EXPOSED within race
    extra={}
    for (pn,r,m),v in s.items():
        if r!='White' and (pn,'White',m) in s.index: extra[(pn,r,m+'_ratio_to_White')]=v/s[(pn,'White',m)]
        if pn=='AIPOS' and ('EXPOSED',r,m) in s.index: extra[('PRIZE_AIPOS_minus_EXPOSED',r,m+'_diff')]=v-s[('EXPOSED',r,m)]; extra[('PRIZE_AIPOS_over_EXPOSED',r,m+'_ratio')]=v/s[('EXPOSED',r,m)]
        if pn=='AIPS2' and ('EXPOSED',r,m) in s.index: extra[('PRIZE_AIPS2_minus_EXPOSED',r,m+'_diff')]=v-s[('EXPOSED',r,m)]; extra[('PRIZE_AIPS2_over_EXPOSED',r,m+'_ratio')]=v/s[('EXPOSED',r,m)]
    s=pd.concat([s,pd.Series(extra)]); s.index=s.index.set_names(['pool','race_eth','metric']); return s
est,se=L.rep_se(stat_fn,ws)
t=pd.concat([est.rename('est'),se.rename('se')],axis=1).reset_index()
nn=pd.DataFrame([(pn,r,len(ix),ws.PWGTP.values[ix].sum(), int(ft[ix].sum())) for (pn,r),ix in cell_idx.items()],columns=['pool','race_eth','n_unw','w_n','n_unw_ftfy'])
t=t.merge(nn,on=['pool','race_eth'],how='left')
t['suppressed']=np.where(t.metric.str.contains('ftfy'), t.n_unw_ftfy<MIN_N, t.n_unw<MIN_N)
# prize rows: thin if either side thin
thin=nn.set_index(['pool','race_eth'])
def pz(row):
    if row.pool.startswith('PRIZE'):
        a='AIPOS' if 'AIPS2' not in row.pool else 'AIPS2'
        col='n_unw_ftfy' if 'ftfy' in row.metric else 'n_unw'
        return min(thin.loc[(a,row.race_eth),col], thin.loc[('EXPOSED',row.race_eth),col])<MIN_N
    if row.metric.endswith('_to_White'):
        col='n_unw_ftfy' if 'ftfy' in row.metric else 'n_unw'
        return min(thin.loc[(row.pool,row.race_eth),col], thin.loc[(row.pool,'White'),col])<MIN_N
    return row.suppressed
t['suppressed']=t.apply(pz,axis=1)
t.to_csv(f'{B}/wages_by_occclass_race.csv',index=False)
print('wage table done',flush=True)

# ----- regression gap test -----
def design(sample, A, adjust):
    s=sample
    side=np.where(s.occ_class.isin(A),'A','E')
    cols={}; names=[]
    cols['const']=np.ones(len(s))
    for c in sorted(set(A)|set(L.EXPOSED))[1:]: cols['cls_'+c]=(s.occ_class.values==c).astype(float)
    for r in L.RACES[1:]:
        for sd in ('A','E'): cols[f'{r}_{sd}']=((s.race_eth.values==r)&(side==sd)).astype(float)
    cols['side_A']=(side=='A').astype(float)   # absorbed partly by class FE; keep out to avoid collinearity
    cols.pop('side_A')
    if adjust:
        cols['age']=s.AGEP.values.astype(float); cols['age2']=(s.AGEP.values.astype(float)**2)/100
        cols['female']=(s.SEX.values==2).astype(float)
        for e in ['HS','SomeCollege_Assoc','Bachelors','Graduate']: cols['edu_'+e]=(s.education.values==e).astype(float)
        for c in sorted(L.BAY.values())[1:]: cols['cty_'+c]=(s.county.values==c).astype(float)
        cols['foreign_born']=(s.NATIVITY.values==2).astype(float)
    X=np.column_stack(list(cols.values())); return X, list(cols.keys())
def wls(X,y,w):
    XtW=X.T*w; return np.linalg.solve(XtW@X, XtW@y)
rows=[]
for Aname,A in (('AI_PRODUCER+SOFTWARE_ENG',['AI_PRODUCER','SOFTWARE_ENG']),('AIPOS3',L.AIPOS)):
    smp=ws[ws.occ_class.isin(A+L.EXPOSED)].reset_index(drop=True)
    y=np.log(smp.hourly_wage.values)
    for adjust in (False,True):
        X,names=design(smp,A,adjust)
        b0=wls(X,y,smp.PWGTP.values)
        B_=np.array([wls(X,y,smp[r].values) for r in L.REP])
        se_=np.sqrt(4/80*((B_-b0)**2).sum(axis=0))
        # difference A-E for each race
        for r in ['Black','Hispanic','Asian','Two_or_Other']:
            ia,ie=names.index(f'{r}_A'),names.index(f'{r}_E')
            diff=b0[ia]-b0[ie]; dse=np.sqrt(4/80*(((B_[:,ia]-B_[:,ie])-diff)**2).sum())
            nA=int(((smp.race_eth==r)&smp.occ_class.isin(A)).sum()); nE=int(((smp.race_eth==r)&smp.occ_class.isin(L.EXPOSED)).sum())
            rows.append(dict(A_def=Aname,adjusted=adjust,race_eth=r,vs='White',log_gap_in_AIclasses=b0[ia],se_A=se_[ia],log_gap_in_exposed=b0[ie],se_E=se_[ie],
                diff_A_minus_E=diff,se_diff=dse,z=diff/dse,n_A_unw=nA,n_E_unw=nE,pct_gap_A=np.expm1(b0[ia]),pct_gap_E=np.expm1(b0[ie]),thin=min(nA,nE)<MIN_N))
pd.DataFrame(rows).to_csv(f'{B}/wage_gap_tests.csv',index=False)
print(pd.DataFrame(rows).round(4).to_string())
