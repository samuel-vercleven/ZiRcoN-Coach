# LAST RUN

## Status
PASS

## Date
2026-08-31 17:10 local

## Command
`python main.py` through the project `.venv`; complete terminal output captured in `logs/latest_full_run.txt`.

## Runtime
- completed successfully;
- 2.02s reported by the official freeze validation run.

## Files changed
- New Phase 2H provenance, inventory, semantic mapping/composition, synthetic, precision, research, inventory-audit, and full-audit modules under `knowledge/`.
- `main.py`: Phase 2H current harness; Phase 2G and all earlier layers remain protected, and all seven Phase 2H production/validation files now join the FROZEN guard.
- `AGENTS.md`, `PROJECT_STATE.md`, `DECISIONS.md`, `TODO.md`, and `LAST_RUN.md`: official Phase 2H v1 freeze state.
- Checkpoint commits already created: `1ba23ed` (inventory) and `988f190` (validated semantics); the final audit/documentation commit contains this report.
- No FROZEN production or validation file changed.

## Tests executed
- Phase 2H `py_compile`: PASS.
- Synthetic checks: PASS 21/21.
- Precision checks: PASS 31/31 across 6 stat fixtures and 4 formula fixtures.
- Public-source provenance audit: PASS.
- Exact pinned inventory audit: PASS.
- Full real stat-semantics audit: PASS (its historical `REVIEW_REQUIRED FOR FREEZE` suffix is preserved by the now-frozen validation module; project review accepted the freeze).
- Final `python main.py`: PASS.
- FROZEN guard: PASS, 0 frozen modifications.
- `git diff --check`: PASS.

## Errors encountered
- none in the final run.

## Main analyzer results
### Current analyzer
- Version: `champion_spell_stat_semantics_phase2h_v1`.
- Exact source: `Haru-Kay/LeagueDatamines@9245fd616059c6c658d1faa1029f0e18ea179154`, patch 26.16; Data Dragon 16.16.1/fr_FR.
- Other recorded sources: `LeagueToolkit/lol-meta-classes@6222976776a9ca18fc63945930f22b8b03b30144`, `moonshadow565/calcrev@40f21c06e5cfc10750bb44b39d1f2d4e3567a6dc`, `CommunityDragon/CDTB@b52d04fa986a1620f31bd3ca8f9dbbea169b1641`, `OsOmE1/leaguebuilder@1ae51c26bdde36e178174b98f7c65a52d55f10fa`, HextechDocs, and official Riot patch notes 9.2, 9.24, 26.1, and 26.2. Exact URLs and limitations are in the sources module.
- Inventory: 885 occurrences = 569 `mStat` + 316 explicit `mStatFormula`; 16 explicit IDs `[1, 2, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 18, 29, 31]`.
- Effective formula values: `[0, 1, 2]`; explicit serialized values `[1, 2]`.
- Validated stats: `{1: ARMOR, 2: ATTACK_DAMAGE, 12: HEALTH}`; execution-eligible coverage 468/569 (82.25%).
- Strongly supported/non-executable: IDs `[4, 6, 7, 8, 9, 10, 18, 29, 31]`.
- Ambiguous/contradicted stat IDs: none; unresolved `[13, 14, 15, 16]`.
- Validated formulas: `{0: TOTAL_STAT, 2: BONUS_STAT}`, covering 568/569 (99.82%); formula 1 is contradicted and excluded.
- Ownership: caster 0, target 0, source-level 0, context-dependent 0, unresolved 569.
- Composition: 0 real fully resolved references; 467 reach the owner gate, 101 stop on stat ID, and 1 stops on formula ID. Six snapshot fields are structurally composable only after future owner proof.
- AbilityResource: 8 separate class nodes, one explicit raw ID 4, all `RESOURCE_ENUM_RESEARCH_ONLY`.
- Phase 2H v1 is FROZEN by accepted project review; all seven Phase 2H files are guarded and Phase 2G frozen behavior and counts remain unchanged.

## Suspicious findings
- Public formula tables disagree: historical HextechDocs labels formula 2 as total, while exact pinned Akshan/Diana fixtures and current leaguebuilder support bonus. Formula 1 has incompatible bonus/total claims and only one non-discriminating pinned occurrence.
- Four pinned `mStat` IDs (13-16) are absent from the exact pinned `GlobalStatsUIData` table; no positional inference was admitted.

## Methodological concerns
- The exact stat UI table is a community datamine/export of Riot files, not Riot Developer API documentation.
- Structural `UInt8` and reverse-engineered call topology do not prove enum meaning or owner identity.
- Missing serialized enum fields are preserved distinctly from explicit zero; zero remains a legitimate value.

## Remaining issues
- Formula 1, raw IDs 13-16, resource enum semantics, and all owner identities remain non-executable by the accepted freeze baseline.
- Phase 2I was not started.

## Codex technical recommendation
- Review the recorded evidence and contradictions as-is; do not increase coverage without new patch-specific owner or enum proof.

## Review request
NONE. Phase 2H v1 is FROZEN by accepted project review; its unresolved contracts remain explicit.
