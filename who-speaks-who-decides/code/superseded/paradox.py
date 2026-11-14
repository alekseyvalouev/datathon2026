import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, re, pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',40); pd.set_option('display.max_colwidth',220)
P=sys.argv[1]
h=pd.read_csv(WORK+'/heard_projects.csv',index_col=0); c=pd.read_csv(WORK+'/c_groups.csv',low_memory=False,parse_dates=['date'])
it=pd.read_csv(P+'/items.csv.gz',low_memory=False); it=it[it.id_parent.isin(h.index)].copy(); it['date']=pd.to_datetime(it.meeting_date)
it['L']=it.item_text.fillna('').str.lower().str.replace(r'\s+',' ',regex=True); it['A']=it.ACTION.fillna('').str.replace(r'\s+',' ',regex=True)
h['t']=h.index.map(it.groupby('id_parent').L.apply(lambda x:' || '.join(x.unique())))
c=c[c.pid.isin(h.index)]; f=c[c['first']]
print('== stance of each group overall (all comments on these projects) and at first hearing')
print(c.groupby('g').position.agg(n='size',support=lambda s:(s=='support').mean()).round(3).loc[['tenant','antidisp','construction','nhood','drteam','prohousing','projteam','unaff']].to_string())
print('\n== soft-kill rate by the GROUP\'S OWN STANCE at first hearing')
rows=[]
for g in ['tenant','antidisp','construction','nhood','prohousing']:
    x=f[f.g==g].groupby('pid').position.agg(lambda s:(s=='support').mean())
    for lab,ids in [('all opposed',x[x==0].index),('all supported',x[x==1].index),('split',x[(x>0)&(x<1)].index)]:
        s=h.loc[h.index.intersection(ids)]
        rows.append({'group':g,'group stance':lab,'projects':len(s),'soft-killed':int(s.soft.sum()),'soft %':round(100*s.soft.mean(),1) if len(s) else np.nan,'disapproved %':round(100*(s.final=='disapproved').mean(),1) if len(s) else np.nan,'mean hearings':round(s.nh.mean(),2) if len(s) else np.nan,'mean other opp':round(s.opp_unaff.mean(),1) if len(s) else np.nan})
print(pd.DataFrame(rows).to_string(index=False))
K={'demolition':'demoli','unit merger/removal':r'merg|removal of|remove an? |unauthorized','condo conversion':'condominium conversion','tenant/eviction in text':r'tenant|evict|rent[- ]control','addition to existing bldg':r'addition','ADU':r'accessory dwelling|\badu','new construction':r'new construction|construct a new','density bonus':r'density bonus|home-sf','sro/group housing/hotel':r'\bsro\b|group housing|residential hotel|tourist hotel','cannabis/retail/restaurant':r'cannabis|formula retail|restaurant'}
print('\n== what kinds of projects each group shows up on (share of that group\'s first-hearing projects)')
out={}
for g in ['tenant','antidisp','construction','nhood','drteam','ALL']:
    s=h if g=='ALL' else h[h[f'{g}_first']==1]; out[g]={k:round(100*s.t.str.contains(p).mean()) for k,p in K.items()}; out[g].update({'n':len(s),'DR case':round(100*(s.dr==True).mean()),'10+ units':round(100*(s.units>=10).mean()),'50+ units':round(100*(s.units>=50).mean()),'mean other opp':round(s.opp_unaff.mean(),1),'mean other sup':round(s.sup_unaff.mean(),1),'low-price area':round(100*(s.terc=='low $/sqft').mean())})
print(pd.DataFrame(out).to_string())
# how the stall happened: last action calendar
def how(pid):
    q=it[it.id_parent==pid].sort_values('date'); last=q[q.date==q.date.max()]
    direction=q.A.str.lower().str.contains('direction|intent to|closing public comment|closing pc').any()
    cal='proposed-for-continuance calendar' if (last.section_group=='Items Proposed for Continuance').all() else 'after hearing (regular/DR calendar)'
    return pd.Series({'last_calendar':cal,'commission_direction_or_heard_then_continued':direction,'last_year':q.date.max().year,'n_dates':q.date.nunique()})
sk=h[h.soft==1]; hw=sk.index.to_series().apply(how); sk=sk.join(hw)
print('\n== how soft kills end (all 147)'); print(pd.crosstab(sk.last_calendar,sk.commission_direction_or_heard_then_continued,margins=True)); print('last hearing year:',sk.last_year.value_counts().sort_index().to_dict()); print('all first-heard years (for base):',h.year.value_counts().sort_index().to_dict())
for g in ['tenant','antidisp','construction']:
    s=sk[sk[f'{g}_first']==1]; print(f'\n######## soft-killed projects with {g} present at first hearing: {len(s)}')
    for pid,r in s.iterrows():
        q=it[it.id_parent==pid].sort_values('date'); txt=q.L.iloc[q.L.str.len().argmax()]; m=re.search(r'(request for.*|proposing.*|proposal.*)',txt); d=(m.group(1) if m else txt)
        gs=f[(f.pid==pid)&(f.g==g)].position.value_counts().to_dict()
        acts=' > '.join(f"{a.date.date()}:{a.A[:70]}" for a in q.drop_duplicates(['date','A']).itertuples() if a.A)
        print(f"- {pid} | {r.final} | units {r.units} | {g} stance {gs} | others opp {int(r.opp_unaff)} sup {int(r.sup_unaff)} | {r.last_calendar}\n    DESC: {d[:330]}\n    ACTS: {acts[:520]}")
# co-presence
print('\n== co-presence at first hearing (share of row-group projects where column-group also present)')
G=['tenant','antidisp','construction','nhood','prohousing','drteam']; print(pd.DataFrame({a:{b:round(100*h[h[f'{a}_first']==1][f'{b}_first'].mean()) for b in G} for a in G}).T.to_string())
