import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, re, pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_colwidth',400)
P,PJ=sys.argv[1:3]
it=pd.read_csv(P+'/items.csv.gz',low_memory=False); c=pd.read_csv(P+'/comments.csv',low_memory=False,usecols=['item_id','position','is_staff','role_group','text'])
c=c[c.is_staff!=1]; g=c.groupby('item_id').position
it['opp']=it.item_id.map(g.apply(lambda s:(s=='oppose').sum())).fillna(0).astype(int); it['sup']=it.item_id.map(g.apply(lambda s:(s=='support').sum())).fillna(0).astype(int)
it['date']=pd.to_datetime(it.meeting_date)
d=pd.read_csv(PJ); d['tot_opp']=d.id_parent.map(it.groupby('id_parent').opp.sum()); d['tot_sup']=d.id_parent.map(it.groupby('id_parent').sup.sum()); d['nh']=d.id_parent.map(it.groupby('id_parent').date.nunique())
d=d[(d.housing==1)&(d.year>=2015)]
def show(pid):
    q=it[it.id_parent==pid].sort_values(['date','item_num'])
    f=q.iloc[0]; txt=re.sub(r'\s+',' ',str(q[q.item_text.str.len()==q.item_text.str.len().max()].item_text.iloc[0]))
    print(f'\n--- {pid} | hearings {q.date.nunique()} | {q.date.min().date()} -> {q.date.max().date()} | opp {q.opp.sum()} sup {q.sup.sum()}')
    print('   TEXT:',txt[:520])
    for _,r in q.drop_duplicates(['date','ACTION']).iterrows():
        print(f"   {r.date.date()} [{str(r.section_group)[:12]}] rec={str(r.prelim_rec)[:45]!r} act={re.sub(chr(10),' ',str(r.ACTION))[:170]!r} ayes/nays={str(r.AYES)[:0]}{len(str(r.AYES).split(',')) if pd.notna(r.AYES) else '-'}-{len(str(r.NAYES).split(',')) if pd.notna(r.NAYES) and str(r.NAYES).strip().lower() not in ('none','') else 0} o{r.opp}/s{r.sup}")
cats={
 'A clean approval, no opposition':d[(d.y_notdecided==0)&(d.tot_opp==0)&(d.y_modified==0)&(d.y_disapprove==0)&(d.is_dr==0)&(d.nh==1)],
 'B approved w/ conditions, some opposition, one hearing':d[(d.y_notdecided==0)&(d.tot_opp.between(3,8))&(d.is_dr==0)&(d.nh==1)&(d.y_disapprove==0)],
 'C DR taken, modified':d[(d.is_dr==1)&(d.y_tookdr==1)&(d.y_disapprove==0)],
 'D DR not taken':d[(d.is_dr==1)&(d.y_tookdr==0)&(d.y_disapprove==0)&(d.y_nofinal==0)],
 'E heavy opposition, prolonged, approved':d[(d.tot_opp>=15)&(d.nh>=4)&(d.y_disapprove==0)&(d.y_nofinal==0)],
 'F disapproved':d[(d.y_disapprove==1)],
 'G no final vote':d[(d.y_nofinal==1)&(d.year<=2022)],
}
for k,v in cats.items():
    print('\n==========',k,'n=',len(v),'| median units',v.units.median(),'| median opp',v.tot_opp.median())
    for pid in v.sample(min(int(sys.argv[3]),len(v)),random_state=11).id_parent: show(pid)
