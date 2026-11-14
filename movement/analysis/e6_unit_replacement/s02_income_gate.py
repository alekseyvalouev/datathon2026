"""Step 2 (Analysis 1): income gate for the household that takes the leaver's place.
For each E2 turnover pair: minimum qualifying income = mult x 12 x asking rent, before (last ask of the leaver's
tenancy) and after (first ask to the newcomer), compared with the CA HCD / HUD 80% ('Low') and 50% ('Very Low')
income limits for a household sized to the unit (persons = bedrooms + 1, studio = 1), in the limit year in force
at each date. Limits take effect ~June each year, so a date in [Jun Y, May Y+1] uses year Y; 2022 is the earliest
parsed year, so the year-matched (primary) sample requires the leaver's last ask on/after 2022-06-01."""
import os, re, sys, numpy as np, pandas as pd, duckdb
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

MULT_PAT = re.compile(r"income[^.$]{0,120}?\b([23](?:\.\d{1,2})?)\s*(?:x|×|times)\s*(?:the\s+)?(?:monthly\s+|total\s+)?rent"
                      r"|\b([23](?:\.\d{1,2})?)\s*(?:x|×|times)\s*(?:the\s+)?(?:monthly\s+)?rent[^.]{0,40}?income", re.I)

def stated_mult(desc):
    if not isinstance(desc, str): return np.nan
    m = MULT_PAT.search(desc)
    if not m: return np.nan
    v = float(m.group(1) or m.group(2))
    return v if 2.0 <= v <= 4.0 else np.nan

def limit_year(d):
    d = pd.to_datetime(d)
    return np.where(d.dt.month >= 6, d.dt.year, d.dt.year - 1)

def load():
    df = pd.read_parquet(E2_SAMPLE)
    ex = pd.read_parquet(os.path.join(CACHE, "extra.parquet"), columns=["zpid", "description"])
    ex["stated_mult"] = ex.description.map(stated_mult)
    d = ex.drop_duplicates("description").stated_mult.dropna()
    d.round(2).value_counts().rename_axis("stated_multiplier").rename("n_distinct_descriptions").to_csv(
        os.path.join(OUT, "a1_stated_income_multiplier_dist.csv"))
    df = df.merge(ex[["zpid", "stated_mult"]], on="zpid", how="left")
    df["hh"] = (df.beds.fillna(0).clip(0, 7) + 1).astype(int)
    il = pd.read_csv(os.path.join(OUT, "income_limits_bay.csv"))
    lim = {}
    for r in il.itertuples():
        for k in range(1, 9): lim[(r.year, r.county, r.level, k)] = getattr(r, f"p{k}")
    df["ly0"] = limit_year(df.end_d); df["ly1"] = limit_year(df.next_start)
    for lev in ["LI", "VLI", "MED"]:
        for t in ["0", "1"]:
            df[f"{lev}{t}"] = [lim.get((y, c, lev, h), np.nan) for y, c, h in zip(df[f"ly{t}"], df.county, df.hh)]
        df[f"{lev}1same"] = df[f"{lev}1"]   # same (newcomer-year) limit applied to both rents
    return df

def gate(df, mult_col, suffix=""):
    m = df[mult_col]
    df["inc0" + suffix] = m * 12 * df.last_p; df["inc1" + suffix] = m * 12 * df.next_first
    for lev in ["LI", "VLI"]:
        q0 = df["inc0" + suffix] <= df[f"{lev}0"]; q1 = df["inc1" + suffix] <= df[f"{lev}1"]
        df[f"lost_{lev}{suffix}"] = (q0 & ~q1).astype(float)
        df[f"gained_{lev}{suffix}"] = (~q0 & q1).astype(float)
        df[f"q0_{lev}{suffix}"] = q0.astype(float); df[f"q1_{lev}{suffix}"] = q1.astype(float)
        # same-limit variant: both rents judged against the newcomer-year limit (isolates the price move)
        df[f"lostsame_{lev}{suffix}"] = ((df["inc0" + suffix] <= df[f"{lev}1"]) & ~q1).astype(float)
        # counterfactual: rent had risen only at the AB 1482 maximum (10%/yr) over the gap -> still qualifiable?
        cf = m * 12 * df.last_p * 1.10 ** df.start_gap_y
        df[f"lost_turnover_{lev}{suffix}"] = (q0 & ~q1 & (cf <= df[f"{lev}1"])).astype(float)
    df["ami0" + suffix] = df["inc0" + suffix] / df.MED0; df["ami1" + suffix] = df["inc1" + suffix] / df.MED1
    return df

def summarize(d, by, sfx=""):
    g = d.groupby(by, dropna=False)
    t = g.agg(n=("zpid", "size"), med_rent0=("last_p", "median"), med_rent1=("next_first", "median"),
              med_inc0=("inc0" + sfx, "median"), med_inc1=("inc1" + sfx, "median"),
              med_ami0=("ami0" + sfx, "median"), med_ami1=("ami1" + sfx, "median"),
              q0_LI=("q0_LI" + sfx, "mean"), q1_LI=("q1_LI" + sfx, "mean"),
              lost_LI=("lost_LI" + sfx, "mean"), lost_turnover_LI=("lost_turnover_LI" + sfx, "mean"),
              q0_VLI=("q0_VLI" + sfx, "mean"), q1_VLI=("q1_VLI" + sfx, "mean"), lost_VLI=("lost_VLI" + sfx, "mean"),
              gained_LI=("gained_LI" + sfx, "mean"), gained_VLI=("gained_VLI" + sfx, "mean"))
    t["net_LI"] = t.lost_LI - t.gained_LI; t["net_VLI"] = t.lost_VLI - t.gained_VLI
    t["lost_LI_given_q0"] = t.lost_LI / t.q0_LI; t["lost_VLI_given_q0"] = t.lost_VLI / t.q0_VLI
    return t.round(4)

def main():
    df = load()
    df = df[df.beds.notna()].copy()
    df["mult3"] = df.stated_mult.fillna(3.0); df["mult25"] = 2.5
    df = gate(df, "mult3"); df = gate(df, "mult25", "_25")
    df["year1"] = pd.to_datetime(df.next_start).dt.year
    df["beds_g"] = df.beds.clip(0, 4).map({0: "0 studio", 1: "1", 2: "2", 3: "3", 4: "4+"})
    prim = df[(pd.to_datetime(df.end_d) >= "2022-06-01") & df.LI0.notna() & df.LI1.notna()].copy()
    print(f"pairs {len(df)}; primary (year-matched limits, leaver's last ask >= 2022-06) {len(prim)}; "
          f"stated multiplier found for {df.stated_mult.notna().mean():.1%} of pairs (median {df.stated_mult.median()})")
    # sample flow / overall
    rows = []
    for name, d, sfx in [("primary_3x", prim, ""), ("primary_2.5x", prim, "_25")]:
        s = summarize(d.assign(all="all"), "all", sfx).iloc[0].to_dict(); s["sample"] = name; rows.append(s)
    # same-limit variant on all 2023+ newcomer pairs (old & new rent vs newcomer-year limit)
    alt = df[df.LI1.notna()].copy()
    rows.append(dict(sample="newcomer_year_limit_both_rents_3x", n=len(alt), lost_LI=alt.lostsame_LI.mean(),
                     lost_VLI=alt.lostsame_VLI.mean(), gained_LI=((alt.inc0 > alt.LI1) & (alt.q1_LI == 1)).mean(), q0_LI=(alt.inc0 <= alt.LI1).mean(), q1_LI=alt.q1_LI.mean()))
    ov = pd.DataFrame(rows); ov.to_csv(os.path.join(OUT, "a1_income_gate_overall.csv"), index=False)
    print(ov.T.to_string())
    for by in ["county", "beds_g", "year1"]:
        t = summarize(prim, by); t.to_csv(os.path.join(OUT, f"a1_income_gate_by_{by.replace('_g','')}.csv"))
        print(t[["n", "med_ami0", "med_ami1", "q0_LI", "q1_LI", "lost_LI", "gained_LI", "net_LI", "lost_LI_given_q0",
                 "lost_turnover_LI", "lost_VLI", "gained_VLI", "lost_VLI_given_q0"]].to_string())
    t = summarize(prim, ["county", "beds_g"]); t.to_csv(os.path.join(OUT, "a1_income_gate_by_county_beds.csv"))
    # by ZIP (n >= 30), no addresses
    z = summarize(prim, ["county", "zipcode"]); z = z[z.n >= 30].sort_values("lost_LI", ascending=False)
    z.to_csv(os.path.join(OUT, "a1_income_gate_by_zip.csv"))
    keep = ["zipcode", "county", "homeType", "beds", "hh", "end_d", "next_start", "start_gap_y", "last_p", "next_first", "r",
            "stated_mult", "mult3", "LI0", "LI1", "VLI0", "VLI1", "MED0", "MED1", "inc0", "inc1", "ami0", "ami1",
            "q0_LI", "q1_LI", "lost_LI", "gained_LI", "lost_turnover_LI", "lost_VLI", "lost_LI_25", "lost_VLI_25"]
    prim[keep].to_parquet(os.path.join(OUT, "a1_pairs_primary.parquet"), index=False)
    figs(prim)

def figs(p):
    # Fig 1: required income as share of AMI, before vs after, by county
    c = p.groupby("county")[["ami0", "ami1"]].median().sort_values("ami1")
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    y = np.arange(len(c))
    ax.hlines(y, c.ami0, c.ami1, color="#bbb", lw=2)
    ax.scatter(c.ami0, y, color="#4a7fb5", label="leaver's rent", zorder=3)
    ax.scatter(c.ami1, y, color="#c0392b", label="newcomer's rent", zorder=3)
    ax.axvline(0.8, color="#555", ls="--", lw=1); ax.text(0.805, -0.6, "80% AMI", fontsize=8, color="#555")
    ax.set_yticks(y, [s.replace(" County", "") for s in c.index]); ax.set_xlabel("income needed at 3x rent, share of area median (same household size)")
    ax.set_title("Same unit, next tenant: income needed to qualify (median)", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="lower right"); fig.tight_layout(); fig.savefig(os.path.join(FIG, "a1_ami_needed_by_county.png"), dpi=150); plt.close(fig)
    # Fig 2: share of turnovers that priced the unit out of a <=80% / <=50% household, by county
    t = p.groupby("county")[["lost_LI", "lost_VLI", "lost_turnover_LI"]].mean().sort_values("lost_LI")
    fig, ax = plt.subplots(figsize=(7.5, 4.2)); y = np.arange(len(t)); h = 0.38
    ax.barh(y + h / 2, t.lost_LI * 100, h, color="#c0392b", label="lost <=80% AMI qualifiability")
    ax.barh(y - h / 2, t.lost_VLI * 100, h, color="#e8a29a", label="lost <=50% AMI qualifiability")
    ax.set_yticks(y, [s.replace(" County", "") for s in t.index]); ax.set_xlabel("% of turnovers (leaver's last ask >= Jun 2022)")
    ax.legend(frameon=False, fontsize=8, loc="lower right"); ax.set_title("Turnovers that priced the unit out of reach of a low-income household of the unit's size", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "a1_lost_qualifiability_by_county.png"), dpi=150); plt.close(fig)

if __name__ == "__main__":
    main()
