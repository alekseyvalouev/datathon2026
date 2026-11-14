import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, re, pandas as pd, numpy as np
from sklearn.linear_model import LogisticRegression
pd.set_option('display.width',250); pd.set_option('display.max_columns',40); pd.set_option('display.max_colwidth',150)
P=sys.argv[1]
pj=pd.read_csv(WORK+'/site_projects.csv',index_col=0); it=pd.read_csv(P+'/items.csv.gz',low_memory=False); c=pd.read_csv(P+'/comments.csv',low_memory=False)
it=it[it.id_parent.isin(pj.index)].copy(); it['date']=pd.to_datetime(it.meeting_date); it['L']=it.item_text.fillna('').str.lower().str.replace(r'\s+',' ',regex=True)
A=it.ACTION.fillna('').str.lower().str.replace(r'\s+',' ',regex=True); it['A']=A
intent=A.str.contains('intent to')
it['d_app']=(it.action_final.isin(['approve','approve with conditions'])|A.str.contains(r'approv|no dr|not take dr|did not take|took dr|take dr and|upheld|uphold|certif|adopted|grant|accepted'))&~A.str.contains(r'disapprov|deny|denied|continu')&~intent
it['d_dis']=A.str.contains(r'disapprov|denied|\bdeny')&~intent&~A.str.contains('failed|continu')
it['d_wd']=A.str.contains('withdraw'); it['d_indef']=A.str.contains('indefinite'); it['d_cont']=A.str.contains('continu')|(it.action_final=='continuance')
def fin(q):
    q=q.sort_values('date'); dec=q[q.d_app|q.d_dis|q.d_wd]
    if len(dec):
        ld=dec.date.max(); l=dec[dec.date==ld]
        if l.d_app.any(): return 'approved'
        if l.d_dis.any(): return 'disapproved'
        return 'withdrawn'
    last=q[q.date==q.date.max()]
    if q.d_indef.any(): return 'continued indefinitely'
    if last.d_cont.any(): return 'continued, never returned'
    return 'no action recorded'
pj['final']=it.groupby('id_parent').apply(fin,include_groups=False)
pj['status']=it.groupby('id_parent').prj_record_status.last()
pj['year']=pd.to_datetime(pj['first']).dt.year
# comments at project level
c=c[c.is_staff!=1].merge(it[['item_id','id_parent','date']].rename(columns={'id_parent':'pid'}),on='item_id'); c=c[c.position.isin(['support','oppose'])]
grp={'YIMBY':'prohousing','Pro-Housing Advocacy':'prohousing','SPUR':'prohousing','Anti-Displacement':'antidisp','Race/Immigration/LGBTQ Groups':'antidisp','Slow Growth':'nhood','Historic Preservation':'nhood','Neighborhood Association':'nhood','DR Team':'drteam','Tenant Association':'tenant','Construction':'construction','Labor':'construction','Project Team':'projteam','Legal':'projteam'}
c['g']=np.where(c.role_long.isna(),'unaff',c.role_long.map(grp).fillna('other'))
d0=c.groupby('pid').date.min(); c['first']=c.date==c.pid.map(d0)
heard=pj[pj.index.isin(d0.index)&(pj.year<=2023)].copy(); print('site-specific projects with testimony, first heard <=2023:',len(heard))
print(heard.final.value_counts().to_frame('n').assign(share=lambda t:(t.n/len(heard)).round(3)))
heard['soft']=heard.final.isin(['withdrawn','continued indefinitely','continued, never returned']).astype(int); heard['notfwd']=(heard.final!='approved').astype(int)
print('city record status for soft-killed:',heard[heard.soft==1].status.fillna('no match').value_counts().head(6).to_dict()); print('  for approved:',heard[heard.final=='approved'].status.fillna('no match').value_counts().head(5).to_dict())
G=['drteam','nhood','antidisp','tenant','construction','prohousing','projteam']
for scope,cc in [('first',c[c['first']]),('ever',c)]:
    for g in G: heard[f'{g}_{scope}']=heard.index.isin(cc[cc.g==g].pid.unique()).astype(int)
f=c[c['first']]; heard['opp_unaff']=f[(f.g=='unaff')&(f.position=='oppose')].groupby('pid').size().reindex(heard.index).fillna(0); heard['sup_unaff']=f[(f.g=='unaff')&(f.position=='support')].groupby('pid').size().reindex(heard.index).fillna(0)
heard['nhood_opp_first']=heard.index.isin(f[(f.g=='nhood')&(f.position=='oppose')].pid.unique()).astype(int)
print('\n== soft-kill and not-approved rates by who spoke at the FIRST hearing with testimony')
rows=[]
for g in G+['nhood_opp']:
    col=f'{g}_first'; a=heard[heard[col]==1]; b=heard[heard[col]==0]
    rows.append({'group present':g,'projects':len(a),'soft-kill %':100*a.soft.mean(),'absent soft-kill %':100*b.soft.mean(),'disapproved %':100*(a.final=='disapproved').mean(),'absent disapproved %':100*(b.final=='disapproved').mean(),'mean hearings':a.nh.mean(),'absent hearings':b.nh.mean()})
print(pd.DataFrame(rows).round(1).to_string(index=False))
heard['oppb']=pd.cut(heard.opp_unaff,[-1,0,2,5,1e9],labels=['0','1-2','3-5','6+']); print('\nby unaffiliated opposition at first hearing:'); print(heard.groupby('oppb',observed=True).agg(n=('soft','size'),soft=('soft','mean'),disapproved=('final',lambda s:(s=='disapproved').mean())).round(3).to_string())
print('\nwithin non-DR vs DR cases (soft-kill rate, present vs absent):')
for lab,sub in [('non-DR',heard[heard.dr!=True]),('DR',heard[heard.dr==True])]:
    print(' ',lab,'n',len(sub),'base soft',round(sub.soft.mean(),3),{g:(int(sub[f'{g}_first'].sum()),round(sub[sub[f'{g}_first']==1].soft.mean(),3),round(sub[sub[f'{g}_first']==0].soft.mean(),3)) for g in ['drteam','nhood','antidisp','tenant','construction','prohousing']})
# adjusted model
heard['demo']=heard.txt.str.contains('demoli').astype(int) if 'txt' in heard else heard.index.map(it.groupby('id_parent').L.apply(lambda x:x.str.contains('demoli').any())).astype(int)
X=pd.DataFrame({**{g:heard[f'{g}_first'] for g in ['drteam','nhood','antidisp','tenant','construction','prohousing','projteam']},'log_opp_unaff':np.log1p(heard.opp_unaff),'log_sup_unaff':np.log1p(heard.sup_unaff),'is_dr':(heard.dr==True).astype(int),'log_units':np.log1p(heard.units.fillna(0)),'units_missing':heard.units.isna().astype(int),'demo':heard.demo,'year':heard.year-2015}).reset_index(drop=True)
rng=np.random.default_rng(1)
def boot(y,n=500):
    y=np.asarray(y); o=[]
    for _ in range(n):
        i=rng.integers(0,len(y),len(y)); o.append(LogisticRegression(C=10,max_iter=3000).fit(X.iloc[i],y[i]).coef_[0])
    o=np.array(o); return pd.DataFrame({'odds_ratio':np.exp(np.median(o,0)),'lo':np.exp(np.percentile(o,2.5,0)),'hi':np.exp(np.percentile(o,97.5,0))},index=X.columns).round(2)
print('\n== adjusted odds ratios, outcome = soft-killed (n=%d, events=%d)'%(len(heard),heard.soft.sum())); print(boot(heard.soft.values).to_string())
print('\n== adjusted odds ratios, outcome = 3+ hearings (events=%d)'%((heard.nh>=3).sum())); print(boot((heard.nh>=3).astype(int).values).to_string())
heard.drop(columns=[x for x in ['txt'] if x in heard]).to_csv(WORK+'/heard_projects.csv'); c.drop(columns=['text','body','comment'],errors='ignore').to_csv(WORK+'/c_groups.csv',index=False)

print('\n################ frequency of review requestors and neighbourhood associations')
allc=c
for g,lab in [('drteam','review requestors'),('nhood','neighbourhood associations')]:
    x=allc[allc.g==g]; pp=x.groupby('pid').size()
    print(f'\n{lab}: comments {len(x)} | projects {x.pid.nunique()} of {pj.index.isin(allc.pid.unique()).sum()} with comments | distinct people {x.commenter_id.nunique()} | comments/project median {pp.median()} max {pp.max()}')
    pc=x.groupby('commenter_id').pid.nunique(); print('   people by number of projects:',pd.cut(pc,[0,1,2,4,9,1e9],labels=['1','2','3-4','5-9','10+']).value_counts().sort_index().to_dict(),'| share of comments from people on 3+ projects',round(x.commenter_id.map(pc).ge(3).mean(),3))
    yr=pd.to_datetime(x.meeting_date).dt.year; print('   projects per period:',x.groupby(pd.cut(yr,[2004,2009,2014,2019,2026])).pid.nunique().to_dict())
    print('   by project kind:',x.merge(pj[['kind']],left_on='pid',right_index=True).groupby('kind').pid.nunique().to_dict())
x=allc[allc.g=='nhood']; print('\nmost frequent organisations (neighbourhood assoc. label):'); print(x[x.organization.notna()].groupby('organization').agg(comments=('pid','size'),projects=('pid','nunique'),support=('position',lambda s:(s=='support').mean())).sort_values('projects',ascending=False).head(15).round(2).to_string())
print('share of nhood-labelled comments with organization name',x.organization.notna().mean().round(2))
