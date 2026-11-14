import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, re, pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',40); pd.set_option('display.max_colwidth',160)
P=sys.argv[1]
pj=pd.read_csv(WORK+'/site_projects.csv',index_col=0); it=pd.read_csv(P+'/items.csv.gz',low_memory=False); call=pd.read_csv(P+'/comments.csv',low_memory=False)
it['L']=it.item_text.fillna('').str.lower().str.replace(r'\s+',' ',regex=True)
tx=it.groupby('id_parent').L.apply(lambda x:' || '.join(x.unique())); pj['txt']=pj.index.map(tx)
print('################ PART 1: affordable share and approval')
b=pj[(pj.u_prj>=10)&(pj.aff_prj>=0)].copy(); b['sh']=(b.aff_prj/b.u_prj).clip(0,1); b['year']=pd.to_datetime(b['first']).dt.year
b['bonus']=b.txt.str.contains('density bonus|home-sf|home sf'); b['fee']=b.txt.str.contains(r'in-lieu|in lieu|affordable housing fee')
print('share histogram (projects with 0<share<0.5):'); print(pd.cut(b[(b.sh>0)&(b.sh<.5)].sh,[0,.10,.115,.125,.14,.155,.17,.19,.21,.26,.5]).value_counts().sort_index().to_string())
b['bucket']=pd.cut(b.sh,[-.01,0,.2,.99,1],labels=['0 on site','1-20%','21-99%','100%'])
def summ(g): return pd.Series({'n':len(g),'median_units':g.u_prj.median(),'approved':(g.out=='approved').mean(),'disapproved':(g.out=='disapproved').mean(),'mean_hearings':g.nh.mean(),'share_3plus_hearings':(g.nh>=3).mean(),'mean_opp':g.opp.mean(),'mean_sup':g.sup.mean(),'opp_share':g.opp.sum()/max(g.opp.sum()+g.sup.sum(),1),'bonus':(g.bonus.mean() if 'bonus' in g else np.nan)})
print(b.groupby('bucket',observed=True).apply(summ,include_groups=False).round(2).to_string())
print('\nby density bonus / HOME-SF use (10+ units):'); print(b.groupby('bonus').apply(summ,include_groups=False).round(2).to_string())
print('bonus use by era:', b.groupby(pd.cut(b.year,[2004,2012,2016,2019,2026]),observed=True).bonus.agg(['mean','sum','size']).round(2).to_dict('index'))
bb=b[b.bonus]; print('bonus projects affordable share: median',bb.sh.median().round(3),'| zero recorded',(bb.sh==0).sum(),'of',len(bb))
# size-matched: 25-150 units, since 2012
m=b[b.u_prj.between(25,200)&(b.year>=2012)&(b.sh<.99)]; print('\nsize-matched (25-200 units, 2012+, not 100% affordable):'); print(m.groupby(m.sh>0).apply(summ,include_groups=False).round(2).rename(index={False:'0 on site',True:'some on site'}).to_string())
from sklearn.linear_model import LogisticRegression, LinearRegression
r=b[b.sh<.99].copy().reset_index(drop=True); X=pd.DataFrame({'has_onsite':(r.sh>0).astype(int),'bonus':r.bonus.astype(int),'log_units':np.log(r.u_prj),'year':r.year-2015,'low_price':(r.terc=='low $/sqft').astype(int)})
rng=np.random.default_rng(0)
def bootfit(y,kind):
    out=[]
    for _ in range(400):
        i=rng.integers(0,len(r),len(r))
        if kind=='logit':
            if y[i].min()==y[i].max(): continue
            out.append(LogisticRegression(C=1e4,max_iter=2000).fit(X.iloc[i],y[i]).coef_[0])
        else: out.append(LinearRegression().fit(X.iloc[i],y[i]).coef_)
    o=np.array(out); return {k:(round(float(np.median(o[:,j])),2),[round(float(np.percentile(o[:,j],2.5)),2),round(float(np.percentile(o[:,j],97.5)),2)]) for j,k in enumerate(X.columns)}
print('n',len(r)); print('3+ hearings (log-odds, 95% bootstrap):',bootfit((r.nh>=3).astype(int).values,'logit'))
print('approved (log-odds):',bootfit((r.out=='approved').astype(int).values,'logit'))
print('opposing comments (count):',bootfit(r.opp.values,'ols'))

print('\n################ PART 2: the unaffiliated')
call=call[call.is_staff!=1]; nall=call.commenter_id.map(call.commenter_id.value_counts())
c=call.merge(it[['item_id','id_parent']].rename(columns={'id_parent':'pid'}),on='item_id'); c=c[c.pid.isin(pj.index)&c.position.isin(['support','oppose'])].copy()
c=c.join(pj[['kind','aff','units','terc','dr']],on='pid'); c['sup']=(c.position=='support').astype(int); c['n_all']=c.commenter_id.map(call.commenter_id.value_counts())
c['year']=pd.to_datetime(c.meeting_date).dt.year
u=c[c.role_long.isna()].copy(); print('unaffiliated comments',len(u),'| unique commenter ids',u.commenter_id.nunique(),'| no id',u.commenter_id.isna().sum(),'| anonymous flag',int((u.is_anonymous==1).sum()),'| email',int((u.channel=='email').sum()),'| campaign email',int((u.is_campaign==1).sum()))
u['freq']=pd.cut(u.n_all.fillna(0),[-1,0,1,2,5,20,1e9],labels=['no id/anonymous','1 comment ever','2','3-5','6-20','21+'])
print(u.groupby('freq',observed=True).sup.agg(n='size',support='mean').round(3).assign(share=lambda t:(t.n/len(u)).round(3)).to_string())
pp=u.groupby('commenter_id').pid.nunique(); print('people who commented on exactly one project:',(pp==1).mean().round(3),'| on 5+ projects:',(pp>=5).sum())
t=u.text.fillna('').str.lower()
SELF={'neighbor / lives nearby':r'neighbor|next door|adjacent|across the street|abut|lives? (?:on|at|near|in the)|resident of|nearby resident|block','tenant / renter of the building':r'\btenant|renter|\brents?\b|evict|lived (?:here|there)','property owner / homeowner':r'homeowner|property owner|\bowner\b|owns','business owner / merchant':r'business owner|merchant|store owner|restaurant|shop','worker / union / builder':r'\bunion\b|carpenter|worker|local \d+|laborer|contractor|electrician','family / senior / parent':r'famil|senior|elder|children|\bkids\b|parent','speaks for a group':r'on behalf|represent|association|coalition|committee|club|council'}
has=t.str.len()>3; print('unaffiliated with any text',int(has.sum()))
rows=[{'self-description in note':k,'n':int(t[has].str.contains(p).sum()),'share':t[has].str.contains(p).mean(),'support':u[has][t[has].str.contains(p)].sup.mean()} for k,p in SELF.items()]
print(pd.DataFrame(rows).round(3).to_string(index=False)); anyself=t.str.contains('|'.join(SELF.values())); print('none of these cues:',(~anyself[has]).mean().round(3),'support among them',u[has&~anyself].sup.mean().round(3))
print('\nunaffiliated support by project kind:'); print(u.groupby('kind').sup.agg(n='size',support='mean').round(3).to_string())
print('by channel:',u.groupby('channel').sup.agg(['size','mean']).round(3).to_dict('index')); print('campaign vs not (email):',u[u.channel=='email'].groupby('is_campaign').sup.agg(['size','mean']).round(3).to_dict('index'))
print('by era:',u.groupby(pd.cut(u.year,[2004,2010,2015,2019,2026]),observed=True).sup.agg(['size','mean']).round(3).to_dict('index'))
big=u[u.units>=10]; print('10+ unit projects by price tercile:',big.groupby('terc',observed=True).sup.agg(['size','mean']).round(3).to_dict('index'))
# one-off concentration: share of unaffiliated comments in items where >=10 unaffiliated spoke
k=u.groupby('pid').size(); print('share of unaffiliated comments on projects with 20+ such comments:',(u.pid.map(k)>=20).mean().round(3),'| projects:',int((k>=20).sum()),'of',len(k))
print('top 8 projects by unaffiliated comments:'); top=k.sort_values(ascending=False).head(8)
for pid,n in (top.items() if SHOW else []): print('  ',n,'| support',round(u[u.pid==pid].sup.mean(),2),'|',re.sub(r'^.*?\)\s*','',pj.loc[pid,'txt'])[:95])

print('\n################ PART 3: DR team and how affiliation relates to stance')
d=c[c.role_long=='DR Team']; print('DR Team comments',len(d),'| support',d.sup.mean().round(3),'| on DR-calendar projects',d.dr.mean().round(3),'| role_source',d.role_source.value_counts().to_dict())
if SHOW: print('sample role_title/comment for DR Team:'); print(d[['role_title','text']].dropna(subset=['text']).sample(8,random_state=2).assign(text=lambda x:x.text.str.replace(r'\s+',' ',regex=True).str[:110]).to_string(index=False))
c['role']=c.role_long.fillna('Unaffiliated'); grp={'YIMBY':'Pro-housing / YIMBY / SPUR','Pro-Housing Advocacy':'Pro-housing / YIMBY / SPUR','SPUR':'Pro-housing / YIMBY / SPUR','Anti-Displacement':'Anti-displacement / identity groups','Race/Immigration/LGBTQ Groups':'Anti-displacement / identity groups','Slow Growth':'Neighborhood Association','Historic Preservation':'Neighborhood Association','Labor':'Construction'}
c['role2']=c.role.replace(grp); keep=['Unaffiliated','Project Team','DR Team','Neighborhood Association','Construction','Pro-housing / YIMBY / SPUR','Tenant Association','Anti-displacement / identity groups']; c2=c[c.role2.isin(keep)].copy()
c2['proj_mean']=c2.groupby('pid').sup.transform('mean'); c2['n_proj']=c2.groupby('pid').sup.transform('size')
w=c2[c2.n_proj>=5]; print('\nstance relative to everyone else on the SAME project (projects with 5+ comments):'); print(w.groupby('role2').apply(lambda g:pd.Series({'n':len(g),'raw_support':g.sup.mean(),'project_avg':g.proj_mean.mean(),'gap_vs_same_project':(g.sup-g.proj_mean).mean()}),include_groups=False).round(3).sort_values('gap_vs_same_project').to_string())
c2['size']=np.where(c2.dr==True,'DR case',np.where(c2.units>=50,'50+ units',np.where(c2.units>=10,'10-49 units','<10 / unknown')))
c2['demo']=c2.pid.map(pj.txt.str.contains('demoli')); c2['affk']=np.where(c2.units>=10,c2.aff,'(small)')
for col in ['size','affk','terc','demo']:
    x=c2.pivot_table(index='role2',columns=col,values='sup',aggfunc='mean',observed=True).round(2); n=c2.pivot_table(index='role2',columns=col,values='sup',aggfunc='size',observed=True)
    print(f'\nsupport share by role x {col} (cells with <15 comments blanked)'); print(x.where(n>=15).to_string())
# consistency of repeat commenters by role
v=c.groupby(['commenter_id']).agg(n=('sup','size'),s=('sup','mean'),role=('role2' if 'role2' in c else 'role',lambda x:x.mode().iloc[0])); v=v[v.n>=5]
v['type']=np.select([v.s>=.9,v.s<=.1],['always support','always oppose'],'mixed'); print('\nrepeat commenters (5+ comments on these projects) by modal role:'); print(pd.crosstab(v.role,v.type).assign(n=lambda t:t.sum(axis=1)).sort_values('n',ascending=False).head(9).to_string())
# within-person: same person, with vs without stated affiliation
pc=c[c.commenter_id.isin(c[c.role!='Unaffiliated'].commenter_id)&~c.role.isin(['Project Team','DR Team','Legal'])]; g=pc.groupby('commenter_id').role.nunique(); both=pc[pc.commenter_id.isin(c[c.role=='Unaffiliated'].commenter_id)]
print('\npeople with an org label on some comments and none on others:',both.commenter_id.nunique(),'| support when labelled',both[both.role!='Unaffiliated'].sup.mean().round(3),'| when unlabelled',both[both.role=='Unaffiliated'].sup.mean().round(3))
