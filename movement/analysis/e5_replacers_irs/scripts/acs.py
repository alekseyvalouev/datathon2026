"""ACS 2018-22 5-yr (B07010 mobility x individual income, B07013 mobility x tenure), Bay counties.
Usage: python3 -I scripts/acs.py <acs_raw_dir> <out_dir>
Person-level, current residence. Sums of estimates across counties; MOEs not propagated (shown per county)."""
import sys
from pathlib import Path
import pandas as pd
A, OUT = Path(sys.argv[1]), Path(sys.argv[2])
BAY = {"001": "Alameda", "013": "Contra Costa", "041": "Marin", "055": "Napa", "075": "San Francisco",
       "081": "San Mateo", "085": "Santa Clara", "095": "Solano", "097": "Sonoma"}
GROUPS = {"same_house": 0, "moved_within_county": 1, "from_other_CA_county": 2, "from_other_state": 3, "from_abroad": 4}
rows = []
for t in ["b07010", "b07013"]:
    d = pd.read_csv(A / f"bay_{t}.dat", sep="|", dtype=str)
    d["county"] = d.GEO_ID.str[-3:].map(BAY)
    for c in d.columns:
        if c.startswith("B07"):
            d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.set_index("county")
    d.loc["Bay Area (9 counties)"] = d.drop(columns="GEO_ID").sum()
    for u, r in d.iterrows():
        for g, k in GROUPS.items():
            if t == "b07010":
                base = 12 + 11 * k  # header cell of block: total, no income, with income, 8 bins
                tot, noinc, withinc, top = (r[f"B07010_E{base:03d}"], r[f"B07010_E{base+1:03d}"],
                                            r[f"B07010_E{base+2:03d}"], r[f"B07010_E{base+10:03d}"])
                rows.append(dict(unit=u, group=g, table="B07010", persons_15plus=tot,
                                 share_no_income=noinc / tot, share_75k_plus_of_with_income=top / withinc,
                                 share_under_25k_of_with_income=sum(r[f"B07010_E{base+i:03d}"] for i in (3, 4, 5)) / withinc))
            else:
                base = 4 + 3 * k
                tot, own, rent = r[f"B07013_E{base:03d}"], r[f"B07013_E{base+1:03d}"], r[f"B07013_E{base+2:03d}"]
                rows.append(dict(unit=u, group=g, table="B07013", persons_in_households=tot, share_renter=rent / tot))
x = pd.DataFrame(rows)
w = x[x.table == "B07010"].drop(columns=["table", "persons_in_households", "share_renter"]).merge(
    x[x.table == "B07013"][["unit", "group", "persons_in_households", "share_renter"]], on=["unit", "group"])
tot = w.groupby("unit").persons_15plus.transform("sum")
movers_in = w[w.group.isin(["from_other_CA_county", "from_other_state", "from_abroad"])].groupby("unit").persons_15plus.transform("sum")
w["share_of_all_15plus"] = w.persons_15plus / tot
w.loc[w.group.isin(["from_other_CA_county", "from_other_state", "from_abroad"]), "share_of_in_movers"] = w.persons_15plus / movers_in
w.to_csv(OUT / "acs_2018_22_mobility_income_tenure.csv", index=False)
print(w[w.unit.isin(["Bay Area (9 counties)", "San Francisco", "Santa Clara"])].round(3).to_string())
