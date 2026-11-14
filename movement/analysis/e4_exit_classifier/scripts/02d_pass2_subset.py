"""Step 2d: choose the 100-item subset for the second, blind labeling pass and write
it (text only, no pass-1 labels) to labels/pass2_items.txt.
Composition: 40 pass-1 positives + 60 pass-1 OTHER (30 regex tier A/B/enrichment
hard negatives + 30 others), shuffled. Pass-1 labels are not in the file."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from annot_tools import snippet  # noqa: E402
from common import LABELS  # noqa: E402

s = pd.read_csv(LABELS / "sample_to_label.csv")
l1 = pd.read_csv(LABELS / "labels_pass1.csv")
d = s.reset_index().rename(columns={"index": "idx"}).merge(l1[["item_id", "label"]], on="item_id")
d["norm"] = d.text.str.lower().str.replace(r"\W+", " ", regex=True).str.strip()
d = d.drop_duplicates("norm")
pos = d[d.label != "OTHER"].sample(40, random_state=1)
neg = d[d.label == "OTHER"]
hard = neg[(neg.tier.isin(["A", "B"])) | (neg["round"] > 1)].sample(30, random_state=1)
rest = neg.drop(hard.index).sample(30, random_state=1)
sub = pd.concat([pos, hard, rest]).sample(frac=1, random_state=2)
sub[["idx", "item_id"]].to_csv(LABELS / "pass2_subset_ids.csv", index=False)
with open(LABELS / "pass2_items.txt", "w") as f:
    for _, r in sub.iterrows():
        f.write(f"[{r.idx}] r/{r['sub']} {r.kind} | T: {str(r.thread_title)[:90]}\n   {snippet(r.text)}\n")
print(len(sub))
