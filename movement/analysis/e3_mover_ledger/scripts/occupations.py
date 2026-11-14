"""Regex rules that normalize Indeed job titles into common lower-wage occupation groups.

Applied to the lower-cased job_title, first match wins (order matters). A title that matches EXCLUDE
(management / supervisory / licensed or senior roles) is never assigned. SOC codes are the BLS OEWS
occupations used for the out-of-state wage comparison.
"""
import re
import pandas as pd

EXCLUDE = re.compile(
    r"\b(manager|mgr|supervisor|director|superintendent|lead|leader|coordinator|instructor|trainer|"
    r"administrator|owner|chief|head|executive|recruiter|scheduler|educator|"
    r"rn|lvn|registered nurse|vocational nurse|pharmacist|physician|sous|chef de|"
    r"engineer|engineering|software|developer|analyst|reporter|cyber|cybersecurity|information|attorney|isso|program)\b")

OCC_RULES = [
    # key, label, SOC (OEWS), include regex
    ("cna", "CNA / nursing assistant", "311131",
     r"\bc\.?n\.?a\b|certified nurs(e|ing) assistant|nursing assistant|nurse aide|nursing aide|patient care (tech|assistant)"),
    ("caregiver", "Caregiver / home health aide", "311120",
     r"caregiver|care giver|home health aide|\bhha\b|personal care (aide|assistant|attendant)|in-home care|direct support professional|\bdsp\b"),
    ("med_asst", "Medical assistant", "319092",
     r"medical assistant|\bm\.?a\.?\b.*(clinic|medical)|back office assistant"),
    ("pharm_tech", "Pharmacy technician", "292052",
     r"pharmacy tech|pharmacy technician|\bcpht\b"),
    ("warehouse", "Warehouse / material handler", "537062",
     r"warehouse|picker|packer|material handler|forklift|order (selector|filler|picker)|freight|receiving associate|"
     r"shipping (and|&) receiving|loader|unloader|stocker|stock associate|inventory associate|fulfillment associate"),
    ("janitor", "Janitor / custodian / housekeeper", "372011",
     r"janitor|custodian|custodial|cleaner|housekeep|\bporter\b|environmental services (tech|aide|associate|worker)|\bevs\b"),
    ("security", "Security guard", "339032",
     r"security (officer|guard|agent|professional)|\bguard\b|patrol officer"),
    ("cook", "Cook", "352014",
     r"\bcook\b|line cook|prep cook|kitchen (team|staff|helper|associate)"),
    ("crew", "Fast-food / restaurant crew", "353023",
     r"crew (team )?member|\bcrew\b|dishwasher|busser|food service worker|barista|counter (help|attendant)"),
    ("cashier", "Cashier / retail sales", "412031",
     r"cashier|sales associate|retail associate|store associate|retail sales|sales floor|customer service associate"),
    ("driver", "Delivery driver", "533033",
     r"^(?!.*\b(class a|cdl|truck|bus|otr|tractor|flatbed)\b).*(delivery driver|driver helper|courier|\bdriver\b)"),
]
_COMPILED = [(k, l, s, re.compile(r)) for k, l, s, r in OCC_RULES]
LABELS = {k: l for k, l, _, _ in OCC_RULES}
SOC = {k: s for k, _, s, _ in OCC_RULES}


def classify(title: str):
    if not isinstance(title, str):
        return None
    t = title.lower()
    if EXCLUDE.search(t):
        return None
    for k, _, _, rx in _COMPILED:
        if rx.search(t):
            return k
    return None


def classify_series(s: pd.Series) -> pd.Series:
    return s.map(classify)
