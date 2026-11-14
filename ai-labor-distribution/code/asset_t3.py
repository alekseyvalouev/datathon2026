import numpy as np, pandas as pd, glob, statsmodels.formula.api as smf, warnings
warnings.filterwarnings('ignore')
S='/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/'
MINPOST=50; MINZ=30; MINCELL=10
z=pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(S+'base/asset_zillow_p?.parquet'))],ignore_index=True).copy()
z['cl']=z.city.str.lower().str.strip()
ind=pd.read_parquet(S+'base/indeed_base_v2.parquet'); b=ind[ind.bay&(ind.city!='san francisco bay area')].copy()
AIP=['AI_PRODUCER','SOFTWARE_ENG','DATA_ENG_ANALYTICS']; EXP=['CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED']
KEY=['AI_PRODUCER','SOFTWARE_ENG','DATA_ENG_ANALYTICS','AI_DATA_WORK','CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED','FRONTLINE_SERVICE']
g=b.groupby(['county','city'])
c=g.size().rename('postings_total').to_frame()
c['ai_positioned_share']=g.apply(lambda d:d.occ.isin(AIP).mean())
c['exposed_share']=g.apply(lambda d:d.occ.isin(EXP).mean())
c['frontline_share']=g.apply(lambda d:(d.occ=='FRONTLINE_SERVICE').mean())
c['pct_postings_with_salary']=g.apply(lambda d:100*d.has_salary.mean())
for k in KEY:
    s=b[(b.occ==k)&b.has_salary]; gg=s.groupby(['county','city']).sal_mid
    c['n_sal_'+k]=gg.size().reindex(c.index).fillna(0)
    m=gg.median().reindex(c.index); m[c['n_sal_'+k]<MINCELL]=np.nan; c['sal_med_'+k]=m
c=c.reset_index(); c=c[c.postings_total>=MINPOST]
# zillow city stats
sale=z[z.homeStatus!='FOR_RENT']
zz=sale.groupby('cl').agg(n_zestimate=('zestimate','count'),med_zestimate=('zestimate','median'),med_livingArea=('livingArea','median'),med_beds=('bedrooms','median'),
     pct_sfh=('homeType',lambda s:100*s.isin(['SINGLE_FAMILY','SINGLEFAMILY']).mean()))
zz['med_zest_per_sqft']=sale[sale.livingArea>300].assign(p=lambda d:d.zestimate/d.livingArea).groupby('cl').p.median()
zz['n_rentZestimate']=z.groupby('cl').rentZestimate.count(); zz['med_rentZestimate']=z.groupby('cl').rentZestimate.median()
fr=z[(z.homeStatus=='FOR_RENT')&(z.price>500)&(z.price<30000)]
zz['n_asking_rent']=fr.groupby('cl').size(); zz['med_asking_rent']=fr.groupby('cl').price.median()
zz['zillow_records']=z.groupby('cl').size()
c=c.merge(zz,left_on='city',right_index=True,how='left')
# appreciation from zestimate history (balanced same-home panel)
def col(y,m): return f'zh_{y}{m:02d}'
zcols=sorted(c for c in z.columns if c.startswith('zh_'))
zf=z[zcols].ffill(axis=1); z['zh_last']=zf.iloc[:,-1]
lastm=z[zcols].notna().values[:,::-1].argmax(1); z['zh_last_month']=np.array(zcols)[len(zcols)-1-lastm]; z.loc[z[zcols].notna().sum(1)==0,'zh_last_month']=None
print(z.zh_last_month.value_counts().sort_index().tail(8)); 
END='zh_last'; z.loc[z.zh_last_month.fillna('')<'zh_202606',END]=np.nan
print('END coverage',z[END].notna().mean())
def appr(df,start,end):
    ok=df[start].notna()&df[end].notna()&(df[start]>50000)
    return ok
for nm,(s0,s1) in {'w23':('zh_202301',END),'w17_22':('zh_201701','zh_202212'),'w17_26':('zh_201701',END)}.items():
    ok=appr(z,s0,s1); d=z[ok].copy(); d['lr']=np.log(d[s1]/d[s0])
    gg=d.groupby('cl'); r=pd.DataFrame({'n_'+nm:gg.size(),'medlogchg_'+nm:gg.lr.median(),'valwtd_pct_'+nm:100*(gg[s1].sum()/gg[s0].sum()-1),'med_start_'+nm:gg[s0].median(),'med_end_'+nm:gg[s1].median()})
    r['medpct_'+nm]=100*(np.exp(r['medlogchg_'+nm])-1)
    c=c.merge(r,left_on='city',right_index=True,how='left')
c['n_appr_panel']=c.n_w23
c['excluded_thin_zillow']=(c.n_zestimate.fillna(0)<MINZ)
c.to_csv(S+'base/asset_city_jobs_housing.csv',index=False)
print(len(c),'cities >= ',MINPOST,'postings;',c.excluded_thin_zillow.sum(),'thin zillow excluded:',c[c.excluded_thin_zillow].city.tolist())
a=c[~c.excluded_thin_zillow].copy()
a['ln_zest']=np.log(a.med_zestimate); a['ln_rent']=np.log(a.med_rentZestimate); a['ln_ask']=np.log(a.med_asking_rent); a['ln_area']=np.log(a.med_livingArea)
a['ai']=100*a.ai_positioned_share; a['exp']=100*a.exposed_share
print('N cities',len(a))
print('AI share range',a.ai.describe().round(1).to_dict())
res=[]
def ols(f,y,label,df=a):
    m=smf.ols(f,data=df).fit(cov_type='HC3'); 
    t='ai' if 'ai' in m.params.index else 'exp'
    res.append(dict(model=label,dep=y,n=int(m.nobs),coef_ai_per_10pp=m.params['ai']*10 if 'ai' in m.params else np.nan,se_per_10pp=m.bse['ai']*10 if 'ai' in m.params else np.nan,p=m.pvalues['ai'] if 'ai' in m.params else np.nan,r2=m.rsquared))
    return m
print('corr ai vs ln_zest',a[['ai','ln_zest','ln_rent','ln_ask','exp']].corr().round(2).to_string())
print('spearman',a[['ai','med_zestimate','med_rentZestimate','med_asking_rent','exp']].corr(method='spearman').round(2).iloc[0].to_dict())
for y in ['ln_zest','ln_rent','ln_ask']:
    ols(f'{y} ~ ai','', f'{y}: bivariate'); 
    ols(f'{y} ~ ai + ln_area + med_beds','',f'{y}: + sqft,beds')
    ols(f'{y} ~ ai + ln_area + med_beds + C(county)','',f'{y}: + sqft,beds,county FE')
    ols(f'{y} ~ ai + C(county)','',f'{y}: + county FE only')
R=pd.DataFrame(res); R['dep']=R.model.str.split(':').str[0]; print(R.round(4).to_string())
# within-county correlation
a['ai_dm']=a.ai-a.groupby('county').ai.transform('mean'); a['z_dm']=a.ln_zest-a.groupby('county').ln_zest.transform('mean'); print('within-county corr ai,ln_zest',a[['ai_dm','z_dm']].corr().iloc[0,1].round(3))
print(a.groupby('county').agg(n=('city','size'),ai=('ai','mean'),zest=('med_zestimate','median')).round(1))
# appreciation regs
res=[]
for y in ['medlogchg_w23','medlogchg_w17_22','medlogchg_w17_26']:
    for f,lab in [('~ ai','bivariate'),('~ ai + C(county)','+county FE'),('~ ai + ln_area + med_beds + C(county)','+sqft,beds,county FE')]:
        d=a.dropna(subset=[y,'ai']); ols(y+f,y,y+': '+lab,d)
R2=pd.DataFrame(res); R2['dep']=R2.model.str.split(':').str[0]; print(R2.round(4).to_string())
# time series of group ratio, pooled same-home panel (homes present Jan2017 and Sep2026)
tercile=pd.qcut(a.ai,3,labels=['low','mid','high']); tmap=dict(zip(a.city,tercile)); print('tercile cutoffs',a.ai.quantile([1/3,2/3]).round(1).tolist())
pz=z[z.cl.isin(tmap)&z['zh_201701'].notna()&z[END].notna()].copy(); pz['terc']=pz.cl.map(tmap)
mths=['201701','201801','201901','202001','202101','202201','202301','202401','202501','202601','_last']
ts=pd.DataFrame({m:pz.groupby('terc')['zh'+('_' if not m.startswith('_') else '')+m.lstrip('_') if False else ('zh_'+m if m!='_last' else 'zh_last')].median() for m in mths}).T; ts['high_over_low']=ts.high/ts.low; ts['high_over_mid']=ts.high/ts.mid
print('panel homes',len(pz)); print(ts.round(3))
ts.to_csv(S+'base/asset_city_aigroup_value_ts.csv')
# indexed growth by tercile
idx=pd.DataFrame({m:pz.groupby('terc').apply(lambda d:np.exp(np.log(d['zh'+('_' if not m.startswith('_') else '')+m.lstrip('_') if False else ('zh_'+m if m!='_last' else 'zh_last')]/d['zh_201701']).median())) for m in mths}).T; print(idx.round(3))
for s0,s1,lab in [('zh_201701','zh_202212','2017-01..2022-12'),('zh_202301',END,'2023-01..2026-09'),('zh_201701',END,'2017-01..2026-09')]:
    d=z[z.cl.isin(tmap)&z[s0].notna()&z[s1].notna()].copy(); d['terc']=d.cl.map(tmap); d['lr']=np.log(d[s1]/d[s0])
    print(lab, d.groupby('terc').lr.agg(['size','median']).assign(pct=lambda x:100*(np.exp(x['median'])-1)).round(1).to_dict('index'))
R.to_csv(S+'base/asset_t3_level_regs.csv',index=False); R2.to_csv(S+'base/asset_t3_appr_regs.csv',index=False)
