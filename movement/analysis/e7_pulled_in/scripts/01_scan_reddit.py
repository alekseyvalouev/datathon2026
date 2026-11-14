"""Step 1 (Reddit): stream the raw CSV, flatten posts + nested comments (same walk as E4),
and keep recall-oriented *arrival* candidates (first-person moves TO the Bay).
Writes data/arrival_pool.parquet. No usernames are selected."""
import json
import time

import duckdb
import pandas as pd

from e7common import DATA, RAW_REDDIT, arrival_tier, sub_group

MAX_CHARS = 6000


def walk(nodes, out):
    if not isinstance(nodes, list):
        return
    for n in nodes:
        if not isinstance(n, dict):
            continue
        txt = n.get("comment") or n.get("reply") or ""
        dt = n.get("date_of_comment") or n.get("date_of_reply") or ""
        if txt:
            out.append((txt[:MAX_CHARS], dt))
        walk(n.get("replies"), out)


def main():
    con = duckdb.connect()
    rel = con.execute(f"""select post_id, community_name, title, description, date_posted, comments
        from read_csv('{RAW_REDDIT}', header=true, all_varchar=true, max_line_size=30000000,
                      ignore_errors=true, parallel=false)""")
    pool, seen = [], set()
    n_posts = n_comments = 0
    t0 = time.time()
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
            t = arrival_tier(ptxt, grp)
            if t:
                pool.append(dict(item_id=post_id, kind="post", sub=sub, group=grp, date=date,
                                 text=ptxt[:8000], thread_title=title or "", tier=t))
            if comments and comments.startswith("["):
                try:
                    tree = json.loads(comments)
                except Exception:
                    continue
                flat = []
                walk(tree, flat)
                for i, (ctxt, cdt) in enumerate(flat):
                    n_comments += 1
                    t = arrival_tier(ctxt, grp)
                    if t:
                        pool.append(dict(item_id=f"{post_id}_c{i}", kind="comment", sub=sub,
                                         group=grp, date=cdt or date, text=ctxt,
                                         thread_title=title or "", tier=t))
        print(f"posts={n_posts:,} comments={n_comments:,} pool={len(pool):,} "
              f"{time.time()-t0:.0f}s", flush=True)
    df = pd.DataFrame(pool).drop_duplicates("text")
    df.to_parquet(DATA / "arrival_pool.parquet", index=False)
    json.dump(dict(n_posts=n_posts, n_comments=n_comments, n_pool=len(df),
                   by_tier=df.tier.value_counts().to_dict(),
                   by_group=df.group.value_counts().to_dict()),
              open(DATA / "arrival_pool_stats.json", "w"), indent=1)
    print(df.groupby(["group", "tier"]).size())


if __name__ == "__main__":
    main()
