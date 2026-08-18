# LAST RUN

## Status
REVIEW_REQUIRED

## Date
2026-08-18 21:02 local

## Command
python -m knowledge.rune_knowledge

## Runtime
- completed
- approximate duration: about 1 second
- `python main.py` was not run because the new Rune Knowledge layer is not integrated into main.py and this task requested catalog/history audits for the new module

## Files changed
- knowledge/rune_knowledge.py
- knowledge/rune_knowledge_synthetic_checks.py
- knowledge/rune_knowledge_precision_checks.py
- PROJECT_STATE.md
- TODO.md
- LAST_RUN.md
- logs/latest_full_run.txt

## Tests executed
- `python -m py_compile knowledge/rune_knowledge.py knowledge/rune_knowledge_synthetic_checks.py knowledge/rune_knowledge_precision_checks.py` - PASS
- `python -m pytest knowledge/rune_knowledge_synthetic_checks.py knowledge/rune_knowledge_precision_checks.py -q` - NOT RUN, pytest is not installed
- Direct test runner over all `test_*` functions in both new check files - PASS, 15/15
- `python -m knowledge.rune_knowledge` - PASS

## Errors encountered
- `pytest` is not installed in the local environment.
- Fixed one overly strict precision check: a plain PV reference can be classified as HEALTH as long as it is not misclassified as damage.
- Real audit revealed two parser precision issues before final baseline:
  - `GOLD` matched French "pouvez" through an overly broad `" po"` phrase.
  - single-letter `s` was too broad as a seconds unit.
- Fixed both issues and reran tests/audit successfully.

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
- Implemented Rune Knowledge Base Phase 2C1 as a new factual, patch-aware, UI-agnostic layer.
- Data Dragon schema observed: top-level list of style records; style keys icon/id/key/name/slots; slot key runes; rune keys icon/id/key/longDesc/name/shortDesc.
- Resolved Data Dragon version: 16.16.1.
- Locale: fr_FR.
- Rune knowledge version: rune_knowledge_phase2c1_v1.
- Total rune trees/styles: 5.
- Total slots: 20.
- Total rune records: 62.
- Formula status counts: 62 RUNE_FORMULA_INCOMPLETE.
- Structure completeness: 18 FULLY_STRUCTURED, 44 PARTIALLY_STRUCTURED.
- Unparsed/partial text records: 60 PARTIALLY_STRUCTURED_RUNE_TEXT, 12 UNPARSED_RUNE_TEXT.
- Numeric fragments: 305 NUMERIC_LITERAL, 29 NUMERIC_RANGE.
- Static statPerks present in runesReforged: none.
- Historical raw JSON audited: 104 matches, 1040 participants.
- Rune selections observed: 6240.
- Rune catalog link statuses: 6240 LINKED_RUNE_CATALOG, 0 UNKNOWN_PERK_ID.
- Rune style link statuses: 2080 LINKED_RUNE_STYLE, 0 UNKNOWN_RUNE_STYLE_ID.
- Riot `var1`/`var2`/`var3` observations: 6240 each; values preserved as RIOT_OBSERVED_UNINTERPRETED.
- Non-zero var observations: var1 5927, var2 2324, var3 289.
- statPerks status counts: offense/flex/defense each 1040 STAT_PERK_NOT_EXPOSED_BY_DDRAGON_RUNE_CATALOG.
- statPerks.offense IDs: 5005 552, 5008 378, 5007 110.
- statPerks.flex IDs: 5001 90, 5008 905, 5010 45.
- statPerks.defense IDs: 5001 793, 5011 216, 5013 31.
- Magical Footwear static record found: rune 8304, key MagicalFootwear, name Chaussures magiques, Inspiration slot 1.
- Magical Footwear observed: 211 participant selections across 97 matches.
- Frozen Itemization v22 compatibility check: PASS for 8304 / item 2422 / RUNE_GRANT / DERIVED_INFERRED timing.

## Suspicious findings
- Data Dragon `runesReforged.json` does not expose stat shard meanings or values, so the observed IDs 5005/5008/5007/5001/5010/5011/5013 remain NOT_EXPOSED.
- All runes remain RUNE_FORMULA_INCOMPLETE because descriptions are not executable formulas.

## Methodological concerns
- REVIEW_REQUIRED: project review must validate whether Phase 2C1's conservative semantic tags, condition extraction, numeric fragment handling, and stat shard non-interpretation are acceptable.
- Future consumers must not treat PARTIALLY_STRUCTURED_RUNE_TEXT or UNPARSED_RUNE_TEXT as understood.
- Future consumers must not execute rune conditions or infer stat shard values from memory.

## Remaining issues
- No rune formula execution exists.
- No stat shard meaning/value mapping exists from official Data Dragon data.
- No damage, Burst/TTK, composition, recommendation, rune scoring, or ML work was started.

## Codex technical recommendation
- Have project review inspect the Phase 2C1 baseline and decide whether to request another precision pass or freeze the factual Rune Knowledge layer.

## Review request
- REVIEW_REQUIRED because this is a new knowledge layer and the task explicitly requested review before moving forward.
