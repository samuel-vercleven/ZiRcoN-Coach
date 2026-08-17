# LAST RUN

## Status
REVIEW_REQUIRED

## Date
2026-08-17 18:04 local

## Command
.\.venv\Scripts\python.exe main.py

## Runtime
- completed
- approximate duration: 71s
- full main.py output saved to logs/latest_full_run.txt
- focused audit output saved to logs/reset_v21_threshold_independent_audit.txt

## Files changed
- analysis/reset_audit.py
- LAST_RUN.md
- PROJECT_STATE.md
- TODO.md

## Tests executed
- .\.venv\Scripts\python.exe -m compileall analysis\reset_audit.py
- .\.venv\Scripts\python.exe -m compileall analysis\reset_audit.py analysis\reset_analyzer.py analysis\reset_statistics.py main.py database
- .\.venv\Scripts\python.exe -m analysis.reset_audit
- .\.venv\Scripts\python.exe main.py

## Errors encountered
- Initial sandboxed compile could not access the venv's external Python target; the same compile was rerun with approved escalation and passed.
- No code/runtime errors after the audit changes.

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
- Production SHOP_CLUSTER_GAP_SECONDS remains 20.
- Full run completed with 891 shop/reset proxy sequences.
- Production split remains 509 VOLUNTARY_RESET_PROXY and 382 POST_DEATH_SHOP.
- Historical references remain: 339 CHAMPION_PHASE_ORIGIN_TIME, 282 PHASE_ORIGIN_TIME, 32 CHAMPION_PHASE_ORIGIN, 11 PHASE_ORIGIN, 227 WARMUP.
- Final threshold-independent audit inspected all 24 consecutive player shop-cluster pairs with 20s < gap <= 45s.
- Final audit classification: 13 SEPARATE_VISITS, 11 UNRESOLVED, 0 SAME_VISIT_CANDIDATE.
- Riot frame resolution: 13 pairs used the same Riot frame, 11 used distinct frames.
- Classification reasons: 11 same-frame UNRESOLVED, 6 player K/A/D between clusters, 3 major objective/building events on distinct frames, 3 observable OUTSIDE_BASE intermediate frames, 1 resource progression on distinct frames.
- Gap-bin summary after classification:
  - 20-25s: total 7, SAME 0, SEPARATE 1, UNRESOLVED 6
  - 25-30s: total 3, SAME 0, SEPARATE 1, UNRESOLVED 2
  - 30-35s: total 5, SAME 0, SEPARATE 4, UNRESOLVED 1
  - 35-40s: total 3, SAME 0, SEPARATE 2, UNRESOLVED 1
  - 40-45s: total 6, SAME 0, SEPARATE 5, UNRESOLVED 1
- Sensitivity unchanged: 20s = 891 total / 509 voluntary / 382 post-death; 30s = 881 / 509 / 372; 45s = 867 / 508 / 359.
- Scored/unscored sensitivity: 20s = 628 scored / 263 unscored; 30s = 617 / 264; 45s = 605 / 262.
- Tight voluntary objective sequences: 20s = 54, 30s = 54, 45s = 56.
- Target match EUW1_7951911875 remains 7 sequences: 4 voluntary, 3 post-death, 0 near-threshold pairs, 2 tight-pre-objective proxies.
- Objective <=5s technical check: 6/6 timing values are measured from cluster end, 6/6 objectives occur after the complete purchase cluster, 6/6 extraction/order checks passed.

## Suspicious findings
- No SAME_VISIT_CANDIDATE remains under the stricter threshold-independent audit.
- 11/24 pairs remain UNRESOLVED because both clusters map to the same Riot frame; zero XP/JCS/Gold delta on those rows was not used as evidence of one shop visit.
- The lower gap bins are mostly unresolved once gap is removed from classification, so the audit no longer provides independent support for choosing 30s solely from gap behavior.

## Methodological concerns
- SHOP_CLUSTER_GAP_SECONDS was not changed.
- Reentry weights, historical-reference minimums, validation thresholds, and FDR families were not changed.
- Near-objective reset remains context only. No reset is labeled a mistake because an objective follows.
- Any production threshold change or v21 freeze decision remains a project-review decision.

## Remaining issues
- Project review must decide whether the current 20s clustering threshold should stay, whether more audit evidence is needed, or whether a production threshold change is justified.
- If the production threshold changes, v21 validation should be rerun before any freeze decision.

## Codex technical recommendation
- Use the threshold-independent 24-pair audit, especially the 11 same-frame UNRESOLVED cases, as the review basis before changing production clustering.

## Review request
- REVIEW_REQUIRED because the final audit affects the interpretation of clustering-threshold readiness, but changing the production threshold or freezing v21 is reserved for project review.
