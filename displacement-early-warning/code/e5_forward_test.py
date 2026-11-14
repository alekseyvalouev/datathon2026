import sys, os, site; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); site.addsitedir(site.getusersitepackages())  # needed because scripts run with python -I
"""E5 Forward test: do conditions known by end-2018 predict post-2018 market pressure?
Outcomes (tract level, Zillow events dated 2019-01-01 or later):
  flip   = share of resales closing 2019-2026 that were flips (resold <=18 months after purchase at >=20% markup); tracts with >=15 resales
  apprec = median annualized same-property appreciation, bought 2019+ and held >=24 months; tracts with >=8 such pairs
  rent   = median annualized same-unit asking-rent change, first listing 2019-2023 vs last listing 2025-2026; tracts with >=5 units
Binary target = tract in the top quartile of the outcome (threshold computed on dev tracts only).
Features: UDP census variables for 2012/2018 (C) and Zillow features built only from events dated before 2019 (Z).
Test set: spatial blocks (0.1-degree grid cells within county, 25% of each county's cells) never used for tuning; tuning by county-held-out GroupKFold on dev."""
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.inspection import permutation_importance
from sklearn.base import clone
from common import *

CUT = pd.Timestamp('2019-01-01')
u = load_udp(); p = load_joined(); p = p[p.GEOID.isin(u.GEOID)]
s, pr = sales_and_pairs(p)
pre, post = pr[pr.d < CUT], pr[pr.d >= CUT]
assert pre.d.max() < CUT and s[s.d < CUT].d.max() < CUT
T = pd.DataFrame(index=u.GEOID)
# ---------- outcomes (2019+) ----------
g = post.groupby('GEOID').flip.agg(['size', 'sum']); T['post_pairs'] = g['size']; T['post_flips'] = g['sum']; T['flip'] = (g['sum'] / g['size']).where(g['size'] >= 15)
h = post[(post.pd_ >= CUT) & (post.mo >= 24)].groupby('GEOID').ann.agg(['size', 'median']); T['post_hold_n'] = h['size']; T['apprec'] = h['median'].where(h['size'] >= 8)
e = load_events(); r = e[(e.rental == 1) & (e.price > 500) & (e.price < 20000)].copy(); r['y'] = r.d.dt.year
r = r.join(p.set_index('zpid')[['GEOID']], on='zpid', how='inner')
ry = r.groupby(['zpid', 'GEOID', 'y']).price.median().reset_index()
a = ry[ry.y.between(2019, 2023)].sort_values('y').groupby('zpid').first(); b = ry[ry.y >= 2025].sort_values('y').groupby('zpid').last()
rc = a.join(b[['y', 'price']], rsuffix='_b', how='inner'); rc['ann'] = (rc.price_b / rc.price) ** (1 / (rc.y_b - rc.y)) - 1; rc = rc[rc.ann.between(-.3, .5)]
h = rc.groupby('GEOID').ann.agg(['size', 'median']); T['post_rent_n'] = h['size']; T['rent'] = h['median'].where(h['size'] >= 5)
# ---------- Zillow features (strictly before 2019) ----------
pre10 = pre[pre.d >= '2009-01-01']; p0 = pre10.flip.mean()
g = pre10.groupby('GEOID').flip.agg(['size', 'sum']).reindex(T.index).fillna(0)
T['z_flip_pre'] = (g['sum'] + 10 * p0) / (g['size'] + 10)   # shrunk toward the regional pre-2019 rate (10 pseudo-pairs)
T['z_log_pairs_pre'] = np.log1p(g['size'])
def med(x, col, k): h = x.groupby('GEOID')[col].agg(['size', 'median']); return h['median'].where(h['size'] >= k)
T['z_apprec_pre'] = med(pre[pre.d >= '2012-01-01'], 'ann', 3)
sp = s[(s.d < CUT) & s.ppsf.notna()]
T['z_ppsf_14_18'] = med(sp[sp.y >= 2014], 'ppsf', 3); T['z_ppsf_09_13'] = med(sp[sp.y.between(2009, 2013)], 'ppsf', 3)
T['z_ppsf_growth_pre'] = np.log(T.z_ppsf_14_18 / T.z_ppsf_09_13)
T['z_log_sales_12_18'] = np.log1p(sp[sp.y >= 2012].groupby('GEOID').size().reindex(T.index).fillna(0))
rp = ry[ry.y.between(2015, 2018)].groupby(['zpid', 'GEOID']).price.median().reset_index()
T['z_rent_pre'] = med(rp, 'price', 3); T['z_log_rent_units_pre'] = np.log1p(rp.groupby('GEOID').size().reindex(T.index).fillna(0))
T['z_rent_to_ppsf_pre'] = T.z_rent_pre / T.z_ppsf_14_18
# neighbour features: 8 nearest tract centroids (features only, never outcomes)
cen = pd.read_csv(os.path.join(RES, 'e4_tract_centroids.csv'), dtype={'GEOID': str}).set_index('GEOID').reindex(T.index)
xy = np.c_[cen.lon.values * np.cos(np.radians(37.8)), cen.lat.values]; dist = ((xy[:, None, :] - xy[None, :, :]) ** 2).sum(-1); np.fill_diagonal(dist, np.inf)
nb = np.argsort(dist, axis=1)[:, :8]
T['z_nb_flip_pre'] = (g['sum'].values[nb].sum(1) + 10 * p0) / (g['size'].values[nb].sum(1) + 10)
for c in ['z_ppsf_14_18', 'z_apprec_pre', 'z_ppsf_growth_pre']: T['z_nb_' + c[2:]] = np.nanmean(T[c].values[nb], axis=1)
ZF = [c for c in T.columns if c.startswith('z_')]
CF = FEATS18 + ['per_ch_zillow_12_18']
D = u.set_index('GEOID').join(T).join(cen)
D['city'] = pd.read_csv(os.path.join(RES, 'e4_tract_city.csv'), dtype={'GEOID': str}).set_index('GEOID').city.reindex(D.index)
# spatial blocks = 0.1-degree grid cells within a county; 25% of each county's cells (at least one) are held out.
# (A first draw that ignored county happened to contain no San Francisco tract; that run is kept in logs/e5_first_draw_no_sf.log.)
D['block'] = D.cfips + '_' + np.floor(D.lon / 0.1).astype(int).astype(str) + '_' + np.floor(D.lat / 0.1).astype(int).astype(str)
blocks = np.sort(D.block.unique()); rng = np.random.RandomState(SEED); tb = []
for c in sorted(COUNTY):
    bc = np.array([b for b in blocks if b.startswith(c + '_')]); tb += list(rng.choice(bc, max(1, int(round(.25 * len(bc)))), replace=False))
D['is_test'] = D.block.isin(tb)
print('tracts', len(D), '| spatial blocks', len(blocks), '| test blocks', len(tb), '| test tracts', int(D.is_test.sum()))
print('test tracts by county:', D[D.is_test].county_name.value_counts().to_dict())
print('outcome coverage (tracts):', {k: int(D[k].notna().sum()) for k in ['flip', 'apprec', 'rent']}, '| post resales', int(T.post_pairs.sum()), 'post flips', int(T.post_flips.sum()), '| hold pairs', int(T.post_hold_n.sum()), '| rent units', len(rc))
print('Zillow feature missing share:'); print(D[ZF].isna().mean().round(3).to_string())
print('outcome summary:'); print(D[['flip', 'apprec', 'rent']].describe().T.to_string())
print('Spearman between outcomes:'); print(D[['flip', 'apprec', 'rent']].corr(method='spearman').to_string())
print('outcomes by UDP typology (median; n tracts):'); print(D.groupby('typ')[['flip', 'apprec', 'rent']].agg(['median', 'count']).reindex(TYP_ORDER).to_string())
D.drop(columns=[c for c in D.columns if c.startswith('mov_')]).to_csv(os.path.join(RES, 'e5_tract_table.csv'))

def lr(C): return make_pipeline(SimpleImputer(strategy='median', add_indicator=True), StandardScaler(), LogisticRegression(C=C, max_iter=3000))
def gb(depth): return HistGradientBoostingClassifier(learning_rate=0.05, max_depth=depth, max_iter=150, l2_regularization=1.0, random_state=SEED)
def rf(leaf): return make_pipeline(SimpleImputer(strategy='median', add_indicator=True), RandomForestClassifier(n_estimators=300, min_samples_leaf=leaf, random_state=SEED, n_jobs=-1))
CANDS = [('logistic', lr, 0.1), ('logistic', lr, 1.0), ('grad_boost', gb, 2), ('grad_boost', gb, 3), ('random_forest', rf, 10)]
def oof(model, X, y, grp, splitter):
    o = np.full(len(y), np.nan)
    for tr, va in splitter.split(X, y, grp): o[va] = clone(model).fit(X.iloc[tr], y[tr]).predict_proba(X.iloc[va])[:, 1]
    return o
allrows = []; allpred = []; allimp = []
for tgt in ['flip', 'apprec', 'rent']:
    E = D[D[tgt].notna()].copy(); dev, te = E[~E.is_test], E[E.is_test]
    if len(te) < 60 or len(dev) < 250: print(f'\n### {tgt}: too few tracts (dev {len(dev)}, test {len(te)}), skipped'); continue
    thr = dev[tgt].quantile(.75); E['y'] = (E[tgt] > thr).astype(int); dev, te = E[~E.is_test], E[E.is_test]
    yd, yt = dev.y.values, te.y.values; k = int(yt.sum())
    print(f'\n### target {tgt}: top-quartile threshold (dev) = {thr:.4f} | dev n={len(dev)} pos={yd.sum()} | TEST n={len(te)} pos={k}')
    scores = {}; chosen = {}
    for fs, cols in [('census', CF), ('zillow', ZF), ('census+zillow', CF + ZF)]:
        best = None
        for name, f, a in CANDS:
            o = oof(f(a), dev[cols], yd, dev.cfips.values, GroupKFold(5)); auc = roc_auc_score(yd, o)
            if best is None or auc > best[0]: best = (auc, average_precision_score(yd, o), name, f, a)
        m = best[3](best[4]).fit(dev[cols], yd); scores[fs] = m.predict_proba(te[cols])[:, 1]; chosen[fs] = (best, m, cols)
        E['p_' + fs] = m.predict_proba(E[cols])[:, 1]
        allrows.append(dict(target=tgt, model=f'{fs}: {best[2]}({best[4]})', n_features=len(cols), cv_auc_dev=best[0], cv_ap_dev=best[1]))
    base = {'UDP vul_gent_18 flag': te.vul_gent_18, 'UDP hotmarket_18 flag': te.hotmarket_18,
            'UDP typology in OD/ARG/EOG/AdvG': te.typ.isin(['OD', 'ARG', 'EOG', 'AdvG']).astype(float),
            'UDP typology low-income group (LISD/OD/ARG/EOG)': (te.typ_group == 'low_income').astype(float),
            'persistence: own pre-2019 value': {'flip': te.z_flip_pre, 'apprec': te.z_apprec_pre, 'rent': te.z_rent_pre}[tgt]}
    for n_, s_ in base.items(): scores[n_] = np.asarray(s_.fillna(s_.median()), float); allrows.append(dict(target=tgt, model=n_))
    for row in allrows:
        if row['target'] != tgt: continue
        key = row['model'].split(':')[0] if row['model'].split(':')[0] in scores else row['model']; sc = scores[key]
        pk, rk = topk_metrics(yt, sc, k)
        row.update(test_n=len(te), test_pos=k, test_auc=roc_auc_score(yt, sc), test_ap=average_precision_score(yt, sc), prec_at_k=pk, recall_at_k=rk, spearman_cont=spearmanr(sc, te[tgt]).correlation)
    bs = np.random.RandomState(SEED); dif = []; ac = []; az = []
    for _ in range(2000):
        ix = bs.randint(0, len(te), len(te))
        if yt[ix].min() == yt[ix].max(): continue
        a1, a2 = roc_auc_score(yt[ix], scores['census'][ix]), roc_auc_score(yt[ix], scores['census+zillow'][ix]); dif.append(a2 - a1); ac.append(a1); az.append(a2)
    print('test AUC census %.3f [%.3f, %.3f] | census+zillow %.3f [%.3f, %.3f] | difference %.3f [%.3f, %.3f], share of bootstraps >0: %.3f' % (
        roc_auc_score(yt, scores['census']), *np.percentile(ac, [2.5, 97.5]), roc_auc_score(yt, scores['census+zillow']), *np.percentile(az, [2.5, 97.5]),
        roc_auc_score(yt, scores['census+zillow']) - roc_auc_score(yt, scores['census']), *np.percentile(dif, [2.5, 97.5]), np.mean(np.array(dif) > 0)))
    best, m, cols = chosen['census+zillow']
    pi = permutation_importance(m, te[cols], yt, scoring='roc_auc', n_repeats=20, random_state=SEED)
    imp = pd.DataFrame({'target': tgt, 'feature': cols, 'auc_drop': pi.importances_mean, 'sd': pi.importances_std}).sort_values('auc_drop', ascending=False); allimp.append(imp)
    print('top permutation importances (census+zillow model, test):'); print(imp.head(8).to_string(index=False))
    E['p_loco'] = oof(best[3](best[4]), E[cols], E.y.values, E.cfips.values, LeaveOneGroupOut())
    print('leave-one-county-out (all %d eligible tracts) AUC census+zillow: %.3f' % (len(E), roc_auc_score(E.y, E.p_loco)))
    allpred.append(E[['y', tgt, 'is_test', 'p_census', 'p_zillow', 'p_census+zillow', 'p_loco']].rename(columns={tgt: 'outcome'}).assign(target=tgt).reset_index())
res = pd.DataFrame(allrows); print('\nSPATIAL-BLOCK TEST RESULTS'); print(res.to_string(index=False))
res.to_csv(os.path.join(RES, 'e5_test_metrics.csv'), index=False)
pd.concat(allpred).to_csv(os.path.join(RES, 'e5_predictions.csv'), index=False); pd.concat(allimp).to_csv(os.path.join(RES, 'e5_permutation_importance.csv'), index=False)
