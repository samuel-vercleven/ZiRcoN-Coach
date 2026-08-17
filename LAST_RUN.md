# LAST RUN

## Status
REVIEW_REQUIRED

## Date
2026-08-18 00:00 local

## Command
python main.py

## Runtime
- completed
- approximate duration: 74 seconds
- raw terminal output saved to logs/latest_full_run.txt
- dedicated itemization audit saved to logs/itemization_v22_phase1c_audit.txt

## Files changed
- analysis/itemization_analyzer.py
- analysis/itemization_synthetic_checks.py
- main.py
- TODO.md
- PROJECT_STATE.md
- LAST_RUN.md

## Tests executed
- `.venv\Scripts\python.exe -m py_compile analysis\itemization_analyzer.py analysis\itemization_synthetic_checks.py main.py`
- `.venv\Scripts\python.exe -m analysis.itemization_synthetic_checks`
- `.venv\Scripts\python.exe -m analysis.itemization_analyzer`
- focused sell-warning verification for EUW1_7839112939
- `.venv\Scripts\python.exe main.py`

## Errors encountered
- No Python traceback or analyzer runtime failure.
- One production reconstruction bug was found and fixed: ITEM_UNDO after a completed-item purchase restored the purchased item removal but did not restore components consumed by that purchase.
- Regression added: undo of a component-consuming purchase now restores the actual consumed components, allowing later sells to be coherent.

## Main analyzer results
### Death Analyzer
- v11 not modified; remains FROZEN.

### Tempo / Pathing
- v17 not modified; remains FROZEN.

### Objective Analyzer
- v20 not modified; remains FROZEN.

### Recall / Reset Analyzer
- v21 not modified; remains FROZEN.

### Current analyzer
- Build / Itemization Analyzer v22 Phase 1C remains factual reconstruction only.
- No champion matchup, composition, build recommendation, item score, or ML logic was added.
- Processed 87 Jungle games and 4277 player item events.
- Event counts: 1536 purchases, 11 sells, 45 undo events, 2685 destroyed events.
- Final inventory validation: 86 EXACT, 1 EXACT_WITH_EXPLAINED_GRANT, 0 PARTIAL, 0 MISMATCH, 0 UNKNOWN.
- Observed exact final inventory rate: 98.9%; observed-or-explained rate: 100.0%.
- Magical Footwear remains separated: item 2422 is RUNE_GRANT / MAGICAL_FOOTWEAR with no Riot item transaction; derived timestamp remains DERIVED_INFERRED.
- Target EUW1_7951911875 remains EXACT.
- Target EUW1_7836627546 remains EXACT_WITH_EXPLAINED_GRANT.

## Suspicious findings
- ITEM_DESTROYED audit: 2685 total, 1085 confidently explained, 1600 remaining audit records.
- Evidence-based destroyed classifications: 834 CONFIRMED_OR_STRONG_TEMPORARY_STATE, 674 UNRESOLVED_TEMPORARY_POSSIBLE, 79 MISSED_TRANSFORMATION, 13 UNRESOLVED.
- Held-before-destroy cases: 515 total; 512 UNRESOLVED_TEMPORARY_POSSIBLE, 3 MISSED_TRANSFORMATION.
- Non-held cases: 1085 total; 834 confirmed/strong temporary, 162 unresolved temporary possible, 76 missed transformation, 13 unresolved.
- Viego is isolated as audit context only: 9 games, 1384 destroyed events, 1189 ambiguous events; evidence classifications are 674 UNRESOLVED_TEMPORARY_POSSIBLE, 588 CONFIRMED_OR_STRONG_TEMPORARY_STATE, 12 MISSED_TRANSFORMATION.
- No event was classified as LIKELY_REAL_REMOVAL.

## Methodological concerns
- REVIEW_REQUIRED: v22 Phase 1C now avoids circular destroyed-event proof, but freeze remains a project-review decision.
- Viego possession windows are not observable enough to reconstruct temporary inventories; unresolved Viego intervals must remain unreliable for coaching.
- 79 MISSED_TRANSFORMATION records are audit evidence only; production destroyed behavior was not changed because no concrete final/intermediate corruption demanded it.

## Remaining issues
- Intermediate contradiction audit still reports 78 component-consumed-after-ignored-destroy cases and 3 retained-after-missed-transformation cases.
- 13 destroyed records remain plain UNRESOLVED.
- Viego temporary possession inventory remains TEMPORARY_POSSESSION_INVENTORY_UNRELIABLE.

## Codex technical recommendation
- Submit v22 Phase 1C for review with the undo bugfix accepted.
- Do not freeze v22 or start recommendation logic until project review accepts the destroyed-event uncertainty policy.

## Review request
- REVIEW_REQUIRED because Phase 1C changes audit methodology and leaves explicit unresolved destroyed-event / Viego temporary-state limitations for project review.
