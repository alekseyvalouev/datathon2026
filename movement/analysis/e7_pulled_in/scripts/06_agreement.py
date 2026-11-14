"""Step 6: agreement between pass-1 labels and the blind pass-2 labels (separate fresh-context
LLM instance, main label only, 80 items)."""
import json

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from e7common import LABELS, OUT

LAB = dict(A="ARRIVED", P="PLANNING", W="WITHIN_BAY", O="OTHER")


def main():
    p1 = pd.read_csv(LABELS / "labels_pass1.csv")[["idx", "label"]]
    rows = [l.split("|") for l in (LABELS / "raw" / "pass2_blind.txt").read_text().split()
            if "|" in l]
    p2 = pd.DataFrame([(int(a), LAB[b.strip()]) for a, b in rows], columns=["idx", "label2"])
    m = p1.merge(p2, on="idx")
    m["bin1"] = m.label.isin(["ARRIVED", "PLANNING"])
    m["bin2"] = m.label2.isin(["ARRIVED", "PLANNING"])
    res = dict(n=len(m), raw_agreement_4class=float((m.label == m.label2).mean()),
               kappa_4class=float(cohen_kappa_score(m.label, m.label2)),
               raw_agreement_arrival_vs_not=float((m.bin1 == m.bin2).mean()),
               kappa_arrival_vs_not=float(cohen_kappa_score(m.bin1, m.bin2)))
    pd.crosstab(m.label, m.label2).to_csv(OUT / "agreement_confusion.csv")
    m.to_csv(LABELS / "labels_pass2.csv", index=False)
    json.dump(res, open(OUT / "intra_annotator_agreement.json", "w"), indent=1)
    print(res)
    print(pd.crosstab(m.label, m.label2))


if __name__ == "__main__":
    main()
