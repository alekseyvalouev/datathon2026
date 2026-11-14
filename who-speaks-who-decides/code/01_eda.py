import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, pandas as pd, numpy as np
pd.set_option('display.width',220); pd.set_option('display.max_columns',100); pd.set_option('display.max_colwidth',110)
P=sys.argv[1]
c=pd.read_csv(P+'/comments.csv',low_memory=False); it=pd.read_csv(P+'/items.csv.gz',low_memory=False)
print(c.shape, list(c.columns)); print(it.shape, list(it.columns))
print(pd.crosstab([c.channel,c.position_source.fillna('NA')],c.position.fillna('NA'),margins=True))
c['year']=pd.to_datetime(c.meeting_date,errors='coerce').dt.year
print(c.groupby('year').agg(n=('comment_id','size'),signed=('position_source',lambda s:(s=='stenographer').sum())).T.to_string())
for ch in ['spoken','email']:
    t=c[c.channel==ch].text.dropna().astype(str); L=t.str.split().str.len()
    print(ch,'has text',len(t),'/',(c.channel==ch).sum(),'words q10/50/90/99',L.quantile([.1,.5,.9,.99]).tolist())
s=c[(c.position_source=='stenographer')&c.text.notna()]
print('stenographer w/ text',len(s), s.position.value_counts(normalize=True).round(3).to_dict())
for p in (['support','oppose','neutral'] if SHOW else []):
    print('---',p); print(s[s.position==p].text.sample(8,random_state=1).str[:160].to_string(index=False))
if SHOW: print('--- email sample'); print(c[c.channel=='email'].text.dropna().sample(3,random_state=2).str[:300].to_string(index=False))
e=c[c.channel=='email']; print('emails campaign share',e.is_campaign.mean(), 'unique texts',e.text.nunique(), 'years',e.year.min(),e.year.max())
print('\nITEMS'); print(it.section_group.value_counts().head(12))
print(it.action_final.value_counts(dropna=False)); print(it.rec_final.value_counts(dropna=False))
h=it[it.housing_kw==1]; print('housing items',len(h)); print(h.action_final.value_counts(dropna=False))
print('coords',it.latitude.notna().sum(),'record_type top',it.record_type.value_counts().head(10).to_dict())
n=c.groupby('item_id').size(); it['n_comments']=it.item_id.map(n).fillna(0)
print('items with >=1 comment',(it.n_comments>0).sum(),' >=5',(it.n_comments>=5).sum())
w=it[(it.n_comments>0)&it.action_final.notna()]; print('commented items w/ action',len(w)); print(w.action_final.value_counts(normalize=True).round(3))
print(pd.crosstab(w.rec_final.fillna('NA'),w.action_final))
