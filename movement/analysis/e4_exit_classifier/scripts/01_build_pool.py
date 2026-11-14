"""Step 1: stream the raw Reddit CSV, flatten posts + nested comment threads into
items, and keep a recall-oriented candidate pool of possible exit stories.

Outputs (no usernames are ever written):
  data/pool.parquet          candidate items (item_id, kind, sub, group, date, text, thread_title)
  data/denominators.csv      total items per month x group x kind (for normalising counts)
"""
import json
import sys
import time

import duckdb
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import DATA, RAW_CSV, in_pool, sub_group  # noqa: E402

MAX_COMMENT_CHARS = 6000


def walk_comments(nodes, post_id, out, depth=0):
    """Recursively flatten comments and replies -> (text, date)."""
    if not isinstance(nodes, list):
        return
    for n in nodes:
        if not isinstance(n, dict):
            continue
        txt = n.get("comment") or n.get("reply") or ""
        dt = n.get("date_of_comment") or n.get("date_of_reply") or ""
        if txt:
            out.append((txt[:MAX_COMMENT_CHARS], dt, depth))
        walk_comments(n.get("replies"), post_id, out, depth + 1)


def main():
    con = duckdb.connect()
    q = f"""
      select post_id, community_name, title, description, date_posted, comments
      from read_csv('{RAW_CSV}', header=true, all_varchar=true, max_line_size=30000000,
                    ignore_errors=true, parallel=false)
    """
    rel = con.execute(q)
    pool, denom = [], {}
    n_posts = n_comments = n_bad = 0
    t0 = time.time()
    seen = set()
    while True:
        batch = rel.fetchmany(2000)
        if not batch:
            break
        for post_id, sub, title, desc, date, comments in batch:
            if not post_id or post_id in seen:
                continue
            seen.add(post_id)
            grp = sub_group(sub)
            n_posts += 1
            ptxt = f"{title or ''}\n{desc or ''}".strip()
            m = (date or "")[:7]
            denom[(m, grp, "post")] = denom.get((m, grp, "post"), 0) + 1
            if in_pool(ptxt, grp):
                pool.append(dict(item_id=post_id, kind="post", sub=sub, group=grp,
                                 date=date, text=ptxt[:8000], thread_title=title or ""))
            if comments and comments.startswith("["):
                try:
                    tree = json.loads(comments)
                except Exception:
                    n_bad += 1
                    continue
                flat = []
                walk_comments(tree, post_id, flat)
                for i, (ctxt, cdt, depth) in enumerate(flat):
                    n_comments += 1
                    cm = (cdt or date or "")[:7]
                    denom[(cm, grp, "comment")] = denom.get((cm, grp, "comment"), 0) + 1
                    if in_pool(ctxt, grp):
                        pool.append(dict(item_id=f"{post_id}_c{i}", kind="comment", sub=sub,
                                         group=grp, date=cdt or date, text=ctxt,
                                         thread_title=title or ""))
        print(f"posts={n_posts:,} comments={n_comments:,} pool={len(pool):,} "
              f"bad_json={n_bad} {time.time()-t0:.0f}s", flush=True)
    df = pd.DataFrame(pool)
    df.to_parquet(DATA / "pool.parquet", index=False)
    d = pd.DataFrame([(k[0], k[1], k[2], v) for k, v in denom.items()],
                     columns=["month", "group", "kind", "n_items"])
    d.sort_values(["month", "group", "kind"]).to_csv(DATA / "denominators.csv", index=False)
    with open(DATA / "pool_stats.json", "w") as f:
        json.dump(dict(n_posts=n_posts, n_comments=n_comments, n_bad_json=n_bad,
                       n_pool=len(df),
                       pool_by_group_kind=df.groupby(["group", "kind"]).size()
                       .rename("n").reset_index().to_dict("records")), f, indent=1)
    print(df.groupby(["group", "kind"]).size())


if __name__ == "__main__":
    main()
