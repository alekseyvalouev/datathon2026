"""Step 3: train/evaluate classifiers on the annotated sample.

Split: stratified 60/20/20 (train/val/test) by label, seed fixed, saved to labels/splits.csv.
Models: (a) naive regex rule, (b) majority class, (c) TF-IDF + LR,
        (d) frozen sentence embeddings (MiniLM-L6 / mpnet-base) + LR,
        (e) hybrid: TF-IDF + MiniLM embedding + 6 regex flags -> LR.
Model/C selection: 5-fold stratified CV on train+val (the val split alone was ~190 items
with ~25 positives, too noisy). Test (20%) is touched once at the end.
The chosen config is then refit on all labels and saved to data/final_model.pkl.
Also evaluates the rule-based reason/destination extractors against gold labels.
"""
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, cohen_kappa_score, confusion_matrix,
                             f1_score)
from sklearn.model_selection import StratifiedKFold, train_test_split

sys.path.insert(0, str(Path(__file__).parent))
from features import EMB_MODELS, Featurizer, embed, model_input  # noqa: E402
from common import CLASSES, DATA, LABELS, OUT, naive_rule  # noqa: E402
import extract  # noqa: E402

SEED = 7


def load_labeled():
    s = pd.read_csv(LABELS / "sample_to_label.csv")
    l1 = pd.read_csv(LABELS / "labels_pass1.csv").fillna("")
    d = s.merge(l1.drop(columns="idx"), on="item_id")
    # identical texts (cross-posted comments) are dropped so they cannot leak across splits
    d["norm"] = d.text.str.lower().str.replace(r"\W+", " ", regex=True).str.strip()
    n0 = len(d)
    d = d.drop_duplicates("norm").drop(columns="norm").reset_index(drop=True)
    print(f"labeled items: {n0}, after removing duplicate texts: {len(d)}")
    return d


def make_splits(d):
    f = LABELS / "splits.csv"
    if f.exists():
        sp = pd.read_csv(f)
        return d.merge(sp, on="item_id")
    tr, te = train_test_split(d.item_id, test_size=0.2, stratify=d.label, random_state=SEED)
    dd = d.set_index("item_id")
    tr, va = train_test_split(tr, test_size=0.25, stratify=dd.loc[tr].label, random_state=SEED)
    sp = pd.concat([pd.DataFrame({"item_id": tr, "split": "train"}),
                    pd.DataFrame({"item_id": va, "split": "val"}),
                    pd.DataFrame({"item_id": te, "split": "test"})])
    sp.to_csv(f, index=False)
    return d.merge(sp, on="item_id")


def binary(y):
    return np.where(np.asarray(y) == "OTHER", "OTHER", "EXIT")


CS = (0.1, 0.3, 1, 3, 10, 30)
LEARNED = ["tfidf", "emb_minilm", "emb_mpnet", "hybrid"]


def cv_select(kind, dev, E_dev):
    """5-fold stratified CV on train+val -> (best C, mean macro-F1). Test is never used."""
    skf = StratifiedKFold(5, shuffle=True, random_state=SEED)
    res = {C: [] for C in CS}
    for a, b in skf.split(dev.x, dev.label):
        fz = Featurizer(kind).fit(dev.x.iloc[a])
        Xa = fz.transform(dev.x.iloc[a].tolist(), E_dev[a] if E_dev is not None else None)
        Xb = fz.transform(dev.x.iloc[b].tolist(), E_dev[b] if E_dev is not None else None)
        for C in CS:
            m = LogisticRegression(C=C, max_iter=5000, class_weight="balanced").fit(Xa, dev.label.iloc[a])
            res[C].append(f1_score(dev.label.iloc[b], m.predict(Xb), average="macro"))
    best = max(res, key=lambda C: np.mean(res[C]))
    return best, float(np.mean(res[best])), float(np.std(res[best]))


def fit_final(kind, C, df, E):
    fz = Featurizer(kind).fit(df.x)
    m = LogisticRegression(C=C, max_iter=5000, class_weight="balanced").fit(
        fz.transform(df.x.tolist(), E), df.label)
    return fz, m


def main():
    d = make_splits(load_labeled())
    d["x"] = model_input(d)
    emb = {k: embed(d.x.tolist(), k, "labeled") for k in EMB_MODELS}
    dev_mask = (d.split != "test").values
    dev, te = d[dev_mask].reset_index(drop=True), d[~dev_mask].reset_index(drop=True)
    print({"dev(train+val)": len(dev), "test": len(te)}, d.label.value_counts().to_dict())
    preds, info = {}, {}
    maj = dev.label.mode()[0]
    preds["majority"] = (None, np.array([maj] * len(te)))
    preds["naive_regex"] = (None, np.array([naive_rule(t, g) for t, g in zip(te.text, te.group)]))
    info["naive_regex"] = dict(cv_macro_f1=f1_score(
        dev.label, [naive_rule(t, g) for t, g in zip(dev.text, dev.group)], average="macro"))
    info["majority"] = dict(cv_macro_f1=f1_score(dev.label, [maj] * len(dev), average="macro"))
    for kind in LEARNED:
        ek = "mpnet" if kind == "emb_mpnet" else "minilm"
        E_dev = emb[ek][dev_mask] if kind != "tfidf" else None
        C, f, sd = cv_select(kind, dev, E_dev)
        fz, m = fit_final(kind, C, dev, E_dev)
        pt = m.predict(fz.transform(te.x.tolist(), emb[ek][~dev_mask] if kind != "tfidf" else None))
        preds[kind] = (None, pt)
        info[kind] = dict(C=C, cv_macro_f1=f, cv_sd=sd)
        print(kind, info[kind])
    rename = {"tfidf": "tfidf_lr", "emb_minilm": "minilm_emb_lr", "emb_mpnet": "mpnet_emb_lr",
              "hybrid": "hybrid_tfidf+minilm+rx_lr"}
    rows = []
    for name, (pv, pt) in preds.items():
        rep = classification_report(te.label, pt, labels=CLASSES, output_dict=True, zero_division=0)
        rows.append(dict(
            model=rename.get(name, name), key=name,
            cv_macro_f1_dev=info[name]["cv_macro_f1"], C=info[name].get("C"),
            test_macro_f1=rep["macro avg"]["f1-score"],
            test_acc=rep["accuracy"],
            **{f"test_{c}_{k}": rep[c][k] for c in CLASSES for k in ("precision", "recall", "f1-score")},
            test_binary_exit_f1=f1_score(binary(te.label), binary(pt), pos_label="EXIT", zero_division=0),
        ))
    res = pd.DataFrame(rows).round(3)
    res.to_csv(OUT / "metrics_test.csv", index=False)
    print(res[["model", "cv_macro_f1_dev", "test_macro_f1", "test_binary_exit_f1"]].to_string())

    # best by CV macro-F1 on dev among learned models (never by test)
    best = max(LEARNED, key=lambda k: info[k]["cv_macro_f1"])
    print("best (by val):", best)
    for name in set([best, "naive_regex", "tfidf"]):
        cm = confusion_matrix(te.label, preds[name][1], labels=CLASSES)
        pd.DataFrame(cm, index=[f"true_{c}" for c in CLASSES],
                     columns=[f"pred_{c}" for c in CLASSES]).to_csv(OUT / f"confusion_{name}.csv")
    # final model for application: refit chosen config on ALL labeled data
    ek = "mpnet" if best == "emb_mpnet" else "minilm"
    fz, m = fit_final(best, info[best]["C"], d, emb[ek] if best != "tfidf" else None)
    with open(DATA / "final_model.pkl", "wb") as fh:
        pickle.dump(dict(kind=best, emb_key=ek, featurizer=fz, model=m), fh)
    te_out = te[["item_id", "kind", "sub", "group", "text", "label"]].copy()
    for name, (pv, pt) in preds.items():
        te_out[f"pred_{rename.get(name, name)}"] = pt
    te_out.drop(columns="text").to_csv(OUT / "test_predictions.csv", index=False)
    te_out.to_parquet(DATA / "test_predictions_with_text.parquet", index=False)
    json.dump(dict(best=rename[best], selection="5-fold CV macro-F1 on train+val", info=info,
                   sizes={s: int((d.split == s).sum()) for s in ("train", "val", "test")}),
              open(OUT / "model_selection.json", "w"), indent=1)

    # ---- intra-annotator agreement
    p2f = LABELS / "labels_pass2.csv"
    if p2f.exists():
        l1 = pd.read_csv(LABELS / "labels_pass1.csv").fillna("")
        l2 = pd.read_csv(p2f).fillna("")
        mm = l1.merge(l2, on="item_id", suffixes=("_1", "_2"))
        k3 = cohen_kappa_score(mm.label_1, mm.label_2)
        kb = cohen_kappa_score(binary(mm.label_1), binary(mm.label_2))
        pos = mm[(mm.label_1 != "OTHER") & (mm.label_2 != "OTHER")]
        kd = cohen_kappa_score(pos.dest_bucket_1, pos.dest_bucket_2) if len(pos) > 5 else np.nan
        agree = dict(n=len(mm), kappa_3class=round(k3, 3), kappa_binary=round(kb, 3),
                     raw_agreement=round((mm.label_1 == mm.label_2).mean(), 3),
                     n_both_positive=len(pos), kappa_dest_bucket=round(kd, 3))
        cm = pd.crosstab(mm.label_1, mm.label_2)
        cm.to_csv(OUT / "agreement_confusion.csv")
        json.dump(agree, open(OUT / "intra_annotator_agreement.json", "w"), indent=1)
        print(agree)
        print(cm)

    # ---- extractor validation on gold positives (all labeled positives)
    pos = d[d.label != "OTHER"]
    rows = []
    for r in extract.REASON_RX:
        gold = pos.reasons.str.contains(r)
        pr = pos.text.apply(lambda t: r in extract.reasons(t))
        tp = (gold & pr).sum()
        rows.append(dict(tag=r, gold_n=int(gold.sum()), pred_n=int(pr.sum()),
                         precision=round(tp / max(pr.sum(), 1), 3),
                         recall=round(tp / max(gold.sum(), 1), 3)))
    pd.DataFrame(rows).to_csv(OUT / "extractor_reasons_eval.csv", index=False)
    db = pos.text.apply(lambda t: extract.destination(t)[0])
    dacc = (db == pos.dest_bucket).mean()
    pd.crosstab(pos.dest_bucket, db).to_csv(OUT / "extractor_destination_confusion.csv")
    print(pd.DataFrame(rows)); print("dest bucket accuracy", round(dacc, 3))
    json.dump(dict(dest_bucket_accuracy=round(float(dacc), 3), n=len(pos)),
              open(OUT / "extractor_destination_eval.json", "w"))


if __name__ == "__main__":
    main()
