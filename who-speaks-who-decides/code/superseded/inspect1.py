import os
WORK=os.environ.get('WORK_DIR','work'); SHOW=os.environ.get('SHOW_TEXT')  # SHOW_TEXT=1 prints raw comment samples (may contain names; do not commit that output)
import sys, glob, pandas as pd
pd.set_option('display.width',250); pd.set_option('display.max_columns',200); pd.set_option('display.max_colwidth',60)
D=os.environ.get('RAW_DIR','data')
def head(p, n=None):
    df = pd.read_csv(p, nrows=n, low_memory=False)
    print('\n#####', p.split('/')[-1], df.shape); print(list(df.columns)); return df
r = head(glob.glob(D+'/z3/*/*.csv')[0])
print(r['community_name'].value_counts().head(30) if 'community_name' in r else '')
for c in r.columns:
    if 'date' in c.lower(): print(c, r[c].min(), r[c].max())
print(r.notna().mean().round(2).to_dict())
i = head(glob.glob(D+'/z2/*/*.csv')[0])
print(i.notna().mean().round(2).to_dict())
for c in ['location','job_type']:
    if c in i: print(i[c].value_counts().head(8))
for c in i.columns:
    if 'date' in c.lower(): print(c, i[c].min(), i[c].max())
g = head(D+'/z5/glassdoor reviews dataset/glassdoor_reviews.csv', 2000)
z = head(D+'/z10/zillow housing dataset/Zillow_part1.csv', 500)
m = head(D+'/z8/google maps dataset/google_maps.csv', 500)
v = head(D+'/z9/google maps reviews dataset/google_maps_reviews.csv', 500)
