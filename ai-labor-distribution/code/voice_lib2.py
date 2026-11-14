import re
AIM_CS=re.compile(r"\bAI\b|\bA\.I\.|AI-|-AI\b|ChatGPT|Chat GPT|chatgpt|OpenAI|\bLLMs?\b|[Gg]enerative AI|\bClaude\b|\bCopilot\b|\bGemini\b|DeepSeek|[Aa]rtificial [Ii]ntelligence|\bGPT-?\d")
AIW=r"(?:AI|A\.I\.|chat ?gpt|chatbots?|automation|LLMs?|claude|copilot|gemini)"
ACTUAL2=re.compile(
 r"replaced (?:me|us|my|our|him|her|them|the (?:team|department|staff|workers|employees|writers|designers|engineers|developers|agents))\b[^.]{0,60}\b"+AIW+r"\b"
 r"|\b(?:replace|replaced|replacing)\b[^.]{0,40}\b(?:with|by) (?:an? )?"+AIW+r"\b"
 r"|\b"+AIW+r" (?:replaced|took|is replacing|has replaced|eliminated|took over)\b"
 r"|(?:laid off|layoffs?|let go|fired|terminated|eliminated|redundan\w+|downsiz\w+|restructur\w+)[^.]{0,80}\b(?:because of|due to|thanks to|as a result of|replaced by|in favor of|to make way for|attribut\w+ to|blamed|citing|cited)\b[^.]{0,30}\b"+AIW+r"\b"
 r"|\b(?:my|our) (?:job|role|position|team|department|company|employer)\b[^.]{0,60}\b(?:was|were|has been|have been|is being|are being|got) (?:replaced|eliminated|laid off|let go|cut|automated)[^.]{0,50}\b"+AIW+r"\b"
 r"|\b(?:lost|losing) (?:my|his|her|their) (?:job|position|role|work|clients?|contracts?|income)\b[^.]{0,60}\b"+AIW+r"\b"
 r"|\b"+AIW+r"\b[^.]{0,60}\b(?:took|taking|stole|stealing|killed|eliminated) (?:my|our|his|her|their|the) (?:job|work|role|position|clients|income|career)"
 r"|(?:laid off|let go|fired)\b[^.]{0,20}\b(?:because|since|after)\b[^.]{0,40}\b"+AIW+r"\b"
 r"|\b"+AIW+r"\b[^.]{0,40}\b(?:layoffs?|laid off|let go) (?:at|from|of) (?:my|our)"
 r"|(?:laid off|laying off|lays off|layoffs?|cut|cutting|fired|firing)\b[^.]{0,80}\b(?:automat\w+|replac\w+|substitut\w+)\w* (?:\w+ ){0,3}(?:with |by |using )?"+AIW+r"\b"
 r"|(?:gutted|replaced|cut|eliminated)\b[^.]{0,40}\b(?:team|department|staff|designers|writers|agents|engineers)\b[^.]{0,60}\b(?:AI|prompts?|chat ?gpt)\b"
 r"|laid off\b[^.]{0,60}\bto hire\b[^.]{0,40}\bAI\b"
 r"|(?:layoffs?|laid off|let go)\b[^.]{0,60}\b"+AIW+r"\b[^.]{0,60}\b(?:my|our|I was|I got|we were)\b", re.I)
HW=r"(?:resumes?|résumés?|CVs?|ATS|applicant tracking|applicants?|applications?|screen\w*|interview\w*|recruiters?|hiring process|candidates?|job posts?|job postings|ghost\w*|cover letters?|rejections?|rejected|auto-?reject\w*)"
HIRING2=re.compile(r"\b"+AIW+r"\b[^.]{0,60}\b"+HW+r"\b|\b"+HW+r"\b[^.]{0,60}\b"+AIW+r"\b|\bbots?\b[^.]{0,40}\b"+HW+r"\b|\b"+HW+r"\b[^.]{0,40}\bbots?\b",re.I)
FEAR=re.compile(
 r"(?:will|would|could|can|going to|gonna|about to|might|may|is|are) "+AIW+r"\b[^.]{0,40}\b(?:replace|take|steal|eliminat|destroy|kill|wipe|automate|displace|come for|end)"
 r"|\b(?:replace|replacing|take|taking|steal|eliminate|destroy|wipe out|displace|automate|automating)\b[^.]{0,40}\b(?:our|my|your|their|all|most|many|these|the|white.collar|entry.level|junior)\b[^.]{0,20}\b(?:jobs?|careers?|work|workers|roles|positions|workforce|developers|engineers|programmers|writers|designers)"
 r"|\b(?:worried|worry|scared|afraid|anxious|anxiety|terrified|fear|fears|nervous|concerned|doomed|obsolete|screwed|uncertain|dread|hopeless|existential)\b[^.]{0,80}\b"+AIW+r"\b"
 r"|\b"+AIW+r"\b[^.]{0,80}\b(?:worried|worry|scared|afraid|anxious|terrified|fear|nervous|doomed|obsolete|screwed|future of|dread|hopeless|threat\w*|existential)\b"
 r"|AI.proof|safe from AI|threatened by AI|should I (?:still )?(?:go|study|major|pursue|switch|learn|become)"
 r"|job (?:market|loss(?:es)?|displacement|apocalypse|security)\b[^.]{0,60}\b"+AIW+r"\b|\b"+AIW+r"\b[^.]{0,60}\bjob (?:loss(?:es)?|displacement|security|apocalypse)"
 r"|entry.level\b[^.]{0,60}\b"+AIW+r"\b|\b"+AIW+r"\b[^.]{0,60}\bentry.level"
 r"|\b"+AIW+r"\b[^.]{0,60}\b(?:take over|takeover|take jobs|take our jobs|taking jobs|replace\w*|obsolete|displac\w+)\b",re.I)
TOOL2=re.compile(r"\b(?:at work|my job|my boss|my manager|my company|my employer|coworkers?|colleagues?|my team|our team|the office|workplace|my role|management|leadership)\b[^.]{0,80}\b"+AIW+r"\b|\b"+AIW+r"\b[^.]{0,80}\b(?:at work|my job|my boss|my manager|my company|my employer|coworkers?|colleagues?|my team|our team|the office|workplace|my role|mandate\w*|productivity|workflow|headcount|output)\b",re.I)
FEAR_STRONG=re.compile(
 r"(?:will|would|could|can|going to|gonna|about to|might|may|is|are|to) "+AIW+r"\b[^.]{0,40}\b(?:replace|take|steal|eliminat|destroy|kill|wipe|automate|displace|come for|end)"
 r"|\b(?:replace|replacing|take|taking|steal|eliminate|destroy|wipe out|displace|automate|automating)\b[^.]{0,40}\b(?:our|my|your|their|all|most|many|these|the|white.collar|entry.level|junior)\b[^.]{0,20}\b(?:jobs?|careers?|work|workers|roles|positions|workforce|developers|engineers|programmers|writers|designers)"
 r"|coming for (?:your|our|my|their|all|every)\b[^.]{0,20}\b(?:jobs?|careers?)|AI.proof|safe from AI|threatened by AI|\b"+AIW+r"\b[^.]{0,40}\b(?:take over|takeover|replace\w*|obsolete|displac\w+)\b",re.I)

HIRING_FIRST=re.compile(r"\bAI (?:interview\w*|recruiter\w*|screen\w*|phone|hiring|resume|rejection|hr)\b|\b(?:interview|screen\w*|recruit\w*)\b[^.]{0,20}\bwith (?:an? |their )?AI\b|\bresumes? (?:got )?(?:rejected|filtered|screened)\b[^.]{0,30}\bAI",re.I)

HYPO=re.compile(r"\b(?:will|would|could|can|cannot|can't|might|may|going to|gonna|if|when|should|whether|think|thinks|thought|believe|predict\w*|soon|eventually|someday|about to|want|wants|how|why|what|do you|does|is it|are we|are you)\b[^.]{0,50}$",re.I)
def actual_match(t):
    title=t.split(' . ')[0]
    if title.strip().endswith('?'): return None
    for m in ACTUAL2.finditer(t):
        pre=t[max(0,m.start()-50):m.start()]
        # restrict lookback to the current sentence
        pre=re.split(r"[.!?\n]",pre)[-1]
        if HYPO.search(pre+' '): continue
        if re.search(r"\b(?:will|would|could|might|may|going to|gonna|can)\b",m.group(0)[:40],re.I): continue
        return m
    return None

ACTUAL3=re.compile(
 r"\b(?:I|we|I've|I was|we were|my \w+|our \w+)\b[^.]{0,30}\b(?:was|were|got|been|am|are|get)?\s*(?:laid off|let go|fired|replaced|made redundant|terminated|downsized|displaced|axed|cut)\b[^.]{0,60}\b(?:because of|due to|thanks to|by|with|after|over|replacing|in favou?r of)\b[^.]{0,12}\b"+AIW+r"\b"
 r"|\b"+AIW+r"\b[^.]{0,50}\b(?:replaced|took|taking|eliminated|stole|killed|ended)\b[^.]{0,5}\b(?:me|my (?:\w+ ){0,2}(?:job|role|position|work|career|team|department|clients|income|business)|us|our (?:team|jobs?|department|work))\b"
 r"|\b(?:replaced|replace|replacing|lost|losing|laid off|let go)\b[^.]{0,15}\b(?:me|my (?:job|role|position|work|team|department|clients|income))\b[^.]{0,40}\b(?:with|by|to|because of|due to|for)\b[^.]{0,10}\b"+AIW+r"\b"
 r"|\b(?:my|our|his|her|their|friend's|colleague's|coworker's|sister's|brother's|husband's|wife's|dad's|mom's|partner's)\s+(?:company|employer|boss|firm|agency|team|department|workplace|office|school|hospital|store)\b[^.]{0,60}\b(?:replaced|laid off|let go|fired|cut|eliminated|got rid of|downsized|automated)\b[^.]{0,80}\b(?:with|by|for|because of|due to|to)\b[^.]{0,15}\b"+AIW+r"\b"
 r"|\b(?:replaced|laid off|let go|fired)\b[^.]{0,30}\b(?:because|since|after)\b[^.]{0,30}\b"+AIW+r"\b"
 r"|\b(?:lost|losing) (?:my|his|her|their) (?:job|position|role|work|clients?|contracts?|income|career)\b[^.]{0,30}\b(?:to|because of|due to|thanks to)\b[^.]{0,10}\b"+AIW+r"\b"
 r"|(?:laid off|let go|fired)\b[^.]{0,60}[.!]\s*(?:Replaced|Fired|Cut|Let go)\b[^.]{0,20}\b"+AIW+r"\b"
 r"|\b(?:made redundant|redundancy|laid off)\b[^.]{0,60}\b(?:automation|AI)\b",re.I)
NEGACT=re.compile(r"\bnot (?:due to|because of|from|by) (?:AI|automation)\b|\bwasn'?t (?:due to|because of|from|by) AI\b|\bwill (?:be )?(?:replaced|laid off)|\bcould (?:be )?(?:replaced|laid off)|\bgoing to (?:be )?(?:replaced|laid off)|\bif (?:I|we)\b|\bnot been (?:replaced|laid off)",re.I)
def actual_match(t):
    title=t.split(' . ')[0]
    if title.strip().endswith('?'): return None
    for m in ACTUAL3.finditer(t):
        pre=re.split(r"[.!?\n]",t[max(0,m.start()-60):m.start()])[-1]
        if HYPO.search(pre+' '): continue
        ctx=t[max(0,m.start()-20):m.end()+40]
        if NEGACT.search(ctx): continue
        return m
    return None
