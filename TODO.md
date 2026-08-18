# ZiRcoN Coach - TODO

## Current task
COMPLETED - Freeze Rune Knowledge Base Phase 2C1-B.

## Completion status
FROZEN.

Validated freeze baseline:
- Rune knowledge version: `rune_knowledge_phase2c1_b_v3`.
- Data Dragon version: 16.16.1.
- Locale: fr_FR.
- Rune records: 62/62 audited.
- Styles: 5.
- Slots: 20.
- Synthetic checks: PASS 13/13.
- Precision checks: PASS 10/10.
- Real Rune Knowledge audit: PASS.
- Full catalog audit: PASS.
- Full catalog blocking issues: 0.
- Full catalog review cases: 0.
- Legacy generic stat tags: 0.
- Historical raw JSON: 104 matches / 1040 participants.
- Historical rune selections: 6240.
- Rune catalog links: 6240 LINKED_RUNE_CATALOG, 0 UNKNOWN_PERK_ID.
- Rune style links: 2080 LINKED_RUNE_STYLE, 0 UNKNOWN_RUNE_STYLE_ID.
- Magical Footwear 8304 compatibility with frozen Itemization v22: PASS.
- FROZEN guard: PASS.

Permanent limitations:
- All 62 formulas remain RUNE_FORMULA_INCOMPLETE.
- Rune conditions remain NOT_EXECUTED.
- Riot var1/var2/var3 remain RIOT_OBSERVED_UNINTERPRETED.
- statPerk meanings/values remain NOT_EXPOSED from the validated static source.
- partial/unparsed text remains explicit uncertainty.
- no damage, Burst/TTK, composition recommendations, build recommendations, rune scoring, or ML is part of this frozen layer.

Freeze rule:
Do not modify Rune Knowledge Phase 2C1-B unless there is a demonstrated factual correctness bug, Riot/Data Dragon compatibility requirement, strictly necessary downstream integration change, or explicit project review request.

## Next major task
NEXT - Level-Resolved Champion Stat Formula Foundation.

Scope:
- establish and validate the exact champion level-stat calculation contract before combat simulation;
- consume the frozen Champion Knowledge layer without retuning it;
- preserve provenance and explicit unsupported/unknown states;
- add focused synthetic checks, precision checks, and real-data diagnostics;
- do not start Combat / Damage Engine, Burst/TTK, composition recommendations, build recommendations, or ML yet.

After this foundation is validated, project review will define the next factual combat-input/formula layer before Combat / Damage Engine work.
