"""Single entry point for E4 (exit-story classifier).

  python3 run_all.py                 # rerun modelling + analysis from saved labels
  python3 run_all.py --rebuild-pool  # also re-scan the 5.2 GB raw CSV (~2.5 min)

Annotation is NOT rerun: labels live in labels/raw/*.txt (compact) and are compiled to
labels/labels_pass1.csv / labels_pass2.csv. The sampling scripts (02, 02b, 02c, 02d)
are kept for provenance and refuse to redraw an existing sample.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
S = HERE / "scripts"


def run(*args):
    print(f"\n=== {' '.join(args)}", flush=True)
    subprocess.run([sys.executable, *args], check=True, cwd=HERE)


if __name__ == "__main__":
    if "--rebuild-pool" in sys.argv or not (HERE / "data" / "pool.parquet").exists():
        run(str(S / "01_build_pool.py"))
    run(str(S / "annot_tools.py"), "compile")
    run(str(S / "03_train_eval.py"))
    run(str(S / "04_apply_pool.py"))
    run(str(S / "05_subgroups_errors.py"))
    run(str(S / "06_figures_verify.py"))
