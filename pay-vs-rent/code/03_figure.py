"""Render the background-slide table from results/pay_rent_by_class.csv.

Writes figs/pay_vs_rent_burden.html, and a 2x PNG beside it when Playwright is installed.
"""
import os
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGS = os.path.join(BASE, "figs")
ROWS = [
    ("AI-positioned", [("AI_POSITIONED", "Software, AI and data engineering"),
                       ("PRODUCT_DESIGN", "Product and design")]),
    ("AI-exposed", [("CUSTOMER_SUPPORT", "Customer support"),
                    ("FRONTLINE_SERVICE", "Frontline service"),
                    ("PROF_EXPOSED", "Junior professional"),
                    ("CLERICAL_ADMIN", "Clerical and admin")]),
    ("All occupations", [("ALL", "Every full-time worker who rents")]),
]
LO, HI = -2.0, 7.0          # bar scale, percentage points
ZERO = (0 - LO) / (HI - LO) * 100

CSS = """
:root{--paper:#f5f3ef;--ink:#1c1d22;--muted:#6f7076;--rule:#d6d3cd;--rust:#8a392d}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Hanken Grotesk","Helvetica Neue",Arial,sans-serif}
.fig{width:1288px;padding:44px 55px 40px}
.eyebrow{color:var(--rust);font-size:18px;font-weight:700;letter-spacing:.2em;text-transform:uppercase}
h1{margin:18px 0 10px;font-size:42px;line-height:1.1;font-weight:500;letter-spacing:-.01em}
.sub{margin:0 0 26px;font-size:19px;line-height:1.4;color:var(--muted);max-width:60em}
.row{display:grid;grid-template-columns:372px 108px 1fr 196px 88px;column-gap:20px;align-items:center;
     border-bottom:1px solid var(--rule);font-variant-numeric:tabular-nums}
.head{color:var(--muted);font-size:17px;padding-bottom:12px}
.head .c,.head .r{white-space:nowrap}
.grp{color:var(--rust);font-size:15px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;
     padding:26px 0 10px;border-bottom:1px solid var(--rule)}
.body{font-size:23px;font-weight:500;height:52px}
.r{text-align:right}.c{text-align:center}
.pay{font-weight:600}
.lvl{font-size:18px;font-weight:400;color:var(--muted)}
.chg{font-weight:600;color:var(--rust)}
.chg.ns{color:var(--muted);font-weight:500}
.chg.down{color:var(--ink)}
.track{position:relative;height:20px}
.track i{position:absolute;top:0;height:100%;background:var(--rust)}
.track i.down{background:var(--ink)}
.track::after{content:"";position:absolute;top:-8px;bottom:-8px;left:var(--zero);width:1.5px;background:var(--ink)}
.foot{display:flex;justify-content:space-between;gap:40px;margin-top:22px;color:var(--muted);font-size:16px;line-height:1.45}
.foot p{margin:0}
.key{display:flex;gap:22px;white-space:nowrap}
.key span::before{content:"";display:inline-block;width:22px;height:11px;margin-right:9px;background:var(--rust)}
.key span.k2::before{background:var(--ink)}
"""


def bar(v):
    w = abs(v) / (HI - LO) * 100
    left = ZERO if v >= 0 else ZERO - w
    cls = "" if v >= 0 else ' class="down"'
    return f'<div class="track" style="--zero:{ZERO:.2f}%"><i{cls} style="left:{left:.2f}%;width:{w:.2f}%"></i></div>'


def main():
    d = pd.read_csv(os.path.join(BASE, "results", "pay_rent_by_class.csv")).set_index("occ_class")
    assert (d.pay_growth > 0).all(), "headline says pay rose in every class"
    html = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>Pay vs rent burden</title>",
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&display=swap">',
            f"<style>{CSS}</style></head><body><div class=\"fig\">",
            '<div class="eyebrow">Pay vs rent burden, 2018–19 to 2023–24</div>',
            "<h1>Pay rose in every job. Outside tech, rent burden rose anyway</h1>",
            '<p class="sub">Full-time workers who rent in the nine Bay Area counties. '
            "Rent-burdened means the household spends 30% or more of its income on rent.</p>",
            '<div class="row head"><div>Occupation</div><div class="r">Median pay</div>'
            '<div class="c">← fewer rent-burdened · 0 · more →</div>'
            '<div class="r">Share burdened</div><div class="r">Change</div></div>']
    for group, rows in ROWS:
        html.append(f'<div class="grp">{group}</div>')
        for key, label in rows:
            r = d.loc[key]
            pts = r.burden30_change * 100
            sig = abs(r.z_burden30_change) >= 1.96
            cls = "chg" + ("" if sig else " ns") + (" down" if sig and pts < 0 else "")
            html.append(
                f'<div class="row body"><div>{label}</div>'
                f'<div class="r pay">+{r.pay_growth * 100:.0f}%</div>{bar(pts)}'
                f'<div class="r lvl">{r.burden30_pre * 100:.0f}% → {r.burden30_post * 100:.0f}%</div>'
                f'<div class="r {cls}">{pts:+.1f} pts</div></div>'.replace("+-", "−").replace(">-", ">−"))
    html.append('<div class="foot"><p>Source: ACS PUMS 1-year files, 2018–19 and 2023–24 pooled. '
                "Pay is the median wage of full-time, year-round workers, not adjusted for inflation. "
                "Grey changes are within sampling error.</p>"
                "</div>")
    html.append("</div></body></html>")
    os.makedirs(FIGS, exist_ok=True)
    path = os.path.join(FIGS, "pay_vs_rent_burden.html")
    with open(path, "w") as f:
        f.write("\n".join(html))
    print("wrote", path)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed; skipped PNG")
        return
    with sync_playwright() as pw:
        try:
            b = pw.chromium.launch()
        except Exception:
            b = pw.chromium.launch(channel="chrome")  # fall back to the installed Chrome
        pg = b.new_page(viewport={"width": 1288, "height": 800}, device_scale_factor=2)
        pg.goto("file://" + path)
        pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        pg.locator(".fig").screenshot(path=path.replace(".html", ".png"))
        b.close()
    print("wrote", path.replace(".html", ".png"))


if __name__ == "__main__":
    main()
