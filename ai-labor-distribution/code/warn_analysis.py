import pandas as pd, numpy as np, re, statsmodels.api as sm
pd.set_option('display.width',250); pd.set_option('display.max_columns',30); pd.set_option('display.max_rows',200)
S='/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad'
df=pd.read_parquet(S+'/base/warn_ca.parquet')
den=pd.read_csv(S+'/base/warn_county_denominators.csv',dtype={'COUNTYFP':str})
BAY=['Alameda','Contra Costa','Marin','Napa','San Francisco','San Mateo','Santa Clara','Solano','Sonoma']
df=df[~df.county.isin(['Clark','Dallas'])].copy()   # drop 2 out-of-state rows from CA analysis
df['bay']=df.county.isin(BAY)
emp_den=den.set_index('county').employed_residents_acs2024
BAYW=emp_den[BAY].sum(); CAW=emp_den.sum(); RESTW=CAW-BAYW
print('Bay employed residents',BAYW,'CA',CAW,'rest',RESTW,'Bay share of CA workers',BAYW/CAW)
# ---- (a) quarterly
q=df.groupby(['quarter','bay']).agg(notices=('company','size'),employees=('employees','sum')).unstack('bay').fillna(0)
q.columns=[f"{a}_{'bay' if b else 'rest'}" for a,b in q.columns]
q['emp_ca']=q.employees_bay+q.employees_rest; q['notices_ca']=q.notices_bay+q.notices_rest
q['bay_share_emp']=q.employees_bay/q.emp_ca; q['bay_share_notices']=q.notices_bay/q.notices_ca
q['bay_per10k']=q.employees_bay/BAYW*1e4; q['rest_per10k']=q.employees_rest/RESTW*1e4
# partial-quarter flags: first quarter is full (2023Q3); last 2026Q4 through 11/9
last=df.received_date.max(); print('last received',last)
q['days']=[92 if p!='2026Q4' else (last-pd.Timestamp('2026-10-01')).days+1 for p in q.index]
q['bay_per10k_per_92d']=q.bay_per10k*92/q.days; q['rest_per10k_per_92d']=q.rest_per10k*92/q.days
q['bay_to_rest_intensity_ratio']=q.bay_per10k/q.rest_per10k
q.round(3).to_csv(S+'/out/warn_quarterly_bay_vs_rest.csv'); print(q.round(2))
# trend tests on full quarters 2023Q3..2026Q3 (13 quarters)
full=q.iloc[:-1].copy(); full['t']=range(len(full))
def trend(y,name):
    m=sm.OLS(full[y],sm.add_constant(full['t'])).fit(cov_type='HAC',cov_kwds={'maxlags':2})
    print(f'{name}: slope/qtr={m.params.t:.3f} (se {m.bse.t:.3f}, p={m.pvalues.t:.3f}) mean={full[y].mean():.2f}')
for y in ['employees_bay','bay_per10k','rest_per10k','bay_share_emp','bay_share_notices','notices_bay']: trend(y,y)
# Spearman
from scipy.stats import spearmanr
for y in ['bay_per10k','bay_share_emp']: print(y,'spearman',spearmanr(full.t,full[y]))
# like-for-like Jul1-Nov9 windows
d=df.copy(); d['md']=d.received_date.dt.month*100+d.received_date.dt.day
w=d[(d.md>=701)&(d.md<=1109)]
lfl=w.groupby(['fiscal_year','bay']).agg(notices=('company','size'),employees=('employees','sum'),med=('employees','median')).unstack('bay')
lfl.columns=[f"{a}_{'bay' if b else 'rest'}" for a,b in lfl.columns]
lfl['bay_per10k']=lfl.employees_bay/BAYW*1e4; lfl['rest_per10k']=lfl.employees_rest/RESTW*1e4
lfl['bay_share']=lfl.employees_bay/(lfl.employees_bay+lfl.employees_rest)
print('\nLIKE-FOR-LIKE Jul1-Nov9'); print(lfl.round(3)); lfl.round(3).to_csv(S+'/out/warn_like_for_like_jul1_nov9.csv')
# full FY
fy=d.groupby(['fiscal_year','bay']).agg(notices=('company','size'),employees=('employees','sum')).unstack('bay')
fy.columns=[f"{a}_{'bay' if b else 'rest'}" for a,b in fy.columns]
fy['bay_per10k']=fy.employees_bay/BAYW*1e4; fy['rest_per10k']=fy.employees_rest/RESTW*1e4; fy['bay_share']=fy.employees_bay/(fy.employees_bay+fy.employees_rest)
print('\nFY'); print(fy.round(3)); fy.round(3).to_csv(S+'/out/warn_fy_bay_vs_rest.csv')
# robustness: drop top-5 single notices per FY in each region -> concentration
big=d.sort_values('employees',ascending=False).groupby('fiscal_year').head(1)[['fiscal_year','company','county','employees']]
print('\nlargest single rows per FY'); print(big)
# Bay: share of employees from top-10 rows per FY
for f,g in d[d.bay].groupby('fiscal_year'):
    s=g.employees.sort_values(ascending=False); print(f,'Bay top10 rows share',round(s.head(10).sum()/s.sum(),3),'median notice size',g.employees.median(),'rows<50',round((g.employees<50).mean(),3))
for f,g in d[~d.bay].groupby('fiscal_year'):
    print(f,'Rest median notice size',g.employees.median(),'rows<50',round((g.employees<50).mean(),3))
# firm-level (company_norm) distinct employers in Bay per FY
print(d[d.bay].groupby('fiscal_year').company_norm.nunique())
# ---- (b) county-quarter
cq=d[d.bay].groupby(['county','quarter']).agg(notices=('company','size'),employees=('employees','sum')).reset_index()
cq=cq.merge(den[['county','employed_residents_acs2024','POPESTIMATE2024']],on='county')
cq['employees_per10k_workers']=cq.employees/cq.employed_residents_acs2024*1e4
cq.round(3).to_csv(S+'/base/warn_bay_county_quarter.csv',index=False)
pv=cq.pivot(index='quarter',columns='county',values='employees').fillna(0); print('\nCOUNTY employees by quarter'); print(pv)
cf=d[d.bay].groupby(['county','fiscal_year']).employees.sum().unstack().fillna(0)
cf['workers']=emp_den[cf.index]
for c in ['FY2023-24','FY2024-25','FY2025-26']: cf[c+'_per10k']=cf[c]/cf.workers*1e4
cf['FY26-27 Jul1-Nov9']=w[w.fiscal_year=='FY2026-27'][w.bay].groupby('county').employees.sum()
print(cf.round(1)); cf.round(2).to_csv(S+'/out/warn_bay_county_fy.csv')
# county LFL
cl=w[w.bay].groupby(['county','fiscal_year']).employees.sum().unstack().fillna(0); print('\nCounty LFL Jul1-Nov9'); print(cl)
cl.to_csv(S+'/out/warn_bay_county_lfl.csv')
# ---- (d) type mix
d['perm']=d.duration
tm=d.groupby(['fiscal_year','bay','duration']).employees.sum().unstack().fillna(0)
tm['perm_share']=tm['Permanent']/tm.sum(axis=1); print('\nDuration mix (employees)'); print(tm.round(3))
tm2=d.groupby(['fiscal_year','bay','kind']).employees.sum().unstack().fillna(0); tm2['closure_share']=tm2.Closure/tm2.sum(axis=1); print(tm2.round(3))
tq=d.groupby(['quarter','bay','duration']).employees.sum().unstack().fillna(0); tq['perm_share']=tq['Permanent']/tq.sum(axis=1)
tq.round(3).to_csv(S+'/out/warn_type_mix_quarter.csv'); print(tq.round(3).xs(True,level='bay'))
tm.round(3).to_csv(S+'/out/warn_type_mix_fy.csv'); tm2.round(3).to_csv(S+'/out/warn_kind_mix_fy.csv')
# ---- (c) employers
TECH=r'google|alphabet|meta platforms|facebook|\bmeta\b|apple|amazon|microsoft|salesforce|oracle|intel\b|cisco|nvidia|adobe|intuit|vmware|broadcom|ebay|paypal|uber|lyft|twitter|x corp|linkedin|netflix|dropbox|zoom|workday|servicenow|autodesk|snap\b|pinterest|airbnb|stripe|block, inc|square|doordash|okta|twilio|yahoo|hp inc|hewlett|dell|ibm|qualcomm|micron|applied materials|lam research|kla|western digital|sandisk|seagate|juniper|palo alto|splunk|tesla|rivian|zynga|electronic arts|roblox|unity|zendesk|slack|atlassian|docusign|yelp|chegg|coinbase|robinhood|instacart|opendoor|redfin|zillow|wish|gopro|fitbit|magic leap|ring|zoox|cruise|waymo|samsara|veeva|medallia|anaplan|nextdoor|grammarly|stitch fix|better\.com|carta|gusto|lacework|fastly|cloudflare|digital realty|equinix|sunpower|sunrun|enphase|rubrik|nutanix|informatica|symantec|nortonlifelock|gen digital|mcafee|rambus|synaptics|xilinx|amd\b|advanced micro|ebay|wish|opentext|sap |sap$|software|technolog|digital|data|cloud|systems|networks|labs\b|\bai\b|robot|semiconductor|internet|online|app\b|platform'
d['tech_name']=d.company.str.lower().str.contains(TECH)
d['tech_ind']=d.industry.fillna('').str.startswith(('51 ','54 '))
bayd=d[d.bay]
top=bayd.groupby('company_norm').agg(company=('company',lambda s:s.value_counts().index[0]),employees=('employees','sum'),notices=('company','size'),counties=('county',lambda s:', '.join(sorted(set(s)))),tech_name=('tech_name','max'),tech_ind=('tech_ind','max'),ind=('industry',lambda s: s.dropna().mode().iloc[0] if s.notna().any() else '')).sort_values('employees',ascending=False).head(60)
print('\nTOP 60 BAY'); print(top[['company','employees','notices','counties','tech_name','ind']].to_string())
top.to_csv(S+'/out/warn_bay_top60_raw.csv')
d.to_parquet(S+'/out/warn_work.parquet')
