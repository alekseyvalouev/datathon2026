"""Step 2 (Indeed): flag relocation offers, degree mentions, remote/hybrid and a broad
occupation group for every posting. Reuses E3's cleaned postings (parsed hourly pay,
county/metro/area, low-wage occupation groups) and joins description/benefits from the
shared Indeed DuckDB (read-only). Writes data/postings_flags.parquet."""
import re

import duckdb
import numpy as np
import pandas as pd

from e7common import DATA, E3, INDEED_DB

# --- relocation -------------------------------------------------------------
# positive phrases: an offer of relocation help/money
RELO_POS = re.compile(
    r"relocation (assistance|package|bonus|stipend|support|reimbursement|benefits?|allowance|"
    r"expenses?|assist\w*|incentive|pay|funds?|money|offered|available|provided|is available|"
    r"is offered|is provided|may be (available|offered|provided|considered)|negotiable|"
    r"(will be|can be|could be) (offered|provided|considered)|options?)|"
    r"(assistance|help|support|reimburse\w*|paid|offer\w*|provide\w*|includ\w*) (with |for )?relocation|"
    r"paid relocation|\brelo (package|assistance|bonus|stipend)|sign[- ]on and relocation|"
    r"relocation and sign[- ]on|eligible for[^.;\n]{0,80}relocation|relocation or living|moving (expenses?|allowance|stipend|assistance) (paid|reimburs\w*|provided|offered|available)",
    re.I)
# negations in the same sentence as 'relocation'
RELO_NEG = re.compile(
    r"\b(no|not|without|unable to|cannot|can't|won't|doesn't|does not|do not|don't|isn't|is not|"
    r"neither|nor|unavailable|ineligible|n't)\b[^.;\n]{0,50}relocat|"
    r"relocat\w*[^.;\n]{0,50}\b(is not|isn't|are not|not (be )?(available|offered|provided|"
    r"eligible|considered|included|authorized)|unavailable|will not|won't|cannot|not an option)\b|"
    r"relocat\w*( \w+){0,2}\s*[:\-]?\s*(no|none|n/a)\b", re.I)
SENT = re.compile(r"(?<=[.!?;\n•])\s+")


def relocation_flag(desc: str, benefits: str) -> tuple[int, str]:
    """1 if the posting offers relocation help (structured benefit tag, or an un-negated
    positive phrase in the description). Returns (flag, source)."""
    if desc:  # field-style "Relocation expenses reimbursed\nNo": join the answer to its field
        desc = re.sub(r"\s*\n\s*(?=(no|none|n/a|not)\b)", " ", desc, flags=re.I)
    sents = SENT.split(desc) if desc and "relocat" in desc.lower() else []
    neg = [s for s in sents if RELO_NEG.search(s)]
    pos = [s for s in sents if RELO_POS.search(s) and not RELO_NEG.search(s)]
    if benefits and "relocation assistance" in benefits.lower():
        # structured tag, unless the text explicitly says no and never offers it
        return (0, "") if (neg and not pos) else (1, "benefits_tag")
    if pos:
        return 1, "description"
    return 0, ""


COND = re.compile(r"\b(may|might|possible|possibly|eligible|if (applicable|needed|eligible)|as needed|"
                  r"based on|certain|considered|select|depending|for those|qualif\w+)\b", re.I)


def relocation_conditional(desc: str) -> int:
    """1 if every relocation-offer sentence is hedged (may / might / eligible / based on ...)."""
    if not desc or "relocat" not in desc.lower():
        return 0
    pos = [s for s in SENT.split(desc) if RELO_POS.search(s) and not RELO_NEG.search(s)]
    return int(bool(pos) and all(COND.search(s) for s in pos))


# --- degree mentions ---------------------------------------------------------
DEG = {
    "phd": re.compile(r"\bph\.? ?d\b|doctorate|doctoral degree", re.I),
    "masters": re.compile(r"master'?s|\bm\.?s\.? (degree|in)\b|\bmba\b", re.I),
    "bachelors": re.compile(r"bachelor'?s|\bb\.?[as]\.? (degree|in)\b|\bbs/ba\b|\bba/bs\b|"
                            r"four[- ]year degree|4[- ]year degree|undergraduate degree|college degree", re.I),
}
REQ = re.compile(r"requir|must have|minimum|\bmin\.? qualif|basic qualif", re.I)


def degree_level(desc: str) -> tuple[str, int]:
    """Highest degree mentioned anywhere in the description, and whether any degree
    mention sits in a sentence with 'required/minimum/must have'."""
    if not desc:
        return "none", 0
    lvl = "none"
    for k in ("bachelors", "masters", "phd"):
        if DEG[k].search(desc):
            lvl = k
    req = 0
    if lvl != "none":
        for s in SENT.split(desc):
            if any(rx.search(s) for rx in DEG.values()) and REQ.search(s):
                req = 1
                break
    return lvl, req


# --- broad occupation group (title regex, first match wins) -------------------
# E3's 10 low-wage groups (+ pharm tech) are taken as-is; the rest are classified here.
BROAD = [
    ("tech_software_data", r"software|developer|\bswe\b|data scien|data engineer|machine learning|"
     r"\bml\b|\bai\b|devops|\bsre\b|site reliability|cloud|full[- ]?stack|back[- ]?end|front[- ]?end|"
     r"\bios\b|android|security engineer|product manager|product designer|ux|ui designer|"
     r"research scientist|programmer|it (support|specialist|administrator)|network|systems admin|"
     r"database|analytics engineer|platform engineer|infrastructure"),
    ("physician_clinician", r"physician|\bmd\b|doctor|psychiatrist|pharmacist|nurse practitioner|"
     r"\bnp\b|physician assistant|\bpa-c\b|dentist|\bdds\b|surgeon|anesthesi|radiologist|"
     r"hospitalist|optometrist|veterinarian|\bdvm\b|psychologist"),
    ("nurse_rn_therapist", r"registered nurse|\brn\b|\bnurse\b|therapist|\blvn\b|\blpn\b|"
     r"pharmacy tech|respiratory|sonograph|radiolog|technologist|dietitian|social worker|counselor"),
    ("engineering_science", r"engineer|scientist|chemist|biolog|research associate|lab(oratory)? "
     r"(tech|associate)|architect\b|designer"),
    ("education", r"teacher|professor|instructor|tutor|faculty|educat|lecturer|paraeducator|"
     r"teaching|preschool|childcare|child care"),
    ("management", r"manager|director|\bvp\b|vice president|head of|chief|supervisor|"
     r"superintendent|\blead\b|principal"),
    ("business_finance_legal", r"analyst|accountant|accounting|finance|financial|attorney|lawyer|"
     r"paralegal|legal|consultant|recruiter|human resources|\bhr\b|marketing|bookkeep|auditor|"
     r"underwriter|actuar|coordinator|administrator|administrative|assistant|clerk|receptionist|"
     r"office"),
    ("sales_customer", r"sales|account executive|account manager|customer|representative|"
     r"\brep\b|banker|teller|agent|advisor"),
    ("trades_technicians", r"electrician|plumber|hvac|mechanic|technician|welder|maintenance|"
     r"carpenter|operator|installer|machinist|construction|laborer|painter|apprentice|"
     r"lineman|inspector"),
]
BROAD = [(k, re.compile(v, re.I)) for k, v in BROAD]


def broad_occ(title: str, e3_occ) -> str:
    if isinstance(e3_occ, str) and e3_occ:
        return "lowwage_service_E3"
    t = title or ""
    for k, rx in BROAD:
        if rx.search(t):
            return k
    return "other"


def pay_tier(h):
    if not np.isfinite(h):
        return "no_pay"
    if h < 25:
        return "<$25"
    if h < 40:
        return "$25-40"
    if h < 60:
        return "$40-60"
    return "$60+"


def main():
    p = pd.read_parquet(E3 / "outputs" / "postings_with_pay.parquet",
                        columns=["jobid", "company_name", "job_title", "job_type", "job_location",
                                 "pay_mid", "pay_hourly", "pay_imputed", "county", "metro", "area",
                                 "occ"])
    con = duckdb.connect(str(INDEED_DB), read_only=True)
    d = con.execute("select jobid, description_text, benefits from i").df()
    p = p.merge(d, on="jobid", how="left")
    print("rows", len(p))
    rf = [relocation_flag(a, b) for a, b in zip(p.description_text, p.benefits)]
    p["relo"] = [x[0] for x in rf]
    p["relo_source"] = [x[1] for x in rf]
    p["relo_conditional"] = [relocation_conditional(d) if f else 0
                             for d, f in zip(p.description_text, p.relo)]
    p["relo_firm"] = ((p.relo == 1) & (p.relo_conditional == 0)).astype(int)
    p["relo_any_mention"] = p.description_text.fillna("").str.contains("relocat", case=False) | \
        p.benefits.fillna("").str.contains("relocat", case=False)
    dl = [degree_level(x) for x in p.description_text]
    p["degree"] = [x[0] for x in dl]
    p["degree_req_sentence"] = [x[1] for x in dl]
    p["degree_any"] = (p.degree != "none").astype(int)
    jl = p.job_location.fillna("").str.lower()
    p["work_mode"] = np.where(jl.str.startswith("remote"), "remote",
                              np.where(jl.str.startswith("hybrid"), "hybrid", "onsite_or_unstated"))
    p["occ_broad"] = [broad_occ(t, o) for t, o in zip(p.job_title, p.occ)]
    p["region"] = np.where(p.metro == "Bay Area", "Bay Area",
                           np.where(p.metro == "Unknown", "Unknown", "Rest of CA"))
    p["pay_tier"] = [pay_tier(h) for h in p.pay_mid.astype(float)]
    p["pay_tier_imputed"] = [pay_tier(h) for h in p.pay_hourly.astype(float)]
    keep = [c for c in p.columns if c not in ("benefits",)]
    p[keep].to_parquet(DATA / "postings_flags.parquet", index=False)
    print(p.relo.sum(), p.relo_firm.sum(), p.relo_source.value_counts().to_dict(), p.relo_any_mention.sum())


if __name__ == "__main__":
    main()
