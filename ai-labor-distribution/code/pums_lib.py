"""Shared helpers: OCCP -> occ_class mapping (rules verified against the official PUMS data dictionary), race_eth, replicate-weight SEs."""
import csv, numpy as np, pandas as pd

CLASSES = ['AI_PRODUCER','SOFTWARE_ENG','DATA_ENG_ANALYTICS','OTHER_ENGINEERING','PRODUCT_DESIGN','CLERICAL_ADMIN',
           'CUSTOMER_SUPPORT','PROF_EXPOSED','HEALTH_CLINICAL','EDUCATION','FRONTLINE_SERVICE','SKILLED_TRADE',
           'SALES_BIZ','MANAGEMENT','OTHER']
EXPOSED = ['CLERICAL_ADMIN','CUSTOMER_SUPPORT','PROF_EXPOSED']
AIPOS = ['AI_PRODUCER','SOFTWARE_ENG','DATA_ENG_ANALYTICS']
RACES = ['White','Black','Asian','Hispanic','AIAN','NHPI','Two_or_Other']
BAY = {'001':'Alameda','013':'Contra Costa','041':'Marin','055':'Napa','075':'San Francisco','081':'San Mateo','085':'Santa Clara','095':'Solano','097':'Sonoma'}

PREFIX_DEFAULT = {'MGR':'MANAGEMENT','BUS':'SALES_BIZ','FIN':'PROF_EXPOSED','CMM':'SOFTWARE_ENG','ENG':'OTHER_ENGINEERING',
  'SCI':'OTHER','CMS':'OTHER','LGL':'OTHER','EDU':'EDUCATION','ENT':'OTHER','MED':'HEALTH_CLINICAL','HLS':'HEALTH_CLINICAL',
  'PRT':'FRONTLINE_SERVICE','EAT':'FRONTLINE_SERVICE','CLN':'FRONTLINE_SERVICE','PRS':'FRONTLINE_SERVICE','SAL':'SALES_BIZ',
  'OFF':'CLERICAL_ADMIN','FFF':'OTHER','CON':'SKILLED_TRADE','EXT':'SKILLED_TRADE','RPR':'SKILLED_TRADE','PRD':'SKILLED_TRADE',
  'TRN':'FRONTLINE_SERVICE','MIL':'OTHER'}
OVERRIDE = {}
def _o(cls, codes, note):
    for c in codes.split(): OVERRIDE[c]=(cls,note)
_o('AI_PRODUCER','1005 1240','CS research scientists; 1240 holds data scientists/statisticians/mathematicians (SOCP-checked)')
_o('DATA_ENG_ANALYTICS','1200 1220','actuaries; operations research analysts')
_o('PRODUCT_DESIGN','1032 2631 2632 2635 2640','web/digital interface (UX) and non-graphic designers')
_o('PRODUCT_DESIGN','0705','project management specialists = closest separable proxy for product/program managers (JUDGMENT)')
_o('CUSTOMER_SUPPORT','1050','computer support specialists (per spec)')
_o('CUSTOMER_SUPPORT','5010 5020 5040 5160 5240 5300 5410 5521 5522','switchboard/telephone ops, tellers, CSRs, hotel desk, reservation agents, dispatchers/telecommunicators')
_o('PROF_EXPOSED','0540 0565 0630 0640 0650 0735 2105 2145 2170 2180 2634 2810 2825 2830 2840 2850 2861 2862 5910','claims adjusters, compliance, HR/training, marketing research, legal support, graphic designers, writers/editors/PR/translators/reporters, proofreaders')
_o('SALES_BIZ','0850 4940','personal financial advisors (sales-type); telemarketers (sales)')
_o('FRONTLINE_SERVICE','2633 2636 4700 4720 4740 4750 4760 4900 4950','retail/cashier/counter/promoter/vendor sales; floral designers & merchandise displayers (retail)')
_o('CLERICAL_ADMIN','3515 3646','medical records specialists; medical transcriptionists (clerical content, not hands-on care)')
_o('FRONTLINE_SERVICE','5510 5530 5550 5560 5610 5630','couriers, meter readers, mail carriers/postal sorters, shipping-receiving & weigher clerks = physical logistics, not screen-based clerical (JUDGMENT; see robustness)')
AMBIGUOUS_TO_CLERICAL = '5510 5530 5550 5560 5610 5630'.split()   # robustness: treat as CLERICAL_ADMIN

def load_occp(dict_csv):
    d={}
    for r in csv.reader(open(dict_csv, encoding='utf-8-sig')):
        if r[0]=='VAL' and r[1]=='OCCP': d[r[4]]=r[6]
    return d

def classify(code, title):
    if code in OVERRIDE: return OVERRIDE[code][0], 'override: '+OVERRIDE[code][1]
    pre = title.split('-')[0]
    if pre in PREFIX_DEFAULT: return PREFIX_DEFAULT[pre], 'prefix '+pre
    return 'OTHER', 'not an occupation (N/A/never worked)'

def race_eth(hisp, rac1p):
    h = pd.to_numeric(hisp, errors='coerce'); r = pd.to_numeric(rac1p, errors='coerce')
    out = np.select([h>1, r==1, r==2, r.isin([3,4,5]), r==6, r==7], ['Hispanic','White','Black','AIAN','Asian','NHPI'], 'Two_or_Other')
    return pd.Series(out, index=hisp.index)

def edu_bucket(schl):
    s = pd.to_numeric(schl, errors='coerce')
    return pd.cut(s, [0,15,17,20,21,24], labels=['LessThanHS','HS','SomeCollege_Assoc','Bachelors','Graduate']).astype(object)

# ---------- weighted stats ----------
def wmedian(x, w):
    x=np.asarray(x,float); w=np.asarray(w,float)
    m=~np.isnan(x)&(w>0); x=x[m]; w=w[m]
    if len(x)==0: return np.nan
    i=np.argsort(x,kind='stable'); x=x[i]; cw=np.cumsum(w[i]); return x[np.searchsorted(cw, 0.5*cw[-1])]

REP = [f'PWGTP{i}' for i in range(1,81)]
def rep_se(fn, df, wcol='PWGTP'):
    """fn(df, wcol)->pd.Series. Successive-difference replication: var = 4/80 * sum (theta_r - theta)^2. Returns (est, se)."""
    est = fn(df, wcol)
    acc = None
    for r in REP:
        d = (fn(df, r).reindex(est.index) - est)**2
        acc = d if acc is None else acc + d.fillna(0)*1.0
    return est, np.sqrt(4/80*acc)
