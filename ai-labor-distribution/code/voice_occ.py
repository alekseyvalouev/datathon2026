import re
# ordered: specific first. (class, regex)
OCC=[
('AI_DATA_WORK',r"data ?annotat\w*|annotators?|ai trainers?|ai training (?:job|work|project|gig)|rlhf|content (?:evaluators?|raters?|moderators?)|search (?:evaluators?|raters?)|\braters?\b|outlier(?:\.ai)?|dataannotation|mercor|scale ai|data labell?ing|labell?ers?"),
('AI_PRODUCER',r"ml engineers?|machine learning engineers?|\bai engineers?|ai researchers?|research scientists?|prompt engineers?|ai developers?|mlops"),
('DATA_ENG_ANALYTICS',r"data engineers?|data analysts?|data scientists?|bi analysts?|business analysts?|analytics engineers?|data science|data analytics|data engineering"),
('SOFTWARE_ENG',r"software (?:engineers?|developers?|engineering|development)|\bswes?\b|\bdevs?\b|developers?|programmers?|programming|coders?|coding|front.?end|back.?end|full.?stack|devops|\bsdet\b|qa engineers?|web developers?|sysadmin|it support|computer science|software|swe|\bcs (?:grads?|majors?|degree|students?)|junior (?:dev|engineer)s?|tech (?:workers?|jobs?)"),
('OTHER_ENGINEERING',r"(?:mechanical|electrical|civil|hardware|chemical|aerospace|industrial|manufacturing|structural|biomedical|electronics?|embedded) engineer\w*"),
('PRODUCT_DESIGN',r"product managers?|\bpms?\b|ux designers?|ui designers?|ux/ui|product designers?|ux researchers?|program managers?"),
('CUSTOMER_SUPPORT',r"customer (?:service|support|success|care)|call cent(?:er|re)s?|help ?desk|support agents?|\bcsrs?\b|tech support|contact cent(?:er|re)s?|chat ?support|support (?:rep|staff|team)s?"),
('CLERICAL_ADMIN',r"admin(?:istrative)? (?:assistants?|staff|work|jobs?|roles?)|executive assistants?|receptionists?|secretar(?:y|ies)|data entry|office (?:admin|work|clerks?|jobs?|assistants?)|book ?keep\w*|clerks?|clerical|back.?office|paper ?work|virtual assistants?|office managers?|billing|medical coders?|claims? (?:processor|adjuster)s?|payroll"),
('PROF_EXPOSED',r"paralegals?|legal (?:assistants?|work|research)|accountants?|accounting|auditors?|recruiters?|recruiting|talent acquisition|marketing|marketers?|content (?:writers?|creators?|creation|marketing)|copy ?writers?|copywriting|writers?|journalists?|journalism|editors?|proofread\w*|translators?|translation|interpreters?|graphic designers?|illustrators?|animators?|artists?|video editors?|voice actors?|social media|\bhr\b|human resources|designers?|design(?:ing)? jobs?|analysts?|researchers?|lawyers?|attorneys?|law (?:clerk|firm)s?|financial analysts?|actuar\w+|consultants? ?\(analyst|photograph\w+"),
('HEALTH_CLINICAL',r"nurses?|nursing|doctors?|physicians?|radiolog\w+|therapists?|pharmac\w+|dentists?|surgeons?|medical (?:assistants?|staff)|healthcare workers?|clinicians?|paramedics?|caregivers?|psychologists?|psychiatrists?|veterinar\w+|healthcare|medicine|medical field"),
('EDUCATION',r"teachers?|teaching|professors?|tutors?|instructors?|educators?|lecturers?|school (?:staff|district)|faculty"),
('SKILLED_TRADE',r"electricians?|plumbers?|welders?|mechanics?|hvac|carpenters?|construction|the trades|skilled trades?|tradespeople|trade jobs?|technicians?|machinists?|linem[ae]n|roofers?"),
('FRONTLINE_SERVICE',r"cashiers?|waiters?|waitress\w*|servers?\b|baristas?|retail|warehouse|truck drivers?|drivers?|delivery|cooks?|chefs?|janitor\w*|fast food|mcdonald'?s|restaurant\w*|bartenders?|stockers?|housekeep\w+|security guards?|amazon warehouse|hospitality|food service|barber|hairstylists?|cleaners?|labou?rers?|manual labou?r"),
('SALES_BIZ',r"sales(?:people|person| reps?| roles?| jobs?)?|\bsdrs?\b|\bbdrs?\b|account executives?|account managers?|business development|bankers?|banking|investment banking|finance (?:jobs?|roles?|bros?)|real estate agents?|realtors?|insurance (?:agents?|brokers?)|brokers?|wealth manage\w+|consulting|consultants?|private equity"),
('MANAGEMENT',r"managers?|directors?|\bvps?\b|vice presidents?|executives?|c-suite|\bceos?\b|team leads?|supervisors?|middle management|leadership"),
]
OCCC=[(c,re.compile(r"\b(?:"+p+r")\b",re.I)) for c,p in OCC]
# first-person own-occupation patterns (tight: occupation within 35 chars, no punctuation between)
SELF=re.compile(r"(?:\bI(?:'m| am| was|'ve been| have been| worked as| work as| work in| worked in|'m currently| am currently| used to be)\s+(?:currently |now |still |an? |the )?|\bas an? |\bmy (?:job|role|position|career|profession) (?:as|is|was)\s+(?:an? )?|\bformer |\blaid off (?:as|from)\s+(?:an? )?)([^.,;\n!?]{0,35})",re.I)
def own_class(t):
    for m in SELF.finditer(t):
        seg=m.group(1)
        for c,rx in OCCC:
            if c=='MANAGEMENT': continue
            if rx.search(seg): return c
    return None
def any_classes(t):
    out=[]
    for c,rx in OCCC:
        if c=='MANAGEMENT': continue
        if rx.search(t): out.append(c)
    return out
def first_named(t):
    # earliest-position mention; specific-order tie
    best=(10**9,None)
    for c,rx in OCCC:
        if c=='MANAGEMENT': continue
        m=rx.search(t)
        if m and m.start()<best[0]: best=(m.start(),c)
    return best[1]

def primary(t):
    s=own_class(t)
    if s: return s,'self'
    title=t.split(' . ')[0]
    f=first_named(title)
    if f: return f,'title'
    f=first_named(t)
    if f: return f,'body_lowconf'
    return None,None
