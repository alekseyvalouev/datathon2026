"""Rule-based reason-tag and destination extractors, applied to items the classifier
flags as LEFT/CONSIDERING. They are validated against the LLM-annotated gold labels
in 03_train_eval.py."""
import re

REASON_RX = {
    "housing_cost": r"\brent\b|rents\b|mortgage|home prices|house prices|housing (cost|price)|"
                    r"afford a (home|house)|buy a (home|house)|bought a (home|house)|priced out|evict|"
                    r"down ?payment|\bhome\b.{0,20}(cost|price|afford)",
    "jobs_wages": r"\bjob\b|\bjobs\b|laid off|layoff|salary|wages?\b|career|\bpay (cut|raise)|"
                  r"job offer|for work|residency|transfer|promotion|unemploy",
    "cost_of_living_other": r"cost of living|\bcol\b|\btax(es)?\b|gas prices|groceries|childcare|"
                            r"day ?care|expensive|insurance|bills",
    "family": r"(closer to|near|be with|take care of|care for|caring for)\b[^.]{0,20}"
              r"(family|parents?|mom|dad|in-laws|grand\w+|kids|daughter|son|brother|sister)|"
              r"\bfor family\b|family reasons|divorce|aging (mother|father|parents?)",
    "schools": r"school",
    "safety_quality_of_life": r"crime|unsafe|safety|homeless|traffic|commute|quality of life|"
                              r"politic|weather|smoke|fires?\b|car break|break-?ins?|drugs|"
                              r"burn(ed|t)? out|space|yard|slower pace|quiet",
    "remote_work": r"remote|work from home|\bwfh\b|work from anywhere",
}
REASON_RX = {k: re.compile(v, re.I) for k, v in REASON_RX.items()}

BAY_PLACES = (r"san francisco|\bsf\b|oakland|berkeley|san jose|fremont|hayward|richmond|vallejo|"
              r"antioch|concord|walnut creek|pleasanton|livermore|dublin|san ramon|brentwood|"
              r"pittsburg|daly city|san mateo|redwood city|palo alto|mountain view|sunnyvale|"
              r"santa clara|milpitas|gilroy|morgan hill|santa rosa|petaluma|napa|fairfield|"
              r"vacaville|novato|san rafael|alameda|east bay|south bay|north bay|peninsula|"
              r"marin|sonoma|solano|contra costa")
CV_PLACES = (r"sacramento|\bsac\b|roseville|rocklin|elk grove|folsom|davis|woodland|placer|"
             r"el dorado|auburn|stockton|tracy|manteca|lodi|modesto|turlock|merced|fresno|"
             r"visalia|bakersfield|central valley|mountain house|lathrop|ripon|yuba|chico|"
             r"san joaquin|los banos|clovis")
OTHER_CA = (r"los angeles|\bla\b|socal|southern california|san diego|orange county|irvine|"
            r"long beach|pasadena|riverside|inland empire|santa barbara|san luis obispo|"
            r"\bslo\b|monterey|santa cruz|salinas|tahoe|truckee|grass valley|nevada city|"
            r"redding|eureka|humboldt|mendocino|palm springs|temecula|ventura|central coast")
STATES = {
    "AL": "alabama", "AK": "alaska", "AZ": "arizona|phoenix|tucson|scottsdale",
    "AR": "arkansas", "CO": "colorado|denver|boulder|colorado springs",
    "CT": "connecticut", "DE": "delaware", "FL": "florida|miami|tampa|orlando",
    "GA": "georgia|atlanta", "HI": "hawaii|honolulu|maui", "ID": "idaho|boise",
    "IL": "illinois|chicago", "IN": "indiana|indianapolis", "IA": "iowa", "KS": "kansas",
    "KY": "kentucky|louisville", "LA": "louisiana|new orleans", "ME": "maine",
    "MD": "maryland|baltimore", "MA": "massachusetts|boston", "MI": "michigan|detroit",
    "MN": "minnesota|minneapolis", "MS": "mississippi", "MO": "missouri|st\\.? louis|kansas city",
    "MT": "montana", "NE": "nebraska|omaha", "NV": "nevada|reno|las vegas|\\bvegas|henderson",
    "NH": "new hampshire", "NJ": "new jersey", "NM": "new mexico|albuquerque",
    "NY": "new york|nyc|brooklyn", "NC": "north carolina|raleigh|charlotte|durham|asheville",
    "ND": "north dakota", "OH": "ohio|columbus|cleveland|cincinnati",
    "OK": "oklahoma", "OR": "oregon|portland|bend|eugene", "PA": "pennsylvania|philadelphia|pittsburgh",
    "RI": "rhode island", "SC": "south carolina", "SD": "south dakota",
    "TN": "tennessee|nashville|knoxville|memphis", "TX": "texas|austin|dallas|houston|san antonio",
    "UT": "utah|salt lake", "VT": "vermont", "VA": "virginia", "WA": "washington state|seattle|spokane|\\bpnw\\b",
    "WV": "west virginia", "WI": "wisconsin|milwaukee|madison", "WY": "wyoming",
    "DC": "washington,? dc|\\bdc\\b",
}
ABROAD = (r"mexico|canada|japan|portugal|spain|europe|germany|france|uk\b|england|london|"
          r"netherlands|philippines|vietnam|taiwan|china|india|korea|australia|new zealand|"
          r"costa rica|thailand|abroad|overseas|ireland|italy|singapore")

_PATTERNS = ([("sacramento_central_valley", None, re.compile(CV_PLACES, re.I)),
              ("other_ca", None, re.compile(OTHER_CA, re.I)),
              ("abroad", None, re.compile(ABROAD, re.I))]
             + [("out_of_state", st, re.compile(rx, re.I)) for st, rx in STATES.items()]
             + [("out_of_state", None, re.compile(
                 r"out of state|another state|new state|cheaper state|east coast|west virginia|"
                 r"midwest|the south\b|southeast|northeast|new england|red state|other states?", re.I))]
             + [("other_bay_county", None, re.compile(BAY_PLACES, re.I))])
RE_TO = re.compile(r"\b(mov(e|ed|ing)|relocat(e|ed|ing)|went|go(ing)?|left for|headed|"
                   r"bought a house|live|living|now in|out)\b[^.!?\n]{0,25}?\b(to|in)\b\s+", re.I)


RE_MOVEWORD = re.compile(r"\b(mov(e|ed|ing)|left|leav(e|ing)|relocat\w*|priced out|because|"
                         r"due to|reason|so we|so i|afford)\b", re.I)
RE_SENT = re.compile(r"(?<=[.!?\n])\s+")


def reason_window(text):
    """Sentences that mention moving/leaving (or a 'because'), plus the following sentence."""
    sents = RE_SENT.split(text or "")
    keep = set()
    for i, s in enumerate(sents):
        if RE_MOVEWORD.search(s):
            keep.update({i, i + 1})
    return " ".join(sents[i] for i in sorted(keep) if i < len(sents))


def reasons(text):
    w = reason_window(text)
    return [k for k, rx in REASON_RX.items() if rx.search(w)]


def destination(text):
    """Return (bucket, state). Prefer a place right after 'moved to / moving to';
    otherwise the earliest non-Bay place mentioned."""
    t = text or ""
    best = None
    for m in RE_TO.finditer(t):
        tail = t[m.end():m.end() + 40]
        for b, st, rx in _PATTERNS:
            mm = rx.match(tail) or (rx.search(tail[:25]) if b != "other_bay_county" else None)
            if mm:
                return b, st
    for b, st, rx in _PATTERNS:
        if b == "other_bay_county":
            continue
        mm = rx.search(t)
        if mm and (best is None or mm.start() < best[2]):
            best = (b, st, mm.start())
    return (best[0], best[1]) if best else ("unknown", None)
