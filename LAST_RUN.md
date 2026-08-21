# LAST RUN

## Status
PASS - Level-Resolved Champion Stat Formula Foundation Phase 2D v4 accepted for freeze.

## Date
2026-08-22 local

## Validated code commit
2d54d7a89f7889ec272c70fde98f7d92fdcb6f1e - Freeze level-resolved champion stats phase 2D

## Commands
- `python main.py`
- `python -m knowledge.champion_level_stats_full_audit`

## Runtime
- main harness completed successfully on the local Windows / .venv environment;
- reported main duration: 68.29s;
- full catalog audit also completed independently with STATUS : PASS.

## Validation output
- Compilation Champion Level Stats: PASS.
- Synthetic checks: PASS 7/7.
- Precision checks: PASS 8/8.
- Full catalog audit: PASS.
- FROZEN guard: PASS.
- Final harness status: PASS.

## Full-catalog baseline
- Level stats version: `champion_level_stats_phase2d_v4`.
- Champion Knowledge version: `champion_knowledge_phase2b1_c_v1`.
- Data Dragon: 16.16.1.
- Locale: fr_FR.
- Champions: 173.
- Standard rows 1-18: 3114.
- Extended rows 19-20 audited for explicit non-extrapolation: 346.
- Attack Speed Ratio source: `PINNED_LEAGUE_DATAMINE_LIVE_26_16`.
- Attack ratio target/data patch: 16.16.
- Attack Speed Ratios: 173/173 resolved.
- Cross-source mismatches: 0.
- Standard non-AS statuses: 24912 RESOLVED_STANDARD_GROWTH, 6228 RESOLVED_FLAT.
- Attack Speed statuses: 2907 RESOLVED_ATTACK_SPEED_WITH_RATIO, 173 RESOLVED_LEVEL1_ATTACK_SPEED, 34 RESOLVED_ZERO_GROWTH_ATTACK_SPEED.
- Blocking issues: 0.
- Review items: 0.

## Project review decision
- Phase 2D v4 is FROZEN for standard levels 1-18.
- Attack Speed Ratio is sourced separately rather than inferred from Data Dragon base attack speed.
- The freeze source is immutable `Haru-Kay/LeagueDatamines` commit `9245fd616059c6c658d1faa1029f0e18ea179154`, named `LIVE 26.16 (#17)`.
- The 0.7025 / 0.0175 native growth expression is recorded as `VALIDATED_COMMUNITY_FORMULA_WITH_RIOT_ANCHORS`, not as a direct Riot Developer Portal coefficient publication.
- Native growth at levels 19-20 remains intentionally unresolved.

## Permanent limitations
- Levels 19-20 native growth: `UNRESOLVED_TOP_QUEST_LEVEL_FORMULA`.
- No item/rune stat application.
- No champion spell execution/formulas.
- No buffs/debuffs, penetration, shields, damage, Burst/TTK, recommendations, or ML.

## Files changed by freeze step
- PROJECT_STATE.md
- DECISIONS.md
- TODO.md
- LAST_RUN.md
- main.py (FROZEN guard only)

## Next major task
Project review to define the next factual combat-input / formula layer before Combat / Damage Engine work.
