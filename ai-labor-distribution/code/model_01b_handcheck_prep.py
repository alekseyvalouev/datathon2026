import sys; sys.path.insert(0,"/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code")
import pandas as pd, numpy as np, re
from model_lib import *
b=pd.read_parquet(f"{BASE}/indeed_base_v3.parquet",columns=["jobid","title","company","bay","seeded","occ"]); t=pd.read_parquet(f"{BASE}/model_text.parquet")
q=pd.read_parquet(f"{BASE}/model_occ_other_scored.parquet").merge(pd.read_parquet(f"{BASE}/model_occ_other_scored_td.parquet"),on="jobid").merge(b,on="jobid").merge(t,on="jobid")
qb=q[q.bay]; print("Bay OTHER n",len(qb)); print(qb.p.describe())
s=qb.sample(110,random_state=SEED).reset_index(drop=True)
def ex(x):
    x=re.sub(r"\s+"," ",x); m=re.search(r"(responsibilit|duties|you will|what you.ll do|the role|position summary|job summary|essential functions)",x,re.I)
    i=max(0,m.start()-20) if m else 150
    return x[i:i+230]
s["excerpt"]=s.text.map(ex)
s[["jobid","title","company","pred","p","pred_td","excerpt"]].to_csv(f"{BASE}/model_handcheck_other_sample.csv",index=True)
for i,r in s.iterrows(): print(f"[{i}] {r.title} | {r.company} || PRED={r.pred} p={r.p:.2f} (td:{r.pred_td}) || {r.excerpt}")
