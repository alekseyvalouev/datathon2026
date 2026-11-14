import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, re, pandas as pd, numpy as np
pd.set_option('display.width',230); pd.set_option('display.max_columns',60); pd.set_option('display.max_colwidth',170)
P=sys.argv[1]
c=pd.read_csv(P+'/comments.csv',low_memory=False); it=pd.read_csv(P+'/items.csv.gz',low_memory=False)
it['date']=pd.to_datetime(it.meeting_date); it['year']=it.date.dt.year
c=c[c.is_staff!=1]; g=c.groupby('item_id').position
it['n_opp']=it.item_id.map(g.apply(lambda s:(s=='oppose').sum())).fillna(0); it['n_sup']=it.item_id.map(g.apply(lambda s:(s=='support').sum())).fillna(0)
A=it.ACTION.fillna('').str.lower()
it['indef']=A.str.contains('indefinite'); it['withdrawn_txt']=A.str.contains('withdraw'); it['modif']=A.str.contains(r'modif|as amended|amended to|revis|reduc|setback|set back|eliminat|remov')
proj=it[it.id_parent.notna()&it.section_group.isin(['Regular Calendar','Discretionary Review','Consent Calendar','Items Proposed for Continuance'])&(it.year>=2005)].copy()
print('== 1. item-level actions by calendar section (2005+)'); print(pd.crosstab(proj.section_group,proj.action_final.fillna('NA'),normalize='index').round(3).assign(n=proj.section_group.value_counts()))
print('\n== 2. staff recommendation vs action, decided items only (regular+DR)')
d=proj[proj.section_group.isin(['Regular Calendar','Discretionary Review'])&proj.action_final.isin(['approve','approve with conditions','disapprove'])]
print('staff rec distribution:',d.rec_final.fillna('NA').value_counts(normalize=True).round(3).to_dict())
x=d[d.rec_final.isin(['approve','approve with conditions','disapprove'])]; x=x.assign(rec_pos=x.rec_final!='disapprove',act_pos=x.action_final!='disapprove')
print(pd.crosstab(x.rec_pos,x.act_pos,margins=True)); print('commission follows staff direction:',(x.rec_pos==x.act_pos).mean().round(4))
print('\n== 3. DR items: outcomes'); dr=proj[(proj.section_group=='Discretionary Review')]
print(dr.action_dr.fillna('NA').value_counts().to_dict()); print(pd.crosstab(dr.rec_dr.fillna('NA'),dr.action_dr.fillna('NA')))
print(dr.action_final.fillna('NA').value_counts().to_dict())
print('\n== 4. project-level funnel (id_parent), housing projects')
h=proj[proj.housing_kw==1].sort_values('date')
def summ(q):
    last=q.iloc[-1]; dec=q[q.action_final.isin(['approve','approve with conditions','disapprove','withdraw'])]
    fin=dec.iloc[-1].action_final if len(dec) else ('indef_cont' if q.indef.any() else 'cont_only' if (q.action_final=='continuance').any() else 'no_action_recorded')
    if len(dec)==0 and q.withdrawn_txt.any(): fin='withdraw'
    return pd.Series({'first':q.date.iloc[0],'last':q.date.iloc[-1],'n_hear':q.date.nunique(),'n_cont':(q.action_final=='continuance').sum(),'final':fin,'opp':q.n_opp.sum(),'sup':q.n_sup.sum(),'modif':q.modif.any(),'cond':(q.action_final=='approve with conditions').any(),'units':q.prj_number_of_units_net.max(),'dr':(q.section_group=='Discretionary Review').any(),'lat':q.latitude.max(),'lon':q.longitude.max(),'status':q.prj_record_status.iloc[-1]})
pj=h.groupby('id_parent').apply(summ,include_groups=False); pj['days']=(pj['last']-pj['first']).dt.days
print('housing projects',len(pj)); print(pj.final.value_counts().to_frame('n').assign(share=lambda t:(t.n/len(pj)).round(3)))
old=pj[pj['first']<'2024-01-01']; print('first heard before 2024:',len(old)); print(old.final.value_counts(normalize=True).round(3).to_dict())
print('hearings per project:',pj.n_hear.describe().round(2).to_dict()); print('share with >=1 continuance',(pj.n_cont>0).mean().round(3),' >=3',(pj.n_cont>=3).mean().round(3))
print('prj_record_status:',pj.status.fillna('NA').value_counts().head(10).to_dict())
print('\n== 5. opposition vs soft outcomes (housing projects with any signed comment)')
s=pj[(pj.opp+pj.sup)>0].copy(); s['oppbin']=pd.cut(s.opp,[-1,0,2,5,10,1e9],labels=['0','1-2','3-5','6-10','11+'])
print(s.groupby('oppbin',observed=True).agg(n=('final','size'),disapproved=('final',lambda v:(v=='disapprove').mean()),withdrawn=('final',lambda v:(v=='withdraw').mean()),unresolved=('final',lambda v:v.isin(['indef_cont','cont_only','no_action_recorded']).mean()),any_cont=('n_cont',lambda v:(v>0).mean()),mean_cont=('n_cont','mean'),median_days=('days','median'),conditions=('cond','mean'),modif_lang=('modif','mean'),median_units=('units','median')).round(3).to_string())
print('\n== 6. disapproval rate by period (decided regular+DR items)'); d2=d.assign(per=pd.cut(d.year,[2004,2009,2014,2018,2022,2026]))
print(d2.groupby('per',observed=True).agg(n=('item_id','size'),disapprove=('action_final',lambda v:(v=='disapprove').mean()),housing_dis=('housing_kw',lambda v:((v==1)&(d2.loc[v.index,'action_final']=='disapprove')).sum())).round(4))
print('\n== 7. what gets disapproved (housing, sample)'); dis=d[(d.action_final=='disapprove')]; print('n',len(dis),'by type',dis.record_type.value_counts().head(8).to_dict(),'| staff rec',dis.rec_final.fillna('NA').value_counts().to_dict())
print(dis[dis.housing_kw==1].sample(10,random_state=4).assign(t=lambda q:q.item_text.str.replace(r'\s+',' ',regex=True).str[:230])[['year','record_type','rec_final','n_opp','n_sup','t']].to_string(index=False))
print('\n== 8. sample ACTION text with modification language'); print(it[it.modif&(it.housing_kw==1)&(it.year>=2015)].ACTION.str.replace(r'\s+',' ',regex=True).str[:260].sample(8,random_state=5).to_string(index=False))
pj.to_csv(sys.argv[2])
