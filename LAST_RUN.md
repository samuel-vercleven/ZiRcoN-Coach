# LAST RUN

## Status
PASS / REVIEW_REQUIRED FOR FREEZE

## Date
2026-08-22 23:38 local

## Command
`python main.py` through the project `.venv`; complete terminal output captured in `logs/latest_full_run.txt`.

## Runtime
- completed successfully;
- 314.31s reported by the development harness.

## Files changed
- Phase 2G formula taxonomy/evaluator and validation files;
- Phase 2G combat snapshot, damage evidence/resolution, mitigation, cast/runtime, representative, and top-audit files;
- `main.py`, `TODO.md`, `PROJECT_STATE.md`, `DECISIONS.md`, and `LAST_RUN.md`;
- no FROZEN production or validation file changed.

## Tests executed
- Phase 2G compilation: PASS.
- All 12 synthetic modules: PASS.
- All 4 precision modules: PASS.
- Taxonomy, value, DataValue, stat-reference, evaluator, formula-runtime, snapshot, damage-evidence, damage-resolver, mitigation, cast-stat, representative, and top cross-layer real audits: PASS.
- Final `python main.py`: PASS.
- FROZEN guard: PASS.
- `git diff --check`: PASS.

## Errors encountered
- The first top-audit attempt exposed a `None` spell-calculation table in a representative probe; the Phase 2G probe now treats the frozen source's explicit `null` as no calculations, then the audit passed.
- The first `git push origin main` attempt was rejected before network egress because the specific GitHub destination was not explicitly authorized. After explicit user authorization, the tested commits were pushed successfully to `origin/main`.

## Main analyzer results
### Current analyzer
- Version: `combat_formula_foundation_phase2g_v2`.
- Pinned invariants: 173 champions, 692 primary slots, 1,443 calculations, 5,318 graph nodes, 25 classes, 109 observed signatures, exact source commit `9245fd616059c6c658d1faa1029f0e18ea179154`, Data Dragon 16.16.1/fr_FR.
- Exact executable signatures: six (`Number`, `NamedDataValue`, `Sum`, `Product`, core `GameCalculation`, `NamedGameCalculation`); 0 arithmetic evaluations under an unregistered signature.
- DataValue references: 1,464 resolved, 361 not found, 4 unsupported shapes.
- Stat references: 885 occurrences / 16 IDs / 0 mapped; all 16 remain unresolved.
- Evaluator: 13 RESOLVED, 720 PARTIALLY_RESOLVED, 493 UNSUPPORTED_SIGNATURE, 217 UNSUPPORTED_CLASS.
- Snapshot audit: 6,920 rows; 4,844 fully resolved and 2,076 partial.
- Excluded/partial static facts: 692 each for description-derived ability haste, lethality, armor penetration %, and magic penetration %. Structured AD remains exact when AH is partial.
- Percentage penetration regression: sources 30% and 20% preserved separately, combined by frozen Phase 2E to 44%; 100 armor becomes 56 effective armor.
- Damage evidence over 692 spells: 345 high confidence, 195 multiple candidates, 125 not identified, 27 insufficient.
- Evidence tiers: 791 component-local structural links, 40 key-name-only candidates, 4 spell-level-type-only cases; no high-confidence key-name-only case.
- Raw damage: 0 resolved / 831 unresolved. Post-mitigation real damage: 0 resolved. Real composable totals: 0.
- Cast facts: base cooldown 680 resolved / 12 missing; adjusted cooldown 680 resolved / 12 unresolved; cost 568 resolved / 124 missing; range 661 resolved / 31 missing.
- Real probes passed for description-derived lethality/AH, exact penetration multiplicity, multi-signature classes, supported and unsupported signatures, a key-name-only damage candidate, and Rammus without champion-specific logic.

## Suspicious findings
- None that violate the hardened contracts.
- Coverage fell as expected: exact root formulas from 79 to 13 and real raw damage from 1 to 0.

## Methodological concerns
- Numeric stat enums and ownership still lack authoritative evidence, so all remain unresolved.
- Tooltip linkage identifies candidate components but does not establish formula arithmetic, activation, tick count, or composability.

## Remaining issues
- Project review must decide whether Phase 2G should be frozen.
- No known technical blocker remains in the requested pre-freeze hardening scope.

## Codex technical recommendation
- Review the stricter exact-signature, per-stat completeness, structural damage-evidence, and project-validated composability contracts before the freeze decision. Do not start a new phase from this run.

## Review request
REVIEW_REQUIRED for the Phase 2G freeze decision only.
