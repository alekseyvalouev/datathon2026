import sys,json,re;sys.path.insert(0,'/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad/code')
from jobs_lib import *
NEG=re.compile(r"(use of AI or recording tools during|Approach to AI in the Hiring|candidates (do not|refrain|are not)|(do not|don.t|refrain from|not) us(e|ing) AI|AI tools (are|is) (strictly )?(not permitted|prohibited)|Use of AI tools without prior|Any use of AI in application|disclose any use of AI|does not use AI|do not use AI|Candidates are encouraged|you may use AI tools for|AI alert|candidate AI-use guidelines|acceptable and prohibited uses of AI|guidance.{0,40}when and how to use AI|AI Candidates|not AI[- ]generated|guidelines regarding the responsible use of AI|Using AI to produce|ask that you do not use AI)",re.I)
POS_=re.compile(r"(uses? AI tools in its recruiting|AI recruiting assistant|AI screening|AI interview|AI[- ]powered|AI[- ]assisted|AI[- ]enabled|AI-based tools|automated AI tools|artificial intelligence tools|utilizes artificial intelligence|automated (decision|recruitment)|use of AI to perform|(we|may|will|also|uses?|utilizes?) (may )?(use|using|utilize)s? (automated )?AI|may use AI|uses? AI|use AI in (the|our) hiring|AI (notetaker|tools?) .{0,40}(recruiting|interview)|AI interviewer|AI in hiring|AI recruiting)",re.I)
d=load();sn=json.load(open(B+'jobs_aihiring_snips.json'))
x=d[d.ai_hiring].copy();x['s']=x.jobid.map(sn)
x['neg']=x.s.str.contains(NEG);x['pos']=x.s.str.contains(POS_)
x['cls']=np.select([x.neg&~x.pos,x.pos&~x.neg,x.pos&x.neg],['FP_candidate_side','TP','BOTH'],'NEITHER')
print(x.cls.value_counts())
for c in ['BOTH','NEITHER']:
    g=x[x.cls==c].groupby('company').agg(n=('jobid','size'),s=('s',lambda z:z.iloc[0][180:560]))
    print(c);print(g.to_string(max_colwidth=380))
x[['jobid','company','cls']].to_csv(B+'jobs_aihiring_classified.csv',index=False)
