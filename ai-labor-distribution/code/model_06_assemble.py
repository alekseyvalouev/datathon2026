import sys; sys.path.insert(0,"/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code")
import pandas as pd, numpy as np
from model_lib import *
pd.set_option("display.width",250)
m1=pd.read_csv(f"{BASE}/model_m1_metrics_tmp.csv"); m2=pd.read_csv(f"{BASE}/model_m2_metrics_tmp.csv"); m3=pd.read_csv(f"{BASE}/model_m3_metrics_tmp.csv")
rb=pd.read_csv(f"{BASE}/model_m2_robust_metrics.csv"); tm=pd.read_csv(f"{BASE}/model_opacity_text_masked_metrics.csv")
rows=[]
def L(model,name,split,metric,val,n=np.nan): rows.append(dict(model=model,name=name,split=split,metric=metric,value=val,n=n))
for _,r in m1.iterrows():
    for k in ["macro_f1","weighted_f1","accuracy"]: L("M1_occ_classifier",r["name"],r["split"],k,r[k],r.n_test)
L("M1_occ_classifier","desc_only_tfidf_svm","company_5fold_oof_all_labelled","macro_f1",0.7607923346488012,106934)
L("M1_occ_classifier","desc_only_tfidf_svm","company_5fold_oof_all_labelled","accuracy",0.830409411412647,106934)
v1=pd.read_csv(f"{BASE}/model_handcheck_other_verdicts.csv",index_col=0); v2=pd.read_csv(f"{BASE}/model_handcheck_other_verdicts2.csv",index_col=0); vo=pd.read_csv(f"{BASE}/model_handcheck_override_verdicts.csv",index_col=0); vd=pd.read_csv(f"{BASE}/model_handcheck_disagree_verdicts.csv",index_col=0)
elig=v1[(v1.pred!="MANAGEMENT")&(v1.p>=0.6)]
for nm,v,sp_ in [("hand_check_OTHER_all_predictions_no_rule",v1,"random n=110 Bay OTHER"),("hand_check_OTHER_rule_applied_fresh_sample",v2,"fresh n=45 Bay OTHER assigned by rule"),("hand_check_OTHER_rule_eligible_in_sample1",elig,"sample1 subset")]:
    L("M1_occ_classifier",nm,sp_,"hand_accuracy_strict",(v.verdict=="c").mean(),len(v)); L("M1_occ_classifier",nm,sp_,"hand_accuracy_lenient_incl_ambiguous",(v.verdict!="w").mean(),len(v))
L("M1_occ_classifier","hand_check_MANAGEMENT_predictions_on_OTHER","sample1 subset","hand_accuracy_strict",(v1[v1.pred=="MANAGEMENT"].verdict=="c").mean(),int((v1.pred=="MANAGEMENT").sum()))
r=vd[~vd.is_da]; L("M1_occ_classifier","disagreement_model_right_share_of_decided","n=52 non-DataAnnotation confident disagreements","share_model_right",(r.verdict=="M").sum()/((r.verdict=="M").sum()+(r.verdict=="R").sum()),len(r))
L("M1_occ_classifier","override_sample_regex_wrong","n=30 override-rule cases","share_regex_wrong_model_right",(vo.verdict=="M").mean(),len(vo)); L("M1_occ_classifier","override_sample_regex_right","n=30 override-rule cases","share_regex_right",(vo.verdict=="R").mean(),len(vo))
for _,r in m2.iterrows():
    for k in ["rmse_log","mae_log","rmse_usd","mae_usd","r2","bias_log"]: L("M2_salary",r["name"],r["split"],k,r[k],r.n_test)
for _,r in rb.iterrows():
    for k in ["medae_log","p90_abs_log","share_within_20pct"]: L("M2_salary",r["name"],f"company_5fold_oof|{r.scope}",k,r[k])
for _,r in m3.iterrows():
    for k in ["auc","avg_precision","precision_opaque","recall_opaque","f1_opaque","accuracy","base_rate_opaque"]: L("M3_opacity",r["name"],r["split"],k,r[k],r.n_test)
for _,r in tm.iterrows():
    for k in ["auc","avg_precision"]: L("M3_opacity","text_logit_pay_words_masked",f"company_5fold_oof|{r.scope}",k,r[k])
M=pd.DataFrame(rows); M.to_csv(f"{BASE}/model_metrics.csv",index=False); print(len(M))
# per-class M1
pc=pd.read_csv(f"{BASE}/model_occ_perclass.csv"); print(pc[pc.model=="desc_only_tfidf_svm"].round(3).to_string()); print(pc[pc.model=="title_plus_desc_tfidf_svm"].round(3)[["cls","precision","recall","f1","support"]].to_string())
cm=pd.read_csv(f"{BASE}/model_occ_confusion_desc_only_tfidf_svm.csv",index_col=0)
x=cm.stack().reset_index(); x.columns=["true","pred","n"]; x=x[x.true!=x.pred].sort_values("n",ascending=False).head(14); print(x.to_string())
