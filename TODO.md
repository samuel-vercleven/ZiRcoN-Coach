# ZiRcoN Coach — TODO

## Current task
COMPLETED — Freeze Item Knowledge Base — Phase 2A.

## Status

Completed by Codex on 2026-08-18.

Result: PASS.

Item Knowledge Base Phase 2A is now documented as FROZEN.

No next major task is defined here; project review should define Phase 2B or any other next step.

## Decision

Project review accepts Phase 2A-C as the validated Item Knowledge baseline.

Item Knowledge Base Phase 2A is now approved for FROZEN status.

This freeze covers factual, patch-aware item knowledge only.

It does NOT freeze future:
- champion knowledge;
- rune knowledge;
- spell formulas;
- composition analysis;
- damage simulation;
- Burst / TTK;
- contextual build reasoning;
- recommendations;
- ML.

---

## Freeze baseline

Validated Data Dragon catalog:

- Item knowledge version: item_knowledge_phase2a_c_v1
- Locale: fr_FR
- Resolved Data Dragon version: 16.16.1
- Total item records: 868
- Purchasable Summoner's Rift items: 254
- Items with normalized stats: 655
- Items with extracted effects: 414
- Items with description effects: 357
- Items with unparsed/partial effect text: 443
- Graph inconsistencies: 0
- Repeated direct-component recipes: 45
- Repeated recursive-component recipes: 170
- Representative diagnostics: 18/18

Description semantic completeness:

- FULLY_PARSED sections: 96
- PARTIALLY_PARSED sections: 253
- COMPLETELY_UNPARSED sections: 384
- same-sentence partial cases preserved: 201

---

## Frozen methodology

Preserve:

- patch-aware Data Dragon version resolution;
- raw item data and descriptions;
- provenance for normalized facts;
- canonical stat normalization;
- UNKNOWN / NOT_EXPOSED handling;
- conservative semantic effect extraction;
- DESCRIPTION_EXPLICIT confidence for parser-derived semantics;
- UNPARSED_EFFECT_TEXT;
- PARTIALLY_PARSED_EFFECT_TEXT;
- original source text for auditability;
- explicit fr_FR semantic parser contract;
- item graph with component multiplicity;
- applicability / map / special-item classification.

Rules:

- Never treat partial or unparsed content as understood.
- Never infer gameplay advice directly from an item semantic tag.
- Semantic precision is preferred over recall.
- Raw source evidence remains authoritative/auditable.
- Unsupported locales must not silently use the French parser.
- Repeated components must preserve multiplicity.

---

## Permanent limitations

1. Data Dragon descriptions are not a complete formal gameplay rules engine.

2. Description-derived mechanics are parser interpretations with evidence,
   not exact executable formulas.

3. Many mechanics intentionally remain PARTIALLY_PARSED or UNPARSED.

4. The semantic description parser is currently supported only for fr_FR.

5. Duplicate item names/variants are preserved rather than merged.

6. Mode-specific, champion-specific, generated and non-purchasable items remain
   in the catalog and must be filtered by future consumers when appropriate.

7. Phase 2A does not determine whether an item is GOOD/BAD or appropriate
   against a specific champion/composition.

---

## Frozen boundary

After this commit, do not modify Item Knowledge Phase 2A unless:

- a demonstrated factual correctness bug is found;
- Riot/Data Dragon format changes require compatibility;
- a later layer requires a strictly necessary integration change;
- project review explicitly reopens it.

Do not retune the parser merely to increase semantic coverage.

---

## Existing frozen modules

Remain untouched:

- Death Analyzer v11
- Jungle Tempo / Pathing v17
- Objective Analyzer v20
- Recall / Reset Analyzer v21
- Build / Itemization Analyzer v22 Phase 1

---

## Python

Do NOT modify Python for this documentation-only freeze.

Do not rerun the catalog unless Python unexpectedly changes.

If Python modification becomes necessary:
stop and return REVIEW_REQUIRED.

---

## Documentation

Update:

- PROJECT_STATE.md
- DECISIONS.md
- TODO.md → COMPLETED
- LAST_RUN.md

Add Item Knowledge Base Phase 2A to the frozen modules / knowledge layers.

Do not start Phase 2B in this commit.

---

## Git

Commit and push.

Suggested commit:

Freeze item knowledge phase 2A
