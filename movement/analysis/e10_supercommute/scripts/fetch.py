"""Download LODES8 CA OD main files + Census 2020 county centers of population into raw/.
Skips files already present (size>0)."""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "raw")
BASE = "https://lehd.ces.census.gov/data/lodes/LODES8/ca/od/"
YEARS = list(range(2010, 2025))
JT01_YEARS = [2010, 2019, 2024]
CENPOP = "https://www2.census.gov/geo/docs/reference/cenpop2020/county/CenPop2020_Mean_CO06.txt"

def get(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    tmp = dest + ".part"
    r = subprocess.run(["curl", "-sfL", "--retry", "3", "-o", tmp, url])
    if r.returncode != 0:
        print("FAILED", url, file=sys.stderr); return
    os.replace(tmp, dest); print("got", os.path.basename(dest))

def main():
    os.makedirs(RAW, exist_ok=True)
    jobs = [(f"{BASE}ca_od_main_JT00_{y}.csv.gz", os.path.join(RAW, f"ca_od_main_JT00_{y}.csv.gz")) for y in YEARS]
    jobs += [(f"{BASE}ca_od_main_JT01_{y}.csv.gz", os.path.join(RAW, f"ca_od_main_JT01_{y}.csv.gz")) for y in JT01_YEARS]
    # aux = CA workplace, out-of-state residence (needed for complete Bay job denominator)
    jobs += [(f"{BASE}ca_od_aux_JT00_{y}.csv.gz", os.path.join(RAW, f"ca_od_aux_JT00_{y}.csv.gz")) for y in YEARS]
    jobs.append((CENPOP, os.path.join(RAW, "CenPop2020_Mean_CO06.txt")))
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(lambda a: get(*a), jobs))

if __name__ == "__main__":
    main()
