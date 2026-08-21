# LAST RUN

## Status
PASS - Combat Resistance / Penetration Rules Foundation Phase 2E v1 accepted for freeze.

## Date
2026-08-22 local

## Validated code commit
b82d0e6f916a0d6d4d0b5857408246c940b5b2ce - Build combat resistance rules phase 2E

## Commands
- `python main.py`
- `python -m knowledge.combat_resistance_full_audit`
- `git diff --check`

## Runtime
- main harness completed successfully on the local Windows / .venv environment;
- reported main duration: 0.45s;
- full deterministic audit also completed independently with STATUS : PASS.

## Validation output
- Compilation Combat Resistance: PASS.
- Synthetic checks: PASS 12/12.
- Precision checks: PASS 10/10.
- Full audit: PASS.
- FROZEN guard: PASS.
- Final harness status: PASS.

## Full-audit baseline
- Version: `combat_resistance_phase2e_v1`.
- Resistance multiplier sweep: 141 cases.
- Armor matrix: 112 cases.
- Magic resistance matrix: 112 cases.
- Blocking issues: 0.
- Review items: 0.
- Resistance formula provenance: COMMUNITY_DOCUMENTED.
- Penetration order provenance: COMMUNITY_DOCUMENTED.
- Lethality 1:1 provenance: RIOT_OFFICIAL.

## Project review decision
- Phase 2E v1 is FROZEN.
- Current lethality is 1:1 flat armor penetration.
- Penetration cannot create negative resistance.
- Resistance reduction can create negative resistance.
- Bonus armor penetration requires a known base/bonus armor split.
- Missing split remains explicit unresolved state.
- Later modules should consume this generic rules layer rather than silently redefining it.

## Permanent limitations
- no champion spell execution;
- no item/rune effect execution;
- no crits;
- no damage amplification/reduction modifiers;
- no shields;
- no executes;
- no healing;
- no on-hit ordering;
- no temporary champion-state execution;
- no Burst/TTK;
- no recommendations;
- no ML.

## Files changed by freeze step
- AGENTS.md
- PROJECT_STATE.md
- DECISIONS.md
- TODO.md
- LAST_RUN.md
- main.py (FROZEN guard only)

## Next major task
Project review to define the next factual combat-input layer.
