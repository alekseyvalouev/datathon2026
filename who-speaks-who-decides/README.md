# who-speaks-who-decides

Who comments on housing projects at the San Francisco Planning Commission, and does it change what happens to them? Synthesis is in [`FINDINGS.md`](FINDINGS.md).

## Layout

```
FINDINGS.md   headline claims, positive and negative, with numbers and limits inline
memos/        per-topic write-ups, project examples, corrections log, datathon context
memos/research/  outside-research notes (data sources, law timeline, literature, commission structure)
results/      text tables printed by each script; every number in FINDINGS.md traces to one
code/         scripts that run raw data -> reported results; code/superseded/ holds earlier versions kept for the record
```

## Reproduce

1. Clone the public-comment dataset: `git clone https://github.com/alexandersahn/sf-planning-public-comment-data` (data CC BY 4.0; cite Sahn 2025, *AJPS*).
2. Put the Zillow part files from the datathon pack in one folder. This workstream had `Zillow_part1.csv` and `zillow_part3.csv` only; with part 2 added, Zillow-based numbers will change.
3. From this folder: `code/run_all.sh <path to sahn repo>/public <zillow folder>`

Needs Python 3 with pandas, numpy, scikit-learn and scipy. Takes about seven minutes. Intermediate tables go to `work/` (ignored by git). Bootstrap seeds are fixed.

## Privacy

- Result tables contain no commenter names. Scripts print raw comment samples only when `SHOW_TEXT=1` is set; do not commit that output.
- `14_examples.py` prints agenda text that includes staff contact details; its output is not committed. `memos/05_project_examples.md` is the curated version.
- Commissioners appear by surname in `results/11_…` and `results/13_…` as public officials casting recorded votes. Two commissioners named Johnson are merged by the name parser.
- Project addresses come from public agendas.

## Status

Exploratory. No notebook, slide deck or video yet. `memos/06_corrections_log.md` lists what was wrong along the way and what has not been rerun.
