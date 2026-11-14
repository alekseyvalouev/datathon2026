"""Step 5 (Reddit): compile LLM labels, measure regex-tier precision, describe arrivals
(reasons, household, origin, occupation, stated money, destination), compare with E4 leaver
reasons, validate a rule-based money extractor, and build labels/verify_sample.csv."""
import json
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from e7common import DATA, E4, FIGS, LABELS, OUT  # noqa: E402
from annot_tools import snippet  # noqa: E402

LAB = dict(A="ARRIVED", P="PLANNING", W="WITHIN_BAY", O="OTHER")
RC = dict(t="tech_job", j="other_job", s="school", p="partner_family", l="lifestyle",
          c="returning", o="other")
HC = dict(s="single", c="couple", f="family_kids", r="roommates", u="unknown")
EC = dict(n="recent", a="long_ago", u="unknown")
OC = dict(us="other_US_state", ca="elsewhere_CA", ab="abroad", u="unknown")
OCC = dict(t="tech", h="healthcare", a="academic_student", s="service_trades_hourly",
           f="finance_law_prof", u="unknown")


def compile_labels():
    s = pd.read_csv(LABELS / "sample_to_label.csv")
    rows = []
    for f in sorted((LABELS / "raw").glob("pass1_*.txt")):
        for line in f.read_text().splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            p = (line.split("|") + [""] * 9)[:9]
            idx, lab, rs, hh, era, org, dest, occ, money = [x.strip() for x in p]
            pos = lab in ("A", "P")
            rows.append(dict(idx=int(idx), label=LAB[lab],
                             reasons=";".join(RC[x] for x in rs.split(";") if x) if pos else "",
                             household=HC.get(hh, "") if pos else "",
                             era=EC.get(era, "") if pos else "",
                             origin=OC.get(org, "") if pos else "",
                             dest=dest if pos else "", occ=OCC.get(occ, "") if pos else "",
                             money=money if pos else ""))
    lab = pd.DataFrame(rows)
    assert lab.idx.is_unique and len(lab) == len(s), (len(lab), len(s))
    lab = lab.merge(s[["idx", "item_id", "kind", "sub", "group", "tier", "date", "sample_prob"]],
                    on="idx")
    lab.to_csv(LABELS / "labels_pass1.csv", index=False)
    return lab, s


# ---- money extractor (rule-based, validated against the LLM labels) ----------------------
RE_K = re.compile(r"\$?\s?(\d{2,3}(?:\.\d)?)\s?[kK]\b")
RE_DOLLAR = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+|\d{3,6})(?:\.\d\d)?(?!\d)")
SAL_CTX = re.compile(r"salary|offer|base|\btc\b|total comp|comp(ensation)?\b|income|make|making|"
                     r"earn|paid|pay\b|a year|/yr|per year|annual", re.I)
RENT_CTX = re.compile(r"rent|budget|/mo|a month|per month|monthly|studio|apartment|1br|1 ?bed|room",
                      re.I)


def extract_money(text):
    """Return (annual_salaries, monthly_rents) stated in text."""
    t = text or ""
    sal, rent = [], []
    for m in RE_K.finditer(t):
        v = float(m.group(1)) * 1000
        ctx = t[max(0, m.start() - 60):m.end() + 40]
        if 30_000 <= v <= 1_500_000 and (SAL_CTX.search(ctx) or not RENT_CTX.search(ctx)):
            sal.append(v)
        elif RENT_CTX.search(ctx) and 1_000 <= v <= 10_000:
            rent.append(v)
    for m in RE_DOLLAR.finditer(t):
        v = float(m.group(1).replace(",", ""))
        ctx = t[max(0, m.start() - 60):m.end() + 40]
        if 500 <= v <= 10_000 and RENT_CTX.search(ctx):
            rent.append(v)
        elif 30_000 <= v <= 1_500_000 and SAL_CTX.search(ctx):
            sal.append(v)
    return sal, rent


def label_money(s):
    """Parse the annotator's money field -> (salary-like annual, rent-like monthly)."""
    sal, rent = [], []
    for part in (s or "").split(";"):
        part = part.strip().lower()
        nums = [float(x) * (1000 if k else 1) for x, k in
                re.findall(r"(\d+(?:\.\d+)?)(k)?", part.replace(",", ""))]
        if not nums:
            continue
        if part.startswith(("sal", "tc", "hh")):
            sal.append(nums[0] * (12 if "/mo" in part and nums[0] < 100_000 else 1))
        elif part.startswith("rent"):
            rent.append(np.mean(nums[:2]))
    return sal, rent


def share_table(df, col, multi=False):
    if multi:
        vals = df[col].fillna("").apply(lambda x: x.split(";") if x else ["(none stated)"])
        ex = vals.explode()
    else:
        ex = df[col]
    t = ex.value_counts().rename("n").to_frame()
    t["share_of_items"] = t.n / len(df)
    return t.reset_index().rename(columns={"index": col})


def main():
    lab, s = compile_labels()
    pool = pd.read_parquet(DATA / "arrival_pool.parquet")
    text = dict(zip(s.idx, s.text))

    # 1. regex-tier precision and pool estimates (inverse sampling probability)
    lab["is_arrival"] = lab.label.isin(["ARRIVED", "PLANNING"]).astype(int)
    tp = lab.groupby("tier").agg(n_labeled=("idx", "size"), precision_A_or_P=("is_arrival", "mean"),
                                 share_ARRIVED=("label", lambda x: (x == "ARRIVED").mean()),
                                 share_PLANNING=("label", lambda x: (x == "PLANNING").mean()),
                                 share_WITHIN=("label", lambda x: (x == "WITHIN_BAY").mean()))
    tp["pool_n"] = pool.tier.value_counts()
    tp["est_arrival_items_in_pool"] = (tp.precision_A_or_P * tp.pool_n).round()
    tp.reset_index().to_csv(OUT / "arrival_regex_tier_precision.csv", index=False)

    pos = lab[lab.is_arrival == 1].copy()
    recent = pos[(pos.era == "recent")]
    sets = {"all_arrivals_A_or_P": pos, "recent_newcomers": recent}

    # 2. descriptive tables
    out = []
    for name, d in sets.items():
        for col, multi in [("reasons", True), ("household", False), ("origin", False),
                           ("occ", False), ("era", False), ("label", False)]:
            t = share_table(d, col, multi)
            t.columns = ["value", "n", "share_of_items"]
            t.insert(0, "field", col)
            t.insert(0, "set", name)
            t["n_items_in_set"] = len(d)
            out.append(t)
    desc = pd.concat(out)
    desc.to_csv(OUT / "arrival_profile.csv", index=False)

    # destinations
    def dest_bucket(x):
        x = (x or "").lower()
        if re.search(r"\bsf\b|san francisco", x):
            return "San Francisco"
        if re.search(r"oakland|berkeley|alameda|east bay|hayward|fremont|san leandro|walnut creek|"
                     r"lafayette|piedmont|newark|castro valley|dublin|pleasanton|livermore", x):
            return "East Bay (Alameda/Contra Costa)"
        if re.search(r"san jose|santa clara|sunnyvale|south bay|mountain view|milpitas|palo alto", x):
            return "South Bay / Santa Clara Co."
        if re.search(r"peninsula|san mateo|redwood|burlingame|belmont|san bruno|south sf|atherton|"
                     r"menlo|foster", x):
            return "Peninsula / San Mateo Co."
        if re.search(r"north bay|marin", x):
            return "North Bay"
        return "Bay Area (unspecified)"
    pos["dest_bucket"] = pos.dest.apply(dest_bucket)
    dt = pos.groupby("dest_bucket").size().rename("n").reset_index()
    dt["share"] = dt.n / dt.n.sum()
    dt.sort_values("n", ascending=False).to_csv(OUT / "arrival_destinations.csv", index=False)
    pos.dest.value_counts().rename_axis("dest_as_written").rename("n").reset_index().to_csv(
        OUT / "arrival_destinations_detail.csv", index=False)

    # 3. stated money
    mrows = []
    for _, r in pos.iterrows():
        ls, lr = label_money(r.money)
        es, er = extract_money(text[r.idx])
        mrows.append(dict(idx=r.idx, item_id=r.item_id, label=r.label, era=r.era, occ=r.occ,
                          household=r.household, label_money=r.money,
                          label_salary_annual=ls[0] if ls else np.nan,
                          label_rent_monthly=lr[0] if lr else np.nan,
                          extractor_salary_annual=es[0] if es else np.nan,
                          extractor_rent_monthly=er[0] if er else np.nan))
    mon = pd.DataFrame(mrows)
    mon["label_salary_hourly_equiv"] = mon.label_salary_annual / 2080
    mon.to_csv(OUT / "arrival_stated_money.csv", index=False)
    ev = {}
    for k in ("salary_annual", "rent_monthly"):
        g, e = mon[f"label_{k}"].notna(), mon[f"extractor_{k}"].notna()
        tp_ = int((g & e).sum())
        ev[k] = dict(gold_n=int(g.sum()), extractor_n=int(e.sum()), both=tp_,
                     precision=tp_ / max(e.sum(), 1), recall=tp_ / max(g.sum(), 1))
    sal = mon.label_salary_annual.dropna()
    ev["n_arrivals"] = int(len(pos))
    ev["share_stating_any_money"] = float((mon.label_money.fillna("") != "").mean())
    ev["stated_salaries_annual"] = sorted(sal.tolist())
    ev["stated_salary_hourly_equiv_median"] = float((sal / 2080).median()) if len(sal) else None
    ev["stated_rents_monthly"] = sorted(mon.label_rent_monthly.dropna().tolist())
    json.dump(ev, open(OUT / "arrival_money_summary.json", "w"), indent=1)

    # 4. compare with E4 leaver reasons (gold labels, multi-label shares)
    e4 = pd.read_csv(E4 / "outputs" / "reason_distribution.csv")[["reason", "gold_n", "gold_share_of_exits"]]
    arr = share_table(pos, "reasons", True)
    arr.columns = ["reason", "n", "share"]
    cmp_rows = [
        ("jobs / career", ["tech_job", "other_job"], ["jobs_wages"]),
        ("school / university", ["school"], ["other"]),  # E4 'other' includes school/college
        ("partner / family", ["partner_family"], ["family"]),
        ("housing cost", [], ["housing_cost"]),
        ("cost of living (other)", [], ["cost_of_living_other"]),
        ("lifestyle / quality of life", ["lifestyle"], ["safety_quality_of_life"]),
        ("returning home", ["returning"], []),
        ("K-12 schools", [], ["schools"]),
        ("remote work", [], ["remote_work"]),
        ("no reason stated", ["(none stated)"], ["(no reason stated)"]),
    ]
    a_sets = pos.reasons.fillna("").apply(lambda x: set(x.split(";")) if x else {"(none stated)"})
    rows = []
    for name, a_keys, e_keys in cmp_rows:
        a_share = float(a_sets.apply(lambda z: bool(z & set(a_keys))).mean()) if a_keys else 0.0
        e_share = float(e4[e4.reason.isin(e_keys)].gold_share_of_exits.sum()) if e_keys else 0.0
        rows.append(dict(reason=name, arrivals_share=a_share, arrivals_n=len(pos),
                         leavers_share_E4=e_share, leavers_n_E4=142,
                         note="E4 'other' bundles school/college/health/visa/retirement"
                         if name.startswith("school") else ""))
    comp = pd.DataFrame(rows)
    comp.to_csv(OUT / "reasons_arrivals_vs_leavers.csv", index=False)

    # 5. figures
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    c = comp[comp.reason != "no reason stated"]
    y = np.arange(len(c))
    ax.barh(y + .2, 100 * c.arrivals_share, .4, color="#2a6f97", label=f"arrivals (E7, n={len(pos)})")
    ax.barh(y - .2, 100 * c.leavers_share_E4, .4, color="#c8553d", label="leavers (E4 gold, n=142)")
    ax.set_yticks(y, c.reason)
    ax.invert_yaxis()
    ax.set_xlabel("% of first-person stories citing the reason (multi-label; LLM-labeled)")
    ax.set_title("Why people say they come vs why they say they go (Reddit)")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGS / "reasons_arrivals_vs_leavers.png", dpi=160)

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
    for ax, col, title in zip(axes, ["household", "origin", "occ"],
                              ["household", "origin", "occupation (if stated)"]):
        t = recent[col].value_counts()
        ax.barh(t.index[::-1], 100 * t.values[::-1] / len(recent), color="#2a6f97")
        ax.set_title(f"{title}", fontsize=10)
        ax.set_xlabel("% of recent newcomers")
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"Recent newcomers on Reddit (arrived ≤~5y or planning; n={len(recent)}, LLM-labeled)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGS / "arrival_profile.png", dpi=160)

    # 6. verify sample (30 items: 18 positives, 12 negatives), human columns blank
    rng = np.random.RandomState(30)
    vs = pd.concat([lab[lab.is_arrival == 1].sample(18, random_state=rng),
                    lab[lab.is_arrival == 0].sample(12, random_state=rng)]).sample(frac=1, random_state=rng)
    vs = vs.assign(snippet=[snippet(text[i], 400) for i in vs.idx])
    vs = vs[["idx", "item_id", "sub", "kind", "snippet", "label", "reasons", "household", "origin",
             "occ", "money"]].rename(columns={c: f"llm_{c}" for c in
                                              ["label", "reasons", "household", "origin", "occ", "money"]})
    for c in ["human_label", "human_reasons", "human_household", "human_money", "human_notes"]:
        vs[c] = ""
    vs.to_csv(LABELS / "verify_sample.csv", index=False)

    summary = dict(n_labeled=len(lab), label_counts=lab.label.value_counts().to_dict(),
                   n_arrival=len(pos), n_recent=len(recent),
                   pool_size=len(pool), est_arrival_items_in_pool=float(tp.est_arrival_items_in_pool.sum()),
                   money=ev)
    json.dump(summary, open(OUT / "arrival_summary.json", "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in summary.items() if k != "money"}, indent=1, default=float))
    print(tp)
    print(comp)
    print(desc[desc.set == "recent_newcomers"].to_string())
    print(json.dumps(ev, indent=1))


if __name__ == "__main__":
    main()
