"""Download ACS 1-year PUMS (California person + housing files) and keep the 9 Bay Area counties.

Years 2018, 2019, 2021-2024 (the 2020 1-year file was experimental and is skipped).
Raw zips land in ../raw/ (untrusted data, never executed); slim parquet extracts in ../data/.
Bay Area = California PUMAs whose first three digits are a Bay county FIPS code; this holds
for both the 2010 PUMA vintage (2018-2021 files) and the 2020 vintage (2022+ files).
"""
import os
import subprocess
import zipfile
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, DATA = os.path.join(BASE, "raw"), os.path.join(BASE, "data")
YEARS = [2018, 2019, 2021, 2022, 2023, 2024]
URL = "https://www2.census.gov/programs-surveys/acs/data/pums/{y}/1-Year/csv_{k}.zip"
BAY = {1: "Alameda", 13: "Contra Costa", 41: "Marin", 55: "Napa", 75: "San Francisco",
       81: "San Mateo", 85: "Santa Clara", 95: "Solano", 97: "Sonoma"}
P_COLS = ["SERIALNO", "SPORDER", "ST", "STATE", "PUMA", "AGEP", "ESR", "COW", "WAGP", "WKHP",
          "WKWN", "WKW", "OCCP", "ADJINC", "PWGTP"] + [f"PWGTP{i}" for i in range(1, 81)]
H_COLS = ["SERIALNO", "ST", "STATE", "PUMA", "NP", "TEN", "GRNTP", "GRPIP", "HINCP", "BDSP", "MV",
          "WGTP", "ADJHSG", "ADJINC"]


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    print("downloading", url, flush=True)
    subprocess.run(["curl", "-sSfL", "--retry", "3", "-o", dest + ".part", url], check=True)
    os.replace(dest + ".part", dest)


def read_bay(zpath, cols):
    out = []
    with zipfile.ZipFile(zpath) as z:
        for name in sorted(n for n in z.namelist() if n.lower().endswith(".csv")):
            with z.open(name) as f:
                header = f.readline().decode().strip().split(",")
            use = [c for c in cols if c in header]
            with z.open(name) as f:
                for chunk in pd.read_csv(f, usecols=use, dtype={"SERIALNO": str},
                                         chunksize=400_000, low_memory=False):
                    chunk = chunk.rename(columns={"STATE": "ST"})  # renamed in the 2023 file
                    out.append(chunk[(chunk.ST == 6) & (chunk.PUMA // 100).isin(BAY)])
    return pd.concat(out, ignore_index=True)


def main():
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)
    for y in YEARS:
        for kind, cols, tag in [("pca", P_COLS, "p"), ("hca", H_COLS, "h")]:
            dest = os.path.join(DATA, f"{tag}_{y}.parquet")
            if os.path.exists(dest):
                continue
            zpath = os.path.join(RAW, f"csv_{kind}_{y}.zip")
            fetch(URL.format(y=y, k=kind), zpath)
            df = read_bay(zpath, cols)
            df["YEAR"] = y
            df.to_parquet(dest)
            print(y, kind, len(df), flush=True)


if __name__ == "__main__":
    main()
