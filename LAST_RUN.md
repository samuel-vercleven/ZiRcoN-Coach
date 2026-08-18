# LAST RUN

## Status
REVIEW_REQUIRED

## Date
2026-08-18 19:15 local

## Command
python -m knowledge.champion_knowledge

## Runtime
- completed
- approximate duration: about 99 seconds for the final full real Data Dragon champion catalog audit
- `python main.py` was not run because Champion Knowledge Phase 2B1-C is a standalone knowledge layer and is not integrated into the dev harness
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
- One precision check failed during development because the positive synthetic fixture said only "Change de forme" without an explicit self/champion subject.
- Fixed the fixture to carry explicit champion ownership evidence, then reran compile, synthetic checks, precision checks, and the full audit successfully.

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
- Champion Knowledge Phase 2B1-C implemented and tested.
- No rune knowledge, level-resolved stats, executable spell formulas, damage simulation, combos, Burst/TTK, composition analysis, champion scoring, item recommendation, or ML was added.

Phase 2B1-C audit:
- Champion knowledge version: champion_knowledge_phase2b1_c_v1.
- Locale: fr_FR.
- Resolved Data Dragon version: 16.16.1.
- Total champions: 173; individual champion files loaded: 173.
- Total spells: 692; spell-count distribution: 4 spells = 173 champions.
- Canonical stat coverage: all 20 mapped base/growth fields present for all 173 champions.
- Unknown stat fields: 0.
- Placeholder resolution: 4479 UNKNOWN_PLACEHOLDER, 33 RESOLVED_EFFECT_BURN, 10 UNRESOLVED_VAR.
- Formula status: 692 FORMULA_INCOMPLETE.
- Formula fragments: 6920 FORMULA_FRAGMENT_STRUCTURED, 4489 FORMULA_INCOMPLETE.
- Semantic parse completeness: 61 FULLY_PARSED, 1297 PARTIALLY_PARSED, 199 COMPLETELY_UNPARSED.
- TRANSFORMATION semantic count: 53.
- Complexity flags: 154 STANDARD_KIT, 19 COMPLEX_KIT_UNDERMODELED, 16 ALTERNATE_FORM_POSSIBLE, 3 COPIED_OR_DYNAMIC_ABILITY.

Transformation / complexity result:
- TRANSFORMATION remains a generic factual semantic: some transformation mechanic is described.
- ALTERNATE_FORM_POSSIBLE now requires separate evidence that the champion enters or owns an alternate form, named form, stance, or kit state.
- Generic "transforme" no longer creates champion alternate-form complexity for damage, target, mark, resource, effect, terrain/object, summoned entity, seed/plant, weapon, or ability transformations.
- Phase 2B1-B non-standard baseline audited: 31 champion cases.
- Baseline audit status: 13 CONFIRMED_COMPLEX_MECHANIC, 6 PLAUSIBLE_BUT_UNDERMODELED, 12 FALSE_POSITIVE.
- Remaining ALTERNATE_FORM_POSSIBLE: Anivia, Bel'Veth, Elise, Galio, Gnar, Irelia, Jax, Kennen, Maokai, Nidalee, Rammus, Senna, Shyvana, Swain, Udyr, Volibear.
- Remaining COPIED_OR_DYNAMIC_ABILITY: Wukong, Sylas, Viego.
- Removed Phase 2B1-B alternate-form false positives: Ambessa, Ashe, Aurelion Sol, Jarvan IV, Jayce, Jhin, K'Santé, Lissandra, Lulu, Yorick, Zeri, Zyra.

Targeted audit findings:
- Lissandra enemy-servant transformation is now non-champion target/summoned entity evidence, not champion alternate form.
- Lulu polymorph target, Zeri projectile-to-laser, and Zyra seed-to-plant are no longer champion alternate-form evidence.
- Nidalee is retained as PLAUSIBLE_BUT_UNDERMODELED via named fr_FR form evidence, including "forme de couguar" and "forme humaine".
- Xerath "dévoile sa forme véritable" is not newly promoted because it does not show the champion entering/activating that form under the current generic rules.

## Suspicious findings
- Some real kit-state champions can still be conservative false negatives when Data Dragon describes transformed weapons/abilities rather than explicit champion-owned form/state.
- Jayce and K'Santé are currently removed by the generic rules and should be reviewed before any freeze decision.
- All 692 spells remain FORMULA_INCOMPLETE by design.

## Methodological concerns
- REVIEW_REQUIRED because Champion Knowledge Phase 2B1-C is not FROZEN and freeze remains a project-review decision.
- Semantic effects are parser-derived factual evidence, not champion strength, threat, or recommendation labels.
- TRANSFORMATION must not be consumed downstream as champion form-change unless ALTERNATE_FORM_POSSIBLE evidence separately supports it.

## Remaining issues
- Phase 2B1-C is not FROZEN.
- Future formula/combat work must validate level-stat formulas and spell-damage formula semantics before calculating damage.
- Future consumers must explicitly handle UNKNOWN_PLACEHOLDER, FORMULA_INCOMPLETE, PARTIALLY_PARSED, and UNPARSED records.

## Codex technical recommendation
- Project review should inspect logs/latest_full_run.txt, especially the 31 champion complexity audit rows, Jayce/K'Santé conservative removals, and the remaining 16 ALTERNATE_FORM_POSSIBLE entries before deciding whether Phase 2B1 is freeze-ready.

## Review request
REVIEW_REQUIRED because Champion Knowledge Phase 2B1-C is implemented and tested, but freeze remains a project-review decision.
