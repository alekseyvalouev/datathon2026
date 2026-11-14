"""Step 1: categorize Google Maps places into essential-service categories.
Reads the raw google_maps.csv (duckdb), keeps open places, applies the rules in RULES (main `category` field, plus
`all_categories` tags for food banks), drops obvious off-topic "clinics" by name, and writes:
  cache/places_cat.parquet   one row per (place, service category) with lat/lon, rating, reviews
  outputs/places_category_rules.csv, outputs/places_category_counts.csv
  outputs/hand_check_places_sample.csv (30 rows, stratified, seed 42) and, merged with the manual verdicts in
  hand_check_verdicts.csv, outputs/hand_check_places.csv + outputs/hand_check_places_precision.csv"""
import os, re, sys, duckdb, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

# main-category rules (case-insensitive exact match on the `category` field)
RULES = {
    "grocery": ["Grocery store", "Supermarket", "Produce market", "Discount supermarket", "Chinese supermarket",
                "Japanese supermarket", "Asian grocery store", "Indian grocery store", "Mexican grocery store",
                "Gourmet grocery store", "Korean grocery store", "Japanese grocery store", "Italian grocery store",
                "European grocery store", "Filipino grocery store", "Russian grocery store", "Kosher grocery store",
                "Eastern European grocery store", "American grocery store", "Gourmet Grocery Shop",
                "Indian Grocery Shop", "Asian Grocery Shop"],
    # general / urgent / community care FACILITIES (v3): these categories always count ...
    "clinic": ["Community health center", "Urgent care center", "Urgent care centre", "Walk-in clinic", "Free clinic",
               "Medical Center", "Hospital", "General hospital", "Emergency room", "Pediatric clinic"],
    "pharmacy": ["Pharmacy"],
    "transit": ["Bus stop", "Transport hub", "Transit station"],   # 'Transport hub' rows are bus-stop names (checked)
    "foodbank": ["Food bank", "Foodbank", "Soup kitchen"],
    "bank": ["Bank", "Credit union", "Federal credit union", "Credit Union"],
    "afs": ["Check cashing service", "Pawn shop", "Money transfer service"],   # alternative financial services
}
# ... and these noisy categories (mostly individual practitioners / specialists / non-care businesses) count only
# when the NAME signals general, urgent or community care (v3, after the clinic rows in two hand-check rounds failed)
CLINIC_NAMED_CATS = ["Medical clinic", "Clinic", "Women's health clinic", "Family practice physician"]
CLINIC_NAME_OK = re.compile(r"urgent|community|family|primary|health cent|cl[ií]nica|medical group|medical cent|walk.?in|"
                            r"kaiser|sutter|one medical|planned parenthood|county|free clinic|minute ?clinic|"
                            r"carbon health|federally|fqhc|neighborhood|public health|health services|medical clinic|"
                            r"health clinic|internal medicine|pediatric", re.I)
# all_categories tags that also qualify (a pantry run by a church/non-profit is often filed under its main category)
TAG_RULES = {"foodbank": re.compile(r'"(?:food bank|foodbank|food pantry|soup kitchen)"', re.I)}
# name exclusions (v2 rules, added after the round-1 hand check in hand_check_round1_v1rules.csv):
#  clinic   : cosmetic / non-care / non-medical slips of the keyword-matched category
#  grocery  : gas-station marts, liquor/smoke shops, convenience marts, distributors (USDA counts supermarkets and
#             large grocery stores only; size is not observed, so these name cues are the only filter available)
#  pharmacy : specialty / compounding / infusion / long-term-care pharmacies that do not serve walk-in retail
GROCERY_EXCL = re.compile(r"\bgas\b|fuel|chevron|\bshell\b|\barco\b|valero|7-eleven|7 eleven|liquor|smoke|tobacco|vape|"
                          r"distribut|wholesale|food ?mart|mini ?mart|convenience", re.I)
PHARM_EXCL = re.compile(r"omnicare|long.?term|institution|infusion|specialty|compound", re.I)
CLINIC_EXCL = re.compile(r"depil|electroly|\bwax|tattoo|"
                         r"cosmetic|aesthetic|med ?spa|medspa|botox|laser|\bIV\b|iv therapy|drip|rejuv|weight loss|"
                         r"skin|dermatolog|hair|plastic|fertility|lasik|imaging|radiology|\blab\b|labs\b|audiology|"
                         r"hearing|immigration|\bgym\b|vein|sleep|vision|optometr|dental|dentist|chiropract|massage|"
                         r"acupunct|veterinar|animal|\bpet\b|lawyer|attorney", re.I)


def load_raw():
    c = duckdb.connect()
    p = c.execute(f"""select place_id, name, category, all_categories, lat, lon, rating, reviews_count,
                        coalesce(permanently_closed, false) pclosed, coalesce(temporarily_closed, false) tclosed
                      from read_csv_auto('{PLACES_CSV}', sample_size=-1)""").df()
    return p


def categorize(p):
    rows = []
    cat_l = p.category.fillna("").str.lower()
    for k, lst in RULES.items():
        m = cat_l.isin([s.lower() for s in lst])
        if k in TAG_RULES: m |= p.all_categories.fillna("").str.contains(TAG_RULES[k])
        if k == "clinic":
            m |= cat_l.isin([s.lower() for s in CLINIC_NAMED_CATS]) & p.name.fillna("").str.contains(CLINIC_NAME_OK)
        d = p[m].copy(); d["svc"] = k
        excl = {"clinic": CLINIC_EXCL, "grocery": GROCERY_EXCL, "pharmacy": PHARM_EXCL}.get(k)
        if excl is not None:
            ex = d.name.fillna("").str.contains(excl)
            print(f"{k}: excluded {ex.sum()} of {len(d)} by name keyword")
            d = d[~ex]
        rows.append(d)
    # sensitivity set: v2 clinic rule (all clinic-like categories regardless of name, minus exclusions) -> recall check
    m = cat_l.isin([s.lower() for s in RULES["clinic"] + CLINIC_NAMED_CATS]) & ~p.name.fillna("").str.contains(CLINIC_EXCL)
    rows.append(p[m].assign(svc="clinic_broad"))
    return pd.concat(rows, ignore_index=True)


def reviews_agg():
    if not os.path.exists(REVIEWS_CSV): return None
    c = duckdb.connect()
    return c.execute(f"""select place_id, avg(review_rating) rev_mean, count(*) rev_n
                         from read_csv_auto('{REVIEWS_CSV}', sample_size=20000) group by 1""").df()


def main():
    ensure_dirs()
    p = load_raw()
    n0 = len(p)
    p = p.drop_duplicates("place_id")
    flow = [("raw rows", n0), ("unique place_id", len(p))]
    open_ = p[~p.pclosed & ~p.tclosed]
    flow.append(("not permanently/temporarily closed", len(open_)))
    cat = categorize(open_)
    flow.append(("(place, service) rows after rules", len(cat)))
    cat.loc[(cat.reviews_count.fillna(0) == 0) | (cat.rating == 0), "rating"] = np.nan   # 0 = unrated
    rv = reviews_agg()
    if rv is not None: cat = cat.merge(rv, on="place_id", how="left")
    cat.drop(columns=["pclosed", "tclosed"]).to_parquet(os.path.join(CACHE, "places_cat.parquet"), index=False)
    # also: how many closed places would have been categorized (coverage note)
    closed_cat = categorize(p[p.pclosed | p.tclosed])
    cnt = cat.groupby("svc").agg(n_open=("place_id", "size"), median_rating=("rating", "median"),
                                 share_rated=("rating", lambda s: s.notna().mean()),
                                 share_with_review_rows=("rev_n", lambda s: s.notna().mean()) if rv is not None else ("rating", "size"))
    cnt["n_closed_excluded"] = closed_cat.svc.value_counts()
    cnt.to_csv(os.path.join(OUT, "places_category_counts.csv"))
    pd.DataFrame(flow, columns=["step", "n"]).to_csv(os.path.join(OUT, "places_flow.csv"), index=False)
    pd.DataFrame([(k, "; ".join(v) + ("; OR (" + "; ".join(CLINIC_NAMED_CATS) + ") with name ~ /" + CLINIC_NAME_OK.pattern
                                       + "/" if k == "clinic" else ""), TAG_RULES[k].pattern if k in TAG_RULES else "",
                   {"clinic": CLINIC_EXCL, "grocery": GROCERY_EXCL, "pharmacy": PHARM_EXCL}[k].pattern
                   if k in ("clinic", "grocery", "pharmacy") else "") for k, v in RULES.items()],
                 columns=["service", "main_category_in", "or_all_categories_regex", "name_exclusion_regex"]).to_csv(
        os.path.join(OUT, "places_category_rules.csv"), index=False)
    print(pd.DataFrame(flow).to_string(index=False)); print(cnt.to_string())
    # final hand-check sample under the final (v3) rules (seed 43): 6 grocery, 6 clinic, 6 pharmacy, 4 transit, 5 food bank,
    # 3 bank/afs; names/categories only. (Round 1, 30 rows under v1 rules, is kept in
    # hand_check_round1_v1rules.csv; an interim v2 look at 6 clinic rows -> v3 clinic rule, see README.)
    rng = np.random.default_rng(SEED + 1)
    parts = []
    for k, n in [("grocery", 6), ("clinic", 6), ("pharmacy", 6), ("transit", 4), ("foodbank", 5)]:
        d = cat[cat.svc == k]; parts.append(d.iloc[rng.choice(len(d), n, replace=False)])
    d = cat[cat.svc.isin(["bank", "afs"])]; parts.append(d.iloc[rng.choice(len(d), 3, replace=False)])
    hs = pd.concat(parts)[["place_id", "svc", "name", "category", "all_categories", "rating", "reviews_count"]]
    hs.to_csv(os.path.join(OUT, "hand_check_places_sample.csv"), index=False)
    vf = os.path.join(HERE, "hand_check_verdicts_final.csv")
    if os.path.exists(vf):
        v = pd.read_csv(vf)
        h = hs.merge(v[["place_id", "svc", "correct", "strict_ok", "note"]], on=["place_id", "svc"], how="left")
        h.to_csv(os.path.join(OUT, "hand_check_places.csv"), index=False)
        pr = h.groupby("svc").agg(n=("correct", "size"), n_checked=("correct", "count"), correct=("correct", "sum"), strict_ok=("strict_ok", "sum"))
        pr.loc["ALL"] = pr.sum()
        pr.to_csv(os.path.join(OUT, "hand_check_places_precision.csv")); print(pr.to_string())
    else:
        print("no hand_check_verdicts.csv yet; wrote sample only")


if __name__ == "__main__":
    main()
