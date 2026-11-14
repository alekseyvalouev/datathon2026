import sys; sys.path.insert(0,"/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code")
"""MODEL 1a: occupation classifier from description text. Company-split evaluation, baselines, random-split comparison, OOF scores, OTHER scoring."""
import numpy as np, pandas as pd, scipy.sparse as sp, time
from sklearn.svm import LinearSVC
from sklearn.multiclass import OneVsRestClassifier
from sklearn.model_selection import GroupShuffleSplit, GroupKFold, train_test_split
from sklearn.metrics import f1_score, accuracy_score, precision_recall_fscore_support, confusion_matrix
from scipy.special import softmax
from scipy.optimize import minimize_scalar
from model_lib import *
t0=time.time()
d=load(); print("loaded",d.shape,time.time()-t0)
Xd=tfidf_desc(d); Xt=tfidf_title(d); print("tfidf",Xd.shape,Xt.shape,time.time()-t0)
Xb=sp.hstack([Xd,Xt]).tocsr()
lab=np.where(d.occ.values!="OTHER")[0]; oth=np.where(d.occ.values=="OTHER")[0]
y=d.occ.values; classes=sorted(set(y[lab]))
def fit(X,idx): 
    m=OneVsRestClassifier(LinearSVC(C=0.5,random_state=SEED),n_jobs=8); m.fit(X[idx],y[idx]); return m
# ---- splits
gss=GroupShuffleSplit(n_splits=1,test_size=0.2,random_state=SEED)
tr_i,te_i=next(gss.split(lab,groups=d.grp.values[lab])); trC,teC=lab[tr_i],lab[te_i]
trR,teR=train_test_split(lab,test_size=0.2,random_state=SEED)
print("company split train/test",len(trC),len(teC),"n companies shared:",len(set(d.grp[trC])&set(d.grp[teC])),
      "| random split: test rows whose company is in train:",np.mean(d.grp[teR].isin(set(d.grp[trR]))).round(3))
rows=[]
def rec(model,split,yt,yp,extra=None):
    rows.append(dict(model="M1_occ",name=model,split=split,n_test=len(yt),macro_f1=f1_score(yt,yp,average="macro"),
        weighted_f1=f1_score(yt,yp,average="weighted"),accuracy=accuracy_score(yt,yp)))
# baselines
maj=pd.Series(y[trC]).mode()[0]
rec("majority_class","company",y[teC],np.full(len(teC),maj))
res={}
for nm,X in [("title_only_linear",Xt),("desc_only_tfidf_svm",Xd),("title_plus_desc_tfidf_svm",Xb)]:
    for sn,(a,b) in {"company":(trC,teC),"random_row":(trR,teR)}.items():
        m=fit(X,a); p=m.predict(X[b]); rec(nm,sn,y[b],p); res[(nm,sn)]=(m,p,b)
        print(nm,sn,round(rows[-1]["macro_f1"],4),round(rows[-1]["accuracy"],4),time.time()-t0,flush=True)
M=pd.DataFrame(rows)
# seeded vs unseeded + title-novel breakdown (company split)
sd=d.seeded.values; extra=[]
trt=set(d.title_c.values[trC])
for nm in ["title_only_linear","desc_only_tfidf_svm","title_plus_desc_tfidf_svm"]:
    m,p,b=res[(nm,"company")]
    for lbl,mask in [("seeded",sd[b]),("unseeded",~sd[b]),("title_not_in_train",~np.array([t in trt for t in d.title_c.values[b]]))]:
        extra.append(dict(model="M1_occ",name=nm,split="company|"+lbl,n_test=int(mask.sum()),macro_f1=f1_score(y[b][mask],p[mask],average="macro"),
          weighted_f1=f1_score(y[b][mask],p[mask],average="weighted"),accuracy=accuracy_score(y[b][mask],p[mask])))
M=pd.concat([M,pd.DataFrame(extra)]); M.to_csv(f"{BASE}/model_m1_metrics_tmp.csv",index=False); print(M.to_string())
# per-class + confusion on company split
pc=[]
for nm in ["title_only_linear","desc_only_tfidf_svm","title_plus_desc_tfidf_svm"]:
    m,p,b=res[(nm,"company")]
    pr,rc,f,s=precision_recall_fscore_support(y[b],p,labels=classes,zero_division=0)
    pc.append(pd.DataFrame(dict(model=nm,cls=classes,precision=pr,recall=rc,f1=f,support=s)))
    cm=pd.DataFrame(confusion_matrix(y[b],p,labels=classes),index=classes,columns=classes); cm.to_csv(f"{BASE}/model_occ_confusion_{nm}.csv")
pd.concat(pc).to_csv(f"{BASE}/model_occ_perclass.csv",index=False)
# ---- OOF (company-grouped 5-fold) desc-only scores on all labelled -> temperature + disagreement set
oof=np.zeros((len(lab),len(classes)),np.float32)
for k,(a,b) in enumerate(GroupKFold(n_splits=5,shuffle=True,random_state=SEED).split(lab,groups=d.grp.values[lab])):
    m=fit(Xd,lab[a]); assert list(m.classes_)==classes; oof[b]=m.decision_function(Xd[lab[b]]); print("fold",k,time.time()-t0,flush=True)
yi=np.array([classes.index(c) for c in y[lab]])
def nll(T): 
    p=softmax(oof*T,axis=1); return -np.mean(np.log(p[np.arange(len(yi)),yi]+1e-12))
T=minimize_scalar(nll,bounds=(0.5,30),method="bounded").x; print("temperature",T)
P=softmax(oof*T,axis=1)
o=pd.DataFrame(dict(idx=lab,jobid=d.jobid.values[lab],regex_occ=y[lab],oof_pred=np.array(classes)[P.argmax(1)],oof_p=P.max(1),
     p_regex=P[np.arange(len(yi)),yi])); o.to_parquet(f"{BASE}/model_occ_oof.parquet")
print("OOF macroF1 desc-only (5-fold company)",f1_score(y[lab],o.oof_pred,average="macro"),"acc",accuracy_score(y[lab],o.oof_pred))
# ---- final model on all labelled; score OTHER (all CA)
m=fit(Xd,lab); S=m.decision_function(Xd[oth]); Po=softmax(S*T,axis=1)
q=pd.DataFrame(dict(idx=oth,jobid=d.jobid.values[oth],pred=np.array(classes)[Po.argmax(1)],p=Po.max(1)))
for j,c in enumerate(classes): q["p_"+c]=Po[:,j]
q.to_parquet(f"{BASE}/model_occ_other_scored.parquet")
# title+desc variant on OTHER for comparison
m2=fit(Xb,lab); S2=m2.decision_function(Xb[oth]); P2=softmax(S2*T,axis=1)
pd.DataFrame(dict(jobid=d.jobid.values[oth],pred_td=np.array(classes)[P2.argmax(1)],p_td=P2.max(1))).to_parquet(f"{BASE}/model_occ_other_scored_td.parquet")
pd.Series(dict(T=T)).to_csv(f"{BASE}/model_occ_T.csv")
print("done",time.time()-t0)
