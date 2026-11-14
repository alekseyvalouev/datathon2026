"""Small keyless downloads that depend on the Census centers-of-population file:
 - OSRM public demo server table: driving distance (m) and free-flow duration (s) from every CA county
   center of population to each of the 9 Bay county centers -> raw/osrm_table.json
 - BLS CPI-U (CUUR0000SA0) monthly 2010-2024 via the public v1 API -> raw/cpi_*.json"""
import os, json, subprocess, sys, csv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "raw")
BAY = ["06001","06013","06041","06055","06075","06081","06085","06095","06097"]

def read_cenpop():
    rows = []
    with open(os.path.join(RAW, "CenPop2020_Mean_CO06.txt"), encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            r = {k.strip(): v.strip() for k, v in r.items()}
            rows.append(dict(fips=r["STATEFP"] + r["COUNTYFP"], name=r["COUNAME"],
                             pop=int(r["POPULATION"]), lat=float(r["LATITUDE"]), lon=float(r["LONGITUDE"])))
    return rows

def osrm():
    dest = os.path.join(RAW, "osrm_table.json")
    if os.path.exists(dest) and os.path.getsize(dest) > 0: return
    rows = read_cenpop()
    coords = ";".join(f"{r['lon']:.6f},{r['lat']:.6f}" for r in rows)
    dst_idx = ";".join(str(i) for i, r in enumerate(rows) if r["fips"] in BAY)
    url = (f"https://router.project-osrm.org/table/v1/driving/{coords}"
           f"?destinations={dst_idx}&annotations=distance,duration")
    r = subprocess.run(["curl", "-sfL", "--retry", "3", "-o", dest + ".part", url])
    if r.returncode != 0:
        print("FAILED osrm table (fallback: haversine x circuity)", file=sys.stderr); return
    d = json.load(open(dest + ".part"))
    d["_order"] = [r["fips"] for r in rows]
    json.dump(d, open(dest, "w")); os.remove(dest + ".part"); print("got osrm_table.json")

def cpi():
    for a, b in [(2010, 2019), (2020, 2024)]:
        dest = os.path.join(RAW, f"cpi_{a}_{b}.json")
        if os.path.exists(dest) and os.path.getsize(dest) > 0: continue
        body = json.dumps({"seriesid": ["CUUR0000SA0"], "startyear": str(a), "endyear": str(b)})
        r = subprocess.run(["curl", "-sfL", "-X", "POST", "-H", "Content-Type: application/json",
                            "--data-binary", body, "-o", dest,
                            "https://api.bls.gov/publicAPI/v1/timeseries/data/"])
        print("got" if r.returncode == 0 else "FAILED", dest)

if __name__ == "__main__":
    osrm(); cpi()
