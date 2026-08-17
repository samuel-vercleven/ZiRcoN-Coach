# ZiRcoN Coach — TODO

## Current task
COMPLETED - Finalize and freeze Recall / Reset Analyzer v21.

Completion note:
- Completed by Codex on 2026-08-17.
- Recall / Reset Analyzer v21 is now documented as FROZEN.
- Production clustering remains SHOP_CLUSTER_GAP_SECONDS = 20.
- No Python code, frozen analyzer, threshold, weight, or validation rule was modified.
- No new major task is defined here.

## Project review decision

Recall / Reset Analyzer v21 is approved as FROZEN.

Production clustering remains:

SHOP_CLUSTER_GAP_SECONDS = 20

Do NOT change the threshold.

Reason:
- final threshold-independent audit found:
  - 13 SEPARATE_VISITS
  - 11 UNRESOLVED
  - 0 SAME_VISIT_CANDIDATE
- raising the threshold would merge some independently supported separate visits;
- unresolved same-frame Riot cases are insufficient evidence for merging;
- the conservative 20s threshold is therefore retained.

## Required changes

### PROJECT_STATE.md

Move:

Recall / Reset Analyzer v21

from IN DEVELOPMENT to FROZEN.

Document:
- 20s clustering threshold retained;
- threshold-independent audit results;
- Riot same-frame limitation;
- SHOP/RESET remains a proxy;
- current Gold remains exploratory only;
- objective proximity remains context only;
- Reentry Score measures post-reset production, not causal recall quality.

### DECISIONS.md

Add final freeze decision:

Recall / Reset Analyzer v21 — FROZEN

Reasons:
- voluntary vs post-death separation validated;
- historical-only Reentry Score;
- real-history validation passed;
- threshold-independent clustering audit completed;
- 20s threshold retained conservatively;
- no independent evidence justified increasing the threshold;
- objective-near reset audit found no extraction/order bug;
- target match remained stable.

Permanent limitations:
- Riot does not expose perfect recall lifecycle;
- purchase clusters are SHOP/RESET proxies;
- same-frame gaps may remain unresolved;
- current Gold is exploratory;
- objective proximity != player mistake;
- Reentry Score != causal recall quality.

### LAST_RUN.md

Record this as a project-review freeze decision.

No need to rerun full analysis unless code is modified.

### TODO.md

Mark the freeze finalization complete.

Do not invent the next major analyzer.

## Restrictions

Do NOT modify:
- reset_analyzer.py production logic;
- Death Analyzer v11;
- Tempo / Pathing v17;
- Objective Analyzer v20;
- thresholds;
- weights;
- validation methodology.

## Git

Commit and push the documentation freeze.

Suggested commit:

Freeze Recall Reset Analyzer v21
