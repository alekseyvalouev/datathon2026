import sys,re,pandas as pd
S=sys.argv[1]
df=pd.read_pickle(S+'/base/_reddit_all_labeled_t.pkl'); w=df[df.scope=='WORK_GEN']
P={'f_ghost':r"ghost(?:ed|ing|s)?\b|ghost jobs?|fake (?:job|listing|posting)s?|fake job postings?|job (?:posting|listing)s? (?:that|are) (?:fake|not real)",
'f_volume':r"\b\d{2,5}\+? (?:job )?(?:applications?|applied)|applied (?:to|for) (?:over |more than |about |around )?\d{2,5}|(?:hundreds|thousands) of (?:applications?|jobs|resumes)|sent out (?:over |about )?\d{2,5}|\d{2,5}\+? applicants?|(?:hundreds|thousands) of applicants?|application volume|flood(?:ed|ing)? (?:of|with) applications?",
'f_ai_screen':r"\bATS\b|applicant tracking|ai (?:screen|interview|recruiter|resume|filter|hiring|rejection)|auto-?reject\w*|resume (?:scanner|screen|filter|parser)|screened by (?:an? )?(?:ai|bot|algorithm)|(?:ai|bot|algorithm|automated)[^.]{0,40}(?:screen|filter|reject)\w*|hirevue|one-way video interview",
'f_entry':r"entry.level|new grad\w*|recent grad\w*|fresh grad\w*|fresher|junior (?:role|position|dev|engineer|level)|internships?\b|no experience|first job|graduat\w+ (?:in|from|with|\d)|class of 20\d\d|college grad\w*|\bgen ?z\b"}
for f,p in P.items():
    d=w[w[f]].sample(24,random_state=4); print('=====',f)
    for k,(i,r) in enumerate(d.iterrows()):
        m=re.search(p,r.t,re.I); j=m.start()
        print(f'[{k}]',r.t[max(0,j-90):j+110].replace('\n',' '))
