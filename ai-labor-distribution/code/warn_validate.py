import pandas as pd, pdfplumber, re, random, pypdf
S='/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad'
df=pd.read_parquet(S+'/base/warn_ca.parquet')
df['m']=df.received_date.dt.strftime('%B %Y')
bad=0
for f,pg in [('warn_7-1-2023-to-06-30-2024.pdf',64),('warn_fy2425.pdf',53),('warn_7-1-25-to-6-30-26.pdf',21)]:
    with pdfplumber.open(S+'/ext/'+f) as pdf:
        t=[r for q in pdf.pages[-2:] for tb in q.extract_tables() for r in tb]
    sub=df[df.source_file==f]
    for r in [x for x in t if re.match(r'^([A-Z][a-z]+ 20\d\d|Total)$',x[0] or '')]:
        mo=r[0]; n=int(r[1].replace(',','')); e=int(r[2].replace(',',''))
        if mo=='Total': a=sub
        else: a=sub[sub.m==mo]
        ok=(len(a)==n and a.employees.sum()==e)
        if not ok: bad+=1
        print(f[:18],mo,n,e,'|',len(a),a.employees.sum(),'OK' if ok else '<<< MISMATCH')
print('mismatches',bad)
