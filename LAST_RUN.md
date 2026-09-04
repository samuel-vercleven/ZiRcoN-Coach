# LAST RUN

## Status
PASS

## Date
2026-09-04 19:00 local

## Command
`python main.py` through the project `.venv`; complete output captured in `logs/latest_full_run.txt`.

## Runtime
- completed successfully;
- completed successfully in 2.90s wall time (2.77s reported by the integration harness).

## Files changed
- New Phase 2I owner provenance, exhaustive inventory/contract, synthetic, precision, research-audit, full-audit, and top-foundation audit modules under `knowledge/`.
- `main.py`: Phase 2I owner-gate harness with all seven accepted Phase 2I production/validation files added to `FROZEN_FILES`.
- `AGENTS.md`, `PROJECT_STATE.md`, `DECISIONS.md`, `TODO.md`, and `LAST_RUN.md`: official Phase 2I v1 freeze record.
- No Phase 2G or Phase 2H production/validation file changed.
- Local `TODO.before_phase2i.md` is an untracked backup and is deliberately excluded from commits.

## Tests executed
- Phase 2I `py_compile`: PASS.
- Owner synthetic checks: PASS 10/10, including validated caster/target synthetic-only paths, non-executable uncertain statuses, exact signature/context mismatch, damage-target separation, and provenance.
- Owner precision checks: PASS 61/61 across 9 unrelated real context fixtures and 2 unresolved hashed-field fixtures.
- Owner public-source provenance audit: PASS, 5 records, 2 exact/patch-matched structural sources and 3 executable reverse-engineering cross-checks.
- Full real owner audit: PASS (accepted zero-gate baseline).
- Top Phase 2I foundation audit: PASS (accepted zero-gate baseline).
- Official-freeze Phase 2I validation stack: PASS.
- Final `python main.py`: PASS (2.77s harness runtime).
- FROZEN guard: PASS, 0 frozen modifications.
- `git diff --check`: PASS before the freeze commit and after the final push.

## Errors encountered
- One harness-ordering issue was detected before the final run: the Phase 2H command assignment initially overrode the new Phase 2I assignment. The Phase 2I block was moved after the retained Phase 2H definitions and the full run was repeated successfully.

## Main analyzer results
### Current analyzer
- Version: `champion_spell_stat_owner_semantics_phase2i_v1`; top audit `stat_scaling_formula_foundation_phase2i_v1`.
- Exact source: `Haru-Kay/LeagueDatamines@9245fd616059c6c658d1faa1029f0e18ea179154`, patch 26.16, Data Dragon 16.16.1/fr_FR.
- Structural/runtime cross-checks: `LeagueToolkit/lol-meta-classes@6222976776a9ca18fc63945930f22b8b03b30144`, `moonshadow565/calcrev@40f21c06e5cfc10750bb44b39d1f2d4e3567a6dc`, and `OsOmE1/leaguebuilder@1ae51c26bdde36e178174b98f7c65a52d55f10fa`.
- Owner baseline: 569/569 rows, preserving champion, slot, source path, calculation key, graph path, exact signature, frozen stat/formula results, root/parent/ancestor context, siblings, subparts, tooltip linkage, and provenance.
- Classes: 279 `StatByNamedDataValueCalculationPart`, 271 `StatByCoefficientCalculationPart`, 19 `StatBySubPartCalculationPart`.
- Eight exact signatures observed; 88 exact class/signature/context contracts audited.
- Contract statuses: 86 `OWNER_CONTEXT_DEPENDENT`, 2 `OWNER_UNRESOLVED`.
- Occurrence statuses: 567 `OWNER_CONTEXT_DEPENDENT`, 2 `OWNER_UNRESOLVED`; 0 validated caster, target, source-level, or other owner; 0 strongly supported, ambiguous, or contradicted.
- Exact tooltip calculation-token links: 461/569.
- Owner execution-eligible occurrences: 0/569.
- Gate blockers: 467 owner, 101 frozen stat ID, 1 frozen formula ID; snapshot/DataValue/subpart arithmetic was not reached.
- Frozen Phase 2H consumption remained 468 validated stat occurrences and 568 validated formula occurrences.
- Execution gate: accepted FAIL-CLOSED / zero eligible occurrences. Branch B was not started and no stat-scaling evaluator was created.
- Formula replay: the 1,443-calculation inventory was confirmed. Numeric replay was not run because the TODO requires at least one validated real owner contract before arithmetic.
- Frozen Phase 2G baseline remains 13 RESOLVED, 720 PARTIALLY_RESOLVED, 493 UNSUPPORTED_SIGNATURE, 217 UNSUPPORTED_CLASS. Phase 2I newly resolved formulas: 0 by gate; no replacement replay counts were fabricated.
- Representative real fixtures include Aatrox, Akshan, Diana, Malphite, Shyvana, Bel'Veth, Dr. Mundo, Viego, and Rammus; none is promoted to caster ownership from champion-spell membership.

## Suspicious findings
- Historical/current reverse-engineered implementations agree that stat lookup consumes a caller-provided unit/champion context, but they do not prove how every 26.16 client call site binds that context.
- Ekko W and Kindred W each carry an unknown `0xa8cb9c14` field in their stat-part signature; both remain fully owner-unresolved.

## Methodological concerns
- `UnitStatComponent` proves a stat-bearing runtime object, not that the object is the caster.
- LeagueBuilder's caller-supplied `Champion` is independent supporting implementation evidence, not authoritative client call-graph evidence.
- Damage target, tooltip subject, spell owner, and scaling-stat owner remain separate concepts.

## Remaining issues
- A patch-specific runtime/call-site proof is required before any concrete owner contract can be execution-eligible.
- AP remains outside execution because frozen Phase 2H did not promote raw `mStat=0`.
- No numeric stat-scaling replay exists for this zero-gate result; frozen Phase 2G counts are unchanged.

## Codex technical recommendation
- Preserve the accepted frozen zero-gate baseline. Any future stat arithmetic requires a new reviewed task and patch-specific evidence binding the evaluation unit to a concrete snapshot role for an exact real contract.

## Review request
NONE. Phase 2I v1 is FROZEN by project review; the accepted baseline promotes no owner semantic and starts no successor phase.
