"""E0 Extract slim property table and price-history events from one raw Zillow CSV (7.4 GB total, 139 columns).
Usage: python3 -I e0_extract_zillow.py <raw_csv> <tag> <out_dir>   -> <out_dir>/slim_<tag>.csv and hist_<tag>.jsonl
hist line = [zpid, [[date, event, price, postingIsRental(0/1)], ...]]. Rows with a wrong column count are skipped."""
import sys, csv, json, os
csv.field_size_limit(10**9)
src, tag, out = sys.argv[1], sys.argv[2], sys.argv[3]
keep = ['zpid', 'city', 'county', 'zipcode', 'homeStatus', 'homeType', 'price', 'zestimate', 'rentZestimate', 'bedrooms', 'bathrooms', 'livingArea', 'yearBuilt',
        'latitude', 'longitude', 'lastSoldPrice', 'dateSold', 'daysOnZillow', 'taxAssessedValue', 'propertyTaxRate']
n = 0
with open(src, newline='', encoding='utf-8', errors='replace') as f, open(os.path.join(out, f'slim_{tag}.csv'), 'w', newline='') as o, open(os.path.join(out, f'hist_{tag}.jsonl'), 'w') as h:
    r = csv.reader(f); hdr = next(r); ix = {c: i for i, c in enumerate(hdr)}
    w = csv.writer(o); w.writerow(keep); ph = ix['priceHistory']; nh = len(hdr)
    for row in r:
        n += 1
        if len(row) != nh: continue
        w.writerow([row[ix[c]] for c in keep])
        try:
            ev = [[e.get('date'), e.get('event'), e.get('price'), 1 if e.get('postingIsRental') else 0] for e in json.loads(row[ph])] if row[ph] else []
        except Exception: ev = None
        h.write(json.dumps([row[ix['zpid']], ev]) + '\n')
print(tag, 'rows read', n)
