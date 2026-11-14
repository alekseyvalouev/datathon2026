import sys,pandas as pd,numpy as np
S=sys.argv[1]
df=pd.read_pickle(S+'/base/_reddit_all_labeled_t.pkl')
pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
w=df[df.scope=='WORK_GEN']
print(pd.crosstab(w.month,w.community_name))
g=w.groupby('month').agg(n=('post_id','size'),ai=('ai_work','sum'),act=('ai_cat',lambda s:(s=='actual_displacement').sum()),fear=('ai_cat',lambda s:(s=='fear_anticipation').sum()),hire=('ai_cat',lambda s:(s=='ai_hiring_search').sum()),tool=('ai_cat',lambda s:(s=='ai_tool_at_work').sum()))
g['share']=g.ai/g.n
print(g)
b=df[df.scope=='BAY'].groupby('month').agg(n=('post_id','size'),ai=('ai_work','sum')); print(b.T)
print(df.groupby('scope').date_posted.agg(['min','max']))
