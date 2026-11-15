"""Raw Zillow CSVs -> analysis/cache/zillow.duckdb with tables:
  z    : one row per property (selected columns)
  ev   : flattened priceHistory events (zpid, d, event, p, rental)
  rep  : rental listing episodes (one per 'Listed for rent'; last_p = last listed price in episode)
  turn : consecutive episode pairs on same unit (same unit, next tenant)
Usage: python3 analysis/common/build_zillow.py
"""
import duckdb, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# Raw data lives outside git: DATATHON_DATA, default <repo>/data, laid out by scripts/setup_data.sh
DATA_DIR = os.environ.get("DATATHON_DATA") or os.path.join(os.path.dirname(ROOT), "data")
FILES = [os.path.join(DATA_DIR, "zillow", f) for f in ("Zillow_part1.csv", "zillow_part2.csv", "zillow_part3.csv")]
COLS = ("zpid,city,county,zipcode,state,homeStatus,homeType,price,zestimate,rentZestimate,bedrooms,bathrooms,"
        "livingArea,yearBuilt,latitude,longitude,lastSoldPrice,dateSold,daysOnZillow,priceHistory,taxHistory,"
        "isNonOwnerOccupied,countyFIPS,is_flipped_within_12_months,listing_provided_by,is_listed_by_management_company")
os.makedirs(os.path.join(ROOT, "analysis/cache"), exist_ok=True)
con = duckdb.connect(os.path.join(ROOT, "analysis/cache/zillow.duckdb"))
parts = []
for i, f in enumerate(FILES):
    con.execute(f"create or replace table z{i} as select {COLS} from read_csv('{f}', header=true, all_varchar=true, "
                "max_line_size=50000000, ignore_errors=true, parallel=false)")
    parts.append(f"select * from z{i}")
con.execute("create or replace table z as " + " union all by name ".join(parts))
for i in range(len(FILES)): con.execute(f"drop table z{i}")
con.execute("""create or replace table ev as
select zpid, county, city, zipcode, homeStatus, homeType, try_cast(bedrooms as double) beds,
  try_cast(bathrooms as double) baths, try_cast(livingArea as double) sqft, try_cast(yearBuilt as int) yearBuilt,
  try_cast(latitude as double) lat, try_cast(longitude as double) lon,
  e->>'date' as d, e->>'event' as event, try_cast(e->>'price' as double) as p, (e->>'postingIsRental')='true' as rental,
  k, (e->>'date') || '#' || lpad((1000000 - k)::varchar, 7, '0') as sk
from (select *, unnest(h) e, generate_subscripts(h, 1) k
      from (select *, from_json(priceHistory, '["JSON"]') h from z where priceHistory like '[%'))""")
# k = position in Zillow's priceHistory (newest first), so on the same date a smaller k is the later event.
# sk sorts events in time with that tie-break; without it, same-day events were ordered arbitrarily and
# 71 of 145,870 rental episodes could get a different last price on each build.
con.execute("""create or replace table rep as
with r as (select *, sum(case when event='Listed for rent' then 1 else 0 end) over (partition by zpid order by d,
             case event when 'Listed for rent' then 0 else 1 end, k desc rows unbounded preceding) ep from ev where rental),
e as (select zpid, any_value(county) county, any_value(city) city, any_value(zipcode) zipcode, any_value(homeType) homeType,
       any_value(beds) beds, any_value(baths) baths, any_value(sqft) sqft, any_value(yearBuilt) yearBuilt,
       any_value(lat) lat, any_value(lon) lon, ep,
       min(d) filter (where event='Listed for rent') start_d, max(d) end_d,
       arg_max(p, sk) filter (where p is not null and event<>'Listing removed') last_p,
       arg_min(p, sk) filter (where event='Listed for rent') first_p,
       count(*) filter (where event='Price change') n_changes
      from r where ep>0 group by zpid, ep)
select * from e where start_d is not null and last_p between 500 and 30000""")
con.execute("""create or replace table turn as
select a.*, b.start_d next_start, b.first_p next_first, b.last_p next_last, b.n_changes next_n_changes,
  date_diff('day', a.end_d::date, b.start_d::date)/365.25 gap_y,
  date_diff('day', a.start_d::date, b.start_d::date)/365.25 start_gap_y
from rep a join rep b on a.zpid=b.zpid and b.ep=a.ep+1""")
for t in ["z", "ev", "rep", "turn"]:
    print(t, con.execute(f"select count(*) from {t}").fetchone()[0])
