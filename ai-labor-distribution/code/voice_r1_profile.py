import pandas as pd, sys
f='/Users/alekseyvalouev/Desktop/Datathon/reddit_posts-003.csv'
S=sys.argv[1]
cols=['post_id','title','description','date_posted','community_name','num_comments','num_upvotes','tag']
out=[]
n=0
for ch in pd.read_csv(f,usecols=cols,chunksize=20000,dtype=str,engine='c',on_bad_lines='skip'):
    out.append(ch); n+=len(ch)
df=pd.concat(out); print(len(df))
df.to_parquet(S+'/base/reddit_slim.parquet')
print(df.community_name.value_counts().head(60))
print(df.community_name.nunique())
df['m']=df.date_posted.str[:7]
print(df.m.value_counts().sort_index())
