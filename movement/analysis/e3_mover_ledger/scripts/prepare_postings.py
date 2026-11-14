"""Step 1: postings -> parsed salary, county/metro, occupation group. Writes outputs/postings_clean.parquet."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from load_indeed import load_df
from salary_parser import parse_series
from geo import assign
from occupations import classify_series

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "outputs")


def main():
    df = load_df()
    df = df.drop_duplicates("jobid")
    sal = parse_series(df.salary_formatted)
    geo = assign(df.location)
    df = pd.concat([df.reset_index(drop=True), sal.reset_index(drop=True).add_prefix("pay_"),
                    geo.reset_index(drop=True)], axis=1)
    df["occ"] = classify_series(df.job_title)
    df["has_salary_text"] = df.salary_formatted.notna() & (df.salary_formatted.str.strip() != "")
    df.to_parquet(os.path.join(OUT, "postings_clean.parquet"), index=False)
    print("rows", len(df), "parsed hourly", df.pay_mid.notna().sum())
    print(df.groupby("metro").size())
    print(pd.crosstab(df.occ, df.metro))
    return df


if __name__ == "__main__":
    main()
