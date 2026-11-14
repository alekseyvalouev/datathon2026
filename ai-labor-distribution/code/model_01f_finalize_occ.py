import sys; sys.path.insert(0,"/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code")
import pandas as pd, numpy as np
from model_lib import *
TAU=0.6; OV_P=0.9; OV_PR=0.05
b=pd.read_parquet(f"{BASE}/indeed_base_v3.parquet",columns=["jobid","occ","bay","seeded","county"])
o=pd.read_parquet(f"{BASE}/model_occ_oof.parquet")[["jobid","oof_pred","oof_p","p_regex"]]
q=pd.read_parquet(f"{BASE}/model_occ_other_scored.parquet")[["jobid","pred","p"]]
r=b.merge(o,on="jobid",how="left").merge(q,on="jobid",how="left")
r["predicted_class"]=r.oof_pred.fillna(r.pred); r["predicted_prob"]=r.oof_p.fillna(r.p)
r["pred_source"]=np.where(r.occ=="OTHER","final_model_on_regex_OTHER","company_grouped_OOF")
ov=(r.occ!="OTHER")&(r.oof_p>=OV_P)&(r.p_regex<OV_PR)&(r.oof_pred!="MANAGEMENT")&(r.occ!="AI_DATA_WORK")&(r.oof_pred!=r.occ)
asg=(r.occ=="OTHER")&(r.pred!="MANAGEMENT")&(r.p>=TAU)
r["consensus"]=np.where(ov,r.oof_pred,np.where(asg,r.pred,r.occ))
r["consensus_source"]=np.where(ov,"regex_overridden_by_model",np.where(asg,"OTHER_reassigned_by_model",np.where(r.occ=="OTHER","OTHER_unresolved","regex_kept")))
out=r[["jobid","occ","predicted_class","predicted_prob","consensus","consensus_source","pred_source"]].rename(columns={"occ":"regex_occ"})
out.to_csv(f"{BASE}/model_occ_reassigned.csv",index=False)
print(out.consensus_source.value_counts())
# ---- hand-check roll-up
v1=pd.read_csv(f"{BASE}/model_handcheck_other_verdicts.csv",index_col=0)
rule=v1[(v1.pred!="MANAGEMENT")&(v1.p>=TAU)]
print("sample1 (all 110, no rule): strict",(v1.verdict=="c").mean().round(3),"lenient",(v1.verdict!="w").mean().round(3),"| rule-eligible in sample1 n",len(rule),"strict",(rule.verdict=="c").mean().round(3),"lenient",(rule.verdict!="w").mean().round(3))
print("MANAGEMENT predictions in sample1:",(v1.pred=="MANAGEMENT").sum(),"strict",(v1[v1.pred=="MANAGEMENT"].verdict=="c").mean().round(3))
s2=pd.read_csv(f"{BASE}/model_handcheck_other_sample2.csv",index_col=0)
A2=[3,8,20,21,22,25,34,36,39]; s2["verdict"]=["a" if i in A2 else "c" for i in s2.index]; s2.to_csv(f"{BASE}/model_handcheck_other_verdicts2.csv")
print("sample2 (fresh n=45, rule applied): strict",(s2.verdict=="c").mean().round(3),"lenient",(s2.verdict!="w").mean().round(3))
so=pd.read_csv(f"{BASE}/model_handcheck_override_sample.csv",index_col=0)
M=[1,3,4,9,10,11,12,13,14,16,19,20,22,24,25,26]; R=[2,8]; so["verdict"]=["M" if i in M else "R" if i in R else "B" for i in so.index]; so.to_csv(f"{BASE}/model_handcheck_override_verdicts.csv")
print("override sample n=30:",so.verdict.value_counts().to_dict())
# ---- distribution shift (Bay)
bay=r[r.bay].copy(); bay["cons"]=bay.consensus
tab=pd.DataFrame({"regex_all":bay.occ.value_counts(normalize=True),"consensus_all":bay.cons.value_counts(normalize=True),
    "regex_unseeded":bay[~bay.seeded].occ.value_counts(normalize=True),"consensus_unseeded":bay[~bay.seeded].cons.value_counts(normalize=True)}).fillna(0)
tab["n_regex_all"]=bay.occ.value_counts(); tab["n_cons_all"]=bay.cons.value_counts()
tab.to_csv(f"{BASE}/model_occ_bay_distribution.csv"); print((tab*1).round(4).to_string())
for nm,sub in [("all",bay),("unseeded",bay[~bay.seeded])]:
    for lab,col in [("regex","occ"),("consensus","cons")]:
        ai=sub[col].isin(AIPOS).mean(); ex=sub[col].isin(EXPOSED).mean(); ai3=sub[col].isin(["AI_PRODUCER","SOFTWARE_ENG","DATA_ENG_ANALYTICS"]).mean()
        print(nm,lab,"AI_POSITIONED(incl AI_DATA_WORK)",round(ai,4),"AI_POSITIONED(3 classes)",round(ai3,4),"EXPOSED",round(ex,4),"OTHER",round((sub[col]=="OTHER").mean(),4))
# share of denominators: among resolved only
for nm,sub in [("unseeded",bay[~bay.seeded])]:
    rr=sub[sub.occ!="OTHER"]; print("regex-labelled only denominators, AI3",rr.occ.isin(["AI_PRODUCER","SOFTWARE_ENG","DATA_ENG_ANALYTICS"]).mean().round(4),"EXPOSED",rr.occ.isin(EXPOSED).mean().round(4))
print("overrides by pair (Bay):"); print(bay[bay.consensus_source if False else ov[bay.index]].groupby(["occ","consensus"]).size().sort_values(ascending=False).head(10) if False else "")
