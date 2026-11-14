import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, re, pandas as pd, numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, make_union
from sklearn.metrics import f1_score, accuracy_score, classification_report
P=sys.argv[1]
c=pd.read_csv(P+'/comments.csv',low_memory=False); it=pd.read_csv(P+'/items.csv.gz',low_memory=False,usecols=['item_id','section_group','housing_kw','record_type'])
s=c[(c.position_source=='stenographer')&c.text.notna()&(c.is_staff!=1)].merge(it,on='item_id',how='left')
s['text']=s.text.astype(str).str.replace(r'\s+',' ',regex=True).str.strip()
s['year']=pd.to_datetime(s.meeting_date).dt.year; s['nw']=s.text.str.split().str.len()
print('n',len(s),'dup-text share',s.text.duplicated().mean().round(3))
tr=s[s.year<=2019]; te=s[s.year>=2021]   # 2020 left out as gap
print('train',len(tr),'test',len(te)); print(te.position.value_counts(normalize=True).round(3).to_dict())
SUP=r'\b(support|in favor|favor of|approve|urge approval|yes on)'; OPP=r'\b(oppos|against|object|deny|disapprov|concern|take dr|appeal)'
def kw(t):
    t=t.lower(); a=bool(re.search(SUP,t)); b=bool(re.search(OPP,t))
    return 'support' if a and not b else 'oppose' if b and not a else 'support'
def rep(name,y,p): print(f'{name:38s} acc {accuracy_score(y,p):.3f}  macroF1 {f1_score(y,p,average="macro"):.3f}')
y=te.position
rep('majority',y,['support']*len(te)); rep('keyword rule',y,te.text.map(kw))
def model(): return make_pipeline(make_union(TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True),TfidfVectorizer(analyzer='char_wb',ngram_range=(2,5),min_df=3,sublinear_tf=True)),LogisticRegression(C=4,max_iter=2000,class_weight='balanced'))
m=model().fit(tr.text,tr.position); p=m.predict(te.text); rep('tfidf+LR full text',y,p); print(classification_report(y,p,digits=3))
te=te.assign(pred=p,ok=(p==y))
STRIP=r'(?i)\b(support\w*|oppos\w*|in favor|favor\w*|against|approv\w*|disapprov\w*|object\w*|deny|denial|concern\w*)\b'
m2=model().fit(tr.text.str.replace(STRIP,' ',regex=True),tr.position); p2=m2.predict(te.text.str.replace(STRIP,' ',regex=True)); rep('tfidf+LR stance words stripped',y,p2)
print('test rows with explicit stance word',te.text.str.contains(STRIP,regex=True).mean().round(3))
te['len']=pd.cut(te.nw,[0,2,5,15,50,1e9],labels=['1-2','3-5','6-15','16-50','50+'])
for g in ['len','section_group','housing_kw','year']:
    r=te.groupby(g,observed=True).apply(lambda d: pd.Series({'n':len(d),'acc':d.ok.mean(),'macroF1':f1_score(d.position,d.pred,average='macro'),'opp_share':(d.position=='oppose').mean()}),include_groups=False)
    print('\nby',g); print(r[r.n>=150].round(3).to_string())
longm=te.nw>=6
rep('LONG(>=6w) majority',y[longm],['support']*longm.sum()); rep('LONG keyword',y[longm],te.text[longm].map(kw)); rep('LONG tfidf+LR',y[longm],p[longm]); rep('LONG stripped',y[longm],p2[longm])
if SHOW: print('\nfailures:'); print(te[~te.ok&(te.nw.between(6,40))][['position','pred','text']].sample(8,random_state=3).assign(text=lambda d:d.text.str[:150]).to_string(index=False))
# cross-channel: emails with LLM labels
e=c[(c.channel=='email')].copy(); e=e[e.is_campaign!=1]
pe=m.predict(e.text.astype(str)); print('\nemail (non-campaign) n',len(e),'agreement with LLM label acc',round(accuracy_score(e.position,pe),3),'macroF1',round(f1_score(e.position,pe,average='macro'),3)); print(pd.crosstab(e.position,pe))
