import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, re, pandas as pd, numpy as np
from sklearn.linear_model import LogisticRegression
pd.set_option('display.width',250); pd.set_option('display.max_columns',40)
P=sys.argv[1]
h=pd.read_csv(WORK+'/heard_dedup.csv',index_col=0); it=pd.read_csv(P+'/items.csv.gz',low_memory=False,usecols=['id_parent','item_text','record_type']); c=pd.read_csv(WORK+'/c_groups.csv',low_memory=False)
it=it[it.id_parent.isin(h.index)]; L=it.item_text.fillna('').str.lower().str.replace(r'\s+',' ',regex=True); t=L.groupby(it.id_parent).apply(lambda x:' || '.join(x.unique())); h['t']=h.index.map(t)
h['district']=pd.to_numeric(h.t.str.extract(r'\(district (\d+)\)')[0],errors='coerce')
def zone(s):
    for lab,p in [('RH-1 (one-family)',r'\brh-1'),('RH-2 (two-family)',r'\brh-2'),('RH-3 (three-family)',r'\brh-3'),('RM/RTO/RC (multi-family)',r'\brm-\d|\brto|\brc-\d'),('NC (neighborhood commercial)',r'\bnc[a-z]?-?\d|\bnct|neighborhood commercial'),('Downtown / mixed-use / other',r'\bc-3|\bumu|\bmur|\bmug|\bdtr|\bpdr|\bc-2|\brcd|\bwmug|\bcmuo')]:
        if re.search(p,s): return lab
    return 'not stated'
h['zone']=h.t.map(zone)
F={'vertical addition':'vertical addition|additional stor|add a .{0,12}(?:floor|story)|third[- ]story|fourth[- ]story addition','horizontal / rear addition':'horizontal|rear addition|rear yard','new construction':'new construction|construct a new|construction of a new','roof deck':'roof deck','demolition':'demoli','single-family home involved':'single[- ]family','ADU':'accessory dwelling|\\badu','unit merger / removal':'merg|removal of .{0,20}unit|unauthorized','density bonus / HOME-SF':'density bonus|home-sf','formula retail / commercial':'formula retail|restaurant|retail use','garage / parking':'garage|parking'}
for k,p in F.items(): h[k]=h.t.str.contains(p).astype(int)
h['is_dr']=(h.dr==True).astype(int); h['any_dr_team']=h.drteam_ever; h['any_nhood']=h.nhood_ever; h['any_opp']=(h.opp>0).astype(int); h['heavy_opp']=(h.opp>=6).astype(int)
print('projects',len(h),'| DR-calendar',h.is_dr.sum(),'| any DR-team speaker',h.any_dr_team.sum(),'| any nhood assoc',h.any_nhood.sum(),'| any opposition',h.any_opp.sum(),'| 6+ opposing',h.heavy_opp.sum())
def tab(col,order=None):
    r=h.groupby(col,observed=True).agg(projects=('is_dr','size'),dr_case=('is_dr','mean'),nhood_assoc=('any_nhood','mean'),any_opposition=('any_opp','mean'),six_plus_opp=('heavy_opp','mean'),mean_opp=('opp','mean'),soft_kill=('soft','mean')).round(3)
    return r
print('\n== by zoning'); print(tab('zone').sort_values('dr_case',ascending=False).to_string())
h['size']=np.where(h.units.isna(),'units unknown',np.where(h.units<=2,'1-2 units',np.where(h.units<10,'3-9',np.where(h.units<50,'10-49','50+'))))
print('\n== by size'); print(tab('size').loc[['1-2 units','3-9','10-49','50+','units unknown']].to_string())
print('\n== by neighbourhood price tercile'); print(tab('terc').to_string())
print('\n== by supervisor district'); print(tab('district').to_string())
rows=[]
for k in F:
    a=h[h[k]==1]; b=h[h[k]==0]; rows.append({'feature in project description':k,'projects':len(a),'DR case %':100*a.is_dr.mean(),'(without) DR %':100*b.is_dr.mean(),'nhood assoc %':100*a.any_nhood.mean(),'(without) nhood %':100*b.any_nhood.mean(),'6+ opp %':100*a.heavy_opp.mean(),'(without) 6+ opp %':100*b.heavy_opp.mean(),'mean opp':a.opp.mean()})
print('\n== by scope of work'); print(pd.DataFrame(rows).round(1).to_string(index=False))
X=pd.concat([h[list(F)],pd.get_dummies(h.zone,dtype=int).drop(columns=['not stated']),pd.DataFrame({'high_price':(h.terc=='high $/sqft').astype(int),'low_price':(h.terc=='low $/sqft').astype(int),'log_units':np.log1p(h.units.fillna(0)),'year':h.year-2015})],axis=1).reset_index(drop=True)
rng=np.random.default_rng(2)
def boot(y,n=300):
    y=np.asarray(y); o=[]
    for _ in range(n):
        i=rng.integers(0,len(y),len(y)); o.append(LogisticRegression(C=10,max_iter=3000).fit(X.iloc[i],y[i]).coef_[0])
    o=np.array(o); r=pd.DataFrame({'OR':np.exp(np.median(o,0)),'lo':np.exp(np.percentile(o,2.5,0)),'hi':np.exp(np.percentile(o,97.5,0))},index=X.columns).round(2); return r[(r.lo>1)|(r.hi<1)].sort_values('OR',ascending=False)
print('\n== adjusted odds ratios (only those whose 95% interval excludes 1)')
for lab,y in [('is a DR case',h.is_dr),('neighbourhood association spoke',h.any_nhood),('6+ opposing comments',h.heavy_opp)]:
    print('--',lab,'(events',int(y.sum()),')'); print(boot(y.values).to_string())
print('\nmedian Zillow $/sqft near project: DR cases',h[h.is_dr==1].ppsf.median().round(0),'| other',h[h.is_dr==0].ppsf.median().round(0),'| nhood assoc present',h[h.any_nhood==1].ppsf.median().round(0),'| absent',h[h.any_nhood==0].ppsf.median().round(0))
d=h[h.is_dr==1]; print('DR cases: units median',d.units.median(),'| share 1-2 units or unknown',((d.units<=2)|d.units.isna()).mean().round(2),'| outcome',d.final.value_counts(normalize=True).round(3).to_dict())
print('DR cases: mean supporters',d.sup.mean().round(1),'opponents',d.opp.mean().round(1),'| share where requestor side outnumbers support',(d.opp>d.sup).mean().round(2))
