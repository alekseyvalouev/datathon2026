import sys; sys.path.insert(0,"/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code")
import pandas as pd, numpy as np, re
from model_lib import *
b=pd.read_parquet(f"{BASE}/indeed_base_v3.parquet",columns=["jobid","title","company","company_norm","bay","seeded"]); t=pd.read_parquet(f"{BASE}/model_text.parquet")
o=pd.read_parquet(f"{BASE}/model_occ_oof.parquet").merge(b,on="jobid").merge(t,on="jobid")
dis=o[o.oof_pred!=o.regex_occ]; print("OOF disagreements",len(dis),"of",len(o),f"({len(dis)/len(o):.3f})")
conf=dis[(dis.oof_p>=0.7)&(dis.p_regex<0.15)]; print("confident disagreements",len(conf))
print(conf.groupby(["regex_occ","oof_pred"]).size().sort_values(ascending=False).head(25))
da=o[o.company_norm.fillna("").str.contains("dataannotation")]; print("DataAnnotation rows",len(da)); print(da.regex_occ.value_counts()); print(da.oof_pred.value_counts())
print(da.title.str.contains("AI Trainer",case=False).mean())
rs=np.random.RandomState(SEED)
s1=conf.sample(55,random_state=SEED); s2=da.sample(min(12,len(da)),random_state=SEED)
s=pd.concat([s1,s2]).drop_duplicates("jobid").reset_index(drop=True)
def ex(x):
    x=re.sub(r"\s+"," ",x); m=re.search(r"(responsibilit|duties|you will|what you.ll do|the role|position summary|job summary)",x,re.I); i=max(0,m.start()-20) if m else 100
    return x[i:i+200]
s["excerpt"]=s.text.map(ex); s["is_da"]=s.company_norm.fillna("").str.contains("dataannotation")
s[["jobid","title","company","regex_occ","oof_pred","oof_p","p_regex","is_da","excerpt"]].to_csv(f"{BASE}/model_handcheck_disagree_sample.csv")
for i,r in s.iterrows(): print(f"[{i}] {r.title[:70]} | {r.company[:20]} || REGEX={r.regex_occ} MODEL={r.oof_pred} ({r.oof_p:.2f}) || {r.excerpt[:150]}")
