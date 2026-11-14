import sys,re,pandas as pd,numpy as np
sys.path.insert(0,sys.argv[1]+'/code')
from voice_lib import *
S=sys.argv[1]
c=pd.read_pickle(S+'/base/_cand.pkl')
def lab(t):
    n=len(AIM_CS.findall(t))
    if n==0: return 'no_ai'
    ti=t.split(' . ')[0]
    if not (AIM_CS.search(ti) or n>=2): return 'single_mention'
    if ACTUAL2.search(t): return 'actual_displacement'
    if HIRING2.search(t): return 'ai_hiring_search'
    if FEAR.search(t): return 'fear_anticipation'
    if TOOL2.search(t): return 'ai_tool_at_work'
    return 'weak_other'
c['lab']=c.t.map(lab)
print(pd.crosstab(c.scope,c.lab).to_string())
c.to_pickle(S+'/base/_cand2.pkl')
def snip(t):
    m=AI_UP.search(t) or re.search(r'chat ?gpt|artificial intelligence|openai|llm|generative ai|claude',t,re.I)
    i=m.start() if m else 0
    return t[max(0,i-150):i+250].replace('\n',' ')
if len(sys.argv)>2:
    seed=int(sys.argv[2]); n=int(sys.argv[3])
    sub=c[c.scope.isin(['BAY','WORK_GEN'])].sample(n,random_state=seed)
    for k,(i,r) in enumerate(sub.iterrows()):
        print(f"[{k}] {r.lab} | {r.community_name} | T: {r.title[:110]} || {snip(r.t)}\n")
