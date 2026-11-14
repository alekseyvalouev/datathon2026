import sys,re,pandas as pd,numpy as np
S=sys.argv[1]; sys.path.insert(0,S+'/code')
from voice_norm import company_norm
from voice_titles import classify_title
d=pd.read_csv(S+'/gd_extract/glassdoor_reviews.csv',low_memory=False)
print('all rows',len(d))
d['is_ca']=d.employee_location.fillna('').str.endswith(', CA')
ca=d[d.is_ca].copy()
print('CA rows',len(ca),'unique cos',ca.company_name.nunique())
BAY={'san francisco','san jose','oakland','berkeley','palo alto','mountain view','sunnyvale','santa clara','menlo park','redwood city','san mateo','foster city','fremont','cupertino','milpitas','pleasanton','south san francisco','newark','livermore','san ramon','walnut creek','concord','alameda','emeryville','hayward','san leandro','los gatos','campbell','los altos','san carlos','burlingame','belmont','brisbane','daly city','san bruno','millbrae','redwood shores','union city','dublin','santa rosa','petaluma','san rafael','novato','napa','fairfield','vacaville','vallejo','richmond','pittsburg','antioch','martinez','danville','orinda','lafayette','mill valley','sausalito','saratoga','morgan hill','gilroy','half moon bay','larkspur','corte madera','east palo alto','pacifica','el cerrito','albany','san pablo','hercules','pinole','benicia','brentwood','oakley','castro valley','alamo','moraga','los altos hills','portola valley','woodside','atherton','hillsborough','san anselmo','tiburon','belvedere','mountain view','santa clara','scotts valley'}
ca['city']=ca.employee_location.str.replace(r',\s*CA$','',regex=True).str.strip()
ca['bay_area']=ca.city.str.lower().isin(BAY)
ca['rating_dt']=pd.to_datetime(ca.rating_date,utc=True).dt.tz_localize(None)
ca['month']=ca.rating_dt.dt.strftime('%Y-%m')
ca['company_norm']=ca.company_name.map(company_norm)
tt=ca.apply(lambda r:classify_title(r.employee_job_title,r.company_norm),axis=1)
ca['occ_class']=[x[0] for x in tt]; ca['occ_rule']=[x[1] for x in tt]
ca['status_current']=ca.employee_type.fillna('').str.lower().str.startswith('current')
ca['tenure_code']=ca.employee_length
ca.to_pickle(S+'/base/_gd_ca_text.pkl')
print(ca.occ_class.value_counts()); print(ca.occ_rule.value_counts())
print(ca.month.value_counts().sort_index())
print(ca[ca.occ_class=='OTHER'].employee_job_title.value_counts().head(60))
