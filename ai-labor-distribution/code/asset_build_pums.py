import sys, numpy as np, pandas as pd
sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
import pums_lib as L
S='/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/'
x=pd.read_csv(S+'base/puma_county_xwalk.csv',dtype=str); x=x[x.is_bay.astype(str)=='True']
pm=dict(zip(x.PUMA5CE,x.dom_county))
cols=['SERIALNO','SPORDER','PUMA','ADJINC','PWGTP','AGEP','INTP','RETP','SEMP','OIP','WAGP','PINCP','ESR','HISP','RAC1P','RELSHIPP']+[f'PWGTP{i}' for i in range(1,81)]
out=[]
for ch in pd.read_csv(S+'ext/pums/psam_p06.csv',usecols=cols,dtype={'SERIALNO':str,'PUMA':str},chunksize=300000):
    ch=ch[ch.PUMA.isin(pm)].copy(); out.append(ch)
p=pd.concat(out); p['county']=p.PUMA.map(pm).map(L.BAY)
p['race_eth']=L.race_eth(p.HISP,p.RAC1P)
p.to_parquet(S+'base/asset_pums_person_bay.parquet'); print(p.shape, p.county.value_counts())
h=pd.read_csv(S+'asset_ext/psam_h06.csv',usecols=['SERIALNO','PUMA','ADJINC','ADJHSG','WGTP','NP','TYPEHUGQ','TEN','VALP','HINCP','MV','BDSP','RNTP','GRNTP']+[f'WGTP{i}' for i in range(1,81)],dtype={'SERIALNO':str,'PUMA':str})
h=h[h.PUMA.isin(pm)].copy(); h['county']=h.PUMA.map(pm).map(L.BAY); h.to_parquet(S+'base/asset_pums_hh_bay.parquet'); print(h.shape)
