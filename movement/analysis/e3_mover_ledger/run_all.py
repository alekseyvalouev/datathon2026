"""Single entry point for E3 (the mover's ledger).
Usage: python3 -I run_all.py [--rebuild-indeed] [--skip-model]
Steps: fetch external data -> prepare postings -> parser hand checks -> salary model + imputation -> ledger -> figures.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
os.makedirs(os.path.join(HERE, "outputs"), exist_ok=True)
import fetch_external, load_indeed, prepare_postings, hand_checks, salary_model, ledger, figs

if "--rebuild-indeed" in sys.argv:
    load_indeed.build()
fetch_external.download_files(); fetch_external.fetch_oews()
prepare_postings.main()
hand_checks.main(os.path.join(HERE, "outputs"))
if "--skip-model" not in sys.argv or not os.path.exists(os.path.join(HERE, "outputs", "postings_with_pay.parquet")):
    salary_model.main()
ledger.main()
figs.main()
print("done")
