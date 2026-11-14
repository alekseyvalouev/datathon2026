"""E1: composition vs. people effects in Bay Area AGI per return (IRS SOI county migration).

Usage: python3 -I scripts/analyze.py <raw_dir> <out_dir>

See README.md for the identity. All AGI in IRS migration files is from the *year-2* return
(IRS users guide, sections E.3/E.4: "The number of individuals and AGI are based on the year 2 tax return").
File "YYZZ" = returns filed in calendar years 20YY and 20ZZ -> year-2 AGI is tax year 20ZZ-1.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

RAW = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

BAY = {1: "Alameda", 13: "Contra Costa", 41: "Marin", 55: "Napa", 75: "San Francisco",
       81: "San Mateo", 85: "Santa Clara", 95: "Solano", 97: "Sonoma"}
CV = {67: "Sacramento", 77: "San Joaquin", 99: "Stanislaus", 47: "Merced", 19: "Fresno"}
FILES = ["1112", "1213", "1314", "1415", "1516", "1617", "1718", "1819", "1920", "2021", "2122", "2223"]
METHOD_BREAK = "2223"  # 2022-23: new matching method (~+5% returns), new disclosure rules


def ty(f):  # tax year of the year-2 AGI
    return 2000 + int(f[2:]) - 1


def load(kind, f):
    d = pd.read_csv(RAW / f"county{kind}{f}.csv", encoding="latin-1")
    d.columns = [c.lower() for c in d.columns]
    if kind == "inflow":
        d = d.rename(columns={"y2_statefips": "hs", "y2_countyfips": "hc", "y1_statefips": "os",
                              "y1_countyfips": "oc", "y1_state": "ost", "y1_countyname": "oname"})
    else:
        d = d.rename(columns={"y1_statefips": "hs", "y1_countyfips": "hc", "y2_statefips": "os",
                              "y2_countyfips": "oc", "y2_state": "ost", "y2_countyname": "oname"})
    d = d[d.hs == 6].copy()  # California home counties only
    d["file"] = f
    d["ty"] = ty(f)
    for c in ["n1", "n2", "agi"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d


rows, dest_rows, supp = [], [], []
for f in FILES:
    inf, outf = load("inflow", f), load("outflow", f)
    for d, kind in [(inf, "inflow"), (outf, "outflow")]:
        b = d[d.hc.isin(BAY)]
        supp.append(dict(file=f, kind=kind, bay_rows=len(b), suppressed_rows=int((b.n1 < 0).sum())))
    # counties
    for c, name in BAY.items():
        i = inf[inf.hc == c]
        o = outf[outf.hc == c]
        S_in = i[(i.os == 6) & (i.oc == c)].iloc[0]
        S_out = o[(o.os == 6) & (o.oc == c)].iloc[0]
        assert S_in.n1 == S_out.n1 and S_in.agi == S_out.agi, (f, c)
        I = i[(i.os == 96) & (i.oc == 0)].iloc[0]
        O = o[(o.os == 96) & (o.oc == 0)].iloc[0]
        rows.append(dict(unit=name, file=f, ty=int(ty(f)),
                         n_stay=S_in.n1, agi_stay=S_in.agi, n_in=I.n1, agi_in=I.agi,
                         n_out=O.n1, agi_out=O.agi))
        dest_rows.append(o.assign(origin=name))
    # region: flows between bay counties are internal (become "stayers")
    bi = inf[inf.hc.isin(BAY)]
    bo = outf[outf.hc.isin(BAY)]
    intra_in = bi[(bi.os == 6) & bi.oc.isin(BAY) & (bi.oc != bi.hc) & (bi.n1 > 0)]
    intra_out = bo[(bo.os == 6) & bo.oc.isin(BAY) & (bo.oc != bo.hc) & (bo.n1 > 0)]
    nonmig = bi[(bi.os == 6) & (bi.oc == bi.hc)]
    tot_in = bi[(bi.os == 96) & (bi.oc == 0)]
    tot_out = bo[(bo.os == 96) & (bo.oc == 0)]
    rows.append(dict(unit="Bay Area (9-county region)", file=f, ty=int(ty(f)),
                     n_stay=nonmig.n1.sum() + intra_in.n1.sum(), agi_stay=nonmig.agi.sum() + intra_in.agi.sum(),
                     n_in=tot_in.n1.sum() - intra_in.n1.sum(), agi_in=tot_in.agi.sum() - intra_in.agi.sum(),
                     n_out=tot_out.n1.sum() - intra_out.n1.sum(), agi_out=tot_out.agi.sum() - intra_out.agi.sum(),
                     intra_bay_moves_in_file=intra_in.n1.sum(), intra_bay_moves_out_file=intra_out.n1.sum()))

g = pd.DataFrame(rows)
g["method_break"] = g.file == METHOD_BREAK
# means in $ per return (agi is in $1000s)
for k in ["stay", "in", "out"]:
    g[f"mean_{k}"] = 1000 * g[f"agi_{k}"] / g[f"n_{k}"]
g["mean_place"] = 1000 * (g.agi_stay + g.agi_in) / (g.n_stay + g.n_in)      # M: residents at end of year pair
g["mean_cohort"] = 1000 * (g.agi_stay + g.agi_out) / (g.n_stay + g.n_out)   # M*: start-of-pair residents, followed
g["place_minus_cohort"] = g.mean_place - g.mean_cohort
g["out_vs_stay_pct"] = 100 * (g.mean_out / g.mean_stay - 1)
g["in_vs_stay_pct"] = 100 * (g.mean_in / g.mean_stay - 1)
g["out_rate_pct"] = 100 * g.n_out / (g.n_stay + g.n_out)
g["in_rate_pct"] = 100 * g.n_in / (g.n_stay + g.n_in)
g.sort_values(["unit", "ty"]).to_csv(OUT / "groups_by_unit_year.csv", index=False)
pd.DataFrame(supp).to_csv(OUT / "suppression_counts.csv", index=False)

# ---- decomposition across consecutive files ----
dec = []
for u, d in g.sort_values("ty").groupby("unit"):
    d = d.set_index("ty")
    for t in d.index[:-1]:
        a, b = d.loc[t], d.loc[t + 1]
        people = b.mean_cohort - a.mean_place
        exit_ = b.mean_stay - b.mean_cohort
        entry = b.mean_place - b.mean_stay
        dec.append(dict(unit=u, ty_from=t, ty_to=t + 1, mean_from=a.mean_place, mean_to=b.mean_place,
                        change=b.mean_place - a.mean_place, people=people, exit=exit_, entry=entry,
                        composition=exit_ + entry, method_break=bool(b.method_break)))
dec = pd.DataFrame(dec)
assert np.allclose(dec.change, dec.people + dec.exit + dec.entry)
dec.to_csv(OUT / "decomposition_annual.csv", index=False)


def period(d, t0, t1):
    s = d[(d.ty_from >= t0) & (d.ty_to <= t1)]
    out = s.groupby("unit")[["change", "people", "exit", "entry", "composition"]].sum()
    first = d[d.ty_from == t0].set_index("unit").mean_from
    last = d[d.ty_to == t1].set_index("unit").mean_to
    out.insert(0, "mean_from", first)
    out.insert(1, "mean_to", last)
    out["composition_share_pct"] = 100 * out.composition / out.change
    out["period"] = f"TY{t0}->TY{t1}"
    return out.reset_index()


per = pd.concat([period(dec, 2011, 2021), period(dec, 2011, 2022), period(dec, 2016, 2021)])
per.to_csv(OUT / "decomposition_period.csv", index=False)

# ---- destinations of out-movers ----
D = pd.concat(dest_rows)
det = D[(D.os.between(1, 56)) & ~((D.os == 6) & (D.oc == D.hc)) & (D.n1 > 0)].copy()


def dgroup(r):
    if r.os == 6 and r.oc in BAY:
        return "Other Bay county"
    if r.os == 6 and r.oc in CV:
        return "Central Valley (5 counties)"
    if r.os == 6:
        return "Rest of California"
    return "Out of state"


det["dest_group"] = det.apply(dgroup, axis=1)
stay = g[g.unit.isin(BAY.values())][["unit", "file", "n_stay", "agi_stay", "n_out", "agi_out"]]


def dest_tables(files, label):
    x = det[det.file.isin(files)]
    top = (x.groupby(["origin", "os", "oc", "ost", "oname"])[["n1", "n2", "agi"]].sum().reset_index())
    top["agi_per_return"] = 1000 * top.agi / top.n1
    s = stay[stay.file.isin(files)].groupby("unit")[["n_stay", "agi_stay", "n_out", "agi_out"]].sum()
    s["mean_stay"] = 1000 * s.agi_stay / s.n_stay
    s["mean_out_all"] = 1000 * s.agi_out / s.n_out
    top = top.merge(s[["mean_stay"]], left_on="origin", right_index=True)
    top["pct_vs_stayers"] = 100 * (top.agi_per_return / top.mean_stay - 1)
    top["period"] = label
    grp = x.groupby(["origin", "dest_group"])[["n1", "agi"]].sum().reset_index()
    grp["agi_per_return"] = 1000 * grp.agi / grp.n1
    grp = grp.merge(s[["mean_stay", "mean_out_all", "n_out"]], left_on="origin", right_index=True)
    grp["share_of_out_returns_pct"] = 100 * grp.n1 / grp.n_out
    grp["pct_vs_stayers"] = 100 * (grp.agi_per_return / grp.mean_stay - 1)
    grp["period"] = label
    st = x[x.os != 6].groupby(["origin", "ost"])[["n1", "agi"]].sum().reset_index()
    st["agi_per_return"] = 1000 * st.agi / st.n1
    st = st.merge(s[["mean_stay"]], left_on="origin", right_index=True)
    st["pct_vs_stayers"] = 100 * (st.agi_per_return / st.mean_stay - 1)
    st["period"] = label
    return top, grp, st


tops, grps, sts = [], [], []
for files, label in [(FILES[:11], "files 2011-12..2021-22 pooled"), (["2122"], "2021-22"), (["2223"], "2022-23 (new method)")]:
    a, b, c = dest_tables(files, label)
    tops.append(a); grps.append(b); sts.append(c)
top = pd.concat(tops)
top.sort_values(["period", "origin", "n1"], ascending=[True, True, False]).to_csv(OUT / "destinations_county.csv", index=False)
pd.concat(grps).to_csv(OUT / "destinations_by_group.csv", index=False)
pd.concat(sts).sort_values(["period", "origin", "n1"], ascending=[True, True, False]).to_csv(OUT / "destinations_out_of_state.csv", index=False)

# residual "other flows" share (unassignable to a named county), for caveat
o2 = D[D.file.isin(FILES[:11])]
tot = o2[(o2.os == 96) & (o2.oc == 0)].groupby("origin").n1.sum()
named = det[det.file.isin(FILES[:11])].groupby("origin").n1.sum()
pd.DataFrame({"out_returns": tot, "named_county_returns": named,
              "named_share_pct": 100 * named / tot}).to_csv(OUT / "destinations_coverage.csv")
print("done")
