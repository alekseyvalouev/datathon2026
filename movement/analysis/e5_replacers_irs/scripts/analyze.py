"""E5: Who replaces the leavers? IRS SOI migration files.

Usage: python3 -I scripts/analyze.py <e1_raw_dir> <e5_raw_dir> <out_dir>

Part A (county files, read in place from E1/raw): origin mix, AGI/return, persons/return (n2/n1)
         of in-movers vs out-movers vs stayers, like-for-like replacement ratios.
Part B (state gross migration files {YYZZ}inmigall.csv in E5/raw): California age and AGI-class
         distributions of in- vs out-migrants, plus year-1 vs year-2 AGI.

All AGI in thousands of nominal dollars in the raw files; means below are in dollars.
File "YYZZ" -> year-2 AGI is tax year 20ZZ-1 (users guide: n2 and AGI are from the year-2 return).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

E1RAW, RAW, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)

BAY = {1: "Alameda", 13: "Contra Costa", 41: "Marin", 55: "Napa", 75: "San Francisco",
       81: "San Mateo", 85: "Santa Clara", 95: "Solano", 97: "Sonoma"}
REGION = "Bay Area (9-county region)"
FILES = ["1112", "1213", "1314", "1415", "1516", "1617", "1718", "1819", "1920", "2021", "2122", "2223"]
SPECIAL = {57, 58, 59, 96, 97, 98}


def ty(f):
    return 2000 + int(f[2:]) - 1


def load(kind, f):
    d = pd.read_csv(E1RAW / f"county{kind}{f}.csv", encoding="latin-1")
    d.columns = [c.lower() for c in d.columns]
    if kind == "inflow":
        m = {"y2_statefips": "hs", "y2_countyfips": "hc", "y1_statefips": "os", "y1_countyfips": "oc",
             "y1_state": "ost", "y1_countyname": "oname"}
    else:
        m = {"y1_statefips": "hs", "y1_countyfips": "hc", "y2_statefips": "os", "y2_countyfips": "oc",
             "y2_state": "ost", "y2_countyname": "oname"}
    d = d.rename(columns=m)
    d = d[(d.hs == 6) & d.hc.isin(BAY)].copy()
    for c in ["n1", "n2", "agi"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
        d.loc[d[c] < 0, c] = np.nan  # -1 = suppressed
    return d


def pick(d, s, c):
    r = d[(d.os == s) & (d.oc == c)]
    if len(r) == 0:
        return np.array([0.0, 0.0, 0.0])
    return r[["n1", "n2", "agi"]].iloc[0].fillna(0).to_numpy(float)


# ---------------------------------------------------------------- Part A: county files
cat_rows, state_rows, pair_rows = [], [], []
for f in FILES:
    inf, outf = load("inflow", f), load("outflow", f)
    for c, name in BAY.items():
        for direction, d in [("in", inf[inf.hc == c]), ("out", outf[outf.hc == c])]:
            tot, us, same, diff, frn = (pick(d, 96, 0), pick(d, 97, 0), pick(d, 97, 1),
                                        pick(d, 97, 3), pick(d, 98, 0))
            stay = pick(d, 6, c)
            bayr = d[(d.os == 6) & d.oc.isin(BAY) & (d.oc != c)]
            bay = bayr[["n1", "n2", "agi"]].fillna(0).sum().to_numpy(float)
            n_bay_supp = int(bayr.n1.isna().sum())
            cats = {"all": tot, "domestic": us, "same_state": same, "other_bay": bay,
                    "rest_of_CA": same - bay, "other_states": diff, "foreign": frn,
                    "domestic_excl_bay": us - bay, "all_excl_bay": tot - bay}
            for k, v in cats.items():
                cat_rows.append(dict(unit=name, file=f, ty=ty(f), direction=direction, cat=k,
                                     n1=v[0], n2=v[1], agi=v[2], bay_rows_suppressed=n_bay_supp))
            if direction == "in":
                cat_rows.append(dict(unit=name, file=f, ty=ty(f), direction="stay", cat="stayers",
                                     n1=stay[0], n2=stay[1], agi=stay[2], bay_rows_suppressed=0))
            # named partner rows (counties): for like-for-like pair matching and top states
            named = d[~d.os.isin(SPECIAL) & ~((d.os == 6) & (d.oc == c))].copy()
            named["unit"], named["file"], named["ty"], named["direction"] = name, f, ty(f), direction
            pair_rows.append(named[["unit", "file", "ty", "direction", "os", "oc", "ost", "oname", "n1", "n2", "agi"]])

cat = pd.DataFrame(cat_rows)
# region: intra-Bay moves are internal -> region in/out = county flows excluding other-Bay rows; stayers add intra-Bay inflows
reg = cat[cat.cat.isin(["all_excl_bay", "domestic_excl_bay", "rest_of_CA", "other_states", "foreign", "stayers", "other_bay"])]
reg = reg.groupby(["file", "ty", "direction", "cat"], as_index=False)[["n1", "n2", "agi"]].sum()
st = reg[(reg.direction == "stay")].set_index("file")[["n1", "n2", "agi"]]
ib = reg[(reg.direction == "in") & (reg.cat == "other_bay")].set_index("file")[["n1", "n2", "agi"]]
st_reg = (st + ib).reset_index().assign(direction="stay", cat="stayers")
st_reg["ty"] = st_reg.file.map(ty)
reg = reg[(reg.direction != "stay") & (reg.cat != "other_bay")].copy()
reg["cat"] = reg.cat.replace({"all_excl_bay": "all", "domestic_excl_bay": "domestic"})
reg = pd.concat([reg, st_reg], ignore_index=True)
reg["unit"] = REGION
cat = pd.concat([cat, reg], ignore_index=True)
cat["mean_agi"] = cat.agi * 1000 / cat.n1
cat["persons_per_return"] = cat.n2 / cat.n1
cat["agi_per_person"] = cat.agi * 1000 / cat.n2
cat["method_break"] = cat.file == "2223"
cat["n2_definition"] = np.where(cat.ty >= 2019, "individuals (2019-20 file on)", "exemptions")
tot = cat[cat.cat == "all"].set_index(["unit", "file", "direction"]).n1
cat["share_of_direction_total"] = [r.n1 / tot.get((r.unit, r.file, r.direction), np.nan)
                                   if r.direction != "stay" else np.nan for r in cat.itertuples()]
cat = cat.sort_values(["unit", "ty", "direction", "cat"])
cat.to_csv(OUT / "flows_by_origin_type.csv", index=False)

# sanity: region all-in / all-out / stayers must match E1 groups_by_unit_year
e1 = pd.read_csv(E1RAW.parent / "outputs" / "groups_by_unit_year.csv")
chk = []
for r in e1.itertuples():
    for dirn, col, cc in [("in", "mean_in", "all"), ("out", "mean_out", "all"), ("stay", "mean_stay", "stayers")]:
        v = cat[(cat.unit == r.unit) & (cat.file == f"{r.file:04d}") & (cat.direction == dirn) & (cat.cat == cc)].mean_agi
        chk.append(abs(float(v.iloc[0]) - getattr(r, col)))
print(f"max abs diff vs E1 group means: {max(chk):.6f}")
assert max(chk) < 1e-6

# ---- replacement ratios (in / out) by unit-year and comparison type
piv = cat[cat.direction.isin(["in", "out"])].pivot_table(index=["unit", "file", "ty", "cat"], columns="direction",
                                                       values=["n1", "mean_agi", "persons_per_return", "agi_per_person"])
piv.columns = [f"{a}_{b}" for a, b in piv.columns]
piv = piv.reset_index()
stay = cat[cat.direction == "stay"].set_index(["unit", "file"])
piv["mean_agi_stay"] = [stay.loc[(u, f), "mean_agi"] for u, f in zip(piv.unit, piv.file)]
piv["ppr_stay"] = [stay.loc[(u, f), "persons_per_return"] for u, f in zip(piv.unit, piv.file)]
piv["agi_per_person_stay"] = [stay.loc[(u, f), "agi_per_person"] for u, f in zip(piv.unit, piv.file)]
piv["replacement_ratio_per_return"] = piv.mean_agi_in / piv.mean_agi_out
piv["replacement_ratio_per_person"] = piv.agi_per_person_in / piv.agi_per_person_out
piv["method_break"] = piv.file == "2223"

# ---- partner-matched ratio: reweight in-movers' origin means to out-movers' destination mix
pairs = pd.concat(pair_rows, ignore_index=True)
pairs["file"] = pairs.file.astype(str)
pairs.to_csv(OUT / "named_partner_flows.csv", index=False)
pm = []
for (u, f), g in pairs.groupby(["unit", "file"]):
    i = g[g.direction == "in"].set_index(["os", "oc"])
    o = g[g.direction == "out"].set_index(["os", "oc"])
    j = i.join(o, lsuffix="_in", rsuffix="_out", how="inner").dropna(subset=["n1_in", "n1_out", "agi_in", "agi_out"])
    for scope, jj in [("all_named_counties", j), ("named_excl_bay", j[~((j.index.get_level_values(0) == 6) & j.index.get_level_values(1).isin(BAY))]),
                      ("named_other_bay_only", j[(j.index.get_level_values(0) == 6) & j.index.get_level_values(1).isin(BAY)])]:
        if len(jj) == 0:
            continue
        mi, mo = jj.agi_in * 1000 / jj.n1_in, jj.agi_out * 1000 / jj.n1_out
        w = jj.n1_out
        pm.append(dict(unit=u, file=f, ty=ty(f), scope=scope, partners=len(jj),
                       n_in=jj.n1_in.sum(), n_out=jj.n1_out.sum(),
                       mean_in_raw=jj.agi_in.sum() * 1000 / jj.n1_in.sum(),
                       mean_out=jj.agi_out.sum() * 1000 / jj.n1_out.sum(),
                       mean_in_reweighted_to_out_mix=(mi * w).sum() / w.sum(),
                       share_partners_in_lower=float(((mi < mo) * w).sum() / w.sum())))
pm = pd.DataFrame(pm)
pm["ratio_raw"] = pm.mean_in_raw / pm.mean_out
pm["ratio_partner_matched"] = pm.mean_in_reweighted_to_out_mix / pm.mean_out
pm.to_csv(OUT / "replacement_ratio_partner_matched.csv", index=False)
piv.to_csv(OUT / "replacement_ratios.csv", index=False)

# ---- top origin / destination states for the region and each county (named county rows only)
oos = pairs[(pairs.os != 6)].groupby(["unit", "file", "ty", "direction", "ost"], as_index=False)[["n1", "n2", "agi"]].sum()
# region = sum of county rows (out-of-state partners are never intra-Bay)
oreg = oos.groupby(["file", "ty", "direction", "ost"], as_index=False)[["n1", "n2", "agi"]].sum().assign(unit=REGION)
oos = pd.concat([oos, oreg], ignore_index=True)
oos["mean_agi"] = oos.agi * 1000 / oos.n1
oos.to_csv(OUT / "other_state_flows_named.csv", index=False)
pool = oos[(oos.ty <= 2021) & (oos.unit == REGION)].groupby(["direction", "ost"], as_index=False)[["n1", "agi"]].sum()
pool["mean_agi"] = pool.agi * 1000 / pool.n1
pw = pool.pivot(index="ost", columns="direction", values=["n1", "mean_agi"])
pw.columns = [f"{a}_{b}" for a, b in pw.columns]
pw = pw.dropna().sort_values("n1_in", ascending=False)
pw["ratio_in_over_out"] = pw.mean_agi_in / pw.mean_agi_out
pw.reset_index().to_csv(OUT / "region_state_pairs_pooled_2011_2021.csv", index=False)

# ---------------------------------------------------------------- Part B: CA gross migration (age x AGI class)
AGES = {1: "<26", 2: "26-34", 3: "35-44", 4: "45-54", 5: "55-64", 6: "65+", 0: "all"}
AGIC = {0: "all", 1: "$1-10k", 2: "$10-25k", 3: "$25-50k", 4: "$50-75k", 5: "$75-100k", 6: "$100-200k", 7: "$200k+"}
grp_rows = []
for f in FILES:
    g = pd.read_csv(RAW / f"{f}inmigall.csv", encoding="latin-1", dtype=str)
    g.columns = [c.strip().lower() for c in g.columns]
    g = g[pd.to_numeric(g.statefips, errors="coerce") == 6]
    for r in g.itertuples(index=False):
        r = r._asdict()
        for grp in ["total", "nonmig", "outflow", "inflow", "samest"]:
            for a in range(7):
                v = {k: pd.to_numeric(r.get(f"{grp}_{k}_{a}"), errors="coerce") for k in ["n1", "n2", "y1_agi", "y2_agi"]}
                grp_rows.append(dict(file=f, ty=ty(f), agi_stub=int(r["agi_stub"]), agi_class=AGIC[int(r["agi_stub"])],
                                     group=grp, age=AGES[a], **v))
ga = pd.DataFrame(grp_rows)
ga["mean_y1_agi"] = ga.y1_agi * 1000 / ga.n1
ga["mean_y2_agi"] = ga.y2_agi * 1000 / ga.n1
ga["persons_per_return"] = ga.n2 / ga.n1
ga.to_csv(OUT / "ca_gross_migration_long.csv", index=False)

allc = ga[ga.agi_stub == 0].copy()
tot_age = allc[allc.age == "all"].set_index(["file", "group"]).n1
allc["share_of_group"] = [n / tot_age[(f, g)] for n, f, g in zip(allc.n1, allc.file, allc.group)]
allc["y2_over_y1"] = allc.y2_agi / allc.y1_agi
allc.to_csv(OUT / "ca_age_profile.csv", index=False)

cls = ga[(ga.age == "all") & (ga.agi_stub > 0)].copy()
tot_c = ga[(ga.age == "all") & (ga.agi_stub == 0)].set_index(["file", "group"]).n1
cls["share_of_group"] = [n / tot_c[(f, g)] for n, f, g in zip(cls.n1, cls.file, cls.group)]
cls.to_csv(OUT / "ca_agi_class_profile.csv", index=False)

# age-standardised in/out ratio: in-migrant age-specific means reweighted to out-migrant age mix
std = []
for f, g in allc[allc.age != "all"].groupby("file"):
    i = g[g.group == "inflow"].set_index("age")
    o = g[g.group == "outflow"].set_index("age")
    n = g[g.group == "nonmig"].set_index("age")
    std.append(dict(file=f, ty=ty(f),
                    in_mean_y2=i.y2_agi.sum() * 1000 / i.n1.sum(), out_mean_y2=o.y2_agi.sum() * 1000 / o.n1.sum(),
                    nonmig_mean_y2=n.y2_agi.sum() * 1000 / n.n1.sum(),
                    in_mean_y2_at_out_age_mix=(i.mean_y2_agi * o.n1).sum() / o.n1.sum(),
                    in_mean_y1=i.y1_agi.sum() * 1000 / i.n1.sum(), out_mean_y1=o.y1_agi.sum() * 1000 / o.n1.sum(),
                    in_share_under35=i.loc[["<26", "26-34"], "n1"].sum() / i.n1.sum(),
                    out_share_under35=o.loc[["<26", "26-34"], "n1"].sum() / o.n1.sum(),
                    nonmig_share_under35=n.loc[["<26", "26-34"], "n1"].sum() / n.n1.sum(),
                    in_ppr=i.n2.sum() / i.n1.sum(), out_ppr=o.n2.sum() / o.n1.sum(), nonmig_ppr=n.n2.sum() / n.n1.sum()))
std = pd.DataFrame(std)
std["ratio_raw"] = std.in_mean_y2 / std.out_mean_y2
std["ratio_age_standardised"] = std.in_mean_y2_at_out_age_mix / std.out_mean_y2
std["method_break"] = std.file == "2223"
std.to_csv(OUT / "ca_in_vs_out_age_standardised.csv", index=False)
print("Part A/B done")
