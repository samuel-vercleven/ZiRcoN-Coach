# ZiRcoN Coach — TODO

## Current task
COMPLETED - Final threshold-independent clustering audit for Recall / Reset Analyzer v21.

Completion note:
- Completed by Codex on 2026-08-17.
- Production reset clustering threshold remains unchanged at 20s.
- No frozen analyzer was modified.
- Final result is REVIEW_REQUIRED for project review; no new major task is defined here.

## Why
The previous pre-freeze audit found:

- 24 shop-cluster gaps with 20s < gap <=45s
- 10 LIKELY_SAME_SHOP_VISIT
- 14 LIKELY_SEPARATE_VISITS
- 30s sensitivity merges exactly 10 pairs
- 45s sensitivity merges all 24

However, the audit heuristic currently contains:

`if gap <= 30: LIKELY_SAME_SHOP_VISIT`

This makes the evidence for choosing 30s partially circular.

The goal of this task is to remove that circularity before the final freeze decision.

## Part A — Make the audit classification threshold-independent

Modify ONLY the audit logic in `analysis/reset_audit.py`.

Do NOT modify production `reset_analyzer.py` yet.

The SAME / SEPARATE classification must NOT use:
- 20s
- 30s
- 45s
- any other gap cutoff

The gap must be descriptive evidence only.

Use observable evidence instead.

### Strong evidence for SEPARATE_VISITS

Examples:
- player kill between clusters
- player assist between clusters
- player death between clusters
- major objective activity involving observable game progression
- positive XP gain between genuinely distinct observable frames
- positive Jungle CS gain between genuinely distinct observable frames
- meaningful Gold gain consistent with gameplay between genuinely distinct frames
- clear movement/state progression when the available Riot frames actually distinguish the two moments

### SAME_VISIT_CANDIDATE

Use only when:
- there is no observable player gameplay activity between clusters;
- no observable resource progression supports a separate visit;
- available frame evidence is compatible with staying in the same shop/base visit.

This is still a candidate, not ground truth.

### UNRESOLVED

Use when Riot frame granularity cannot distinguish the two possibilities.

Do NOT turn missing evidence into evidence that the visits are the same.

## Part B — Explicitly audit frame resolution

For all 24 pairs report:

- gap seconds
- frame timestamp used at cluster 1 end
- frame timestamp used at cluster 2 start
- whether both states come from the SAME Riot frame
- XP delta
- Jungle CS delta
- total Gold delta
- position delta
- K/A/D between
- objective/event evidence between
- final threshold-independent classification

This is critical because two clusters 20–45s apart may map to the same ~1-minute Riot frame.

If both sides use the same frame, resource delta = 0 must NOT be treated as strong evidence of one shop visit.

## Part C — Results by gap, without using gap for classification

After classification, only then summarize results by:

- 20–25s
- 25–30s
- 30–35s
- 35–40s
- 40–45s

Report for each bin:
- SAME_VISIT_CANDIDATE
- SEPARATE_VISITS
- UNRESOLVED

This allows project review to see whether a natural threshold emerges from independent evidence.

## Part D — Sensitivity

Keep the existing audit-only 20 / 30 / 45 sensitivity comparison.

Report:
- total sequences
- voluntary
- post-death
- scored/unscored
- tight-objective sequences
- target match split

Do not change production threshold.

## Part E — Objective <=5s cases

Review the 6 voluntary sequences whose next objective occurs <=5s later.

Determine only whether:
- objective timing is correctly measured from cluster end;
- objective occurs after the complete purchase cluster;
- there is any extraction/order bug.

If timing is technically correct, keep them as valid CONTEXT.

Do not call them player mistakes.

## Restrictions

Do NOT modify:
- Death Analyzer v11
- Jungle Tempo / Pathing v17
- Objective Analyzer v20
- production SHOP_CLUSTER_GAP_SECONDS
- Reentry Score weights
- historical reference minimums
- validation thresholds
- FDR families

This task is audit-only.

## Required output

Run:
- compile checks
- focused reset audit
- python main.py if required for regression verification

Update:
- LAST_RUN.md
- PROJECT_STATE.md
- TODO.md → completed only

LAST_RUN must include the final threshold-independent 24-pair summary.

Finish with REVIEW_REQUIRED.

Do not freeze v21 and do not change the production threshold.
