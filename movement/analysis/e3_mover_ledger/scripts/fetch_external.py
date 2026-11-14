"""Download external inputs into ../raw/ (skips files that already exist).
  - Zillow ZORI metro (all homes, smoothed, monthly): files.zillowstatic.com
  - Census 2020 ZCTA->county relationship file (for Indeed ZIP -> county)
  - BLS OEWS May-2025 metro hourly median (datatype 08) and mean (03) wages via the public BLS API v2
    (bulk oesm25ma.zip download returns HTTP 403 to scripts; the API works without a key, 25 series/request).
HUD FMR xlsx downloads returned HTTP 202 with an empty body, so FMR is not used.
"""
import os, json, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "raw")
os.makedirs(RAW, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (datathon research script)"}

FILES = {
    "Metro_zori_uc_sfrcondomfr_sm_month.csv": "https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv",
    "tab20_zcta520_county20_natl.txt": "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt",
}
# OEWS metro area codes = CBSA codes
OEWS_AREAS = {
    "41860": "San Francisco-Oakland-Fremont, CA", "41940": "San Jose-Sunnyvale-Santa Clara, CA",
    "40900": "Sacramento-Roseville-Folsom, CA", "44700": "Stockton-Lodi, CA", "33700": "Modesto, CA",
    "23420": "Fresno, CA", "38060": "Phoenix-Mesa-Chandler, AZ", "29820": "Las Vegas-Henderson-North Las Vegas, NV",
    "39900": "Reno, NV", "14260": "Boise City, ID", "19100": "Dallas-Fort Worth-Arlington, TX",
    "26420": "Houston-Pasadena-The Woodlands, TX", "38900": "Portland-Vancouver-Hillsboro, OR-WA",
}
OEWS_SOC = ["311131", "311120", "319092", "292052", "537062", "537065", "372011", "339032", "352014", "353023",
            "412011", "412031", "533033"]


def download_files():
    for name, url in FILES.items():
        p = os.path.join(RAW, name)
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            continue
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=120) as r, open(p, "wb") as f:
            f.write(r.read())
        print("downloaded", name)


def bls(series):
    body = json.dumps({"seriesid": series, "startyear": "2024", "endyear": "2025"}).encode()
    req = urllib.request.Request("https://api.bls.gov/publicAPI/v2/timeseries/data/", data=body,
                                 headers={"Content-Type": "application/json", **UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def fetch_oews():
    p = os.path.join(RAW, "oews_api.json")
    if os.path.exists(p):
        return
    series = [f"OEUM00{a}000000{s}{dt}" for dt in ["08", "03"] for a in OEWS_AREAS for s in OEWS_SOC]
    results = []
    for i in range(0, len(series), 25):
        js = bls(series[i:i + 25])
        if js.get("status") != "REQUEST_SUCCEEDED":
            raise RuntimeError(js)
        results += js["Results"]["series"]
        time.sleep(1)
    json.dump(results, open(p, "w"))
    print("OEWS series:", len(results))


if __name__ == "__main__":
    download_files()
    fetch_oews()
