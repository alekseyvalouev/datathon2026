"""Step 0: pull extra listing columns (not in the shared cache) from the raw Zillow CSVs -> cache/extra.parquet.
Only non-identifying columns are kept (no address / streetAddress / url)."""
import duckdb, os
from common import ROOT, CACHE
D = os.path.join(ROOT, "data/[For Students] 8th Datathon For Social Good/zillow housing dataset/")
FILES = [D + "Zillow_part1.csv", os.path.join(ROOT, "zillow_part2-005.csv"), D + "zillow_part3.csv"]
COLS = ("zpid,homeStatus,homeType,county,zipcode,price,bedrooms,description,special_offer,base_rent,"
        "rentalApplicationsAcceptedType,mortgageRates,sold_to_list_ratio,is_flipped_within_12_months,"
        "propertyTaxRate,yearBuilt,is_listed_by_management_company,unit_amenities,dateSold,lastSoldPrice")
def main():
    out = os.path.join(CACHE, "extra.parquet")
    if os.path.exists(out):
        print("cached", out); return
    con = duckdb.connect()
    q = " union all by name ".join(
        f"select {COLS} from read_csv('{f}', header=true, all_varchar=true, max_line_size=50000000, "
        f"ignore_errors=true, parallel=false)" for f in FILES)
    con.execute(f"copy ({q}) to '{out}' (format parquet)")
    print(con.execute(f"select count(*), count(distinct zpid) from '{out}'").fetchone())
if __name__ == "__main__":
    main()
