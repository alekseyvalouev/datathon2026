import sys, os, site; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); site.addsitedir(site.getusersitepackages())  # needed because scripts run with python -I
"""E3 Fairness and failure analysis for the E2 backtest.
Subgroups use year-2000 characteristics. Two views: (a) held-out test tracts scored by the dev-trained model,
(b) all tracts scored by leave-one-county-out models. A tract is 'flagged' if it is in the top 19% of scores
(the regional base rate), so every subgroup faces the same regional threshold."""
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from common import *

d = load_udp(); pr = pd.read_csv(os.path.join(RES, 'e2_predictions.csv'), dtype={'GEOID': str})
d = d.merge(pr[['GEOID', 'is_test', 'p_logistic', 'p_calibrated', 'p_loco']], on='GEOID')
sg = subgroups(d, '00')
def table(mask, score, tag):
    y = d.lostli_18.values[mask]; s = d[score].values[mask]; g = sg[mask]
    thr = np.sort(s)[::-1][int(round(y.mean() * len(s))) - 1]; flag = s >= thr
    rows = [dict(view=tag, cut='ALL', group='all', n=len(y), pos=int(y.sum()), base_rate=y.mean(), auc=roc_auc_score(y, s),
                 flagged_share=flag.mean(), recall=flag[y == 1].mean(), precision=y[flag].mean(), fpr=flag[y == 0].mean())]
    for c in g.columns:
        for v, ix in g.groupby(c).indices.items():
            yy, ss, ff = y[ix], s[ix], flag[ix]
            rows.append(dict(view=tag, cut=c, group=v, n=len(ix), pos=int(yy.sum()), base_rate=yy.mean(),
                             auc=roc_auc_score(yy, ss) if 0 < yy.sum() < len(yy) else np.nan, flagged_share=ff.mean(),
                             recall=ff[yy == 1].mean() if yy.sum() else np.nan, precision=yy[ff].mean() if ff.sum() else np.nan,
                             fpr=ff[yy == 0].mean()))
    return pd.DataFrame(rows)
t = pd.concat([table(d.is_test.values, 'p_logistic', 'test'), table(np.ones(len(d), bool), 'p_loco', 'loco_all')])
for v in ['test', 'loco_all']: print('\n==', v); print(t[t.view == v].drop(columns='view').to_string(index=False))
t.to_csv(os.path.join(RES, 'e3_subgroups.csv'), index=False)

# failure tracts from the held-out test set
d['rank_pct'] = d.p_logistic.where(d.is_test).rank(pct=True); te = d[d.is_test].copy()
cols = ['GEOID', 'county_name', 'typ', 'p_logistic', 'p_calibrated', 'rank_pct', 'lostli_18', 'ch_all_li_count_00_18', 'all_li_count_00', 'per_all_li_00',
        'per_rent_00', 'per_nonwhite_00', 'per_col_00', 'real_hinc_00', 'real_mhval_00', 'rail', 'pop_00', 'pop_18', 'hh_00', 'hh_18', 'per_all_li_18', 'real_hinc_18']
fn = te[te.lostli_18 == 1].sort_values('p_logistic').head(6); fp = te[te.lostli_18 == 0].sort_values('p_logistic', ascending=False).head(6)
print('\nregional medians of the same columns:'); print(d[cols[3:]].median(numeric_only=True).to_frame().T.to_string())
print('\nWORST MISSES (lost low-income households, model scored low):'); print(fn[cols].to_string(index=False))
print('\nWORST FALSE ALARMS (model scored high, no loss):'); print(fp[cols].to_string(index=False))
pd.concat([fn.assign(kind='missed'), fp.assign(kind='false_alarm')])[['kind'] + cols].to_csv(os.path.join(RES, 'e3_failure_tracts.csv'), index=False)
# how sharp is the label? share of positives that are marginal losses
pos = d[d.lostli_18 == 1]; rel = -pos.ch_all_li_count_00_18 / pos.all_li_count_00
print('\nlabel sharpness: among %d positive tracts, median loss = %.0f low-income households (%.1f%% of 2000 count); share losing <5%%: %.3f' % (len(pos), -pos.ch_all_li_count_00_18.median(), 100 * rel.median(), (rel < .05).mean()))
big = (d.lostli_18 == 1) & (-d.ch_all_li_count_00_18 / d.all_li_count_00 >= .10)
print('AUC (LOCO) for clear losses (>=10%% of LI households lost, n=%d) vs non-losing tracts: %.3f' % (big.sum(), roc_auc_score(big[big | (d.lostli_18 == 0)], d.p_loco[big | (d.lostli_18 == 0)])))
