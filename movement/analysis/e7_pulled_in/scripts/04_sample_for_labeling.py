"""Step 4 (Reddit): frozen stratified annotation sample of 300 arrival candidates
(by regex tier), shuffled. Writes labels/sample_to_label.csv. Sampling probabilities kept."""
import pandas as pd

from e7common import DATA, LABELS

N_PER_TIER = {"A_first_person_move_to_bay": 150, "B_newcomer_implicit": 70,
              "B_newcomer_place": 40, "C_offer_in_bay": 40}


def main():
    pool = pd.read_parquet(DATA / "arrival_pool.parquet")
    parts = []
    for tier, n in N_PER_TIER.items():
        g = pool[pool.tier == tier]
        s = g.sample(min(n, len(g)), random_state=7).copy()
        s["sample_prob"] = len(s) / len(g)
        parts.append(s)
    s = pd.concat(parts).sample(frac=1, random_state=7).reset_index(drop=True)
    s.insert(0, "idx", range(len(s)))
    s.to_csv(LABELS / "sample_to_label.csv", index=False)
    print(s.tier.value_counts(), s.group.value_counts())


if __name__ == "__main__":
    main()
