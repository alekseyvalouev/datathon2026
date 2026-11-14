"""50 hand-checked salary strings (2 random rows from each of the 20 most common string patterns + 10 from rarer
patterns, sampled once with fixed seeds). Expected hourly low/high were written by hand as arithmetic on the
raw string (year/2080, month*12/2080, week/40, day/8). The script compares the parser against them and writes
outputs/parser_hand_checks.csv. `note` records semantic doubts where the arithmetic is right but the
hourly-equivalent may be misleading.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from salary_parser import parse_one

Y, M, W, D = 2080, 2080 / 12, 40, 8
CHECKS = [
    ("790a1a7ce13f3bb5", "$17.28 an hour + tips", 17.28, 17.28, "tips excluded"),
    ("990627724a6885e6", "$25.03 - $33.54 por hora", 25.03, 33.54, "Spanish"),
    ("1191461aa63e182c", "$16.90 por hora", 16.90, 16.90, "CA min wage 2025"),
    ("cb2963eefbec090e", "$16.90 - $50.00 por hora", 16.90, 50.00, "very wide range; mid less meaningful"),
    ("f26b5f971a601cd9", "Desde $21 por hora", 21, 21, "open-ended 'from'"),
    ("c6223fcb2576ba42", "$25.90 an hour", 25.90, 25.90, ""),
    ("d7bc0bf67db004b9", "Up to $23 an hour", 23, 23, "open-ended 'up to' (upper bound)"),
    ("75a2642c4f6d4b22", "From $95,000 a year", 95000 / Y, 95000 / Y, ""),
    ("4231a7d545ba9104", "Hasta $117.73 por hora", 117.73, 117.73, ""),
    ("69ad1942bbe9cd7a", "$250 - $800 a day", 250 / D, 800 / D, "day rate; 8h/day assumed"),
    ("04890fcdc1225969", "$16 an hour + tips", 16, 16, "tips excluded"),
    ("2276632bf9e13932", "Desde $18 por hora", 18, 18, ""),
    ("86fe0e85610628b8", "$2,042 a week", 2042 / W, 2042 / W, "travel-nurse style weekly pay"),
    ("0302ce81b27745da", "Up to $206,000 a year", 206000 / Y, 206000 / Y, ""),
    ("662ed451cc7f2d2d", "From $100,000 a year", 100000 / Y, 100000 / Y, ""),
    ("415085eccbbbd67a", "$16.00 - $17.75 an hour + tips", 16.00, 17.75, ""),
    ("5bbafd80bb41897a", "$500 a week", 500 / W, 500 / W, "DOUBT: likely part-time weekly pay; 40h assumption understates hourly"),
    ("8bdf03012823ec18", "$5,000 - $10,000 a month", 5000 / M, 10000 / M, ""),
    ("a3d762e60fef7619", "$53,000 por año", 53000 / Y, 53000 / Y, ""),
    ("2b0b669d2c1aedaa", "$900 - $1,400 a week", 900 / W, 1400 / W, ""),
    ("cff884ac0be68d60", "$52,000 a year", 25, 25, ""),
    ("03d631f1c6a55905", "$84.64 - $122.73 a day", 84.64 / D, 122.73 / D, "DOUBT: probably a short shift/per-visit day rate"),
    ("95d9aeb985f3d463", "$550 - $650 por día", 550 / D, 650 / D, ""),
    ("2b323ce402aff4b9", "$87,840 - $109,800 a year", 87840 / Y, 109800 / Y, ""),
    ("107854821423cc34", "From $27.58 an hour", 27.58, 27.58, ""),
    ("4d7bd9e593898443", "$16 an hour + tips", 16, 16, ""),
    ("b1ed89b299371b01", "Desde $55,000 por año", 55000 / Y, 55000 / Y, ""),
    ("1844b2d0bf58b5de", "$22 an hour", 22, 22, ""),
    ("b1bd03fc02842cc9", "$92,000 - $180,000 por año", 92000 / Y, 180000 / Y, ""),
    ("d6e8890c077c89a4", "$15.50 - $16.30 an hour + tips", 15.50, 16.30, "below CA min wage: sub-minimum tipped/locality"),
    ("2f61cac9344336f1", "$5,250 - $18,000 por mes", 5250 / M, 18000 / M, "very wide range"),
    ("2a6eb0cdd1c100a5", "From $20 an hour", 20, 20, ""),
    ("11764fefc6ea2fe0", "$4,000 - $7,000 a month", 4000 / M, 7000 / M, ""),
    ("166ece0cba718702", "$800 - $2,000 por semana", 800 / W, 2000 / W, ""),
    ("5e969b6ccdcec77c", "$22 - $25 an hour", 22, 25, ""),
    ("7d09776c00e2e2df", "$600 - $800 a week", 600 / W, 800 / W, ""),
    ("37b019327051727d", "$21 por hora", 21, 21, ""),
    ("feeddd30b61acbb9", "$7,895.95 - $9,990.90 por mes", 7895.95 / M, 9990.90 / M, ""),
    ("9196666fde688db5", "$1,500 por semana", 1500 / W, 1500 / W, ""),
    ("db8bb65039c5d9f2", "Desde $85,000 por año", 85000 / Y, 85000 / Y, ""),
    ("2aa662dd675b3d4b", "$150,000 - $170,000 por año", 150000 / Y, 170000 / Y, ""),
    ("d666b866b6100e96", "$340,000 a year", 340000 / Y, 340000 / Y, ""),
    ("a4d32cc8c63124bf", "Up to $23 an hour", 23, 23, ""),
    ("fd8771494c219d15", "$1,250 - $2,500 por semana", 1250 / W, 2500 / W, ""),
    ("07c36e479124315a", "Up to $140,000 a year", 140000 / Y, 140000 / Y, ""),
    ("0a83afa8676794a5", "From $0.60 per mile", None, None, "per-mile pay: intentionally not converted"),
    ("1e205cf63174079c", "$40 - $65 per class", None, None, "per-class pay: intentionally not converted"),
    ("7ca80430938065f8", "$153,296 - $186,368 a year", 153296 / Y, 186368 / Y, ""),
    ("60931c15eebdd221", "$62,502.70 por año", 62502.70 / Y, 62502.70 / Y, ""),
    ("707f5ed257f84fa5", "$26 - $30 an hour", 26, 30, ""),
]


def main(outdir):
    rows = []
    for jid, s, lo, hi, note in CHECKS:
        p = parse_one(s) or {}
        plo, phi = p.get("low"), p.get("high")
        ok = (lo is None and plo is None) or (lo is not None and plo is not None and abs(plo - lo) < 0.01 and abs(phi - hi) < 0.01)
        rows.append(dict(jobid=jid, salary_formatted=s, expected_low=lo, expected_high=hi, parsed_low=plo, parsed_high=phi,
                         parsed_unit=p.get("unit"), parsed_kind=p.get("kind"), match=ok, note=note))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(outdir, "parser_hand_checks.csv"), index=False)
    print(f"hand checks: {df.match.sum()}/{len(df)} match; semantic doubts flagged: {df.note.str.startswith('DOUBT').sum()}")
    return df


if __name__ == "__main__":
    main(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs"))
