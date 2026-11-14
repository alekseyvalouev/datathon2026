import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pums_lib as L
csv_path, dict_csv, xwalk_path, out_parquet = sys.argv[1:5]
xw = pd.read_csv(xwalk_path, dtype=str)
puma2cty = dict(zip(xw.PUMA5CE, xw.dom_county)); split = dict(zip(xw.PUMA5CE, xw.split))
bay_pumas = set(xw[xw.dom_county.isin(L.BAY)].PUMA5CE) | set(xw[xw.bay_counties_touched.notna()].PUMA5CE)
head = pd.read_csv(csv_path, nrows=0).columns
base = ['SERIALNO','SPORDER','PUMA','STATE','ADJINC','PWGTP','AGEP','SEX','RAC1P','HISP','OCCP','SOCP','INDP','COW','WAGP','PERNP','PINCP','SEMP','WKHP','WKWN','ESR','SCHL','POVPIP','NATIVITY','ENG','DIS']
use = [c for c in base if c in head] + L.REP
parts=[]
for ch in pd.read_csv(csv_path, usecols=use, dtype=str, chunksize=150000):
    ch = ch[(ch.STATE=='06') & ch.PUMA.isin(bay_pumas)]
    ch = ch[(pd.to_numeric(ch.AGEP)>=16) & ch.ESR.isin(['1','2','4','5'])]
    parts.append(ch)
d = pd.concat(parts, ignore_index=True)
print('rows', len(d))
num = [c for c in d.columns if c not in ('SERIALNO','PUMA','STATE','OCCP','SOCP','INDP','RAC1P','HISP','COW','ESR','SCHL','NATIVITY','ENG','DIS')]
for c in num: d[c]=pd.to_numeric(d[c], errors='coerce')
for c in ['HISP','RAC1P','COW','ESR','NATIVITY','ENG','DIS']: d[c]=pd.to_numeric(d[c], errors='coerce')
d['county_fips']=d.PUMA.map(puma2cty); d['county']=d.county_fips.map(L.BAY); d['puma_split']=d.PUMA.map(split)
assert d.county.notna().all(), d[d.county.isna()].PUMA.unique()
d['race_eth']=L.race_eth(d.HISP, d.RAC1P)
d['occ_code']=d.OCCP
occ=L.load_occp(dict_csv)
assert d.OCCP.isin(occ).all(), set(d.OCCP)-set(occ)
cls={c:L.classify(c,t)[0] for c,t in occ.items()}
d['occ_class']=d.OCCP.map(cls)
d['occ_title']=d.OCCP.map(occ)
adj=d.ADJINC/1e6
d['adjinc_factor']=adj
d['annual_wage_adj']=d.WAGP*adj        # wages & salary only, constant dollars (2023$ for 5-yr, 2024$ for 1-yr)
d['earnings_adj']=d.PERNP*adj          # wages + self-employment net income
d['semp_adj']=d.SEMP*adj
d['weeks_worked']=d.WKWN               # exact weeks (WKWN, 2019+), so no bracket midpoint needed
d['hourly_wage']=np.where((d.WKHP>0)&(d.WKWN>0)&(d.WAGP>0), d.annual_wage_adj/(d.WKHP*d.WKWN), np.nan)
d['self_employed']=d.COW.isin([6,7])
d['self_employed_unincorp']=d.COW==6
d['wage_salary_worker']=d.COW.isin([1,2,3,4,5])
d['education']=L.edu_bucket(d.SCHL)
d['full_time']=d.WKHP>=35
d['ftfy']=(d.WKHP>=35)&(d.WKWN>=50)
d['military']=d.ESR.isin([4,5])
d.to_parquet(out_parquet, index=False)
print(d.groupby('race_eth').agg(n=('PWGTP','size'), w=('PWGTP','sum')))
print(d.groupby('county').agg(n=('PWGTP','size'), w=('PWGTP','sum')))
print('weighted employed', d.PWGTP.sum(), 'puma_split any', d.puma_split.eq('True').sum())
