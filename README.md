# datathon2026

Findings from several independent workstreams, to be synthesized into a single idea.

8th Annual Datathon for Social Good. Region: San Francisco Bay Area.

## Workstreams

| Folder | Question | Status |
|---|---|---|
| [`ai-labor-distribution/`](ai-labor-distribution/) | AI's distributional effect on the region: who captures AI-era gains (equity holders, engineers) versus who is exposed (support, clerical, contract roles)? Links job postings, WARN layoffs and occupation data to wages by race and county. | Complete — 6 experiments |

## Convention for adding a workstream

One folder per workstream, named for the question rather than the method. Inside it:

```
<workstream>/
  FINDINGS.md     synthesis — headline claims, positive AND negative, with the numbers inline
  memos/          per-experiment write-ups, including methods and limitations
  results/        tidy result tables; every number in FINDINGS.md should trace to one
  code/           scripts that run raw data -> reported results
```

Two things that make cross-workstream synthesis possible:

1. **Report nulls as prominently as positives.** A workstream that only reports what it confirmed cannot be combined with one that reports honestly — the synthesis will overstate. `ai-labor-distribution` documents 17 null results and they materially constrain what the combined story can claim.
2. **State the limits where the claim appears,** not in a footnote. Several results here are cross-sectional associations or accounting arithmetic that look causal if quoted without their caveat.

## Data

Bulk datasets are **not** committed. Each workstream's `code/` rebuilds its analysis tables from the original datathon pack plus any external sources, which its `FINDINGS.md` lists.

## Cross-workstream notes

Findings so far that other workstreams may need to reconcile with:

- **Displacement does not show up in the measurable record.** Bay Area WARN layoff intensity has no trend across 13 quarters (slope −0.17/quarter, p=0.66); there is no call-center relocation signal; worker AI-displacement discourse is flat to falling; the entry-level rung is not thinner in exposed occupations. Any claim that AI is visibly destroying Bay Area jobs needs to contend with this.
- **The job-postings data cannot support a time trend.** Posting dates are reconstructed from relative strings and 55.8% are censored; the crawl is also partly keyword-seeded toward tech titles. Anyone else using this Indeed extract should read `ai-labor-distribution/FINDINGS.md` §"data-quality traps" first.
- **Gains and assets flow to different groups.** White households hold 70.7% of Bay Area capital income while being under-represented in AI-positioned jobs; Asian workers are the mirror image. A single "winners" category will not fit the data.
