import sys, os, site; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); site.addsitedir(site.getusersitepackages())  # needed because scripts run with python -I
"""E2 Historical backtest: predict lostli_18 (tract lost low-income households 2000-2018)
from 1990/2000 census features only. Models vs UDP rule baselines.
Design: 25% stratified test split (never used for tuning) + county-held-out GroupKFold on the 75% dev set
for model/hyper-parameter selection + leave-one-county-out predictions for all tracts (used by E3)."""
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split, GroupKFold, LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.inspection import permutation_importance
from sklearn.base import clone
from common import *

d = load_udp()
d = d[d.lostli_18.notna()].reset_index(drop=True)
y = d.lostli_18.astype(int).values; X = d[FEATS00]; grp = d.cfips.values
print('n tracts', len(d), 'positives', y.sum(), 'base rate', round(y.mean(), 4), '| features', len(FEATS00))
print('missing feature cells:', int(X.isna().sum().sum()))
strat = d.cfips + '_' + d.lostli_18.astype(int).astype(str)
strat = strat.where(strat.map(strat.value_counts()) >= 4, 'rare')
dev, test = train_test_split(np.arange(len(d)), test_size=0.25, random_state=SEED, stratify=strat)
print('dev n', len(dev), 'pos', y[dev].sum(), '| test n', len(test), 'pos', y[test].sum())

def lr(C): return make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), LogisticRegression(C=C, max_iter=2000, class_weight='balanced'))
def rf(leaf, mf): return make_pipeline(SimpleImputer(strategy='median'), RandomForestClassifier(n_estimators=400, min_samples_leaf=leaf, max_features=mf, class_weight='balanced_subsample', random_state=SEED, n_jobs=-1))
def gb(lr_, depth): return HistGradientBoostingClassifier(learning_rate=lr_, max_depth=depth, max_iter=150, l2_regularization=1.0, random_state=SEED)
grid = {'logistic': [(lr, (C,)) for C in [0.01, 0.1, 1, 10]],
        'random_forest': [(rf, a) for a in [(5, 'sqrt'), (15, 'sqrt'), (30, 'sqrt'), (15, 0.5)]],
        'grad_boost': [(gb, a) for a in [(0.03, 2), (0.03, 3), (0.1, 2), (0.1, 3)]]}

def cv_oof(model, idx, splitter):
    oof = np.full(len(idx), np.nan)
    for tr, va in splitter.split(idx, y[idx], grp[idx]):
        m = clone(model).fit(X.iloc[idx[tr]], y[idx[tr]]); oof[va] = m.predict_proba(X.iloc[idx[va]])[:, 1]
    return oof

rows = []; best = {}
for name, cands in grid.items():
    for f, a in cands:
        oof = cv_oof(f(*a), dev, GroupKFold(5))
        r = dict(model=name, params=str(a), cv_auc=roc_auc_score(y[dev], oof), cv_ap=average_precision_score(y[dev], oof))
        rows.append(r)
        if name not in best or r['cv_auc'] > best[name][0]: best[name] = (r['cv_auc'], f, a)
cv = pd.DataFrame(rows); print('\ncounty-held-out GroupKFold(5) on dev set (tuning):'); print(cv.to_string(index=False))
cv.to_csv(os.path.join(RES, 'e2_cv_tuning.csv'), index=False)

# baselines: published UDP flags computed for 2000 and simple one-variable rules
base = {'UDP vul_gent_00 flag': d.vul_gent_00, 'UDP lostli_00 (lost LI hh 1990-2000)': d.lostli_00,
        'UDP hotmarket_00 flag': d.hotmarket_00, 'UDP gent_90_00 flag': d.gent_90_00,
        'UDP rule: vul_gent_00 + hotmarket_00': d.vul_gent_00 + d.hotmarket_00,
        'one variable: renter share 2000': d.per_rent_00}
k = int(y[test].sum()); k20 = int(round(0.2 * len(test)))
rng = np.random.RandomState(SEED)
def evalrow(name, s, cvauc=np.nan, cvap=np.nan, proba=False):
    s = np.asarray(pd.Series(s).fillna(pd.Series(s).median()), float); yt = y[test]; st = s[test]
    bs = [roc_auc_score(yt[b], st[b]) for b in (rng.randint(0, len(test), len(test)) for _ in range(1000)) if yt[b].min() != yt[b].max()]
    p1, r1 = topk_metrics(yt, st, k); p2, r2 = topk_metrics(yt, st, k20)
    return dict(model=name, cv_auc_dev=cvauc, cv_ap_dev=cvap, test_auc=roc_auc_score(yt, st), auc_lo=np.percentile(bs, 2.5), auc_hi=np.percentile(bs, 97.5),
                test_ap=average_precision_score(yt, st), prec_at_k=p1, recall_at_k=r1, prec_top20pct=p2, recall_top20pct=r2,
                brier=brier_score_loss(yt, st) if proba else np.nan)
out = []; preds = d[['GEOID', 'county_name', 'lostli_18']].copy(); preds['is_test'] = False; preds.loc[test, 'is_test'] = True
fitted = {}
for name, (cvauc, f, a) in best.items():
    m = f(*a).fit(X.iloc[dev], y[dev]); fitted[name] = m
    s = m.predict_proba(X)[:, 1]; preds['p_' + name] = s
    cvap = cv[(cv.model == name) & (cv.params == str(a))].cv_ap.iloc[0]
    out.append(evalrow(f'{name} {a}', s, cvauc, cvap, proba=True))
for name, s in base.items():
    sd = np.asarray(s.fillna(s.median()), float)
    out.append(evalrow(name, s, roc_auc_score(y[dev], sd[dev]), average_precision_score(y[dev], sd[dev])))
res = pd.DataFrame(out)
print(f'\nHELD-OUT TEST (n={len(test)}, positives={k}; k={k} for precision/recall@k, top20% = {k20} tracts); base rate AP = {y[test].mean():.3f}')
print(res.to_string(index=False)); res.to_csv(os.path.join(RES, 'e2_test_metrics.csv'), index=False)

# model picked on dev CV AUC only
pick = max(best, key=lambda n: best[n][0]); print('\nselected on dev CV AUC:', pick, best[pick][2])
sp = preds['p_' + pick].values
# calibration on test: balanced class weights inflate probabilities, so also report an isotonic-recalibrated version fit on dev OOF
from sklearn.isotonic import IsotonicRegression
oof = cv_oof(best[pick][1](*best[pick][2]), dev, GroupKFold(5))
iso = IsotonicRegression(out_of_bounds='clip').fit(oof, y[dev]); pc = iso.predict(sp)
preds['p_calibrated'] = pc
cal = pd.DataFrame({'y': y[test], 'raw': sp[test], 'cal': pc[test]})
cal['bin'] = pd.qcut(cal.raw, 5, labels=False)
ct = cal.groupby('bin').agg(n=('y', 'size'), mean_raw_score=('raw', 'mean'), mean_calibrated=('cal', 'mean'), observed_rate=('y', 'mean'))
print('\ncalibration on test by score quintile:'); print(ct.to_string())
print('Brier raw %.4f | calibrated %.4f | always-base-rate %.4f' % (brier_score_loss(y[test], sp[test]), brier_score_loss(y[test], pc[test]), brier_score_loss(y[test], np.full(len(test), y[dev].mean()))))
ct.to_csv(os.path.join(RES, 'e2_calibration.csv'))
pi = permutation_importance(fitted[pick], X.iloc[test], y[test], scoring='roc_auc', n_repeats=30, random_state=SEED)
imp = pd.DataFrame({'feature': FEATS00, 'auc_drop_mean': pi.importances_mean, 'auc_drop_sd': pi.importances_std}).sort_values('auc_drop_mean', ascending=False)
if pick == 'logistic': imp['std_coef'] = imp.feature.map(dict(zip(FEATS00, fitted[pick][-1].coef_[0])))
print('\npermutation importance on test (AUC drop):'); print(imp.to_string(index=False)); imp.to_csv(os.path.join(RES, 'e2_permutation_importance.csv'), index=False)
print('\nunivariate test AUC of each feature (direction-free):')
print(pd.Series({f: roc_auc_score(y[test], X[f].fillna(X[f].median()).values[test]) for f in FEATS00}).round(3).to_string())
# leave-one-county-out predictions for every tract with the selected model (spatial transfer check, used in E3)
loco = cv_oof(best[pick][1](*best[pick][2]), np.arange(len(d)), LeaveOneGroupOut()); preds['p_loco'] = loco
print('\nleave-one-county-out, all %d tracts: AUC %.3f AP %.3f' % (len(d), roc_auc_score(y, loco), average_precision_score(y, loco)))
print(pd.DataFrame([dict(county=COUNTY[c], n=(grp == c).sum(), pos=y[grp == c].sum(), auc=roc_auc_score(y[grp == c], loco[grp == c])) for c in sorted(COUNTY)]).to_string(index=False))
for b in ['vul_gent_00', 'lostli_00']: print('all-tract AUC baseline', b, round(roc_auc_score(y, d[b].fillna(0)), 3))
preds.to_csv(os.path.join(RES, 'e2_predictions.csv'), index=False)
