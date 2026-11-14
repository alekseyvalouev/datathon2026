import sys, json, numpy as np, pandas as pd
S='/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/'
src,tag=sys.argv[1],sys.argv[2]
BAYN={'Alameda','Contra Costa','Marin','Napa','San Francisco','San Mateo','Santa Clara','Solano','Sonoma'}
cols=['zpid','city','state','homeStatus','bedrooms','bathrooms','price','yearBuilt','zipcode','longitude','latitude','livingArea','homeType','zestimate','rentZestimate','taxAssessedValue','taxAssessedYear','propertyTaxRate','lastSoldPrice','dateSoldString','countyFIPS','county','priceHistory','zestimate_history','is_flipped_within_12_months']
rows=[];sales=[];rents=[];allcnt=[]
n=0
for ch in pd.read_csv(src,usecols=cols,chunksize=20000,dtype={'zipcode':str}):
    n+=len(ch)
    ch['county_name']=ch.county.astype(str).str.replace(' County','',regex=False)
    allcnt.append(ch.groupby(['state','county_name']).size().rename('n').reset_index())
    ch=ch[(ch.state=='CA')&ch.county_name.isin(BAYN)].copy()
    zh_rows=[]
    for z,ph,zh in zip(ch.zpid,ch.priceHistory,ch.zestimate_history):
        if isinstance(ph,str):
            try:
                for e in json.loads(ph):
                    if e.get('event')=='Sold' and not e.get('postingIsRental') and e.get('price'):
                        sales.append((z,e['date'],e['price'],e.get('pricePerSquareFoot')))
                    elif e.get('event')=='Listed for rent' and e.get('price'):
                        rents.append((z,e['date'],e['price']))
            except Exception: pass
        d={'zpid':z}
        if isinstance(zh,str):
            try:
                for e in json.loads(zh):
                    d['zh_'+e['as_of_date'][:7].replace('-','')]=e['amount']*1000
            except Exception: pass
        zh_rows.append(d)
    z=pd.DataFrame(zh_rows)
    ch=ch.drop(columns=['priceHistory','zestimate_history']).merge(z,on='zpid',how='left')
    rows.append(ch)
df=pd.concat(rows,ignore_index=True); df['src']=tag
zc=[c for c in df.columns if c.startswith('zh_')]; df[zc]=df[zc].astype('float32')
df.to_parquet(S+f'base/asset_zillow_{tag}.parquet')
pd.DataFrame(sales,columns=['zpid','date','price','ppsf']).to_parquet(S+f'base/asset_zillow_sales_{tag}.parquet')
pd.DataFrame(rents,columns=['zpid','date','price']).to_parquet(S+f'base/asset_zillow_rentlist_{tag}.parquet')
pd.concat(allcnt).groupby(['state','county_name']).n.sum().reset_index().to_csv(S+f'base/asset_zillow_allrows_county_{tag}.csv',index=False)
print(tag,'rows read',n,'bay kept',len(df),flush=True)
