"""Regex text flags on the CURRENT listing description / special_offer (shared by s04 and the hand check)."""
import re, numpy as np
REMODEL = re.compile(r"\b(remodel(?:ed|ing)?|renovat(?:ed|ion|ions)|newly (?:updated|upgraded|refreshed|remodeled|renovated)"
                     r"|fully updated|upgraded (?:kitchen|bath|unit|home|apartment|finishes|throughout)|brand[- ]new (?:kitchen|appliances|floors?|flooring|bath\w*|cabinets|countertops)"
                     r"|new (?:stainless(?: steel)? )?appliances|new (?:flooring|floors|carpet|cabinets|countertops|kitchen))\b", re.I)
LUXURY = re.compile(r"\bluxur(?:y|ious)\b", re.I)
NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "a": 1, "half a": 0.5, "half": 0.5}
WEEKS = re.compile(r"\b(\d{1,2}|one|two|three|four|five|six|seven|eight)\s*(?:\+\s*)?weeks?\s+(?:of\s+)?(?:free|off|rent[- ]free)", re.I)
MONTHS = re.compile(r"\b(\d(?:\.\d)?|one|two|three|half a|half|a)\s*months?(?:'s)?\s+(?:of\s+)?(?:free|off|rent[- ]free|free rent)", re.I)
FIRSTMONTH = re.compile(r"\b(?:first|1st) month(?:'s)?\s+(?:rent\s+)?(?:free|off)\b", re.I)

def _v(s):
    s = s.lower(); return float(NUM[s]) if s in NUM else float(s)

def concession_weeks(text):
    """Largest stated free-rent concession in weeks (1 month = 52/12 weeks); NaN if none. 'Up to' is taken at face value."""
    if not isinstance(text, str): return np.nan
    w = [_v(m.group(1)) for m in WEEKS.finditer(text)]
    w += [_v(m.group(1)) * 52 / 12 for m in MONTHS.finditer(text)]
    if FIRSTMONTH.search(text): w.append(52 / 12)
    w = [x for x in w if 0 < x <= 13]
    return max(w) if w else np.nan

def flag(pat, text):
    return bool(isinstance(text, str) and pat.search(text))
