"""Step 3 (Indeed): who gets relocation help? Bay vs rest of CA, by pay tier, occupation,
degree mention and work mode. Writes outputs/relocation_*.csv and figs/relocation_*.png."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from e7common import DATA, FIGS, OUT  # noqa: E402

TIERS = ["<$25", "$25-40", "$40-60", "$60+", "no_pay"]


def rate_table(p, by):
    g = p.groupby(["region"] + by)
    t = g.agg(n=("relo", "size"), n_relo=("relo", "sum"), relo_rate=("relo", "mean"),
              relo_firm_rate=("relo_firm", "mean"), n_companies=("company_name", "nunique"))
    # company-balanced rate: each company weighs equally (guards against one employer's boilerplate)
    cb = (p.groupby(["region"] + by + ["company_name"]).relo.mean()
          .groupby(["region"] + by).mean().rename("relo_rate_company_balanced"))
    t = t.join(cb).reset_index()
    t["ci95_halfwidth"] = 1.96 * np.sqrt(t.relo_rate * (1 - t.relo_rate) / t.n)
    return t


def main():
    p = pd.read_parquet(DATA / "postings_flags.parquet")
    p = p[p.region != "Unknown"].copy()
    p["company_name"] = p.company_name.fillna("(none)")
    res = {}

    # 1. pay tier
    t1 = rate_table(p, ["pay_tier"])
    t1["pay_tier"] = pd.Categorical(t1.pay_tier, TIERS)
    t1 = t1.sort_values(["region", "pay_tier"])
    t1.to_csv(OUT / "relocation_by_paytier.csv", index=False)
    # sensitivity: imputed pay (E3 ridge) fills missing-pay rows
    t1b = rate_table(p.assign(pay_tier=p.pay_tier_imputed), ["pay_tier"])
    t1b.to_csv(OUT / "relocation_by_paytier_imputedpay.csv", index=False)
    # sensitivity: drop the top-5 relocation posters statewide
    top = p[p.relo == 1].company_name.value_counts().head(5)
    t1c = rate_table(p[~p.company_name.isin(top.index)], ["pay_tier"])
    t1c.to_csv(OUT / "relocation_by_paytier_excl_top5_employers.csv", index=False)

    # 2. occupation, degree, work mode
    t2 = rate_table(p, ["occ_broad"])
    t2.to_csv(OUT / "relocation_by_occupation.csv", index=False)
    t3 = rate_table(p, ["degree"])
    t3.to_csv(OUT / "relocation_by_degree.csv", index=False)
    t4 = rate_table(p, ["work_mode"])
    t4.to_csv(OUT / "relocation_by_workmode.csv", index=False)

    # 3. profile of relocation vs non-relocation postings
    rows = []
    for (reg, r), g in p.groupby(["region", "relo"]):
        pay = g.pay_mid.dropna()
        rows.append(dict(region=reg, relocation=int(r), n=len(g),
                         share_with_posted_pay=g.pay_mid.notna().mean(),
                         median_posted_hourly=pay.median(), p25=pay.quantile(.25),
                         p75=pay.quantile(.75),
                         share_under_25=(pay < 25).mean(), share_60plus=(pay >= 60).mean(),
                         share_degree_any=g.degree_any.mean(),
                         share_bachelors_plus=(g.degree != "none").mean(),
                         share_masters_or_phd=g.degree.isin(["masters", "phd"]).mean(),
                         share_phd=(g.degree == "phd").mean(),
                         share_degree_in_required_sentence=g.degree_req_sentence.mean(),
                         share_remote=(g.work_mode == "remote").mean(),
                         share_hybrid=(g.work_mode == "hybrid").mean(),
                         share_lowwage_E3_occ=(g.occ_broad == "lowwage_service_E3").mean(),
                         share_tech=(g.occ_broad == "tech_software_data").mean(),
                         share_physician=(g.occ_broad == "physician_clinician").mean(),
                         top_occ=g.occ_broad.value_counts().index[0]))
    prof = pd.DataFrame(rows)
    prof.to_csv(OUT / "relocation_profile.csv", index=False)

    # occupation mix of relocation postings
    mix = (p[p.relo == 1].groupby("region").occ_broad.value_counts(normalize=True)
           .rename("share_of_relocation_postings").reset_index())
    mix.to_csv(OUT / "relocation_occupation_mix.csv", index=False)

    # employer concentration
    conc = []
    for reg, g in p[p.relo == 1].groupby("region"):
        vc = g.company_name.value_counts()
        conc.append(dict(region=reg, n_relo=len(g), n_companies=len(vc),
                         top5_share=vc.head(5).sum() / len(g),
                         top5=", ".join(f"{k} ({v})" for k, v in vc.head(5).items())))
    pd.DataFrame(conc).to_csv(OUT / "relocation_employer_concentration.csv", index=False)

    # E3 low-wage groups specifically
    lw = (p[p.occ.notna()].groupby(["region", "occ"])
          .agg(n=("relo", "size"), n_relo=("relo", "sum"), relo_rate=("relo", "mean")).reset_index())
    lw.to_csv(OUT / "relocation_lowwage_E3_groups.csv", index=False)

    # headline
    b = t1[t1.region == "Bay Area"].set_index("pay_tier")
    r = t1[t1.region == "Rest of CA"].set_index("pay_tier")
    res = dict(
        n_postings=int(len(p)), n_relo=int(p.relo.sum()), n_relo_firm=int(p.relo_firm.sum()),
        bay_relo_rate_60plus=float(b.loc["$60+", "relo_rate"]), bay_n_60plus=int(b.loc["$60+", "n"]),
        bay_relo_rate_under25=float(b.loc["<$25", "relo_rate"]), bay_n_under25=int(b.loc["<$25", "n"]),
        bay_relo_firm_rate_60plus=float(b.loc["$60+", "relo_firm_rate"]),
        bay_relo_firm_rate_under25=float(b.loc["<$25", "relo_firm_rate"]),
        bay_cb_rate_60plus=float(b.loc["$60+", "relo_rate_company_balanced"]),
        bay_cb_rate_under25=float(b.loc["<$25", "relo_rate_company_balanced"]),
        rest_relo_rate_60plus=float(r.loc["$60+", "relo_rate"]),
        rest_relo_rate_under25=float(r.loc["<$25", "relo_rate"]),
        bay_overall=float(p[p.region == "Bay Area"].relo.mean()),
        rest_overall=float(p[p.region == "Rest of CA"].relo.mean()),
        top5_relo_employers_statewide=top.to_dict(),
    )
    json.dump(res, open(OUT / "relocation_headline.json", "w"), indent=1)
    print(json.dumps(res, indent=1))

    # figures
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    tiers = TIERS[:4]
    x = np.arange(len(tiers))
    for k, (reg, col) in enumerate([("Bay Area", "#2a6f97"), ("Rest of CA", "#a0a0a0")]):
        t = t1[t1.region == reg].set_index("pay_tier").loc[tiers]
        ax.bar(x + (k - .5) * .38, 100 * t.relo_rate, .38, color=col, label=f"{reg} (any offer)",
               yerr=100 * t.ci95_halfwidth, capsize=2)
        ax.scatter(x + (k - .5) * .38, 100 * t.relo_firm_rate, color="k", marker="_", s=200, zorder=3,
                   label="firm (un-hedged) offers only" if k == 0 else None)
        for xi, (rate, n) in enumerate(zip(t.relo_rate, t.n)):
            ax.text(xi + (k - .5) * .38, 100 * rate + 1.2, f"{100*rate:.1f}%\nn={n:,}",
                    ha="center", fontsize=7)
    ax.set_ylim(0, 100 * t1[t1.pay_tier.isin(tiers)].relo_rate.max() * 1.3)
    ax.set_xticks(x, [f"{t}/h" for t in tiers])
    ax.set_ylabel("% of postings offering relocation help")
    ax.set_xlabel("posted pay (hourly-equivalent midpoint, E3 parser)")
    ax.set_title("Relocation offers by posted pay tier (Indeed, California)")
    ax.legend(fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGS / "relocation_by_paytier.png", dpi=160)

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    t = t2.pivot(index="occ_broad", columns="region", values="relo_rate").fillna(0)
    nn = t2.pivot(index="occ_broad", columns="region", values="n").fillna(0)
    t = t.sort_values("Bay Area")
    y = np.arange(len(t))
    ax.barh(y + .2, 100 * t["Bay Area"], .4, color="#2a6f97", label="Bay Area")
    ax.barh(y - .2, 100 * t["Rest of CA"], .4, color="#a0a0a0", label="Rest of CA")
    ax.set_yticks(y, [f"{i} (Bay n={int(nn.loc[i,'Bay Area']):,})" for i in t.index], fontsize=8)
    ax.set_xlabel("% of postings offering relocation help")
    ax.set_title("Relocation offers by occupation group (title regex)")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGS / "relocation_by_occupation.png", dpi=160)


if __name__ == "__main__":
    main()
