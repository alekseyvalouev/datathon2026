import sys,re,pandas as pd,numpy as np
S=sys.argv[1]; sys.path.insert(0,S+'/code')
from voice_lib import *
from voice_occ import *
df=pd.read_parquet(S+'/base/reddit_slim.parquet')
df['scope']=df.community_name.map(scope)
df['month']=df.date_posted.str[:7]
df['title']=df.title.fillna(''); df['description']=df.description.fillna('')
df['t']=(df.title+' . '+df.description).str.slice(0,6000)
df['n_ai']=df.t.map(lambda x:len(AIM_CS.findall(x)))
def lab(t,n):
    if n==0: return 'none'
    ti=t.split(' . ')[0]
    act=actual_match(t)
    if act: return 'actual_displacement'
    if not (AIM_CS.search(ti) or n>=2): return 'none'
    if HIRING_FIRST.search(t): return 'ai_hiring_search'
    if FEAR_STRONG.search(t): return 'fear_anticipation'
    if HIRING2.search(t): return 'ai_hiring_search'
    if FEAR.search(t): return 'fear_anticipation'
    if TOOL2.search(t): return 'ai_tool_at_work'
    return 'none'
cand=(df.n_ai>0)
df['ai_cat']='none'
df.loc[cand,'ai_cat']=[lab(t,n) for t,n in zip(df.t[cand],df.n_ai[cand])]
df['ai_work']=df.ai_cat!='none'
# occupation for displacement/fear posts
ex=df.ai_cat.isin(['actual_displacement','fear_anticipation'])
df['occ_self']=None; df['occ_first']=None; df['occ_any']=None
df.loc[ex,'occ_self']=df.t[ex].map(own_class)
df.loc[ex,'occ_first']=df.t[ex].map(first_named)
pr=df.t[ex].map(primary)
df['occ_primary']=None; df['occ_basis']=None
df.loc[ex,'occ_primary']=pr.map(lambda x:x[0]); df.loc[ex,'occ_basis']=pr.map(lambda x:x[1])
df.loc[ex,'occ_any']=df.t[ex].map(lambda x:'|'.join(any_classes(x)))
# job search friction (all posts, not only AI)
T=df.t
ghost=T.str.contains(r"ghost(?:ed|ing|s)?\b|ghost jobs?|fake (?:job|listing|posting)s?|fake job postings?|job (?:posting|listing)s? (?:that|are) (?:fake|not real)",case=False,regex=True)
vol=T.str.contains(r"\b\d{2,5}\+? (?:job )?(?:applications?|applied)|applied (?:to|for) (?:over |more than |about |around )?\d{2,5}|(?:hundreds|thousands) of (?:applications?|jobs|resumes)|sent out (?:over |about )?\d{2,5}|\d{2,5}\+? applicants?|(?:hundreds|thousands) of applicants?|application volume|flood(?:ed|ing)? (?:of|with) applications?",case=False,regex=True)
aiscr=T.str.contains(r"\bATS\b|applicant tracking|ai (?:screen|interview|recruiter|resume|filter|hiring|rejection)|auto-?reject\w*|resume (?:scanner|screen|filter|parser)|screened by (?:an? )?(?:ai|bot|algorithm)|(?:ai|bot|algorithm|automated)[^.]{0,40}(?:screen|filter|reject)\w*|hirevue|one-way video interview",case=False,regex=True)
entry=T.str.contains(r"entry.level|new grad\w*|recent grad\w*|fresh grad\w*|fresher|junior (?:role|position|dev|engineer|level)|internships?\b|no experience|first job|graduat\w+ (?:in|from|with|\d)|class of 20\d\d|college grad\w*|\bgen ?z\b",case=False,regex=True)
jobsearch=T.str.contains(r"job (?:search|hunt|market)|job hunting|applying (?:to|for)|applications?|resume|interview|rejected|rejection|unemploy|laid off|layoff",case=False,regex=True)
df['f_ghost']=ghost; df['f_volume']=vol; df['f_ai_screen']=aiscr; df['f_entry']=entry; df['f_jobsearch']=jobsearch
df['f_friction_any']=ghost|vol|aiscr
df.drop(columns=['t']).to_parquet(S+'/base/_reddit_all_labeled.parquet')
df['t']=df.t
df.to_pickle(S+'/base/_reddit_all_labeled_t.pkl')
print(pd.crosstab(df.scope,df.ai_cat).to_string())
