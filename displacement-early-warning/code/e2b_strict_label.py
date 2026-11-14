import sys, os, site; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); site.addsitedir(site.getusersitepackages())
"""E2b Label robustness. The base label lostli_18 flags any net loss of low-income households 2000-2018,
even a loss of one household. Two stricter labels are tested with the same 25% test split and the same features:
  strict10 : lost at least 10% of the tract's year-2000 low-income households
  share5   : the low-income share of households fell by at least 5 percentage points (count-free)
Logistic regression (C chosen by county-held-out CV on dev only) vs the UDP vul_gent_00 flag."""
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split, GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.base import clone
from common import *
d = load_udp(); d = d[d.lostli_18.notna()].reset_index(drop=True)
X = d[FEATS00]; grp = d.cfips.values
strat = d.cfips + '_' + d.lostli_18.astype(int).astype(str)
strat = strat.where(strat.map(strat.value_counts()) >= 4, 'rare')
dev, test = train_test_split(np.arange(len(d)), test_size=0.25, random_state=SEED, stratify=strat)  # identical to E2
pct = d.ch_all_li_count_00_18 / d.all_li_count_00.replace(0, np.nan)
labels = {'base: any loss (lostli_18)': d.lostli_18.astype(int).values,
          'strict10: lost >=10% of low-income households': (pct <= -0.10).fillna(False).astype(int).values,
          'share5: low-income share fell >=5 points': ((d.per_all_li_18 - d.per_all_li_00) <= -0.05).fillna(False).astype(int).values}
def lr(C): return make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), LogisticRegression(C=C, max_iter=2000, class_weight='balanced'))
rng = np.random.RandomState(SEED); rows = []; preds = pd.DataFrame({'GEOID': d.GEOID, 'is_test': np.isin(np.arange(len(d)), test)})
for name, y in labels.items():
    best = None
    for C in [0.01, 0.1, 1, 10]:
        oof = np.full(len(dev), np.nan)
        for tr, va in GroupKFold(5).split(dev, y[dev], grp[dev]):
            oof[va] = clone(lr(C)).fit(X.iloc[dev[tr]], y[dev[tr]]).predict_proba(X.iloc[dev[va]])[:, 1]
        a = roc_auc_score(y[dev], oof)
        if best is None or a > best[0]: best = (a, C)
    m = lr(best[1]).fit(X.iloc[dev], y[dev]); s = m.predict_proba(X.iloc[test])[:, 1]; yt = y[test]
    bs = [roc_auc_score(yt[i], s[i]) for i in (rng.randint(0, len(yt), len(yt)) for _ in range(1000)) if yt[i].min() != yt[i].max()]
    k = int(yt.sum()); pk, rk = topk_metrics(yt, s, k)
    base = d.vul_gent_00.values[test]
    rows.append(dict(label=name, positives_all=int(y.sum()), base_rate=y.mean(), C=best[1], cv_auc_dev=best[0], test_n=len(test), test_pos=int(yt.sum()),
                     test_auc=roc_auc_score(yt, s), auc_lo=np.percentile(bs, 2.5), auc_hi=np.percentile(bs, 97.5), test_ap=average_precision_score(yt, s),
                     recall_at_k=rk, udp_flag_auc=roc_auc_score(yt, base), udp_flag_ap=average_precision_score(yt, base)))
    preds['y_' + name.split(':')[0]] = y
out = pd.DataFrame(rows); print(out.to_string(index=False)); out.to_csv(os.path.join(RES, 'e2b_label_robustness.csv'), index=False)
preds.to_csv(os.path.join(RES, 'e2b_labels.csv'), index=False)
print('agreement of labels:'); print(pd.crosstab(preds['y_base'], preds['y_strict10'])); print(pd.crosstab(preds['y_base'], preds['y_share5']))
