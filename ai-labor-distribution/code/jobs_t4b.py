import sys,re;sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
from jobs_lib import *
t=pd.read_pickle(B+'jobs_aitrainer_prefix.pkl')
u=t[t.prefix_cls.isna()].copy()
rules=[('EXPOSED_like_analyst',r'economic analyst|credit analyst|risk analyst|venture capital|pricing analyst|corporate development|actuar|customer specialist|closer'),
 ('TECH_like',r'developer|application engineer|embedded|predictive model|decision scientist|detection engineer|simulation engineer|product analyst|experimentation'),
 ('QUANT_stat',r'quantitative|statistic|econom(ist|etric)|forecast'),
 ('FINANCE_SALES',r'trading|banker|trader'),
 ('SCIENCE_research',r'physic|chem|neuro|astro|geo|scientist|researcher')]
def m(p):
    for n,r in rules:
        if re.search(r,p,re.I): return n
    return 'UNMAPPED'
u['hand']=u.prefix.map(m);print(u.hand.value_counts());print(u[u.hand=='UNMAPPED'].prefix.value_counts())
t['bucket']=t.prefix_cls
t.loc[u.index,'bucket']=u.hand
EXPO=['CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED','LEGAL_PROF','EXPOSED_like_analyst']
POSB=['SOFTWARE_ENG','AI_PRODUCER','DATA_ENG_ANALYTICS','TECH_like']
def top(b):
    return 'EXPOSED(clerical/support/prof/legal + analyst-like)' if b in EXPO else ('AI_POSITIONED(+tech-like)' if b in POSB else ('QUANT_stat (technical-quant, ambiguous)' if b=='QUANT_stat' else 'OTHER (engineering, science, education, finance/sales, mgmt, design)'))
t['top']=t.bucket.map(top)
out=[]
for nm,x in [('CA',t),('Bay',t[t.bay])]:
    a=x.bucket.value_counts().rename('n').reset_index();a.insert(0,'sample',nm);a['level']='bucket';out.append(a.rename(columns={'bucket':'key'}))
    b=x.top.value_counts().rename('n').reset_index();b.insert(0,'sample',nm);b['level']='top';out.append(b.rename(columns={'top':'key'}))
    print(nm,len(x));print(x.top.value_counts());print(x.bucket.value_counts().to_dict())
    strict=x.bucket.isin(['CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED','LEGAL_PROF']).sum();print('taxonomy-only EXPOSED',strict, strict/len(x),'POS taxonomy-only',x.bucket.isin(['SOFTWARE_ENG','AI_PRODUCER','DATA_ENG_ANALYTICS']).sum())
pd.concat(out).to_csv(B+'jobs_aitrainer_former_occ.csv',index=False)
# title shares: 'Remote' / pay in these
print(t.title.str.contains('Remote',case=False).mean())
print(t.groupby('top').rate.median())
