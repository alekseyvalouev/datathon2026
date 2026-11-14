import sys,numpy as np,pandas as pd,json
S=sys.argv[1]
def wilson(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return c-h,c+h
rows=[ # measure, checked, correct
('reddit_relevance_actual',20,20),('reddit_cat_actual',20,14),
('reddit_relevance_fear',28,24),('reddit_cat_fear',28,24),
('reddit_relevance_tool',28,26),('reddit_cat_tool',28,18),
('reddit_relevance_hiring',28,27),('reddit_cat_hiring',28,26),
('reddit_uniform_relevance',70,63),('reddit_uniform_category',70,56),
('reddit_ghost',24,24),('reddit_volume',24,23),('reddit_ai_screen',24,21),('reddit_entry',24,17),
('reddit_occ_highconf',45,36),('reddit_occ_body_lowconf',26,9),
('gd_title_class',100,92),
('gd_layoff',32,29),('gd_staffing',35,32),('gd_workload',32,30),('gd_ai_mention',35,33),('gd_ai_threat_strict',35,20),('gd_ai_threat_halfcredit',35,23.5),('gd_offshore_displace',32,28)]
out=[]
for m,n,k in rows:
    lo,hi=wilson(k,n); out.append((m,n,k,k/n,lo,hi))
df=pd.DataFrame(out,columns=['measure','n_checked','n_correct','precision','ci_lo','ci_hi']); 
# prevalence-weighted reddit precision
prev={'actual':20,'fear':254,'tool':81,'hiring':569}
w=lambda pre:sum(prev[c]*df.set_index('measure').loc[f'{pre}_{c}','precision'] for c in prev)/sum(prev.values())
rel=sum(prev[c]*df.set_index('measure').loc[f'reddit_relevance_{c}','precision'] for c in prev)/sum(prev.values())
cat=sum(prev[c]*df.set_index('measure').loc[f'reddit_cat_{c}','precision'] for c in prev)/sum(prev.values())
df.loc[len(df)]=['reddit_relevance_weighted(924 posts)',104,np.nan,rel,np.nan,np.nan]
df.loc[len(df)]=['reddit_category_weighted(924 posts)',104,np.nan,cat,np.nan,np.nan]
df.to_csv(S+'/base/voice_precision_handchecks.csv',index=False)
print(df.round(3).to_string())
