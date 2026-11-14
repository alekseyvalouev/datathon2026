import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys,re,pandas as pd
pd.set_option('display.width',250)
P,PJ=sys.argv[1:3]
it=pd.read_csv(P+'/items.csv.gz',low_memory=False); it['date']=pd.to_datetime(it.meeting_date)
for pid,n in [('2016-005252',1),('2017-001225DRP',1),('2014.1459',1),('2015-009955',2),('2014-002033',3),('2014.0376',2),('2014-002849',1),('2013.1037',1),('2020-006544',1),('2016-006860',1)]:
    q=it[it.id_parent==pid].sort_values('date'); t=re.sub(r'\s+',' ',q.item_text.iloc[q.item_text.str.len().argmax()])
    m=re.search(r'(Request.*)',t); print('\n##',pid,'|',(m.group(1) if m else t)[150:800])
    for a in q[q.ACTION.notna()].ACTION.tail(n): print('   ACT:',re.sub(r'\s+',' ',a)[:600])
