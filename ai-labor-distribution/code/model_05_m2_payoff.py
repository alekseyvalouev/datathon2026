import sys; sys.path.insert(0,"/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code")
import numpy as np, pandas as pd, pickle
from model_lib import *
pd.set_option("display.width",250); pd.set_option("display.max_rows",300)
P,fold=pickle.load(open(f"{CACHE}/m2_cv.pkl","rb"))
s=pd.read_csv(f"{BASE}/model_salary_predictions.csv"); s["hourly_equiv_actual"]=s.sal_mid/2080
y=np.log(s.sal_mid.values); T=np.where(fold>=0)[0]
# robust metrics
res=(P["lgbm_text_stack"]-y)[T]; ar=np.abs(res)
rows=[]
for nm in ["occ_median","ols_structured","ridge_text","lgbm_structured","lgbm_text_stack"]:
    r=(P[nm]-y)[T]; 
    for sc,m in [("CA_all",np.ones(len(T),bool)),("Bay",s.bay.values[T])]:
        rows.append(dict(name=nm,scope=sc,medae_log=np.median(np.abs(r[m])),p90_abs_log=np.quantile(np.abs(r[m]),.9),share_within_20pct=np.mean(np.abs(r[m])<np.log(1.2))))
R=pd.DataFrame(rows); print(R.round(3).to_string()); R.to_csv(f"{BASE}/model_m2_robust_metrics.csv",index=False)
# bias by actual-pay quintile (regression to mean)
q=pd.qcut(y[T],5,labels=False); print("bias(pred-actual) by quintile of ACTUAL log pay:",pd.Series(res).groupby(q).mean().round(3).to_dict())
q2=pd.qcut(P["lgbm_text_stack"][T],5,labels=False); print("bias by quintile of PREDICTED pay:",pd.Series(res).groupby(q2).mean().round(3).to_dict())
# ---- imputation payoff (Bay, unseeded primary)
c=pd.read_csv(f"{BASE}/model_occ_reassigned.csv",usecols=["jobid","consensus"]); s=s.merge(c,on="jobid"); s["cls"]=s.consensus
bb=pd.read_parquet(f"{BASE}/indeed_base_v3.parquet",columns=["jobid","job_type"]); s=s.merge(bb,on="jobid")
B=s[s.bay&(s.cls!="AI_DATA_WORK")].copy()
B["disc"]=B.train_ok; B["pay_hr"]=np.where(B.disc,B.sal_mid/2080,B.pred_hourly_equiv)
B["pay_hr_disc"]=np.where(B.disc,B.sal_mid/2080,np.nan)
print("Bay postings",len(B),"disclosers usable",int(B.disc.sum()),"nondisclosers imputed",int(B.imputed.sum()),"nondisc not imputed",int((~B.has_salary&~B.imputed).sum()))
def agg(df):
    return pd.Series(dict(n=len(df),n_disc=int(df.disc.sum()),n_imp=int(df.imputed.sum()),
      med_hourly_equiv_disclosed=np.nanmedian(df.pay_hr_disc),med_hourly_equiv_disc_plus_imputed=np.nanmedian(df.pay_hr),
      med_annual_FTE_disclosed=np.nanmedian(df.pay_hr_disc)*2080,med_annual_FTE_disc_plus_imputed=np.nanmedian(df.pay_hr)*2080,
      mean_pred_nondisc=df[df.imputed].pred_log.mean(),mean_pred_disc_oof=df[df.disc].pred_log.mean(),mean_actual_disc=np.log(df[df.disc].sal_mid).mean()))
for nm,sub in [("Bay_unseeded",B[~B.seeded]),("Bay_all",B)]:
    t=sub.groupby("cls").apply(agg,include_groups=False); t["shift_pct"]=100*(t.med_hourly_equiv_disc_plus_imputed/t.med_hourly_equiv_disclosed-1)
    t["rank_disclosed"]=t.med_hourly_equiv_disclosed.rank(ascending=False); t["rank_with_imputed"]=t.med_hourly_equiv_disc_plus_imputed.rank(ascending=False)
    t["pred_gap_log_nondisc_minus_disc"]=t.mean_pred_nondisc-t.mean_pred_disc_oof
    t.round(3).to_csv(f"{BASE}/model_salary_imputation_by_class_{nm}.csv"); print(nm); print(t.round(3).to_string())
# selection: within class x county, predicted pay of nondisclosers vs disclosers (both from model preds, so comparing observables only)
S=B[~B.seeded&B.pred_log.notna()].copy(); S["nd"]=(~S.has_salary).astype(float)
S["cell"]=S.cls+"|"+S.county
S["pl_dm"]=S.pred_log-S.groupby("cell").pred_log.transform("mean")
S["nd_dm"]=S.nd-S.groupby("cell").nd.transform("mean")
b=(S.pl_dm*S.nd_dm).sum()/(S.nd_dm**2).sum(); 
# cluster-bootstrap by company
S["grp"]=S.jobid.map(pd.read_parquet(f"{BASE}/indeed_base_v3.parquet",columns=["jobid","company_norm"]).set_index("jobid").company_norm).fillna(S.jobid)
g=S.groupby("grp"); rb=np.random.default_rng(SEED); ug=S.grp.unique(); gs={k:v for k,v in g}
num=g.apply(lambda x:(x.pl_dm*x.nd_dm).sum()); den=g.apply(lambda x:(x.nd_dm**2).sum()); bs=[]
for _ in range(300):
    pk=rb.choice(len(ug),len(ug)); n_=num.values[pk].sum(); d_=den.values[pk].sum(); bs.append(n_/d_)
print("WITHIN class x county: predicted log pay gap, nondisclosers minus disclosers = %.4f (95%% CI %.4f, %.4f)  => %.1f%%"%(b,*np.percentile(bs,[2.5,97.5]),100*(np.exp(b)-1)))
for cl in sorted(S.cls.unique()):
    x=S[S.cls==cl]; 
    if x.nd.sum()>=20: print(cl,"gap(log)",round(x[x.nd==1].pred_log.mean()-x[x.nd==0].pred_log.mean(),3),"within-county",round(((x.pl_dm*x.nd_dm).sum()/(x.nd_dm**2).sum()),3),"n_nd",int(x.nd.sum()))
pd.Series(dict(gap_log=b,ci_lo=np.percentile(bs,2.5),ci_hi=np.percentile(bs,97.5))).to_csv(f"{BASE}/model_salary_selection_gap.csv")
# interval widths
I=B[B.imputed]; print("imputed PI80 median width ratio hi/lo:",(I.pi80_hi_usd/I.pi80_lo_usd).median().round(2),"| disclosed OOF PI80 ratio",(B[B.disc].pi80_hi_usd/B[B.disc].pi80_lo_usd).median().round(2))
print("imputed period split:",I.period_used.value_counts(normalize=True).round(3).to_dict(), "| disclosed hourly share",(B[B.disc].sal_period=="hour").mean().round(3))
print("p_hourly among nondisc:",I.p_hourly.describe().round(3).to_dict())
