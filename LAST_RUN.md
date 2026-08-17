# LAST RUN

## Status
REVIEW_REQUIRED

## Date
2026-08-18 00:24 local

## Command
python main.py

## Runtime
- completed
- approximate duration: 75 seconds
- raw terminal output saved to logs/latest_full_run.txt
- dedicated itemization audit saved to logs/itemization_v22_phase1d_audit.txt

## Files changed
- analysis/itemization_analyzer.py
- analysis/itemization_synthetic_checks.py
- main.py
- TODO.md
- PROJECT_STATE.md
- LAST_RUN.md
- DECISIONS.md

## Tests executed
- `.venv\Scripts\python.exe -m py_compile analysis\itemization_analyzer.py analysis\itemization_synthetic_checks.py main.py`
- `.venv\Scripts\python.exe -m analysis.itemization_synthetic_checks`
- `.venv\Scripts\python.exe -m analysis.itemization_analyzer`
- `.venv\Scripts\python.exe main.py`

## Errors encountered
- Direct script mode for `analysis\itemization_synthetic_checks.py` could not import the package root; reran successfully with `-m analysis.itemization_synthetic_checks`.
- No Python traceback or analyzer runtime failure in the final audit or `main.py`.

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
- Build / Itemization Analyzer v22 Phase 1D remains factual reconstruction only.
- No champion matchup, composition, build recommendation, item score, or ML logic was added.
- Processed 87 Jungle games and 4277 player item events.
- Final inventory validation: 86 EXACT, 1 EXACT_WITH_EXPLAINED_GRANT, 0 PARTIAL, 0 MISMATCH, 0 UNKNOWN.
- Observed exact final inventory rate: 98.9%; observed-or-explained rate: 100.0%.
- Target EUW1_7951911875 remains EXACT.
- Magical Footwear target EUW1_7836627546 remains EXACT_WITH_EXPLAINED_GRANT; grant source is RUNE_GRANT with DERIVED_INFERRED timing.

## Suspicious findings
- 79 MISSED_TRANSFORMATION records are now grouped by root cause: 60 TEMPORARY_MECHANIC, 9 EVENT_ORDER_DUPLICATE, 8 VIEGO_TEMPORARY_POSSIBLE, 1 ALREADY_HANDLED_BY_PURCHASE_COMPONENT_CONSUMPTION, 1 REAL_MISSED_TRANSFORMATION.
- The 3 retained_after_missed_transformation cases are: 1 real non-Viego transformation interval, 2 Viego temporary-possible intervals.
- component_consumed_after_ignored_destroy dropped from 78 to 68 after excluding stale destroyed events followed by a clear reacquisition before consumption.
- Plain UNRESOLVED destroyed records dropped from 13 to 0; the inspected cases were consumable Riot representations, now classified as CONSUMABLE_DESTROYED_NOT_HELD_RIOT_REPRESENTATION.
- No LIKELY_REAL_REMOVAL evidence was found.

## Methodological concerns
- REVIEW_REQUIRED: one real non-Viego intermediate transformation remains marked unreliable rather than fabricated as a corrected inventory event.
- Reliability states were added for future consumers: RELIABLE, AMBIGUOUS_TEMPORARY_STATE, UNRESOLVED_TRANSFORMATION.
- Inventory reliability intervals: 509 AMBIGUOUS_TEMPORARY_STATE, 47 UNRESOLVED_TRANSFORMATION.
- Affected transaction states: 2635 RELIABLE, 1396 AMBIGUOUS_TEMPORARY_STATE, 246 UNRESOLVED_TRANSFORMATION.
- Viego uncertainty remains isolated through generic reliability intervals and does not alter normal champion reconstruction.

## Remaining issues
- Phase 1D is not frozen; freeze decision belongs to project review.
- Remaining ambiguous inventory periods are explicitly marked unreliable, not force-corrected.
- Viego temporary possession windows remain unobservable in Riot data.

## Codex technical recommendation
- Submit v22 Phase 1D for review as freeze candidate evidence.
- Do not start build recommendation logic until project review accepts the reliability semantics.

## Review request
- REVIEW_REQUIRED because v22 Phase 1D introduces durable reliability semantics and leaves explicit unreliable intervals for project review rather than inventing events.
