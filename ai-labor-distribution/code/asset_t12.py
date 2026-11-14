import sys, numpy as np, pandas as pd
sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
import pums_lib as L
S='/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/'
RACE_ORDER=['White','Black','Asian','Hispanic','AIAN','NHPI','Two_or_Other']
p=pd.read_parquet(S+'base/asset_pums_person_bay.parquet')
p=p[p.AGEP>=18].copy()
adj=p.ADJINC.astype(float)/1e6
for c in ['INTP','RETP','SEMP','OIP','WAGP','PINCP']:
    p[c+'_a']=p[c].astype(float)*adj
p['emp']=pd.to_numeric(p.ESR,errors='coerce').isin([1,2,4,5]).astype(float)
p['intp_pos']=(p.INTP_a>0).astype(float)
p['intp_pos_val']=p.INTP_a.clip(lower=0)
p['one']=1.0
WC=['PWGTP']+[f'PWGTP{i}' for i in range(1,81)]
def sums(df, keys, vals):
    """returns dict val-> DataFrame (groups x 81 weight cols) of weighted sums; groups via keys list"""
    g=df.groupby(keys).ngroup(); ng=g.max()+1
    lab=df.groupby(keys).size().index
    W=df[WC].values.astype(float)
    out={}
    for v in vals:
        x=df[v].values.astype(float)[:,None]*W
        M=np.zeros((ng,81)); np.add.at(M,g.values,x); out[v]=M
    n=df.groupby(keys).size().values
    return out,lab,n
def se(num,den=None):
    # num/den arrays (g,81) col0=full sample
    r=num/den if den is not None else num
    return r[:,0], np.sqrt(4/80*((r[:,1:]-r[:,[0]])**2).sum(1))

def wmed_by(df,keys,col,wcol):
    return df.groupby(keys).apply(lambda d: L.wmedian(d[col].values,d[wcol].values),include_groups=False)

vals=['one','emp','intp_pos','INTP_a','intp_pos_val','WAGP_a','PINCP_a','RETP_a','SEMP_a','OIP_a']
def build(df, keys):
    s,lab,n=sums(df,keys,vals)
    tot_s,_,_=sums(df.assign(_t=1),['_t'],vals)
    t={k:v for k,v in tot_s.items()}
    res=pd.DataFrame(index=lab); res['n_adults_unw']=n
    res['thin_lt50']=n<50
    res['adults_w']=s['one'][:,0]
    # participation
    r,e=se(s['intp_pos'],s['one']); res['pct_any_positive_INTP']=100*r; res['pct_any_INTP_se']=100*e
    # mean INTP all
    r,e=se(s['INTP_a'],s['one']); res['mean_INTP_all_$']=r; res['mean_INTP_all_se']=e
    # mean among holders (positive INTP)
    r,e=se(s['intp_pos_val'],s['intp_pos']); res['mean_INTP_holders_$']=r; res['mean_INTP_holders_se']=e
    r,e=se(s['INTP_a'],s['PINCP_a']); res['capinc_pct_of_total_income']=100*r; res['capinc_pct_se']=100*e
    r,e=se(s['WAGP_a'],s['PINCP_a']); res['wage_pct_of_total_income']=100*r
    r,e=se(s['RETP_a'],s['PINCP_a']); res['retire_pct_of_total_income']=100*r
    r,e=se(s['SEMP_a'],s['PINCP_a']); res['selfemp_pct_of_total_income']=100*r
    r,e=se(s['OIP_a'],s['PINCP_a']); res['other_pct_of_total_income']=100*r
    return res,s,t
def with_medians(res,df,keys):
    hold=df[df.INTP_a>0]
    mh=wmed_by(hold,keys,'INTP_a','PWGTP'); nh=hold.groupby(keys).size()
    res['median_INTP_holders_$']=mh.reindex(res.index).values
    res['n_holders_unw']=nh.reindex(res.index).fillna(0).values
    res['median_INTP_holders_thin_lt50']=res['n_holders_unw']<50
    return res
def shares(res,s,t,tot_key=None, tot_override=None):
    # group share of totals, with SE (denominator = overall total in same weight col)
    T={k:(tot_override[k] if tot_override is not None else t[k]) for k in ['INTP_a','WAGP_a','emp','one','intp_pos_val','PINCP_a']}
    for name,key in [('share_capital_income_INTP_net','INTP_a'),('share_positive_INTP','intp_pos_val'),('share_wage_income','WAGP_a'),('share_employed_workers','emp'),('share_adults','one'),('share_total_personal_income','PINCP_a')]:
        k={'INTP_a':'INTP_a','intp_pos_val':'intp_pos_val','WAGP_a':'WAGP_a','emp':'emp','one':'one','PINCP_a':'PINCP_a'}[key]
        num=s[key]; den=np.repeat(T[k],num.shape[0],axis=0)
        r,e=se(num,den); res[name+'_pct']=100*r; res[name+'_se']=100*e
    res['capital_share_minus_employment_share_pp']=res['share_capital_income_INTP_net_pct']-res['share_employed_workers_pct']
    res['capital_share_over_employment_share']=res['share_capital_income_INTP_net_pct']/res['share_employed_workers_pct']
    return res

# ---- by race (Bay overall)
res,s,t=build(p,['race_eth']); res=with_medians(res,p,['race_eth']); res=shares(res,s,t)
tot,s0,t0=build(p.assign(race_eth='ALL_BAY'),['race_eth']); tot=with_medians(tot,p.assign(race_eth='ALL_BAY'),['race_eth'])
tot['share_capital_income_INTP_net_pct']=100.0;tot['share_wage_income_pct']=100.0;tot['share_employed_workers_pct']=100.0;tot['share_adults_pct']=100.0
res=pd.concat([res.reindex(RACE_ORDER),tot]); res.index.name='race_eth'; res['level']='bay_total'
res.reset_index().to_csv(S+'base/asset_capital_income_by_race.csv',index=False)
pd.set_option('display.width',250,'display.max_columns',50)
print(res[['n_adults_unw','pct_any_positive_INTP','median_INTP_holders_$','mean_INTP_holders_$','mean_INTP_all_$','capinc_pct_of_total_income','share_capital_income_INTP_net_pct','share_capital_income_INTP_net_se','share_wage_income_pct','share_employed_workers_pct','share_adults_pct','capital_share_over_employment_share']].round(2).to_string())
print(res[['share_positive_INTP_pct','share_total_personal_income_pct','retire_pct_of_total_income','selfemp_pct_of_total_income','other_pct_of_total_income','wage_pct_of_total_income']].round(2))

# ---- race x county (shares relative to the county total) and county total
rc,s,t=build(p,['county','race_eth']); rc=with_medians(rc,p,['county','race_eth'])
# county totals for share denominators
cs,clab,_=sums(p,['county'],vals)
ci={c:i for i,c in enumerate(clab)}
den_idx=[ci[c] for c,_r in rc.index]
for name,key in [('share_capital_income_INTP_net','INTP_a'),('share_wage_income','WAGP_a'),('share_employed_workers','emp'),('share_adults','one')]:
    num=s[key]; den=cs[key][den_idx]; r,e=se(num,den); rc[name+'_of_county_pct']=100*r; rc[name+'_se']=100*e
rc['capital_over_employment_share']=rc['share_capital_income_INTP_net_of_county_pct']/rc['share_employed_workers_of_county_pct']
rc.index.names=['county','race_eth']; rc['level']='race_x_county'
cty,s,t=build(p,['county']); cty=with_medians(cty,p,['county']); cty.index.names=['county']; cty['race_eth']='ALL'; cty['level']='county_total'
out=pd.concat([rc.reset_index(),cty.reset_index()],ignore_index=True)
out.to_csv(S+'base/asset_capital_income_by_race_county.csv',index=False)
print(cty[['n_adults_unw','pct_any_positive_INTP','median_INTP_holders_$','mean_INTP_all_$','capinc_pct_of_total_income']].round(2))
w=rc.reset_index().pivot(index='county',columns='race_eth',values='pct_any_positive_INTP').round(1); print(w[RACE_ORDER])
w=rc.reset_index().pivot(index='county',columns='race_eth',values='capital_over_employment_share').round(2); print(w[RACE_ORDER])
print('thin cells',rc.thin_lt50.sum(),'of',len(rc))
p.to_parquet(S+'base/asset_pums_adults_tmp.parquet')
