"""Shared paths/constants for E8 (where can a displaced low-income household re-rent, and what access do they give up)."""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA_DIR = os.environ.get("DATATHON_DATA") or os.path.join(os.path.dirname(ROOT), "data")   # see scripts/setup_data.sh
DATA = os.path.join(DATA_DIR, "datathon_pack")
PLACES_CSV = os.path.join(DATA, "google maps dataset/google_maps.csv")
REVIEWS_CSV = os.path.join(DATA, "google maps reviews dataset/google_maps_reviews.csv")
DB = os.path.join(ROOT, "analysis/cache/zillow.duckdb")
E6_LIMITS = os.path.join(ROOT, "analysis/e6_unit_replacement/outputs/income_limits_bay.csv")
E2_EXT = os.path.join(ROOT, "analysis/e2_turnover_model/external")       # UDP typology + 2018 TIGER tracts
E2_ZIPS = os.path.join(ROOT, "analysis/e2_turnover_model/outputs/zip_reentry_cost.csv")
OUT = os.path.join(HERE, "outputs"); FIG = os.path.join(HERE, "figs"); CACHE = os.path.join(HERE, "cache")
SEED = 42
EARTH_M = 6371008.8
LIMIT_YEAR = 2026          # Zillow snapshot runs to 2026-11-13 -> HCD 2026 limits (in force Jun 2026 - May 2027)
CATS = ["grocery", "clinic", "pharmacy", "transit", "foodbank", "bank", "afs"]
RADII = [400, 800, 1600]

# service-desert thresholds (justified in README)
TH = {"grocery": 1609.0,   # USDA Food Access Research Atlas urban low-access line: > 1 mile from a supermarket/grocery
      "clinic": 3218.0,    # 2 miles: ~40 min walk / beyond a short bus ride; no federal standard -> 2x the grocery line
      "transit": 800.0}    # 1/2 mile: standard walk-shed for transit (CA "major transit stop" / TOD buffers)


def haversine_m(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_M * np.arcsin(np.sqrt(a))


def ensure_dirs():
    for d in (OUT, FIG, CACHE): os.makedirs(d, exist_ok=True)
