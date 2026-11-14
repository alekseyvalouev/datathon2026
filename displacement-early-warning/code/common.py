"""Shared loaders and helpers. Paths are overridable through environment variables:
  UDP_REPO    clone of github.com/urban-displacement/displacement-typologies (default <project>/data/udp)
  ZILLOW_WORK folder with slim_*.csv and hist_*.jsonl made by e0_extract_zillow.py (default ~/work)
  RESULTS     output folder (default <project>/results)
"""
import os, json, glob
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UDP_REPO = os.environ.get('UDP_REPO', os.path.join(ROOT, 'data', 'udp'))
ZW = os.environ.get('ZILLOW_WORK', os.path.join(os.path.expanduser('~'), 'work'))
RES = os.environ.get('RESULTS', os.path.join(ROOT, 'results'))
os.makedirs(RES, exist_ok=True)
UDP_CSV = os.path.join(UDP_REPO, 'data/outputs/typologies/SanFrancisco_typology_output.csv')
TRACT_SHP = os.path.join(UDP_REPO, 'data/inputs/shp/SanFrancisco/cb_2018_06_tract_500k')
SEED = 42
COUNTY = {'001': 'Alameda', '013': 'Contra Costa', '041': 'Marin', '055': 'Napa', '075': 'San Francisco',
          '081': 'San Mateo', '085': 'Santa Clara', '095': 'Solano', '097': 'Sonoma'}
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 300); pd.set_option('display.max_columns', 60)
pd.set_option('display.float_format', lambda x: f'{x:,.3f}')

# 1990/2000 features only (no 2012/2018 information) for the 2000-2018 backtest
FEATS00 = ['per_all_li_90', 'per_all_li_00', 'per_nonwhite_90', 'per_nonwhite_00', 'per_rent_90', 'per_rent_00',
           'per_col_90', 'per_col_00', 'real_mrent_90', 'real_mrent_00', 'real_mhval_90', 'real_mhval_00',
           'real_hinc_90', 'real_hinc_00', 'pctch_real_mhval_90_00', 'pctch_real_mrent_90_00',
           'pctch_real_hinc_90_00', 'ch_per_col_90_00', 'ch_all_li_count_90_00']
# 2012/2018 census features for the forward test (known by 2018)
FEATS18 = ['per_all_li_18', 'per_nonwhite_18', 'per_rent_18', 'per_col_18', 'real_mrent_18', 'real_mhval_18',
           'real_hinc_18', 'real_mrent_12', 'real_mhval_12', 'pctch_real_mhval_00_18', 'pctch_real_mrent_12_18',
           'pctch_real_hinc_00_18', 'ch_per_col_00_18', 'per_limove_18', 'per_limove_12', 'per_units_pre50_18',
           'ch_all_li_count_00_18', 'rail', 'presence_ph_LIHTC', 'dense', 'log_pop_18']
TYP_ORDER = ['LISD', 'OD', 'ARG', 'EOG', 'AdvG', 'SMMI', 'ARE', 'BE', 'SAE', 'Unclassified']
TYP_NAME = {'LISD': 'Low-Income/Susceptible to Displacement', 'OD': 'Ongoing Displacement',
            'ARG': 'At Risk of Gentrification', 'EOG': 'Early/Ongoing Gentrification',
            'AdvG': 'Advanced Gentrification', 'SMMI': 'Stable Moderate/Mixed Income',
            'ARE': 'At Risk of Becoming Exclusive', 'BE': 'Becoming Exclusive',
            'SAE': 'Stable/Advanced Exclusive', 'Unclassified': 'Unclassified'}


def load_udp():
    """UDP typology output -> nine-county Bay Area tracts with pop00flag==1 (expected 1,550)."""
    d = pd.read_csv(UDP_CSV, low_memory=False)
    d['GEOID'] = d['GEOID'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(11)
    d['cfips'] = d.GEOID.str[2:5]
    d = d[d.cfips.isin(COUNTY) & (d.pop00flag == 1)].copy()
    d = d.replace([np.inf, -np.inf], np.nan)
    d['county_name'] = d.cfips.map(COUNTY)
    # primary typology = first code in the list; 'AdvG, BE' double label is kept as AdvG
    d['typ'] = d.typ_cat.str.extract(r"'(\w+)'")[0].fillna('Unclassified')
    d['typ_group'] = d.typ.map({'LISD': 'low_income', 'OD': 'low_income', 'ARG': 'low_income', 'EOG': 'low_income',
                                'AdvG': 'moderate', 'SMMI': 'moderate', 'ARE': 'high', 'BE': 'high', 'SAE': 'high',
                                'Unclassified': 'unclassified'})
    d['log_pop_18'] = np.log1p(d.pop_18)
    return d.reset_index(drop=True)


def subgroups(d, yr):
    """Subgroup labels built from year-`yr` ('00' or '18') characteristics, i.e. known at prediction time."""
    g = pd.DataFrame(index=d.index)
    inc = d[f'real_hinc_{yr}']
    g['income_tercile'] = pd.qcut(inc, 3, labels=['low income', 'middle income', 'high income']).astype(object)
    g['race'] = np.where(d[f'per_nonwhite_{yr}'] > .5, 'majority people of color', 'majority white')
    g['tenure'] = np.where(d[f'per_rent_{yr}'] > .5, 'majority renter', 'majority owner')
    g['rail'] = np.where(d['rail'] == 1, 'rail', 'no rail')
    g['county'] = d['county_name']
    return g


def topk_metrics(y, s, k):
    """precision and recall when the k highest-scored tracts are flagged."""
    y = np.asarray(y); s = np.asarray(s)
    idx = np.argsort(-s, kind='stable')[:k]
    tp = y[idx].sum()
    return tp / k, tp / max(y.sum(), 1)


def load_props():
    p = pd.concat([pd.read_csv(f, dtype={'zpid': str, 'zipcode': str}, low_memory=False)
                   for f in sorted(glob.glob(os.path.join(ZW, 'slim_*.csv')))], ignore_index=True)
    p = p.drop_duplicates('zpid')
    p['county'] = p.county.str.replace(' County', '', regex=False)
    return p


def load_events():
    rows = []
    for f in sorted(glob.glob(os.path.join(ZW, 'hist_*.jsonl'))):
        with open(f) as fh:
            for line in fh:
                z, ev = json.loads(line)
                for e in ev or []:
                    rows.append((z, e[0], e[1], e[2], e[3]))
    e = pd.DataFrame(rows, columns=['zpid', 'date', 'event', 'price', 'rental'])
    e['d'] = pd.to_datetime(e.date, errors='coerce')
    e['price'] = pd.to_numeric(e.price, errors='coerce')
    return e.dropna(subset=['d']).drop_duplicates()


def load_joined():
    """properties with tract GEOID (made by e4_zillow_tract_join.py)."""
    return pd.read_csv(os.path.join(RES, 'e4_property_tract.csv.gz'), dtype={'zpid': str, 'GEOID': str, 'zipcode': str})


def sales_and_pairs(p):
    """Clean Sold events and consecutive same-property resale pairs. p must have zpid, GEOID, livingArea, homeType."""
    e = load_events()
    info = p[p.homeType != 'LOT'].set_index('zpid')[['GEOID', 'zipcode', 'city', 'county', 'livingArea', 'homeType']]
    s = e[(e.event == 'Sold') & (e.rental == 0) & (e.price > 50000)].sort_values(['zpid', 'd']).drop_duplicates(['zpid', 'date'])
    s = s.join(info, on='zpid', how='inner')
    s['y'] = s.d.dt.year
    s['ppsf'] = s.price / s.livingArea.where(s.livingArea > 200)
    s['pd_'] = s.groupby('zpid').d.shift(); s['pp'] = s.groupby('zpid').price.shift()
    pr = s.dropna(subset=['pp']).copy()
    pr['mo'] = (pr.d - pr.pd_).dt.days / 30.44
    pr = pr[pr.mo >= 1]
    pr['mk'] = pr.price / pr.pp - 1
    pr = pr[(pr.mk > -0.8) & (pr.mk < 5)]
    pr['ann'] = (pr.price / pr.pp) ** (12 / pr.mo.clip(lower=12)) - 1
    pr['flip'] = ((pr.mo <= 18) & (pr.mk >= 0.2)).astype(int)
    pr['buy_y'] = pr.pd_.dt.year
    return s, pr
