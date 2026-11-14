import sys; sys.path.insert(0,"/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code")
import pandas as pd, numpy as np, re
from model_lib import *
TAU=0.6
b=pd.read_parquet(f"{BASE}/indeed_base_v3.parquet",columns=["jobid","title","company","company_norm","bay","seeded"]); t=pd.read_parquet(f"{BASE}/model_text.parquet")
o=pd.read_parquet(f"{BASE}/model_occ_oof.parquet").merge(b,on="jobid").merge(t,on="jobid")
ov=o[(o.oof_p>=0.9)&(o.p_regex<0.05)&(o.oof_pred!="MANAGEMENT")&(o.regex_occ!="AI_DATA_WORK")]
print("override candidates (all CA)",len(ov),"of",len(o)); print(ov.groupby(["regex_occ","oof_pred"]).size().sort_values(ascending=False).head(12))
d0=pd.read_csv(f"{BASE}/model_handcheck_disagree_verdicts.csv",index_col=0).merge(ov[["jobid"]],on="jobid")
print("prior sample rows meeting override rule:",d0.verdict.value_counts().to_dict())
q=pd.read_parquet(f"{BASE}/model_occ_other_scored.parquet").merge(b,on="jobid").merge(t,on="jobid")
qb=q[q.bay&(q.pred!="MANAGEMENT")&(q.p>=TAU)]; prev=set(pd.read_csv(f"{BASE}/model_handcheck_other_sample.csv").jobid)
print("Bay OTHER n",int(q.bay.sum()),"assigned under rule",len(qb),len(qb)/q.bay.sum())
def ex(x):
    x=re.sub(r"\s+"," ",x); m=re.search(r"(responsibilit|duties|you will|what you.ll do|the role|position summary|job summary)",x,re.I); i=max(0,m.start()-20) if m else 100
    return x[i:i+170]
s1=qb[~qb.jobid.isin(prev)].sample(45,random_state=SEED+1).reset_index(drop=True); s1["excerpt"]=s1.text.map(ex)
s1[["jobid","title","company","pred","p","excerpt"]].to_csv(f"{BASE}/model_handcheck_other_sample2.csv")
for i,r in s1.iterrows(): print(f"[{i}] {r.title[:70]} | {r.company[:20]} || {r.pred} {r.p:.2f} || {r.excerpt}")
s2=ov.sample(30,random_state=SEED+2).reset_index(drop=True); s2["excerpt"]=s2.text.map(ex)
s2[["jobid","title","company","regex_occ","oof_pred","oof_p","excerpt"]].to_csv(f"{BASE}/model_handcheck_override_sample.csv")
print("-----OVERRIDES")
for i,r in s2.iterrows(): print(f"[{i}] {r.title[:70]} | {r.company[:20]} || REGEX={r.regex_occ} MODEL={r.oof_pred} {r.oof_p:.2f} || {r.excerpt[:140]}")
