import sys;sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
from jobs_lib import *
import statsmodels.api as sm
pd.set_option('display.width',250);pd.set_option('display.max_columns',40)
p=pd.read_parquet(B+'glassdoor_ca.parquet')
R=['rating_overall','rating_compensation_benefits','rating_career_opportunities','rating_senior_leadership','rating_work_life']
for c in R: p[c]=p[c].where(p[c]>0)   # 0 -> missing (already NaN in parquet; zeros=0 confirmed)
gc=pd.read_csv(B+'glassdoor_company.csv')
def firm(x):
    a=x.groupby('company_norm')[R].mean();a['n_reviews']=x.groupby('company_norm').size();a['n_rated_comp']=x.groupby('company_norm').rating_compensation_benefits.count();return a
F_all=firm(p);F_bay=firm(p[p.bay_area==True])
# check shipped company means vs recomputed
chk=gc.set_index('company_norm').join(F_all,rsuffix='_re')
print('max abs diff mean_comp',(chk.mean_compensation_benefits-chk.rating_compensation_benefits).abs().max(),'overall',(chk.mean_overall-chk.rating_overall).abs().max())
w=pd.read_csv(B+'warn_ca.csv');BAY9=['Alameda','Contra Costa','Marin','Napa','San Francisco','San Mateo','Santa Clara','Solano','Sonoma']
wb=set(w[w.county.isin(BAY9)].company_norm);wa=set(w.company_norm)
d=load();postf=set(d[d.bay].company_norm.dropna())
print('WARN Bay firms',len(wb),'in glassdoor',len(wb&set(F_all.index)),'with >=10 reviews',len(wb&set(F_all[F_all.n_reviews>=10].index)),'| any-CA WARN',len(wa),len(wa&set(F_all.index)),len(wa&set(F_all[F_all.n_reviews>=10].index)))
print('Bay-WARN firms matched in Indeed postings',len(wb&postf),'of which in glassdoor>=10',len(wb&postf&set(F_all[F_all.n_reviews>=10].index)))
rows=[];out=[]
def run(F,flagset,label,minr=10):
    x=F[F.n_reviews>=minr].copy();x['warn']=x.index.isin(flagset).astype(float);x['lnr']=np.log(x.n_reviews)
    x['band']=pd.cut(x.n_reviews,[9,24,99,499,1e9],labels=['10-24','25-99','100-499','500+'])
    for r in R:
        y=x[r].dropna();xx=x.loc[y.index]
        a=xx[xx.warn==1][r];b=xx[xx.warn==0][r]
        X=sm.add_constant(xx[['warn','lnr']]);m=sm.OLS(xx[r],X).fit(cov_type='HC1')
        # band-adjusted: dummies
        X2=pd.concat([xx[['warn']],pd.get_dummies(xx.band,drop_first=True,dtype=float)],axis=1);X2=sm.add_constant(X2);m2=sm.OLS(xx[r],X2).fit(cov_type='HC1')
        rows.append(dict(sample=label,min_reviews=minr,rating=r,n_warn=len(a),n_nonwarn=len(b),mean_warn=a.mean(),mean_nonwarn=b.mean(),raw_diff=a.mean()-b.mean(),raw_se=np.sqrt(a.var()/len(a)+b.var()/len(b)),
          adj_lnreviews_diff=m.params['warn'],adj_lnreviews_se=m.bse['warn'],adj_band_diff=m2.params['warn'],adj_band_se=m2.bse['warn']))
        for bn,g in xx.groupby('band',observed=True):
            ga=g[g.warn==1][r];gb=g[g.warn==0][r]
            if len(ga)>=3: out.append(dict(sample=label,rating=r,band=bn,n_warn=len(ga),n_nonwarn=len(gb),mean_warn=ga.mean(),mean_nonwarn=gb.mean(),diff=ga.mean()-gb.mean()))
for lab,F,fs in [('allCA_reviews|BayCounty_WARN',F_all,wb),('allCA_reviews|anyCA_WARN',F_all,wa),('BayArea_reviews_only|BayCounty_WARN',F_bay,wb)]:
    run(F,fs,lab,10)
run(F_all,wb,'allCA_reviews|BayCounty_WARN',30)
A=pd.DataFrame(rows);Bd=pd.DataFrame(out)
A.to_csv(B+'jobs_warn_glassdoor.csv',index=False);Bd.to_csv(B+'jobs_warn_glassdoor_bands.csv',index=False)
print(A.round(3).to_string());print(Bd[Bd['sample']=='allCA_reviews|BayCounty_WARN'].round(3).to_string())
x=F_all[F_all.n_reviews>=10];print('median reviews warn vs non',x[x.index.isin(wb)].n_reviews.median(),x[~x.index.isin(wb)].n_reviews.median())
