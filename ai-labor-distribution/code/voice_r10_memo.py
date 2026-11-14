import sys,pandas as pd,numpy as np
S=sys.argv[1]
mon=pd.read_csv(S+'/base/reddit_monthly.csv'); rw=pd.read_csv(S+'/base/reddit_monthly_reweighted.csv')
wg=mon[mon.scope=='WORK_GEN'].set_index('month'); by=mon[mon.scope=='BAY'].set_index('month')
def md(df,fmt=None):
    cols=list(df.columns); s='| '+' | '.join(cols)+' |\n|'+'|'.join(['---']*len(cols))+'|\n'
    for _,r in df.iterrows(): s+='| '+' | '.join(str(v) for v in r.values)+' |\n'
    return s
t=pd.DataFrame({'month':wg.index,'posts in WORK_GEN':wg.n_posts.values,'AI-work posts':wg.n_ai_work.values,'raw share %':(wg.share_ai_work*100).round(2).values,
 'fixed-mix share %':(rw.set_index('month').reindex(wg.index).reweighted_share_ai_work*100).round(2).values,
 'any-AI-term share %':(wg.share_ai_any_term*100).round(1).values,'BAY posts':by.reindex(wg.index).n_posts.values,'BAY AI-work':by.reindex(wg.index).n_ai_work.values})
t.loc[t.month=='2026-11','month']='2026-11 (partial, 13 days)'
series=md(t)
cr=pd.read_csv(S+'/base/glassdoor_class_ratings.csv')
keep=['AI_PRODUCER','SOFTWARE_ENG','DATA_ENG_ANALYTICS','CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED','FRONTLINE_SERVICE','HEALTH_CLINICAL','SKILLED_TRADE','EDUCATION','MANAGEMENT','SALES_BIZ','PRODUCT_DESIGN','OTHER_ENGINEERING','AI_DATA_WORK','OTHER','MISSING_TITLE','AI_POSITIONED','EXPOSED','IN_PERSON','ALL_CA']
c=cr.set_index('label').loc[keep]
ct=pd.DataFrame({'class':c.index,'n':c.n.values,'overall':c.mean_overall.round(2).values,'comp':c.mean_compensation_benefits.round(2).values,'career':c.mean_career_opportunities.round(2).values,'sr.leader':c.mean_senior_leadership.round(2).values,'work-life':c.mean_work_life.round(2).values,'culture':c.mean_culture_values.round(2).values,'D&I':c.mean_diversity_inclusion.round(2).values})
ctab=md(ct)
a=pd.read_csv(S+'/base/glassdoor_aip_vs_exposed.csv')
at=pd.DataFrame({'outcome':a.outcome.str.replace('rating_','').values,'AI-pos mean':a.mean_AI_POSITIONED.round(3).values,'Exposed mean':a.mean_EXPOSED.round(3).values,'diff':a.diff_AIP_minus_EXP.round(3).values,"Cohen's d (CI)":[f'{d:.2f} [{l:.2f},{h:.2f}]' for d,l,h in zip(a.cohens_d,a.d_ci_lo,a.d_ci_hi)],'Welch p':[f'{p:.3g}' for p in a.welch_p],'adj. diff (Exposed - AIP), controls':a.adj_coef_exposed_controls.round(3).values,'adj. diff, company FE (se)':[f'{b:.3f} ({s:.3f}), p={p:.3g}' for b,s,p in zip(a.companyFE_coef_exposed,a.companyFE_se,a.companyFE_p)]})
atab=md(at)
tx=pd.read_csv(S+'/base/glassdoor_text_rates_by_class.csv').set_index('label')
sel=['AI_POSITIONED','EXPOSED','IN_PERSON','CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED','SOFTWARE_ENG','FRONTLINE_SERVICE','HEALTH_CLINICAL']
tt=pd.DataFrame({'class':sel,'n':tx.loc[sel,'n_cons'].values})
for k,nm in [('t_layoff','layoffs/restructuring'),('t_staffing','understaffing / work of 2+'),('t_workload','workload'),('t_ai_mention','AI/automation mention'),('t_ai_threat','AI replace/cut (strict)'),('t_offshore','offshoring/outsourcing')]:
    tt[nm+' %']=(tx.loc[sel,k]*100).round(2).values
ttab=md(tt)
pr=pd.read_csv(S+'/base/voice_precision_handchecks.csv')
prt=pd.DataFrame({'measure':pr.measure,'checked':pr.n_checked,'correct':pr.n_correct,'precision %':(pr.precision*100).round(1),'95% CI':[('' if pd.isna(l) else f'{l*100:.0f}-{h*100:.0f}') for l,h in zip(pr.ci_lo,pr.ci_hi)]})
prtab=md(prt)
open(S+'/out/_tables.md','w').write('## SERIES\n'+series+'\n## CLASSRATINGS\n'+ctab+'\n## AIPEXP\n'+atab+'\n## TEXT\n'+ttab+'\n## PREC\n'+prtab)
print(open(S+'/out/_tables.md').read())
