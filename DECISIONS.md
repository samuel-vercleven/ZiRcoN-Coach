# ZiRcoN Coach - Decisions Log

## Development philosophy
Develop and validate major analyzers one by one.
Freeze when measurement semantics are coherent, real-game audit is plausible, no major correctness bug remains, validation is appropriate, and limitations are documented.

## Death Analyzer v11 - FROZEN
Reasons:
- historical-only scoring;
- exact death-count conditioning;
- game-level CV, walk-forward, bootstrap, FDR;
- volume separated from per-death cost.
Rule: never phrase cumulative resource loss as causal net cost.

## Jungle Tempo / Pathing v17 - FROZEN
Reasons:
- personal pathing separated from enemy success;
- FARMABLE vs MIRRORED;
- time-local references;
- +/-60s boundary guard;
- sustained alerts became rare and plausible.
Rule: pathing score is a historical composite, not a probability.

## Objective Analyzer v20 - FROZEN
Reasons:
- stable extraction;
- preparation/conversion separation;
- BEFORE vs AFTER trade direction fixed;
- spatial contest;
- meaningful resource-compensation thresholds;
- historical minimum 20.
Rule: contest is evidence, not ground truth; lost objective != automatic player error.

## Recall / Reset Analyzer v21 - FROZEN
Decision:
Freeze Recall / Reset Analyzer v21 with production SHOP_CLUSTER_GAP_SECONDS retained at 20.

Reasons:
- voluntary reset proxies and post-death shop sequences are separated credibly on real history;
- Reentry Score is historical-only;
- real-history validation passed on the local 87-game Jungle dataset;
- threshold-independent clustering audit completed;
- final audit found 13 SEPARATE_VISITS, 11 UNRESOLVED, and 0 SAME_VISIT_CANDIDATE among the 24 pairs with 20s < gap <= 45s;
- 20s clustering threshold is retained conservatively;
- no independent evidence justified increasing the production threshold;
- raising the threshold would merge some independently supported separate visits;
- unresolved same-frame Riot cases are insufficient evidence for merging;
- objective-near reset audit found no extraction/order bug;
- target match EUW1_7951911875 remained stable.

Permanent limitations:
- Riot does not expose a perfect recall lifecycle;
- purchase clusters are SHOP/RESET proxies, not exact recalls;
- same-frame Riot gaps may remain unresolved;
- current Gold is exploratory/contextual only;
- objective proximity is context, not a player-mistake label;
- Reentry Score measures observed post-reset production, not causal recall quality.

Rules:
- Do not change the 20s clustering threshold without explicit project review.
- Do not describe reset proxies as exact recalls.
- Do not convert current Gold, objective proximity, or low Reentry Score into automatic fault labels.
- Keep raw reset components auditable alongside any explanatory composite.

## Build / Itemization Analyzer v22 Phase 1 - FROZEN
Decision:
Freeze Build / Itemization Analyzer v22 Phase 1 as factual item/inventory reconstruction.

Scope:
- Riot timeline item-event reconstruction;
- Data Dragon item metadata usage;
- purchase, sell, undo, component, trinket, consumable, jungle-item, and final-inventory validation behavior;
- Magical Footwear grant handling;
- generic inventory reliability intervals.

Out of scope:
- item semantic quality;
- champion matchup knowledge;
- allied/enemy composition analysis;
- contextual build reasoning;
- item recommendations;
- ML.

Reasons:
- project review accepted Phase 1D as the freeze baseline;
- 87-game Jungle validation completed with 86 EXACT and 1 EXACT_WITH_EXPLAINED_GRANT final inventories;
- observed-or-explained final inventory agreement reached 100.0%;
- no PARTIAL, MISMATCH, or UNKNOWN final inventory remained;
- no LIKELY_REAL_REMOVAL evidence was found;
- Phase 1D resolved plain UNRESOLVED destroyed records as consumable Riot representation;
- remaining ambiguity is explicitly surfaced through reliability intervals instead of hidden or overclaimed.

Rules:
- RELIABLE means the reconstructed durable inventory can be used by future consumers.
- AMBIGUOUS_TEMPORARY_STATE means a temporary/possession-like mechanic may make the observed inventory unreliable for that interval.
- UNRESOLVED_TRANSFORMATION means Riot/Data Dragon chronology indicates a transformation or grant-related interval that cannot be safely materialized as an observed item event.
- Do not fabricate corrected inventory events when Riot item chronology is ambiguous.
- Viego-specific uncertainty must use the generic reliability mechanism and remain isolated from normal champion reconstruction.
- Viego possession inventory is not reliably reconstructible from the current Riot data.
- ITEM_DESTROYED must not be treated globally as permanent item removal.
- The non-Viego REAL_MISSED_TRANSFORMATION interval remains UNRESOLVED_TRANSFORMATION rather than a fabricated item event.
- Magical Footwear derived timing remains DERIVED / INFERRED unless Riot emits an observed item event.
- Future consumers, including build recommendations, must ignore or explicitly handle inventory intervals that are not RELIABLE.
- Do not modify Phase 1 production reconstruction unless a demonstrated correctness bug is found, a later phase requires a strictly necessary compatibility change, or project review explicitly reopens it.

Status:
FROZEN.

## Item Knowledge Base Phase 2A - FROZEN
Decision:
Freeze Item Knowledge Base Phase 2A as the factual, patch-aware item knowledge layer.

Scope:
- Data Dragon item catalog loading and patch-aware version resolution;
- raw item data preservation, including descriptions, plaintext, stats, effects, gold, tags, maps, components, upgrades, consumed fields, and audit metadata;
- canonical stat normalization with provenance;
- conservative semantic description parsing for fr_FR;
- DESCRIPTION_EXPLICIT confidence for parser-derived mechanics;
- UNKNOWN, NOT_EXPOSED, UNPARSED_EFFECT_TEXT, and PARTIALLY_PARSED_EFFECT_TEXT preservation;
- item graph facts with repeated component multiplicity preserved;
- applicability, map, special/generated, champion-specific, mode-specific, non-purchasable, consumable, trinket, jungle-starter, and boots classification.

Out of scope:
- champion knowledge;
- rune knowledge;
- spell formulas;
- composition analysis;
- damage simulation;
- Burst / TTK;
- contextual build reasoning;
- recommendations;
- GOOD/BAD item labels;
- item scoring;
- ML.

Validated baseline:
- item knowledge version item_knowledge_phase2a_c_v1;
- Data Dragon version 16.16.1;
- locale fr_FR;
- 868 total item records;
- 254 purchasable Summoner's Rift items;
- 655 items with normalized stats;
- 414 items with extracted effects;
- 357 items with description effects;
- 443 items with unparsed or partial effect text;
- 96 FULLY_PARSED description sections;
- 253 PARTIALLY_PARSED description sections;
- 384 COMPLETELY_UNPARSED description sections;
- 201 same-sentence partial cases preserved as incomplete;
- 45 repeated direct-component recipes;
- 170 repeated recursive-component recipes;
- 0 graph inconsistencies;
- representative diagnostics coverage 18/18.

Reasons:
- project review validated Phase 2A-C as the accepted Phase 2A baseline;
- parser behavior now favors precision and auditability over false completeness;
- same-sentence multi-mechanic text is not marked FULLY_PARSED merely because one mechanic was recognized;
- raw source evidence and provenance remain available to downstream consumers;
- Data Dragon component multiplicity is preserved instead of deduplicated away;
- unsupported locales cannot silently use the French semantic parser.

Permanent limitations:
- Data Dragon descriptions are not a complete formal gameplay rules engine;
- description-derived mechanics are parser interpretations with evidence, not exact executable formulas;
- the semantic description parser is supported only for fr_FR;
- many mechanics intentionally remain PARTIALLY_PARSED or UNPARSED;
- duplicate item names and variants are preserved rather than merged;
- mode-specific, champion-specific, generated, and non-purchasable records remain in the catalog and must be filtered by future consumers when appropriate;
- Phase 2A does not decide whether an item is good or bad in a champion/composition context.

Rules:
- Prefer UNKNOWN / UNPARSED / PARTIALLY_PARSED to false certainty.
- Never treat partial or unparsed content as understood.
- Never infer gameplay advice directly from an item semantic tag.
- Preserve raw Data Dragon source text and provenance for audit.
- Preserve repeated component multiplicity.
- Do not retune the parser merely to increase semantic coverage.
- Do not modify Phase 2A without a demonstrated factual correctness bug, Riot/Data Dragon compatibility need, strictly necessary downstream integration change, or explicit project review request.

Status:
FROZEN.

## Champion Knowledge Base Phase 2B1 - FROZEN
Decision:
Freeze Champion Knowledge Base Phase 2B1 as the factual, patch-aware champion knowledge layer after project review validated Phase 2B1-C.

Scope:
- Data Dragon champion catalog loading plus all individual champion detail files;
- champion identity, Riot metadata, raw individual champion JSON, base stats, growth fields, passive and spell records;
- cooldowns, costs, ranges, effects, effectBurn, vars, images, tooltips, raw descriptions, cleaned descriptions, semantic evidence, placeholder resolution, formula fragments, and complexity flags;
- conservative fr_FR semantic parsing with provenance;
- conservative kit-complexity warnings with evidence.

Out of scope:
- rune knowledge;
- level-resolved stat calculation;
- executable formulas;
- damage engine;
- combos;
- Burst / TTK;
- composition analysis;
- champion strength scoring;
- item recommendations;
- ML.

Validated baseline:
- champion knowledge version champion_knowledge_phase2b1_c_v1;
- Data Dragon version 16.16.1;
- locale fr_FR;
- 173 champions;
- 692 spells;
- all 20 mapped base/growth stat fields present for all 173 champions;
- 4479 UNKNOWN_PLACEHOLDER preserved;
- 692 FORMULA_INCOMPLETE by design;
- semantic parse completeness: 61 FULLY_PARSED, 1297 PARTIALLY_PARSED, 199 COMPLETELY_UNPARSED;
- complexity flags: 154 STANDARD_KIT, 19 COMPLEX_KIT_UNDERMODELED, 16 ALTERNATE_FORM_POSSIBLE, 3 COPIED_OR_DYNAMIC_ABILITY.

Core rule:
- TRANSFORMATION means something is transformed.
- ALTERNATE_FORM_POSSIBLE requires separate provenance that the champion itself owns or enters a form, posture, or kit state.
- Future consumers must not treat TRANSFORMATION as proof of champion alternate form without ALTERNATE_FORM_POSSIBLE evidence.

Reasons:
- project review accepted the Phase 2B1-C correction separating generic transformation semantics from champion form complexity;
- the layer preserves raw Data Dragon source facts and marks unresolved formula/placeholder content instead of fabricating precision;
- UNKNOWN_PLACEHOLDER and FORMULA_INCOMPLETE are intentional factual limitations;
- parser output is auditable through evidence text and provenance;
- complexity flags are conservative warnings, not exhaustive truth;
- false negatives caused by Data Dragon wording limitations are accepted in preference to champion-specific hacks.

Rules:
- Prefer UNKNOWN, PARTIALLY_PARSED, COMPLETELY_UNPARSED, and FORMULA_INCOMPLETE to false certainty.
- Do not calculate level-resolved stats until a later validated formula/stat layer exists.
- Do not execute spell formulas from Phase 2B1 data.
- Do not infer champion strength, matchup advice, build advice, or composition recommendations from Phase 2B1 facts alone.
- Do not add champion-specific production hacks to improve complexity coverage.
- Do not modify Phase 2B1 without a demonstrated factual correctness bug, Riot/Data Dragon compatibility need, strictly necessary downstream integration change, or explicit project review request.

Status:
FROZEN.
