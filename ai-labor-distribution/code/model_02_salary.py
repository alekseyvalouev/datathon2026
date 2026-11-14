import sys; sys.path.insert(0,"/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code")
import numpy as np, pandas as pd, scipy.sparse as sp, time, lightgbm as lgb
from sklearn.linear_model import Ridge, LogisticRegression, LinearRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
from model_lib import *
t0=time.time()
d=load(); cons=pd.read_csv(f"{BASE}/model_occ_reassigned.csv",usecols=["jobid","consensus"])
d=d.merge(cons,on="jobid",how="left"); d["occ_c"]=d.consensus.fillna(d.occ)
Xd=tfidf_desc(d); Xt=tfidf_title(d); Xtext=sp.hstack([Xd,Xt]).tocsr()
da=(d.occ_c=="AI_DATA_WORK")|d.company_norm.fillna("").str.contains("dataannotation")
ratio=d.sal_hi/d.sal_lo
d["train_ok"]=d.has_salary&d.sal_mid.between(15000,1e6)&(ratio<=5)&~da
d["y"]=np.log(d.sal_mid)
d["y_pt"]=np.log(d.sal_mid*np.where((d.sal_period=="hour")&d.parttime,0.5,1.0))   # robustness: part-time hourly annualised at 1040h
d["ishour"]=(d.sal_period=="hour")
print("salary rows",int(d.has_salary.sum()),"usable",int(d.train_ok.sum()),"excluded DataAnnotation/AI_DATA_WORK disclosers",int((d.has_salary&da).sum()))
# ---------- structured features
cty_top=d.county.value_counts().index[:15]; city_top=d.city.value_counts().index[:60]
def struct(d,period):
    S=pd.DataFrame(index=d.index)
    S["occ"]=pd.Categorical(d.occ_c,categories=sorted(d.occ_c.unique()))
    S["county"]=pd.Categorical(d.county.where(d.county.isin(cty_top),"Other"),categories=list(cty_top)+["Other"])
    S["city"]=pd.Categorical(d.city.where(d.city.isin(city_top),"other"),categories=list(city_top)+["other"])
    S["job_type"]=pd.Categorical(d.job_type.fillna("NA"),categories=sorted(d.job_type.fillna("NA").unique()))
    S["period"]=pd.Categorical(period,categories=["hour","year","month","week","day"])
    for c in ["remote","hybrid","contract","parttime","fulltime","internship","senior","junior","deg_ba","deg_grad","no_deg","ai_any","ai_strict","ai_build","ai_use","bay"]: S[c]=d[c].astype(float)
    S["yrs_min"]=d.yrs_min; S["log_desc_len"]=np.log1p(d.desc_len); S["rating"]=d.company_rating; S["log_reviews"]=np.log1p(d.company_reviews)
    return S
Sobs=struct(d,d.sal_period.where(d.sal_period.isin(["hour","year","month","week","day"])))
def ols_design(S):
    Z=pd.get_dummies(S,columns=["occ","county","city","job_type","period"],dtype=float)
    for c in ["yrs_min","rating"]: Z[c+"_na"]=Z[c].isna().astype(float); Z[c]=Z[c].fillna(Z[c].median() if Z[c].notna().any() else 0)
    Z["log_reviews"]=Z.log_reviews.fillna(0); return Z
Zols=ols_design(Sobs)
LGB=dict(n_estimators=500,learning_rate=0.05,num_leaves=63,min_child_samples=40,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,reg_lambda=2,random_state=SEED,n_jobs=8,verbose=-1)
RALPHA=2.0
def ridge_fit(idx,y): return Ridge(alpha=RALPHA,solver="sparse_cg",tol=1e-3,max_iter=200).fit(Xtext[idx],y)
def ridge_oof(idx,y,k=4):
    o=np.zeros(len(idx))
    for a,b in GroupKFold(n_splits=k,shuffle=True,random_state=SEED).split(idx,groups=d.grp.values[idx]):
        o[b]=ridge_fit(idx[a],y[a]).predict(Xtext[idx[b]])
    return o
def fit_predict(tr,te,ytr_col="y",Ste=None,restrict=None):
    """returns dict of predictions for te rows. tr,te index arrays."""
    ytr=d[ytr_col].values[tr]
    rm=ridge_fit(tr,ytr); r_te=rm.predict(Xtext[te]); r_tr=ridge_oof(tr,ytr)
    S_tr=Sobs.iloc[tr].copy(); S_te=(Sobs.iloc[te] if Ste is None else Ste).copy()
    out={"ridge_text":r_te}
    m0=lgb.LGBMRegressor(**LGB).fit(S_tr,ytr); out["lgbm_structured"]=m0.predict(S_te)
    S_tr["ridge"]=r_tr; S_te["ridge"]=r_te
    m1=lgb.LGBMRegressor(**LGB).fit(S_tr,ytr); out["lgbm_text_stack"]=m1.predict(S_te)
    return out,rm,m1
if __name__=="__main__":
    tr_all=np.where(d.train_ok)[0]; y=d.y.values
    folds=list(GroupKFold(n_splits=5,shuffle=True,random_state=SEED).split(tr_all,groups=d.grp.values[tr_all]))
    P={k:np.full(len(d),np.nan) for k in ["global_median","occ_median","ols_structured","ridge_text","lgbm_structured","lgbm_text_stack","lgbm_sep_period","lgbm_ptadj_target"]}
    fold_of=np.full(len(d),-1)
    import pickle,os
    PK=f'{CACHE}/m2_cv.pkl'
    if os.path.exists(PK): P,fold_of=pickle.load(open(PK,'rb')); folds=[]
    for k,(a,b) in enumerate(folds):
        tr,te=tr_all[a],tr_all[b]; fold_of[te]=k
        P["global_median"][te]=np.median(y[tr])
        med=pd.Series(y[tr]).groupby(d.occ_c.values[tr]).median(); P["occ_median"][te]=d.occ_c.iloc[te].map(med).fillna(np.median(y[tr])).values
        P["ols_structured"][te]=LinearRegression().fit(Zols.iloc[tr],y[tr]).predict(Zols.iloc[te])
        o,_,_=fit_predict(tr,te)
        for kk,v in o.items(): P[kk][te]=v
        # robustness: separate models by pay period (text-stack), and part-time-adjusted target
        for per in [True,False]:
            trp=tr[d.ishour.values[tr]==per]; tep=te[d.ishour.values[te]==per]
            if len(tep)==0: continue
            o2,_,_=fit_predict(trp,tep); P["lgbm_sep_period"][tep]=o2["lgbm_text_stack"]
        o3,_,_=fit_predict(tr,te,ytr_col="y_pt"); P["lgbm_ptadj_target"][te]=o3["lgbm_text_stack"]+0   # on y_pt scale
        print("fold",k,time.time()-t0,flush=True)
    if not os.path.exists(PK): pickle.dump((P,fold_of),open(PK,'wb'))
    T=np.where(fold_of>=0)[0]
    # ---- metrics (log points & dollars), all CA and Bay
    rows=[]
    for scope,mask in [("CA_all",np.ones(len(T),bool)),("Bay",d.bay.values[T])]:
        for k,v in P.items():
            tgt=d.y_pt.values if k=="lgbm_ptadj_target" else y
            yt=tgt[T][mask]; yp=v[T][mask]
            rows.append(dict(model="M2_salary",name=k,split=f"company_5fold_oof|{scope}",n_test=int(mask.sum()),rmse_log=rmse(yt,yp),mae_log=mae(yt,yp),
              rmse_usd=rmse(np.exp(yt),np.exp(yp)),mae_usd=mae(np.exp(yt),np.exp(yp)),
              r2=1-np.sum((yt-yp)**2)/np.sum((yt-yt.mean())**2),bias_log=float(np.mean(yp-yt))))
    M2=pd.DataFrame(rows); print(M2.to_string()); M2.to_csv(f"{BASE}/model_m2_metrics_tmp.csv",index=False)
    # ---- subgroup errors
    d["pred"]=P["lgbm_text_stack"]; d["res"]=d.pred-d.y; d["fold"]=fold_of
    sg=[]
    def add(scope,variant,res,mask,stype,series):
        gv=series.values[T][mask]; ra=res[T][mask]
        for g in pd.unique(gv):
            if pd.isna(g): continue
            r=ra[gv==g]
            if len(r)<15: continue
            sg.append(dict(scope=scope,variant=variant,subgroup_type=stype,subgroup=str(g),n=len(r),rmse_log=float(np.sqrt(np.mean(r**2))),mae_log=float(np.mean(np.abs(r))),
                bias_log=float(r.mean()),bias_pct=float(np.exp(r.mean())-1),se_bias=float(r.std(ddof=1)/np.sqrt(len(r))),share_overpredicted=float((r>0).mean())))
    d["g3"]=d.occ_c.map(grp3); d["seniority"]=np.where(d.senior,"senior",np.where(d.junior,"junior","mid_unlabelled"))
    d["emp"]=np.where(d.contract,"contract",np.where(d.parttime,"parttime",np.where(d.fulltime,"fulltime","unspecified")))
    d["period_g"]=d.sal_period.fillna("NA"); d["pt_g"]=np.where(d.parttime,"parttime","not_parttime")
    d["period_x_class_ft"]=d.period_g
    variants={"lgbm_text_stack":(P["lgbm_text_stack"]-y),"lgbm_structured":(P["lgbm_structured"]-y),"occ_median":(P["occ_median"]-y),
              "ols_structured":(P["ols_structured"]-y),"lgbm_sep_period":(P["lgbm_sep_period"]-y),"lgbm_ptadj_target":(P["lgbm_ptadj_target"]-d.y_pt.values)}
    for scope,mask in [("Bay",d.bay.values[T]),("CA_all",np.ones(len(T),bool))]:
        for v,res in variants.items():
            for st,col in [("occ_class","occ_c"),("county","county"),("group3","g3"),("seniority","seniority"),("employment","emp"),("pay_period","period_g"),("parttime","pt_g"),("seeded","seeded")]:
                if st=="county" and scope=="CA_all": continue
                add(scope,v,res,mask,st,d[col])
            # period x class (pay-period artifact check)
            add(scope,v,res,mask,"period_x_group3",d.period_g+"|"+d.g3)
    SG=pd.DataFrame(sg); SG.to_csv(f"{BASE}/model_subgroup_errors.csv",index=False)
    # ---- conformal intervals (cross-conformal by group3-class cells)
    d["cell"]=d.occ_c
    res=d.res.values; lo=np.full(len(d),np.nan); hi=np.full(len(d),np.nan)
    def qs(mask_idx,cell):
        r=res[mask_idx]; rc=r[d.cell.values[mask_idx]==cell]
        if len(rc)<200: rc=r
        return np.quantile(rc,0.10),np.quantile(rc,0.90)
    for k in range(5):
        te=T[fold_of[T]==k]; cal=T[fold_of[T]!=k]
        for c in d.cell.iloc[te].unique():
            q10,q90=qs(cal,c); m=te[d.cell.values[te]==c]; lo[m]=d.pred.values[m]-q90; hi[m]=d.pred.values[m]-q10
    cov=((y[T]>=lo[T])&(y[T]<=hi[T])); d["cov"]=np.nan; d.loc[T,"cov"]=cov.astype(float)
    cv=d.loc[T].groupby("g3")["cov"].agg(["mean","size"]); print("80% interval coverage overall",cov.mean(),"\n",cv)
    cv.to_csv(f"{BASE}/model_salary_interval_coverage.csv"); d.loc[T].groupby("occ_c")["cov"].mean().to_csv(f"{BASE}/model_salary_interval_coverage_by_class.csv")
    # ---- failures
    rm=ridge_fit(tr_all,y[tr_all]); vocab=np.concatenate([pd.read_csv(f"{CACHE}/desc_vocab.csv").iloc[:,0].astype(str).values,("T:"+pd.read_csv(f"{CACHE}/title_vocab.csv").iloc[:,0].astype(str)).values])
    def drivers(i):
        row=Xtext[i]; c=row.data*rm.coef_[row.indices]; o=np.argsort(-np.abs(c))[:6]; return "; ".join(f"{vocab[row.indices[j]]}({c[j]:+.2f})" for j in o)
    tt=d.loc[T].copy(); tt["resid"]=tt.res; fl=[]
    for nm,sub in [("over",tt.nlargest(8,"res")),("under",tt.nsmallest(8,"res"))]:
        for i,r in sub.iterrows():
            fl.append(dict(kind=nm+"-prediction",jobid=r.jobid,title=r.title,company=r.company,occ=r.occ_c,sal_period=r.sal_period,sal_lo=r.sal_lo,sal_hi=r.sal_hi,actual=round(np.exp(r.y)),predicted=round(np.exp(r.pred)),
              log_resid=round(r.res,2),features=f"parttime={r.parttime} contract={r.contract} junior={r.junior} senior={r.senior} county={r.county}",text_drivers=drivers(i)))
    pd.DataFrame(fl).to_csv(f"{BASE}/model_salary_failures.csv",index=False); print(pd.DataFrame(fl)[["kind","title","company","occ","sal_period","sal_lo","sal_hi","actual","predicted"]].to_string())
    # ---- period classifier for non-disclosers + final fit + imputation
    pc_oof=np.full(len(d),np.nan); ph=d.ishour.values.astype(int)
    Xp=sp.hstack([Xtext,sp.csr_matrix(Zols.drop(columns=[c for c in Zols.columns if c.startswith('period_')]).fillna(0).values.astype(np.float32))]).tocsr()
    for a,b in GroupKFold(n_splits=5,shuffle=True,random_state=SEED).split(tr_all,groups=d.grp.values[tr_all]):
        pc_oof[tr_all[b]]=LogisticRegression(C=2,max_iter=300).fit(Xp[tr_all[a]],ph[tr_all[a]]).predict_proba(Xp[tr_all[b]])[:,1]
    auc=roc_auc_score(ph[tr_all],pc_oof[tr_all]); print("pay-period (hourly vs other) classifier AUC",auc)
    pcm=LogisticRegression(C=2,max_iter=300).fit(Xp[tr_all],ph[tr_all])
    non=np.where(~d.has_salary.values)[0]; p_non=pcm.predict_proba(Xp[non])[:,1]
    per_non=np.where(p_non>=0.5,"hour","year")
    Sn=Sobs.iloc[non].copy(); Sn["period"]=pd.Categorical(per_non,categories=["hour","year","month","week","day"])
    o,_,_=fit_predict(tr_all,non,Ste=Sn); pn=o["lgbm_text_stack"]
    # intervals for imputed: residual quantiles from all OOF by cell
    allres=res[T]; pred_lo=np.zeros(len(non)); pred_hi=np.zeros(len(non))
    for j,i in enumerate(non):
        c=d.cell.iloc[i]; rc=res[T][d.cell.values[T]==c]; rc=rc if len(rc)>=200 else allres
        pred_lo[j]=pn[j]-np.quantile(rc,0.9); pred_hi[j]=pn[j]-np.quantile(rc,0.1)
    ex=da.values[non]   # DataAnnotation / AI_DATA_WORK: not imputed
    out=pd.DataFrame(dict(jobid=d.jobid,bay=d.bay,county=d.county,city=d.city,occ_consensus=d.occ_c,seeded=d.seeded,has_salary=d.has_salary,sal_period=d.sal_period,parttime=d.parttime,
        sal_mid=d.sal_mid,train_ok=d.train_ok,oof_fold=fold_of,pred_log=np.nan,pred_usd_annualised=np.nan,pi80_lo_usd=np.nan,pi80_hi_usd=np.nan,period_used=None,p_hourly=np.nan,imputed=False,not_imputed_flag=False))
    out.loc[T,"pred_log"]=d.pred.values[T]; out.loc[T,"pi80_lo_usd"]=np.exp(lo[T]); out.loc[T,"pi80_hi_usd"]=np.exp(hi[T]); out.loc[T,"period_used"]=d.sal_period.values[T]
    out.loc[non,"pred_log"]=pn; out.loc[non,"pi80_lo_usd"]=np.exp(pred_lo); out.loc[non,"pi80_hi_usd"]=np.exp(pred_hi); out.loc[non,"period_used"]=per_non; out.loc[non,"p_hourly"]=p_non; out.loc[non,"imputed"]=True
    out.loc[non[ex],["pred_log","pi80_lo_usd","pi80_hi_usd"]]=np.nan; out.loc[non[ex],"imputed"]=False; out.loc[non[ex],"not_imputed_flag"]=True
    out["pred_usd_annualised"]=np.exp(out.pred_log); out["pred_hourly_equiv"]=out.pred_usd_annualised/2080
    out.to_csv(f"{BASE}/model_salary_predictions.csv",index=False)
    d.drop(columns=["text","text_c"]).to_pickle(f"{CACHE}/m2_d.pkl"); print("done",time.time()-t0)
