"""Step 3 (Analysis 2): tenure replacement.
(a) rent -> sale: a unit's rental tenancy is followed by a sale (no rental listing in between, sale within 2 years
    of the last rent listing event). Who can replace the renter by buying? Required buyer income = annual PITI / DTI with
    20% down, Freddie Mac PMMS 30-yr fixed rate in the sale week, property tax 1.2%/yr, insurance 0.35%/yr, no HOA
    (missing; biases condo burdens down). DTI 28% (front-end) headline, 36% sensitivity. Compared with the prior
    renter's 3x-rent income (both nominal at their own dates; the rent ask is <=2 years before the sale).
(b) sale -> rent within 12 months (investor / landlord conversion).
(c) flips: two arm's-length 'Sold' events <= 12 months apart in priceHistory; markup = p2/p1."""
import os, sys, numpy as np, pandas as pd, duckdb
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
TAX, INS, DOWN, MULT = 0.012, 0.0035, 0.20, 3.0
RES = ("SINGLE_FAMILY", "SINGLEFAMILY", "CONDO", "TOWNHOUSE", "TOWNHOME", "MULTI_FAMILY", "APARTMENT")

def pmms():
    p = pd.read_csv(os.path.join(RAW, "pmms.csv"), usecols=["date", "pmms30"])
    p["date"] = pd.to_datetime(p.date, format="%m/%d/%Y"); p["pmms30"] = pd.to_numeric(p.pmms30, errors="coerce")
    return p.dropna().sort_values("date")

def add_rate(df, col):
    p = pmms(); df = df.sort_values(col); df[col] = df[col].astype("datetime64[ns]"); p["date"] = p.date.astype("datetime64[ns]")
    df = pd.merge_asof(df, p.rename(columns={"date": col}), on=col, direction="backward")
    return df

def buyer_income(price, rate_pct, dti):
    r = rate_pct / 100 / 12; n = 360; L = price * (1 - DOWN)
    pi = L * r / (1 - (1 + r) ** -n)
    return 12 * (pi + price * (TAX + INS) / 12) / dti

def main():
    con = duckdb.connect(DB, read_only=True)
    sales = con.execute(f"""select distinct zpid, d::date d, p from ev where not rental and event='Sold' and p between 50000 and 20000000""").df()
    rep = con.execute(f"""select zpid, county, zipcode, homeType, beds, lat, lon, ep, start_d::date start_d, end_d::date end_d, last_p
                          from rep where homeType in {RES}""").df()
    con.close()
    rep["county"] = rep.county.where(rep.county.isin(BAY.values()))
    rep = rep.dropna(subset=["county"])
    for c in ["start_d", "end_d"]: rep[c] = pd.to_datetime(rep[c])
    sales["d"] = pd.to_datetime(sales.d)
    # ---- (a) rent -> sale
    nxt = rep[["zpid", "ep", "start_d"]].rename(columns={"ep": "ep_prev", "start_d": "next_rent_start"})
    nxt["ep_prev"] -= 1
    a = rep.merge(nxt, left_on=["zpid", "ep"], right_on=["zpid", "ep_prev"], how="left").merge(sales, on="zpid")
    a = a[(a.d > a.end_d) & (a.d <= a.end_d + pd.Timedelta(days=730)) & (a.next_rent_start.isna() | (a.d < a.next_rent_start))]
    a = a.sort_values(["zpid", "ep", "d"]).drop_duplicates(["zpid", "ep"])   # first sale after the tenancy
    a = a.sort_values(["zpid", "ep"]).drop_duplicates(["zpid", "d"], keep="last")   # one sale -> its last preceding tenancy
    a = a.drop_duplicates(["lat", "lon", "beds", "d", "p", "last_p"])            # floor-plan duplicate zpids
    a["price_to_annual_rent"] = a.p / (12 * a.last_p)
    n0 = len(a); a = a[a.price_to_annual_rent.between(5, 60)]
    print(f"rent->sale events {n0}; after price/annual-rent in [5,60]: {len(a)}")
    a = add_rate(a, "d")
    a["renter_inc"] = MULT * 12 * a.last_p
    a["buyer_inc28"] = buyer_income(a.p, a.pmms30, 0.28); a["buyer_inc36"] = buyer_income(a.p, a.pmms30, 0.36)
    a["ratio28"] = a.buyer_inc28 / a.renter_inc; a["ratio36"] = a.buyer_inc36 / a.renter_inc
    a["cash_down"] = DOWN * a.p
    a["year"] = a.d.dt.year
    a["hh"] = (a.beds.fillna(0).clip(0, 7) + 1).astype(int)
    il = pd.read_csv(os.path.join(OUT, "income_limits_bay.csv")); il = il[il.level == "MED"]
    med = {(r.year, r.county, k): getattr(r, f"p{k}") for r in il.itertuples() for k in range(1, 9)}
    ly = np.where(a.d.dt.month >= 6, a.year, a.year - 1)
    a["MED"] = [med.get((y, c, h), np.nan) for y, c, h in zip(ly, a.county, a.hh)]
    a["buyer_ami"] = a.buyer_inc28 / a.MED; a["renter_ami"] = a.renter_inc / a.MED
    def tab(g):
        return g.agg(n=("zpid", "size"), med_rent=("last_p", "median"), med_price=("p", "median"),
                     med_rate=("pmms30", "median"), med_renter_inc=("renter_inc", "median"),
                     med_buyer_inc28=("buyer_inc28", "median"), med_ratio28=("ratio28", "median"),
                     med_ratio36=("ratio36", "median"), med_cash_down=("cash_down", "median"),
                     med_renter_ami=("renter_ami", "median"), med_buyer_ami=("buyer_ami", "median"),
                     share_buyer_gt_2x=("ratio28", lambda s: (s > 2).mean())).round(3)
    allt = tab(a.assign(all="all").groupby("all"))
    yc = tab(a[a.year >= 2015].groupby("year")); cc = tab(a[a.year >= 2022].groupby("county"))
    ht = tab(a[a.year >= 2022].groupby("homeType"))
    allt.to_csv(os.path.join(OUT, "a2_rent_to_sale_overall.csv")); yc.to_csv(os.path.join(OUT, "a2_rent_to_sale_by_year.csv"))
    cc.to_csv(os.path.join(OUT, "a2_rent_to_sale_by_county_2022plus.csv")); ht.to_csv(os.path.join(OUT, "a2_rent_to_sale_by_hometype_2022plus.csv"))
    print(allt.T.to_string()); print(yc.to_string()); print(cc.to_string()); print(ht.to_string())
    # ---- (b) sale -> rent within 12 months
    con = duckdb.connect(DB, read_only=True)
    zinfo = con.execute(f"select zpid, any_value(county) county, any_value(homeType) homeType, any_value(beds) beds from rep group by 1").df()
    allsales = con.execute(f"""select s.zpid, s.d::date d, s.p, any_value(z.county) county, any_value(z.homeType) homeType
        from (select distinct zpid, d, p from ev where not rental and event='Sold' and p between 50000 and 20000000) s
        join z using(zpid) group by 1,2,3""").df()
    con.close()
    allsales = allsales[allsales.county.isin(BAY.values()) & allsales.homeType.isin(RES)]
    allsales["d"] = pd.to_datetime(allsales.d)
    b = allsales.merge(rep[["zpid", "start_d", "last_p"]].rename(columns={"start_d": "rent_d", "last_p": "rent_p"}), on="zpid", how="left")
    b["conv"] = (b.rent_d > b.d) & (b.rent_d <= b.d + pd.Timedelta(days=365))
    b = b.sort_values(["zpid", "d", "conv", "rent_d"], ascending=[True, True, False, True]).drop_duplicates(["zpid", "d"])
    b["year"] = b.d.dt.year
    # restrict to sales with >= 12 months of follow-up before the scrape (max event date 2026-11)
    bb = b[(b.year >= 2015) & (b.d <= "2025-10-31")]
    conv = bb.groupby("year").agg(n_sales=("zpid", "size"), share_listed_for_rent_12m=("conv", "mean")).round(4)
    conv_c = bb[bb.year >= 2022].groupby("county").agg(n_sales=("zpid", "size"), share_listed_for_rent_12m=("conv", "mean")).round(4)
    cv = bb[bb.conv].copy(); cv = add_rate(cv, "d")
    cv["gross_yield"] = 12 * cv.rent_p / cv.p
    cv["owner_cost_mo"] = buyer_income(cv.p, cv.pmms30, 1.0) / 12
    cv["rent_over_owner_cost"] = cv.rent_p / cv.owner_cost_mo
    cvt = cv.groupby("year").agg(n=("zpid", "size"), med_price=("p", "median"), med_first_rent=("rent_p", "median"),
                                 med_gross_yield=("gross_yield", "median"), med_rent_over_PITI=("rent_over_owner_cost", "median")).round(3)
    conv = conv.join(cvt)
    conv.to_csv(os.path.join(OUT, "a2_sale_to_rent_12m_by_year.csv")); conv_c.to_csv(os.path.join(OUT, "a2_sale_to_rent_12m_by_county_2022plus.csv"))
    print(conv.to_string()); print(conv_c.to_string())
    print(f"sale->rent within 12m, all sales 2015..Oct-2025: {bb.conv.mean():.3%} of {len(bb)}")
    # ---- (c) flips from history
    s = allsales.sort_values(["zpid", "d"]).copy()
    s["d2"] = s.groupby("zpid").d.shift(-1); s["p2"] = s.groupby("zpid").p.shift(-1)
    f = s[(s.d2.notna()) & ((s.d2 - s.d).dt.days.between(30, 365))].copy()
    f["markup"] = f.p2 / f.p - 1; f = f[f.markup.between(-0.5, 3)]
    f["year"] = f.d2.dt.year
    ft = f[f.year >= 2015].groupby("year").agg(n_flips=("zpid", "size"), med_markup=("markup", "median"),
                                               p75_markup=("markup", lambda x: x.quantile(.75)),
                                               med_days=("d2", lambda x: np.nan), med_buy=("p", "median"), med_resale=("p2", "median")).round(3)
    ft["med_days"] = f[f.year >= 2015].assign(dd=(f.d2 - f.d).dt.days).groupby("year").dd.median()
    sales_y = allsales.assign(year=allsales.d.dt.year).groupby("year").size()
    ft["share_of_sales"] = (ft.n_flips / sales_y.reindex(ft.index)).round(4)
    fc = f[f.year >= 2022].groupby("county").agg(n_flips=("zpid", "size"), med_markup=("markup", "median")).round(3)
    ft.to_csv(os.path.join(OUT, "a2_flips_by_year.csv")); fc.to_csv(os.path.join(OUT, "a2_flips_by_county_2022plus.csv"))
    print(ft.to_string()); print(fc.to_string())
    # flag agreement
    con = duckdb.connect(DB, read_only=True)
    flag = con.execute("select zpid, is_flipped_within_12_months flag from z").df(); con.close()
    flag["hist_flip"] = flag.zpid.isin(f.zpid)
    fa = pd.crosstab(flag.flag, flag.hist_flip); fa.to_csv(os.path.join(OUT, "a2_flip_flag_vs_history.csv")); print(fa)
    a[["county", "zipcode", "homeType", "beds", "end_d", "d", "last_p", "p", "pmms30", "renter_inc", "buyer_inc28",
       "buyer_inc36", "ratio28", "renter_ami", "buyer_ami"]].to_parquet(os.path.join(OUT, "a2_rent_to_sale_events.parquet"), index=False)
    # figure
    fig, ax = plt.subplots(figsize=(7.5, 4))
    y = yc[yc.n >= 50]
    ax.plot(y.index, y.med_renter_inc / 1000, "o-", color="#4a7fb5", label="prior renter (3x rent)")
    ax.plot(y.index, y.med_buyer_inc28 / 1000, "o-", color="#c0392b", label="buyer of same unit (28% DTI, 20% down)")
    ax2 = ax.twinx(); ax2.bar(y.index, y.med_ratio28, alpha=0.15, color="#555"); ax2.set_ylabel("median buyer/renter income ratio (bars)")
    ax.set_ylabel("median income needed, $k (nominal)"); ax.set_xlabel("sale year")
    ax.set_zorder(ax2.get_zorder() + 1); ax.patch.set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper left"); ax.set_title("Rental unit sold: income needed by the household that replaces the renter", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "a2_rent_to_sale_income.png"), dpi=150); plt.close(fig)

if __name__ == "__main__":
    main()
