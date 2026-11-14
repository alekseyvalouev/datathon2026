import sys;sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
from jobs_lib import *
pd.set_option('display.width',250);pd.set_option('display.max_columns',50)
d=load()
def summ(x,key):
    rows=[]
    N=len(x);Nu=(~x.seeded).sum()
    for k,g in x.groupby(key):
        s=g[g.sal_ok];h=g[g.hourly]
        rows.append(dict(cls=k,n=len(g),share_all=len(g)/N,share_unseeded=(~g.seeded).sum()/Nu,n_sal=len(s),share_sal=len(s)/len(g),
          med=s.sal_mid.median(),p25=q(s.sal_mid,.25),p75=q(s.sal_mid,.75),p90=q(s.sal_mid,.9),med_lo=s.sal_lo.median(),med_hi=s.sal_hi.median(),
          n_hourly=len(h),share_sal_hourly=len(h)/max(len(s),1),med_hourly_rate=h.rate.median(),p25_rate=q(h.rate,.25),p75_rate=q(h.rate,.75),pt_share_hourly=h.parttime.mean() if len(h) else np.nan,
          med_annual_posted_only=s[s.sal_period=='year'].sal_mid.median(),n_annual_posted=int((s.sal_period=='year').sum())))
    return pd.DataFrame(rows).sort_values('med',ascending=False)
out=[]
for nm,x in [('BayArea',d[d.bay]),('California',d),('BayArea_unseeded',d[d.bay&~d.seeded])]:
    for keyname,key in [('occ','occ'),('grp','grp')]:
        t=summ(x,key);t.insert(0,'level',keyname);t.insert(0,'sample',nm);out.append(t)
    t=summ(x.assign(all='ALL'),'all');t.insert(0,'level','all');t.insert(0,'sample',nm);out.append(t)
cs=pd.concat(out);cs.to_csv(B+'jobs_class_summary.csv',index=False)
print(cs[(cs['sample']=='BayArea')&(cs['level']=='occ')].round(3).to_string())
print(cs[(cs['sample']=='BayArea_unseeded')&(cs['level']=='grp')][['cls','n','share_unseeded','n_sal','med']].round(3).to_string())
for nm,x0 in [('Bay',d[d.bay]),('Bay_unseeded',d[d.bay&~d.seeded]),('CA',d)]:
    s=x0[x0.sal_ok]
    m=lambda g:s[g].sal_mid.median()
    P=m(s.occ.isin(POS));E=m(s.occ.isin(EXP));F=m(s.occ=='FRONTLINE_SERVICE');A=m(s.occ=='AI_DATA_WORK')
    print(nm,'POS',P,'EXP',E,'FL',F,'ADW',A,'ratios P/E',P/E,'P/F',P/F,'P/ADW',P/A,'gaps',P-E,P-F,P-A)
    print(' overall median',s.sal_mid.median(),'drop POS',s[~s.occ.isin(POS)].sal_mid.median(),'POS share of salaried',s.occ.isin(POS).mean(),'of all postings',x0.occ.isin(POS).mean(),'EXP share all',x0.occ.isin(EXP).mean())
    rng=np.random.default_rng(1)
    pp=s[s.occ.isin(POS)];ee=s[s.occ.isin(EXP)]
    pc=pp.groupby('company_norm').sal_mid.apply(np.array);
    r=[]
    for _ in range(500):
        a=pp.sample(len(pp),replace=True,random_state=int(rng.integers(1e9)));b=ee.sample(len(ee),replace=True,random_state=int(rng.integers(1e9)))
        r.append(a.sal_mid.median()/b.sal_mid.median())
    print(' P/E boot CI',np.percentile(r,[2.5,97.5]))
    for lab,g in [('occ17',s.occ),('grp',s.grp)]:
        y=s.lsal;tot=((y-y.mean())**2).sum();gm=y.groupby(g).transform('mean');btw=((gm-y.mean())**2).sum()
        print(' var decomp',lab,'between share',btw/tot,'within',1-btw/tot,'total var',y.var(),'n',len(s))
    gm=s.groupby(['occ','city']).lsal.transform('mean');print(' occ x city between (overfit upper bound)',(((gm-s.lsal.mean())**2).sum())/(((s.lsal-s.lsal.mean())**2).sum()))
# monthly trend (uncensored)
u=d[(~d.censored)&d.bay&(d.post_date>='2026-02-01')&(d.post_date<'2026-10-01')].copy()
u['m']=u.post_date.dt.strftime('%Y-%m')
print(len(u), (~d.censored).sum(), d[(~d.censored)].bay.sum())
tr=u.groupby('m').agg(n=('jobid','size'),ai_any=('ai_any','mean'),ai_strict=('ai_strict','mean'),ai_use=('ai_use','mean'),ai_build=('ai_build','mean'),pos_share=('grp',lambda g:(g=='AI_POSITIONED').mean()),exp_share=('grp',lambda g:(g=='EXPOSED').mean()),fl_share=('grp',lambda g:(g=='FRONTLINE_SERVICE').mean()),med_sal=('sal_mid','median'))
print(tr.round(3))
mix=pd.crosstab(u.m,u.occ,normalize='index').round(3);print(mix.T)
print(d[~d.censored].crawl.str[:7].value_counts().sort_index())
# within-class monthly AI share
w=u.groupby(['m','grp']).ai_strict.mean().unstack().round(3);print(w[['AI_POSITIONED','EXPOSED','FRONTLINE_SERVICE']])
cmp=pd.DataFrame({'cens':d[d.bay&d.censored].grp.value_counts(normalize=True),'uncens':d[d.bay&~d.censored].grp.value_counts(normalize=True)});print(cmp.round(3))
print('ai_strict censored vs not',d[d.bay].groupby('censored')[['ai_any','ai_strict','ai_use','ai_build','has_salary']].mean())
tr.to_csv(B+'jobs_monthly_uncensored.csv');mix.to_csv(B+'jobs_monthly_mix_uncensored.csv')
