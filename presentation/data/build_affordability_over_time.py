"""Share of Bay Area cities where a median full-time worker's pay covers the city's median asking rent
(rent <= 30% of gross pay), by year, for clerical, customer support and frontline service work.

Pay : ACS 1-year PUMS, California person file, nine Bay counties, full-time full-year workers
      (35+ hours, 50-52 weeks), weighted median WAGP, nominal dollars. No 2020 file exists.
Rent: Zillow priceHistory rental episodes (zillow.duckdb table `rep`), median settled asking rent
      of listings that started that year, per city.
Also reports the share of individual listings (all Bay cities pooled) that the same pay covers.
Usage: python3 build_affordability_over_time.py <dir with pca_YYYY.zip> <zillow.duckdb> <out dir>
"""
import sys, zipfile, numpy as np, pandas as pd, duckdb
PUMS, ZDB, OUT = sys.argv[1:4]
YEARS = [2012,2013,2014,2015,2016,2017,2018,2019,2021,2022,2023,2024]
BAY = {'001','013','041','055','075','081','085','095','097'}
MIN_N = 10; THR = 0.30
SUPPORT = {1050,5010,5020,5040,5160,5240,5300,5410,5520,5521,5522}
LOGI = {5510,5530,5550,5560,5610,5630}
RETAIL = {4700,4720,4740,4750,4760,4900,4950}
def occ(c):
    if c in SUPPORT: return 'CUSTOMER_SUPPORT'
    if c in LOGI or c in RETAIL: return 'FRONTLINE_SERVICE'
    if 5000 <= c <= 5940: return 'CLERICAL_ADMIN'
    if 3700 <= c <= 4655 or 9000 <= c <= 9760: return 'FRONTLINE_SERVICE'
    return None
def wmed(x, w):
    i = np.argsort(x); x = x[i]; cw = np.cumsum(w[i]); return float(x[np.searchsorted(cw, 0.5*cw[-1])])
rows = []
for y in YEARS:
    with zipfile.ZipFile(f'{PUMS}/pca_{y}.zip') as z:
        name = [n for n in z.namelist() if n.lower().endswith('.csv')][0]
        with z.open(name) as f: hdr = f.readline().decode().strip().split(',')
        wk = 'WKWN' if 'WKWN' in hdr else 'WKW'
        with z.open(name) as f:
            d = pd.read_csv(f, usecols=['PUMA','OCCP','WAGP','WKHP',wk,'PWGTP'], dtype=str)
    for c in ['OCCP','WAGP','WKHP',wk,'PWGTP']: d[c] = pd.to_numeric(d[c], errors='coerce')
    d = d[d.PUMA.str.zfill(5).str[:3].isin(BAY)]
    fy = (d[wk] >= 50) if wk == 'WKWN' else (d[wk] == 1)
    d = d[fy & (d.WKHP >= 35) & (d.WAGP > 0) & d.OCCP.notna()].copy()
    d['occ'] = d.OCCP.astype(int).map(occ)
    for o, g in d.dropna(subset=['occ']).groupby('occ'):
        rows.append(dict(year=y, occ=o, median_pay=wmed(g.WAGP.values, g.PWGTP.values), n_workers_unweighted=len(g)))
pay = pd.DataFrame(rows)
con = duckdb.connect(ZDB, read_only=True)
rent = con.execute(f"""select cast(substr(start_d,1,4) as int) as "year", lower(trim(city)) as city, any_value(county) as county,
    median(last_p) as median_rent, count(*) as n_listings from rep where city is not null group by 1,2 having count(*)>={MIN_N}""").df()
rent = rent[rent.year.between(2012, 2026)]
rent.to_csv(f'{OUT}/city_rent_by_year.csv', index=False)
# cities present (>= MIN_N listings) in every year from 2017 on: a fixed panel, so the city mix does not drift
lst = con.execute('select cast(substr(start_d,1,4) as int) as "year", last_p as p from rep').df()
p = rent[rent.year >= 2017]; fixed = set(p.groupby('city').year.nunique().loc[lambda s: s == p.year.nunique()].index)
out = []
for _, r in pay.iterrows():
    L = lst[lst.year == r.year].p
    c = rent[rent.year == r.year]; cf = c[c.city.isin(fixed)]
    out.append(dict(year=int(r.year), occ=r.occ, median_pay=r.median_pay, max_rent_at_30pct=round(r.median_pay*THR/12),
        n_cities=len(c), cities_affordable=int((12*c.median_rent <= THR*r.median_pay).sum()),
        pct_cities_affordable=round(100*(12*c.median_rent <= THR*r.median_pay).mean(), 1),
        n_listings=len(L), pct_listings_affordable=round(100*(12*L <= THR*r.median_pay).mean(), 1), median_listing_rent=L.median(),
        median_city_rent=c.median_rent.median(), median_rent_burden_pct=round(100*(12*c.median_rent/r.median_pay).median(), 1),
        n_cities_fixed=len(cf), pct_cities_affordable_fixed=round(100*(12*cf.median_rent <= THR*r.median_pay).mean(), 1) if len(cf) else np.nan,
        n_workers_unweighted=int(r.n_workers_unweighted)))
o = pd.DataFrame(out).sort_values(['occ','year']); o.to_csv(f'{OUT}/affordability_over_time.csv', index=False)
pd.set_option('display.width', 250); print(o.to_string(index=False)); print('fixed panel cities', len(fixed))
print(rent.groupby('year').agg(n_cities=('city','size'), med=('median_rent','median'), mn=('median_rent','min'), listings=('n_listings','sum')))
