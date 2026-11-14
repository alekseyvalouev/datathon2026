import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, pandas as pd, numpy as np
pd.set_option('display.width',250)
P=sys.argv[1]
c=pd.read_csv(P+'/comments.csv',low_memory=False); c=c[(c.is_staff!=1)&(c.channel=='spoken')].copy(); c['date']=pd.to_datetime(c.meeting_date); c['year']=c.date.dt.year
it=pd.read_csv(P+'/items.csv.gz',low_memory=False,usecols=['item_id','section_group','housing_kw']); c=c.merge(it,on='item_id',how='left')
st=c[c.position_source=='stenographer']; print('stenographer-marked spoken comments, support share of support+oppose, by year:')
x=st[st.position.isin(['support','oppose'])&st.year.between(2005,2025)]; print(x.groupby('year').position.agg(n='size',support=lambda s:(s=='support').mean()).round(3).T.to_string())
c['signed']=c.position_source=='stenographer'; print('share of spoken comments carrying a secretary mark by year:',c[c.year.between(2014,2025)].groupby('year').signed.mean().round(2).to_dict())
c['ym']=c.date.dt.to_period('Q'); q=c[c.date>='2018-01-01'].groupby('ym').agg(comments=('comment_id','size'),meetings=('meeting_date','nunique'),anon=('is_anonymous','mean'),single=('name_single','mean')).assign(per_meeting=lambda t:(t.comments/t.meetings).round(1)); print(q.round(3).to_string())
n=c.commenter_id.map(c.commenter_id.value_counts()); c['first_time']=c.groupby('commenter_id').date.transform('min')==c.date
for lab,a,b in [('2017-01..2020-02 (in person)','2017-01-01','2020-02-29'),('2020-04..2021-12','2020-04-01','2021-12-31'),('2022','2022-01-01','2022-12-31'),('2023','2023-01-01','2023-12-31'),('2024-01..2026-03','2024-01-01','2026-03-31')]:
    d=c[(c.date>=a)&(c.date<=b)]; so=d[d.position.isin(['support','oppose'])&(d.position_source=='stenographer')]
    print(f'{lab:30s} meetings {d.meeting_date.nunique():3d} | spoken comments/meeting {len(d)/d.meeting_date.nunique():5.1f} | no usable name {100*d.commenter_id.isna().mean():4.1f}% | first-ever appearance {100*d[d.commenter_id.notna()].first_time.mean():4.1f}% | support {100*(so.position=="support").mean():4.1f}% | general public comment share {100*d.section_group.isin(["General Public Comment","Public Comment"]).mean():4.1f}%')
