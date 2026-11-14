import pandas as pd, numpy as np
S='/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad'
B=S+'/base/'; O=S+'/out/'
POS=['AI_PRODUCER','SOFTWARE_ENG','DATA_ENG_ANALYTICS']
EXP=['CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED']
def load():
    d=pd.read_parquet(B+'indeed_base_v3.parquet')
    d['grp']=np.where(d.occ.isin(POS),'AI_POSITIONED',np.where(d.occ.isin(EXP),'EXPOSED',d.occ))
    # salary sanity: keep 15k..1.5M annualized, drop inverted
    ok=d.sal_mid.between(15000,1.5e6)
    d['sal_ok']=d.has_salary & ok
    d['lsal']=np.log(d.sal_mid.where(d.sal_ok))
    d['width']=(d.sal_hi/d.sal_lo).where(d.sal_ok)
    d['hourly']=d.sal_ok&(d.sal_period=='hour'); d['rate']=(d.sal_mid/2080).where(d.hourly); d['seeded']=d.seeded.astype(bool)
    return d
def q(s,p): return s.quantile(p)
