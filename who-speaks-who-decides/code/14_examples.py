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

allp=pd.read_csv(PJ)
tt=it.groupby('id_parent').agg(types=('record_type',lambda x:'|'.join(sorted(set(x.dropna())))),info=('prelim_rec',lambda x:x.fillna('').str.lower().str.contains('informational|review and comment').mean()),hasaddr=('item_text',lambda x:x.fillna('').str.contains(r'\b(?:Lot|Lots)\b.{0,40}Assessor').any()))
allp=allp.join(tt,on='id_parent',rsuffix='_all'); allp['tot_opp']=allp.id_parent.map(it.groupby('id_parent').opp.sum()); allp['nh']=allp.id_parent.map(it.groupby('id_parent').date.nunique())
leg=allp.types_all.str.contains('PCA|CWP|GPA|MAP|PPS',na=False)|(allp['info']>0.5)|(~allp.hasaddr)
print('all first-heard projects',len(allp),'| legislation/policy/informational or no parcel',int(leg.sum()))
site=allp[~leg&(allp.housing==1)]; print('site-specific housing projects',len(site))
def fin(r): return 'disapproved' if r.y_disapprove==1 else 'no final vote' if r.y_nofinal==1 else 'modified/DR taken' if r.y_modified==1 else 'approved as recommended'
site=site.assign(final=site.apply(fin,axis=1)); print(site.final.value_counts().to_frame('n').assign(share=lambda t:(t.n/len(site)).round(3)))
print(pd.crosstab(pd.cut(site.tot_opp,[-1,0,2,5,10,1e9],labels=['0','1-2','3-5','6-10','11+']),site.final,normalize='index').round(3).assign(n=pd.cut(site.tot_opp,[-1,0,2,5,10,1e9],labels=['0','1-2','3-5','6-10','11+']).value_counts(),mean_hearings=site.groupby(pd.cut(site.tot_opp,[-1,0,2,5,10,1e9],labels=['0','1-2','3-5','6-10','11+']),observed=True).nh.mean().round(2)))
print('DR share of site-specific',site.is_dr.mean().round(3),'| units median (known)',site.units.median(),'| units>=10 share',(site.units>=10).mean().round(3))
s2=site[site.year>=2015]
for pid in ['2016-000378','2020-005514','2016-010632']: show(pid)
print('\n##### big (>=20 units) heavy opposition'); 
for pid in s2[(s2.units>=20)&(s2.tot_opp>=10)].sort_values('tot_opp',ascending=False).head(6).id_parent: show(pid)
print('\n##### site-specific no final vote');
for pid in s2[(s2.final=='no final vote')&(s2.year<=2022)].sample(5,random_state=3).id_parent: show(pid)
print('\n##### site-specific disapproved');
for pid in s2[(s2.final=='disapproved')].sample(5,random_state=5).id_parent: show(pid)
w=it[(it.action_final=='withdraw')&(it.housing_kw==1)&(it.date>='2015')]
print('\n##### withdrawn'); 
for pid in w.id_parent.dropna().drop_duplicates().sample(3,random_state=2): show(pid)
