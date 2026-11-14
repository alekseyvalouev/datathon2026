"""Shared helpers for EXPERIMENT M (model_*). Seeds fixed everywhere (SEED=42)."""
import os, re, numpy as np, pandas as pd, scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
SCR="/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad"
BASE=f"{SCR}/base"; OUT=f"{SCR}/out"; CACHE=f"{BASE}/model_cache"; os.makedirs(CACHE,exist_ok=True)
SEED=42
EXPOSED=['CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED']
AIPOS=['AI_PRODUCER','AI_DATA_WORK','SOFTWARE_ENG','DATA_ENG_ANALYTICS']
FRONT=['FRONTLINE_SERVICE','SKILLED_TRADE','HEALTH_CLINICAL','EDUCATION']   # "frontline/in-person" group for subgroup audit
def grp3(o):
    return 'AI_POSITIONED' if o in AIPOS else 'EXPOSED' if o in EXPOSED else 'FRONTLINE' if o in FRONT else 'OTHER_GROUP'

_RX=[(re.compile(r'https?://\S+|www\.\S+|\S+@\S+'),' '),
     (re.compile(r'\$\s?\d[\d,]*(\.\d+)?\s*[kK]?'),' SALNUM '),               # dollar amounts -> scrub (salary leakage)
     (re.compile(r'\b\d[\d,]*(\.\d+)?\s*(k|K)\b'),' SALNUM '),
     (re.compile(r'\b\d{2,3},\d{3}\b'),' SALNUM '),
     (re.compile(r'\b\d+(\.\d+)?\s*(/|per|an|a)\s*(hr|hour|year|yr|annum)\b',re.I),' SALNUM ')]
def clean(t):
    t=t or ""
    for rx,r in _RX: t=rx.sub(r,t)
    return t.lower()

def load():
    b=pd.read_parquet(f"{BASE}/indeed_base_v3.parquet")
    t=pd.read_parquet(f"{BASE}/model_text.parquet")
    d=b.merge(t,on="jobid",how="left").reset_index(drop=True)
    d["grp"]=d.company_norm.fillna(d.jobid).replace("",np.nan).fillna(d.jobid)
    d["text_c"]=[clean(x) for x in d.text.fillna("")]
    d["title_c"]=d.title.fillna("").str.lower()
    return d

TOK=r"(?u)\b[a-zA-Z][a-zA-Z+#\-]{1,}\b"
def tfidf_desc(d,maxf=250000):
    p=f"{CACHE}/desc.npz"
    if os.path.exists(p): return sp.load_npz(p).tocsr()
    v=TfidfVectorizer(ngram_range=(1,2),min_df=8,max_df=0.4,max_features=maxf,sublinear_tf=True,dtype=np.float32,token_pattern=TOK,stop_words="english")
    X=v.fit_transform(d.text_c.str[:5000]); sp.save_npz(p,X); 
    pd.Series(v.get_feature_names_out()).to_csv(f"{CACHE}/desc_vocab.csv",index=False)
    return X.tocsr()
def tfidf_title(d):
    p=f"{CACHE}/title.npz"
    if os.path.exists(p): return sp.load_npz(p).tocsr()
    v=TfidfVectorizer(ngram_range=(1,2),min_df=3,sublinear_tf=True,dtype=np.float32,token_pattern=TOK)
    X=v.fit_transform(d.title_c); sp.save_npz(p,X)
    pd.Series(v.get_feature_names_out()).to_csv(f"{CACHE}/title_vocab.csv",index=False)
    return X.tocsr()
def rmse(a,b): return float(np.sqrt(np.mean((np.asarray(a)-np.asarray(b))**2)))
def mae(a,b): return float(np.mean(np.abs(np.asarray(a)-np.asarray(b))))
