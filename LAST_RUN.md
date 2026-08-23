# LAST RUN

## Status
PASS

## Date
2026-08-23 02:43 local

## Command
`python main.py` through the project `.venv`; complete terminal output captured in `logs/latest_full_run.txt`.

## Runtime
- completed successfully;
- 325.65s reported by the development harness.

## Files changed
- `main.py`: Phase 2G v2 FROZEN guard expanded to all 43 approved production/validation files.
- `AGENTS.md`, `PROJECT_STATE.md`, `DECISIONS.md`, and `TODO.md`: official Phase 2G v2 freeze state and next-step boundary.
- `LAST_RUN.md`: this freeze report.
- No Phase 2G production or validation behavior changed.

## Tests executed
- Phase 2G compilation: PASS.
- All 12 synthetic modules: PASS.
- All 4 precision modules: PASS.
- Taxonomy, value, DataValue, stat-reference, evaluator, formula-runtime, snapshot, damage-evidence, damage-resolver, mitigation, cast-stat, representative, and top cross-layer real audits: PASS.
- Final `python main.py`: PASS.
- Phase 2G FROZEN guard: PASS; 43 Phase 2G files protected.
- `git diff --check`: PASS.

## Errors encountered
- none.

## Main analyzer results
### Current analyzer
- Phase 2G v2 is FROZEN by accepted project review.
- Pinned baseline: 173 champions, 692 primary slots, 1,443 calculations, 5,318 graph nodes, 25 classes, 109 signatures, Data Dragon 16.16.1/fr_FR, commit `9245fd616059c6c658d1faa1029f0e18ea179154`.
- Six exact executable signatures; 0 arithmetic evaluations under unregistered signatures.
- Evaluator: 13 RESOLVED, 720 PARTIALLY_RESOLVED, 493 UNSUPPORTED_SIGNATURE, 217 UNSUPPORTED_CLASS.
- Snapshots: 6,920 audited rows; 4,844 resolved and 2,076 partial.
- Damage evidence: 345 high confidence, 195 multiple candidates, 125 not identified, 27 insufficient; no high-confidence key-name-only case.
- Real raw/post-mitigation damage and composable totals: 0 / 0 / 0; accepted as the precise frozen coverage.
- Percentage penetration remains multiplicative: 30% + 20% = 44% through frozen Phase 2E.

## Suspicious findings
- none.

## Methodological concerns
- Stat enums/owners, conditional mechanics, ticks, alternate forms, excluded description-derived item facts, rune execution, and composability without `PROJECT_VALIDATED` evidence remain explicitly unresolved.

## Remaining issues
- No active implementation task. The next major task requires project review.

## Codex technical recommendation
- Preserve the frozen Phase 2G contracts and start no successor layer without an explicit reviewed TODO.

## Review request
NONE.
