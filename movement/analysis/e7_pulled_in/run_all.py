"""E7 single entry point: who is pulled in to replace the people priced out?

  python3 run_all.py              # from cached arrival pool + saved labels (~1 min)
  python3 run_all.py --rescan     # also re-scan the raw 5.2 GB Reddit CSV (~2 min)

Never re-runs annotation: LLM labels are stored as data in labels/raw/*.txt.
"""
import subprocess
import sys
from pathlib import Path

S = Path(__file__).parent / "scripts"
steps = (["01_scan_reddit.py"] if "--rescan" in sys.argv or not (Path(__file__).parent / "data" / "arrival_pool.parquet").exists() else []) + [
    "02_relocation_flags.py", "03_relocation_analysis.py",
    "05_arrivals_analysis.py", "06_agreement.py"]
for s in steps:
    print(f"== {s}", flush=True)
    subprocess.run([sys.executable, s], cwd=S, check=True)
print("done")
