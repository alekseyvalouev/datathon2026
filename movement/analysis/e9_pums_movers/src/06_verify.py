"""Hand-verify one weighted estimate independently of the pandas pipeline.

Estimate: share of out-of-state Bay leavers (adults 18-64, household pop., ACS 2022-24) who own their home,
and its replicate-weight SE. Recomputed in DuckDB SQL straight from the slim PUMS extracts (persons + housing),
using hard-coded Bay MIGPUMA codes, and compared with outputs/leaver_vs_stayer_contrasts.csv.
"""
import os
import duckdb
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA, OUT = os.path.join(BASE, "data"), os.path.join(BASE, "outputs")
YEARS = [int(y) for y in os.environ.get("E9_YEARS", "2022,2023,2024").split(",")]
BAY_MIGPUMA = (100, 1300, 4100, 5500, 7500, 8100, 8500, 9500, 9700)  # Alameda ... Sonoma (2020 MIGPUMAs)


def main():
    con = duckdb.connect()
    p = ",".join(f"'{os.path.join(DATA, f'persons_{y}.parquet')}'" for y in YEARS)
    h = ",".join(f"'{os.path.join(DATA, f'housing_{y}.parquet')}'" for y in YEARS)
    reps = ", ".join(f"SUM(PWGTP{i} * own) / SUM(PWGTP{i}) AS r{i}" for i in range(1, 81))
    q = f"""
    WITH x AS (
      SELECT p.*, CASE WHEN h.TEN IN (1,2) THEN 1.0 ELSE 0.0 END AS own
      FROM read_parquet([{p}]) p JOIN read_parquet([{h}]) h USING (SERIALNO)
      WHERE p.MIG = 3 AND p.MIGSP = 6 AND p.MIGPUMA IN {BAY_MIGPUMA} AND p.ST <> 6
        AND p.AGEP BETWEEN 18 AND 64 AND h.TYPEHUGQ = 1)
    SELECT COUNT(*) AS n, SUM(PWGTP) AS wN, SUM(PWGTP * own) / SUM(PWGTP) AS est, {reps} FROM x
    """
    r = con.execute(q).df().iloc[0]
    est = r.est
    rr = np.array([r[f"r{i}"] for i in range(1, 81)])
    se = np.sqrt(4 / 80 * ((rr - est) ** 2).sum())
    c = pd.read_csv(os.path.join(OUT, "leaver_vs_stayer_contrasts.csv"))
    pipe = c.query("sample=='all' and treatment=='left_ca' and outcome=='own'").iloc[0]
    lines = [
        "Hand verification: homeownership share among out-of-state Bay leavers (18-64, household pop.)",
        f"  DuckDB SQL from raw extracts: n={int(r.n)}, weighted N={r.wN:,.0f}, share={est:.4f}, replicate SE={se:.4f}",
        f"  Pipeline (03_estimate.py):    n={int(pipe.n_treat_nonmissing)}, share={pipe.leaver_mean:.4f}, SE={pipe.leaver_se:.4f}",
        f"  Match: {abs(est - pipe.leaver_mean) < 1e-9 and int(r.n) == int(pipe.n_treat_nonmissing)}",
        "  Formula: share = sum(PWGTP*own)/sum(PWGTP); SE = sqrt(4/80 * sum_r (share_r - share)^2), r = PWGTP1..80",
    ]
    txt = "\n".join(lines)
    print(txt)
    open(os.path.join(OUT, "hand_verification.txt"), "w").write(txt + "\n")


if __name__ == "__main__":
    main()
