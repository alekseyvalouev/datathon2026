import pandas as pd, zipfile
S='/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad'
# PUMA->county weights by tract share
t=pd.read_csv(S+'/ext/tract2puma.txt',dtype=str,encoding='utf-8-sig'); t=t[t.STATEFP=='06']
w=t.groupby(['PUMA5CE','COUNTYFP']).size().rename('n').reset_index()
w['share']=w.n/w.groupby('PUMA5CE').n.transform('sum')
z=zipfile.ZipFile(S+'/ext/pums2024_1yr_ca.zip')
p=pd.read_csv(z.open('psam_p06.csv'),usecols=['PUMA','PWGTP','ESR'],dtype={'PUMA':str})
p['PUMA']=p.PUMA.str.zfill(5)
emp=p[p.ESR.isin([1,2,4,5])].groupby('PUMA').PWGTP.sum().rename('emp').reset_index()
e=emp.merge(w,left_on='PUMA',right_on='PUMA5CE'); e['emp']=e.emp*e.share
ce=e.groupby('COUNTYFP').emp.sum()
c=pd.read_csv(S+'/den/co-est2024.csv',encoding='latin1'); c=c[(c.STNAME=='California')&(c.SUMLEV==50)]
c['COUNTYFP']=c.COUNTY.astype(str).str.zfill(3)
out=c[['COUNTYFP','CTYNAME','POPESTIMATE2023','POPESTIMATE2024']].copy()
out['county']=out.CTYNAME.str.replace(' County','')
out['employed_residents_acs2024']=out.COUNTYFP.map(ce).round()
out.drop(columns='CTYNAME').to_csv(S+'/base/warn_county_denominators.csv',index=False)
print(out.sort_values('POPESTIMATE2024',ascending=False).head(12)); print(out.employed_residents_acs2024.sum(), out.POPESTIMATE2024.sum())
