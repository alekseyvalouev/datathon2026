import sys,re,pandas as pd
S=sys.argv[1]; sys.path.insert(0,S+'/code')
from voice_gd_text import *
ca=pd.read_pickle(S+'/base/_gd_ca_text.pkl')
ca=ca[ca.review_cons.notna()]
pat={'LAYOFF':LAYOFF,'WORKLOAD':WORKLOAD_ANY,'OFFD':OFFSHORE_DISPLACE,'STAFF':STAFFING}
k=sys.argv[2]; seed=int(sys.argv[3]); n=int(sys.argv[4])
m=ca[ca.review_cons.str.contains(pat[k])]
print(k,'matches',len(m),'of',len(ca))
for i,(j,r) in enumerate(m.sample(n,random_state=seed).iterrows()):
    mm=pat[k].search(r.review_cons); a=mm.start()
    print(f'[{i}]',r.occ_class[:8],'|',r.review_cons[max(0,a-100):a+120].replace('\n',' '))
