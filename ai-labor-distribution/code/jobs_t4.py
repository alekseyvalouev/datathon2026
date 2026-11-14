import sys,re;sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
from jobs_lib import *
pd.set_option('display.width',250);pd.set_option('display.max_columns',40);pd.set_option('display.max_rows',300)
src=open('build_indeed_v2.py').read().split('\n')[88:112]
exec('\n'.join(src))
d=load();a=d[d.occ=='AI_DATA_WORK'];ab=a[a.bay];prod=d[d.occ=='AI_PRODUCER'];fl=d[d.occ=='FRONTLINE_SERVICE']
def prof(x,tag):
    s=x[x.sal_ok];h=x[x.hourly]
    return dict(group=tag,n=len(x),n_companies=x.company_norm.nunique(),top_company_share=x.company_norm.value_counts(normalize=True).iloc[0],n_sal=len(s),n_hourly=len(h),share_hourly_posted=len(h)/max(len(s),1),
      med_hourly_rate=h.rate.median(),p25_rate=q(h.rate,.25),p75_rate=q(h.rate,.75),med_annualized_2080=s.sal_mid.median(),n_annual_posted=int((s.sal_period=='year').sum()),med_annual_posted=s[s.sal_period=='year'].sal_mid.median(),
      contract=x.contract.mean(),parttime=x.parttime.mean(),fulltime=x.fulltime.mean(),remote=x.remote.mean(),hybrid=x.hybrid.mean(),deg_ba=x.deg_ba.mean(),deg_grad=x.deg_grad.mean(),no_deg=x.no_deg.mean(),yrs_med=x.yrs_min.median(),yrs_known=x.yrs_min.notna().mean(),ai_strict=x.ai_strict.mean(),
      width_med=s.width.median(),pt_share_hourly=h.parttime.mean())
rows=[prof(ab,'AI_DATA_WORK_Bay'),prof(a,'AI_DATA_WORK_CA'),prof(ab[ab.company_norm=='dataannotation'],'AI_DATA_WORK_Bay_DataAnnotation'),prof(ab[ab.company_norm!='dataannotation'],'AI_DATA_WORK_Bay_nonDA'),
      prof(prod[prod.bay],'AI_PRODUCER_Bay'),prof(prod,'AI_PRODUCER_CA'),prof(fl[fl.bay],'FRONTLINE_Bay'),prof(fl,'FRONTLINE_CA')]
P=pd.DataFrame(rows);print(P.T.to_string())
print('Bay top employers',ab.company.value_counts().head(10).to_dict());print('CA top',a.company.value_counts().head(8).to_dict())
print('Bay city',ab.city.value_counts().head(12).to_dict());print('county',ab.county.value_counts().to_dict())
print('job_location sample',ab.job_location.value_counts().head(8).to_dict())
print('Bay remote by job_location contains Remote',ab.job_location.str.contains('remote',case=False).mean())
print('annual-posted AI_DATA_WORK Bay');print(ab[ab.sal_period=='year'][['title','company','sal_lo','sal_hi','contract','parttime','remote']])
print(a[a.sal_period=='year'][['title','company','sal_lo','sal_hi','bay']])
# DataAnnotation distinct title count / identical ranges
da=ab[ab.company_norm=='dataannotation'];print('DA bay',len(da),'unique titles',da.title.nunique(),'range counts',da.groupby(['sal_lo','sal_hi']).size().sort_values(ascending=False).head(6).to_dict())
# non-DA Bay
print(ab[ab.company_norm!='dataannotation'][['title','company','sal_lo','sal_hi','sal_period','contract','remote']])
# former-occupation parse: all CA DataAnnotation (and 'AI Trainer' titled) postings
t=a[a.title.str.contains(r'\s[-–]\s*AI Trainer',case=False)].copy()
t['prefix']=t.title.str.replace(r'\s*[-–]\s*AI Trainer.*','',regex=True).str.strip()
t['prefix_cls']=t.prefix.map(occ_class)
print(len(t),t.bay.sum())
print(t.prefix_cls.value_counts())
oth=t[t.prefix_cls=='OTHER'].prefix.value_counts();print(oth.to_string())
t.to_pickle(B+'jobs_aitrainer_prefix.pkl')
P.to_csv(B+'jobs_aidatawork.csv',index=False)
