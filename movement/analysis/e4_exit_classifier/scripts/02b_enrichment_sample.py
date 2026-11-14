"""Step 2b: positive-enrichment round. Round 1 (random stratified) produced only ~10%
positives, too few to train/evaluate 3 classes. Round 2 draws items matching a
stricter first-person exit pattern (not already sampled), stratified by group x kind,
and appends them to labels/sample_to_label.csv with round=2 and their own p_sample.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import DATA, LABELS  # noqa: E402

RE_ENRICH = re.compile(
    r"\b(i|we|my (wife|husband|partner|family)|our family|i've|we've|i'm|we're)\b[^.?!\n]{0,50}"
    r"\b(moved (to|out of|away)|moving (to|out of|away)|relocat\w+ to|left (the bay|sf|san francisco|"
    r"california|cali|ca\b|the state|the area|oakland|san jose)|leaving (the bay|sf|san francisco|"
    r"california|cali|ca\b|the state|the area)|priced out|out of state)", re.I)
SEED = 99
N = 170


def main():
    s = pd.read_csv(LABELS / "sample_to_label.csv")
    if "round" in s.columns and (s["round"] == 2).any():
        print("round 2 already drawn; refusing to redraw"); return
    s["round"] = 1
    pool = pd.read_parquet(DATA / "pool.parquet")
    cand = pool[~pool.item_id.isin(s.item_id) & pool.text.str.contains(RE_ENRICH)].copy()
    cand["stratum2"] = cand.group + "|" + cand.kind
    vc = cand.stratum2.value_counts()
    w = np.sqrt(vc.values.astype(float)); alloc = np.round(N * w / w.sum()).astype(int)
    parts = []
    for st, k in zip(vc.index, alloc):
        g = cand[cand.stratum2 == st]; k = min(k, len(g))
        parts.append(g.sample(n=k, random_state=SEED).assign(p_sample=k / len(g)))
    r2 = pd.concat(parts).sample(frac=1, random_state=SEED)
    r2["round"] = 2
    r2["stratum"] = "enrich|" + r2.stratum2
    cols = list(s.columns)
    out = pd.concat([s, r2[cols]], ignore_index=True)
    out.to_csv(LABELS / "sample_to_label.csv", index=False)
    print(vc.to_dict(), r2.groupby("stratum2").size().to_dict(), len(out))


if __name__ == "__main__":
    main()
