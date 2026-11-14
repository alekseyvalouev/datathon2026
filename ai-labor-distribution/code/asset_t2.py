import sys, numpy as np, pandas as pd
sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
import pums_lib as L
S='/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/'
RACE_ORDER=['White','Black','Asian','Hispanic','AIAN','NHPI','Two_or_Other']
pp=pd.read_parquet(S+'base/asset_pums_person_bay.parquet',columns=['SERIALNO','RELSHIPP','race_eth','AGEP'])
pp=pp[pd.to_numeric(pp.RELSHIPP,errors='coerce')==20][['SERIALNO','race_eth','AGEP']].rename(columns={'AGEP':'hh_age'})
print('householders',len(pp),'dup',pp.SERIALNO.duplicated().sum())
h=pd.read_parquet(S+'base/asset_pums_hh_bay.parquet')
h=h[pd.to_numeric(h.TYPEHUGQ,errors='coerce')==1]
h['TEN']=pd.to_numeric(h.TEN,errors='coerce'); h=h[h.TEN.isin([1,2,3,4])]
h=h.merge(pp,on='SERIALNO',how='left'); print('hh occupied',len(h),'no householder match',h.race_eth.isna().sum())
h=h.dropna(subset=['race_eth'])
h['owner']=h.TEN.isin([1,2]).astype(float); h['renter']=(h.TEN==3).astype(float)
h['VALP']=pd.to_numeric(h.VALP,errors='coerce'); h['MV']=pd.to_numeric(h.MV,errors='coerce')
h['val_o']=np.where(h.owner==1,h.VALP.fillna(0),0.0); h['has_val']=((h.owner==1)&h.VALP.notna()).astype(float)
h['hinc']=pd.to_numeric(h.HINCP,errors='coerce')*h.ADJINC.astype(float)/1e6
h['one']=1.0
h['own10']=((h.owner==1)&(h.MV>=5)).astype(float)   # moved in 10+ years before survey year
h['own20']=((h.owner==1)&(h.MV>=6)).astype(float)
WC=['WGTP']+[f'WGTP{i}' for i in range(1,81)]
vals=['one','owner','renter','val_o','has_val','own10','own20']
def sums(df,keys):
    g=df.groupby(keys).ngroup(); lab=df.groupby(keys).size().index; ng=g.max()+1
    W=df[WC].values.astype(float); out={}
    for v in vals:
        M=np.zeros((ng,81)); np.add.at(M,g.values,df[v].values.astype(float)[:,None]*W); out[v]=M
    return out,lab,df.groupby(keys).size().values
def se(n,d=None):
    r=n/d if d is not None else n
    return r[:,0],np.sqrt(4/80*((r[:,1:]-r[:,[0]])**2).sum(1))
def build(df,keys,den=None):
    s,lab,n=sums(df,keys); res=pd.DataFrame(index=lab); res['n_households_unw']=n; res['thin_lt50']=n<50
    res['households_w']=s['one'][:,0]
    r,e=se(s['owner'],s['one']); res['homeownership_rate_pct']=100*r; res['homeownership_se']=100*e
    ow=df[df.owner==1]
    res['n_owners_unw']=ow.groupby(keys).size().reindex(res.index).fillna(0).values
    res['median_VALP_owners_$']=ow.groupby(keys).apply(lambda d:L.wmedian(d.VALP.values,d.WGTP.values),include_groups=False).reindex(res.index).values
    res['mean_VALP_owners_$']=(s['val_o'][:,0]/s['has_val'][:,0])
    res['total_owner_value_$bn']=s['val_o'][:,0]/1e9
    res['pct_owners_moved_in_10plus_yrs']=100*s['own10'][:,0]/s['owner'][:,0]
    res['pct_owners_moved_in_20plus_yrs']=100*s['own20'][:,0]/s['owner'][:,0]
    res['median_MV_code_owners']=ow.groupby(keys).apply(lambda d:L.wmedian(d.MV.values,d.WGTP.values),include_groups=False).reindex(res.index).values
    res['median_HINCP_adj_$']=df.groupby(keys).apply(lambda d:L.wmedian(d.hinc.values,d.WGTP.values),include_groups=False).reindex(res.index).values
    res['median_HINCP_owners_$']=ow.groupby(keys).apply(lambda d:L.wmedian(d.hinc.values,d.WGTP.values),include_groups=False).reindex(res.index).values
    res['median_HINCP_renters_$']=df[df.renter==1].groupby(keys).apply(lambda d:L.wmedian(d.hinc.values,d.WGTP.values),include_groups=False).reindex(res.index).values
    return res,s
MVLAB={1:'<=12mo',2:'13-23mo',3:'2-4y',4:'5-9y',5:'10-19y',6:'20-29y',7:'30y+'}
# by race, bay total
r,s=build(h,['race_eth']); 
T={k:s[k].sum(0,keepdims=True) for k in vals}
for nm,k in [('share_households','one'),('share_owner_households','owner'),('share_renter_households','renter'),('share_owner_occupied_value','val_o')]:
    a,e=se(s[k],np.repeat(T[k],s[k].shape[0],0)); r[nm+'_pct']=100*a; r[nm+'_se']=100*e
r['value_share_over_hh_share']=r.share_owner_occupied_value_pct/r.share_households_pct
tot,_=build(h.assign(race_eth='ALL_BAY'),['race_eth'])
r=pd.concat([r.reindex(RACE_ORDER),tot]); r.index.name='race_eth'; r['county']='ALL_BAY'
# race x county
rc,s2=build(h,['county','race_eth']); 
cs,cl,_=sums(h,['county']); ci={c:i for i,c in enumerate(cl)}; idx=[ci[c] for c,_ in rc.index]
for nm,k in [('share_households','one'),('share_owner_households','owner'),('share_owner_occupied_value','val_o')]:
    a,e=se(s2[k],cs[k][idx]); rc[nm+'_of_county_pct']=100*a; rc[nm+'_se']=100*e
rc['value_share_over_hh_share']=rc.share_owner_occupied_value_of_county_pct/rc.share_households_of_county_pct
rc.index.names=['county','race_eth']
ct,_=build(h,['county']); ct.index.names=['county']; ct['race_eth']='ALL'
out=pd.concat([r.reset_index(),rc.reset_index(),ct.reset_index()],ignore_index=True)
out['median_MV_label_owners']=out.median_MV_code_owners.map(MVLAB)
out.to_csv(S+'base/asset_homeownership_by_race_county.csv',index=False)
pd.set_option('display.width',250,'display.max_columns',50)
c=['n_households_unw','homeownership_rate_pct','homeownership_se','median_VALP_owners_$','mean_VALP_owners_$','total_owner_value_$bn','share_households_pct','share_owner_occupied_value_pct','share_owner_occupied_value_se','value_share_over_hh_share','pct_owners_moved_in_10plus_yrs','median_MV_label_owners','median_HINCP_adj_$']
print(out[out.county=='ALL_BAY'][['race_eth']+c].round(2).to_string())
print(ct[['n_households_unw','homeownership_rate_pct','median_VALP_owners_$','total_owner_value_$bn']].round(1))
print(rc.reset_index().pivot(index='county',columns='race_eth',values='homeownership_rate_pct').round(1)[RACE_ORDER])
print(rc.reset_index().pivot(index='county',columns='race_eth',values='median_VALP_owners_$').round(0)[RACE_ORDER])
print('thin',rc.thin_lt50.sum())
# VALP unadjusted: check ADJHSG not applied
h.to_parquet(S+'base/asset_pums_hh_joined_tmp.parquet')
