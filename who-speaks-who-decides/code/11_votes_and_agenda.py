import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, re, pandas as pd, numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
pd.set_option('display.width',260); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',200)
P=sys.argv[1]
it=pd.read_csv(P+'/items.csv.gz',low_memory=False); mt=pd.read_csv(P+'/meetings.csv'); c=pd.read_csv(P+'/comments.csv',low_memory=False)
it['date']=pd.to_datetime(it.meeting_date); it['year']=it.date.dt.year; it=it[it.year>=2005].copy()
def names(s):
    if pd.isna(s): return []
    s=re.sub(r'\(.*?\)','',str(s)); s=re.split(r'\s{2,}|\n|ADJOURN|MOTION|RESOLUTION|ABSENT|RECUSED|NAYES|EXCUSED',s)[0]
    if re.match(r'^\s*(none|n/a|-)?\s*$',s,re.I): return []
    return [x.strip().title() for x in re.split(r',|;| and |&',s) if 1<len(x.strip())<25 and re.match(r"^[A-Za-z .'\-]+$",x.strip())]
it['ay']=it.AYES.map(names); it['na']=it.NAYES.map(names); it['n_ay']=it.ay.str.len(); it['n_na']=it.na.str.len()
v=it[(it.n_ay>=3)&(it.n_ay+it.n_na<=7)].copy(); v['split']=(v.n_na>0).astype(int); v['close']=((v.n_na>=2)|(v.n_ay<=4)&(v.n_na>=1)).astype(int)
print('items with a recorded vote',len(v),'| split',v.split.mean().round(3),'| vote patterns top:',(v.n_ay.astype(str)+'-'+v.n_na.astype(str)).value_counts().head(8).to_dict())
c=c[c.is_staff!=1]; g=c.groupby('item_id').position; v['opp']=v.item_id.map(g.apply(lambda s:(s=='oppose').sum())).fillna(0); v['sup']=v.item_id.map(g.apply(lambda s:(s=='support').sum())).fillna(0)
dec=v[v.section_group.isin(['Regular Calendar','Discretionary Review'])&v.action_final.isin(['approve','approve with conditions','disapprove'])].copy()
print('decided regular+DR items with votes',len(dec),'split rate',dec.split.mean().round(3))
print('\nsplit-vote rate by year:'); print(dec.groupby('year').split.agg(['size','mean']).round(3).T.to_string())
dec['oppb']=pd.cut(dec.opp,[-1,0,2,5,10,1e9],labels=['0','1-2','3-5','6-10','11+']); print('\nsplit rate by opposing comments:'); print(dec.groupby('oppb',observed=True).agg(n=('split','size'),split=('split','mean'),two_plus_nays=('n_na',lambda s:(s>=2).mean()),disapproved=('action_final',lambda s:(s=='disapprove').mean())).round(3).to_string())
dec['supb']=pd.cut(dec.sup,[-1,0,2,5,10,1e9],labels=['0','1-2','3-5','6-10','11+']); print(pd.crosstab(dec.oppb,dec.supb,values=dec.split,aggfunc='mean').round(2).to_string())
print('\nsplit rate by case type:'); print(dec.groupby('record_type').split.agg(['size','mean']).query('size>=60').round(3).sort_values('mean',ascending=False).to_string())
for k in ['housing_kw','demo_kw','new_construction_kw','adu_kw']: print(k,dec.groupby(k).split.agg(['size','mean']).round(3).to_dict('index'))
dec['bonus']=dec.item_text.fillna('').str.lower().str.contains('density bonus|home-sf'); print('density bonus:',dec.groupby('bonus').split.agg(['size','mean']).round(3).to_dict('index'))
print('staff rec vs split:',dec.groupby(dec.rec_final.fillna('NA')).split.agg(['size','mean']).round(3).to_dict('index'))
# predict split vote
dec['n_c']=dec.opp+dec.sup; dec['opp_share']=dec.opp/dec.n_c.replace(0,np.nan); dec['is_dr']=(dec.section_group=='Discretionary Review').astype(int)
for k in ['CUA','DRM','DRP','ENV','PCA','VAR','DNX']: dec['rt_'+k]=(dec.record_type==k).astype(int)
base=['rec_num','is_dr','housing_kw','demo_kw','new_construction_kw','bonus']+[x for x in dec if x.startswith('rt_')]; com=['opp','sup','n_c','opp_share']
tr=dec[dec.year<=2017]; te=dec[dec.year>=2018]; print(f'\npredict split vote: train {len(tr)} test {len(te)} (test rate {te.split.mean():.3f}, n pos {te.split.sum()})')
rng=np.random.default_rng(0); pr={}
for nm,F in [('base (staff rec + type)',base),('base + comments',base+com),('comments only',com)]:
    m=HistGradientBoostingClassifier(max_depth=3,learning_rate=0.05,max_iter=200,random_state=0).fit(tr[F].astype(float),tr.split); p=m.predict_proba(te[F].astype(float))[:,1]; pr[nm]=p; print(f'  {nm:26s} AUC {roc_auc_score(te.split,p):.3f}  PR-AUC {average_precision_score(te.split,p):.3f}')
y=te.split.values; dd=[]
for _ in range(1000):
    i=rng.integers(0,len(y),len(y))
    if y[i].min()!=y[i].max(): dd.append(roc_auc_score(y[i],pr['base + comments'][i])-roc_auc_score(y[i],pr['base (staff rec + type)'][i]))
print('  AUC gain from comments 95% CI',np.percentile(dd,[2.5,97.5]).round(3))
# commissioner-level
rows=[]
for r in dec.itertuples():
    for n in r.ay: rows.append((n,r.year,1,r.split,r.action_final,r.housing_kw,r.item_id))
    for n in r.na: rows.append((n,r.year,0,r.split,r.action_final,r.housing_kw,r.item_id))
cv=pd.DataFrame(rows,columns=['name','year','aye','split','action','housing','item_id'])
cnt=cv.name.value_counts(); cv=cv[cv.name.isin(cnt[cnt>=150].index)]
cv['pro']=np.where(cv.action=='disapprove',1-cv.aye,cv.aye)  # voted for the project going ahead
s=cv.groupby('name').agg(votes=('aye','size'),first=('year','min'),last=('year','max'),dissent_rate=('aye',lambda x:1-x.mean()),split_items=('split','sum')).join(cv[cv.split==1].groupby('name').pro.mean().rename('pro_project_share_on_split_votes')).round(3).sort_values('pro_project_share_on_split_votes')
print('\ncommissioners with 150+ recorded votes (public officials, official votes):'); print(s.to_string())
print('\n== agenda position and meeting length')
rc=it[it.section_group.isin(['Regular Calendar','Discretionary Review'])&it.action_final.notna()].copy(); rc['pos']=rc.groupby('meeting_date').cumcount()+1; rc['n_in']=rc.groupby('meeting_date').item_id.transform('size'); rc['rel']=rc.pos/rc.n_in
rc['cont']=(rc.action_final=='continuance').astype(int); rc['opp']=rc.item_id.map(g.apply(lambda s:(s=='oppose').sum())).fillna(0); rc['ncom']=rc.item_id.map(c.groupby('item_id').size()).fillna(0)
rc=rc[rc.n_in>=6]; rc['q']=pd.cut(rc.rel,[0,.25,.5,.75,1.0],labels=['first quarter','second','third','last quarter'])
print(rc.groupby('q',observed=True).agg(n=('cont','size'),continued=('cont','mean'),disapproved=('action_final',lambda s:(s=='disapprove').mean()),dr_share=('section_group',lambda s:(s=='Discretionary Review').mean()),mean_comments=('ncom','mean')).round(3).to_string())
nd=rc[rc.section_group=='Regular Calendar']; print('regular calendar only:'); print(nd.groupby('q',observed=True).agg(n=('cont','size'),continued=('cont','mean'),mean_comments=('ncom','mean')).round(3).to_string())
mt['st']=pd.to_datetime(mt.start_time,format='%H:%M',errors='coerce'); mt['en']=pd.to_datetime(mt.end_time,format='%H:%M',errors='coerce'); mt['hrs']=((mt.en-mt.st).dt.total_seconds()/3600); mt.loc[mt.hrs<0,'hrs']+=24
print('meeting length known for',mt.hrs.notna().sum(),'of',len(mt),'| median hours',mt.hrs.median(),'| by period:',mt.assign(y=pd.to_datetime(mt.meeting_date).dt.year).groupby(pd.cut(pd.to_datetime(mt.meeting_date).dt.year,[2004,2009,2014,2019,2022,2026])).hrs.agg(['count','median','mean']).round(2).to_dict('index'))
rc=rc.merge(mt[['meeting_date','hrs','n_comments']],on='meeting_date',how='left'); rc['long']=pd.cut(rc.hrs,[0,4,6,8,24],labels=['<4h','4-6h','6-8h','8h+'])
print(rc.groupby('long',observed=True).agg(n=('cont','size'),continued=('cont','mean'),disapproved=('action_final',lambda s:(s=='disapprove').mean())).round(3).to_string())
lastq=rc[rc.q=='last quarter']; print('last-quarter items by meeting length:',lastq.groupby('long',observed=True).cont.agg(['size','mean']).round(3).to_dict('index'))
X=pd.DataFrame({'rel':rc.rel,'log_com':np.log1p(rc.ncom),'is_dr':(rc.section_group=='Discretionary Review').astype(int),'hrs':rc.hrs.fillna(rc.hrs.median()),'year':rc.year-2015}); o=[]
for _ in range(300):
    i=rng.integers(0,len(rc),len(rc)); o.append(LogisticRegression(C=10,max_iter=2000).fit(X.iloc[i],rc.cont.values[i]).coef_[0])
o=np.array(o); print('continuance logit OR:',{k:(round(float(np.exp(np.median(o[:,j]))),2),[round(float(np.exp(np.percentile(o[:,j],2.5))),2),round(float(np.exp(np.percentile(o[:,j],97.5))),2)]) for j,k in enumerate(X.columns)})
