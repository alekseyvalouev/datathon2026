"""E6 single entry point: what replaces the leaver (unit + household).
Usage: python3 analysis/e6_unit_replacement/run_all.py
Downloads (if missing) CA HCD State Income Limits PDFs 2022-2026 and Freddie Mac PMMS into raw/ (untrusted; parsed with
python -I), then runs s00..s05. Reads analysis/cache/zillow.duckdb read-only and the E2 sample parquet."""
import os, subprocess, sys, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "raw")
for d in ["outputs", "figs", "raw", "cache"]: os.makedirs(os.path.join(HERE, d), exist_ok=True)
DL = {"pmms.csv": "https://www.freddiemac.com/pmms/docs/PMMS_history.csv",
      "hcd_il2022.pdf": "https://www.hcd.ca.gov/docs/grants-and-funding/inc2k22.pdf"}
for y in (2023, 2024, 2025, 2026):
    DL[f"hcd_il{y}.pdf"] = f"https://www.hcd.ca.gov/sites/default/files/docs/grants-and-funding/income-limits-{y}.pdf"
for f, u in DL.items():
    p = os.path.join(RAW, f)
    if not os.path.exists(p):
        print("downloading", u)
        # some hosts (Freddie Mac, CA HCD) return 403 to Python's default user agent
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (compatible; datathon-reproduction)"})
        with urllib.request.urlopen(req, timeout=120) as r, open(p, "wb") as fh:
            fh.write(r.read())
steps = [("s00_extract_text.py", False), ("s01_income_limits.py", True), ("s02_income_gate.py", False),
         ("s03_tenure.py", False), ("s04_text.py", False), ("s05_hand_check_sample.py", False)]
for s, isolated in steps:
    print(f"\n===== {s} =====", flush=True)
    cmd = [sys.executable] + (["-I"] if isolated else []) + [os.path.join(HERE, s)]
    subprocess.run(cmd, check=True, cwd=HERE)
