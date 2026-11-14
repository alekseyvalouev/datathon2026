import sys,re,pandas as pd,numpy as np
import statsmodels.api as sm, statsmodels.formula.api as smf
S=sys.argv[1]; sys.path.insert(0,S+'/code')
from voice_lib import AIM_CS
df=pd.read_pickle(S+'/base/_reddit_all_labeled_t.pkl')
df['ai_any']=df.n_ai>0
out=open(S+'/out/_reddit_numbers.txt','w')
def P(*a):
    print(*a); print(*a,file=out)
def wilson(k,n,z=1.96):
    if n==0: return (np.nan,np.nan)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (c-h,c+h)
# ---- profile
P('TOTAL posts',len(df),'communities',df.community_name.nunique(),'range',df.date_posted.min()[:10],df.date_posted.max()[:10])
P(df.scope.value_counts().to_string())
P('top communities'); P(df.community_name.value_counts().head(25).to_string())
bay=df[df.scope=='BAY']; P('BAY communities:'); P(bay.community_name.value_counts().to_string())
P('monthly posts all'); P(df.month.value_counts().sort_index().to_string())
P('monthly posts by scope'); P(pd.crosstab(df.month,df.scope).to_string())
# ---- classification counts
P(pd.crosstab(df.scope,df.ai_cat).to_string())
# ---- monthly table
cats=['actual_displacement','fear_anticipation','ai_hiring_search','ai_tool_at_work']
rows=[]
for sc,d in list(df.groupby('scope'))+[('ALL_IN_SCOPE(WORK_GEN+BAY)',df[df.scope.isin(['WORK_GEN','BAY'])])]:
    for m,g in d.groupby('month'):
        r={'scope':sc,'month':m,'n_posts':len(g),'n_ai_any_term':int(g.ai_any.sum()),'n_ai_work':int(g.ai_work.sum())}
        for c in cats: r['n_'+c]=int((g.ai_cat==c).sum())
        for f in ['f_ghost','f_volume','f_ai_screen','f_entry','f_jobsearch','f_friction_any']: r['n_'+f]=int(g[f].sum())
        r['share_ai_work']=r['n_ai_work']/r['n_posts']; r['share_ai_any_term']=r['n_ai_any_term']/r['n_posts']
        lo,hi=wilson(r['n_ai_work'],r['n_posts']); r['ai_work_ci_lo']=lo; r['ai_work_ci_hi']=hi
        r['share_ghost']=r['n_f_ghost']/r['n_posts']; r['share_ai_screen']=r['n_f_ai_screen']/r['n_posts']; r['share_volume']=r['n_f_volume']/r['n_posts']
        r['small_cell_flag']=r['n_posts']<300
        rows.append(r)
mon=pd.DataFrame(rows); mon.to_csv(S+'/base/reddit_monthly.csv',index=False)
# ---- reweighted series (fixed subreddit mix) WORK_GEN
w=df[(df.scope=='WORK_GEN')].copy()
core=[c for c,n in w.community_name.value_counts().items() if n>=500]
P('WORK_GEN core subs for reweighting',core)
wc=w[w.community_name.isin(core)]
wt=wc.community_name.value_counts(normalize=True)
rw=[]
for m,g in wc.groupby('month'):
    s=g.groupby('community_name').ai_work.mean()
    ss=g.groupby('community_name').ai_any.mean()
    cov=wt[s.index].sum()
    rw.append({'month':m,'n':len(g),'reweighted_share_ai_work':(s*wt[s.index]).sum()/cov,'reweighted_share_ai_any':(ss*wt[ss.index]).sum()/cov,'sub_coverage_weight':cov,'raw_share':g.ai_work.mean()})
rw=pd.DataFrame(rw); rw.to_csv(S+'/base/reddit_monthly_reweighted.csv',index=False)
P(rw.round(4).to_string())
# ---- trend tests (WORK_GEN, exclude partial last month; months idx)
full=w[(w.month<'2026-11')].copy()
full['t']=(pd.to_datetime(full.month+'-01')-pd.Timestamp('2025-01-01')).dt.days/30.4
full['y']=full.ai_work.astype(int)
m1=smf.logit('y~t',full).fit(disp=0); m2=smf.logit('y~t+C(community_name)',full).fit(disp=0)
for nm,m in [('pooled',m1),('subreddit FE',m2)]:
    P('LOGIT trend',nm,'coef/month=%.4f se=%.4f p=%.3f'%(m.params['t'],m.bse['t'],m.pvalues['t']),'OR/month=%.4f'%np.exp(m.params['t']))
full['yany']=full.ai_any.astype(int)
m3=smf.logit('yany~t+C(community_name)',full).fit(disp=0); P('LOGIT any-AI-term trend subFE coef=%.4f p=%.3f'%(m3.params['t'],m3.pvalues['t']))
for a,b in [('2025-01','2025-06'),('2025-07','2025-12'),('2026-01','2026-06'),('2026-07','2026-10')]:
    g=full[(full.month>=a)&(full.month<=b)]; k=g.y.sum(); n=len(g); lo,hi=wilson(k,n)
    P(f'WORK_GEN {a}..{b}: n={n} ai_work={k} share={k/n:.4f} CI[{lo:.4f},{hi:.4f}]  any-term share={g.ai_any.mean():.4f}')
# by category by half
for a,b in [('2025-01','2025-06'),('2025-07','2025-12'),('2026-01','2026-06'),('2026-07','2026-10')]:
    g=full[(full.month>=a)&(full.month<=b)]
    P(a,b,{c:round((g.ai_cat==c).mean()*100,3) for c in cats})
# BAY
b=df[df.scope=='BAY']; P('BAY n',len(b),'ai_work',int(b.ai_work.sum()),'any term',int(b.ai_any.sum()))
for a,bb in [('2025-01','2025-12'),('2026-01','2026-06'),('2026-07','2026-10')]:
    g=b[(b.month>=a)&(b.month<=bb)]; lo,hi=wilson(g.ai_work.sum(),len(g)); P(f'BAY {a}..{bb}: n={len(g)} ai_work={g.ai_work.sum()} share={g.ai_work.mean():.4f} CI[{lo:.4f},{hi:.4f}] any-term={g.ai_any.mean():.4f}')
P(b[b.ai_work].groupby('community_name').size().to_string()); P(b[b.ai_work].ai_cat.value_counts().to_string())
# all scopes shares
P(df.groupby('scope').agg(n=('post_id','size'),ai_work=('ai_work','mean'),ai_any=('ai_any','mean')).round(4).to_string())
# ---- occupation attribution
ex=df[df.scope.isin(['WORK_GEN','BAY'])&df.ai_cat.isin(['actual_displacement','fear_anticipation'])]
P('EXPOSURE POOL n',len(ex)); P(ex.occ_basis.value_counts(dropna=False).to_string())
hc=ex[ex.occ_basis.isin(['self','title'])]
P('HIGH-CONF primary occ (n=%d)'%len(hc)); P(hc.occ_primary.value_counts().to_string())
act=ex[ex.ai_cat=='actual_displacement']; P('ACTUAL strict n',len(act)); P(act.occ_primary.value_counts(dropna=False).to_string()); P(act.occ_basis.value_counts(dropna=False).to_string())
P('ACTUAL high-conf:'); P(act[act.occ_basis.isin(['self','title'])].occ_primary.value_counts().to_string())
P('LOW-CONF body:'); P(ex[ex.occ_basis=='body_lowconf'].occ_primary.value_counts().to_string())
# any-mention rates vs baseline in WORK_GEN (all posts), per class
from voice_occ import OCCC
base=df[df.scope=='WORK_GEN']; 
def mention_rate(d,txt='t'):
    r={}
    for c,rx in OCCC:
        if c=='MANAGEMENT': continue
        r[c]=d[txt].str.contains(rx).mean()
    return pd.Series(r)
mr_ex=mention_rate(ex); mr_base=mention_rate(base.sample(8000,random_state=1))
cmp=pd.DataFrame({'mention_rate_exposure_posts':mr_ex,'mention_rate_all_WORKGEN':mr_base}); cmp['lift']=cmp.iloc[:,0]/cmp.iloc[:,1]
P(cmp.round(4).to_string())
grp={'AI_POSITIONED(AI_PRODUCER,SOFTWARE_ENG,DATA_ENG)':['AI_PRODUCER','SOFTWARE_ENG','DATA_ENG_ANALYTICS'],'EXPOSED(CLERICAL,CUST_SUPPORT,PROF_EXPOSED)':['CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED'],'IN_PERSON(FRONTLINE,TRADE,HEALTH)':['FRONTLINE_SERVICE','SKILLED_TRADE','HEALTH_CLINICAL']}
for k,v in grp.items():
    P(k,'high-conf share:',round(hc.occ_primary.isin(v).sum()/hc.occ_primary.notna().sum(),3),'n=',int(hc.occ_primary.isin(v).sum()),'| all-basis share:',round(ex.occ_primary.isin(v).sum()/ex.occ_primary.notna().sum(),3),'n=',int(ex.occ_primary.isin(v).sum()))
# ---- friction
for sc in ['WORK_GEN','BAY']:
    d=df[df.scope==sc]
    P(sc,'n',len(d),{f:round(d[f].mean(),4) for f in ['f_jobsearch','f_ghost','f_volume','f_ai_screen','f_entry','f_friction_any']})
w=df[df.scope=='WORK_GEN']
for f in ['f_ghost','f_volume','f_ai_screen','f_friction_any']:
    a=w[w.f_entry][f].mean(); b2=w[~w.f_entry][f].mean(); P('entry vs non-entry',f,round(a,4),round(b2,4),'n_entry',int(w.f_entry.sum()))
# ai-hiring share among entry vs not
for nm,d in [('entry',w[w.f_entry]),('non-entry',w[~w.f_entry])]:
    P(nm,'n',len(d),'ai_hiring_search share',round((d.ai_cat=='ai_hiring_search').mean(),4),'ai_work share',round(d.ai_work.mean(),4),'fear share',round((d.ai_cat=='fear_anticipation').mean(),4))
# application counts
pat=re.compile(r"(?:applied (?:to|for) (?:over |more than |about |around |nearly |almost )?|sent (?:out )?(?:over |about |around )?|submitted (?:over |about |around )?)(\d{2,5})\+?\s*(?:jobs|job|applications|resumes|positions|roles|different)|(\d{2,5})\+?\s*(?:job )?applications",re.I)
nums=[]
for t in w.t:
    for m in pat.finditer(t):
        x=m.group(1) or m.group(2)
        try: nums.append(int(x))
        except: pass
nums=pd.Series([n for n in nums if 10<=n<=10000]); P('stated application counts (mentions, WORK_GEN): n=',len(nums),'median',nums.median(),'p25',nums.quantile(.25),'p75',nums.quantile(.75))
# monthly friction WORK_GEN reweighted? simple
fm=w.groupby('month').agg(n=('post_id','size'),ghost=('f_ghost','mean'),ai_screen=('f_ai_screen','mean'),volume=('f_volume','mean'),entry=('f_entry','mean'),aihire=('ai_cat',lambda s:(s=='ai_hiring_search').mean()))
P(fm.round(4).to_string())
# friction ai-hiring in BAY subs
# save posts csv
keep=df[df.ai_work].copy()
keep[['post_id','community_name','scope','month','ai_cat','n_ai','occ_primary','occ_basis','occ_self','occ_any','f_ghost','f_volume','f_ai_screen','f_entry','f_jobsearch']].to_csv(S+'/base/reddit_ai_posts.csv',index=False)
P('saved ai posts',len(keep))
