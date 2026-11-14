import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, re, pandas as pd, numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import f1_score, accuracy_score
from scipy.sparse import hstack, csr_matrix
P=sys.argv[1]
c=pd.read_csv(P+'/comments.csv',low_memory=False); it=pd.read_csv(P+'/items.csv.gz',low_memory=False,usecols=['item_id','section_group','record_type','item_text','housing_kw','prelim_rec'])
s=c[(c.position_source=='stenographer')&c.text.notna()&(c.is_staff!=1)].merge(it,on='item_id',how='left')
s['text']=s.text.astype(str).str.replace(r'\s+',' ',regex=True).str.strip(); s['year']=pd.to_datetime(s.meeting_date).dt.year
s['ctx']=s.item_text.fillna('').str.replace(r'\s+',' ',regex=True).str[:1500]; s['role']=s.role_long.fillna('none'); s['sec']=s.section_group.fillna('NA'); s['rt']=s.record_type.fillna('NA')
s['nw']=s.text.str.split().str.len(); s['order']=s.speaker_order.fillna(0).clip(0,40)
# neighbours' stance on same item is NOT used (would leak labels)
tr=s[s.year<=2019]; te=s[s.year>=2021].copy(); y=te.position; print('train',len(tr),'test',len(te))
def rep(n,p): print(f'{n:46s} acc {accuracy_score(y,p):.3f}  macroF1 {f1_score(y,p,average="macro"):.3f}')
tv1=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True); tv2=TfidfVectorizer(analyzer='char_wb',ngram_range=(2,5),min_df=3,sublinear_tf=True); tc=TfidfVectorizer(ngram_range=(1,2),min_df=5,max_features=40000,sublinear_tf=True,stop_words='english')
A1=hstack([tv1.fit_transform(tr.text),tv2.fit_transform(tr.text)]).tocsr(); B1=hstack([tv1.transform(te.text),tv2.transform(te.text)]).tocsr()
oh=OneHotEncoder(handle_unknown='ignore'); A2=oh.fit_transform(tr[['role','sec','rt']]); B2=oh.transform(te[['role','sec','rt']])
A3=tc.fit_transform(tr.ctx)*0.5; B3=tc.transform(te.ctx)*0.5
num=lambda d: csr_matrix(np.c_[np.log1p(d.nw),np.log1p(d.order)])
def fit(A,B,C=4): return LogisticRegression(C=C,max_iter=3000,class_weight='balanced').fit(A,tr.position).predict(B)
rep('majority',['support']*len(te))
p1=fit(A1,B1); rep('comment text only (previous model)',p1)
p2=fit(hstack([A1,A2]).tocsr(),hstack([B1,B2]).tocsr()); rep('+ speaker role, calendar section, case type',p2)
p3=fit(hstack([A1,A2,A3,num(tr)]).tocsr(),hstack([B1,B2,B3,num(te)]).tocsr()); rep('+ project description text, length, order',p3)
p4=fit(hstack([A2,A3,num(tr)]).tocsr(),hstack([B2,B3,num(te)]).tocsr()); rep('context only, NO comment text',p4)
p5=fit(A2,B2); rep('role + section + case type only',p5)
te['p']=p3; te['ok']=te.p==y
for gcol in ['sec','role']:
    r=te.groupby(gcol).apply(lambda d:pd.Series({'n':len(d),'acc':d.ok.mean(),'macroF1':f1_score(d.position,d.p,average='macro')}),include_groups=False); print('\nby',gcol); print(r[r.n>=60].round(3).sort_values('n',ascending=False).head(10).to_string())
te['len']=pd.cut(te.nw,[0,2,5,15,1e9],labels=['1-2 words','3-5','6-15','16+']); print(te.groupby('len',observed=True).apply(lambda d:pd.Series({'n':len(d),'acc_text_only':(p1[te.index.get_indexer(d.index)]==d.position).mean(),'acc_full':d.ok.mean()}),include_groups=False).round(3).to_string())
# two-class version (drop neutral)
m=te.position!='neutral'; trm=tr.position!='neutral'
pb=LogisticRegression(C=4,max_iter=3000,class_weight='balanced').fit(hstack([A1,A2,A3,num(tr)]).tocsr()[trm.values],tr.position[trm]).predict(hstack([B1,B2,B3,num(te)]).tocsr()[m.values])
print('\nsupport vs oppose only: n',int(m.sum()),'acc',round(accuracy_score(y[m],pb),3),'macroF1',round(f1_score(y[m],pb,average='macro'),3),'| majority acc',round((y[m]=='support').mean(),3))
