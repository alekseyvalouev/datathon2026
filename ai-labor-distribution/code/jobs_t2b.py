import sys;sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
exec(open('jobs_t2.py').read().split('R=[]')[0])
b=prep(d[d.bay])
# firm tech-intensity: share of firm's Bay postings (all, not only salaried) that are AI_POSITIONED
allb=d[d.bay];ti=allb.groupby('company_norm').grp.apply(lambda z:(z=='AI_POSITIONED').mean());b['tech_firm']=b.company_norm.map(ti)
R=[]
ex=b[b.grp=='EXPOSED']
R+=fit(ex[ex.tech_firm<0.3],AI+CT,label='Bay|within EXPOSED, firms <30% AI_POSITIONED postings|occ+city FE')
R+=fit(ex[ex.tech_firm>=0.3],AI+CT,label='Bay|within EXPOSED, firms >=30% AI_POSITIONED postings|occ+city FE')
R+=fit(ex[~ex.seeded.astype(bool)],[c for c in AI+CT if c!='seeded'],label='Bay|within EXPOSED, unseeded only|occ+city FE')
R+=fit(b[~b.seeded.astype(bool)],[c for c in AI+CT if c!='seeded'],label='Bay|all, unseeded only|occ+city FE')
R+=fit(b[b.hourly==False],AI+CT,label='Bay|all, annual-posted salaries only|occ+city FE') if False else []
ann=b[b.sal_period=='year'];R+=fit(ann,AI+CT,label='Bay|all, annual-posted only|occ+city FE')
R+=fit(ann[ann.grp=='EXPOSED'],AI+CT,label='Bay|within EXPOSED, annual-posted only|occ+city FE')
print('exposed ai_use n',ex.ai_use.sum(),'at tech firms',(ex.ai_use.astype(bool)&(ex.tech_firm>=.3)).sum(),'distinct firms with ai_use in exposed',ex[ex.ai_use>0].company_norm.nunique())
print(ex[ex.ai_use>0].company.value_counts().head(10).to_dict())
r=pd.DataFrame(R);print(r[r['var'].isin(AI)][['spec','var','coef','se','p','n']].round(4).to_string())
old=pd.read_csv(B+'jobs_ai_premium_regressions.csv');pd.concat([old,r]).to_csv(B+'jobs_ai_premium_regressions.csv',index=False)
