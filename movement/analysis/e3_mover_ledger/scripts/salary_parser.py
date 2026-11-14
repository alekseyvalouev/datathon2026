"""Parse Indeed `salary_formatted` strings into hourly-equivalent pay.

Handles English and Spanish forms seen in the data:
  "$20 - $22 an hour", "From $20 an hour", "Up to $23 an hour", "$80,000 - $90,000 a year",
  "$18 - $21 por hora", "Desde $21 por hora", "Hasta $120 por hora", "... por año/mes/semana/día",
  "... a month/a week/a day", "... an hour + tips".
Conversions to hourly: year/2080, month/(2080/12 = 173.33), week/40, day/8.
Unparseable units (per mile, per session, per class, per order, per trip) -> NaN.
Returns low, high, mid hourly; "From X" -> low=high=X (open-ended, flagged), "Up to X" -> low=high=X (flagged).
"""
import re
import numpy as np
import pandas as pd

HOURS = {"hour": 1.0, "year": 2080.0, "month": 2080.0 / 12, "week": 40.0, "day": 8.0}
UNIT_RE = [
    (re.compile(r"an hour|por hora"), "hour"),
    (re.compile(r"a year|por año|por ano"), "year"),
    (re.compile(r"a month|por mes"), "month"),
    (re.compile(r"a week|por semana"), "week"),
    (re.compile(r"a day|por día|por dia"), "day"),
]
NUM_RE = re.compile(r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)")


def parse_one(s):
    """Return dict(unit, low, high, mid, kind) in hourly-equivalent dollars, or None."""
    if not isinstance(s, str) or not s.strip():
        return None
    t = s.strip().lower()
    unit = next((u for rx, u in UNIT_RE if rx.search(t)), None)
    if unit is None:
        return None
    nums = [float(x.replace(",", "")) for x in NUM_RE.findall(t)]
    if not nums:
        return None
    if t.startswith(("from", "desde")):
        kind = "from"
    elif t.startswith(("up to", "hasta")):
        kind = "upto"
    elif len(nums) >= 2:
        kind = "range"
    else:
        kind = "point"
    lo, hi = (nums[0], nums[1]) if len(nums) >= 2 else (nums[0], nums[0])
    if hi < lo:
        lo, hi = hi, lo
    h = HOURS[unit]
    return {"unit": unit, "kind": kind, "low": lo / h, "high": hi / h, "mid": (lo + hi) / 2 / h}


def parse_series(s: pd.Series) -> pd.DataFrame:
    rows = [parse_one(x) or {} for x in s]
    out = pd.DataFrame(rows, index=s.index).reindex(columns=["unit", "kind", "low", "high", "mid"])
    # plausibility filter: drop hourly-equivalent < $10 or > $300, or ranges whose high/low ratio > 4 (e.g. "$100,000 - $1,000,000")
    ratio = out["high"] / out["low"]
    bad = (out["mid"] < 10) | (out["mid"] > 300) | (ratio > 4)
    out.loc[bad, ["low", "high", "mid"]] = np.nan
    out["implausible"] = bad
    return out


if __name__ == "__main__":
    for x in ["$20 - $22 an hour", "From $20 an hour", "$80,000 - $90,000 a year", "$2,100 - $2,160 a week",
              "Desde $21 por hora", "$5,286.46 - $7,083.63 por mes", "$0.73 per mile", "$16 an hour + tips"]:
        print(x, "->", parse_one(x))
