"""Step 1: parse CA HCD State Income Limits PDFs (raw/hcd_il{YEAR}.pdf; HUD-based 50% 'Very Low' and 80% 'Low' limits
for 1-8 person households) for the 9 Bay Area counties -> outputs/income_limits_bay.csv.
Run with python -I (raw/ is untrusted input). Layout-robust: words are matched by page coordinates."""
import fitz, os, re, sys, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I drops the script dir; add it back explicitly
from common import RAW, OUT, BAY
LABELS = {"Acutely": "ALI", "Extremely": "ELI", "Very": "VLI", "Low": "LI", "Median": "MED", "Moderate": "MOD"}
COUNTIES = set(BAY.values())

def parse(path):
    rows = []
    for page in fitz.open(path):
        W = page.get_text("words")
        heads = []   # (y, county)
        for i, w in enumerate(W):
            if w[4] == "County" and w[0] < 200:
                name = " ".join(x[4] for x in W if abs(x[1] - w[1]) < 3 and x[0] < w[0] and x[0] < 200)
                heads.append((w[1], name + " County"))
        labs = []    # (y, label)
        for w in W:
            if 130 < w[0] < 150 and w[4] in LABELS:
                # 'Low' alone is the 80% row; 'Very Low', 'Acutely Low', 'Extremely Low' start with their own word
                labs.append((w[1], LABELS[w[4]]))
        nums = [(w[1], w[0], int(w[4])) for w in W if w[0] > 215 and re.fullmatch(r"\d{4,6}", w[4])]
        if not heads or not labs: continue
        vals = {i: [] for i in range(len(labs))}
        for y, x, v in nums:
            i = min(range(len(labs)), key=lambda k: abs(labs[k][0] - y))
            if abs(labs[i][0] - y) < 9: vals[i].append((x, v))
        for i, (y, lab) in enumerate(labs):
            c = min(heads, key=lambda h: abs(h[0] - y))[1]
            v = [v for _, v in sorted(vals[i])]
            if c in COUNTIES and lab in ("VLI", "LI", "MED"):
                rows.append(dict(county=c, level=lab, n=len(v), **{f"p{k+1}": v[k] if k < len(v) else None for k in range(8)}))
    return pd.DataFrame(rows)

def parse_text(path):
    """Reading-order parser (works when each county's block is emitted contiguously, e.g. the rotated 2025 PDF)."""
    toks = []
    for page in fitz.open(path):
        toks += [t.strip() for t in page.get_text().split("\n") if t.strip()]
    rows = []
    for i, t in enumerate(toks):
        if t in COUNTIES:
            j = i + 1
            blk = toks[j:j + 60]
            for lab, key in (("Very Low Income", "VLI"), ("Low Income", "LI"), ("Median Income", "MED")):
                if lab in blk:
                    k = blk.index(lab)
                    v = [int(x) for x in blk[k + 1:k + 9] if re.fullmatch(r"\d{4,6}", x)]
                    rows.append(dict(county=t, level=key, n=len(v), **{f"p{q+1}": v[q] if q < len(v) else None for q in range(8)}))
    return pd.DataFrame(rows)

def ok(d):
    if d.empty: return False
    d = d.drop_duplicates(["county", "level"])
    if len(d) != 27 or (d.n != 8).any(): return False
    P = d[[f"p{k}" for k in range(1, 9)]].to_numpy(float)
    if not (P[:, 1:] >= P[:, :-1]).all(): return False
    w = d.set_index(["county", "level"]).p4.unstack()
    return bool((w.LI > w.VLI).all())

def main():
    out = []
    for f in sorted(os.listdir(RAW)):
        m = re.fullmatch(r"hcd_il(\d{4})\.pdf", f)
        if not m: continue
        p = os.path.join(RAW, f)
        d = parse(p)
        if not ok(d): d = parse_text(p)
        assert ok(d), f"could not parse {f}"
        d = d.drop_duplicates(["county", "level"]); d["year"] = int(m.group(1)); out.append(d)
    il = pd.concat(out)
    il = il.drop_duplicates(["year", "county", "level"])
    assert len(il) == len(out) * 9 * 3, (len(il), il.groupby("year").size())
    il.drop(columns="n").to_csv(os.path.join(OUT, "income_limits_bay.csv"), index=False)
    print(il[il.level != "MED"].pivot_table(index="county", columns=["level", "year"], values="p4").to_string())

if __name__ == "__main__":
    main()
