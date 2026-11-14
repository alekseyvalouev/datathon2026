import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, pandas as pd, numpy as np
cols=['zpid','city','county','zipcode','latitude','longitude','homeStatus','homeType','price','zestimate','rentZestimate','livingArea','bedrooms']
fs=sys.argv[1:-1]; out=sys.argv[-1]; parts=[]
for f in fs:
    for ch in pd.read_csv(f,usecols=cols,chunksize=20000,low_memory=False):
        parts.append(ch)
z=pd.concat(parts).drop_duplicates('zpid'); print('all rows',len(z)); print(z.county.value_counts().head(12)); print(z.homeStatus.value_counts())
sf=z[z.county.astype(str).str.contains('San Francisco',case=False)|(z.city.astype(str).str.lower()=='san francisco')]
print('SF rows',len(sf)); print(sf.homeStatus.value_counts()); print(sf[['price','zestimate','rentZestimate','livingArea']].describe().round(0).T)
print(sf.notna().mean().round(2).to_dict())
z.to_parquet(out.replace('sf','all')) if False else None
sf.to_csv(out,index=False); z[cols].to_csv(out.replace('zillow_sf','zillow_all'),index=False)
