"""MODEL 4: demand-weighted demographic INCIDENCE ACCOUNTING (not a forecast, not causal). Posting-flow class mix x PUMS incumbent-stock race composition."""
import sys; sys.path.insert(0,"/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code")
import numpy as np, pandas as pd
from model_lib import *
RACES=['White','Black','Asian','Hispanic','AIAN','NHPI','Two_or_Other']; THR=150000; NB=300
rng=np.random.default_rng(SEED)
b=pd.read_parquet(f"{BASE}/indeed_base_v3.parquet",columns=["jobid","bay","county","seeded","occ"])
c=pd.read_csv(f"{BASE}/model_occ_reassigned.csv",usecols=["jobid","consensus"]); s=pd.read_csv(f"{BASE}/model_salary_predictions.csv",usecols=["jobid","sal_mid","has_salary","pred_usd_annualised","train_ok","sal_period","parttime"])
d=b.merge(c,on="jobid").merge(s,on="jobid"); d=d[d.bay]
MAP={"AI_DATA_WORK":"AI_PRODUCER","LEGAL_PROF":"OTHER"}      # PUMS taxonomy has no AI_DATA_WORK / LEGAL_PROF class
d["pc"]=d.consensus.replace(MAP)
d["pay"]=np.where(d.has_salary&d.sal_mid.between(15000,1e6),d.sal_mid,d.pred_usd_annualised)   # disclosed else imputed (FT-equivalent annualised)
d["pay_disc"]=np.where(d.has_salary&d.sal_mid.between(15000,1e6),d.sal_mid,np.nan)
d["aipos"]=d.pc.isin(["AI_PRODUCER","SOFTWARE_ENG","DATA_ENG_ANALYTICS"]); d["exposed"]=d.pc.isin(EXPOSED)
p=pd.read_parquet(f"{BASE}/pums_bay.parquet",columns=["county","race_eth","occ_class","annual_wage_adj","PWGTP"])
p=p[p.occ_class.notna()]
def comp(df): 
    w=df.groupby("race_eth").PWGTP.sum().reindex(RACES).fillna(0); return w/w.sum()
bay_comp={k:comp(g) for k,g in p.groupby("occ_class")}
bay_comp_hi={k:comp(g[g.annual_wage_adj>=THR]) for k,g in p.groupby("occ_class") if (g.annual_wage_adj>=THR).sum()>=30}
cty_comp={}; cty_comp_hi={}; med_wage={}
for (cy,k),g in p.groupby(["county","occ_class"]):
    cty_comp[(cy,k)]=comp(g) if len(g)>=40 else bay_comp[k]
    gh=g[g.annual_wage_adj>=THR]; cty_comp_hi[(cy,k)]=comp(gh) if len(gh)>=30 else bay_comp_hi.get(k,bay_comp[k])
    w=g.dropna(subset=["annual_wage_adj"]); o=np.argsort(w.annual_wage_adj.values); cw=np.cumsum(w.PWGTP.values[o]); med_wage[(cy,k)]=w.annual_wage_adj.values[o][np.searchsorted(cw,cw[-1]/2)]
def implied(df,county,hi=False):
    """df postings (rows) -> weighted race shares by class composition (counts each posting equally)."""
    cnt=df.pc.value_counts(); tot=np.zeros(len(RACES))
    for k,n in cnt.items():
        cm=(cty_comp_hi if hi else cty_comp).get((county,k)) if county else None
        cm=cm if cm is not None else (bay_comp_hi.get(k,bay_comp[k]) if hi else bay_comp[k])
        tot+=n*cm.values
    return tot/tot.sum() if tot.sum()>0 else tot
def stock(mask_cls,county):
    g=p[p.occ_class.isin(mask_cls)] if mask_cls is not None else p
    if county: g=g[g.county==county]
    return comp(g).values
rows=[]
def boot_ci(df,county,hi):
    m=[]; n=len(df)
    for _ in range(NB):
        x=df.iloc[rng.integers(0,n,n)]; m.append(implied(x,county,hi))
    m=np.array(m); return np.percentile(m,5,axis=0),np.percentile(m,95,axis=0)
def emit(measure,county,df,shares,n,lo=None,hi_=None,wage=None):
    r=dict(county=county or "Bay Area (9 counties)",measure=measure,n_postings=n,implied_incumbent_median_wage=wage)
    for i,rc in enumerate(RACES):
        r[rc]=shares[i]; 
        if lo is not None: r[rc+"_p05"]=lo[i]; r[rc+"_p95"]=hi_[i]
    rows.append(r)
def wage_of(df,county): 
    v=[med_wage.get((county,k),np.nan)*n for k,n in df.pc.value_counts().items()] if county else [np.nan]; return float(np.nansum(v)/len(df)) if county and len(df) else np.nan
for sample,dd in [("UNSEEDED",d[~d.seeded]),("SEEDED_INCLUSIVE_sensitivity",d)]:
    for county in [None]+sorted(d.county.unique()):
        x=dd if county is None else dd[dd.county==county]
        if len(x)<20: continue
        hp=x[x.aipos&(x.pay>=THR)]; hd=x[x.aipos&(x.pay_disc>=THR)]; ex=x[x.exposed]
        for meas,df,hi in [("A_highpay_AIPOSITIONED_demand__incumbent_comp",hp,False),("A2_highpay_AIPOSITIONED_demand__comp_of_incumbents_earning>=150k",hp,True),
                           ("A3_highpay_AIPOSITIONED_demand__disclosed_pay_only",hd,False),("B_EXPOSED_demand__posting_weighted_incumbent_comp",ex,False),("ALL_postings_demand__incumbent_comp",x,False)]:
            if len(df)<10: continue
            lo,hi_=boot_ci(df,county,hi) if (sample=="UNSEEDED" and len(df)>=10) else (None,None)
            emit(f"{sample}|{meas}",county,df,implied(df,county,hi),len(df),lo,hi_,wage_of(df,county))
    # PUMS stock references (same under both samples)
for county in [None]+sorted(d.county.unique()):
    emit("PUMS_STOCK|EXPOSED_employment_base",county,None,stock(EXPOSED,county),np.nan)
    emit("PUMS_STOCK|AIPOSITIONED_employment_base",county,None,stock(["AI_PRODUCER","SOFTWARE_ENG","DATA_ENG_ANALYTICS"],county),np.nan)
    emit("PUMS_STOCK|ALL_employed",county,None,stock(None,county),np.nan)
R=pd.DataFrame(rows); R.to_csv(f"{BASE}/model_demand_incidence.csv",index=False)
pd.set_option("display.width",250); print(R[R.measure.str.startswith(("UNSEEDED|A_","UNSEEDED|B_","PUMS"))][["county","measure","n_postings"]+RACES].round(3).to_string())
# PUMS class wage / composition table for memo
print(d[~d.seeded].pc.value_counts(normalize=True).round(3))
