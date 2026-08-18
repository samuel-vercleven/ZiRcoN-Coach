# LAST RUN

## Status
REVIEW_REQUIRED

## Date
2026-08-18 18:45 local

## Command
python -m knowledge.champion_knowledge

## Runtime
- completed
- approximate duration: about 51 seconds for the final full real Data Dragon champion catalog audit
- `python main.py` was not run because Champion Knowledge Phase 2B1-B is a standalone knowledge layer and is not integrated into the dev harness
- raw audit and representative diagnostics saved to logs/latest_full_run.txt

## Files changed
- knowledge/champion_knowledge.py
- knowledge/champion_knowledge_synthetic_checks.py
- knowledge/champion_knowledge_precision_checks.py
- PROJECT_STATE.md
- TODO.md
- LAST_RUN.md

## Tests executed
- `.venv\Scripts\python.exe -m py_compile knowledge\champion_knowledge.py knowledge\champion_knowledge_synthetic_checks.py knowledge\champion_knowledge_precision_checks.py`
- `.venv\Scripts\python.exe -m knowledge.champion_knowledge_synthetic_checks`
- `.venv\Scripts\python.exe -m knowledge.champion_knowledge_precision_checks`
- `.venv\Scripts\python.exe -X utf8 -m knowledge.champion_knowledge`

## Errors encountered
- Initial sandboxed Python runs failed because `.venv\Scripts\python.exe` points to a base Python path denied by the sandbox.
- Re-ran the same compile/tests/audit with approved elevated execution; all passed.
- No code/runtime errors remained.

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
- Build / Itemization Analyzer v22 Phase 1 not modified; remains FROZEN.
- Item Knowledge Base Phase 2A not modified; remains FROZEN.
- Champion Knowledge Phase 2B1-B implemented and tested.
- No rune knowledge, level-resolved stats, executable spell formulas, damage simulation, combos, Burst/TTK, composition analysis, champion scoring, item recommendation, or ML was added.

Phase 2B1-B audit:
- Champion knowledge version: champion_knowledge_phase2b1_b_v1.
- Locale: fr_FR.
- Resolved Data Dragon version: 16.16.1.
- Total champions: 173.
- Individual champion files loaded: 173.
- Total spells: 692.
- Spell-count distribution: 4 spells = 173 champions.
- Canonical stat coverage: all 20 mapped base/growth fields present for all 173 champions.
- Unknown stat fields: 0.
- Placeholder resolution: 4479 UNKNOWN_PLACEHOLDER, 33 RESOLVED_EFFECT_BURN, 10 UNRESOLVED_VAR.
- Formula status: 692 FORMULA_INCOMPLETE.
- Formula fragments: 6920 FORMULA_FRAGMENT_STRUCTURED, 4489 FORMULA_INCOMPLETE.
- Semantic parse completeness: 61 FULLY_PARSED, 1297 PARTIALLY_PARSED, 199 COMPLETELY_UNPARSED.
- Complexity flags: 142 STANDARD_KIT, 31 COMPLEX_KIT_UNDERMODELED, 28 ALTERNATE_FORM_POSSIBLE, 3 COPIED_OR_DYNAMIC_ABILITY.

Sensitive semantic counts vs Phase 2B1 baseline:
- SHIELD: 128 -> 41.
- DAMAGE_TYPE_UNRESOLVED: 314 -> 359; increase comes from clause-local untyped outgoing damage evidence, while defensive/reduction contexts are blocked.
- PERCENT_MAX_HEALTH_DAMAGE: 83 -> 62.
- PERCENT_CURRENT_HEALTH_DAMAGE: 13 -> 13.
- MISSING_HEALTH_DAMAGE: 48 -> 21.
- REVEAL: 68 -> 27.
- TRANSFORMATION: 40 -> 53; generic "forme de" no longer qualifies, but explicit transformation clauses are captured with narrower evidence.

Precision fixes verified:
- SHIELD now requires grant/create/obtain/apply/absorb/protect evidence.
- DAMAGE_TYPE_UNRESOLVED requires outgoing damage action and excludes damage taken/reduction/immunity/absorption contexts.
- Percent-health damage requires HP reference and outgoing damage evidence in the same clause.
- Generic "vision" no longer creates REVEAL.
- Generic "forme de" no longer creates TRANSFORMATION or ALTERNATE_FORM_POSSIBLE.
- Rejected sensitive phrase matches are preserved in partial/unparsed records.

Complexity audit:
- All 38 Phase 2B1 baseline complex champions were audited in logs/latest_full_run.txt.
- Review statuses: 25 CONFIRMED_COMPLEX_MECHANIC, 6 PLAUSIBLE_BUT_UNDERMODELED, 7 FALSE_POSITIVE.
- CONFIRMED_COMPLEX_MECHANIC: Ambessa, Anivia, Ashe, Aurelion Sol, Bel'Veth, Elise, Gnar, Jarvan IV, Jayce, Jhin, K'Sante, Kennen, Lissandra, Lulu, Maokai, Wukong, Senna, Shyvana, Swain, Sylas, Viego, Volibear, Yorick, Zeri, Zyra.
- PLAUSIBLE_BUT_UNDERMODELED: Galio, Irelia, Jax, Nidalee, Rammus, Udyr.
- FALSE_POSITIVE removed by generic rules: Aatrox, Fiora, Graves, Kassadin, Renekton, Vayne, Zaahen.

UNKNOWN_PLACEHOLDER audit:
- Families: 2902 likely_formula_related_but_unresolved, 1257 formatting_or_display_placeholder, 308 unknown, 12 calculated_or_custom_ddragon_placeholder.
- Top keys: spellmodifierdescriptionappend 692, cost 567, abilityresourcename 557, totaldamage 200, slowduration 90.
- Placeholders remain unresolved unless Data Dragon gives clear eN/aN/fN provenance; no artificial formula resolution was added.

## Suspicious findings
- All 692 spells remain FORMULA_INCOMPLETE by design.
- DAMAGE_TYPE_UNRESOLVED count increased; evidence is now clause-local and should be reviewed as a granularity change, not a formula claim.
- TRANSFORMATION count increased despite removing generic "forme de"; review should inspect explicit "transforme" cases that may be dynamic ability-state changes rather than full alternate forms.

## Methodological concerns
- REVIEW_REQUIRED because Champion Knowledge Phase 2B1-B is not FROZEN and freeze remains a project-review decision.
- Semantic effects are parser-derived factual evidence, not champion strength, threat, or recommendation labels.
- Level-resolved stats and executable spell formulas remain deliberately out of scope.

## Remaining issues
- Phase 2B1-B is not FROZEN.
- Future formula/combat work must validate level-stat formulas and spell-damage formula semantics before calculating damage.
- Future consumers must explicitly handle UNKNOWN_PLACEHOLDER, FORMULA_INCOMPLETE, PARTIALLY_PARSED, and UNPARSED records.

## Codex technical recommendation
- Project review should inspect logs/latest_full_run.txt, especially the 38 complex champion audit rows and the increased DAMAGE_TYPE_UNRESOLVED / TRANSFORMATION counts, before deciding whether Phase 2B1-B is freeze-ready.

## Review request
REVIEW_REQUIRED because Champion Knowledge Phase 2B1-B is implemented and tested, but freeze remains a project-review decision.
