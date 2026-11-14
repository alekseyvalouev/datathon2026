import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, re, pandas as pd, numpy as np
pd.set_option('display.width',260); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',200)
P=sys.argv[1]
h=pd.read_csv(WORK+'/heard_dedup.csv',index_col=0); c=pd.read_csv(WORK+'/c_groups.csv',low_memory=False,parse_dates=['date'])
raw=pd.read_csv(P+'/comments.csv',low_memory=False,usecols=['comment_id','text']); c=c.merge(raw,on='comment_id',how='left')
c['year']=c.date.dt.year; c['sup']=(c.position=='support').astype(int)
nall=c.commenter_id.map(c.commenter_id.value_counts()); c['onetime']=(nall==1).astype(int)
print('== A. participation by year (site-specific housing projects)')
def conc(g):
    v=g.commenter_id.dropna().value_counts(); k=max(1,int(len(v)*0.05)); return v.head(k).sum()/max(len(g),1)
y=c[c.year.between(2005,2025)].groupby('year').apply(lambda g:pd.Series({'comments':len(g),'projects':g.pid.nunique(),'per_project':len(g)/g.pid.nunique(),'support':g.sup.mean(),'email':(g.channel=='email').mean(),'unaff':(g.g=='unaff').mean(),'prohousing':(g.g=='prohousing').mean(),'nhood':(g.g=='nhood').mean(),'construction':(g.g=='construction').mean(),'tenant+antidisp':g.g.isin(['tenant','antidisp']).mean(),'drteam':(g.g=='drteam').mean(),'top5pct_share':conc(g)}),include_groups=False)
print(y.round(3).to_string())
sp=c[c.channel=='spoken']; print('\nspoken-only support share by period:',sp.groupby(pd.cut(sp.year,[2004,2009,2014,2017,2019,2022,2026])).sup.agg(['size','mean']).round(3).to_dict('index'))
print('\n== B. hearings per project by first-heard year (deduplicated projects)')
h['big']=h.units>=10
b=h.groupby('year').apply(lambda g:pd.Series({'n':len(g),'mean_hearings':g.nh.mean(),'3plus':(g.nh>=3).mean(),'6plus':(g.nh>=6).mean(),'big_n':g.big.sum(),'big_mean_hearings':g[g.big].nh.mean(),'big_6plus':(g[g.big].nh>=6).mean(),'stalled':g.soft.mean(),'disapproved':(g.final=='disapproved').mean(),'dr_share':(g.dr==True).mean(),'mean_opp':g.opp.mean()}),include_groups=False)
print(b.round(3).to_string())
for lab,m in [('all',h.year>0),('10+ units',h.big),('DR',h.dr==True)]:
    a=h[m&h.year.between(2015,2019)]; z=h[m&h.year.between(2020,2023)]
    print(f'  {lab}: 2015-19 n={len(a)} mean hearings {a.nh.mean():.2f}, 6+ {100*(a.nh>=6).mean():.1f}% | 2020-23 n={len(z)} mean {z.nh.mean():.2f}, 6+ {100*(z.nh>=6).mean():.1f}%')
print('\n== D. themes in comment text by period (share of comments with text)')
TH={'affordability':r'afford|luxury|market[- ]rate|low[- ]income|bmr','displacement/tenants':r'displac|evict|tenant|gentrif|rent control','height/scale':r'height|tall|stor(?:y|ies)|bulk|scale|massing|density','light/shadow/views/privacy':r'shadow|light|sun|view|privacy','parking/traffic':r'parking|traffic|congest','character/historic':r'character|historic|preserv|context','process/notice':r'notice|outreach|process|not informed','housing need':r'housing (?:crisis|shortage|need)|need(?:s|ed)? (?:more )?housing|more housing|more homes|supply','jobs/labor':r'job|labor|union|carpenter|wage','climate/transit/bike':r'climate|transit|bike|bicycl|muni|bart|walkab','family/children/schools':r'famil|children|school|kids'}
t=c[c.text.fillna('').str.len()>12].copy(); t['tl']=t.text.str.lower(); t['per']=pd.cut(t.year,[2004,2009,2014,2019,2026],labels=['2005-09','2010-14','2015-19','2020-26'])
out={}
for k,p in TH.items():
    m=t.tl.str.contains(p); out[k]=t.assign(m=m).groupby('per',observed=True).m.mean()
    out[k+' |opp-sup|']=pd.Series({'gap':m[t.position=='oppose'].mean()-m[t.position=='support'].mean()})
T=pd.DataFrame({k:v for k,v in out.items() if '|' not in k}).T; T['oppose_minus_support']=[out[k+' |opp-sup|'].gap for k in T.index]; print((100*T).round(1).to_string()); print('n by period',t.per.value_counts().sort_index().to_dict())
print('\n== G. deference to staff by period (all decided regular+DR items)')
it=pd.read_csv(P+'/items.csv.gz',low_memory=False); it['year']=pd.to_datetime(it.meeting_date).dt.year
d=it[it.section_group.isin(['Regular Calendar','Discretionary Review'])&it.action_final.isin(['approve','approve with conditions','disapprove'])&it.rec_final.isin(['approve','approve with conditions','disapprove'])&(it.year>=2005)].copy()
d['rp']=d.rec_final!='disapprove'; d['ap']=d.action_final!='disapprove'; d['mod']=it.ACTION.fillna('').str.lower().str.contains(r'modif|as amended|amended to')
d['per']=pd.cut(d.year,[2004,2009,2014,2019,2026],labels=['2005-09','2010-14','2015-19','2020-26'])
print(d.groupby('per',observed=True).apply(lambda g:pd.Series({'n':len(g),'staff_rec_disapprove':(~g.rp).mean(),'commission_disagrees':(g.rp!=g.ap).mean(),'more_negative_than_staff':(g.rp&~g.ap).mean(),'more_positive_than_staff':(~g.rp&g.ap).mean(),'amended_or_modified':g['mod'].mean()}),include_groups=False).round(3).to_string())
dr=it[(it.section_group=='Discretionary Review')&it.action_dr.notna()&(it.year>=2005)].copy(); dr['per']=pd.cut(dr.year,[2004,2009,2014,2019,2026],labels=['2005-09','2010-14','2015-19','2020-26'])
print('discretionary review: cases with coded outcome and share where review was taken:'); print(dr.groupby('per',observed=True).action_dr.agg(n='size',took=lambda s:(s=='dr').mean()).round(3).to_string())
allit=it[(it.section_group=='Discretionary Review')&(it.year>=2005)]; print('DR-calendar items per year:',allit.groupby('year').id_parent.nunique().to_dict())
