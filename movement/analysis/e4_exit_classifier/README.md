# E4: Reddit "exit stories" classifier (follow people, not places)

**Question.** Who says, in their own words, that they left the Bay Area or California, or
that they are seriously planning to? What reasons do they give, and where do they go? How
does Reddit compare with California Policy Lab's *Priced Out of the Bay* (2026)? CPL finds
that among low-income movers, 75% stay in the Bay, 8% go to the Central Valley and about 12%
leave the state.

> **Labels were produced by an LLM annotator (Claude), not by humans.** The team must
> hand-verify `labels/verify_sample.csv` (50 items, human columns left blank) before
> presenting any results. Every metric below is agreement *with LLM labels*.

## Run

```bash
python3 run_all.py                 # from saved labels: compile → train/eval → apply → subgroups → figs
python3 run_all.py --rebuild-pool  # also re-scan the raw 5.2 GB CSV (~2.5 min)
```

Requirements: python3, duckdb, pandas, scikit-learn, sentence-transformers (CPU), matplotlib.
Annotation is never re-run: the labels are stored as data in `labels/raw/*.txt` and compiled to CSV.

| step | script | what it does |
|---|---|---|
| 1 | `scripts/01_build_pool.py` | Streams `reddit_posts-003.csv` with duckdb and flattens posts plus **nested comment and reply trees** (230,520 posts, 3,413,197 comments, 0 JSON failures). Applies a recall-oriented regex (move/leave/priced out/relocat… AND a Bay/CA place term; in Bay subs a stricter exit phrase alone is enough). Result: **12,918 candidates** (8,428 Bay-local, 1,482 finance/housing, 3,008 work/other; 10,221 are comments). No usernames are kept. |
| 2 | `02_sample_for_labeling.py`, `02b_…`, `02c_…` | Annotation sample (frozen). Round 1: 694 items, stratified by sub-group × post/comment × regex tier (A = naive-rule hit, B = first-person move language, C = **hard negatives**), 93 subreddits. Round 1 was only 10% positive, so two positive-enrichment rounds followed: R2 = 170 items with a first-person move pattern, R3 = 88 items with a strong "I moved to X / left the Bay" pattern. Total **952 labeled** (933 after removing duplicate texts). Sampling probabilities are saved. |
| 2d | `02d_pass2_subset.py` | 100-item subset for the second, blind labeling pass |
| – | `annot_tools.py` | Shows items to the annotator and compiles the compact label lines into `labels/labels_pass{1,2}.csv` |
| 3 | `03_train_eval.py` | Splits 60/20/20 stratified (`labels/splits.csv`). Baselines plus models; model and C selected by **5-fold CV on train+val**; test touched once. Also evaluates the reason/destination extractors. |
| 4 | `04_apply_pool.py` | Applies the final model to all 12,918 candidates and aggregates monthly counts, reasons and destinations vs CPL |
| 5 | `05_subgroups_errors.py` | Out-of-fold subgroup metrics and failure examples |
| 6 | `06_figures_verify.py` | Figures and `labels/verify_sample.csv` |

## Labels (`codebook.md`)
LEFT 109 · CONSIDERING 33 · OTHER 810, plus 29 first-person moves *within* the Bay
(flagged `within_bay`, labeled OTHER). Reason tags and destination buckets were recorded for
every positive.

**Consistency check.** A fresh-context instance of the same LLM, given only the codebook,
re-labeled 100 items blind (40 pass-1 positives and 60 negatives, half of them hard
negatives). **Cohen's κ = 0.865 for 3 classes** (0.85 for exit vs other, raw agreement 93%).
κ for the destination bucket is 0.92. All 7 disagreements are pass 1 = LEFT/CONSIDERING vs
pass 2 = OTHER, and most involve "moved out of SF, destination unstated", which could be a
move within the Bay. This is one model checking itself, so it says nothing about human
validity.

## Results (held-out test, n = 187, of which 21 LEFT and 6 CONSIDERING)

| model | CV macro-F1 (dev) | **test macro-F1** | test exit-vs-other F1 | LEFT P / R | CONS P / R |
|---|---|---|---|---|---|
| majority class | 0.31 | 0.31 | 0.00 | – | – |
| naive regex (earlier rule) | 0.39 | 0.44 | 0.36 | 0.31 / 0.38 | 0.10 / 0.50 |
| TF-IDF + LR | 0.42 | 0.52 | **0.58** | 0.62 / 0.62 | 0.00 / 0.00 |
| MiniLM embeddings + LR | 0.44 | 0.41 | 0.35 | 0.21 / 0.48 | 0.10 / 0.33 |
| mpnet embeddings + LR | 0.43 | 0.50 | 0.49 | 0.32 / 0.52 | 0.17 / 0.33 |
| **hybrid: TF-IDF + MiniLM + 6 regex flags → LR (selected)** | **0.51** | **0.53** | 0.48 | 0.34 / 0.71 | 0.22 / 0.33 |

Fine-tuning a transformer was **not** done. With about 110 positive training examples on a
CPU, we used frozen sentence embeddings plus logistic regression instead (allowed by the
brief). The test set is tiny (27 positives), so differences of ±0.1 in F1 are within noise.
The selected model trades precision for recall. TF-IDF has better test exit-vs-other F1
even though it scored lower in CV. **CONSIDERING is barely learnable at this sample size.**
Test metrics are on a sample enriched for positives, not on the natural pool distribution.

**Subgroups** (5-fold out-of-fold over all 933 items, exit-vs-other F1; the naive regex is in brackets):
Bay-local 0.45 (0.33) · finance/housing 0.47 (0.17) · work/other 0.43 (0.10);
comments 0.45 · posts 0.45; short 0.48 · medium 0.40 · long 0.45; informal/slang
register (top 20% on a lexical proxy) 0.45 vs standard 0.45. The model is roughly flat across
groups. The naive regex collapses outside Bay subs because it relies on the Bay being the
implicit origin. The informal-register proxy is a slang lexicon, **not** an AAVE or
non-native-writing detector, and that subgroup has only 24 positives.
Failure modes (`outputs/failure_examples.csv`): false positives are 142 of 200 errors. They
include "all my friends have left the Bay", "I'll never leave the Bay", moves within the Bay,
people who left and came back, and advice to others. False negatives include exits phrased
without Bay words ("got priced out of california", "moving to tennessee soon") and moves to
the Central Valley that were not written as "leaving".

## Applying the model to the pool (`outputs/`, `figs/`)
* 1,437 predicted exit stories (1,084 LEFT, 353 CONSIDERING) out of 12,918 candidates.
  Rescaling by the test precision/recall ratio gives about 750. The uncertainty is large.
  Monthly counts rise from about 5–45 per month in 2025 to 60–175 per month in 2026, but
  the scrape grew about 10×. **Per 100k scanned items the rate is flat to declining**
  (about 45 → 30). This is no evidence of a rising exodus. See `figs/monthly_exits.png`.
* **Reasons** among the 142 labeled exits (multi-label): no reason stated 46%, other
  (school, health, visa, retirement) 16%, safety/quality of life 15%, housing cost 12%,
  cost of living 11%, jobs 10%, family 7%, schools 5%, remote work 1%. The rule-based
  extractor applied to the pool has a precision of only about 0.4 per tag
  (`extractor_reasons_eval.csv`), so pool-level reason shares are rough.
* **Destinations vs CPL** (`destination_vs_cpl.csv`, `figs/destinations_vs_cpl.png`):

| among movers who left the Bay (known destination) | Sacramento & Central Valley | other CA | out of state or abroad |
|---|---|---|---|
| CPL, low-income movers (8 / 5* / 12 of 25) | **32%** | 20% | 48% |
| Reddit, labeled exits (n = 106) | **7%** | 3% | **91%** |
| Reddit, labeled exits, random round 1 only (n = 51) | 6% | 6% | 88% |

\*CPL's "other CA" share is inferred as the remainder (100 − 75 − 8 − 12). The source report
should be checked. Top out-of-state destinations are TX, OR, NY, WA, NV and CO.

**Interpretation.** Reddit exit stories over-represent long-distance, out-of-state moves
(tech workers, students, remote workers) and almost miss the short-distance
Bay → Central Valley displacement that dominates CPL's low-income exits. People pushed to
Stockton or Antioch rarely write "I left the Bay". That is the theme's point: the people who
leave quietly are the least visible in online data. **Selection bias:** Reddit users are not
low-income movers, nobody's income is observed, and the enrichment rounds favored named
destinations. The finding survives restricting to the unenriched round 1.

## Ethics
No usernames are read into any output (`user_posted` and `user_id` are never selected).
Failure examples are ≤160-character snippets. Outputs contain no text, only item IDs that
can be re-linked to public posts. Do not quote people in slides. Paraphrase instead.

## Advanced Track checklist
| requirement | where |
|---|---|
| **Model** trained (not keywords or an API): hybrid TF-IDF + MiniLM embeddings + LR; embedding-only and TF-IDF variants | `scripts/03_train_eval.py`, `features.py`, `data/final_model.pkl` |
| **Baseline**: majority class, the published naive regex rule, TF-IDF + LR | `outputs/metrics_test.csv`, `figs/model_comparison.png` |
| **Evaluation**: macro-F1, per-class P/R, confusion matrix on a 20% test split never used for selection | `outputs/metrics_test.csv`, `confusion_*.csv`, `figs/confusion_best.png` |
| **Error and fairness analysis**: ≥3 subgroups (subreddit group, post/comment, length, register proxy), failure examples | `outputs/subgroup_metrics.csv`, `failure_examples.csv`, `figs/subgroup_f1.png` |
| **Data decisions**: codebook, stratified sampling with hard negatives, LLM labels, blind re-label κ = 0.87; **human hand-check still TO DO** in `labels/verify_sample.csv` | `codebook.md`, `labels/` |
| **Reproducibility**: raw CSV → results with one command | `run_all.py` |

## Limitations
LLM labels without human verification so far. Small positive set (142; only 33
CONSIDERING). Test n = 27 positives. Candidate-pool recall is unknown because exits without
move or place words are never seen. Destination
and reason extraction is rule-based and noisy. CPL compares administrative records of
low-income movers, which is a different population.
