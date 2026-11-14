"""My (Claude's) manual read-through verdicts. c=correct, a=ambiguous/defensible-not-best, w=wrong.  Disagreement verdicts: M=model right, R=regex right, B=both defensible, N=neither."""
import sys; sys.path.insert(0,"/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code")
import pandas as pd, numpy as np
from model_lib import *
s=pd.read_csv(f"{BASE}/model_handcheck_other_sample.csv",index_col=0)
W=[4,7,19,22,26,28,29,31,37,38,39,41,51,53,55,59,70,72,76,78,82,85,87,93,105,107,108]
A=[13,16,21,27,30,33,48,50,58,60,62,65,66,73,75,77,80,81,83,99,102,103,90]
s["verdict"]=["w" if i in W else "a" if i in A else "c" for i in s.index]
s.to_csv(f"{BASE}/model_handcheck_other_verdicts.csv")
print("n",len(s),s.verdict.value_counts().to_dict())
print("strict accuracy (correct only):",(s.verdict=="c").mean().round(3)," lenient (correct+ambiguous):",(s.verdict!="w").mean().round(3))
s["bin"]=pd.cut(s.p,[0,.4,.6,.8,.9,1.0001])
print(s.groupby("bin",observed=True).verdict.agg(n="size",strict=lambda v:(v=="c").mean(),lenient=lambda v:(v!="w").mean()))
for t in [0.0,0.5,0.6,0.7,0.8,0.9]:
    k=s[s.p>=t]; print("tau",t,"n",len(k),"strict",round((k.verdict=="c").mean(),3),"lenient",round((k.verdict!="w").mean(),3))
print(s.groupby("pred").verdict.agg(n="size",strict=lambda v:(v=="c").mean(),lenient=lambda v:(v!="w").mean()).sort_values("n",ascending=False))
d=pd.read_csv(f"{BASE}/model_handcheck_disagree_sample.csv",index_col=0)
Mr=[1,3,5,7,8,9,12,13,16,17,20,22,24,27,32,37,38,40,41,43,46,52,53]; Rr=[2,10,14,15,26,35,36,42,48,51,54]+list(range(55,67)); Nn=[4,50]
d["verdict"]=["M" if i in Mr else "R" if i in Rr else "N" if i in Nn else "B" for i in d.index]
d.to_csv(f"{BASE}/model_handcheck_disagree_verdicts.csv"); print(len(d),d.verdict.value_counts().to_dict())
r=d[~d.is_da]; print("excluding DataAnnotation: n",len(r),r.verdict.value_counts().to_dict(),"| of decided (M vs R):",(r.verdict=="M").sum(),"vs",(r.verdict=="R").sum())
