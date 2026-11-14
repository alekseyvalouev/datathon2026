"""Annotation helpers (used by the LLM annotator; not needed to re-run the pipeline).
  python annot_tools.py show START END
Label lines live in labels/raw/*.txt, format (one per item):
  idx|label|reasons|household|era|origin|dest|occ|money
  label: A=ARRIVED P=PLANNING W=within-Bay move O=OTHER
  reasons (letters): t=tech/startup job j=other job/transfer/residency s=school p=partner/family
                     l=lifestyle/culture/weather c=return home o=other ; empty = none stated
  household: s=single c=couple f=family with kids r=roommates u=unknown
  era: n=recent (<=5y or 'just/recently'/planning) a=long ago (>5y) u=unknown
  origin: us=other US state ca=elsewhere in CA ab=abroad u=unknown
  dest: Bay city/neighborhood as written (normalised), empty if none
  occ: t=tech h=healthcare a=academic/student s=service/trades/hourly f=finance/law/other prof u=unknown
  money: stated salary / budget, e.g. 'sal 180k' or 'rent 3000' or 'tc 300k'; empty if none
"""
import re
import sys

import pandas as pd

from e7common import LABELS, RE_A, RE_B_PLACE, RE_B_IMPLICIT, RE_C


def snippet(text, width=520):
    text = re.sub(r"\s+", " ", text or "")
    if len(text) <= width:
        return text
    m = RE_A.search(text) or RE_B_PLACE.search(text) or RE_B_IMPLICIT.search(text) or RE_C.search(text)
    start = max(0, (m.start() if m else 0) - width // 4)
    return ("..." if start else "") + text[start:start + width] + "..."


def show(a, b):
    s = pd.read_csv(LABELS / "sample_to_label.csv")
    for i in range(a, min(b, len(s))):
        r = s.iloc[i]
        print(f"[{i}] r/{r['sub']} {r.kind} | T: {str(r.thread_title)[:80]}")
        print("   " + snippet(r.text))


if __name__ == "__main__":
    if sys.argv[1] == "show":
        show(int(sys.argv[2]), int(sys.argv[3]))
