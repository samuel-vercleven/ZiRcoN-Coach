# LAST RUN

## Status
REVIEW_REQUIRED

## Date
2026-08-17 17:38 local

## Command
.\.venv\Scripts\python.exe main.py

## Runtime
- completed
- approximate duration: 78s
- full main.py output saved to logs/latest_full_run.txt
- detailed audit output saved to logs/reset_v21_pre_freeze_audit.txt

## Files changed
- .gitignore
- analysis/reset_audit.py
- LAST_RUN.md
- PROJECT_STATE.md
- TODO.md

## Tests executed
- .\.venv\Scripts\python.exe -m compileall analysis\reset_audit.py analysis\reset_analyzer.py analysis\reset_statistics.py main.py database
- .\.venv\Scripts\python.exe -m compileall analysis\reset_audit.py
- .\.venv\Scripts\python.exe -m analysis.reset_audit
- .\.venv\Scripts\python.exe main.py

## Errors encountered
- none

## Main analyzer results
### Death Analyzer
- v11 not modified.
- Full run still built 491 exploitable death rows.

### Tempo / Pathing
- v17 not modified.
- Full run still built 2,604 tempo intervals.

### Objective Analyzer
- v20 not modified.
- Full run still built 628 objective sequences.

### Current analyzer
- Recall / Reset Analyzer v21 production logic was not modified.
- Full run completed with 891 shop/reset proxy sequences.
- Production split remains 509 VOLUNTARY_RESET_PROXY and 382 POST_DEATH_SHOP.
- Historical reference coverage remains: 339 CHAMPION_PHASE_ORIGIN_TIME, 282 PHASE_ORIGIN_TIME, 227 WARMUP, 32 CHAMPION_PHASE_ORIGIN, 11 PHASE_ORIGIN.
- Pre-freeze audit inspected all 24 consecutive player shop-cluster pairs with 20s < gap <= 45s.
- Audit-only classification: 10 LIKELY_SAME_SHOP_VISIT, 14 LIKELY_SEPARATE_VISITS, 0 AMBIGUOUS.
- Gap bins: 20-25s = 7, 25-30s = 3, 30-35s = 5, 35-40s = 3, 40-45s = 6.
- Champion distribution: Shyvana 17, Belveth 4, Viego 3.
- Phase distribution: LATE 9, MID 4, EARLY_MID 4, MID_LATE 4, EARLY_CLEAR 3.
- Sensitivity: 30s threshold would merge 10 sequences; 45s threshold would merge 24 sequences.
- Sensitivity counts: 20s = 891 total / 509 voluntary / 382 post-death; 30s = 881 / 509 / 372; 45s = 867 / 508 / 359.
- Game-level medians changed little under sensitivity, but post-death sequence volume changed materially enough for review.
- All 54 voluntary tight-pre-objective resets were audited.
- Tight voluntary summary: DRAGON 31, GRUBS 11, BARON 6, HERALD 5, ELDER 1; ENEMY 33, ALLY 20, UNKNOWN 1.
- Tight time-to-objective: 0-15s = 12, 15-30s = 17, 30-45s = 25.
- Tight reset checks: 0 misclassified post-death candidates, 0 split-purchase-cluster candidates, 6 objective-timing artifact candidates with next objective <=5s.
- Target match EUW1_7951911875 confirmed: 7 sequences, 4 voluntary, 3 post-death, 0 near-threshold split candidates, 2 tight-pre-objective proxies.

## Suspicious findings
- The audit found 10 near-threshold pairs likely to be one same shop visit under the audit-only heuristic.
- Those 10 are mostly post-death shop pairs with no observable player XP/JCS/Gold gain between clusters and no player K/A/D evidence between clusters.
- Raising the threshold to 30s would merge exactly those 10 near-threshold pairs; 45s would merge all 24 audited pairs.
- Six voluntary tight-objective resets occur <=5s before the objective event, so objective timing should be reviewed as possible event-order/proxy artifact before interpretation.

## Methodological concerns
- SHOP_CLUSTER_GAP_SECONDS was not changed.
- Reentry weights, historical-reference minimums, validation thresholds, and FDR families were not changed.
- Near-objective reset remains context only. No reset is labeled a mistake because an objective follows.
- Audit-only classifications are not production labels and should not be used for coaching without project review.

## Remaining issues
- Project review must decide whether the 20s clustering threshold should stay or whether a threshold change is methodologically justified.
- If the threshold changes, v21 validation should be rerun and reviewed before any freeze decision.
- Raw logs are intentionally ignored by Git after fixing .gitignore; they remain available locally in logs/.

## Codex technical recommendation
- Review the 10 LIKELY_SAME_SHOP_VISIT near-threshold pairs and the 6 <=5s objective-timing artifact candidates before changing any production threshold.

## Review request
- REVIEW_REQUIRED because the audit suggests the current 20s shop-clustering threshold may split some real shop visits, but changing it is a methodology/project-review decision.
