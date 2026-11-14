import sys; sys.path.insert(0,"/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code")
import numpy as np, pandas as pd, scipy.sparse as sp, time, lightgbm as lgb, statsmodels.api as sm
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_fscore_support, precision_recall_curve
from model_lib import *
t0=time.time()
d=load(); cons=pd.read_csv(f"{BASE}/model_occ_reassigned.csv",usecols=["jobid","consensus"])
d=d.merge(cons,on="jobid",how="left"); d["occ_c"]=d.consensus.fillna(d.occ)
Xtext=sp.hstack([tfidf_desc(d),tfidf_title(d)]).tocsr()
vocab=np.concatenate([pd.read_csv(f"{CACHE}/desc_vocab.csv").iloc[:,0].astype(str).values,("T:"+pd.read_csv(f"{CACHE}/title_vocab.csv").iloc[:,0].astype(str)).values])
d["opaque"]=(~d.has_salary).astype(int); yv=d.opaque.values
cty_top=d.county.value_counts().index[:15]; city_top=d.city.value_counts().index[:60]
S=pd.DataFrame(index=d.index)
S["occ"]=pd.Categorical(d.occ_c,categories=sorted(d.occ_c.unique()))
S["county"]=pd.Categorical(d.county.where(d.county.isin(cty_top),"Other"),categories=list(cty_top)+["Other"])
S["city"]=pd.Categorical(d.city.where(d.city.isin(city_top),"other"),categories=list(city_top)+["other"])
S["job_type"]=pd.Categorical(d.job_type.fillna("NA"),categories=sorted(d.job_type.fillna("NA").unique()))
for c in ["remote","hybrid","contract","parttime","fulltime","internship","senior","junior","deg_ba","deg_grad","no_deg","ai_any","ai_strict","ai_build","ai_use","bay"]: S[c]=d[c].astype(float)
S["yrs_min"]=d.yrs_min; S["log_desc_len"]=np.log1p(d.desc_len); S["rating"]=d.company_rating; S["log_reviews"]=np.log1p(d.company_reviews)
S["rating_missing"]=d.company_rating.isna().astype(float)
LGB=dict(n_estimators=400,learning_rate=0.05,num_leaves=63,min_child_samples=40,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,reg_lambda=2,random_state=SEED,n_jobs=8,verbose=-1)
idx=np.arange(len(d)); folds=list(GroupKFold(n_splits=5,shuffle=True,random_state=SEED).split(idx,groups=d.grp.values))
Z=pd.get_dummies(S,columns=["occ","county","city","job_type"],dtype=float)
Z["yrs_min_na"]=Z.yrs_min.isna().astype(float); Z["yrs_min"]=Z.yrs_min.fillna(Z.yrs_min.median()); Z["rating"]=Z.rating.fillna(Z.rating.median()); Z["log_reviews"]=Z.log_reviews.fillna(0)
Zs=(Z-Z.mean())/Z.std().replace(0,1)
P={k:np.zeros(len(d)) for k in ["majority","logit_structured","lgbm_structured","text_logit","lgbm_text_stack"]}
P["majority"][:]=yv.mean()
for k,(a,b) in enumerate(folds):
    P["logit_structured"][b]=LogisticRegression(C=0.5,max_iter=500).fit(Zs.iloc[a],yv[a]).predict_proba(Zs.iloc[b])[:,1]
    P["lgbm_structured"][b]=lgb.LGBMClassifier(**LGB).fit(S.iloc[a],yv[a]).predict_proba(S.iloc[b])[:,1]
    P["text_logit"][b]=LogisticRegression(C=2,max_iter=300).fit(Xtext[a],yv[a]).predict_proba(Xtext[b])[:,1]
    # stack: inner OOF text logit on train
    inner=np.zeros(len(a))
    for ia,ib in GroupKFold(n_splits=4,shuffle=True,random_state=SEED).split(a,groups=d.grp.values[a]):
        inner[ib]=LogisticRegression(C=2,max_iter=300).fit(Xtext[a[ia]],yv[a[ia]]).predict_proba(Xtext[a[ib]])[:,1]
    Sa=S.iloc[a].copy(); Sb=S.iloc[b].copy(); Sa["text_p"]=inner; Sb["text_p"]=P["text_logit"][b]
    P["lgbm_text_stack"][b]=lgb.LGBMClassifier(**LGB).fit(Sa,yv[a]).predict_proba(Sb)[:,1]
    print("fold",k,time.time()-t0,flush=True)
rows=[]
def metr(name,p,mask,scope):
    yt=yv[mask]; pp=p[mask]
    if name=="majority":
        rows.append(dict(model="M3_opacity",name=name,split=f"company_5fold_oof|{scope}",n_test=int(mask.sum()),auc=0.5,avg_precision=yt.mean(),precision_opaque=0.0,recall_opaque=0.0,f1_opaque=0.0,accuracy=1-yt.mean(),base_rate_opaque=yt.mean(),thr=np.nan)); return
    pr,rc,th=precision_recall_curve(yt,pp); f=2*pr*rc/(pr+rc+1e-12); j=np.argmax(f[:-1]); thr=th[j]
    rows.append(dict(model="M3_opacity",name=name,split=f"company_5fold_oof|{scope}",n_test=int(mask.sum()),auc=roc_auc_score(yt,pp),avg_precision=average_precision_score(yt,pp),
       precision_opaque=pr[j],recall_opaque=rc[j],f1_opaque=f[j],accuracy=float(((pp>=thr)==yt).mean()),base_rate_opaque=yt.mean(),thr=thr))
for scope,mask in [("CA_all",np.ones(len(d),bool)),("Bay",d.bay.values),("Bay_unseeded",d.bay.values&~d.seeded.values)]:
    for k,p in P.items(): metr(k,p,mask,scope)
M3=pd.DataFrame(rows); print(M3.to_string()); M3.to_csv(f"{BASE}/model_m3_metrics_tmp.csv",index=False)
# audit by class & county (Bay)
d["p"]=P["lgbm_text_stack"]; d["p_s"]=P["lgbm_structured"]
aud=[]
for st,col in [("occ_class","occ_c"),("county","county"),("group3",None)]:
    ser=d.occ_c.map(grp3) if col is None else d[col]
    for g,s in d[d.bay].groupby(ser[d.bay]):
        if len(s)<50: continue
        u=s[~s.seeded]
        aud.append(dict(subgroup_type=st,subgroup=g,n_bay=len(s),opaque_rate_raw=s.opaque.mean(),opaque_rate_unseeded=u.opaque.mean() if len(u) else np.nan,mean_pred=s.p.mean(),
            auc=roc_auc_score(s.opaque,s.p) if s.opaque.nunique()>1 else np.nan,auc_structured_only=roc_auc_score(s.opaque,s.p_s) if s.opaque.nunique()>1 else np.nan))
A=pd.DataFrame(aud); A.to_csv(f"{BASE}/model_opacity_audit.csv",index=False); print(A.to_string())
# drivers: (1) standardized logit coefficients (fit on all) (2) LGBM SHAP (3) text words
lm=LogisticRegression(C=0.5,max_iter=500).fit(Zs,yv); co=pd.Series(lm.coef_[0],index=Z.columns)
# (4) Bay-only adjusted odds ratios w/ company-clustered SE (statsmodels)
B=d[d.bay].copy(); Zb=pd.get_dummies(S.loc[B.index],columns=["occ","county","job_type"],dtype=float).drop(columns=["city"])
Zb=Zb.drop(columns=[c for c in Zb.columns if c.startswith("occ_") and c=="occ_OTHER"]+["county_Santa Clara"]+[c for c in Zb.columns if c.startswith("job_type_") ][:1])
Zb["yrs_min"]=Zb.yrs_min.fillna(Zb.yrs_min.median()); Zb["rating"]=Zb.rating.fillna(Zb.rating.median()); Zb["log_reviews"]=Zb.log_reviews.fillna(0); Zb=Zb.loc[:,Zb.std()>0].drop(columns=["bay"],errors="ignore")
Xo=Zb.astype(float); mu,sd=Xo.mean(),Xo.std().replace(0,1); Xs=((Xo-mu)/sd).values; yb=B.opaque.values; gb=pd.factorize(B.grp)[0]
def fitc(ix): return LogisticRegression(C=50,max_iter=500).fit(Xs[ix],yb[ix]).coef_[0]/sd.values   # per-unit log-odds (weak L2 only to handle collinearity)
coef=fitc(np.arange(len(yb))); ug=np.unique(gb); rb=np.random.default_rng(SEED); bs=[]
byg=pd.Series(np.arange(len(gb))).groupby(gb).apply(np.array)
for _ in range(60):
    pick=rb.choice(ug,len(ug),replace=True); bs.append(fitc(np.concatenate(byg.loc[pick].values)))
bs=np.array(bs)
OR=pd.DataFrame(dict(feature=Xo.columns,odds_ratio=np.exp(coef),ci_lo=np.exp(np.percentile(bs,2.5,axis=0)),ci_hi=np.exp(np.percentile(bs,97.5,axis=0)))); OR.to_csv(f"{BASE}/model_opacity_bay_adjusted_OR.csv",index=False)
print(OR.sort_values("odds_ratio").to_string())
fm=lgb.LGBMClassifier(**LGB).fit(S,yv); sh=fm.booster_.predict(S.iloc[::5],pred_contrib=True)[:,:-1]
shap=pd.DataFrame(dict(feature=S.columns,mean_abs_contrib=np.abs(sh).mean(0))).sort_values("mean_abs_contrib",ascending=False); shap.to_csv(f"{BASE}/model_opacity_shap.csv",index=False); print(shap.head(15))
# direction: corr between feature and contribution
dirn=[(c,np.corrcoef(pd.to_numeric(S[c].iloc[::5],errors="coerce").fillna(0) if S[c].dtype!="category" else S[c].iloc[::5].cat.codes,sh[:,i])[0,1]) for i,c in enumerate(S.columns) if c not in ("occ","county","city","job_type")]
print(pd.DataFrame(dirn,columns=["feature","corr_with_shap"]).to_string())
tm=LogisticRegression(C=2,max_iter=300).fit(Xtext,yv); tc=pd.Series(tm.coef_[0],index=vocab)
pd.concat([tc.nlargest(40).rename("coef").reset_index().assign(direction="toward_NO_salary"),tc.nsmallest(40).rename("coef").reset_index().assign(direction="toward_salary_shown")]).to_csv(f"{BASE}/model_opacity_text_words.csv",index=False)
print(tc.nlargest(25)); print(tc.nsmallest(25))
# company concentration: share of opaque postings from top companies; within-company rate heterogeneity
g=d.groupby("grp").opaque.agg(["mean","size"]); big=g[g["size"]>=10]
print("companies>=10 postings:",len(big),"share with all-opaque:",(big["mean"]==1).mean(),"all-disclosed:",(big["mean"]==0).mean(),"mixed:",((big["mean"]>0)&(big["mean"]<1)).mean())
pd.Series(dict(n_comp10=len(big),all_opaque=(big["mean"]==1).mean(),all_disclosed=(big["mean"]==0).mean(),mixed=((big["mean"]>0)&(big["mean"]<1)).mean())).to_csv(f"{BASE}/model_opacity_company_concentration.csv")
d[["jobid","opaque","p"]].to_csv(f"{BASE}/model_opacity_oof.csv",index=False); print("done",time.time()-t0)
