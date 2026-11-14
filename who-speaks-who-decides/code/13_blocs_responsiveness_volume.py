import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, re, pandas as pd, numpy as np
pd.set_option('display.width',250)
P=sys.argv[1]
it=pd.read_csv(P+'/items.csv.gz',low_memory=False); c=pd.read_csv(P+'/comments.csv',low_memory=False); c=c[c.is_staff!=1]
it['date']=pd.to_datetime(it.meeting_date); it['year']=it.date.dt.year; c['date']=pd.to_datetime(c.meeting_date)
def names(s):
    if pd.isna(s): return []
    s=re.sub(r'\(.*?\)','',str(s)); s=re.split(r'\s{2,}|\n|ADJOURN|MOTION|RESOLUTION|ABSENT|RECUSED|NAYES|EXCUSED',s)[0]
    return [x.strip().title() for x in re.split(r',|;| and |&',s) if 1<len(x.strip())<25 and re.match(r"^[A-Za-z .'\-]+$",x.strip()) and x.strip().lower()!='none']
it['ay']=it.AYES.map(names); it['na']=it.NAYES.map(names)
v=it[(it.ay.str.len()>=3)&(it.ay.str.len()+it.na.str.len()<=7)&it.section_group.isin(['Regular Calendar','Discretionary Review'])&it.action_final.isin(['approve','approve with conditions','disapprove'])].copy(); v['split']=v.na.str.len()>0
g=c.groupby('item_id').position; v['opp']=v.item_id.map(g.apply(lambda s:(s=='oppose').sum())).fillna(0)
BOARD={'Moore','Imperial','Williams'}; MAYOR={'Koppel','Diamond','Tanner','Braun','So','Mcgarry','Campbell'}
rows=[]
for r in v[v.split&(v.date>='2020-03-01')].itertuples():
    pro_side='ay' if r.action_final!='disapprove' else 'na'
    for n in r.ay: rows.append((r.item_id,n,pro_side=='ay'))
    for n in r.na: rows.append((r.item_id,n,pro_side=='na'))
d=pd.DataFrame(rows,columns=['item','name','pro']); d['grp']=np.where(d.name.isin(BOARD),'Board-President appointees (3 verified)',np.where(d.name.isin(MAYOR),'Mayoral appointees (7 named in sources)','other/unverified'))
print('split votes since March 2020:',d.item.nunique()); print(d.groupby('grp').pro.agg(['size','mean']).round(3).to_string())
piv=d[d.grp!='other/unverified'].groupby(['item','grp']).pro.mean().unstack(); both=piv.dropna(); print('split items where both groups voted:',len(both),'| groups on opposite sides (all Board appointees vs all mayoral):',int(((both.iloc[:,0]==0)&(both.iloc[:,1]==1)).sum()+((both.iloc[:,0]==1)&(both.iloc[:,1]==0)).sum()),'| Board group less pro-project than mayoral:',round((both.iloc[:,0]<both.iloc[:,1]).mean(),3))
print('\nresponsiveness by era: split-vote rate and "took review / disapproved" by opposition')
v['era']=pd.cut(v.year,[2004,2017,2023,2026],labels=['2005-17','2018-23','2024-26']); v['ob']=pd.cut(v.opp,[-1,0,5,1e9],labels=['0','1-5','6+'])
print(v.pivot_table(index='era',columns='ob',values='split',aggfunc=['mean','size'],observed=True).round(3).to_string())
v['dis']=v.action_final=='disapprove'; print(v.pivot_table(index='era',columns='ob',values='dis',aggfunc='mean',observed=True).round(3).to_string())
dr=it[(it.section_group=='Discretionary Review')&it.action_dr.notna()&(it.year>=2014)].copy(); dr['opp']=dr.item_id.map(g.apply(lambda s:(s=='oppose').sum())).fillna(0); dr['era']=pd.cut(dr.year,[2013,2017,2019,2023,2026],labels=['2014-17','2018-19','2020-23','2024-26']); dr['took']=dr.action_dr=='dr'
print('review taken by era:',dr.groupby('era',observed=True).took.agg(['size','mean']).round(3).to_dict('index')); print('review taken by era x opposition>=3:',dr.pivot_table(index='era',columns=dr.opp>=3,values='took',aggfunc=['mean','size'],observed=True).round(2).to_string())
print('\nvolume: site-specific agenda activity by half-year (regular+DR calendar items with a decision; housing 10+ unit projects first heard)')
h=pd.read_csv(WORK+'/site_projects.csv',index_col=0); h['first']=pd.to_datetime(h['first']); h['half']=h['first'].dt.to_period('2Q')
it['half']=it.date.dt.to_period('2Q'); a=it[(it.date>='2021-01-01')&it.section_group.isin(['Regular Calendar','Discretionary Review'])].groupby('half').agg(items=('item_id','size'),meetings=('meeting_date','nunique'),housing_items=('housing_kw','sum'),dr_items=('section_group',lambda s:(s=='Discretionary Review').sum()))
a['big_housing_first_heard']=h[(h.units>=10)&(h['first']>='2021-01-01')].groupby('half').size(); a['cua_317_items']=it[(it.date>='2021-01-01')&(it.record_type=='CUA')&it.section_group.isin(['Regular Calendar'])].groupby('half').size(); print(a.fillna(0).astype(int).to_string())
sp=c[c.channel=='spoken']
for lab,a_,b_ in [('2018-01..2020-02 in person','2018-01-01','2020-02-29'),('2020-04..2022-03 remote','2020-04-01','2022-03-31'),('2022-04..2023-12 hybrid','2022-04-01','2023-12-31'),('2024-01..2026-03 no remote comment','2024-01-01','2026-03-31')]:
    d=sp[(sp.date>=a_)&(sp.date<=b_)]; so=d[d.position.isin(['support','oppose'])&(d.position_source=='stenographer')]; nm=d[d.commenter_id.notna()]; first=(nm.groupby('commenter_id').date.transform('min')==sp.groupby('commenter_id').date.min().reindex(nm.commenter_id).values)
    items=d.item_id.nunique()
    print(f'{lab:36s} meetings {d.meeting_date.nunique():3d} | comments/meeting {len(d)/d.meeting_date.nunique():5.1f} | comments per commented item {len(d)/items:4.1f} | unnamed {100*d.commenter_id.isna().mean():4.1f}% | first-ever {100*first.mean():4.1f}% | support {100*(so.position=="support").mean():4.1f}% | org-affiliated {100*d.role_long.notna().mean():4.1f}%')
