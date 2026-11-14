import sys;sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
from jobs_lib import *
import statsmodels.api as sm
pd.set_option('display.width',250);pd.set_option('display.max_columns',60);pd.set_option('display.max_rows',300)
d=load();b=d[d.bay].copy();bu=b[~b.seeded]
CL=['AI_POSITIONED','EXPOSED','FRONTLINE_SERVICE']
# ---------- TEST 3
def ent(x,key,tag):
    r=[]
    for k,g in x.groupby(key):
        y=g.yrs_min.dropna();j=g[g.junior]
        r.append(dict(sample=tag,cls=k,n=len(g),entry_share=g.junior.mean(),intern_share=g.internship.mean(),ba_share=g.deg_ba.mean(),grad_share=g.deg_grad.mean(),nodeg_share=g.no_deg.mean(),
          yrs_known=len(y)/len(g),yrs_mean=y.mean(),yrs_med=y.median(),yrs_p25=y.quantile(.25),yrs_p75=y.quantile(.75),yrs_ge3=(y>=3).mean(),yrs_ge5=(y>=5).mean(),
          n_junior=len(j),jr_yrs_known=j.yrs_min.notna().mean(),jr_yrs_mean=j.yrs_min.mean(),jr_yrs_med=j.yrs_min.median(),jr_yrs_ge2=(j.yrs_min.dropna()>=2).mean(),jr_yrs_ge3=(j.yrs_min.dropna()>=3).mean(),jr_ba=j.deg_ba.mean(),jr_nodeg=j.no_deg.mean(),
          jr_ai_strict_share=j.ai_strict.mean(),
          jr_ai_yrs_mean=j[j.ai_strict].yrs_min.mean(),jr_noai_yrs_mean=j[~j.ai_strict].yrs_min.mean(),n_jr_ai=int(j.ai_strict.sum()),jr_ai_ba=j[j.ai_strict].deg_ba.mean(),jr_noai_ba=j[~j.ai_strict].deg_ba.mean(),
          jr_aiuse_yrs_mean=j[j.ai_use].yrs_min.mean(),n_jr_aiuse=int(j.ai_use.sum())))
    t=pd.DataFrame(r)
    t['share_of_all_postings']=t.n/len(x);t['share_of_all_entry']=t.n_junior/t.n_junior.sum();return t
allr=[]
for tag,x in [('Bay_unseeded',bu),('Bay_all',b)]:
    allr+= [ent(x,'grp',tag).assign(level='grp'),ent(x,'occ',tag).assign(level='occ')]
E=pd.concat(allr);
# overall junior AI vs non-AI contrast
b['one']='ALL';E=pd.concat([E,ent(bu.assign(one='ALL'),'one','Bay_unseeded').assign(level='all')])
E.to_csv(B+'jobs_entry_requirements.csv',index=False)
cols=['cls','n','entry_share','ba_share','nodeg_share','yrs_known','yrs_med','yrs_mean','yrs_ge3','n_junior','jr_yrs_mean','jr_yrs_med','jr_yrs_ge2','jr_ba','jr_ai_yrs_mean','jr_noai_yrs_mean','n_jr_ai','jr_ai_ba','jr_noai_ba','share_of_all_postings','share_of_all_entry']
print('TEST3 grp unseeded');print(E[(E['sample']=='Bay_unseeded')&(E.level=='grp')][cols].round(3).to_string())
print(E[(E['sample']=='Bay_unseeded')&(E.level=='occ')][cols].round(3).to_string())
print(E[E.level=='all'][cols].round(3).to_string())
# regression within junior: yrs_min ~ ai + class FE
j=b[b.junior&b.yrs_min.notna()&b.company_norm.notna()].copy()
for c in ['ai_strict','ai_use','ai_build','ai_brand','deg_ba','seeded','remote','fulltime','contract']:j[c]=j[c].astype(float)
for lab,jj in [('junior all',j),('junior EXPOSED',j[j.grp=='EXPOSED']),('junior POS',j[j.grp=='AI_POSITIONED'])]:
    X=jj[['ai_use','ai_build','ai_brand','seeded','fulltime','contract','remote']]
    if lab=='junior all': X=X.join(pd.get_dummies(jj.occ,drop_first=True,dtype=float))
    X=sm.add_constant(X.loc[:,X.std()>0]);y=jj.yrs_min
    m=sm.OLS(y,X).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(jj.company_norm)[0]})
    print(lab,len(jj),m.params[['ai_use','ai_build','ai_brand']].round(3).to_dict(),m.bse[['ai_use','ai_build','ai_brand']].round(3).to_dict())
# ---------- TEST 5
b['size']=pd.cut(b.company_reviews.fillna(-1),[-2,-0.5,19,199,1999,1e9],labels=['no_reviews_listed','1-19','20-199','200-1999','2000+'])
b['omit']=(~b.sal_ok).astype(float);bu=b[~b.seeded]
rows=[]
def om(x,key,tag):
    for k,g in x.groupby(key,observed=True):
        s=g[g.sal_ok]
        rows.append(dict(dim=tag,key=str(k),n=len(g),omit_rate=g.omit.mean(),n_sal=len(s),width_med=s.width.median(),width_p75=s.width.quantile(.75),width_p90=s.width.quantile(.9),share_width_ge2=(s.width>=2).mean(),share_width_eq1=(s.width<=1.0001).mean(),
           width_med_annual_only=s[s.sal_period=='year'].width.median(),width_med_hourly_only=s[s.sal_period=='hour'].width.median()))
om(b,'occ','occ');om(b,'grp','grp');om(b,'county','county');om(b,'size','size_proxy_company_reviews');om(b,'seeded','seeded');om(b.assign(a='ALL'),'a','all')
om(bu,'grp','grp_unseeded');om(bu,'occ','occ_unseeded');om(bu,'county','county_unseeded');
T=pd.DataFrame(rows)
# employers
MINN=30
ce=[]
for k,g in b.groupby('company_norm'):
    if len(g)>=MINN or g.sal_ok.sum()>=MINN:
        s=g[g.sal_ok]
        ce.append(dict(dim='EMPLOYER',key=k,name=g.company.mode().iat[0],n=len(g),omit_rate=g.omit.mean(),n_sal=len(s),width_med=s.width.median() if len(s) else np.nan,width_p90=s.width.quantile(.9) if len(s) else np.nan,share_width_ge2=(s.width>=2).mean() if len(s) else np.nan,top_occ=g.occ.mode().iat[0]))
ce=pd.DataFrame(ce)
T=pd.concat([T,ce]);T.to_csv(B+'jobs_transparency.csv',index=False)
print('TEST5');print(T[T.dim.isin(['all','grp','size_proxy_company_reviews','county','seeded'])].round(3).to_string())
print(T[T.dim=='occ'].round(3).to_string())
print('employers min n',MINN,len(ce))
print(ce[ce.n>=MINN].sort_values('omit_rate',ascending=False).head(15).round(3).to_string())
print(ce[ce.n_sal>=MINN].sort_values('width_med',ascending=False).head(15).round(3).to_string())
# LPM omission
x=b[b.company_norm.notna()].copy();x['omit']=x.omit
X=pd.get_dummies(x[['grp','county','size']].astype(str),drop_first=False,dtype=float)
X=X.drop(columns=['grp_OTHER','county_Santa Clara','size_200-1999']);X['seeded']=x.seeded.astype(float);X['remote']=x.remote.astype(float);X['contract']=x.contract.astype(float);X['parttime']=x.parttime.astype(float)
m=sm.OLS(x.omit,sm.add_constant(X)).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(x.company_norm)[0]})
lp=pd.DataFrame({'coef':m.params,'se':m.bse});lp.to_csv(B+'jobs_transparency_lpm.csv');print(lp.round(4).to_string())
# ---------- TEST 8
cty=[];lng=[]
for k,g in b.groupby('county'):
    gu=g[~g.seeded];s=g[g.sal_ok]
    r=dict(county=k,n=len(g),n_unseeded=len(gu),n_sal=len(s),pos_share_all=g.grp.eq('AI_POSITIONED').mean(),pos_share_unseeded=gu.grp.eq('AI_POSITIONED').mean(),exp_share_unseeded=gu.grp.eq('EXPOSED').mean(),fl_share_unseeded=gu.grp.eq('FRONTLINE_SERVICE').mean(),
      exp_share_all=g.grp.eq('EXPOSED').mean(),fl_share_all=g.grp.eq('FRONTLINE_SERVICE').mean(),med_pay=s.sal_mid.median(),med_pay_unseeded=gu[gu.sal_ok].sal_mid.median(),
      ai_strict_share=g.ai_strict.mean(),remote_share=g.remote.mean(),omit_rate=1-g.sal_ok.mean())
    for c in CL: r['med_'+c]=s[s.grp==c].sal_mid.median();r['n_sal_'+c]=int((s.grp==c).sum())
    r['pos_to_exp_plus_fl_unseeded']=r['pos_share_unseeded']/(r['exp_share_unseeded']+r['fl_share_unseeded'])
    for o,sh in gu.occ.value_counts(normalize=True).items(): r['mix_'+o]=sh
    cty.append(r)
    for o,gg in s.groupby('occ'): lng.append(dict(county=k,occ=o,n_sal=len(gg),med_pay=gg.sal_mid.median()))
C=pd.DataFrame(cty).sort_values('pos_share_unseeded',ascending=False);C['rank_pos_share_unseeded']=range(1,len(C)+1)
C.to_csv(B+'jobs_county_table.csv',index=False);pd.DataFrame(lng).to_csv(B+'jobs_county_class_pay.csv',index=False)
print('TEST8');print(C[[c for c in C.columns if not c.startswith('mix_')]].round(3).to_string())
