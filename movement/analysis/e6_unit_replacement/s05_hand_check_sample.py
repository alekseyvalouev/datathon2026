"""Step 5: draw the regex hand-check sample (20 per text variable, seed 42). Writes outputs/hand_check_text_sample.csv with
a short window around the match (house numbers masked; no addresses). Verdicts were assigned by reading every
snippet and are stored in hand_check_verdicts.csv (manual, same row order); s05 merges and reports precision."""
import os, re, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from textflags import *
from s02_income_gate import MULT_PAT, stated_mult

def snip(text, m, w=90):
    s = text[max(0, m.start() - w):m.end() + w].replace("\n", " ")
    return re.sub(r"\b\d{2,6}\s+([A-Z][a-z]+\s){1,3}(St|Ave|Blvd|Rd|Dr|Way|Ln|Ct|Pl|Street|Avenue|Road|Drive|Lane)\b", "[ADDR]", s)

def main():
    ex = pd.read_parquet(os.path.join(CACHE, "extra.parquet"))
    ex = ex[(ex.homeStatus == "FOR_RENT") & ex.county.isin(BAY.values())]
    ex = ex.drop_duplicates("description")   # floor-plan duplicates share text; check distinct texts
    rows = []
    for var, pat, col in [("remodel", REMODEL, "description"), ("luxury", LUXURY, "description"),
                          ("concession_weeks", None, "both"), ("income_multiplier", MULT_PAT, "description")]:
        if var == "concession_weeks":
            t = (ex.description.fillna("") + " || " + ex.special_offer.fillna(""))
            hit = t[t.map(concession_weeks).notna()]
        else:
            hit = ex[col][ex[col].map(lambda s: bool(isinstance(s, str) and pat.search(s)))]
        smp = hit.sample(20, random_state=SEED)
        for i, txt in smp.items():
            if var == "concession_weeks":
                ms = [m for p in (WEEKS, MONTHS, FIRSTMONTH) for m in p.finditer(txt)]
                m = ms[0]; val = concession_weeks(txt)
            else:
                m = pat.search(txt); val = stated_mult(txt) if var == "income_multiplier" else 1
            rows.append(dict(var=var, row=i, parsed_value=val, snippet=snip(txt, m)))
    out = pd.DataFrame(rows); out.to_csv(os.path.join(OUT, "hand_check_text_sample.csv"), index=False)
    vpath = os.path.join(HERE, "hand_check_verdicts.csv")
    if os.path.exists(vpath):
        v = pd.read_csv(vpath); assert len(v) == len(out) and (v["var"].values == out["var"].values).all()
        out["verdict"] = v.verdict.values; out["note"] = v.note.values
        prec = out.groupby("var").verdict.apply(lambda s: (s == "correct").mean()).rename("precision")
        out.to_csv(os.path.join(OUT, "hand_check_text.csv"), index=False); prec.to_csv(os.path.join(OUT, "hand_check_precision.csv"))
        print(prec)
    else:
        for r in out.itertuples(): print(f"[{r.Index}] {r.var} val={r.parsed_value} :: {r.snippet}")

if __name__ == "__main__":
    main()
