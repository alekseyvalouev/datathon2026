import sys,re,pandas as pd
sys.path.insert(0,sys.argv[1]+'/code')
from voice_lib import *
S=sys.argv[1]
df=pd.read_parquet(S+'/base/reddit_slim.parquet')
df['scope']=df.community_name.map(scope)
print(df.scope.value_counts())
df['t']=df.title.fillna('')+' . '+df.description.fillna('')
df['t']=df.t.str.slice(0,6000)
s=df[df.scope.isin(['BAY','WORK_GEN','JOBS_OTHER_NICHE_OR_INTL','GENERAL_OTHER'])]
a=s.t.str.contains(AI_UP)|s.t.str.contains(r'chat ?gpt|artificial intelligence|openai|\bLLMs?\b|generative ai|claude\b',case=False,regex=True)
j=s.t.str.contains(JOBCTX)
c=s[a&j]
print(c.scope.value_counts())
c.to_pickle(S+'/base/_cand.pkl')
