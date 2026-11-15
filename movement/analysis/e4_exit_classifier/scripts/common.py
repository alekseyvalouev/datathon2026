"""Shared constants, regexes and helpers for E4 (exit-story classifier)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import os  # noqa: E402
# Raw data lives outside git: DATATHON_DATA, default <repo>/data (see scripts/setup_data.sh)
DATA_DIR = Path(os.environ.get("DATATHON_DATA") or ROOT.parents[2] / "data")
RAW_CSV = DATA_DIR / "reddit_posts.csv"
DATA = ROOT / "data"
LABELS = ROOT / "labels"
OUT = ROOT / "outputs"
FIGS = ROOT / "figs"
for d in (DATA, LABELS, OUT, FIGS):
    d.mkdir(exist_ok=True)

# ---------------------------------------------------------------- subreddits
BAY_SUBS = {
    "bayarea", "sanfrancisco", "oakland", "oaklandca", "berkeley", "berkeleyca",
    "sanjose", "eastbay", "bayarearealestate", "sfbayhousing", "southsanfrancisco",
    "whereinsanfrancisco", "sanfranciscosecrets", "bayareaents", "avessfbayarea",
    "sanfranciscoweddings", "oaklandfood",
}
FIN_SUBS = {
    "povertyfinance", "personalfinance", "frugal", "housing", "section8publichousing",
    "homeless", "almosthomeless", "housingcrisis", "ushousingmarket", "realestate",
    "firsttimehomebuyer", "renting", "frugal_jerk", "frugalfemalefashion",
    "frugalmalefashion", "antiwork", "austinhousing", "atlhousing", "bostonhousing",
    "nychousinglottery",
}
# every other subreddit is "work/other" (jobs, careerguidance, opinion, news, sports ...)


def sub_group(sub: str) -> str:
    s = (sub or "").lower()
    if s in BAY_SUBS:
        return "bay_local"
    if s in FIN_SUBS:
        return "finance_housing"
    return "work_other"


# ---------------------------------------------------------------- regexes
# Origin terms: the Bay Area / California
BAY_CA = (r"bay ?area|the bay\b|\bsf\b|san francisco|\boakland|berkeley|san jose|east bay|"
          r"south bay|north bay|peninsula|silicon valley|marin|alameda|contra costa|"
          r"santa clara|san mateo|fremont|hayward|richmond|vallejo|daly city|sunnyvale|"
          r"mountain view|palo alto|walnut creek|concord|antioch|california|\bcali\b|\bca\b|"
          r"\bhcol\b|\bvhcol\b")
# Movement / leaving terms (recall oriented)
MOVE = (r"\bmov(e|ed|ing)\b|\brelocat\w*|\bleav(e|ing)\b|\bleft\b|priced out|"
        r"\bpushed out|\bforced out|\bexodus|\bfled\b|\bflee\w*|got out of|"
        r"\bout of state\b|\bcheaper (state|city|area|place)|\bescap\w+|\btransplant")
RE_BAY = re.compile(BAY_CA, re.I)
RE_MOVE = re.compile(MOVE, re.I)
# Stronger exit pattern used for Bay-local subs where the Bay is implicit
RE_EXIT_IMPLICIT = re.compile(
    r"(mov(e|ed|ing) (out|away|back|to (sac|sacramento|texas|tx|arizona|az|nevada|nv|oregon|"
    r"or\b|washington|wa\b|idaho|colorado|florida|north carolina|nc\b|tennessee|another state|"
    r"the midwest|the east coast|stockton|modesto|tracy|manteca|fresno|reno|vegas|las vegas|"
    r"austin|portland|seattle|boise|phoenix|denver))|priced out|out of state|relocat\w+|"
    r"leav(e|ing) (the bay|sf|california|ca\b|the area|the state)|left (the bay|sf|california|"
    r"ca\b|the area|the state))", re.I)

# The naive regex from the earlier exploration (baseline a)
RE_NAIVE = re.compile(
    r"moving out of|leaving the bay|left the bay|priced out|"
    r"moved to (sacramento|texas|arizona|nevada|oregon|idaho|stockton|tracy|reno|boise|austin|"
    r"portland|seattle|florida|north carolina|tennessee|colorado)", re.I)
RE_PAST = re.compile(r"\b(moved|left|we left|i left|relocated|got out)\b", re.I)


def in_pool(text: str, group: str) -> bool:
    if not text:
        return False
    if RE_MOVE.search(text) and RE_BAY.search(text):
        return True
    if group == "bay_local" and RE_EXIT_IMPLICIT.search(text):
        return True
    return False


def naive_rule(text: str, group: str) -> str:
    """Baseline (a): naive regex + place mention (implicit in Bay subs)
    -> LEFT if past tense, CONSIDERING otherwise, else OTHER."""
    if text and RE_NAIVE.search(text) and (group == "bay_local" or RE_BAY.search(text)):
        return "LEFT" if RE_PAST.search(text) else "CONSIDERING"
    return "OTHER"


CLASSES = ["LEFT", "CONSIDERING", "OTHER"]
REASONS = ["housing_cost", "jobs_wages", "cost_of_living_other", "family", "schools",
           "safety_quality_of_life", "remote_work", "other"]
DEST_BUCKETS = ["other_bay_county", "sacramento_central_valley", "other_ca",
                "out_of_state", "abroad", "unknown"]
