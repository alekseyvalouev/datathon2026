import sys;sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
from jobs_lib import *
pd.set_option('display.width',250);pd.set_option('display.max_columns',40);pd.set_option('display.max_rows',200)
d=load();b=d[d.bay].copy()
w=pd.read_csv(B+'warn_ca.csv',parse_dates=['notice_date'])
BAY9=['Alameda','Contra Costa','Marin','Napa','San Francisco','San Mateo','Santa Clara','Solano','Sonoma']
w['bayco']=w.county.isin(BAY9)
def agg(w):
    return w.groupby('company_norm').agg(warn_company=('company','first'),n_notices=('employees','size'),warn_employees=('employees','sum'),warn_emp_bay=('employees',lambda s:s[w.loc[s.index,'bayco']].sum()),
        first_notice=('notice_date','min'),last_notice=('notice_date','max'),closure_share=('kind',lambda s:(s=='Closure').mean()))
W_all=agg(w);W_bay=agg(w[w.bayco]);W_rec=agg(w[w.notice_date>='2025-01-01'])
print('WARN rows',len(w),'bay-county rows',w.bayco.sum(),'firms all',len(W_all),'bay',len(W_bay),'recent',len(W_rec))
res={}
pfirms=set(b.company_norm.dropna());print('bay posting firms',len(pfirms),'postings',len(b))
for nm,W in [('WARN_any_CA',W_all),('WARN_BayCounty',W_bay),('WARN_BayCounty_since2025',agg(w[w.bayco&(w.notice_date>='2025-01-01')]))]:
    m=b.company_norm.isin(W.index)
    wf=set(W.index)&pfirms
    wtot=W.warn_employees.sum()
    print(nm,'| posting match rate',m.mean(),m.sum(),'| posting firms matched',b[m].company_norm.nunique(),'of',len(pfirms),'| WARN firms with Bay postings',len(wf),'of',len(W),round(len(wf)/len(W),3),'| WARN employees covered',W.loc[list(wf),'warn_employees'].sum()/wtot)
# generic-name risk: matched firm list top 
W=W_bay
b['warn_bay']=b.company_norm.isin(W_all.index)  # any CA WARN
b['warn_baycounty']=b.company_norm.isin(W_bay.index)
for flag in ['warn_baycounty','warn_bay']:
    print('=====',flag)
    for tag,x in [('all',b),('unseeded',b[~b.seeded])]:
        mix=pd.crosstab(x.grp,x[flag],normalize='columns');mix['diff']=mix[True]-mix[False];print(tag,'n warn',int(x[flag].sum()),'n non',int((~x[flag]).sum()));print(mix.round(3).loc[['AI_POSITIONED','EXPOSED','FRONTLINE_SERVICE','MANAGEMENT','HEALTH_CLINICAL','OTHER']])
# firm-cluster bootstrap for POS share diff and EXPOSED share diff (unseeded)
def boot(x,flag,B_=1000):
    f=x.groupby('company_norm').agg(n=('jobid','size'),pos=('grp',lambda z:(z=='AI_POSITIONED').sum()),exp=('grp',lambda z:(z=='EXPOSED').sum()),fl=('grp',lambda z:(z=='FRONTLINE_SERVICE').sum()),w=(flag,'max'))
    rng=np.random.default_rng(3);out=[]
    def stat(f):
        a=f[f.w];c=f[~f.w];return [a.pos.sum()/a.n.sum()-c.pos.sum()/c.n.sum(),a.exp.sum()/a.n.sum()-c.exp.sum()/c.n.sum(),a.fl.sum()/a.n.sum()-c.fl.sum()/c.n.sum()]
    pt=stat(f)
    for _ in range(B_):
        idx=rng.integers(0,len(f),len(f));out.append(stat(f.iloc[idx]))
    out=np.array(out);return pt,np.percentile(out,[2.5,97.5],axis=0),len(f),int(f.w.sum())
BT=[]
for flag in ['warn_baycounty','warn_bay']:
    for tag,x in [('all',b),('unseeded',b[~b.seeded])]:
        pt,ci,nf,nw=boot(x,flag)
        for i,k in enumerate(['POS','EXP','FL']):
            BT.append(dict(flag=flag,sample=tag,class_=k,diff=pt[i],lo=ci[0][i],hi=ci[1][i],n_firms=nf,n_warn_firms=nw))
BT=pd.DataFrame(BT);print(BT.round(3))
# firm-weighted: share of matched firms (>=5 postings) whose majority is POS
f=b.groupby('company_norm').agg(n=('jobid','size'),pos=('grp',lambda z:(z=='AI_POSITIONED').mean()),exp=('grp',lambda z:(z=='EXPOSED').mean()),w=('warn_baycounty','max'),med=('sal_mid','median'))
f5=f[f.n>=5];print('firms>=5 postings',len(f5),'warn',int(f5.w.sum()));print(f5.groupby('w')[['pos','exp','med']].mean().round(3), f5.groupby('w')[['pos','exp','med']].median().round(3))
# top matched firms
m=b[b.warn_bay].groupby('company_norm').agg(company=('company','first'),n_postings=('jobid','size'),pos_share=('grp',lambda z:(z=='AI_POSITIONED').mean()),exp_share=('grp',lambda z:(z=='EXPOSED').mean()),fl_share=('grp',lambda z:(z=='FRONTLINE_SERVICE').mean()),top_occ=('occ',lambda z:z.mode().iat[0]),med_pay=('sal_mid','median'),ai_strict=('ai_strict','mean'))
J=m.join(W_all.drop(columns=['warn_company']),how='left').join(W_bay[['n_notices','warn_employees']].rename(columns={'n_notices':'n_notices_baycounty','warn_employees':'warn_employees_baycounty'}))
J=J.sort_values('warn_employees',ascending=False);J.to_csv(B+'jobs_warn_firm_join.csv')
print(J.head(40).round(3).to_string())
print('matched firms with >=5 postings',(J.n_postings>=5).sum(),'total matched firms',len(J))
# posting pay in WARN vs non-WARN within POS
s=b[b.sal_ok];print(s.groupby(['grp','warn_bay']).sal_mid.median().unstack().loc[['AI_POSITIONED','EXPOSED','FRONTLINE_SERVICE']])
print('ex-top5 check: drop biggest matched firms');top=J.sort_values('n_postings',ascending=False).index[:5];print(list(J.loc[top,'company']))
x=b[~b.company_norm.isin(top)];mix=pd.crosstab(x.grp,x.warn_bay,normalize='columns');print(mix.round(3).loc[['AI_POSITIONED','EXPOSED','FRONTLINE_SERVICE']])
BT.to_csv(B+'jobs_warn_mix_bootstrap.csv',index=False)
