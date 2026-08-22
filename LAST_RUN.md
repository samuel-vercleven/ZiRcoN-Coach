# LAST RUN

## Status
PASS / REVIEW_REQUIRED FOR FREEZE

## Date
2026-08-22 02:33 local

## Command
`python main.py` (project `.venv`, unbuffered; full output captured in `logs/latest_full_run.txt`)

## Runtime
- completed successfully;
- 76.17s reported by the final development harness;
- top real cross-layer audit: 69.61s.

## Files changed
- New Phase 2G taxonomy, rank/DataValue/stat-reference, evaluator, snapshot, formula-runtime, damage-evidence/resolution, mitigation, cast-stat, cache, representative-check, and top-audit modules under `knowledge/`.
- `main.py`, `.gitignore`, `AGENTS.md`, `PROJECT_STATE.md`, `TODO.md`, `DECISIONS.md`, and `LAST_RUN.md`.
- No frozen production or validation module changed.

## Tests executed
- Phase 2F freeze harness before Phase 2G: PASS; synthetic 10/10, precision 4/4, real source audit PASS, FROZEN guard PASS.
- Phase 2G compilation: PASS.
- Phase 2G synthetic checks: PASS 44/44 across 12 modules.
- Phase 2G precision checks: PASS 8/8 across 4 modules.
- Taxonomy, value, DataValue, stat reference, evaluator, formula runtime, cast metadata, representative, snapshot, damage evidence, damage resolver, and top cross-layer real audits: PASS.
- Final `python main.py`: PASS.
- Final FROZEN guard: PASS.
- `git diff --check`: PASS after final documentation updates.

Checkpoint commits created before the final documentation commit:
- `d549eca` Freeze champion spell calculation source phase 2F
- `fac8f22` Catalog champion spell calculation class semantics
- `92b1f87` Add spell value and DataValue resolution foundation
- `dfce8db` Map validated champion spell stat references
- `a380aca` Build conservative champion spell formula evaluator
- `4fc7c72` Build static combat stat snapshot foundation
- `08080ee` Connect spell formulas to static combat context
- `472b4e8` Classify champion spell damage evidence conservatively
- `64a66a1` Resolve validated champion spell damage components
- `a35cce0` Connect spell damage components to combat resistance
- `a83d94c` Add spell combat runtime and cast stat resolution
- `f399640` Harden pinned spell value and cache contracts
- `cecbf9e` Add representative and cross-layer combat audits

## Errors encountered
- Initial direct execution of four check files failed to import `knowledge` because package checks must run with `python -m`; rerun correctly and all passed.
- Real inspection exposed incorrect assumed field names (`mName/mValues`, `mSubparts`, and `mNamedGameCalculation`). Contracts were corrected to actual pinned shapes (`name/values`, `mPart1/mPart2`, and `mSpellCalculationKey`) before checkpoint commits.
- Cast cost arrays use a distinct pinned rank-1..6 shape; this was audited and separated from rank-0..6 arrays.

## Main analyzer results
### Current analyzer
- Version: `combat_formula_foundation_phase2g_v1`.
- Pinned invariants: 173 champions, 692 slots, 1,443 calculations, 5,318 graph nodes, 25 classes, exact commit `9245fd616059c6c658d1faa1029f0e18ea179154`, Data Dragon 16.16.1/fr_FR.
- Taxonomy: 109 signatures; occurrence statuses 1,677 executable, 561 partially validated, 1,226 structural container, 1,223 unresolved semantics.
- DataValue references: 1,464 resolved, 361 not found, 4 unsupported shape (1,829 total).
- Stat references: 885 occurrences, 16 IDs, 0 mapped, 16 unresolved.
- Evaluator: 79 RESOLVED, 1,037 PARTIALLY_RESOLVED, 110 UNSUPPORTED_SIGNATURE, 217 UNSUPPORTED_CLASS.
- Static snapshots: 4,844/4,844 resolved; six actual purchasable SR representative items discovered dynamically.
- Damage evidence across 692 spells: 283 high confidence, 235 multiple candidates, 135 no candidate, 39 insufficient evidence; 849 candidate components.
- Raw damage: 1 resolved, 848 unresolved. Post-mitigation: 1 resolved through frozen Phase 2E; 0 totals declared composable and 1 resolved set retained as not safely composable.
- Cast facts: cooldown 680 resolved / 12 missing; raw cost 568 resolved / 124 missing; range 661 resolved / 31 missing.
- Representative suite: 48 real champion/slot probes including Shyvana, Bel'Veth, Dr. Mundo, Viego, and Rammus; independent manual result 57.0 matched expected 57.0.

## Suspicious findings
- Pinned DataValue references include 361 exact names absent from their per-spell registry and 4 unsupported shapes; none are fuzzy-matched.
- Only one candidate damage component currently clears semantic, arithmetic, activation, and non-negative numeric requirements. This is low coverage but not a technical failure.

## Methodological concerns
- Numeric stat enums and ownership lack sufficient authoritative evidence; all 16 remain unresolved.
- Calculation-key plus frozen Champion Knowledge evidence identifies candidates, but conditional states, mixed/contextual damage, ticks, alternate forms, and component additivity remain unsupported unless explicitly proven.
- Description-derived item stats and all rune effects remain excluded from executable snapshots.

## Remaining issues
- Project review must decide whether the technically clean Phase 2G milestone should be frozen.
- Higher formula/damage coverage requires new evidence for class semantics and stat enum/owner mappings; thresholds or inference rules must not be weakened to obtain it.

## Codex technical recommendation
- Review the unresolved stat-reference evidence and the conservative damage-semantic boundary before any freeze decision. Do not start a new phase from this run.

## Review request
REVIEW_REQUIRED only for the Phase 2G freeze/product decision; no known technical failure remains.
