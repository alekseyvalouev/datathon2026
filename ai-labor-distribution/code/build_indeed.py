import csv, re, json, sys, collections, datetime as dt
import pandas as pd, numpy as np

SCR="/private/tmp/claude-501/-Users-alekseyvalouev--claude-spares-spare-rjO4u1/79646f5d-c0fc-40a8-b07a-1d29046ca563/scratchpad"
SRC="/Users/alekseyvalouev/Desktop/Datathon/indeed_job_listings-002.csv"
csv.field_size_limit(10**9)

# ---------- place -> county ----------
pc = pd.read_csv(f"{SCR}/ext/place_county.txt", sep="|", dtype=str)
pc = pc[pc.STATE=="CA"]
city2cty = {}
for _,r in pc.iterrows():
    nm = re.sub(r'\s+(city|town|CDP|village)$','', r.PLACENAME, flags=re.I).strip().lower()
    cty = r.COUNTYNAME.replace(" County","")
    # keep first (places spanning counties -> primary)
    city2cty.setdefault(nm, cty)
BAY9 = {"Alameda","Contra Costa","Marin","Napa","San Francisco","San Mateo","Santa Clara","Solano","Sonoma"}
EXTRA = {"san francisco bay area":"San Francisco","south san francisco":"San Mateo",
         "mountain view":"Santa Clara","palo alto":"Santa Clara","menlo park":"San Mateo",
         "redwood city":"San Mateo","foster city":"San Mateo","san mateo":"San Mateo",
         "sunnyvale":"Santa Clara","cupertino":"Santa Clara","santa clara":"Santa Clara",
         "san jose":"Santa Clara","oakland":"Alameda","berkeley":"Alameda","fremont":"Alameda",
         "walnut creek":"Contra Costa","emeryville":"Alameda","brisbane":"San Mateo",
         "burlingame":"San Mateo","san carlos":"San Mateo","belmont":"San Mateo",
         "castro valley":"Alameda","san ramon":"Contra Costa","dublin":"Alameda",
         "pleasanton":"Alameda","livermore":"Alameda","milpitas":"Santa Clara",
         "campbell":"Santa Clara","los gatos":"Santa Clara","saratoga":"Santa Clara",
         "morgan hill":"Santa Clara","gilroy":"Santa Clara","newark":"Alameda",
         "union city":"Alameda","hayward":"Alameda","san leandro":"Alameda",
         "richmond":"Contra Costa","concord":"Contra Costa","vallejo":"Solano",
         "fairfield":"Solano","santa rosa":"Sonoma","petaluma":"Sonoma","napa":"Napa",
         "san rafael":"Marin","novato":"Marin","daly city":"San Mateo","millbrae":"San Mateo"}
city2cty.update(EXTRA)

def geo(location, job_location):
    s = (location or "").strip()
    jl = (job_location or "")
    remote = bool(re.search(r'\bremote\b', s+" "+jl, re.I))
    hybrid = bool(re.search(r'\bhybrid\b', s+" "+jl, re.I))
    s = re.sub(r'^(hybrid work in|remote in|remote work in)\s+','',s,flags=re.I)
    # strip street addresses / zips: take the "City, CA" piece
    m = re.search(r'([A-Za-z .\'\-/]+),\s*CA', s)
    city = m.group(1).strip().lower() if m else None
    if city:
        city = re.sub(r'^\d+\s+','',city)
        city = re.sub(r'\s+(expressway|ave|avenue|st|street|blvd|road|rd|dr|drive|way|pkwy|parkway|ct|ln|lane|circle|cir|plaza)$','',city).strip()
        city = city.split("/")[-1].strip() if "/" in city else city
    cty = city2cty.get(city) if city else None
    return pd.Series([city, cty, (cty in BAY9) if cty else False, remote, hybrid])

# ---------- salary ----------
NUM = r'\$?\s*([\d,]+(?:\.\d+)?)'
def parse_salary(s):
    if not s: return (np.nan, np.nan, None)
    t = s.replace("–","-").replace("—","-")
    per = None
    if re.search(r'an hour|por hora|hourly|/hr|per hour', t, re.I): per="hour"
    elif re.search(r'a year|por a|annually|/yr|per year', t, re.I): per="year"
    elif re.search(r'a month|por mes|monthly', t, re.I): per="month"
    elif re.search(r'a week|por semana|weekly', t, re.I): per="week"
    elif re.search(r'a day|por d|daily', t, re.I): per="day"
    nums = [float(x.replace(",","")) for x in re.findall(NUM, t)]
    nums = [n for n in nums if n>0]
    if not nums: return (np.nan, np.nan, per)
    lo, hi = min(nums), max(nums)
    if per is None:
        per = "hour" if hi < 300 else "year"
    mult = {"hour":2080,"year":1,"month":12,"week":52,"day":260}[per]
    lo, hi = lo*mult, hi*mult
    if lo < 10000 or lo > 3_000_000: return (np.nan, np.nan, per)
    return (lo, hi, per)

# ---------- posting date ----------
def post_date(parsed, rel):
    if not parsed: return (pd.NaT, True)
    try: base = pd.Timestamp(parsed).tz_localize(None).normalize()
    except Exception: return (pd.NaT, True)
    r = (rel or "").strip().lower()
    if re.search(r'just posted|today|reci.n publicad|hoy', r): return (base, False)
    if re.search(r'30\+', r): return (base - pd.Timedelta(days=30), True)   # censored
    m = re.search(r'(\d+)\s*(day|d.a)', r)
    if m: return (base - pd.Timedelta(days=int(m.group(1))), False)
    m = re.search(r'(\d+)\s*(hour|hora)', r)
    if m: return (base, False)
    return (base, True)

# ---------- occupation taxonomy ----------
# ordered rules: first match wins
TAX = [
 ("AI_DATA_WORK", r'\b(data annotat|annotator|data label|ai trainer|ai tutor|rlhf|prompt writer|content evaluator|search evaluator|transcriber|transcription|data collect(or|ion) (associate|specialist)|human data|model train(er|ing) (associate|specialist))'),
 ("AI_PRODUCER",  r'\b(machine learning|ml |mlops|ai |a\.i\.|deep learning|nlp|computer vision|llm|generative ai|applied scientist|research scientist|research engineer|data scientist|data science|ai/ml|artificial intelligence|member of technical staff|forward deployed engineer)'),
 ("DATA_ENG_ANALYTICS", r'\b(data engineer|analytics engineer|data architect|data platform|business intelligence|bi developer|data analyst|analytics (manager|lead|analyst))'),
 ("SOFTWARE_ENG",  r'\b(software engineer|software developer|swe\b|full ?stack|front ?end|back ?end|devops|site reliability|sre\b|platform engineer|security engineer|infrastructure engineer|mobile (engineer|developer)|ios (engineer|developer)|android (engineer|developer)|embedded (software|engineer)|firmware|cloud engineer|solutions architect|engineering manager|principal engineer|staff engineer|founding engineer|web developer|programmer|qa engineer|test engineer|automation engineer)'),
 ("OTHER_ENGINEERING", r'\b(mechanical engineer|electrical engineer|hardware engineer|civil engineer|chemical engineer|process engineer|manufacturing engineer|industrial engineer|quality engineer|design engineer|systems engineer|validation engineer|rf engineer|optical engineer|aerospace|structural engineer)'),
 ("PRODUCT_DESIGN", r'\b(product manager|product owner|program manager|technical program|product designer|ux|ui designer|user experience|user research)'),
 ("CLERICAL_ADMIN", r'\b(administrative (assistant|associate|coordinator|specialist)|admin assistant|executive assistant|office (assistant|manager|clerk|coordinator)|data entry|receptionist|front desk (associate|coordinator|agent)?|clerk|clerical|file clerk|scheduler|scheduling (coordinator|specialist)|secretary|billing (specialist|clerk|coordinator)|accounts (payable|receivable)|bookkeep|payroll (clerk|specialist|administrator)|medical records|health information|claims (processor|examiner|specialist|adjuster)|loan (processor|officer assistant)|document (control|specialist)|records (specialist|clerk)|order (entry|processor)|typist|transcriptionist)'),
 ("CUSTOMER_SUPPORT", r'\b(customer (service|support|experience|care|success)|call center|contact center|client service|help ?desk|technical support|tech support|support (specialist|representative|associate|agent|analyst|engineer)|collections (specialist|representative)|dispatcher|reservations agent|teller|patient (access|service|registration)|member services|csr\b)'),
 ("PROF_EXPOSED",  r'\b(paralegal|legal assistant|legal secretary|tax (associate|preparer|specialist)|accountant|accounting (associate|specialist|clerk)|auditor|underwriter|actuarial analyst|financial analyst|marketing (coordinator|specialist|associate|analyst)|content (writer|creator|specialist|strategist)|copywriter|writer|editor|translator|interpreter|graphic designer|social media|seo|recruiter|recruiting coordinator|talent acquisition|hr (coordinator|assistant|generalist|specialist)|human resources (coordinator|assistant|generalist)|research (associate|assistant|analyst)|market research|insurance agent|appraiser|proofread)'),
 ("HEALTH_CLINICAL", r'\b(registered nurse|\brn\b|\blvn\b|\bcna\b|nurse|nursing|physician|doctor|surgeon|dentist|pharmacist|pharmacy technician|medical assistant|physical therap|occupational therap|speech (language )?patholog|respiratory therap|radiolog|sonograph|phlebotom|medical technologist|laboratory (technician|technologist|assistant)|clinical (coordinator|specialist|research)|behavior technician|psycholog|therapist|counselor|social worker|case manager|dental (hygienist|assistant)|veterinar|optometr|anesthe|midwife|paramedic|emt\b|surgical tech|caregiver|home health|personal care|patient care (technician|assistant)|hospice|医)'),
 ("EDUCATION",     r'\b(teacher|professor|instructor|lecturer|tutor|teaching assistant|principal, |school (counselor|psychologist)|childcare|preschool|early childhood|education (coordinator|specialist)|coach, |academic advisor|librarian)'),
 ("FRONTLINE_SERVICE", r'\b(cashier|team member|crew|sales associate|retail (sales|associate|specialist)|store (associate|support|clerk|shopper)|stocker|stock associate|merchandis|cook|chef|baker|barista|server|waiter|waitress|bartender|host(ess)?\b|dishwasher|busser|food (service|runner|prep)|kitchen|prep cook|line cook|deli|butcher|produce|bagger|courtesy clerk|janitor|custodian|housekeep|cleaner|groundskeep|landscap|security (guard|officer|specialist)|driver|delivery|courier|warehouse|material handler|picker|packer|forklift|shipping|receiving|freight|loader|valet|parking|usher|attendant|concierge|laundry|dry clean|car wash|pet (groomer|care)|nail tech|hair stylist|barber|esthetician|massage|fitness|lifeguard|camp counselor)'),
 ("SKILLED_TRADE", r'\b(technician|mechanic|electrician|plumber|carpenter|welder|machinist|hvac|installer|lineman|operator|maintenance|millwright|painter|roofer|mason|ironworker|pipefitter|sheet metal|construction|foreman|surveyor|inspector|locksmith|fabricat|assembler|production (worker|associate|technician)|manufacturing (associate|technician|operator)|cnc)'),
 ("SALES_BIZ",     r'\b(account (executive|manager|director)|sales (representative|manager|director|engineer|consultant|development)|business development|bdr\b|sdr\b|territory manager|regional sales|inside sales|outside sales|real estate agent|mortgage (loan officer|advisor)|financial advisor|relationship manager|broker)'),
 ("MANAGEMENT",    r'\b(manager|director|vice president|\bvp\b|chief |head of|supervisor|lead\b|president|partner|principal|controller|administrator|superintendent|executive director)'),
]
TAXC = [(n, re.compile(p, re.I)) for n,p in TAX]
def occ_class(title):
    t = " "+(title or "").lower()+" "
    for n,p in TAXC:
        if p.search(t): return n
    return "OTHER"

# ---------- AI text flags ----------
AI_BUILD = re.compile(r'\b(train(ing)? (a |an )?model|build(ing)? (ml|ai|machine learning)|ml (pipeline|infrastructure|platform)|model (architecture|deployment|serving)|fine-?tun|pytorch|tensorflow|hugging ?face|transformer architecture|rag pipeline|vector (database|store)|llm (training|inference|serving)|cuda|deep learning)', re.I)
AI_USE   = re.compile(r'\b(ai[- ]?(tool|assisted|powered|enabled|augmented)|using (ai|genai|generative ai|llms?|chatgpt|copilot|claude|gemini)|leverage (ai|genai|llms?)|ai (literacy|fluency|proficien)|comfortable (using|with) ai|prompt (engineering|writing|craft)|copilot|chatgpt|generative ai tools|ai (workflow|agents?) to)', re.I)
AI_ANY   = re.compile(r'\b(artificial intelligence|machine learning|generative ai|genai|gen ai|\bllms?\b|large language model|chatgpt|openai|anthropic|copilot|deep learning|neural network|prompt engineer|\bai\b)', re.I)
AI_REPLACE = re.compile(r'\b(automat(e|ing|ion) (of )?(manual|repetitive|routine)|reduce (manual|repetitive)|ai[- ]first|do(ing)? the work of|replace (manual|repetitive)|eliminate (manual|repetitive)|streamline.{0,30}(with|using) (ai|automation))', re.I)
DEGREE_BA = re.compile(r"\b(bachelor'?s?|\bb\.?s\.?\b|\bb\.?a\.?\b|undergraduate degree|four-year degree)", re.I)
DEGREE_GRAD = re.compile(r"\b(master'?s?|\bm\.?s\.?\b|\bmba\b|ph\.?d|doctorate)", re.I)
NO_DEGREE = re.compile(r'\b(no degree (required|necessary)|high school (diploma|graduate)|ged\b|equivalent experience|or equivalent)', re.I)
YRS = re.compile(r'(\d{1,2})\s*\+?\s*(?:-\s*\d{1,2}\s*)?(?:years?|yrs?)[^.]{0,30}?(?:experience|exp\b)', re.I)
def yrs_min(txt):
    v=[int(m.group(1)) for m in YRS.finditer(txt or "") if int(m.group(1))<=30]
    return min(v) if v else np.nan
SENIOR = re.compile(r'\b(senior|sr\.?|staff|principal|lead|director|head of|vp|chief|manager|ii+\b|iv\b|expert)', re.I)
JUNIOR = re.compile(r'\b(junior|jr\.?|entry[- ]level|associate|intern|trainee|apprentice|assistant|\bi\b|new grad|graduate)', re.I)

def norm_company(c):
    if not c: return ""
    c=c.lower()
    c=re.sub(r'[‘’“”]',"'",c)
    c=re.sub(r'\b(inc|llc|l\.l\.c|corp|corporation|co|ltd|limited|lp|llp|plc|group|holdings|usa|us|the)\b','',c)
    c=re.sub(r'[^a-z0-9]+','',c)
    return c

rows=[]
with open(SRC, newline='', encoding='utf8', errors='replace') as f:
    for i,row in enumerate(csv.DictReader(f)):
        d = row.get('description_text') or row.get('description') or ""
        title = row.get('job_title') or ""
        lo,hi,per = parse_salary(row.get('salary_formatted'))
        pd_,cens = post_date(row.get('date_posted_parsed'), row.get('date_posted'))
        rows.append(dict(
            jobid=row.get('jobid'), title=title, company=row.get('company_name'),
            company_norm=norm_company(row.get('company_name')),
            location=row.get('location'), job_location=row.get('job_location'),
            job_type=row.get('job_type') or "",
            crawl=(row.get('date_posted_parsed') or "")[:10],
            post_date=pd_, censored=cens,
            sal_lo=lo, sal_hi=hi, sal_period=per, has_salary=bool(row.get('salary_formatted')),
            occ=occ_class(title),
            ai_any=bool(AI_ANY.search(d)), ai_build=bool(AI_BUILD.search(d)),
            ai_use=bool(AI_USE.search(d)), ai_replace=bool(AI_REPLACE.search(d)),
            ai_title=bool(AI_ANY.search(title)),
            deg_ba=bool(DEGREE_BA.search(d)), deg_grad=bool(DEGREE_GRAD.search(d)),
            no_deg=bool(NO_DEGREE.search(d)),
            yrs_min=yrs_min(d), senior=bool(SENIOR.search(title)), junior=bool(JUNIOR.search(title)),
            desc_len=len(d),
            company_rating=row.get('company_rating') or None,
            company_reviews=row.get('company_reviews_count') or None,
        ))
        if (i+1)%25000==0: print("  parsed", i+1, file=sys.stderr)

df = pd.DataFrame(rows)
df[['city','county','bay','remote','hybrid']] = df.apply(lambda r: geo(r['location'], r['job_location']), axis=1)
df['contract'] = df.job_type.str.contains('Contract', case=False, na=False)
df['parttime'] = df.job_type.str.contains('Part-time', case=False, na=False)
df['fulltime'] = df.job_type.str.contains('Full-time', case=False, na=False)
df['internship'] = df.job_type.str.contains('Internship|Temporary|Seasonal', case=False, na=False)
df['sal_mid'] = df[['sal_lo','sal_hi']].mean(axis=1)
df['company_rating']=pd.to_numeric(df.company_rating, errors='coerce')
df['company_reviews']=pd.to_numeric(df.company_reviews, errors='coerce')

print("RAW", len(df))
df['dup_key'] = df.title.str.lower().str.strip()+"|"+df.company_norm+"|"+df.city.fillna("")+"|"+df.sal_lo.fillna(-1).astype(str)
dd = df.sort_values('crawl').drop_duplicates('dup_key', keep='first')
print("DEDUPED", len(dd), " bay:", dd.bay.sum())
dd.to_parquet(f"{SCR}/base/indeed_base.parquet", index=False)
print(dd.occ.value_counts().to_string())
print("\ncounty coverage (top 15):"); print(dd.county.value_counts().head(15).to_string())
print("\nunmapped city examples:", dd[dd.county.isna()].city.value_counts().head(15).to_dict())
