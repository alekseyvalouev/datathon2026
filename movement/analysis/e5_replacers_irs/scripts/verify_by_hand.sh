#!/usr/bin/env bash
# Hand check with awk on the raw CSVs (no pandas).
set -euo pipefail
cd "$(dirname "$0")/.."
R=../e1_composition/raw
echo "Santa Clara (06085), TY2021 (file 2122), domestic movers (row 97/000):"
awk -F, '$1+0==6 && $2+0==85 && $3+0==97 && $4+0==0 {printf "  in : n1=%d n2=%d agi=%d -> $%.0f/return, %.3f persons/return\n",$7,$8,$9,$9*1000/$7,$8/$7; a=$9/$7}' $R/countyinflow2122.csv
awk -F, '$1+0==6 && $2+0==85 && $3+0==97 && $4+0==0 {printf "  out: n1=%d n2=%d agi=%d -> $%.0f/return, %.3f persons/return\n",$7,$8,$9,$9*1000/$7,$8/$7}' $R/countyoutflow2122.csv
paste -d, <(awk -F, '$1+0==6 && $2+0==85 && $3+0==97 && $4+0==0 {print $9/$7}' $R/countyinflow2122.csv) \
          <(awk -F, '$1+0==6 && $2+0==85 && $3+0==97 && $4+0==0 {print $9/$7}' $R/countyoutflow2122.csv) | awk -F, '{printf "  replacement ratio (domestic, per return) = %.4f\n",$1/$2}'
python3 -I -c "
import pandas as pd; d=pd.read_csv('outputs/replacement_ratios.csv'); r=d[(d.unit=='Santa Clara')&(d.ty==2021)&(d.cat=='domestic')].iloc[0]
print(f'  pipeline: in \${r.mean_agi_in:.0f}, out \${r.mean_agi_out:.0f}, ratio {r.replacement_ratio_per_return:.4f}')"
echo "California TY2021 (gross file 2122inmigall.csv, all AGI classes): inflow returns under 26 + 26-34, share of inflow:"
awk -F, 'NR==1{for(i=1;i<=NF;i++) c[$i]=i} $1+0==6 && $4==0 {printf "  inflow n1 all=%d, <26=%d, 26-34=%d -> under-35 share %.4f\n",$c["inflow_n1_0"],$c["inflow_n1_1"],$c["inflow_n1_2"],($c["inflow_n1_1"]+$c["inflow_n1_2"])/$c["inflow_n1_0"]}' raw/2122inmigall.csv
python3 -I -c "
import pandas as pd; d=pd.read_csv('outputs/ca_in_vs_out_age_standardised.csv'); print(f'  pipeline: in_share_under35 = {d[d.ty==2021].in_share_under35.iloc[0]:.4f}')"
