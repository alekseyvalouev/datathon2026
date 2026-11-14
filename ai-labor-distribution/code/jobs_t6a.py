import sys;sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
from jobs_lib import *
import csv,re,json
csv.field_size_limit(10**9)
AI_HIRING = re.compile(r'\b((use|uses|using|subject to|includes?) (of )?ai[^.]{0,60}(screen|candidate|applicant|recruit|resume|hiring|interview)|ai (screening|recruiting|candidate|applicant|resume|interview)|automated (screening|decision)[^.]{0,40}(candidate|applicant))', re.I)
d=load();ids=set(d[d.ai_hiring].jobid)
out={}
for row in csv.DictReader(open('/Users/alekseyvalouev/Desktop/Datathon/indeed_job_listings-002.csv')):
    j=row['jobid']
    if j in ids and j not in out:
        t=row.get('description_text') or row.get('description') or ''
        m=AI_HIRING.search(t)
        if m: out[j]=t[max(0,m.start()-250):m.end()+250].replace('\n',' ')
json.dump(out,open(B+'jobs_aihiring_snips.json','w'))
print(len(ids),len(out))
