# ZiRcoN Coach — TODO

## Current task
Validate Recall / Reset Analyzer v21 on the real local history.

### Required checks
1. Confirm no traceback.
2. Report total reset/shop sequences.
3. Report voluntary reset proxy vs post-death shop counts.
4. Audit historical reference coverage and warmup.
5. Audit resets <=45s from a major objective.
6. Audit the 15 worst voluntary reentries.
7. Check whether current-Gold context produces misleading labels.
8. Inspect latest target-match classifications.
9. Check purchase clustering: no split of one shop visit, no merge of two separate visits.
10. Verify objective proximity remains context only.
11. Verify post-death shop is not presented as a voluntary recall mistake.

### Restrictions
Do not modify frozen analyzers unless this integration exposes a concrete correctness bug:
- Death v11
- Tempo/Pathing v17
- Objective v20

### If runtime fails
Fix only the actual runtime error first, then rerun the full Recall / Reset Analyzer.

### Deliverable
Update PROJECT_STATE.md with:
- runtime result;
- sequence counts;
- audit findings;
- bugs fixed;
- remaining methodological issues;
- whether v21 is freeze-ready.

Then rewrite TODO.md with the next concrete task.
