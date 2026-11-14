import sys, os, site; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); site.addsitedir(site.getusersitepackages())  # needed because scripts run with python -I
"""E6 Fairness and failure analysis for the E5 forward test (census+zillow model).
Subgroups use 2018 characteristics. Views: spatial-block test tracts, and all eligible tracts scored by leave-one-county-out models.
Flagged = top share of scores equal to the positive rate in that view (one regional threshold for every subgroup)."""
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from common import *

P = pd.read_csv(os.path.join(RES, 'e5_predictions.csv'), dtype={'GEOID': str})
D = pd.read_csv(os.path.join(RES, 'e5_tract_table.csv'), dtype={'GEOID': str}).set_index('GEOID')
sgall = subgroups(D, '18'); sgall['typology_group'] = D.typ_group
out = []
for tgt in P.target.unique():
    Q = P[P.target == tgt].set_index('GEOID')
    for view, mask, sc in [('test', Q.is_test.values, 'p_census+zillow'), ('loco_all', np.ones(len(Q), bool), 'p_loco')]:
        q = Q[mask]; y = q.y.values; s = q[sc].values; g = sgall.loc[q.index]
        thr = np.sort(s)[::-1][int(round(y.mean() * len(s))) - 1]; flag = s >= thr
        rows = [('ALL', 'all', np.arange(len(q)))] + [(c, v, ix) for c in g.columns for v, ix in g.groupby(c).indices.items()]
        for c, v, ix in rows:
            yy, ss, ff = y[ix], s[ix], flag[ix]
            out.append(dict(target=tgt, view=view, cut=c, group=v, n=len(ix), pos=int(yy.sum()), base_rate=yy.mean(),
                            auc=roc_auc_score(yy, ss) if 0 < yy.sum() < len(yy) else np.nan, flagged_share=ff.mean(),
                            recall=ff[yy == 1].mean() if yy.sum() else np.nan, precision=yy[ff].mean() if ff.sum() else np.nan, fpr=ff[yy == 0].mean() if (yy == 0).any() else np.nan))
t = pd.DataFrame(out); t.to_csv(os.path.join(RES, 'e6_subgroups.csv'), index=False)
for tgt in t.target.unique():
    for v in ['test', 'loco_all']: print(f'\n== {tgt} / {v}'); print(t[(t.target == tgt) & (t.view == v)].drop(columns=['target', 'view']).to_string(index=False))
# failure tracts (flip target, spatial-block test set)
Q = P[(P.target == 'flip') & P.is_test].set_index('GEOID'); Q['score'] = Q['p_census+zillow']; Q['rank_pct'] = Q.score.rank(pct=True)
cols = ['county_name', 'city', 'typ', 'post_pairs', 'post_flips', 'z_flip_pre', 'z_log_pairs_pre', 'z_nb_flip_pre', 'per_col_18', 'per_rent_18', 'per_nonwhite_18', 'real_hinc_18', 'real_mhval_18', 'per_all_li_18', 'vul_gent_18']
Q = Q.join(D[cols])
show = ['county_name', 'city', 'typ', 'score', 'rank_pct', 'outcome', 'post_pairs', 'post_flips', 'z_flip_pre', 'z_nb_flip_pre', 'per_col_18', 'per_rent_18', 'per_nonwhite_18', 'real_hinc_18', 'real_mhval_18', 'vul_gent_18']
fn = Q[Q.y == 1].sort_values('score').head(5); fp = Q[Q.y == 0].sort_values('score', ascending=False).head(5)
print('\ntest medians:'); print(Q[show[3:]].median().to_frame().T.to_string())
print('\nFLIP TARGET, WORST MISSES (flip hot spot, scored low):'); print(fn[show].to_string())
print('\nFLIP TARGET, WORST FALSE ALARMS (scored high, not a hot spot):'); print(fp[show].to_string())
pd.concat([fn.assign(kind='missed'), fp.assign(kind='false_alarm')])[['kind'] + show].to_csv(os.path.join(RES, 'e6_failure_tracts.csv'))
# coverage fairness: which tracts have no outcome at all?
D['has_flip'] = D.flip.notna()
print('\noutcome coverage (share of tracts with a measurable flip outcome) by subgroup:')
for c in sgall.columns: print(D.groupby(sgall[c]).has_flip.agg(['mean', 'size']).round(3).T.to_string())
