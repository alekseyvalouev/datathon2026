#!/usr/bin/env bash
# Independent re-computation (awk on raw CSVs, no pandas) of San Francisco TY2020->TY2021
# (IRS files 2020-21 and 2021-22) and comparison with outputs/decomposition_annual.csv.
set -eu
cd "$(dirname "$0")/.."
get() { # file statefips_other countyfips_other -> "n1 agi" for SF (06/075) home rows
  awk -F, -v s="$2" -v c="$3" '$1+0==6 && $2+0==75 && $3+0==s && $4+0==c {print $7, $9}' "raw/$1"; }
read Ns20 As20 < <(get countyinflow2021.csv 6 75)
read Ni20 Ai20 < <(get countyinflow2021.csv 96 0)
read Ns21 As21 < <(get countyinflow2122.csv 6 75)
read Ni21 Ai21 < <(get countyinflow2122.csv 96 0)
read No21 Ao21 < <(get countyoutflow2122.csv 96 0)
echo "raw rows: TY2020 stay=$Ns20/$As20 in=$Ni20/$Ai20 | TY2021 stay=$Ns21/$As21 in=$Ni21/$Ai21 out=$No21/$Ao21 (returns/AGI \$k)"
awk -v a="$Ns20 $As20 $Ni20 $Ai20 $Ns21 $As21 $Ni21 $Ai21 $No21 $Ao21" 'BEGIN{split(a,v," ");
 M0=1000*(v[2]+v[4])/(v[1]+v[3]); Ms=1000*(v[6]+v[10])/(v[5]+v[9]); S=1000*v[6]/v[5]; M1=1000*(v[6]+v[8])/(v[5]+v[7]);
 printf "HAND  M_2020=%.1f M*_2021=%.1f S_2021=%.1f M_2021=%.1f | change=%.1f people=%.1f exit=%.1f entry=%.1f\n", M0,Ms,S,M1,M1-M0,Ms-M0,S-Ms,M1-S}'
awk -F, 'NR==1{for(i=1;i<=NF;i++)h[$i]=i} $1=="San Francisco" && $2==2020 {printf "PIPE  M_2020=%.1f M_2021=%.1f | change=%.1f people=%.1f exit=%.1f entry=%.1f\n",$h["mean_from"],$h["mean_to"],$h["change"],$h["people"],$h["exit"],$h["entry"]}' outputs/decomposition_annual.csv
