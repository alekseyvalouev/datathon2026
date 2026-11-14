import numpy as np, pandas as pd, glob, warnings
warnings.filterwarnings('ignore')
S='/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/'
RACE=['White','Black','Asian','Hispanic','AIAN','NHPI','Two_or_Other']
z=pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(S+'base/asset_zillow_p?.parquet'))],ignore_index=True).copy()
zc=sorted(c for c in z.columns if c.startswith('zh_'))
z['last']=z[zc].ffill(axis=1).iloc[:,-1]
lm=pd.Series(np.array(zc)[len(zc)-1-z[zc].notna().values[:,::-1].argmax(1)],index=z.index); lm[z[zc].notna().sum(1)==0]=None
z=z[(lm>='zh_202606').values]
# window length: Jan 2023 -> median last month
lastdates=pd.to_datetime(lm[(lm>='zh_202606')].str[3:]+'01',format='%Y%m%d'); end=lastdates.median(); yrs=(end-pd.Timestamp('2023-01-01')).days/365.25
print('median end',end.date(),'years',round(yrs,2))
ok=z.zh_202301.notna()&(z.zh_202301>50000)&z['last'].notna()
d=z[ok]
g=d.groupby('county_name').apply(lambda x:pd.Series({'n_panel':len(x),'g_valwtd':x['last'].sum()/x.zh_202301.sum()-1,'g_median':np.exp(np.log(x['last']/x.zh_202301).median())-1,'med_start':x.zh_202301.median(),'med_end':x['last'].median()}))
print(g.round(3)); g.to_csv(S+'base/asset_county_appreciation_2023_2026.csv')
bay_g=d['last'].sum()/d.zh_202301.sum()-1; print('bay valwtd',bay_g)
h=pd.read_parquet(S+'base/asset_pums_hh_joined_tmp.parquet')
p=pd.read_parquet(S+'base/asset_pums_adults_tmp.parquet')
WC=[f'WGTP{i}' if False else None for i in range(0)]
H=['WGTP']+[f'WGTP{i}' for i in range(1,81)]; P=['PWGTP']+[f'PWGTP{i}' for i in range(1,81)]
def gsum(df,keys,val,W):
    gi=df.groupby(keys).ngroup(); lab=df.groupby(keys).size().index; M=np.zeros((gi.max()+1,81))
    np.add.at(M,gi.values,df[val].values.astype(float)[:,None]*df[W].values.astype(float)); return pd.DataFrame(M,index=lab)
h['mort']=(h.TEN==1)*1.0
rows=[]
for scen,gcol in [('A_valwtd','g_valwtd'),('B_median','g_median')]:
    h['gain']=h.val_o*h.county.map(g[gcol])
    # group totals as (g x 81) matrices
    for keys,lab in [(['race_eth'],'bay'),(['county','race_eth'],'county')]:
        G=gsum(h,keys,'gain',H); V=gsum(h,keys,'val_o',H); OWN=gsum(h,keys,'owner',H); HH=gsum(h,keys,'one',H); MT=gsum(h,keys,'mort',H)
        Wg=gsum(p,keys,'WAGP_a',P); EM=gsum(p,keys,'emp',P)
        idx=G.index.union(Wg.index)
        for k in idx:
            def f(M): return M.loc[k].values if k in M.index else np.zeros(81)
            gain=f(G); val=f(V); own=f(OWN); hh=f(HH); wag=f(Wg); emp=f(EM); mt=f(MT)
            ann=gain/yrs
            r=dict(scenario=scen,level=lab,county=(k[0] if lab=='county' else 'ALL_BAY'),race_eth=(k[1] if lab=='county' else k))
            r.update({'owner_value_$bn':val[0]/1e9,'appreciation_total_$bn':gain[0]/1e9,'appreciation_annualized_$bn':ann[0]/1e9,
                     'wage_income_annual_$bn':wag[0]/1e9,'employed_workers_w':emp[0],'owner_hh_w':own[0],'hh_w':hh[0]})
            ratio=ann/np.where(wag==0,np.nan,wag); r['annual_appreciation_over_annual_wages']=ratio[0]; r['ratio_se']=np.sqrt(4/80*np.nansum((ratio[1:]-ratio[0])**2))
            r['appreciation_per_owner_hh_total_$']=gain[0]/own[0] if own[0] else np.nan
            r['appreciation_per_owner_hh_per_yr_$']=ann[0]/own[0] if own[0] else np.nan
            r['wage_per_worker_per_yr_$']=wag[0]/emp[0] if emp[0] else np.nan
            r['appreciation_per_hh_per_yr_$']=ann[0]/hh[0] if hh[0] else np.nan   # spread over ALL households incl renters
            r['pct_owners_with_mortgage']=100*mt[0]/own[0] if own[0] else np.nan
            r['n_households_unw']=int(h.groupby(keys).size().get(k,0))
            r['thin_lt50']=r['n_households_unw']<50
            rows.append(r)
R=pd.DataFrame(rows)
# shares within bay
for sc in ['A_valwtd','B_median']:
    m=(R.scenario==sc)&(R.level=='bay')
    tot=R[m]
    R.loc[m,'share_of_bay_appreciation_pct']=100*tot['appreciation_total_$bn']/tot['appreciation_total_$bn'].sum()
    R.loc[m,'share_of_bay_wages_pct']=100*tot['wage_income_annual_$bn']/tot['wage_income_annual_$bn'].sum()
    R.loc[m,'share_of_bay_households_pct']=100*tot['hh_w']/tot['hh_w'].sum()
    R.loc[m,'share_of_bay_workers_pct']=100*tot['employed_workers_w']/tot['employed_workers_w'].sum()
tot_row=[]
for sc in ['A_valwtd','B_median']:
    t=R[(R.scenario==sc)&(R.level=='bay')]
    tot_row.append(dict(scenario=sc,level='bay',county='ALL_BAY',race_eth='ALL_BAY',**{'owner_value_$bn':t['owner_value_$bn'].sum(),'appreciation_total_$bn':t['appreciation_total_$bn'].sum(),'appreciation_annualized_$bn':t['appreciation_annualized_$bn'].sum(),'wage_income_annual_$bn':t['wage_income_annual_$bn'].sum(),'employed_workers_w':t.employed_workers_w.sum(),'owner_hh_w':t.owner_hh_w.sum(),'hh_w':t.hh_w.sum()}))
T=pd.DataFrame(tot_row); T['annual_appreciation_over_annual_wages']=T['appreciation_annualized_$bn']/T['wage_income_annual_$bn']; T['appreciation_per_owner_hh_per_yr_$']=T['appreciation_annualized_$bn']*1e9/T.owner_hh_w; T['wage_per_worker_per_yr_$']=T['wage_income_annual_$bn']*1e9/T.employed_workers_w
R=pd.concat([R,T],ignore_index=True); R['window']=f'2023-01 to ~{end.strftime("%Y-%m")} ({yrs:.2f} yrs)'
R.to_csv(S+'base/asset_equity_capture.csv',index=False)
pd.set_option('display.width',250,'display.max_columns',40)
for sc in ['A_valwtd','B_median']:
    x=R[(R.scenario==sc)&(R.level=='bay')].set_index('race_eth')
    print(sc); print(x[['owner_value_$bn','appreciation_total_$bn','appreciation_annualized_$bn','wage_income_annual_$bn','annual_appreciation_over_annual_wages','ratio_se','appreciation_per_owner_hh_per_yr_$','wage_per_worker_per_yr_$','appreciation_per_hh_per_yr_$','share_of_bay_appreciation_pct','share_of_bay_wages_pct','share_of_bay_households_pct','share_of_bay_workers_pct','pct_owners_with_mortgage']].reindex(RACE+['ALL_BAY']).round(3).to_string())
x=R[(R.scenario=='A_valwtd')&(R.level=='county')].pivot(index='county',columns='race_eth',values='annual_appreciation_over_annual_wages')[RACE]; print(x.round(2))
