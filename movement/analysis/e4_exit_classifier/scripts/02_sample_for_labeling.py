"""Step 2: draw a stratified sample of the pool for annotation.

Strata = subreddit group x kind (post/comment) x regex tier:
  tier A: naive regex hit (the earlier ~271-post rule, now also on comments)
  tier B: first-person move language (I/we ... moved/left/moving/leaving/relocat...)
  tier C: everything else in the pool (hard negatives: move + place terms only)
Sampling probabilities are saved so pool-level estimates can be re-weighted.
Run once; the drawn sample (labels/sample_to_label.csv) is frozen afterwards.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import DATA, LABELS, RE_NAIVE, naive_rule  # noqa: E402

RE_FP = re.compile(r"\b(i|we|my (wife|husband|partner|family)|our family)\b[^.?!\n]{0,60}"
                   r"\b(moved|left|moving|leaving|relocat\w*|move|leave|priced out)\b", re.I)
SEED = 20261114
TARGET = {"A": 240, "B": 310, "C": 150}   # ~700 items


def tier(row):
    if naive_rule(row.text, row.group) != "OTHER":
        return "A"
    if RE_FP.search(row.text):
        return "B"
    return "C"


def main():
    if (LABELS / "sample_to_label.csv").exists():
        print("labels/sample_to_label.csv exists (frozen annotation sample); not redrawing")
        return
    pool = pd.read_parquet(DATA / "pool.parquet")
    pool["tier"] = pool.apply(tier, axis=1)
    pool["stratum"] = pool.group + "|" + pool.kind + "|" + pool.tier
    rng = np.random.default_rng(SEED)
    parts = []
    for t, n_t in TARGET.items():
        sub = pool[pool.tier == t]
        strata = sub.stratum.value_counts()
        # allocate within tier: sqrt-proportional (keeps small groups represented),
        # with bay_local up-weighted x1.5 because it has the highest positive rate
        w = np.sqrt(strata.values.astype(float))
        w *= np.array([1.5 if s.startswith("bay_local") else 1.0 for s in strata.index])
        alloc = np.minimum(strata.values, np.maximum(5, np.round(n_t * w / w.sum()))).astype(int)
        for s, k in zip(strata.index, alloc):
            g = sub[sub.stratum == s]
            k = min(k, len(g))
            pick = g.sample(n=k, random_state=int(rng.integers(1e9)))
            pick = pick.assign(p_sample=k / len(g))
            parts.append(pick)
    samp = pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)
    pool.to_parquet(DATA / "pool.parquet", index=False)  # now with tier/stratum
    cols = ["item_id", "kind", "sub", "group", "date", "tier", "stratum", "p_sample",
            "thread_title", "text"]
    samp[cols].to_csv(LABELS / "sample_to_label.csv", index=False)
    print(samp.groupby(["group", "kind", "tier"]).size(), len(samp))
    print(pool.groupby(["group", "kind", "tier"]).size())


if __name__ == "__main__":
    main()
