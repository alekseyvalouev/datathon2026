"""Collect headline numbers from analysis/*/outputs into site/data.json for the findings page."""
import json, os, sys
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
A = os.path.join(ROOT, "analysis")
topo_path = sys.argv[1]  # us-atlas counties-10m.json
out = {}

# --- county geometry (TopoJSON decode) ---
t = json.load(open(topo_path))
sx, sy = t["transform"]["scale"]; tx, ty = t["transform"]["translate"]
arcs = []
for a in t["arcs"]:
    x = y = 0; pts = []
    for dx, dy in a:
        x += dx; y += dy
        pts.append([round(x * sx + tx, 4), round(y * sy + ty, 4)])
    arcs.append(pts)
def arc(i):
    return arcs[i] if i >= 0 else arcs[~i][::-1]
def ring(idx):
    r = []
    for i in idx:
        p = arc(i); r.extend(p if not r else p[1:])
    return r
BAY = {"001":"Alameda","013":"Contra Costa","041":"Marin","055":"Napa","075":"San Francisco","081":"San Mateo","085":"Santa Clara","095":"Solano","097":"Sonoma"}
NEAR = {"067":"Sacramento","077":"San Joaquin","099":"Stanislaus","047":"Merced","087":"Santa Cruz","113":"Yolo","053":"Monterey","069":"San Benito","033":"Lake","045":"Mendocino","101":"Sutter","061":"Placer","017":"El Dorado","005":"Amador","009":"Calaveras","109":"Tuolumne","043":"Mariposa","039":"Madera","019":"Fresno","011":"Colusa","115":"Yuba","007":"Butte","021":"Glenn","003":"Alpine","051":"Mono","057":"Nevada","063":"Plumas"}
feats = []
for g in t["objects"]["counties"]["geometries"]:
    gid = g["id"]
    if not gid.startswith("06"): continue
    c = gid[2:]
    if c not in BAY and c not in NEAR: continue
    if g["type"] == "Polygon":
        coords = [[ring(r) for r in g["arcs"]]]
    else:
        coords = [[ring(r) for r in poly] for poly in g["arcs"]]
    feats.append({"type":"Feature","id":gid,"properties":{"name":BAY.get(c) or NEAR.get(c),"bay":c in BAY},
                  "geometry":{"type":"MultiPolygon","coordinates":coords}})
out["counties"] = {"type":"FeatureCollection","features":feats}

# --- E1 decomposition ---
d = pd.read_csv(f"{A}/e1_composition/outputs/decomposition_period.csv")
d = d[d.period == "TY2011->TY2021"]
out["e1"] = [dict(unit=r.unit.replace(" (9-county region)",""), change=round(r.change), people=round(r.people), exit=round(r.exit),
                  entry=round(r.entry), share=round(r.composition_share_pct,1), mean_from=round(r.mean_from), mean_to=round(r.mean_to))
             for r in d.itertuples()]

# --- E2 ZIP re-entry ---
z = pd.read_csv(f"{A}/e2_turnover_model/outputs/zip_reentry_cost.csv", dtype={"zipcode":str})
z = z[~z.low_n_flag.astype(bool)]
out["zips"] = [dict(zip=r.zipcode, county=r.county.replace(" County",""), lat=round(r.lat,4), lon=round(r.lon,4), n=int(r.n_turnovers),
                    rent=round(r.median_prev_rent), jump=round(r.obs_median_jump_annual,4), pred=round(r.pred_median_jump_annual,4),
                    prem=round(r.obs_median_premium_month_vs_cpi), over=round(r.obs_share_over_10pct_cap,3)) for r in z.itertuples()]

# --- E6 county income gate ---
g = pd.read_csv(f"{A}/e6_unit_replacement/outputs/a1_income_gate_by_county.csv")
out["e6"] = [dict(county=r.county.replace(" County",""), n=int(r.n), lost=round(r.lost_LI,4), gained=round(r.gained_LI,4), net=round(r.net_LI,4)) for r in g.itertuples()]

# --- E7 relocation by pay tier ---
rl = pd.read_csv(f"{A}/e7_pulled_in/outputs/relocation_by_paytier.csv")
out["e7"] = [dict(region=r.region, tier=r.pay_tier, n=int(r.n), n_relo=int(r.n_relo), rate=round(r.relo_rate,4), firm=round(r.relo_firm_rate,4),
                  balanced=round(r.relo_rate_company_balanced,4)) for r in rl.itertuples()]

# --- E5 persons per return, region TY2021 ---
rr = pd.read_csv(f"{A}/e5_replacers_irs/outputs/replacement_ratios.csv")
e5 = rr[(rr.ty == 2021) & (rr.cat == "all")]
out["e5"] = [dict(unit=r.unit, ppr_in=round(r.persons_per_return_in,2), ppr_out=round(r.persons_per_return_out,2), ppr_stay=round(r.ppr_stay,2),
                  agi_in=round(r.mean_agi_in), agi_out=round(r.mean_agi_out), agi_stay=round(r.mean_agi_stay),
                  ratio=round(r.replacement_ratio_per_return,3), ratio_pp=round(r.replacement_ratio_per_person,3)) for r in e5.itertuples()]

# --- E9 contrasts ---
c = pd.read_csv(f"{A}/e9_pums_movers/outputs/leaver_vs_stayer_contrasts.csv")
c = c[c["sample"] == "all"]
out["e9"] = [dict(t=r.treatment, o=r.outcome, n=int(r.n_treat_nonmissing), d=round(r.ipw_diff,4), lo=round(r.ipw_lo,4), hi=round(r.ipw_hi,4),
                  leaver=round(r.leaver_mean,4), stayer=round(r.stayer_ipw_mean,4)) for r in c.itertuples()]

# --- E10 shares + flows + ledger ---
h = pd.read_csv(f"{A}/e10_supercommute/outputs/headline_shares.csv")
out["e10_shares"] = [dict(year=int(r.year), band=r.band, label=r.band_label, commutable=round(r.share_commutable,4), far=round(r.share_far,4),
                          all=round(r.share_all_outside9,4), jobs=int(r.bay_jobs_ca_res)) for r in h.itertuples()]
p = pd.read_csv(f"{A}/e10_supercommute/outputs/top_pairs_2024.csv", dtype={"h_cty":str,"w_cty":str})
p = p[p.miles_oneway <= 130].head(14)
out["e10_pairs"] = [dict(h=r.h_cty, hn=r.h_name, w=r.w_cty, wn=r.w_name, jobs=int(r.S000), jobs2010=int(r.S000_2010), miles=round(r.miles_oneway),
                         minutes=round(r.minutes_freeflow)) for r in p.itertuples()]
l = pd.read_csv(f"{A}/e10_supercommute/outputs/ledger_with_commute.csv")
l = l[l.beds == 1]
out["ledger"] = [dict(occ=r.occupation, gross=round(r.bay_gross_monthly), stay=round(r.stay_residual), rerent=round(r.rerent_bay_residual),
                      dest=r.dest_metro, move=round(r.move_local_wage_residual), keep_fuel=round(r.keep_bay_job_residual_fuel),
                      keep_irs=round(r.keep_bay_job_residual_irs), hours=round(r.commute_hours_month)) for r in l.itertuples()]

# --- E3 rent burden (1BR, OEWS wages, Bay) ---
b = pd.read_csv(f"{A}/e3_mover_ledger/outputs/ledger_burden_1br_oews_bay_area.csv")
out["e3"] = b.round(3).to_dict(orient="records")

# --- E4 destinations ---
out["e4"] = pd.read_csv(f"{A}/e4_exit_classifier/outputs/destination_vs_cpl.csv").to_dict(orient="records")

# --- E8 headline ---
out["e8"] = pd.read_csv(f"{A}/e8_access/outputs/headline.csv").round(4).to_dict(orient="records")

import math
def clean(o):
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)): return None
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    return o
json.dump(clean(out), open(os.path.join(ROOT, "site", "data.json"), "w"), separators=(",", ":"), allow_nan=False)
print({k: (len(v) if isinstance(v, list) else "geo") for k, v in out.items()}, os.path.getsize(os.path.join(ROOT, "site", "data.json")))
