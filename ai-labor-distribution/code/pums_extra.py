"""County concentration of AI-positioned/exposed employment; exposure by sex; wage-rank vs AI-position. Usage: pums_extra.py base_dir"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pums_lib as L, pums_exposure as E
B=sys.argv[1]
d=E.prep(f'{B}/pums_bay.parquet')
def fn(df,w):
    outs={}
    W=df[w].values
    tot=W.sum()
    for c in L.BAY.values():
        m=(df.county.values==c)
        for cat in ('AIPOS','EXPOSED','ALL'):
            x=df['i_'+cat].values
            outs[(c,cat,'w')]=(W*x*m).sum()
        for cat in ('AIPOS','EXPOSED'):
            outs[(c,cat,'share_of_bay_cat')]=(W*df['i_'+cat].values*m).sum()/(W*df['i_'+cat].values).sum()
            outs[(c,cat,'share_of_county_emp')]=(W*df['i_'+cat].values*m).sum()/(W*m).sum()
            outs[(c,cat,'location_quotient')]=outs[(c,cat,'share_of_county_emp')]/((W*df['i_'+cat].values).sum()/tot)
        outs[(c,'ALL','share_of_bay_cat')]=(W*m).sum()/tot
        for r in L.RACES:
            mr=m&(df.race_eth.values==r)
            outs[(c,'AIPOS','share_of_bay_AIPOS_by_race_'+r)]=(W*df.i_AIPOS.values*mr).sum()/(W*df.i_AIPOS.values*m).sum() if (W*df.i_AIPOS.values*m).sum()>0 else np.nan
    s=pd.Series(outs); s.index=s.index.set_names(['county','category','metric']); return s
est,se=L.rep_se(fn,d)
r=pd.concat([est.rename('est'),se.rename('se')],axis=1).reset_index()
nn=d.groupby('county').agg(n_unw=('PWGTP','size')); nA=d[d.i_AIPOS>0].groupby('county').size().rename('n_AIPOS_unw'); nE=d[d.i_EXPOSED>0].groupby('county').size().rename('n_EXPOSED_unw')
r=r.merge(nn.join(nA).join(nE).reset_index(),on='county'); r.to_csv(f'{B}/ai_concentration_by_county.csv',index=False)
# by sex
rows=[]
for sx,nm in ((1,'Male'),(2,'Female')):
    for r_ in L.RACES+['All']:
        m=(d.SEX==sx)&((d.race_eth==r_) if r_!='All' else True)
        x=d[m]; W=x.PWGTP
        rows.append(dict(sex=nm,race_eth=r_,n_unw=len(x),exposed_share=(W*x.i_EXPOSED).sum()/W.sum(),aipos_share=(W*x.i_AIPOS).sum()/W.sum(),n_exposed_unw=int((x.i_EXPOSED>0).sum())))
pd.DataFrame(rows).to_csv(f'{B}/exposure_by_race_sex.csv',index=False)
# share female among exposed
x=d[d.i_EXPOSED>0]; print('female share of exposed',(x.PWGTP*(x.SEX==2)).sum()/x.PWGTP.sum(),' of all',(d.PWGTP*(d.SEX==2)).sum()/d.PWGTP.sum())
# education of exposed vs AIPOS
for nm in ('EXPOSED','AIPOS'):
    x=d[d['i_'+nm]>0]; print(nm, (x.groupby('education').PWGTP.sum()/x.PWGTP.sum()).round(3).to_dict())
print(r[(r.metric.isin(['share_of_bay_cat','location_quotient']))&(r.category=='AIPOS')].round(3).to_string())
print(r[(r.metric=='share_of_bay_cat')&(r.category.isin(['EXPOSED','ALL']))].round(3).pivot_table(index='county',columns='category',values='est'))
print(pd.DataFrame(rows).round(3).to_string())
