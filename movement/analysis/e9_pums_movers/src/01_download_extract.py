"""Download ACS 1-year PUMS (US person + housing files) and extract a slim analysis extract.

Keeps: persons who live in California now (ST==6) OR lived in California one year ago (MIGSP==6),
plus matching household records. Writes parquet files to ../data/.
Raw downloads land in ../raw/ (treated as untrusted data; never executed).
"""
import os
import sys
import zipfile
import subprocess
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
RAW = os.path.join(BASE, "raw")
DATA = os.path.join(BASE, "data")
os.makedirs(RAW, exist_ok=True)
os.makedirs(DATA, exist_ok=True)

YEARS = [int(y) for y in os.environ.get("E9_YEARS", "2022,2023,2024").split(",")]
URL = "https://www2.census.gov/programs-surveys/acs/data/pums/{y}/1-Year/csv_{k}.zip"
XWALK = {
    "puma_migpuma1_pwpuma00_2020.xls": "https://usa.ipums.org/usa/resources/volii/puma_migpuma1_pwpuma00_2020.xls",
    "county_migpuma_pwpuma_2022.xls": "https://usa.ipums.org/usa/resources/volii/county_migpuma_pwpuma_2022.xls",
}

P_COLS = ["SERIALNO", "SPORDER", "ST", "STATE", "PUMA", "PUMA20", "MIG", "MIGSP", "MIGPUMA", "MIGPUMA20",
          "AGEP", "SEX", "RAC1P", "HISP", "SCHL", "ESR", "WAGP", "PINCP", "POVPIP", "JWMNP", "JWTRNS",
          "MAR", "RELSHIPP", "NATIVITY", "DIS", "WKHP", "ADJINC", "PWGTP"] + [f"PWGTP{i}" for i in range(1, 81)]
H_COLS = ["SERIALNO", "NP", "TEN", "GRPIP", "GRNTP", "HINCP", "RMSP", "BDSP", "HHT", "HUPAC", "WGTP",
          "TYPEHUGQ", "TYPE", "ADJHSG", "ADJINC"]


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    print("downloading", url, flush=True)
    subprocess.run(["curl", "-sSfL", "--retry", "3", "-o", dest + ".part", url], check=True)
    os.replace(dest + ".part", dest)


def read_filtered(zpath, cols, keep_fn):
    out = []
    with zipfile.ZipFile(zpath) as z:
        for name in sorted(n for n in z.namelist() if n.lower().endswith(".csv")):
            with z.open(name) as f:
                header = f.readline().decode().strip().split(",")
            use = [c for c in cols if c in header]
            with z.open(name) as f:
                for chunk in pd.read_csv(f, usecols=use, dtype={"SERIALNO": str}, chunksize=400_000,
                                         low_memory=False):
                    out.append(keep_fn(chunk))
            print("  read", name, flush=True)
    return pd.concat(out, ignore_index=True)


def main():
    for fn, url in XWALK.items():
        fetch(url, os.path.join(RAW, fn))
    for y in YEARS:
        pout = os.path.join(DATA, f"persons_{y}.parquet")
        hout = os.path.join(DATA, f"housing_{y}.parquet")
        if os.path.exists(pout) and os.path.exists(hout):
            print("have", y)
            continue
        pz = os.path.join(RAW, f"csv_pus_{y}.zip")
        hz = os.path.join(RAW, f"csv_hus_{y}.zip")
        fetch(URL.format(y=y, k="pus"), pz)
        fetch(URL.format(y=y, k="hus"), hz)

        def pkeep(c):
            if "STATE" in c.columns and "ST" not in c.columns:
                c = c.rename(columns={"STATE": "ST"})
            for a, b in (("PUMA20", "PUMA"), ("MIGPUMA20", "MIGPUMA")):
                if a in c.columns and b not in c.columns:
                    c = c.rename(columns={a: b})
            return c[(c["ST"] == 6) | (c["MIGSP"] == 6)]

        p = read_filtered(pz, P_COLS, pkeep)
        p["YEAR"] = y
        serials = set(p["SERIALNO"])
        h = read_filtered(hz, H_COLS, lambda c: c[c["SERIALNO"].isin(serials)])
        if "TYPE" in h.columns and "TYPEHUGQ" not in h.columns:
            h = h.rename(columns={"TYPE": "TYPEHUGQ"})
        h = h.rename(columns={"ADJINC": "ADJINC_H"})
        h["YEAR"] = y
        p.to_parquet(pout, index=False)
        h.to_parquet(hout, index=False)
        print(y, "persons", len(p), "housing", len(h), flush=True)


if __name__ == "__main__":
    sys.exit(main())
