"""Annotation helpers (used by the LLM annotator; not needed to rerun the pipeline).

  python annot_tools.py show START END [--blind2]   print items for reading
  python annot_tools.py compile                     compile labels/raw/*.txt -> labels/*.csv

Compact label line format (one per item, in labels/raw/pass1_*.txt / pass2_*.txt):
  <idx>|<L|C|O>|<reason codes>|<dest text>|<bucket code>|<state>|<within_bay 0/1>
reason codes: h=housing_cost j=jobs_wages c=cost_of_living_other f=family s=schools
              q=safety_quality_of_life r=remote_work o=other
bucket codes: b=other_bay_county v=sacramento_central_valley ca=other_ca os=out_of_state
              ab=abroad u=unknown
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import LABELS, RE_BAY, RE_MOVE  # noqa: E402

RC = dict(h="housing_cost", j="jobs_wages", c="cost_of_living_other", f="family",
          s="schools", q="safety_quality_of_life", r="remote_work", o="other")
BC = dict(b="other_bay_county", v="sacramento_central_valley", ca="other_ca",
          os="out_of_state", ab="abroad", u="unknown")
LC = dict(L="LEFT", C="CONSIDERING", O="OTHER")


def snippet(text, width=650):
    text = re.sub(r"\s+", " ", text or "")
    if len(text) <= width:
        return text
    m = RE_MOVE.search(text) or RE_BAY.search(text)
    start = max(0, (m.start() if m else 0) - width // 3)
    return ("..." if start else "") + text[start:start + width] + "..."


def show(a, b):
    s = pd.read_csv(LABELS / "sample_to_label.csv")
    for i in range(a, min(b, len(s))):
        r = s.iloc[i]
        print(f"[{i}] r/{r['sub']} {r.kind} | T: {str(r.thread_title)[:90]}")
        print("   " + snippet(r.text))


def compile_labels():
    s = pd.read_csv(LABELS / "sample_to_label.csv")
    for pas in ("pass1", "pass2"):
        rows = []
        for f in sorted((LABELS / "raw").glob(f"{pas}_*.txt")):
            for line in f.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                raw = [x.strip() for x in line.split("|")]
                p = (raw + [""] * 7)[:7]
                idx, lab, rc, dt, bc, st, _ = p
                wb = raw[-1] if len(raw) >= 7 else ""   # within_bay is always the last field
                lab = LC[lab]
                rows.append(dict(
                    idx=int(idx), label=lab,
                    reasons=";".join(RC[c] for c in rc.split(",") if c) if lab != "OTHER" else "",
                    dest_text=dt if lab != "OTHER" else "",
                    dest_bucket=(BC[bc] if bc else "unknown") if lab != "OTHER" else "",
                    dest_state=st, within_bay=int(wb or 0)))
        if not rows:
            continue
        d = pd.DataFrame(rows).drop_duplicates("idx", keep="last").sort_values("idx")
        d["item_id"] = s.item_id.values[d.idx.values]
        d.to_csv(LABELS / f"labels_{pas}.csv", index=False)
        print(pas, len(d), d.label.value_counts().to_dict())


if __name__ == "__main__":
    if sys.argv[1] == "show":
        show(int(sys.argv[2]), int(sys.argv[3]))
    else:
        compile_labels()
