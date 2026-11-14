"""Test (f): COUNTERFACTUAL shift-share incidence grid. NOT a forecast. Usage: pums_incidence.py base_dir"""
import sys, os, itertools, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pums_lib as L
B=sys.argv[1]; MIN_N=50
d=pd.read_parquet(f'{B}/pums_bay.parquet')
d=d[d.annual_wage_adj>0].reset_index(drop=True)      # base = employed persons with positive wage/salary income
a=d.annual_wage_adj.values
disp=d.occ_class.isin(['CLERICAL_ADMIN','CUSTOMER_SUPPORT']).values
gain=d.occ_class.isin(['AI_PRODUCER','SOFTWARE_ENG']).values
race=d.race_eth.values; cty=d.county.values
PEN=0.20
def cf(w, X, Y, R):
    """returns (survivor/re-employed weights+wages arrays) -> per-person arrays"""
    ws=w*(1-X*disp); wa=a*(1+Y*gain)
    wr=w*X*R*disp; ra=a*(1-PEN)
    return ws,wa,wr,ra
def groups():
    g={}
    for r in L.RACES+['All']:
        mr=np.ones(len(d),bool) if r=='All' else race==r
        g[('race',r,'All')]=mr
    for c in list(L.BAY.values())+['All']:
        mc=np.ones(len(d),bool) if c=='All' else cty==c
        g[('county','All',c)]=mc
        for r in L.RACES:
            g[('race_county',r,c)]=mc&(race==r)
    return g
G=groups()
def cell(w,X,Y,R,m):
    ws,wa,wr,ra=cf(w,X,Y,R)
    base_w=w[m]; base_med=L.wmedian(a[m],base_w); base_mass=(base_w*a[m]).sum(); base_n=base_w.sum()
    mass=(ws[m]*wa[m]).sum()+(wr[m]*ra[m]).sum()
    med=L.wmedian(np.concatenate([wa[m],ra[m]]),np.concatenate([ws[m],wr[m]]))
    emp=ws[m].sum()+wr[m].sum()
    return dict(base_median=base_med,cf_median_employed=med,base_mass=base_mass,cf_mass=mass,base_n=base_n,cf_employed=emp,
                base_percap=base_mass/base_n,cf_percap=mass/base_n)
SCEN=list(itertools.product([0.05,0.10,0.20],[0.05,0.10,0.20],[0.0,0.5]))
nU=pd.Series({k:int(m.sum()) for k,m in G.items()})
rows=[]
for X,Y,R in SCEN:
    for (lvl,r,c),m in G.items():
        v=cell(d.PWGTP.values,X,Y,R,m); v.update(level=lvl,race_eth=r,county=c,X_clerical_cs_job_cut=X,Y_ai_wage_gain=Y,reemploy_share=R,reemploy_wage_penalty=PEN if R>0 else np.nan,n_unw=nU[(lvl,r,c)])
        rows.append(v)
g=pd.DataFrame(rows)
for b,cfc in (('base_median','cf_median_employed'),('base_mass','cf_mass'),('base_percap','cf_percap')):
    g['d_'+cfc]=g[cfc]-g[b]; g['pct_'+cfc]=g[cfc]/g[b]-1
g['suppressed']=g.n_unw<MIN_N
# gap rows (race level, Bay-wide) with replicate SEs
def gaps(w,X,Y,R):
    out={}
    for r in ['White','Black','Hispanic','Asian']:
        v=cell(w,X,Y,R,G[('race',r,'All')]); out[r]=v
    res={}
    for r in ['Black','Hispanic','Asian']:
        for nm,b,c in (('median','base_median','cf_median_employed'),('percap','base_percap','cf_percap')):
            res[(r,nm,'baseline_ratio_to_White')]=out[r][b]/out['White'][b]
            res[(r,nm,'cf_ratio_to_White')]=out[r][c]/out['White'][c]
            res[(r,nm,'change_in_ratio_pts')]=res[(r,nm,'cf_ratio_to_White')]-res[(r,nm,'baseline_ratio_to_White')]
            res[(r,nm,'baseline_dollar_gap')]=out['White'][b]-out[r][b]
            res[(r,nm,'cf_dollar_gap')]=out['White'][c]-out[r][c]
            res[(r,nm,'change_in_dollar_gap')]=res[(r,nm,'cf_dollar_gap')]-res[(r,nm,'baseline_dollar_gap')]
    return pd.Series(res)
grow=[]
for X,Y,R in SCEN:
    est=gaps(d.PWGTP.values,X,Y,R); acc=0
    for rw in L.REP:
        acc=acc+(gaps(d[rw].values,X,Y,R)-est)**2
    se=np.sqrt(4/80*acc)
    t=pd.concat([est.rename('est'),se.rename('se')],axis=1).reset_index(); t.columns=['race_eth','gap_measure','metric','est','se']
    t['X_clerical_cs_job_cut']=X; t['Y_ai_wage_gain']=Y; t['reemploy_share']=R
    grow.append(t)
gp=pd.concat(grow)
g.to_csv(f'{B}/incidence_grid.csv',index=False)
gp.to_csv(f'{B}/incidence_gap_changes.csv',index=False)
print(gp[(gp.reemploy_share==0)&(gp.metric.isin(['change_in_ratio_pts','baseline_ratio_to_White']))].pivot_table(index=['race_eth','gap_measure','X_clerical_cs_job_cut'],columns=['metric','Y_ai_wage_gain'],values='est').round(4).to_string())
