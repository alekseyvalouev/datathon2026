import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, re, pandas as pd, numpy as np
from sklearn.linear_model import LogisticRegression
pd.set_option('display.width',250); pd.set_option('display.max_columns',40); pd.set_option('display.max_colwidth',200)
P=sys.argv[1]
h=pd.read_csv(WORK+'/heard_projects.csv',index_col=0); c=pd.read_csv(WORK+'/c_groups.csv',low_memory=False,parse_dates=['date'])
it=pd.read_csv(P+'/items.csv.gz',low_memory=False); it=it[it.id_parent.isin(h.index)].copy(); it['date']=pd.to_datetime(it.meeting_date)
it['L']=it.item_text.fillna('').str.lower().str.replace(r'\s+',' ',regex=True); it['A']=it.ACTION.fillna('').str.lower().str.replace(r'\s+',' ',regex=True)
APP=r'approv|no dr\b|not take dr|did not take|took dr|take dr and|upheld|uphold|certif|adopted (?!a motion of intent)|grant|accepted'
def cls(a):
    if not a: return 'none'
    segs=[s.strip() for s in re.split(r';',a) if s.strip()]; last=segs[-1]
    for s in [last]+segs[::-1]:
        if 'intent to' in s:
            if re.search(r'continu',s): return 'cont'
            continue
        if 'failed' in s: 
            if s is last: 
                # deadlock unless a later clause decided
                continue
            continue
        if re.match(r'^(?:acting |asst\. )?(?:za )?(?:after [^,]*, )?continu',s) or re.search(r'continued (?:to|indefinitely|as proposed)|continue to \w+ \d',s) and not re.search(APP,s.split('continu')[0]): return 'indef' if 'indefinite' in s else 'cont'
        if re.search(r'disapprov|\bdenied|\bdeny',s): return 'dis'
        if re.search(APP,s) and not re.match(r'^(?:discretionary reviews? |dr )?withdraw',s): return 'app'
        if re.search(r'withdraw',s): return 'wd'
    if 'failed' in a: return 'deadlock'
    return 'other'
it['k']=it.A.map(cls); it.loc[(it.k.isin(['other','none']))&it.action_final.isin(['approve','approve with conditions']),'k']='app'
it.loc[(it.k.isin(['other','none']))&(it.action_final=='continuance'),'k']='cont'; it.loc[(it.k.isin(['other','none']))&(it.action_final=='disapprove'),'k']='dis'
def fin(q):
    q=q.sort_values('date'); dec=q[q.k.isin(['app','dis','wd','deadlock'])]
    if len(dec):
        l=dec[dec.date==dec.date.max()]
        for k,lab in [('app','approved'),('dis','disapproved'),('wd','withdrawn'),('deadlock','deadlocked vote, no decision')]:
            if (l.k==k).any(): return lab
    if (q.k=='indef').any(): return 'continued indefinitely'
    if (q[q.date==q.date.max()].k=='cont').any() or (q.k=='cont').any(): return 'continued, never returned'
    return 'no action recorded'
h['final_old']=h.final; h['final']=it.groupby('id_parent').apply(fin,include_groups=False)
print(pd.crosstab(h.final_old,h.final,margins=True).to_string())
h.loc[(h.final=='withdrawn')&(h.dr==True),'final']='review request withdrawn (project proceeds)'
h['soft']=h.final.isin(['withdrawn','continued indefinitely','continued, never returned','deadlocked vote, no decision']).astype(int)
print('\nrevised distribution:'); print(h.final.value_counts().to_frame('n').assign(share=lambda t:(t.n/len(h)).round(3)).to_string())
# batch clusters: same first/last dates and same first 60 chars of request text
key=it.groupby('id_parent').apply(lambda q:(str(q.date.max().date()),re.sub(r'\d+','#',re.sub(r'^.*?request','request',q.L.iloc[0]))[:60]),include_groups=False); h['batch']=h.index.map(key); bs=h.groupby('batch').size(); h['batch_n']=h.batch.map(bs)
print('\nsoft-killed projects in same-day near-identical batches (size>=3):',int(((h.soft==1)&(h.batch_n>=3)).sum()),'| batches:',h[(h.soft==1)&(h.batch_n>=3)].batch.nunique())
sk=h[h.soft==1]; print('\nrandom 0 soft-killed, for hand check:')
for pid in sk.sample(0,random_state=7).index:
    q=it[it.id_parent==pid].sort_values('date'); print(' *',pid,'|',h.loc[pid,'final'],'|',' > '.join(f"{a.date.date()}:{a.A[:60]}" for a in q.drop_duplicates(['date','A']).itertuples() if a.A)[:330])
G=['tenant','antidisp','construction','nhood','prohousing','drteam','projteam']
def table(hh,lab):
    rows=[]
    for g in G:
        a=hh[hh[f'{g}_first']==1]; b=hh[hh[f'{g}_first']==0]; rows.append({'group':g,'projects':len(a),'soft-killed':int(a.soft.sum()),'soft %':100*a.soft.mean(),'absent %':100*b.soft.mean(),'disapproved %':100*(a.final=='disapproved').mean(),'absent dis %':100*(b.final=='disapproved').mean()})
    print(f'\n== {lab} (n={len(hh)}, soft-killed={int(hh.soft.sum())})'); print(pd.DataFrame(rows).round(1).to_string(index=False))
table(h,'revised classifier, all projects')
d=h.sort_values('first').drop_duplicates('batch') ; table(d,'revised classifier, one project per batch')
f=c[c['first']&c.pid.isin(d.index)]
rows=[]
for g in ['tenant','antidisp','construction','nhood','prohousing']:
    x=f[f.g==g].groupby('pid').position.agg(lambda s:(s=='support').mean())
    for lab,ids in [('group opposed',x[x<0.5].index),('group supported',x[x>=0.5].index)]:
        s=d.loc[d.index.intersection(ids)]; rows.append({'group':g,'stance':lab,'projects':len(s),'soft-killed':int(s.soft.sum()),'soft %':round(100*s.soft.mean(),1),'disapproved %':round(100*(s.final=='disapproved').mean(),1),'mean hearings':round(s.nh.mean(),2),'other opposition':round(s.opp_unaff.mean(),1)})
print('\n== by the group\'s own stance (deduplicated)'); print(pd.DataFrame(rows).to_string(index=False))
d=d.copy(); d['demo']=d.index.map(it.groupby('id_parent').L.apply(lambda x:x.str.contains('demoli').any())).astype(int)
X=pd.DataFrame({**{g:d[f'{g}_first'] for g in G},'log_opp_unaff':np.log1p(d.opp_unaff),'log_sup_unaff':np.log1p(d.sup_unaff),'is_dr':(d.dr==True).astype(int),'log_units':np.log1p(d.units.fillna(0)),'units_missing':d.units.isna().astype(int),'demo':d.demo,'year':d.year-2015}).reset_index(drop=True)
rng=np.random.default_rng(1)
def boot(y,n=500):
    y=np.asarray(y); o=[]
    for _ in range(n):
        i=rng.integers(0,len(y),len(y)); o.append(LogisticRegression(C=10,max_iter=3000).fit(X.iloc[i],y[i]).coef_[0])
    o=np.array(o); return pd.DataFrame({'OR':np.exp(np.median(o,0)),'lo':np.exp(np.percentile(o,2.5,0)),'hi':np.exp(np.percentile(o,97.5,0))},index=X.columns).round(2)
print('\n== adjusted odds ratios, soft-killed, deduplicated (events %d)'%d.soft.sum()); print(boot(d.soft.values).to_string())
print('\n== adjusted odds ratios, disapproved (events %d)'%(d.final=='disapproved').sum()); print(boot((d.final=='disapproved').astype(int).values).loc[G+['log_opp_unaff','log_sup_unaff']].to_string())
print('\n== adjusted odds ratios, 3+ hearings (events %d)'%(d.nh>=3).sum()); print(boot((d.nh>=3).astype(int).values).loc[G+['log_opp_unaff','log_sup_unaff']].to_string())
d['oppb']=pd.cut(d.opp_unaff,[-1,0,2,5,1e9],labels=['0','1-2','3-5','6+']); print(d.groupby('oppb',observed=True).agg(n=('soft','size'),soft=('soft','mean'),dis=('final',lambda s:(s=='disapproved').mean())).round(3).to_string())
for g in ['tenant','antidisp','construction']:
    s=d[(d.soft==1)&(d[f'{g}_first']==1)]; print(f'\n#### {g}: soft-killed after dedup = {len(s)}')
    for pid in s.index:
        q=it[it.id_parent==pid].sort_values('date'); txt=q.L.iloc[q.L.str.len().argmax()]; m=re.search(r'(request for.*|proposing.*)',txt); gs=f[(f.pid==pid)&(f.g==g)].position.value_counts().to_dict()
        print(f" - {pid} | {d.loc[pid,'final']} | {g} {gs} | other opp {int(d.loc[pid,'opp_unaff'])} | {(m.group(1) if m else txt)[:170]} || LAST: {q[q.A!=''].A.iloc[-1][:110] if (q.A!='').any() else ''}")
d.to_csv(WORK+'/heard_dedup.csv')

def how(pid):
    q=it[it.id_parent==pid].sort_values('date'); last=q[q.date==q.date.max()]
    return 'ended on continuance calendar (scheduled postponement)' if (last.section_group=='Items Proposed for Continuance').all() else ('heard, then continued' if q.A.str.contains('after hearing|closing public comment|closing pc|direction').any() else 'continued/withdrawn from regular calendar without recorded hearing')
sk=d[d.soft==1]; print('\nhow stalls end:',sk.index.to_series().map(how).value_counts().to_dict()); print('stalled by kind:',sk.kind.value_counts().to_dict()); print('all by kind:',d.kind.value_counts().to_dict())
print('stall rate by kind:',d.groupby('kind').soft.mean().round(3).to_dict()); print('disapproval by kind:',d.groupby('kind').apply(lambda q:(q.final=='disapproved').mean(),include_groups=False).round(3).to_dict())
T={'unit merger/removal/conversion':r'merg|removal of|remove an? |unauthorized|conversion of|condominium conversion|residential hotel','demolition':'demoli','new construction':r'new construction|construct a new'}
tt=d.index.map(it.groupby('id_parent').L.apply(lambda x:' '.join(x.unique())))
for k,p in T.items():
    m=pd.Series(tt,index=d.index).str.contains(p); print(k,'| n',int(m.sum()),'| stall',round(d[m].soft.mean(),3),'vs',round(d[~m].soft.mean(),3),'| disapproved',round((d[m].final=='disapproved').mean(),3),'vs',round((d[~m].final=='disapproved').mean(),3),'| tenant present',round(d[m].tenant_first.mean(),3),'vs',round(d[~m].tenant_first.mean(),3))
ten=d[d.tenant_first==1]; print('tenant-present projects final:',ten.final.value_counts().to_dict(),'| DR share',round((ten.dr==True).mean(),2))
