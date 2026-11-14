import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, pandas as pd, numpy as np
from sklearn.neighbors import BallTree
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, average_precision_score
P,Z=sys.argv[1],sys.argv[2]
c=pd.read_csv(P+'/comments.csv',low_memory=False); it=pd.read_csv(P+'/items.csv.gz',low_memory=False)
z=pd.read_csv(Z); zs=z[z.homeStatus.isin(['RECENTLY_SOLD','FOR_SALE'])&(z.livingArea>200)&(z.price>50000)].copy(); zs['ppsf']=zs.price/zs.livingArea
zs=zs[zs.ppsf.between(200,4000)]; print('zillow sale rows for ppsf',len(zs))
zr=z[(z.homeStatus=='FOR_RENT')&z.price.between(500,30000)].copy()
def knn_med(src,val,pts,k=30):
    src=src.dropna(subset=['latitude','longitude',val]); t=BallTree(np.radians(src[['latitude','longitude']].values),metric='haversine'); d,i=t.query(np.radians(pts),k=k)
    return np.median(src[val].values[i],axis=1), d[:,-1]*6371000
c=c[c.is_staff!=1]
g=c.groupby('item_id'); f=pd.DataFrame({'n_comments':g.size(),'n_sup':g.position.apply(lambda s:(s=='support').sum()),'n_opp':g.position.apply(lambda s:(s=='oppose').sum()),'n_neu':g.position.apply(lambda s:(s=='neutral').sum()),
  'n_nhood':g.role_group.apply(lambda s:(s=='Neighborhood Association').sum()),'n_projteam':g.role_group.apply(lambda s:(s=='Project Team').sum()),'n_email':g.channel.apply(lambda s:(s=='email').sum())})
d=it.merge(f,left_on='item_id',right_index=True,how='inner')
d['year']=pd.to_datetime(d.meeting_date).dt.year
d=d[d.section_group.isin(['Regular Calendar','Discretionary Review'])&d.action_final.isin(['approve','approve with conditions','disapprove','continuance'])&(d.year>=2005)]
d['signed']=d.n_sup+d.n_opp; d['opp_share']=d.n_opp/d.signed.replace(0,np.nan); d['net_opp']=d.n_opp-d.n_sup
print('modelling items',len(d),'with coords',d.latitude.notna().sum(),'housing',int(d.housing_kw.sum()))
m=d.latitude.notna()&d.latitude.between(37.6,37.9)
v,dist=knn_med(zs,'ppsf',d.loc[m,['latitude','longitude']].values); d.loc[m,'z_ppsf']=v; d.loc[m,'z_dist30']=dist
v2,_=knn_med(zr,'price',d.loc[m,['latitude','longitude']].values); d.loc[m,'z_rent']=v2
print('zillow kNN radius to 30th sale (m): median',np.median(dist).round(0),'p90',np.quantile(dist,.9).round(0)); print(d[['z_ppsf','z_rent']].describe().round(0).T)
# descriptive: opposition by neighbourhood price tercile, housing items with signed comments
h=d[(d.housing_kw==1)&d.z_ppsf.notna()&(d.signed>0)].copy(); h['tercile']=pd.qcut(h.z_ppsf,3,labels=['low $/sqft','mid','high $/sqft'])
print(h.groupby('tercile',observed=True).agg(items=('item_id','size'),mean_comments=('n_comments','mean'),mean_opp=('n_opp','mean'),opp_share=('opp_share','mean'),pooled_opp=('n_opp','sum'),pooled_signed=('signed','sum'),disapprove=('action_final',lambda s:(s=='disapprove').mean()),contin=('action_final',lambda s:(s=='continuance').mean())).assign(pooled_share=lambda x:x.pooled_opp/x.pooled_signed).round(3).to_string())
print('spearman opp_share~ppsf',h[['opp_share','z_ppsf']].corr(method='spearman').iloc[0,1].round(3),' n_opp~ppsf',h[['n_opp','z_ppsf']].corr(method='spearman').iloc[0,1].round(3))
# models
d['y_cont']=(d.action_final=='continuance').astype(int); d['y_dis']=(d.action_final=='disapprove').astype(int)
d['y_adverse']=((d.action_final=='disapprove')|((d.section_group=='Discretionary Review')&(d.action_dr=='dr'))).astype(int)
d['rec_num_f']=d.rec_num; d['is_dr']=(d.section_group=='Discretionary Review').astype(int)
for k in ['CUA','DRM','DRP','ENV','PCA','VAR']: d['rt_'+k]=(d.record_type==k).astype(int)
base=['rec_num_f','is_dr']+[x for x in d if x.startswith('rt_')]+['housing_kw','demo_kw','new_construction_kw','prj_number_of_units_net']
com=['n_comments','n_sup','n_opp','n_neu','opp_share','net_opp','n_nhood','n_projteam','n_email']; zil=['z_ppsf','z_rent']
tr=d[d.year<=2018]; te=d[d.year>=2019]; print('train',len(tr),'test',len(te))
for y in ['y_cont','y_dis','y_adverse']:
    print(f'\n{y}: test base rate {te[y].mean():.3f} (n pos {te[y].sum()})')
    lr=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=1000)).fit(tr[base],tr[y]); pb=lr.predict_proba(te[base])[:,1]
    print(f'  baseline staff-rec+type LR   AUC {roc_auc_score(te[y],pb):.3f}  PR-AUC {average_precision_score(te[y],pb):.3f}')
    for nm,F in [('+comments',base+com),('+comments+zillow',base+com+zil),('comments only',com)]:
        gb=HistGradientBoostingClassifier(max_depth=4,learning_rate=0.05,max_iter=300,random_state=0).fit(tr[F],tr[y]); p=gb.predict_proba(te[F])[:,1]
        print(f'  GBM {nm:22s} AUC {roc_auc_score(te[y],p):.3f}  PR-AUC {average_precision_score(te[y],p):.3f}')
d.to_csv(sys.argv[3],index=False)
