import sys,re,pandas as pd
S=sys.argv[1]; sys.path.insert(0,S+'/code')
from voice_lib import *
df=pd.read_pickle(S+'/base/_reddit_all_labeled_t.pkl')
sc=sys.argv[2].split(','); seed=int(sys.argv[3]); n=int(sys.argv[4])
cats=sys.argv[5].split(',') if len(sys.argv)>5 else None
d=df[df.scope.isin(sc)&df.ai_work]
if cats: d=d[d.ai_cat.isin(cats)]
d=d.sample(min(n,len(d)),random_state=seed)
for k,(i,r) in enumerate(d.iterrows()):
    t=r.t; m=(actual_match(t) if r.ai_cat=='actual_displacement' else None) or FEAR_STRONG.search(t) or HIRING2.search(t) or AIM_CS.search(t)
    j=m.start() if m else 0
    print(f"[{k}] <{r.ai_cat}> {r.community_name} | {r.title[:100]} || {t[max(0,j-120):j+200]}".replace('\n',' '),'\n')
