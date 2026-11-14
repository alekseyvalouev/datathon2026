import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, re, pandas as pd, numpy as np
from sklearn.neighbors import BallTree
pd.set_option('display.width',250); pd.set_option('display.max_columns',40); pd.set_option('display.max_colwidth',200)
P,Z=sys.argv[1:3]
it=pd.read_csv(P+'/items.csv.gz',low_memory=False); c=pd.read_csv(P+'/comments.csv',low_memory=False)
it['date']=pd.to_datetime(it.meeting_date); it['year']=it.date.dt.year; it=it[(it.year>=2005)&it.id_parent.notna()]
T=it.item_text.fillna('').str.replace(r'\s+',' ',regex=True); L=T.str.lower(); it['L']=L
UR=r'([\d,]+)\s*(?:\([^)]*\)\s*)?(?:(?:new|residential|dwelling|affordable|rental|senior|housing|sro|group housing|family|market-rate|market rate)\s+)*units'
def units(t):
    v=[int(x.replace(',','')) for x in re.findall(UR,t) if x.replace(',','').isdigit()]; v=[x for x in v if 0<x<6000]; return max(v) if v else np.nan
it['u']=L.map(units)
g=it.groupby('id_parent')
pj=g.agg(first=('date','min'),last=('date','max'),nh=('date','nunique'),types=('record_type',lambda x:'|'.join(sorted(set(x.dropna())))),housing=('housing_kw','max'),u_txt=('u','max'),u_prj=('prj_number_of_units_prop','max'),aff_prj=('prj_number_of_affordable_units','max'),
  txt=('L',lambda x:' || '.join(x.unique())[:20000]),info=('prelim_rec',lambda x:x.fillna('').str.lower().str.contains('informational|review and comment').mean()),lat=('latitude','max'),lon=('longitude','max'),
  dis=('action_final',lambda x:(x=='disapprove').any()),appr=('action_final',lambda x:x.isin(['approve','approve with conditions']).any()),dr=('section_group',lambda x:(x=='Discretionary Review').any()))
pj['hasaddr']=pj.txt.str.contains(r'\blots?\b.{0,40}assessor'); leg=pj.types.str.contains('PCA|CWP|GPA|MAP|PPS')|(pj['info']>0.5)|~pj.hasaddr
pj=pj[~leg&(pj.housing==1)].copy(); pj['units']=pj[['u_txt','u_prj']].max(axis=1)
newres=pj.txt.str.contains(r'construct|new construction|conver|addition of|add |establish')&pj.txt.str.contains('dwelling unit|residential unit|housing unit|affordable|units')
t=pj.txt
allaff=t.str.contains(r'100\s?%\s*affordable|100 percent affordable|100-percent affordable|all[- ]affordable|fully affordable|affordable housing project|affordable senior|supportive housing|affordable to (?:very )?low|low[- ]income housing')|((pj.aff_prj>=0.9*pj.u_prj)&(pj.u_prj>=5))
mixed=t.str.contains(r'inclusionary|below[- ]market|\bbmr\b|density bonus|home-sf|home sf|on-site affordable|onsite affordable|affordable (?:dwelling )?units|affordable housing')|(pj.aff_prj>0)
pj['aff']=np.select([allaff,mixed],['100% affordable','mixed/inclusionary or bonus'],'no affordability mention')
pj['size']=pd.cut(pj.units,[0,2,9,49,1e6],labels=['1-2 units','3-9','10-49','50+']).astype(str).replace('nan','units unknown')
pj['kind']=np.where(pj.dr,'DR (mostly houses)',np.where(pj.units>=10,pj.aff.map({'100% affordable':'10+ units: 100% affordable','mixed/inclusionary or bonus':'10+ units: mixed-income','no affordability mention':'10+ units: no affordable mention'}),'small non-DR (<10 or unknown)'))
print('site-specific housing-keyword projects',len(pj)); print(pj.kind.value_counts())
for k,p in {'density bonus':'density bonus','home-sf':'home-sf|home sf','inclusionary/bmr':r'inclusionary|below[- ]market|\bbmr\b','in-lieu / fee':r'in-lieu|in lieu|affordable housing fee','mohcd/tax credit/public funding':r'mohcd|mayor.s office of housing|tax credit|tax-exempt|bond','development agreement':'development agreement','senior':'senior','student':'student housing','group housing/sro':r'group housing|\bsro\b','demolition':'demoli','condo conversion':'condominium conversion','merger':'merg'}.items():
    m=t.str.contains(p); print(f'  text mentions {k:32s} {int(m.sum()):5d} projects  ({int((m&(pj.units>=10)).sum())} with 10+ units)')
big=pj[pj.units>=10]; print('\n10+ unit projects',len(big),'| total units proposed (text/prj max)',int(big.units.sum()))
print(big.groupby('aff').agg(n=('units','size'),units=('units','sum'),median_units=('units','median'),aff_units_prj=('aff_prj','sum')).assign(unit_share=lambda x:(x.units/x.units.sum()).round(3)))
# comments
c=c[c.is_staff!=1].merge(it[['item_id','id_parent']],on='item_id',suffixes=('','_i')); c=c[c.id_parent.isin(pj.index)].join(pj[['kind','aff','units','lat','lon']],on='id_parent')
c=c[c.position.isin(['support','oppose'])]
print('\ncomments with support/oppose on these projects',len(c),'| with any role label',c.role_long.notna().mean().round(3))
def tab(df,col):
    r=df.groupby(col,observed=True).position.agg(n='size',support=lambda s:(s=='support').mean()).round(3); return r.sort_values('n',ascending=False)
print('\n== position by project kind'); print(tab(c,'kind'))
c['role']=c.role_long.fillna('(no affiliation recorded)')
print('\n== position by speaker role (all site-specific housing)'); r=tab(c,'role'); r['share_of_comments']=(r.n/len(c)).round(3); print(r.head(24))
cb=c[c.units>=10]
print('\n== 10+ unit projects: support share by role x affordability'); x=cb.pivot_table(index='role',columns='aff',values='position',aggfunc=[lambda s:(s=='support').mean(),'size']).round(2); x.columns=[f'{a[1][:14]}_{"sup" if "lambda" in a[0] else "n"}' for a in x.columns]; x['n']=x.filter(like='_n').sum(axis=1); print(x.sort_values('n',ascending=False).head(18))
pjc=c.groupby('id_parent').position.agg(opp=lambda s:(s=='oppose').sum(),sup=lambda s:(s=='support').sum()); pj=pj.join(pjc).fillna({'opp':0,'sup':0})
pj['out']=np.select([pj.dis&~pj.appr,pj.appr],['disapproved','approved'],'no final vote / other')
print('\n== outcomes by kind'); print(pj.groupby('kind').agg(n=('nh','size'),mean_hearings=('nh','mean'),mean_opp=('opp','mean'),mean_sup=('sup','mean'),approved=('out',lambda s:(s=='approved').mean()),disapproved=('out',lambda s:(s=='disapproved').mean()),median_days=('last',lambda s:0)).drop(columns='median_days').round(2))
# themes
TH={'affordability / who it is for':r'afford|luxury|market[- ]rate|low[- ]income|bmr|below market','displacement / tenants / eviction':r'displac|evict|tenant|gentrif|rent control','height / bulk / scale':r'height|tall|stor(?:y|ies)|bulk|scale|massing|too big|density','light / shadow / views / privacy':r'shadow|light|sun|view|privacy|air','parking / traffic':r'parking|traffic|congest|car','neighborhood character / historic':r'character|historic|preserv|context|design|compatib','process / notice / outreach':r'notice|outreach|process|meeting|communicat|not informed','housing need / supply':r'housing (?:crisis|shortage|need)|need(?:s|ed)? (?:more )?housing|more housing|more homes|supply','jobs / labor / union':r'job|labor|union|carpenter|wage|apprentic|local hire','local business / retail':r'business|retail|merchant|formula'}
tx=c.text.fillna('').str.lower(); has=tx.str.len()>12; cc=c[has]; txx=tx[has]
rows=[]
for k,p in TH.items():
    m=txx.str.contains(p); rows.append({'theme':k,'in_oppose':m[cc.position=='oppose'].mean(),'in_support':m[cc.position=='support'].mean()})
print('\n== themes in comment text (share of comments with text; n oppose',int((cc.position=="oppose").sum()),'support',int((cc.position=="support").sum()),')'); print(pd.DataFrame(rows).round(3).to_string(index=False))
# zillow
z=pd.read_csv(Z).dropna(subset=['latitude','longitude']); zs=z[z.homeStatus.isin(['RECENTLY_SOLD','FOR_SALE'])&(z.livingArea>200)&(z.price>50000)].copy(); zs['ppsf']=zs.price/zs.livingArea; zs=zs[zs.ppsf.between(200,4000)]
m=pj.lat.between(37.6,37.9); bt=BallTree(np.radians(zs[['latitude','longitude']].values),metric='haversine'); _,i=bt.query(np.radians(pj.loc[m,['lat','lon']].values),k=30); pj.loc[m,'ppsf']=np.median(zs.ppsf.values[i],axis=1)
pj['terc']=pd.qcut(pj.ppsf,3,labels=['low $/sqft','mid','high $/sqft'])
b=pj[pj.units>=10]
print('\n== where 10+ unit projects are (by neighbourhood price tercile of ALL site-specific projects)'); print(pd.crosstab(b.aff,b.terc,margins=True)); print(b.groupby('terc',observed=True).agg(n=('units','size'),units=('units','sum'),opp_share=('opp',lambda s:s.sum()/(s.sum()+b.loc[s.index,'sup'].sum())),mean_hearings=('nh','mean')).round(3))
print(b.groupby(['aff','terc'],observed=True).apply(lambda q:pd.Series({'n':len(q),'opp_share':q.opp.sum()/max(q.opp.sum()+q.sup.sum(),1)}),include_groups=False).round(2).unstack())
pj.drop(columns='txt').to_csv(sys.argv[3]); c.drop(columns=['text','body','comment'],errors='ignore').to_csv(sys.argv[4],index=False)
if SHOW: print('\n== sample 100% affordable'); print(pj[(pj.aff=='100% affordable')&(pj.units>=10)].sample(6,random_state=1).txt.str[60:330].to_string())
