"""Step 2c: second enrichment round with a high-precision exit pattern (round 2 was
still only ~15% positive). Appends ~110 items with round=3 to labels/sample_to_label.csv."""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import DATA, LABELS  # noqa: E402

DEST = (r"(sacramento|sac\b|stockton|tracy|manteca|modesto|fresno|central valley|roseville|"
        r"texas|tx\b|austin|dallas|houston|arizona|az\b|phoenix|nevada|reno|vegas|las vegas|"
        r"oregon|portland|washington|seattle|idaho|boise|colorado|denver|utah|florida|"
        r"north carolina|tennessee|nashville|georgia|atlanta|ohio|chicago|new york|nyc|"
        r"the east coast|the midwest|the south|another state|out of state|a cheaper state|"
        r"europe|mexico|japan|portugal|canada)")
RE_STRONG = re.compile(
    r"\b(i|we|my (wife|husband|partner|family) and i)\b[^.?!\n]{0,30}\b("
    r"(moved|relocated|left|moving|relocating|are moving|am moving) (from (the bay|sf|san francisco|"
    r"oakland|san jose|the bay area|california|ca\b|cali)[^.?!\n]{0,20} )?to " + DEST + r"|"
    r"left (the bay|the bay area|california|cali|sf|san francisco)|"
    r"(moved|moving) out of (the bay|the bay area|california|cali|state|sf|san francisco)|"
    r"leaving (the bay|the bay area|california|cali|sf|san francisco))", re.I)
SEED = 123
N = 110


def main():
    s = pd.read_csv(LABELS / "sample_to_label.csv")
    if (s["round"] == 3).any():
        print("round 3 already drawn"); return
    pool = pd.read_parquet(DATA / "pool.parquet")
    cand = pool[~pool.item_id.isin(s.item_id) & pool.text.apply(lambda t: bool(RE_STRONG.search(t)))].copy()
    cand["stratum2"] = cand.group + "|" + cand.kind
    vc = cand.stratum2.value_counts()
    w = np.sqrt(vc.values.astype(float)); alloc = np.maximum(4, np.round(N * w / w.sum())).astype(int)
    parts = []
    for st, k in zip(vc.index, alloc):
        g = cand[cand.stratum2 == st]; k = min(k, len(g))
        parts.append(g.sample(n=k, random_state=SEED).assign(p_sample=k / len(g)))
    r3 = pd.concat(parts).sample(frac=1, random_state=SEED)
    r3["round"] = 3; r3["stratum"] = "enrich3|" + r3.stratum2
    out = pd.concat([s, r3[list(s.columns)]], ignore_index=True)
    out.to_csv(LABELS / "sample_to_label.csv", index=False)
    print(vc.to_dict(), r3.stratum2.value_counts().to_dict(), len(out))


if __name__ == "__main__":
    main()
