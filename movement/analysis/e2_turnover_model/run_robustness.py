"""E2 robustness entry point (run after run_all.py; reads its outputs, never overwrites them).
s04 effective-rent target (E6 concession regex), s05 spatial holdout (leave-one-county-out, ZIP blocks),
s06 drift (recent-market features, 2025-Q4 recalibration), s07 bootstrap CIs + seed variability.
Writes outputs/robustness/ and figs/robustness/ only.  Usage:  python3 analysis/e2_turnover_model/run_robustness.py"""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
if __name__ == "__main__":
    for s in ["s04_effective_rent.py", "s05_spatial_holdout.py", "s06_drift.py", "s07_bootstrap.py"]:
        print(f"\n===== {s}", flush=True); subprocess.run([sys.executable, os.path.join(HERE, s)], check=True, cwd=HERE)
