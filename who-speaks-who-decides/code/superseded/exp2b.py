import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, re, pandas as pd, numpy as np
from sklearn.neighbors import BallTree
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.inspection import permutation_importance
pd.set_option('display.width',220)
P,Z,OUT=sys.argv[1:4]
c=pd.read_csv(P+'/comments.csv',low_memory=False); it=pd.read_csv(P+'/items.csv.gz',low_memory=False)
it['date']=pd.to_datetime(it.meeting_date); it['year']=it.date.dt.year
c=c[c.is_staff!=1]; g=c.groupby('item_id')
cf=pd.DataFrame({'n_comments':g.size(),'n_sup':g.position.apply(lambda s:(s=='support').sum()),'n_opp':g.position.apply(lambda s:(s=='oppose').sum()),'n_neu':g.position.apply(lambda s:(s=='neutral').sum()),
 'n_nhood':g.role_group.apply(lambda s:(s=='Neighborhood Association').sum()),'n_projteam':g.role_group.apply(lambda s:(s=='Project Team').sum()),'n_drteam':g.role_group.apply(lambda s:(s=='DR Team').sum()),
 'n_orgs':g.role_group.apply(lambda s:s.isin(['Housing Interest Groups','Pro-Development Interest Groups','Social Interest Groups','Business Groups']).sum()),'n_email':g.channel.apply(lambda s:(s=='email').sum())})
it=it.merge(cf,left_on='item_id',right_index=True,how='left'); cc=list(cf.columns); it[cc]=it[cc].fillna(0)
A=it.ACTION.fillna('').str.lower(); it['indef']=A.str.contains('indefinite'); it['modif']=A.str.contains(r'modif|as amended|amended to|revis|reduc|setback|set back|eliminat')
T=it.item_text.fillna('').str.lower()
def rx(p): return pd.to_numeric(T.str.extract(p)[0].str.replace(',',''),errors='coerce')
it['txt_units']=rx(r'([\d,]+)\s*(?:new\s+)?(?:dwelling|residential|housing|affordable)?\s*units'); it['txt_stories']=rx(r'(\d+)[- ]stor'); it['txt_sqft']=rx(r'([\d,]{4,})\s*(?:gross\s+)?(?:square|sq)'); it['txt_len']=T.str.len()
p=it[it.id_parent.notna()&(it.year>=2005)&it.section_group.isin(['Regular Calendar','Discretionary Review','Consent Calendar','Items Proposed for Continuance'])].sort_values('date')
heard=p[p.section_group.isin(['Regular Calendar','Discretionary Review'])]
first=heard.groupby('id_parent').date.min().rename('d0'); p=p.join(first,on='id_parent'); p=p[p.d0.notna()]
rows=[]
for pid,q in p.groupby('id_parent'):
    d0=q.d0.iloc[0]; f=q[(q.date==d0)&q.section_group.isin(['Regular Calendar','Discretionary Review'])]; after=q[q.date>d0]; onaft=q[q.date>=d0]
    dec=onaft[onaft.action_final.isin(['approve','approve with conditions','disapprove','withdraw'])]
    fa=f.action_final.dropna()
    r={'id_parent':pid,'d0':d0,'year':d0.year,'is_dr':int((f.section_group=='Discretionary Review').any()),'housing':int(f.housing_kw.max()==1),'demo':int(f.demo_kw.max()==1),'newc':int(f.new_construction_kw.max()==1),
       'rec_num':f.rec_num.min(),'rec_missing':int(f.rec_num.isna().all()),'rec_dr':int((f.rec_dr=='dr').any()),'n_items0':len(f),'prior_cont':int((q.date<d0).sum()),
       'types':'|'.join(sorted(set(f.record_type.dropna()))),'units':np.nanmax([f.txt_units.max(),f.prj_number_of_units_net.max()]) if (f.txt_units.notna().any() or f.prj_number_of_units_net.notna().any()) else np.nan,
       'stories':f.txt_stories.max(),'sqft':f.txt_sqft.max(),'txt_len':f.txt_len.max(),'lat':f.latitude.max(),'lon':f.longitude.max()}
    for k in cc: r[k]=f[k].sum()
    decided0=fa.isin(['approve','approve with conditions','disapprove']).any()
    r['y_notdecided']=int(not decided0); r['y_prolonged']=int(after.date.nunique()>=2)
    r['y_nofinal']=int(len(dec)==0); r['days']=(dec.date.max()-d0).days if len(dec) else np.nan
    r['y_modified']=int(onaft.modif.any() or (onaft.action_dr=='dr').any()); r['y_tookdr']=int((onaft.action_dr=='dr').any()) if r['is_dr'] else np.nan
    r['y_disapprove']=int((dec.action_final=='disapprove').any()) if len(dec) else 0
    rows.append(r)
d=pd.DataFrame(rows); d['signed']=d.n_sup+d.n_opp; d['opp_share']=d.n_opp/d.signed.replace(0,np.nan); d['net_opp']=d.n_opp-d.n_sup
d['y_slow']=((d.days>90)|(d.y_nofinal==1)).astype(int)
for k in ['CUA','DRM','DRP','ENV','PCA','VAR','DNX','OFA','SHD','MAP']: d['rt_'+k]=d.types.str.contains(k).astype(int)
z=pd.read_csv(Z).dropna(subset=['latitude','longitude'])
zs=z[z.homeStatus.isin(['RECENTLY_SOLD','FOR_SALE'])&(z.livingArea>200)&(z.price>50000)].copy(); zs['ppsf']=zs.price/zs.livingArea; zs=zs[zs.ppsf.between(200,4000)]
zr=z[(z.homeStatus=='FOR_RENT')&z.price.between(500,30000)]
m=d.lat.between(37.6,37.9)
for src,val,nm in [(zs,'ppsf','z_ppsf'),(zr,'price','z_rent')]:
    t=BallTree(np.radians(src[['latitude','longitude']].values),metric='haversine'); _,i=t.query(np.radians(d.loc[m,['lat','lon']].values),k=30); d.loc[m,nm]=np.median(src[val].values[i],axis=1)
d=d[d.year<=2023]   # leave follow-up time
print('projects',len(d),'| housing',d.housing.sum(),'| DR',d.is_dr.sum(),'| with comments',(d.n_comments>0).sum(),'| units known',d.units.notna().sum(),'| zillow',d.z_ppsf.notna().sum())
base=['rec_num','rec_missing','rec_dr','is_dr','housing','demo','newc','n_items0','prior_cont']+[x for x in d if x.startswith('rt_')]
size=['units','stories','sqft','txt_len']; com=cc+['opp_share','net_opp']; zil=['z_ppsf','z_rent']
tr=d[d.year<=2016]; te=d[d.year>=2017].copy(); print('train',len(tr),'test',len(te))
rng=np.random.default_rng(0)
def boot(y,a,b,n=1000):
    y=np.asarray(y); out=[]
    for _ in range(n):
        i=rng.integers(0,len(y),len(y))
        if y[i].min()==y[i].max(): continue
        out.append(roc_auc_score(y[i],b[i])-roc_auc_score(y[i],a[i]))
    return np.percentile(out,[2.5,97.5])
res={}
for y,sub in [('y_notdecided',None),('y_slow',None),('y_prolonged',None),('y_nofinal',None),('y_modified',None),('y_tookdr','dr'),('y_disapprove',None)]:
    a,b=(tr,te) if sub is None else (tr[tr.is_dr==1],te[te.is_dr==1])
    print(f'\n### {y}: train rate {a[y].mean():.3f}, test rate {b[y].mean():.3f} (test n {len(b)}, pos {int(b[y].sum())})')
    lr=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=2000)).fit(a[base],a[y]); pb=lr.predict_proba(b[base])[:,1]
    print(f'  baseline LR staff rec+type        AUC {roc_auc_score(b[y],pb):.3f}  PR-AUC {average_precision_score(b[y],pb):.3f}')
    preds={}
    for nm,F in [('GBM base+size',base+size),('GBM base+size+comments',base+size+com),('GBM all +zillow',base+size+com+zil),('GBM comments only',com)]:
        gb=HistGradientBoostingClassifier(max_depth=3,learning_rate=0.04,max_iter=250,l2_regularization=1.0,random_state=0).fit(a[F],a[y]); pr=gb.predict_proba(b[F])[:,1]; preds[nm]=(gb,F,pr)
        print(f'  {nm:32s} AUC {roc_auc_score(b[y],pr):.3f}  PR-AUC {average_precision_score(b[y],pr):.3f}')
    lo,hi=boot(b[y],preds['GBM base+size'][2],preds['GBM base+size+comments'][2]); print(f'  AUC gain from comments over base+size: 95% CI [{lo:+.3f}, {hi:+.3f}]')
    lo,hi=boot(b[y],pb,preds['GBM base+size+comments'][2]); print(f'  AUC gain of full model over LR baseline: 95% CI [{lo:+.3f}, {hi:+.3f}]')
    gb,F,pr=preds['GBM all +zillow']; res[y]=pr if sub is None else None
    pi=permutation_importance(gb,b[F],b[y],scoring='roc_auc',n_repeats=8,random_state=0); print('  top features:',', '.join(f'{F[i]} {pi.importances_mean[i]:.3f}' for i in np.argsort(-pi.importances_mean)[:7]))
# subgroup analysis for y_slow
y='y_slow'; te['p']=res[y]; te['terc']=pd.qcut(te.z_ppsf,3,labels=['low $/sqft','mid','high $/sqft']); te['oppg']=pd.cut(te.n_opp,[-1,0,5,1e9],labels=['0 opp','1-5','6+']); te['kind']=np.where(te.is_dr==1,'DR',np.where(te.housing==1,'housing non-DR','non-housing'))
thr=np.quantile(te.p,0.8)
for gcol in ['terc','kind','oppg']:
    print('\nsubgroups for y_slow by',gcol); print(te.groupby(gcol,observed=True).apply(lambda q:pd.Series({'n':len(q),'rate':q[y].mean(),'AUC':roc_auc_score(q[y],q.p) if q[y].nunique()>1 else np.nan,'flag_rate':(q.p>=thr).mean(),'recall@top20%':((q.p>=thr)&(q[y]==1)).sum()/max(q[y].sum(),1),'mean_pred':q.p.mean()}),include_groups=False).round(3).to_string())
print('\nrates by opposition (all years): '); d['oppg']=pd.cut(d.n_opp,[-1,0,2,5,10,1e9],labels=['0','1-2','3-5','6-10','11+'])
print(d.groupby('oppg',observed=True)[['y_notdecided','y_slow','y_prolonged','y_nofinal','y_modified','y_disapprove']].mean().round(3).assign(n=d.oppg.value_counts()).to_string())
d.to_csv(OUT,index=False)
