import pandas as pd, numpy as np, re
pd.set_option('display.width',250); pd.set_option('display.max_columns',30); pd.set_option('display.max_rows',300); pd.set_option('display.max_colwidth',60)
S='/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad'
d=pd.read_parquet(S+'/out/warn_work.parquet')
def grp(c):
    c=re.sub(r'\([^)]*\)','',c); c=re.split(r'\s+-\s+|\s+dba\s+|\s+d/b/a\s+',c,flags=re.I)[0]
    return c
d['employer_group']=d.company.map(grp)
from importlib import import_module
import importlib.util
sp=importlib.util.spec_from_file_location('p',S+'/code/warn_parse.py')
def norm(s):
    s=s.lower()
    s=re.sub(r'\b(incorporated|inc|llc|llp|lp|corporation|corp|company|co|ltd|limited|group|holdings|the)\b',' ',s)
    return re.sub(r'[^a-z0-9]','',s)
d['eg']=d.employer_group.map(norm)
# manual merges
merge={'amazoncom':'amazon','amazoncomservices':'amazon','amazoncomservicesllc':'amazon'}
d['eg']=d.eg.replace(merge)
# tech classification (curated on employer group keys)
CORE={'metaplatforms','ciscosystems','oracleamerica','oracle','broadcom','linkedin','intel','ebay','intuit','workday','salesforce','amazon','apple','paypal','billoperations','applovin','autodesk','synopsys','clari','block','google','alphabet','microsoft','adobe','vmware','servicenow','twitter','xcorp','uber','lyft','dropbox','netflix','zoom','zoomvideocommunications','okta','twilio','yahoo','hpinc','hewlettpackard','dell','dellemc','ibm','qualcomm','nvidia','micron','appliedmaterials','lamresearch','kla','westerndigital','sandisk','seagate','juniper','paloaltonetworks','splunk','pinterest','airbnb','stripe','doordash','snap','instacart','roblox','electronicarts','unity','zendesk','docusign','yelp','chegg','coinbase','robinhood','opendoor','redfin','nextdoor','grammarly','stitchfix','carta','gusto','cloudflare','equinix','digitalrealty','rubrik','nutanix','informatica','mcafee','gendigital','openai','anthropic','sap','sapamerica','sapamericainc','samsara','medallia','anaplan','atlassian','slack','indeed','glassdoor','wish','contextlogic','fastly','verily','x','waymo','zoox','kaseya','cvent','tiktok','bytedance','rippling','brex','plaid','figma','airtable','asana','webflow','lacework','mulesoft','tableau','sumologic','newrelic','pagerduty','mongodb','hashicorp','confluent','cohesity','pureStorage'.lower(),'arista','aristanetworks','fortinet','ciena','infinera','lumentum','coherent','amd','advancedmicrodevices','marvell','skyworks','synaptics','rambus','cadence','cadencedesignsystems','ansys','ptc','teradata','citrix','nortonlifelock','symantec','nokia','ericsson','motorola','verizon','att','tmobile','comcast','spotify','sonos','gopro','fitbit','magicleap','ring','eero','matterport','compass','zillow','turo','getaround','bird','lime','scale','scaleai','databricks','snowflake','palantir','c3','c3ai','veeva','servicetitan','toast','squarespace','wix','godaddy','ubertechnologies','netflix','formagrid','atlassianus','checkr','frontapp','ubisoft','nextdoor'}
ADJ={'tesla','cruise','cruisellc','cruiseheadquarters','lucid','lucidgroup','rivian','jabil','sunpower','sunrun','enphase','moxionpower','amyris','zerolabs','canoo','fisker','nikola','proterra','lyftnotnow','solaredge','tesla'}
core=lambda e: e in CORE
d['tech_core']=d.eg.map(lambda e: e in CORE or e.startswith('cruise'))&~d.eg.str.startswith('cruiseship')
d.loc[d.eg.str.startswith('cruise'),'tech_core']=False
d['tech_adj']=d.eg.map(lambda e: e in ADJ or e.startswith('cruise'))
d['tech_ind51']=d.industry.fillna('').str.startswith('51 ')
d['tech_any']=d.tech_core|d.tech_adj
bay=d[d.bay]
# (c) top 30
top=bay.groupby('eg').agg(employer=('employer_group',lambda s:s.value_counts().index[0]),employees=('employees','sum'),notices=('company','size'),counties=('county',lambda s:', '.join(sorted(set(s)))),tech_core=('tech_core','max'),tech_adjacent=('tech_adj','max'),naics51_flag_in_FY26_27=('tech_ind51','max'),first=('received_date','min'),last=('received_date','max')).sort_values('employees',ascending=False)
top['share_of_bay_total']=top.employees/bay.employees.sum()
top30=top.head(30); print(top30.to_string()); top30.to_csv(S+'/out/warn_bay_top30_employers.csv')
print('top30 share of bay',top30.employees.sum()/bay.employees.sum(),'bay total',bay.employees.sum(),'n employers',len(top))
print(top.iloc[30:80][['employer','employees','tech_core','tech_adjacent']].to_string())
# tech share by FY (Bay)
ts=bay.groupby('fiscal_year').apply(lambda g: pd.Series({'total':g.employees.sum(),'tech_core':g[g.tech_core].employees.sum(),'tech_adj':g[g.tech_adj].employees.sum(),'naics51_xlsx':g[g.tech_ind51].employees.sum()}))
ts['core_share']=ts.tech_core/ts.total; ts['core+adj_share']=(ts.tech_core+ts.tech_adj)/ts.total; print(ts.round(3)); ts.round(3).to_csv(S+'/out/warn_bay_tech_share_fy.csv')
# like-for-like tech share Jul1-Nov9
d['md']=d.received_date.dt.month*100+d.received_date.dt.day
w=bay[(bay.received_date.dt.month*100+bay.received_date.dt.day>=701)&(bay.received_date.dt.month*100+bay.received_date.dt.day<=1109)]
tl=w.groupby('fiscal_year').apply(lambda g: pd.Series({'total':g.employees.sum(),'tech_core':g[g.tech_core].employees.sum(),'tech_adj':g[g.tech_adj].employees.sum()}))
tl['core_share']=tl.tech_core/tl.total; print('LFL tech',tl.round(3))
# quarterly tech core Bay
print(bay.groupby('quarter').apply(lambda g: pd.Series({'tot':g.employees.sum(),'tech_core':g[g.tech_core].employees.sum()})).assign(sh=lambda x:x.tech_core/x.tot).round(2))
# robustness LFL excluding big rows
for cap in [None,1000]:
    w2=d[(d.md>=701)&(d.md<=1109)]
    if cap: w2=w2[w2.employees<cap]
    g=w2.groupby(['fiscal_year','bay']).employees.sum().unstack(); g['bay_share']=g[True]/(g[True]+g[False]); print('cap',cap); print(g)
# Big rows in FY26-27 bay
print(bay[(bay.fiscal_year=='FY2026-27')].sort_values('employees',ascending=False).head(12)[['received_date','company','county','employees','layoff_type','industry']])
print(bay[(bay.quarter=='2026Q2')].sort_values('employees',ascending=False).head(8)[['received_date','company','county','employees','layoff_type']])
# (f) industry
x=d[d.source_file=='warn_report1.xlsx'].copy(); print('industry rows',x.industry.notna().sum(),len(x))
x['ind']=x.industry.fillna('(missing)')
ib=x[x.bay].groupby('ind').agg(employees=('employees','sum'),notices=('company','size')).sort_values('employees',ascending=False); ib['share']=ib.employees/ib.employees.sum()
ir=x[~x.bay].groupby('ind').agg(employees=('employees','sum'),notices=('company','size')).sort_values('employees',ascending=False); ir['share']=ir.employees/ir.employees.sum()
print(ib.round(3)); print(ir.head(8).round(3)); ib.to_csv(S+'/out/warn_bay_industry_fy2627.csv')
x['month']=x.received_date.dt.to_period('M').astype(str)
print(x[x.bay].groupby(['month']).employees.sum())
print('bay 51 info by month'); print(x[x.bay&x.tech_ind51].groupby('month').employees.sum())
print(x[x.bay&x.ind.str.startswith('51')][['company','county','employees']].sort_values('employees',ascending=False).head(10))
# (e) call centers
cc=pd.read_csv(S+'/base/warn_call_centers.csv'); print(cc.T)
print(d[d.company.str.contains('call cent|customer (service|support|care)|contact cent|BPO|teleperform|concentrix|alorica|telus|sitel|conduent|genpact|startek|sykes|ttec',case=False,regex=True)][['received_date','company','county','employees','layoff_type']])
print(d[d.layoff_type.str.contains('Relocat')][['received_date','company','county','employees']])
d.to_parquet(S+'/out/warn_work2.parquet')
dup=d.duplicated(['notice_date','received_date','effective_date','company','county','employees','address'],keep=False)
print('exact duplicate rows (incl. first)',dup.sum(), 'employees in dups', d[dup].employees.sum())
# per-FY Bay core tech summary for memo
print(bay.groupby('fiscal_year').apply(lambda g: g[g.tech_core].groupby('eg').employees.sum().sort_values(ascending=False).head(6)))
# overall
print('window total rows',len(d),d.employees.sum(),'bay',bay.employees.sum(),bay.employees.sum()/d.employees.sum())
print('size dist rows<50 overall',(d.employees<50).mean(), 'emp share in rows <50',d[d.employees<50].employees.sum()/d.employees.sum(),'rows<75',(d.employees<75).mean())
# county/employee data quality
print('county valid CA', d.county.notna().mean(), 'emp valid',d.employees.notna().mean(), 'city present',d.city.notna().mean())
