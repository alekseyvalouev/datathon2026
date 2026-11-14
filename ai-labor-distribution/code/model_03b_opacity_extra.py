import sys; sys.path.insert(0,"/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code")
import numpy as np, pandas as pd, scipy.sparse as sp, re
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, average_precision_score
from model_lib import *
d=load(); cons=pd.read_csv(f"{BASE}/model_occ_reassigned.csv",usecols=["jobid","consensus"]); d=d.merge(cons,on="jobid"); d["occ_c"]=d.consensus
d["opaque"]=(~d.has_salary).astype(int); yv=d.opaque.values
X=sp.hstack([tfidf_desc(d),tfidf_title(d)]).tocsr()
vocab=np.concatenate([pd.read_csv(f"{CACHE}/desc_vocab.csv").iloc[:,0].astype(str).values,("T:"+pd.read_csv(f"{CACHE}/title_vocab.csv").iloc[:,0].astype(str)).values])
bad=re.compile(r"salnum|pay|salary|compensation|wage|range|hour|hr|hourly|per |annual|rate|bonus|\$")
keep=np.array([not bad.search(v) for v in vocab]); print("vocab kept",keep.sum(),"of",len(vocab))
Xm=X[:,np.where(keep)[0]]
oof=np.zeros(len(d))
for a,b in GroupKFold(n_splits=5,shuffle=True,random_state=SEED).split(d,groups=d.grp.values):
    oof[b]=LogisticRegression(C=2,max_iter=300).fit(Xm[a],yv[a]).predict_proba(Xm[b])[:,1]
rows=[]
for sc,m in [("CA_all",np.ones(len(d),bool)),("Bay",d.bay.values),("Bay_unseeded",d.bay.values&~d.seeded.values)]:
    rows.append(dict(scope=sc,auc=roc_auc_score(yv[m],oof[m]),avg_precision=average_precision_score(yv[m],oof[m]),base_rate=yv[m].mean()))
print(pd.DataFrame(rows)); pd.DataFrame(rows).to_csv(f"{BASE}/model_opacity_text_masked_metrics.csv",index=False)
# clean adjusted odds ratios, Bay unseeded, cluster bootstrap
B=d[d.bay&~d.seeded].copy()
cty=["Alameda","Contra Costa","Marin","Napa","San Francisco","San Mateo","Solano","Sonoma"]
Z=pd.DataFrame(index=B.index)
for c in sorted(B.occ_c.unique()):
    if c!="MANAGEMENT": Z["occ_"+c]=(B.occ_c==c).astype(float)
for c in cty: Z["county_"+c]=(B.county==c).astype(float)
for c in ["remote","hybrid","contract","parttime","junior","senior","deg_ba","deg_grad","ai_any"]: Z[c]=B[c].astype(float)
Z["log_desc_len"]=np.log1p(B.desc_len); Z["rating_missing"]=B.company_rating.isna().astype(float); Z["log_reviews"]=np.log1p(B.company_reviews).fillna(0)
Zs=(Z-Z.mean())/Z.std(); yb=B.opaque.values; gb=pd.factorize(B.grp)[0]
def fitc(ix): return LogisticRegression(C=100,max_iter=1000).fit(Zs.values[ix],yb[ix]).coef_[0]/Z.std().values
coef=fitc(np.arange(len(yb))); byg=pd.Series(np.arange(len(gb))).groupby(gb).apply(np.array); rb=np.random.default_rng(SEED); ug=np.unique(gb); bs=[]
for _ in range(100): bs.append(fitc(np.concatenate(byg.loc[rb.choice(ug,len(ug))].values)))
bs=np.array(bs)
OR=pd.DataFrame(dict(feature=Z.columns,odds_ratio=np.exp(coef),ci_lo=np.exp(np.percentile(bs,2.5,0)),ci_hi=np.exp(np.percentile(bs,97.5,0)))); OR.to_csv(f"{BASE}/model_opacity_bay_adjusted_OR_clean.csv",index=False)
print("BASE: occ=MANAGEMENT, county=Santa Clara; Bay unseeded n",len(B)); print(OR.round(3).to_string())
# adjusted marginal opacity by class: predicted rate holding covariates at sample mean
