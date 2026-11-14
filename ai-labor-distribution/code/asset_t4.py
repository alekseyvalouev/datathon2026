import numpy as np, pandas as pd, glob, warnings
warnings.filterwarnings('ignore')
S='/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/'
MINCELL=10; MINPOST=50; THR=0.30
z=pd.concat([pd.read_parquet(f,columns=['zpid','city','county_name','homeStatus','price','rentZestimate']) for f in sorted(glob.glob(S+'base/asset_zillow_p?.parquet'))],ignore_index=True)
z['cl']=z.city.str.lower().str.strip()
fr=z[(z.homeStatus=='FOR_RENT')&(z.price>500)&(z.price<30000)]
city_rent=pd.DataFrame({'rentZ':z.groupby('cl').rentZestimate.median(),'n_rentZ':z.groupby('cl').rentZestimate.count(),'ask':fr.groupby('cl').price.median(),'n_ask':fr.groupby('cl').size()})
cty_rent=pd.DataFrame({'rentZ':z.groupby('county_name').rentZestimate.median(),'n_rentZ':z.groupby('county_name').rentZestimate.count(),'ask':fr.groupby('county_name').price.median(),'n_ask':fr.groupby('county_name').size()})
ind=pd.read_parquet(S+'base/indeed_base_v2.parquet'); b=ind[ind.bay&(ind.city!='san francisco bay area')&ind.has_salary].copy()
tot=ind[ind.bay&(ind.city!='san francisco bay area')].groupby('city').size(); big=set(tot[tot>=MINPOST].index)
rows=[]
def cells(df,keys,rent,level,rentkey):
    for k,d in df.groupby(keys+['occ']):
        *kk,occ=k if isinstance(k,tuple) else (k,)
        name=kk[0] if len(kk)==1 else kk[-1]
        r=rent.loc[name] if name in rent.index else None
        if r is None: continue
        n=len(d); sal=d.sal_mid.median()
        rows.append(dict(level=level,geo=name,county=(d.county.iloc[0]),occ=occ,n_salary_postings=n,thin_lt10=n<MINCELL,median_posted_salary=sal,
            rentZestimate_med=r.rentZ,asking_rent_med=r.ask,n_rentZ=r.n_rentZ,n_ask=r.n_ask))
cells(b,['county'],cty_rent,'county','county_name')
cc=b[b.city.isin(big)&b.city.isin(city_rent.index)]
cells(cc,['city'],city_rent,'city','cl')
m=pd.DataFrame(rows)
for lab,col in [('rentZ','rentZestimate_med'),('ask','asking_rent_med')]:
    m[f'rent_burden_{lab}']=12*m[col]/m.median_posted_salary
    m[f'affordable_30pct_{lab}']=m[f'rent_burden_{lab}']<=THR
    m[f'salary_needed_30pct_{lab}']=12*m[col]/THR
    m[f'salary_shortfall_$_{lab}']=(m[f'salary_needed_30pct_{lab}']-m.median_posted_salary).clip(lower=0)
    m[f'needed_over_salary_x_{lab}']=m[f'salary_needed_30pct_{lab}']/m.median_posted_salary
m['usable']=~m.thin_lt10
m.to_csv(S+'base/asset_rent_burden_matrix.csv',index=False)
pd.set_option('display.width',250,'display.max_columns',40)
CLS=['AI_PRODUCER','SOFTWARE_ENG','DATA_ENG_ANALYTICS','PRODUCT_DESIGN','AI_DATA_WORK','PROF_EXPOSED','CLERICAL_ADMIN','CUSTOMER_SUPPORT','FRONTLINE_SERVICE','SKILLED_TRADE','HEALTH_CLINICAL','EDUCATION']
cm=m[(m.level=='county')]
for lab in ['rentZ','ask']:
    print('COUNTY burden',lab); print(cm.pivot(index='occ',columns='geo',values=f'rent_burden_{lab}').reindex(CLS).round(2).to_string())
print('rents',cty_rent.round(0))
print(cm.pivot(index='occ',columns='geo',values='median_posted_salary').reindex(CLS).round(0).to_string())
print(cm.pivot(index='occ',columns='geo',values='n_salary_postings').reindex(CLS).to_string())
# city counts
ct=m[(m.level=='city')&m.usable]
out=[]
for occ in ['AI_PRODUCER','SOFTWARE_ENG','DATA_ENG_ANALYTICS','CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED','FRONTLINE_SERVICE','AI_DATA_WORK']:
    d=ct[ct.occ==occ]
    out.append(dict(occ=occ,n_cities_with_data=len(d),med_salary=d.median_posted_salary.median(),
      afford_rentZ=int(d.affordable_30pct_rentZ.sum()),afford_ask=int(d.affordable_30pct_ask.sum()),
      med_burden_rentZ=d.rent_burden_rentZ.median(),med_burden_ask=d.rent_burden_ask.median(),
      med_shortfall_rentZ=d.salary_shortfall_rentZ.median() if False else d['salary_shortfall_$_rentZ'].median(),med_shortfall_ask=d['salary_shortfall_$_ask'].median(),
      med_needed_x_rentZ=d.needed_over_salary_x_rentZ.median(),med_needed_x_ask=d.needed_over_salary_x_ask.median()))
O=pd.DataFrame(out); print(O.round(2).to_string()); O.to_csv(S+'base/asset_rent_burden_citycounts.csv',index=False)
# same-city comparison: cities where both an AI-side class and a non-AI class have usable data
cities_both=ct.groupby('geo').occ.apply(set)
ok=[c for c,s in cities_both.items() if ('SOFTWARE_ENG' in s or 'AI_PRODUCER' in s) and ('CLERICAL_ADMIN' in s)]
print('cities with SWE/AIP and CLERICAL both usable',len(ok))
# county-level counts
cn=cm[cm.usable]
O2=[]
for occ in ['AI_PRODUCER','SOFTWARE_ENG','DATA_ENG_ANALYTICS','CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED','FRONTLINE_SERVICE','AI_DATA_WORK']:
    d=cn[cn.occ==occ]; O2.append(dict(occ=occ,n_counties=len(d),afford_rentZ=int(d.affordable_30pct_rentZ.sum()),afford_ask=int(d.affordable_30pct_ask.sum())))
print(pd.DataFrame(O2))
# overall bay medians
bs=b.groupby('occ').sal_mid.median(); print(bs.reindex(CLS))
bay_rentZ=z.rentZestimate.median(); bay_ask=fr.price.median(); print('bay rent',bay_rentZ,bay_ask, 'n',z.rentZestimate.count(),len(fr))
for occ in ['AI_PRODUCER','SOFTWARE_ENG','CLERICAL_ADMIN','CUSTOMER_SUPPORT','FRONTLINE_SERVICE','AI_DATA_WORK']:
    s=bs[occ]; print(occ,s,'burden rentZ',round(12*bay_rentZ/s,3),'ask',round(12*bay_ask/s,3), 'needed rentZ',12*bay_rentZ/.3,'ask',12*bay_ask/.3)
# list city rows for key classes
print(ct[ct.occ.isin(['CLERICAL_ADMIN','CUSTOMER_SUPPORT','FRONTLINE_SERVICE','AI_DATA_WORK','SOFTWARE_ENG','AI_PRODUCER'])].pivot(index='geo',columns='occ',values='rent_burden_ask').round(2).to_string())
