"""Step 6: figures + the human verification sheet.

figs/model_comparison.png, figs/confusion_best.png, figs/monthly_exits.png,
figs/reasons.png, figs/destinations_vs_cpl.png
labels/verify_sample.csv  (50 items: LLM label + blank human columns)
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from annot_tools import snippet  # noqa: E402
from common import FIGS, LABELS, OUT  # noqa: E402

BLUE, GREY, ORANGE, GREEN = "#2b6cb0", "#a0aec0", "#dd6b20", "#2f855a"


def main():
    sel = json.load(open(OUT / "model_selection.json"))
    met = pd.read_csv(OUT / "metrics_test.csv")
    # model comparison
    fig, ax = plt.subplots(figsize=(8, 3.6))
    y = np.arange(len(met))
    ax.barh(y + 0.2, met.test_macro_f1, 0.4, color=BLUE, label="test macro-F1 (3 classes)")
    ax.barh(y - 0.2, met.test_binary_exit_f1, 0.4, color=GREY, label="test exit-vs-other F1")
    ax.set_yticks(y); ax.set_yticklabels(met.model, fontsize=8); ax.set_xlim(0, 1)
    for i, (a, b) in enumerate(zip(met.test_macro_f1, met.test_binary_exit_f1)):
        ax.text(a + 0.01, i + 0.2, f"{a:.2f}", va="center", fontsize=7)
        ax.text(b + 0.01, i - 0.2, f"{b:.2f}", va="center", fontsize=7)
    ax.legend(fontsize=8, loc="lower right")
    ax.set_title(f"Held-out test (n=187, 27 exit stories). Selected by CV: {sel['best']}", fontsize=9)
    fig.tight_layout(); fig.savefig(FIGS / "model_comparison.png", dpi=150); plt.close(fig)

    # confusion
    key = [k for k, v in {"hybrid": "hybrid_tfidf+minilm+rx_lr", "tfidf": "tfidf_lr",
                          "emb_minilm": "minilm_emb_lr", "emb_mpnet": "mpnet_emb_lr"}.items()
           if v == sel["best"]][0]
    cm = pd.read_csv(OUT / f"confusion_{key}.csv", index_col=0)
    fig, ax = plt.subplots(figsize=(4.2, 3.6))
    ax.imshow(cm.values, cmap="Blues")
    for i in range(3):
        for j in range(3):
            ax.text(j, i, cm.values[i, j], ha="center", va="center",
                    color="white" if cm.values[i, j] > cm.values.max() / 2 else "black")
    ax.set_xticks(range(3)); ax.set_xticklabels([c.replace("pred_", "") for c in cm.columns], fontsize=8)
    ax.set_yticks(range(3)); ax.set_yticklabels([c.replace("true_", "") for c in cm.index], fontsize=8)
    ax.set_xlabel("predicted"); ax.set_ylabel("LLM-annotated label")
    ax.set_title(f"Test confusion: {sel['best']}", fontsize=8)
    fig.tight_layout(); fig.savefig(FIGS / "confusion_best.png", dpi=150); plt.close(fig)

    # monthly
    m = pd.read_csv(OUT / "monthly_exit_counts.csv")
    m = m[m.month < "2026-11"]  # partial month dropped
    fig, ax1 = plt.subplots(figsize=(9, 3.8))
    ax1.bar(m.month, m.LEFT, color=BLUE, label="predicted LEFT")
    ax1.bar(m.month, m.CONSIDERING, bottom=m.LEFT, color=ORANGE, label="predicted CONSIDERING")
    ax1.plot(m.month, m.exit_total_pr_corrected, color="black", lw=1.5, marker="o", ms=3,
             label="precision/recall-corrected total")
    ax1.set_ylabel("exit stories / month")
    ax2 = ax1.twinx()
    ax2.plot(m.month, m.exit_per_100k_items, color=GREEN, ls="--", label="raw predicted per 100k items scanned")
    ax2.set_ylabel("per 100k posts+comments", color=GREEN)
    ax1.tick_params(axis="x", rotation=60, labelsize=7)
    h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, fontsize=7, loc="upper left")
    ax1.set_title("Reddit exit stories over time (scrape volume grows ~10x in 2026; read the rate line)", fontsize=9)
    fig.tight_layout(); fig.savefig(FIGS / "monthly_exits.png", dpi=150); plt.close(fig)

    # reasons
    r = pd.read_csv(OUT / "reason_distribution.csv")
    fig, ax = plt.subplots(figsize=(7, 3.6))
    y = np.arange(len(r))
    ax.barh(y + 0.2, r.gold_share_of_exits, 0.4, color=BLUE, label=f"labeled exits (n={int(r.gold_n.iloc[-1] / r.gold_share_of_exits.iloc[-1])})")
    ax.barh(y - 0.2, r.pool_pred_share_of_exits, 0.4, color=GREY, label="model on full pool (rule-extracted)")
    ax.set_yticks(y); ax.set_yticklabels(r.reason, fontsize=8); ax.invert_yaxis()
    ax.set_xlabel("share of exit stories mentioning reason (multi-label)")
    ax.legend(fontsize=8); ax.set_title("Stated reasons for leaving", fontsize=9)
    fig.tight_layout(); fig.savefig(FIGS / "reasons.png", dpi=150); plt.close(fig)

    # destinations vs CPL
    t = pd.read_csv(OUT / "destination_vs_cpl.csv", index_col=0)
    cols = ["CPL_low_income_movers_all", "Reddit_gold_exits_plus_within_Bay_moves",
            "CPL_conditional_on_leaving_Bay", "Reddit_gold_labeled_exits", "Reddit_model_pool_exits"]
    colors = {"other_bay_county": GREY, "sacramento_central_valley": GREEN, "other_ca": ORANGE,
              "out_of_state_or_abroad": BLUE}
    fig, ax = plt.subplots(figsize=(9, 3.8))
    left = np.zeros(len(cols))
    for dest in t.index:
        v = t.loc[dest, cols].values
        ax.barh(range(len(cols)), v, left=left, color=colors[dest], label=dest)
        for i, (a, b) in enumerate(zip(left, v)):
            if b > 0.04:
                ax.text(a + b / 2, i, f"{b:.0%}", ha="center", va="center", fontsize=7, color="white")
        left += v
    ax.set_yticks(range(len(cols)))
    ax.set_yticklabels(["CPL: all low-income movers", "Reddit labeled: exits + within-Bay moves",
                        "CPL: low-income movers who left the Bay", "Reddit labeled: exits (known dest.)",
                        "Reddit model on pool (noisy)"], fontsize=8)
    ax.invert_yaxis(); ax.set_xlim(0, 1)
    ax.legend(fontsize=7, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    ax.set_title("Where do movers go? CPL 'Priced Out of the Bay' vs Reddit exit stories", fontsize=9)
    fig.tight_layout(); fig.savefig(FIGS / "destinations_vs_cpl.png", dpi=150); plt.close(fig)

    # verification sheet: 25 LLM-positive + 25 LLM-OTHER (incl. hard negatives), seeded
    s = pd.read_csv(LABELS / "sample_to_label.csv")
    l1 = pd.read_csv(LABELS / "labels_pass1.csv").fillna("")
    d = s.merge(l1, on="item_id")
    d["norm"] = d.text.str.lower().str.replace(r"\W+", " ", regex=True).str.strip()
    d = d.drop_duplicates("norm")
    pos = d[d.label != "OTHER"].sample(25, random_state=50)
    neg_h = d[(d.label == "OTHER") & (d.tier.isin(["A", "B"]) | (d["round"] > 1))].sample(15, random_state=50)
    neg_r = d[(d.label == "OTHER") & ~d.index.isin(neg_h.index)].sample(10, random_state=50)
    v = pd.concat([pos, neg_h, neg_r]).sample(frac=1, random_state=51)
    v["text_snippet"] = v.text.apply(snippet)
    out = v[["item_id", "sub", "kind", "thread_title", "text_snippet", "label", "reasons",
             "dest_bucket"]].rename(columns={"label": "llm_label", "reasons": "llm_reasons",
                                             "dest_bucket": "llm_dest_bucket"})
    for c in ("human_label", "human_reasons", "human_dest_bucket", "human_initials", "human_notes"):
        out[c] = ""
    out.to_csv(LABELS / "verify_sample.csv", index=False)
    print("figs + verify_sample written", len(out))


if __name__ == "__main__":
    main()
