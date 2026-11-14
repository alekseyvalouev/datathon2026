"""Step 5: subgroup performance and error analysis.

The 187-item test split has only ~27 positives, so subgroup metrics on it alone would be
meaningless. We therefore use 5-fold out-of-fold (OOF) predictions over ALL labeled items
(each item predicted by a model that did not see it; same hybrid config and C as selected
in step 3), and also report the test-split numbers for reference.

Subgroups: subreddit group, post vs comment, text-length tertile, and a crude
"informal / non-standard English" lexical proxy (AAVE / slang / non-standard spelling
markers). That proxy is NOT a dialect classifier and the n is small, so read it as a smoke test.

Outputs: outputs/subgroup_metrics.csv, outputs/failure_examples.csv (paraphrase-length snippets,
no usernames), figs/subgroup_f1.png
"""
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import f1_score  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from common import CLASSES, FIGS, OUT, naive_rule  # noqa: E402
from features import Featurizer, embed, model_input  # noqa: E402
import importlib  # noqa: E402
tr = importlib.import_module("03_train_eval")

INFORMAL = re.compile(
    r"\b(finna|tryna|gonna|wanna|ion|ain'?t|y'?all|hella|deadass|bruh|bro|fr|ngl|lol|lmao|"
    r"imo|tbh|idk|smh|cuz|bc|u|ur|ya|yall|gotta|kinda|sorta|dont|cant|wont|im|thats|"
    r"aint|af|asf|playa)\b", re.I)


def informal_score(t):
    toks = re.findall(r"[A-Za-z']+", t)
    if not toks:
        return 0.0
    lower_i = len(re.findall(r"(^|\s)i(\s|')", t))     # lowercase "i"
    return (len(INFORMAL.findall(t)) + lower_i) / len(toks) * 100


def binary(y):
    return np.where(np.asarray(y) == "OTHER", "OTHER", "EXIT")


def metrics(g):
    if len(g) == 0:
        return {}
    y, p = g.label, g.pred
    pos = (y != "OTHER")
    return dict(n=len(g), n_pos=int(pos.sum()),
                macro_f1=f1_score(y, p, labels=CLASSES, average="macro", zero_division=0),
                exit_f1=f1_score(binary(y), binary(p), pos_label="EXIT", zero_division=0),
                exit_recall=float((binary(p)[pos.values] == "EXIT").mean()) if pos.any() else np.nan,
                exit_precision=float((binary(y)[binary(p) == "EXIT"] == "EXIT").mean())
                if (binary(p) == "EXIT").any() else np.nan,
                naive_exit_f1=f1_score(binary(y), binary(g.naive), pos_label="EXIT", zero_division=0))


def main():
    sel = json.load(open(OUT / "model_selection.json"))
    kind = {"hybrid_tfidf+minilm+rx_lr": "hybrid", "tfidf_lr": "tfidf", "minilm_emb_lr": "emb_minilm",
            "mpnet_emb_lr": "emb_mpnet"}[sel["best"]]
    C = sel["info"][kind]["C"]
    d = tr.make_splits(tr.load_labeled())
    d["x"] = model_input(d)
    ek = "mpnet" if kind == "emb_mpnet" else "minilm"
    E = embed(d.x.tolist(), ek, "labeled")
    d["pred"] = ""
    for a, b in StratifiedKFold(5, shuffle=True, random_state=11).split(d.x, d.label):
        fz = Featurizer(kind).fit(d.x.iloc[a])
        m = LogisticRegression(C=C, max_iter=5000, class_weight="balanced").fit(
            fz.transform(d.x.iloc[a].tolist(), E[a]), d.label.iloc[a])
        d.loc[d.index[b], "pred"] = m.predict(fz.transform(d.x.iloc[b].tolist(), E[b]))
    d["naive"] = [naive_rule(t, g) for t, g in zip(d.text, d.group)]
    d["len_tertile"] = pd.qcut(d.text.str.len(), 3, labels=["short", "medium", "long"]).astype(str)
    d["informal"] = d.text.apply(informal_score)
    thr = d.informal.quantile(0.8)
    d["register"] = np.where(d.informal >= thr, "informal_top20pct", "standard")
    rows = [dict(subgroup_type="all", subgroup="all (OOF)", **metrics(d))]
    for col in ("group", "kind", "len_tertile", "register"):
        for v, g in d.groupby(col):
            rows.append(dict(subgroup_type=col, subgroup=v, **metrics(g)))
    te = d[d.split == "test"]
    for col in ("group", "kind"):
        for v, g in te.groupby(col):
            rows.append(dict(subgroup_type=f"{col} (test split only)", subgroup=v, **metrics(g)))
    res = pd.DataFrame(rows).round(3)
    res.to_csv(OUT / "subgroup_metrics.csv", index=False)
    print(res.to_string())

    # figure
    plot = res[res.subgroup_type.isin(["group", "kind", "len_tertile", "register"])]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ypos = np.arange(len(plot))
    ax.barh(ypos + 0.2, plot.exit_f1, 0.4, label=f"{sel['best']} (OOF)", color="#2b6cb0")
    ax.barh(ypos - 0.2, plot.naive_exit_f1, 0.4, label="naive regex", color="#cbd5e0")
    ax.set_yticks(ypos)
    ax.set_yticklabels([f"{t}: {s} (n={n}, pos={p})" for t, s, n, p in
                        zip(plot.subgroup_type, plot.subgroup, plot.n, plot.n_pos)], fontsize=8)
    ax.set_xlabel("Exit-story F1 (LEFT or CONSIDERING vs OTHER)")
    ax.set_xlim(0, 1)
    ax.legend(fontsize=8, loc="lower right")
    ax.set_title("Subgroup performance (5-fold out-of-fold on 933 labeled items)", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGS / "subgroup_f1.png", dpi=150)

    # failure examples: short, anonymized snippets (<=160 chars around first move word)
    def short(t):
        t = re.sub(r"\s+", " ", t)
        mm = re.search(r"mov|left|leav|relocat|priced", t, re.I)
        a = max(0, (mm.start() if mm else 0) - 60)
        s = t[a:a + 160]
        s = re.sub(r"u/\w+|@\w+", "[user]", s)
        return ("…" if a else "") + s + "…"
    err = d[d.label != d.pred].copy()
    err["error_type"] = np.where(err.label == "OTHER", "false_positive",
                                 np.where(err.pred == "OTHER", "false_negative", "LEFT<->CONSIDERING"))
    ex = (err.groupby("error_type", group_keys=False)
          .apply(lambda g: g.sample(min(len(g), 8), random_state=3)))
    ex["snippet"] = ex.text.apply(short)
    ex[["error_type", "group", "kind", "label", "pred", "snippet"]].to_csv(
        OUT / "failure_examples.csv", index=False)
    print(err.error_type.value_counts())


if __name__ == "__main__":
    main()
