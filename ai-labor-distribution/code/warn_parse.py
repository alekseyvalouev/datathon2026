import pdfplumber, pandas as pd, numpy as np, re, html, warnings, sys
warnings.simplefilter('ignore')
S='/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad'
E_=S+'/ext/'; B=S+'/base/'
DRE=re.compile(r'^\d\d/\d\d/\d{4}$')
PDFS=[('warn_7-1-2023-to-06-30-2024.pdf'),('warn_fy2425.pdf'),('warn_7-1-25-to-6-30-26.pdf')]

def norm(s):
    if not isinstance(s,str): return ''
    s=html.unescape(s).lower()
    s=re.sub(r'\bd/?b/?a\b.*$','',s) if False else s   # keep dba text: do not truncate
    s=re.sub(r'\b(incorporated|inc|llc|llp|lp|corporation|corp|company|co|ltd|limited|group|holdings|the)\b',' ',s)
    return re.sub(r'[^a-z0-9]','',s)

def parse_pdf(f):
    rows=[];skipped=[]
    with pdfplumber.open(E_+f) as pdf:
        for pi,p in enumerate(pdf.pages):
            for t in p.extract_tables():
                for r in t:
                    r=[(c or '').replace('\n',' ').strip() for c in r]
                    if len(r)==8 and DRE.match(r[0]) and DRE.match(r[1]) and DRE.match(r[2]):
                        rows.append(dict(notice_date=r[0],received_date=r[1],effective_date=r[2],company=r[3],county=r[4],emp=r[5],ltype=r[6],address=r[7],source_file=f,page=pi+1))
                    elif any(r): skipped.append((pi+1,r))
    return pd.DataFrame(rows),skipped

dfs=[];allskip={}
for f in PDFS:
    d,sk=parse_pdf(f); dfs.append(d); allskip[f]=sk
pdf_df=pd.concat(dfs,ignore_index=True)

# xlsx
x=pd.read_excel(E_+'warn_report1.xlsx',sheet_name='Detailed WARN Report ',header=1)
x.columns=['county','notice_date','received_date','effective_date','company','ltype','emp','address','industry']
x['source_file']='warn_report1.xlsx'
for c in ['notice_date','received_date','effective_date']: x[c]=pd.to_datetime(x[c]).dt.strftime('%m/%d/%Y')
x['emp']=x['emp'].astype(str)
cc=pd.read_excel(E_+'warn_report1.xlsx',sheet_name='Call Center Relocations Report',header=1)
cc.columns=['county','notice_date','received_date','effective_date','company','ltype','emp','address']
cc['source_file']='warn_report1.xlsx'

df=pd.concat([pdf_df,x],ignore_index=True)
for c in ['notice_date','received_date','effective_date']: df[c]=pd.to_datetime(df[c],format='%m/%d/%Y',errors='coerce')
for c in ['company','county','address','ltype']: df[c]=df[c].astype(str).map(lambda s: html.unescape(re.sub(r'\s+',' ',s)).strip())
df['county']=df['county'].str.replace(r'\s*County$','',regex=True).str.strip()
df['employees']=pd.to_numeric(df['emp'].str.replace(',',''),errors='coerce').astype('Int64')
def lt(s):
    s=s.lower()
    kind='Closure' if s.startswith('closure') else 'Layoff' if s.startswith('layoff') else 'Unknown'
    dur='Permanent' if 'permanent' in s else 'Temporary' if 'temporary' in s else 'Not Identified' if ('not' in s) else 'Unknown'
    return kind,dur
df['kind']=df.ltype.map(lambda s: lt(s)[0]); df['duration']=df.ltype.map(lambda s: lt(s)[1])
df['layoff_type']=np.where(df.kind=='Unknown',df.ltype,df.duration.where(df.duration=='Not Identified',df.duration+' '+df.kind).where(df.duration!='Not Identified',('Not Identified '+df.kind)))
df['company_norm']=df.company.map(norm)

# ---- city via zip->city map learned from double-space-delimited addresses (xlsx + pypdf text lines)
import pypdf, collections
pairs=[]
for a in x.address.astype(str):
    m=re.match(r'^.*\S\s{2,}(.+?)\s+CA\s+(\d{5})',a)
    if m: pairs.append((m.group(2),m.group(1).strip()))
for f in PDFS:
    for pg in pypdf.PdfReader(E_+f).pages:
        for l in pg.extract_text().split('\n'):
            if re.match(r'^\d\d/\d\d/\d{4} ',l):
                m=re.match(r'^.*\S\s{2,}(.+?)\s+CA\s+(\d{5})',l)
                if m: pairs.append((m.group(2),m.group(1).strip()))
zc=collections.defaultdict(collections.Counter)
for z,c in pairs: zc[z][c.title()]+=1
zmap={z:c.most_common(1)[0][0] for z,c in zc.items()}
df['zip']=df.address.str.extract(r'\bCA\s*(\d{5})')[0]
df['city']=df.zip.map(zmap)
df['industry']=df.get('industry')
# fiscal year by received (processed) date, July-June
def fy(d):
    if pd.isna(d): return None
    y=d.year if d.month>=7 else d.year-1
    return f'FY{y}-{str(y+1)[2:]}'
df['fiscal_year']=df.received_date.map(fy)
df['quarter']=df.received_date.dt.to_period('Q').astype(str)
df['county_fips_name']=df.county
out=df[['notice_date','effective_date','received_date','company','company_norm','city','county','address','zip','employees','layoff_type','kind','duration','industry','fiscal_year','quarter','source_file','page']]
out.to_parquet(B+'warn_ca.parquet',index=False); out.to_csv(B+'warn_ca.csv',index=False)
# call centers
cc['company']=cc.company.astype(str).map(html.unescape); cc['county']=cc.county.str.replace(r'\s*County$','',regex=True)
cc['employees']=pd.to_numeric(cc.emp,errors='coerce')
cc['company_norm']=cc.company.map(norm)
cc['fiscal_year']=pd.to_datetime(cc.received_date).map(fy)
cc.drop(columns=['emp']).to_csv(B+'warn_call_centers.csv',index=False)
# ---- validation
print('rows',len(out))
print(out.groupby('fiscal_year').agg(notices=('company','size'),employees=('employees','sum'),min_recv=('received_date','min'),max_recv=('received_date','max')))
print(out.groupby('source_file').agg(notices=('company','size'),employees=('employees','sum')))
for f,sk in allskip.items():
    print(f,'non-row table rows skipped:',len(sk)); print(sk[:5])
print('usable county',out.county.isin(['Alameda','Contra Costa','Marin','Napa','San Francisco','San Mateo','Santa Clara','Solano','Sonoma']).sum(), out.county.nunique(), 'null emp',out.employees.isna().sum(),'zero/neg',(out.employees<=0).sum())
print(sorted(out.county.unique()))
print(out.layoff_type.value_counts())
print('city null',out.city.isna().mean())
