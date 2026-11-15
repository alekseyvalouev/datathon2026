"""Shared paths, regexes and helpers for E7 (who is pulled in)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT.parent
REPO = ANALYSIS.parent
import os  # noqa: E402
DATA_DIR = Path(os.environ.get("DATATHON_DATA") or REPO.parent / "data")   # see scripts/setup_data.sh
RAW_REDDIT = DATA_DIR / "reddit_posts.csv"
INDEED_DB = ANALYSIS / "cache" / "indeed.duckdb"
E3 = ANALYSIS / "e3_mover_ledger"
E4 = ANALYSIS / "e4_exit_classifier"
E2 = ANALYSIS / "e2_turnover_model"
GM_DIR = DATA_DIR / "datathon_pack"
DATA, OUT, FIGS, LABELS = ROOT / "data", ROOT / "outputs", ROOT / "figs", ROOT / "labels"
for d in (DATA, OUT, FIGS, LABELS, LABELS / "raw"):
    d.mkdir(exist_ok=True)

# reuse E4's subreddit grouping (bay_local / finance_housing / work_other)
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("e4common", E4 / "scripts" / "common.py")
_e4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_e4)
sub_group, BAY_SUBS = _e4.sub_group, _e4.BAY_SUBS

# Bay place terms (destination side). Cities + common Bay shorthands.
BAY_PLACE = (r"(the )?bay ?area|the bay\b|sf bay|\bsf\b|san francisco|\bsan fran\b|"
             r"oakland|berkeley|san jose|east bay|south bay|north bay|the peninsula|"
             r"silicon valley|marin|alameda|fremont|hayward|daly city|sunnyvale|mountain view|"
             r"palo alto|menlo park|redwood city|san mateo|santa clara|cupertino|milpitas|"
             r"walnut creek|emeryville|richmond|san rafael|burlingame|san bruno|pleasanton|"
             r"dublin|livermore|campbell|los gatos|foster city|south san francisco|\bssf\b|"
             r"san leandro|albany|el cerrito|concord|lafayette|orinda")
SUBJ = (r"\b(i|we|i've|we've|i'm|we're|i am|we are|i just|we just|"
        r"my (?:wife|husband|partner|spouse|fianc[eé]e?|girlfriend|boyfriend|family|bf|gf) and i)\b")
MOVEV = (r"(moved|moving|move|relocated|relocating|relocate|transplanted|came|coming|"
         r"transferred|transferring)")
# A: first-person subject + move verb + to/into + Bay place
RE_A = re.compile(SUBJ + r"[^.!?\n]{0,40}?\b" + MOVEV + r"\b[^.!?\n]{0,20}?\b(to|into)\s+(" +
                  BAY_PLACE + r")", re.I)
# B: newcomer phrases (place either in phrase or implicit in a Bay subreddit)
RE_B_PLACE = re.compile(r"\b(new to|newcomer to|transplant (to|in)|just (arrived|landed) in|"
                        r"new (resident|transplant) (of|in|to))\s+(" + BAY_PLACE + r")", re.I)
RE_B_IMPLICIT = re.compile(
    r"\b(i|we)\b[^.!?\n]{0,25}?\b(just|recently|finally)? ?(moved|relocated) here\b|"
    r"\b(i'?m|we'?re|i am|we are) (new|moving) here\b|\bnew to the (area|city)\b|"
    r"\brecent transplant\b|\b(i|we) (am|are|'m|'re) (moving|relocating) here\b", re.I)
# C: job offer / admission in the Bay + move word
RE_C = re.compile(r"\b(offer|accepted|admitted|admission|position|internship|new job|got a job|"
                  r"transfer|residency|grad school|phd)\b[^.!?\n]{0,60}?\b(in|at|to)\s+(" +
                  BAY_PLACE + r")", re.I)
RE_MOVEWORD = re.compile(r"\b(mov(e|ed|ing)|relocat\w*)\b", re.I)


def arrival_tier(text: str, group: str) -> str | None:
    """Recall-oriented arrival pattern -> tier label or None."""
    if not text:
        return None
    if RE_A.search(text):
        return "A_first_person_move_to_bay"
    if RE_B_PLACE.search(text):
        return "B_newcomer_place"
    if group == "bay_local" and RE_B_IMPLICIT.search(text):
        return "B_newcomer_implicit"
    if RE_C.search(text) and RE_MOVEWORD.search(text):
        return "C_offer_in_bay"
    return None
