import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pums_lib as L
dict_csv, bay5, bay1, out = sys.argv[1:5]
occ = L.load_occp(dict_csv)
rows=[]
d5=pd.read_parquet(bay5); d1=pd.read_parquet(bay1)
w5=d5.groupby('OCCP').PWGTP.agg(['size','sum']); w1=d1.groupby('OCCP').PWGTP.agg(['size','sum'])
for c,t in occ.items():
    if not c[0].isdigit(): continue
    cl,why=L.classify(c,t)
    rows.append(dict(occp=c, official_title=t, soc_major_prefix=t.split('-')[0], occ_class=cl, rule=why,
        bay_n_unw_2019_23=int(w5['size'].get(c,0)), bay_w_2019_23=float(w5['sum'].get(c,0)),
        bay_n_unw_2024=int(w1['size'].get(c,0)), bay_w_2024=float(w1['sum'].get(c,0))))
x=pd.DataFrame(rows); x.to_csv(out,index=False)
print(x.occ_class.value_counts())
o=x[x.occ_class=='OTHER'].sort_values('bay_w_2019_23',ascending=False)
print('OTHER weighted share 5yr', o.bay_w_2019_23.sum()/x.bay_w_2019_23.sum(), ' 2024', o.bay_w_2024.sum()/x.bay_w_2024.sum(), 'n', o.bay_n_unw_2019_23.sum(), 'of', x.bay_n_unw_2019_23.sum())
print(o.head(25)[['occp','official_title','bay_n_unw_2019_23','bay_w_2019_23']].to_string())
print('OTHER by prefix'); print(o.groupby('soc_major_prefix').bay_w_2019_23.sum().sort_values(ascending=False))
for c in ['1005','1240','1021']:
    s=d5[d5.OCCP==c].groupby('SOCP').PWGTP.agg(['size','sum']); print(c, s.sort_values('sum',ascending=False).head(8))
print(x.groupby('occ_class')[['bay_n_unw_2019_23','bay_w_2019_23']].sum())
# sanity: data occp not in map, titles by class for AI classes
for k in ['AI_PRODUCER','DATA_ENG_ANALYTICS','PRODUCT_DESIGN','CUSTOMER_SUPPORT']:
    print(k, list(x[x.occ_class==k][['occp','official_title']].itertuples(index=False,name=None)))
