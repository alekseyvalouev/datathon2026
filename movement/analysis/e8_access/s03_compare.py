"""Step 3: access of units a low-income household can qualify for vs the rest, overall / by county / vs origin areas.
Two weightings: listing-weighted (every FOR_RENT row) and building-weighted (one row per distinct coordinate within
the group; large complexes list many floor plans/units at one point). Writes outputs/access_compare_*.csv,
outputs/headline.csv and figs/*.png."""
import os, sys, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *


def add_labels(d):
    d["fail_grocery"] = d.d_grocery > TH["grocery"]; d["fail_clinic"] = d.d_clinic > TH["clinic"]
    d["fail_transit"] = d.d_transit > TH["transit"]
    d["n_fail"] = d[["fail_grocery", "fail_clinic", "fail_transit"]].sum(1)
    d["desert"] = (d.n_fail >= 1).astype(int)          # modeling label: >=1 core service beyond its threshold
    d["desert2"] = (d.n_fail >= 2).astype(int)         # stricter: >=2 of 3
    d["no_bus_400"] = d.n400_transit == 0
    return d


def summ(g):
    return pd.Series({
        "n_listings": len(g), "n_buildings": g.loc_id.nunique(), "median_rent": g.rent.median(),
        "med_d_clinic_m": g.d_clinic.median(), "med_d_grocery_m": g.d_grocery.median(),
        "med_d_pharmacy_m": g.d_pharmacy.median(), "med_d_transit_m": g.d_transit.median(),
        "med_d_foodbank_m": g.d_foodbank.median(), "med_d_clinic_broad_m": g.d_clinic_broad.median(),
        "p90_d_clinic_m": g.d_clinic.quantile(.9), "p90_d_grocery_m": g.d_grocery.quantile(.9),
        "share_bus_400": (g.n400_transit > 0).mean(), "share_bus_800": (g.n800_transit > 0).mean(),
        "med_bus_stops_400": g.n400_transit.median(), "share_grocery_800": (g.n800_grocery > 0).mean(),
        "share_grocery_1600": (g.n1600_grocery > 0).mean(), "share_clinic_1600": (g.n1600_clinic > 0).mean(),
        "share_pharmacy_800": (g.n800_pharmacy > 0).mean(), "share_foodbank_1600": (g.n1600_foodbank > 0).mean(),
        "share_desert_any": g.desert.mean(), "share_desert_2of3": g.desert2.mean(),
        "mean_nearest_rated_clinic_rating": g.nearest_rated_clinic_rating.mean(),
        "share_nearest_clinic_rated": g.nearest_clinic_rating.notna().mean(),
        "bank_to_afs_ratio_1600": g.n1600_bank.sum() / max(g.n1600_afs.sum(), 1),
    })


def compare(d, by, w):
    if w == "building":
        d = d.drop_duplicates(by + ["loc_id"] if by else ["loc_id"])
    t = d.groupby(by).apply(summ, include_groups=False) if by else summ(d).to_frame().T
    return t


def main():
    d = add_labels(pd.read_parquet(os.path.join(CACHE, "listings_access.parquet")))
    d["gate"] = np.select([d.qual_VLI, d.qual_LI], ["a <=50% AMI reachable", "b 50-80% AMI reachable"], "c not reachable at 80% AMI")
    d["li"] = np.where(d.qual_LI, "LI-reachable (<=80% AMI)", "not LI-reachable")
    d["vli"] = np.where(d.qual_VLI, "VLI-reachable (<=50% AMI)", "not VLI-reachable")
    d["origin"] = np.where(d.origin_area, "origin (SF/San Mateo/E2 top ZIPs)", "rest of Bay")
    d["beds_g"] = d.beds.clip(0, 3).map({0: "0 studio", 1: "1", 2: "2", 3: "3+"})
    res = {}
    for w in ["listing", "building"]:
        rows = [compare(d, [], w).assign(group="ALL")]
        for col in ["li", "vli", "gate", "origin"]:
            rows.append(compare(d, [col], w).reset_index().rename(columns={col: "group"}))
        # destination framing: units outside the origin areas that a low-income household can qualify for
        dest = d[~d.origin_area]
        rows.append(compare(dest, ["li"], w).reset_index().rename(columns={"li": "group"}).assign(group=lambda x: "rest of Bay & " + x.group))
        rows.append(compare(dest, ["vli"], w).reset_index().rename(columns={"vli": "group"}).assign(group=lambda x: "rest of Bay & " + x.group))
        t = pd.concat(rows, ignore_index=True).set_index("group")
        t.to_csv(os.path.join(OUT, f"access_compare_overall_{w}.csv")); res[w] = t
        for col in ["li", "vli"]:
            c = compare(d, ["county", col], w)
            c.to_csv(os.path.join(OUT, f"access_compare_county_{col}_{w}.csv"))
        compare(d, ["beds_g", "vli"], w).to_csv(os.path.join(OUT, f"access_compare_beds_vli_{w}.csv"))
        compare(d.dropna(subset=["typ_group"]), ["typ_group", "li"], w).to_csv(os.path.join(OUT, f"access_compare_typology_li_{w}.csv"))
    pd.set_option("display.width", 250)
    for w in res:
        print(f"\n== {w}-weighted\n", res[w][["n_listings", "n_buildings", "median_rent", "med_d_clinic_m", "med_d_grocery_m",
              "med_d_transit_m", "share_bus_400", "share_grocery_800", "share_clinic_1600", "share_desert_any",
              "share_desert_2of3", "mean_nearest_rated_clinic_rating", "bank_to_afs_ratio_1600"]].round(3).to_string())
    # headline: ratios, overall and pooled within-county (county-mix removed by comparing inside each county)
    rows = []
    for w in ["listing", "building"]:
        for col, yes in [("qual_LI", "<=80% AMI"), ("qual_VLI", "<=50% AMI")]:
            x = d if w == "listing" else d.drop_duplicates([col, "loc_id"])
            a, b = x[x[col]], x[~x[col]]
            r = dict(weight=w, group=yes, n_reach=len(a), n_not=len(b),
                     clinic_dist_ratio=a.d_clinic.median() / b.d_clinic.median(),
                     grocery_dist_ratio=a.d_grocery.median() / b.d_grocery.median(),
                     transit_dist_ratio=a.d_transit.median() / b.d_transit.median(),
                     bus400_reach=(a.n400_transit > 0).mean(), bus400_not=(b.n400_transit > 0).mean(),
                     desert_reach=a.desert.mean(), desert_not=b.desert.mean())
            r["bus400_rel_diff"] = r["bus400_reach"] / r["bus400_not"] - 1
            # within-county: median of county-level clinic-distance ratios (counties with >=30 in both groups)
            cr = []
            for c, g in x.groupby("county"):
                ga, gb = g[g[col]], g[~g[col]]
                if len(ga) >= 30 and len(gb) >= 30: cr.append(ga.d_clinic.median() / gb.d_clinic.median())
            r["within_county_clinic_ratio_median"] = np.median(cr) if cr else np.nan; r["n_counties"] = len(cr)
            rows.append(r)
    # displaced from origin -> low-income-reachable unit elsewhere
    for w in ["listing", "building"]:
        o = d[d.origin_area]
        if w == "building": o = o.drop_duplicates("loc_id")
        for col, yes in [("qual_LI", "<=80% AMI"), ("qual_VLI", "<=50% AMI")]:
            dst = d[~d.origin_area & d[col]]
            if w == "building": dst = dst.drop_duplicates("loc_id")
            rows.append(dict(weight=w, group=f"origin areas (all units) vs rest-of-Bay {yes}-reachable", n_reach=len(dst), n_not=len(o),
                             clinic_dist_ratio=dst.d_clinic.median() / o.d_clinic.median(),
                             grocery_dist_ratio=dst.d_grocery.median() / o.d_grocery.median(),
                             transit_dist_ratio=dst.d_transit.median() / o.d_transit.median(),
                             bus400_reach=(dst.n400_transit > 0).mean(), bus400_not=(o.n400_transit > 0).mean(),
                             desert_reach=dst.desert.mean(), desert_not=o.desert.mean(),
                             bus400_rel_diff=(dst.n400_transit > 0).mean() / (o.n400_transit > 0).mean() - 1))
    h = pd.DataFrame(rows); h.to_csv(os.path.join(OUT, "headline.csv"), index=False)
    print("\n", h.round(3).to_string())
    figs(d)


def figs(d):
    L = d.groupby("loc_id").agg(lat=("lat", "first"), lon=("lon", "first"), desert=("desert", "first"),
                                d_clinic=("d_clinic", "first"), vli=("qual_VLI", "max"), li=("qual_LI", "mean"),
                                n=("zpid", "size")).reset_index()
    # Map 1: buildings by nearest-clinic distance, with VLI-reachable buildings outlined
    fig, ax = plt.subplots(1, 2, figsize=(13, 7.5), sharex=True, sharey=True)
    sc = ax[0].scatter(L.lon, L.lat, c=np.log10(L.d_clinic.clip(50, 20000)), s=4, cmap="viridis_r", alpha=.8)
    cb = fig.colorbar(sc, ax=ax[0], shrink=.6); cb.set_ticks(np.log10([100, 300, 1000, 3000, 10000]))
    cb.set_ticklabels(["100 m", "300 m", "1 km", "3 km", "10 km"]); cb.set_label("distance to nearest clinic (straight line)")
    ax[0].set_title("Rental buildings: distance to nearest clinic", fontsize=10)
    ax[1].scatter(L.lon, L.lat, c="#d9d9d9", s=3, label="other rental buildings")
    v = L[L.vli]; ax[1].scatter(v.lon, v.lat, c=np.where(v.desert == 1, "#c0392b", "#2c7fb8"), s=9)
    ax[1].scatter([], [], c="#2c7fb8", s=9, label="<=50% AMI-reachable, served"); ax[1].scatter([], [], c="#c0392b", s=9, label="<=50% AMI-reachable, service desert")
    ax[1].legend(fontsize=8, loc="lower left", frameon=False)
    ax[1].set_title("Buildings with a unit a <=50% AMI household can qualify for (3x rent)", fontsize=10)
    for a in ax: a.set_aspect(1 / np.cos(np.radians(37.8))); a.set_xlabel("longitude"); a.set_xticks(np.arange(-123.5, -121.4, 0.5))
    ax[0].set_ylabel("latitude"); fig.tight_layout(); fig.savefig(os.path.join(FIG, "map_clinic_distance_and_vli_units.png"), dpi=140); plt.close(fig)
    # Map 2: desert label
    fig, ax = plt.subplots(figsize=(7, 7.5))
    ax.scatter(L.lon, L.lat, c=np.where(L.desert == 1, "#c0392b", "#bdbdbd"), s=np.where(L.desert == 1, 8, 3))
    ax.set_title("Service-desert rental buildings (red): grocery >1.6 km OR clinic >3.2 km OR bus stop >800 m", fontsize=9)
    ax.set_aspect(1 / np.cos(np.radians(37.8))); fig.tight_layout(); fig.savefig(os.path.join(FIG, "map_desert_label.png"), dpi=140); plt.close(fig)
    # Bar: by county, share with bus stop within 400m and median clinic distance, VLI vs not
    t = d.groupby(["county", "qual_VLI"]).agg(bus=("n400_transit", lambda s: (s > 0).mean()), clinic=("d_clinic", "median"), n=("zpid", "size")).reset_index()
    t = t[t.n >= 30]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    cs = sorted(t.county.unique()); y = np.arange(len(cs))
    for k, (col, lab) in enumerate([("clinic", "median distance to nearest clinic (m)"), ("bus", "share with a bus stop within 400 m")]):
        for off, q, colr, nm in [(-.2, True, "#c0392b", "<=50% AMI-reachable"), (.2, False, "#7f7f7f", "not reachable")]:
            s = t[t.qual_VLI == q].set_index("county").reindex(cs)[col]
            ax[k].barh(y + off, s, height=.4, color=colr, label=nm)
        ax[k].set_yticks(y, [c.replace(" County", "") for c in cs]); ax[k].set_xlabel(lab)
    ax[0].legend(frameon=False, fontsize=8); ax[0].set_title("Within each county (groups with n>=30 listings)", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "county_access_vli_vs_not.png"), dpi=140); plt.close(fig)
    # ECDF of clinic distance: origin vs rest-of-Bay LI/VLI-reachable
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for lab, s, c in [("origin areas, all units", d[d.origin_area].d_clinic, "#333"),
                      ("rest of Bay, <=80% AMI-reachable", d[~d.origin_area & d.qual_LI].d_clinic, "#2c7fb8"),
                      ("rest of Bay, <=50% AMI-reachable", d[~d.origin_area & d.qual_VLI].d_clinic, "#c0392b")]:
        x = np.sort(s.values); ax.plot(x, np.arange(1, len(x) + 1) / len(x), label=f"{lab} (n={len(x):,})", color=c)
    ax.set_xscale("log"); ax.axvline(TH["clinic"], ls="--", color="#999", lw=1); ax.set_xlabel("distance to nearest clinic (m, log)")
    ax.set_ylabel("share of listings within x"); ax.legend(frameon=False, fontsize=8); ax.set_title("Clinic distance, listing-weighted", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "ecdf_clinic_origin_vs_dest.png"), dpi=140); plt.close(fig)


if __name__ == "__main__":
    main()
