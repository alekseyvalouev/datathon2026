"""Step 4: apply the final model (data/final_model.pkl) to the whole candidate pool, then
extract reasons/destinations for predicted exit stories and aggregate.

Outputs (no usernames, no text):
  outputs/pool_predictions.csv      item_id, kind, sub, group, month, pred, p_LEFT, p_CONSIDERING, reasons, dest_bucket, dest_state
  outputs/monthly_exit_counts.csv   monthly counts + rate per 100k items of the same subreddit groups
  outputs/reason_distribution.csv   predicted (pool) and gold (labeled) reason shares
  outputs/destination_vs_cpl.csv    destination buckets vs California Policy Lab shares
"""
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import extract  # noqa: E402
from common import DATA, LABELS, OUT, REASONS  # noqa: E402
from features import embed, model_input  # noqa: E402

# CPL "Priced Out of the Bay" (2026): destinations of low-income movers out of their Bay
# neighbourhood. 75% stay in the Bay, 8% Central Valley, ~12% leave CA; remainder ~5% other CA.
CPL = {"other_bay_county": 0.75, "sacramento_central_valley": 0.08, "other_ca": 0.05,
       "out_of_state_or_abroad": 0.12}


def main():
    pool = pd.read_parquet(DATA / "pool.parquet")
    fm = pickle.load(open(DATA / "final_model.pkl", "rb"))
    x = model_input(pool)
    E = embed(x, fm["emb_key"], "pool") if fm["kind"] != "tfidf" else None
    X = fm["featurizer"].transform(x, E)
    proba = fm["model"].predict_proba(X)
    cls = list(fm["model"].classes_)
    pool["pred"] = np.array(cls)[proba.argmax(1)]
    for c in ("LEFT", "CONSIDERING"):
        pool[f"p_{c}"] = proba[:, cls.index(c)].round(4)
    pool["month"] = pool.date.str[:7]
    ex = pool.pred != "OTHER"
    pool["reasons"] = ""
    pool.loc[ex, "reasons"] = pool.loc[ex, "text"].apply(lambda t: ";".join(extract.reasons(t)))
    dd = pool.loc[ex, "text"].apply(extract.destination)
    pool["dest_bucket"], pool["dest_state"] = "", ""
    pool.loc[ex, "dest_bucket"] = [b for b, _ in dd]
    pool.loc[ex, "dest_state"] = [s or "" for _, s in dd]
    cols = ["item_id", "kind", "sub", "group", "month", "pred", "p_LEFT", "p_CONSIDERING",
            "reasons", "dest_bucket", "dest_state"]
    pool[cols].to_csv(OUT / "pool_predictions.csv", index=False)
    print(pool.pred.value_counts())

    # --- precision/recall correction from held-out test metrics of the selected model
    met = pd.read_csv(OUT / "metrics_test.csv").set_index("key").loc[fm["kind"]]
    corr = {c: met[f"test_{c}_precision"] / max(met[f"test_{c}_recall"], 1e-6)
            for c in ("LEFT", "CONSIDERING")}

    # --- monthly counts
    den = pd.read_csv(DATA / "denominators.csv").groupby("month").n_items.sum()
    m = pool[ex].groupby(["month", "pred"]).size().unstack(fill_value=0)
    m = m.reindex(columns=["LEFT", "CONSIDERING"], fill_value=0)
    m["exit_total"] = m.sum(1)
    m["all_items_scanned"] = den.reindex(m.index).values
    m["exit_per_100k_items"] = (1e5 * m.exit_total / m.all_items_scanned).round(2)
    m["exit_total_pr_corrected"] = (m.LEFT * corr["LEFT"] + m.CONSIDERING * corr["CONSIDERING"]).round(1)
    m.reset_index().to_csv(OUT / "monthly_exit_counts.csv", index=False)

    # --- reasons: pool (predicted, rule-extracted) vs gold labels (labeled positives)
    s = pd.read_csv(LABELS / "sample_to_label.csv")
    l1 = pd.read_csv(LABELS / "labels_pass1.csv").fillna("")
    gold = s.merge(l1, on="item_id")
    gpos = gold[gold.label != "OTHER"]
    rows = []
    for r in REASONS:
        rows.append(dict(reason=r,
                         pool_pred_n=int(pool.loc[ex, "reasons"].str.contains(r).sum()),
                         pool_pred_share_of_exits=round(pool.loc[ex, "reasons"].str.contains(r).mean(), 3),
                         gold_n=int(gpos.reasons.str.contains(r).sum()),
                         gold_share_of_exits=round(gpos.reasons.str.contains(r).mean(), 3)))
    rows.append(dict(reason="(no reason stated)",
                     pool_pred_n=int((pool.loc[ex, "reasons"] == "").sum()),
                     pool_pred_share_of_exits=round((pool.loc[ex, "reasons"] == "").mean(), 3),
                     gold_n=int((gpos.reasons == "").sum()),
                     gold_share_of_exits=round((gpos.reasons == "").mean(), 3)))
    pd.DataFrame(rows).to_csv(OUT / "reason_distribution.csv", index=False)

    # --- destinations vs CPL
    def shares(series, include_bay=None):
        v = series.value_counts()
        known = v.drop("unknown", errors="ignore")
        if include_bay is not None:
            known = known.add(pd.Series({"other_bay_county": include_bay}), fill_value=0)
        tot = known.sum()
        out = {"other_bay_county": known.get("other_bay_county", 0) / tot,
               "sacramento_central_valley": known.get("sacramento_central_valley", 0) / tot,
               "other_ca": known.get("other_ca", 0) / tot,
               "out_of_state_or_abroad": (known.get("out_of_state", 0) + known.get("abroad", 0)) / tot}
        return out, int(tot), int(v.get("unknown", 0))

    pool_sh, pool_n, pool_unk = shares(pool.loc[ex, "dest_bucket"])
    gold_sh, gold_n, gold_unk = shares(gpos.dest_bucket)
    gold_wb_sh, gold_wb_n, _ = shares(gpos.dest_bucket, include_bay=int(gold.within_bay.sum()))
    cpl_cond = {k: v / (1 - CPL["other_bay_county"]) for k, v in CPL.items() if k != "other_bay_county"}
    cpl_cond["other_bay_county"] = 0.0
    tab = pd.DataFrame({
        "CPL_low_income_movers_all": CPL,
        "CPL_conditional_on_leaving_Bay": cpl_cond,
        "Reddit_gold_labeled_exits": gold_sh,
        "Reddit_gold_exits_plus_within_Bay_moves": gold_wb_sh,
        "Reddit_model_pool_exits": pool_sh,
    }).round(3)
    tab.index.name = "destination"
    tab.to_csv(OUT / "destination_vs_cpl.csv")
    json.dump(dict(pool_exit_known_dest_n=pool_n, pool_exit_unknown_dest_n=pool_unk,
                   gold_exit_known_dest_n=gold_n, gold_exit_unknown_dest_n=gold_unk,
                   gold_within_bay_moves=int(gold.within_bay.sum()), pr_correction=corr,
                   pool_pred_counts=pool.pred.value_counts().to_dict(),
                   out_of_state_states_pool=pool.loc[ex & (pool.dest_state != ""), "dest_state"]
                   .value_counts().head(12).to_dict(),
                   out_of_state_states_gold=gpos.loc[gpos.dest_state != "", "dest_state"]
                   .value_counts().head(12).to_dict()),
              open(OUT / "pool_summary.json", "w"), indent=1)
    print(tab)


if __name__ == "__main__":
    main()
