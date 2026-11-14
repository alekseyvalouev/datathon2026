import csv, pandas as pd
csv.field_size_limit(10**9)
SCR="/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad"
SRC="/Users/alekseyvalouev/Desktop/Datathon/indeed_job_listings-002.csv"
ids=set(pd.read_parquet(f"{SCR}/base/indeed_base_v3.parquet",columns=["jobid"]).jobid)
rows=[]
with open(SRC,newline="",encoding="utf-8") as f:
    r=csv.DictReader(f)
    for d in r:
        if d["jobid"] in ids:
            rows.append((d["jobid"],(d["description_text"] or "")[:6000]))
            ids.discard(d["jobid"])
df=pd.DataFrame(rows,columns=["jobid","text"])
print(len(df),"missing",len(ids), "median len",df.text.str.len().median())
df.to_parquet(f"{SCR}/base/model_text.parquet")
