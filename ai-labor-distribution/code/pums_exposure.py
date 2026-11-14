"""Tests (a),(b),(d),(e),(g) + robustness. Usage: pums_exposure.py base_dir"""
import sys, os, numpy as np, pandas as pd
from math import erfc, sqrt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pums_lib as L
B = sys.argv[1]
MIN_N = 50
CATS = L.CLASSES + ['EXPOSED','AIPOS','ALL']
LV = (('Bay Area','bay'),('county','county'))

def prep(path, alt=False):
    d = pd.read_parquet(path)
    if alt: d['occ_class'] = np.where(d.OCCP.isin(L.AMBIGUOUS_TO_CLERICAL), 'CLERICAL_ADMIN', d.occ_class)
    d['bay']='Bay Area'; d['one']=1.0
    for c in L.CLASSES: d['i_'+c]=(d.occ_class==c).astype(float)
    d['i_EXPOSED']=d[['i_'+c for c in L.EXPOSED]].sum(axis=1)
    d['i_AIPOS']=d[['i_'+c for c in L.AIPOS]].sum(axis=1)
    d['i_ALL']=1.0
    return d

def grp_sums(df, w, geocol, cols, vals=None):
    """weighted sums of indicator cols (optionally times vals) by geo x race, plus race='All'."""
    X = df[cols].mul(df[w].values, axis=0)
    if vals is not None: X = X.mul(vals, axis=0)
    S = X.groupby([df[geocol].values, df['race_eth'].values]).sum(); S.index.names=['geo','race_eth']
    A = S.groupby(level='geo').sum(); A['race_eth']='All'; A = A.set_index('race_eth', append=True)
    return pd.concat([S,A]).sort_index()

def stack_metric(T, lvl, metric):
    s = T.stack(); s.index.names=['geo','race_eth','category']; s = s.rename('v').reset_index()
    s.insert(0,'geo_level',lvl); s['metric']=metric
    return s.set_index(['geo_level','geo','race_eth','category','metric'])['v']

icols = ['i_'+c for c in CATS]
def comp_fn(df, w):
    outs=[]
    for lvl,gc in LV:
        S = grp_sums(df,w,gc,icols); S.columns=CATS
        share = S.div(S['ALL'],axis=0)
        geo = share.index.get_level_values('geo')
        allsh = share.xs('All',level='race_eth').loc[geo].values
        allcnt = S.xs('All',level='race_eth').loc[geo].values
        outs += [stack_metric(share,lvl,'share_of_group'), stack_metric(share/allsh,lvl,'rep_index'),
                 stack_metric(S/allcnt,lvl,'share_of_category'), stack_metric(S,lvl,'w_cell')]
        r = (share['EXPOSED']/share['AIPOS']).to_frame('RATIO_EXPOSED_OVER_AIPOS')
        outs.append(stack_metric(r,lvl,'share_of_group'))
    return pd.concat(outs)

def counts(df, cats=CATS):
    outs=[]
    for lvl,gc in LV:
        S = grp_sums(df,'one',gc,['i_'+c for c in cats]); S.columns=cats
        s = S.stack(); s.index.names=['geo','race_eth','category']; s=s.rename('n_cell_unw').reset_index(); s.insert(0,'geo_level',lvl); outs.append(s)
    return pd.concat(outs)

def tidy_rep(fn, df):
    est,se = L.rep_se(fn, df)
    e = est.unstack('metric'); s = se.unstack('metric'); s.columns=['se_'+c for c in s.columns]
    return e.join(s).reset_index()

def tidy_comp(df):
    t = tidy_rep(comp_fn, df)
    cnt = counts(df); k=['geo_level','geo','race_eth']
    ng = cnt[cnt.category=='ALL'].rename(columns={'n_cell_unw':'n_group_unw'}).drop(columns='category')
    nE = cnt[cnt.category=='EXPOSED'].set_index(k).n_cell_unw; nA = cnt[cnt.category=='AIPOS'].set_index(k).n_cell_unw
    t = t.merge(cnt,on=k+['category'],how='left').merge(ng,on=k,how='left')
    idx = pd.MultiIndex.from_frame(t[k])
    t['n_cell_unw']=np.where(t.category=='RATIO_EXPOSED_OVER_AIPOS', np.minimum(nE.reindex(idx).values,nA.reindex(idx).values), t.n_cell_unw)
    t['suppressed']=(t.n_cell_unw<MIN_N)|(t.n_group_unw<MIN_N)
    cols=k+['category','n_group_unw','n_cell_unw','w_cell','share_of_group','se_share_of_group','share_of_category','se_share_of_category','rep_index','se_rep_index','suppressed']
    return t[cols].sort_values(k+['category']).reset_index(drop=True)

if __name__=='__main__':
    d5=prep(f'{B}/pums_bay.parquet'); d1=prep(f'{B}/pums_bay_2024.parquet')
    rc=[]
    for nm,d in (('2019-2023_5yr',d5),('2024_1yr',d1)):
        g=d.groupby('race_eth').agg(n_unweighted=('PWGTP','size'), n_weighted=('PWGTP','sum')); g.loc['All']=g.sum(); g['file']=nm; g['share_of_weighted']=g.n_weighted/g.loc['All','n_weighted']; rc.append(g.reset_index())
    pd.concat(rc).to_csv(f'{B}/race_counts.csv',index=False)
    t5=tidy_comp(d5)
    t5[t5.geo_level=='Bay Area'].drop(columns='geo_level').to_csv(f'{B}/exposure_by_race.csv',index=False)
    t5[t5.geo_level=='county'].drop(columns='geo_level').rename(columns={'geo':'county'}).to_csv(f'{B}/exposure_by_race_county.csv',index=False)
    t1=tidy_comp(d1); t1.to_csv(f'{B}/exposure_2024_all.csv',index=False)
    k=['geo_level','geo','race_eth','category']
    m=t5[t5.geo_level=='Bay Area'].merge(t1[t1.geo_level=='Bay Area'],on=k,suffixes=('_5yr','_2024'))
    m=m[m.category.isin(['EXPOSED','AIPOS','CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED','FRONTLINE_SERVICE','RATIO_EXPOSED_OVER_AIPOS'])].copy()
    m['diff_2024_minus_5yr']=m.share_of_group_2024-m.share_of_group_5yr
    m['se_diff']=np.sqrt(m.se_share_of_group_5yr**2+m.se_share_of_group_2024**2)
    m['z']=m.diff_2024_minus_5yr/m.se_diff
    m['p_two_sided']=m.z.apply(lambda z: erfc(abs(z)/sqrt(2)) if pd.notna(z) else np.nan)
    m['thin']=(m.n_cell_unw_5yr<MIN_N)|(m.n_cell_unw_2024<MIN_N)|(m.n_group_unw_5yr<MIN_N)|(m.n_group_unw_2024<MIN_N)
    m[k+['n_group_unw_5yr','n_group_unw_2024','n_cell_unw_5yr','n_cell_unw_2024','share_of_group_5yr','se_share_of_group_5yr','share_of_group_2024','se_share_of_group_2024','diff_2024_minus_5yr','se_diff','z','p_two_sided','thin']].to_csv(f'{B}/change_2024_vs_5yr.csv',index=False)
    ta=tidy_comp(prep(f'{B}/pums_bay.parquet',alt=True))
    ta[(ta.geo_level=='Bay Area')&ta.category.isin(['EXPOSED','AIPOS','RATIO_EXPOSED_OVER_AIPOS'])].to_csv(f'{B}/exposure_by_race_altmap.csv',index=False)
    print('comp done', flush=True)

    # ---- (d) wage mass ----
    dw=d5[d5.annual_wage_adj>0].copy()
    mc=L.EXPOSED+['EXPOSED','AIPOS','FRONTLINE_SERVICE','ALL']; mcols=['i_'+c for c in mc]
    def mass_fn(df,w):
        outs=[]
        for lvl,gc in LV:
            M=grp_sums(df,w,gc,mcols,vals=df.annual_wage_adj.values); M.columns=mc
            H=grp_sums(df,w,gc,mcols); H.columns=mc
            outs += [stack_metric(M,lvl,'wage_mass'), stack_metric(H,lvl,'wage_earners_w'), stack_metric(M.div(M['ALL'],axis=0),lvl,'share_of_group_wage_mass'),
                     stack_metric(M/H,lvl,'mean_annual_wage'), stack_metric(H.div(H['ALL'],axis=0),lvl,'share_of_group_wage_earners')]
        return pd.concat(outs)
    p=tidy_rep(mass_fn,dw)
    cnt=counts(dw,mc); k=['geo_level','geo','race_eth']
    ng=cnt[cnt.category=='ALL'].rename(columns={'n_cell_unw':'n_group_unw'}).drop(columns='category')
    p=p.merge(cnt,on=k+['category'],how='left').merge(ng,on=k,how='left')
    p['suppressed']=(p.n_cell_unw<MIN_N)|(p.n_group_unw<MIN_N)
    p['wage_mass_$M']=p.wage_mass/1e6; p['se_wage_mass_$M']=p.se_wage_mass/1e6
    p.to_csv(f'{B}/wage_mass_at_risk.csv',index=False)
    print('mass done', flush=True)

    # ---- (e) self-employment / contract ----
    ec=L.EXPOSED+['EXPOSED','AIPOS','FRONTLINE_SERVICE','ALL']; ecols=['i_'+c for c in ec]
    def sef(df,w):
        outs=[]
        for lvl,gc in (('Bay Area','bay'),):
            H=grp_sums(df,w,gc,ecols); H.columns=ec
            for mname,col in (('self_emp_share','self_employed'),('self_emp_unincorp_share','self_employed_unincorp')):
                Mx=grp_sums(df,w,gc,ecols,vals=df[col].astype(float).values); Mx.columns=ec
                outs.append(stack_metric(Mx/H,lvl,mname))
        return pd.concat(outs)
    p=tidy_rep(sef,d5); cnt=counts(d5,ec); cnt=cnt[cnt.geo_level=='Bay Area']
    p=p.merge(cnt,on=['geo_level','geo','race_eth','category'],how='left'); p['suppressed']=p.n_cell_unw<MIN_N
    p.drop(columns=['geo_level','geo']).to_csv(f'{B}/contract_precarity.csv',index=False)
    print('contract done')
