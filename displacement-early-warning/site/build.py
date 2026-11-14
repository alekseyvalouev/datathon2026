"""Build the findings page: reads result tables in ../results and writes index.html next to this file."""
import os, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(os.path.dirname(HERE), 'results')
def rd(n, **k): return pd.read_csv(os.path.join(RES, n), **k)
G = {'dtype': {'GEOID': str}}
TN = {'LISD': 'Low-income / susceptible', 'OD': 'Ongoing displacement', 'ARG': 'At risk of gentrification',
      'EOG': 'Early / ongoing gentrification', 'AdvG': 'Advanced gentrification', 'SMMI': 'Stable moderate / mixed',
      'ARE': 'At risk of becoming exclusive', 'BE': 'Becoming exclusive', 'SAE': 'Stable / advanced exclusive'}
D = {}

# ---- map
geo = json.load(open(os.path.join(RES, 'map_geometry.json')))
p2 = rd('e2_predictions.csv', **G); lab = rd('e2b_labels.csv', **G); city = rd('e4_tract_city.csv', **G)
aff = rd('e10_tract_affordability.csv', **G); p5 = rd('e5_predictions.csv', **G); p5 = p5[p5.target == 'flip']
tt = rd('e5_tract_table.csv', usecols=['GEOID', 'typ', 'typ_group'], **G)
t = p2.merge(lab[['GEOID', 'y_strict10']], on='GEOID').merge(city, on='GEOID', how='left').merge(tt, on='GEOID', how='left')
t = t.merge(p5[['GEOID', 'outcome']], on='GEOID', how='left').merge(aff[['GEOID', 'rent_to_income']], on='GEOID', how='left')
t['rk'] = (t.p_loco.rank(pct=True) * 100).round(0)
k = int(t.lostli_18.sum()); t['flag'] = (t.p_loco.rank(ascending=False, method='first') <= k).astype(int)
t['hm'] = np.select([(t.flag == 1) & (t.lostli_18 == 1), (t.flag == 0) & (t.lostli_18 == 1), (t.flag == 1) & (t.lostli_18 == 0)], [1, 2, 3], 0)
t['loss'] = t.lostli_18 + t.y_strict10
tg = {'low_income': 0, 'moderate': 1, 'high': 2}
rows = {}
for r in t.itertuples():
    rows[r.GEOID] = [r.city if isinstance(r.city, str) else '', r.county_name, TN.get(r.typ, 'Unclassified'), int(r.rk), int(r.loss), int(r.hm),
                     None if pd.isna(r.outcome) else round(r.outcome * 100, 1), None if pd.isna(r.rent_to_income) else round(r.rent_to_income * 100),
                     tg.get(r.typ_group, 3)]
D['geo'] = geo; D['tracts'] = rows
D['hm_counts'] = [int((t.hm == i).sum()) for i in range(4)]

# ---- charts
c = rd('e1_by_county.csv').sort_values('lostli_18', ascending=False)
D['county'] = [{'l': r.county_name, 'v': round(r.lostli_18 * 100, 1), 'n': int(r.tracts)} for r in c.itertuples()]
m = rd('e2_test_metrics.csv'); nm = {'logistic': 'Logistic regression', 'random_forest': 'Random forest', 'grad_boost': 'Gradient boosting',
     'one variable': 'Renter share in 2000 alone', 'UDP vul_gent_00 flag': 'UDP vulnerability flag, 2000', 'UDP lostli_00': 'Lost low-income households 1990-2000'}
D['auc'] = []
for key, name in nm.items():
    r = m[m.model.str.startswith(key)].iloc[0]
    D['auc'].append({'l': name, 'v': round(r.test_auc, 3), 'lo': round(r.auc_lo, 3), 'hi': round(r.auc_hi, 3), 's': 0 if key in ('logistic', 'random_forest', 'grad_boost') else 1})
lb = rd('e2b_label_robustness.csv'); ln = ['Any loss (base label)', 'Lost 10% or more', 'Low-income share fell 5+ points']
D['labels'] = [{'l': ln[i], 'n': f"{int(r.test_pos)} of {int(r.test_n)} test tracts", 'a': round(r.test_auc, 3), 'b': round(r.udp_flag_auc, 3)} for i, r in enumerate(lb.itertuples())]
f = rd('e5_test_metrics.csv'); tn = {'flip': 'Flipping hot spot', 'apprec': 'High price appreciation', 'rent': 'High rent growth'}
D['fwd'] = []
for key, name in tn.items():
    x = f[f.target == key]
    g = lambda pre: round(float(x[x.model.str.startswith(pre)].test_auc.iloc[0]), 3)
    D['fwd'].append({'l': name, 'n': f"{int(x.test_n.iloc[0])} test tracts", 'a': g('census:'), 'b': g('census+zillow'), 'c': g('UDP vul_gent_18')})
fl = rd('e7_flip_by_typology.csv'); cols = [x for x in fl.columns if 'mo_' in x]
fl = fl[fl.typ.isin(TN)].sort_values('18mo_20pct', ascending=False)
fli = fl.set_index('typ')
D['flip'] = [{'l': TN[t], 'v': round(fli.loc[t, '18mo_20pct'] * 100, 1), 'lo': round(fli.loc[t, cols].min() * 100, 1), 'hi': round(fli.loc[t, cols].max() * 100, 1), 'n': int(fli.loc[t, 'resales'])} for t in fli.index]
tr = rd('e9_typology_trajectories.csv'); tr = tr[tr.typ.isin(TN)].sort_values('pre_ann', ascending=False)
D['traj'] = [{'l': TN[r.typ], 'a': round(r.pre_ann * 100, 1), 'b': round(r.post_ann * 100, 1), 'n': int(r.n_min)} for r in tr.itertuples()]
rb = rd('e10_rent_burden_by_typology.csv'); rb = rb[rb.typ.isin(TN)].sort_values('median_rent_to_income', ascending=False)
D['burden'] = [{'l': TN[r.typ], 'v': round(r.median_rent_to_income * 100), 'n': int(r.tracts), 'rent': int(r.median_ask_rent), 'inc': int(r.median_hinc_2018usd)} for r in rb.itertuples()]
rt = pd.read_csv(os.path.join(RES, 'e8_rent_turnover.csv')); rt.columns = ['group'] + list(rt.columns[1:])
x = rt[rt.cut == 'county'].sort_values('share_over_10pct', ascending=False)
D['turn'] = [{'l': r.group, 'v': round(r.share_over_10pct * 100, 1), 'n': int(r.pairs)} for r in x.itertuples()]
s3 = rd('e3_subgroups.csv'); s3 = s3[s3.view == 'test']
order = [('tenure', 'majority renter', 'Majority renter'), ('tenure', 'majority owner', 'Majority owner'), ('income_tercile', 'low income', 'Low-income third'),
         ('income_tercile', 'middle income', 'Middle-income third'), ('income_tercile', 'high income', 'High-income third'), ('rail', 'rail', 'Near rail'), ('rail', 'no rail', 'No rail'),
         ('race', 'majority people of color', 'Majority people of color'), ('race', 'majority white', 'Majority white')]
D['sub'] = []
for cut, grp, name in order:
    r = s3[(s3.cut == cut) & (s3.group == grp)].iloc[0]
    D['sub'].append({'l': name, 'n': f"{int(r.pos)} losses in {int(r.n)} tracts", 'a': round(r.recall * 100), 'b': round(r.fpr * 100)})
s6 = rd('e6_subgroups.csv'); s6 = s6[(s6.target == 'flip') & (s6.view == 'test')]
order6 = [('typology_group', 'low_income', 'UDP low-income typologies'), ('typology_group', 'moderate', 'UDP moderate typologies'), ('typology_group', 'high', 'UDP high-income typologies'),
          ('race', 'majority people of color', 'Majority people of color'), ('race', 'majority white', 'Majority white')]
D['sub6'] = []
for cut, grp, name in order6:
    r = s6[(s6.cut == cut) & (s6.group == grp)].iloc[0]
    D['sub6'].append({'l': name, 'n': f"{int(r.pos)} hot spots in {int(r.n)} tracts", 'a': round(r.recall * 100), 'b': round(r.fpr * 100), 'auc': round(r.auc, 2)})

html = open(os.path.join(HERE, 'template.html')).read().replace('/*__DATA__*/', 'const D=' + json.dumps(D, separators=(',', ':')) + ';')
open(os.path.join(HERE, 'index.html'), 'w').write(html)
print('written', len(html)); print(json.dumps({k: v for k, v in D.items() if k not in ('geo', 'tracts')}, indent=0)[:6000])
