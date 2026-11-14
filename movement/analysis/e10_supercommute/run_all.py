"""E10 super-commuting: single entry point.  python3 -I run_all.py [--skip-fetch] [--skip-aggregate]"""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "scripts")
def run(name, *args):
    print(f"== {name}", flush=True)
    subprocess.run([sys.executable, "-I", os.path.join(S, name), *args], check=True, cwd=HERE)
if "--skip-fetch" not in sys.argv:
    run("fetch.py"); run("fetch_extra.py")
if "--skip-aggregate" not in sys.argv:
    run("aggregate.py")
run("analyze.py"); run("figs.py"); run("hand_check.py", "2024")
