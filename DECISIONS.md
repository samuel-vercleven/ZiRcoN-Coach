# ZiRcoN Coach - Decisions Log

## Development philosophy
Develop and validate major analyzers one by one.
Freeze when measurement semantics are coherent, real-game audit is plausible, no major correctness bug remains, validation is appropriate, and limitations are documented.

## ZiRcoN Coach V0.1 Alpha product architecture - REVIEW REQUIRED FOR ALPHA FREEZE
Decision:
- keep `main.py` as the immutable-backend validation harness and use `run_app.py` as the PySide6 launcher;
- keep the desktop product local-first: SQLite browsing and cached post-game evidence work without Riot availability;
- isolate mutable UI concerns in services/adapters/DTOs instead of changing or copying frozen analyzer behavior;
- use an explicit-key runtime Riot client so a validated replacement development key is effective without restart;
- perform every Riot/Data Dragon network request outside the Qt main thread;
- persist only non-secret profile metadata and analyzer-version-keyed reports in additive SQLite tables;
- keep display-asset Data Dragon versioning separate from frozen semantic knowledge versions;
- preserve `AVAILABLE / PARTIAL / UNAVAILABLE / ERROR` and analyzer provenance in the post-game UI.

Safety boundary:
- deterministic summaries may select and restate analyzer-supported evidence but may not invent causal coaching, combat values, build recommendations, owner mappings, or LLM/ML conclusions;
- `.env`, runtime databases, settings and asset caches remain untracked;
- V0.1 remains under review and is not FROZEN.

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

## Champion Spell Stat Reference Semantics Foundation Phase 2H v1 - FROZEN

Decision:
- treat exact pinned `GlobalStatsUIData.json` identities as primary raw-stat evidence, but require independent exact spell/mechanic evidence before a mapping becomes execution-eligible;
- keep `mStat` identity, `mStatFormula` base/bonus/total semantics, and owner identity as separate records;
- expose convenience maps from `VALIDATED` records only;
- never infer missing enum positions or ownership from frequency, champion archetype, damage type, coefficient magnitude, calculation key, or adjacent integers.

Accepted frozen Phase 2H v1 mappings:
- execution-eligible stats: `1 -> ARMOR`, `2 -> ATTACK_DAMAGE`, `12 -> HEALTH`;
- `STRONGLY_SUPPORTED`, non-executable stats: 4, 6, 7, 8, 9, 10, 18, 29, and 31 with their direct pinned UI identities;
- unresolved stats: 13, 14, 15, and 16;
- formula 0 is `TOTAL_STAT` and formula 2 is `BONUS_STAT` for the exact pinned stat branch;
- formula 1 remains `CONTRADICTED` because the single pinned occurrence does not distinguish the incompatible historical/current public claims.

Ownership and execution boundary:
- all 569 real `mStat` occurrences remain `OWNER_UNRESOLVED`;
- no stat-reference occurrence is fully composable without owner proof;
- Phase 2H may identify a compatible frozen Phase 2G snapshot field, but does not execute stat calculation classes or modify Phase 2G;
- Phase 2G native-at-level fields are not automatically equivalent to internal `BASE_STAT` semantics;
- `AbilityResourceByCoefficientCalculationPart` remains a separate `RESOURCE_ENUM_RESEARCH_ONLY` branch.

Provenance rule:
- immutable repository commits are recorded where available;
- official Riot patch notes are mechanic anchors, not internal enum documentation;
- `UInt8`/memory-layout evidence proves structure only;
- historical community tables that conflict with exact 26.16 fixtures remain recorded as contradictions rather than silently discarded.

Freeze rule:
- do not modify Phase 2H production or validation files without a demonstrated correctness/integration bug or explicit project review request;
- do not promote strongly supported, contradicted, or unresolved semantics to execution eligibility without new patch-specific proof;
- do not start Phase 2I without project review and a new TODO.

Status:
FROZEN by project review.

## Stat Owner Semantics Foundation Phase 2I v1 - FROZEN

Decision:
- freeze the accepted zero-gate baseline `champion_spell_stat_owner_semantics_phase2i_v1` and top foundation `stat_scaling_formula_foundation_phase2i_v1`;
- distinguish the stat subject supplied to a calculation context from the gameplay identity of caster, target, or another unit;
- require owner contracts at `class + exact signature + structural context` granularity;
- treat ordinary pinned stat signatures as `OWNER_CONTEXT_DEPENDENT`, not caster-owned, because the available runtime interfaces expose a caller-supplied `UnitStatComponent` / `Champion` without a patch-specific proof of every client call-site binding;
- keep the two signatures containing unknown `0xa8cb9c14` fields `OWNER_UNRESOLVED`;
- admit only exact `OWNER_VALIDATED_*` contracts to stat arithmetic.

Evidence conclusion:
- the exact 26.16 spell graphs and patch-matched meta schema prove serialized structure but contain no named owner selector for the ordinary stat signatures;
- historical calcrev interfaces route stat lookup through the evaluation context's `UnitStatComponent`;
- LeagueBuilder independently routes stat lookup through the caller-provided `CalculationContext.Champion`;
- these sources agree on a context-supplied stat subject but do not prove universal caster or target identity in the 26.16 game client.

Execution boundary:
- 567/569 occurrences are context-dependent and 2/569 are unresolved;
- 0 real owner contracts are validated and 0 occurrences are owner-execution-eligible;
- the Phase 2I arithmetic gate therefore remains closed;
- no stat-scaling evaluator or numeric 1,443-formula replay is created merely to manufacture coverage;
- the frozen Phase 2H stat/formula maps are consumed as-is and cannot be upgraded by Phase 2I.

Accepted freeze baseline:
- 569 stat occurrences and 88 exact class/signature/context owner contracts;
- 567 `OWNER_CONTEXT_DEPENDENT`, 2 `OWNER_UNRESOLVED`, and zero validated caster, target, source-level, or other-context owners;
- 0 owner-execution-eligible occurrences;
- gate blockers: 467 owner, 101 frozen stat ID, and 1 frozen formula ID;
- Branch B remains not started, with 0 stat arithmetic and no numeric 1,443-calculation replay;
- frozen Phase 2G remains 13 `RESOLVED`, 720 `PARTIALLY_RESOLVED`, 493 `UNSUPPORTED_SIGNATURE`, and 217 `UNSUPPORTED_CLASS`.

Rules:
- damage target must never be substituted for stat owner;
- champion spell membership alone is not caster-owner evidence;
- a caller-supplied calculation unit may be reported as context-dependent, but it cannot be mapped to a source or target snapshot without independent binding evidence;
- unknown extra fields fail closed;
- future execution requires new patch-specific owner/call-site evidence and project review.

Status:
FROZEN by project review.

## Executable Combat Formula Foundation Phase 2G v2 - FROZEN

Decision:
Freeze Executable Combat Formula Foundation Phase 2G v2 after the accepted pre-freeze hardening and full Phase 2G validation stack.

- Formula arithmetic executability and semantic identity as damage are separate decisions. A resolved calculation is not automatically damage.
- Unknown classes, signatures, stat enums, owners, activation conditions, and rank shapes remain explicit unsupported/unresolved results; coverage must not be increased through guessing.
- Pinned DataValue arrays use separately audited source contracts: rank-indexed 0..6 arrays and cast-cost rank-indexed 1..6 arrays. Generic arrays do not inherit those contracts implicitly.
- Static combat snapshots apply only structured, unconditional `DDRAGON_STATS` item facts. Every relevant excluded fact is preserved as structured evidence and makes only its dependent stat partial; an excluded contribution is never silently converted to exact zero.
- Independent percentage-penetration sources remain separate until frozen Phase 2E combines them multiplicatively; adapters must not pre-sum them.
- Executable calculation contracts are exact structural signatures with pinned provenance. An added or missing field fails closed to `UNSUPPORTED_SIGNATURE`, even when the calculation class is known.
- Calculation-key text is supporting evidence only. High-confidence damage identity requires component-local structural linkage between a typed tooltip field and an exact pinned calculation key.
- Combat mitigation delegates to frozen Phase 2E and never duplicates or pre-applies resistance/penetration formulas.
- Multiple spell components remain separate. A total is emitted only for a structured `COMPOSABILITY_VALIDATED` decision that covers every component, contains evidence, and carries `PROJECT_VALIDATED` provenance. Caller assertions and the legacy boolean are insufficient.
- The optional spell-source cache is keyed to source/schema/commit/Data Dragon/locale, checksum-validated, ignored by Git, and may never substitute data from another patch.

Accepted baseline:
- version `combat_formula_foundation_phase2g_v2`;
- 173 champions, 692 primary Q/W/E/R slots, 1,443 calculations, 5,318 graph nodes, 25 classes, and 109 observed structural signatures;
- six exact executable signatures only; 0 arithmetic evaluations under unregistered signatures;
- evaluator: 13 RESOLVED, 720 PARTIALLY_RESOLVED, 493 UNSUPPORTED_SIGNATURE, 217 UNSUPPORTED_CLASS;
- snapshots: 6,920 audited rows, 4,844 fully resolved, 2,076 partial;
- damage evidence: 345 high confidence, 195 multiple candidates, 125 not identified, 27 insufficient, and 0 high-confidence key-name-only cases;
- raw/post-mitigation real damage and composable real totals: 0 / 0 / 0, accepted as the precise result rather than a coverage failure;
- full synthetic, precision, real-audit, `python main.py`, FROZEN guard, and diff validation: PASS.

Freeze rules:
- do not infer stat enums, owner mappings, activation, tick, damage, or composability semantics to raise coverage;
- per-stat completeness remains mandatory; description-derived static item facts stay explicit partial/unknown when excluded from exact arithmetic;
- percentage penetration multiplicity remains preserved and is delegated to frozen Phase 2E;
- high-confidence damage identity requires component-local structural evidence;
- exact totals require a `PROJECT_VALIDATED` composability decision;
- do not begin Phase 2H or any new combat layer without project review.

Status:
FROZEN.

## Champion Spell Calculation Source Foundation Phase 2F v1 - FROZEN
Decision:
Freeze Phase 2F v1 as the patch-pinned, lossless champion primary-spell calculation-source catalog.

Accepted baseline:
- source version `champion_spell_source_phase2f_v1`;
- immutable `Haru-Kay/LeagueDatamines` commit `9245fd616059c6c658d1faa1029f0e18ea179154`, label `LIVE 26.16 (#17)`;
- Data Dragon 16.16.1 / Riot 26.16, locale fr_FR;
- 173/173 champions and 692/692 primary Q/W/E/R mappings;
- 1,443 raw calculation records, 5,063 raw DataValues, and 5,318 dictionary graph nodes;
- 4,687 nodes with `~class`, 631 without `~class`, 25 non-null classes;
- 0 source failures, missing/ambiguous mappings, or malformed graphs;
- synthetic checks PASS 10/10, precision checks PASS 4/4, real audit PASS.

Permanent rules:
- the source is a community datamine/export of Riot game files, not a Riot Developer Portal endpoint;
- raw graph structure, unknown fields, classless dictionaries, and provenance remain lossless and auditable;
- Phase 2F does not execute or semantically interpret formulas;
- downstream layers must consume Phase 2F rather than copy or redefine its source mapping;
- do not modify Phase 2F without a demonstrated correctness/source compatibility bug, strictly necessary integration change, or explicit project review.

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

## Rune Knowledge Base Phase 2C1-B - FROZEN
Decision:
Freeze Rune Knowledge Base Phase 2C1-B as the factual, patch-aware rune knowledge layer after the refined-stat-semantics and full-catalog review.

Scope:
- Data Dragon `runesReforged.json` catalog and patch-aware historical catalog resolution;
- rune tree/style, slot, ID, key, icon, name, description, raw JSON, numeric-fragment, condition, semantic-evidence, unresolved-text, and provenance preservation;
- structural KEYSTONE/MINOR role derivation;
- Riot PRIMARY/SECONDARY page context kept separate from rune role;
- Riot observed perk linkage, `var1`/`var2`/`var3` preservation, and statPerks auditing;
- Magical Footwear compatibility contract with frozen Itemization v22;
- conservative fr_FR semantic relations validated by full-catalog audit.

Validated baseline:
- rune knowledge version rune_knowledge_phase2c1_b_v3;
- Data Dragon version 16.16.1;
- locale fr_FR;
- 5 rune styles, 20 slots, 62 rune records;
- 62/62 runes audited by the full-catalog audit;
- 13/13 synthetic checks PASS;
- 10/10 precision checks PASS;
- real Rune Knowledge audit PASS;
- full-catalog audit PASS;
- 0 blocking issues;
- 0 review cases;
- 0 legacy generic stat tags;
- 104 historical matches / 1040 participants / 6240 rune selections audited;
- 6240 LINKED_RUNE_CATALOG, 0 UNKNOWN_PERK_ID;
- 2080 LINKED_RUNE_STYLE, 0 UNKNOWN_RUNE_STYLE_ID;
- Magical Footwear itemization compatibility PASS;
- previously frozen module guard PASS.

Reasons:
- project review found and corrected false or overly broad semantic treatment before freeze;
- HEALTH references are separated from actual health-stat gains;
- ARMOR and MAGIC_RESISTANCE preserve coordinated sentence semantics and distinguish gain, target reduction, scaling, and reference;
- MOVE_SPEED, ATTACK_SPEED, ABILITY_HASTE, ADAPTIVE_FORCE, and MANA no longer use broad generic modification tags on the validated catalog;
- Ruban de mana distinguishes permanent max-mana gain from mana restoration;
- Tempo mortel distinguishes attack-speed gain from attack-speed-based damage scaling;
- the exhaustive catalog audit now examines all 62 current runes rather than relying only on representative examples;
- historical linkage is patch-aware and does not silently substitute the latest catalog for unavailable historical patches;
- unknown, partial, unparsed, uninterpreted, and not-exposed states remain explicit instead of being filled from memory.

Permanent limitations:
- Data Dragon descriptions are not executable gameplay formulas;
- all 62 rune formulas remain RUNE_FORMULA_INCOMPLETE;
- numeric fragments are source evidence, not computed formulas;
- condition text is NOT_EXECUTED;
- Riot var1/var2/var3 remain RIOT_OBSERVED_UNINTERPRETED;
- statPerk meanings/values are not exposed by the validated static source and remain NOT_EXPOSED;
- partial/unparsed text must not be treated as understood;
- semantic tags are factual parser evidence, not rune strength or recommendation labels;
- the full-catalog PASS validates the implemented invariants, not complete formal modeling of every live-game rune mechanic.

Rules:
- Prefer UNKNOWN / NOT_EXPOSED / PARTIAL / UNPARSED / INCOMPLETE over false certainty.
- Do not infer stat shard meanings or values from memory.
- Do not execute rune formulas or conditions from this layer.
- Do not infer rune strength, champion synergy, build advice, composition advice, or matchup recommendations directly from Phase 2C1-B facts.
- Do not modify Phase 2C1-B without a demonstrated factual correctness bug, Riot/Data Dragon compatibility requirement, strictly necessary downstream integration change, or explicit project review request.

Status:
FROZEN.

## Level-Resolved Champion Stat Formula Foundation Phase 2D v4 - FROZEN
Decision:
Freeze Level-Resolved Champion Stat Formula Foundation Phase 2D v4 as the factual standard-level champion native-stat calculation layer.

Scope:
- frozen Champion Knowledge Phase 2B1-C as the base/growth input source;
- native champion level-resolved stats for standard Summoner's Rift levels 1-18;
- attack-speed calculation using a separate Attack Speed Ratio source;
- explicit source and formula provenance;
- explicit unknown/unsupported handling for non-frozen extended-level behavior.

Validated baseline:
- level stats version champion_level_stats_phase2d_v4;
- Champion Knowledge version champion_knowledge_phase2b1_c_v1;
- Data Dragon 16.16.1, fr_FR;
- 173 champions;
- 3114 standard champion-level rows;
- 24912 RESOLVED_STANDARD_GROWTH non-AS rows;
- 6228 RESOLVED_FLAT non-AS rows;
- Attack Speed Ratio 173/173 resolved;
- 2907 RESOLVED_ATTACK_SPEED_WITH_RATIO;
- 173 RESOLVED_LEVEL1_ATTACK_SPEED;
- 34 RESOLVED_ZERO_GROWTH_ATTACK_SPEED;
- 0 Data Dragon / datamine cross-source mismatches;
- synthetic checks 7/7 PASS;
- precision checks 8/8 PASS;
- full catalog audit PASS;
- blocking issues 0;
- review items 0;
- FROZEN guard PASS.

Attack Speed Ratio source decision:
- do not infer `attackSpeedRatio = base attack speed`;
- do not depend on a moving `/latest` static-data source for the freeze baseline;
- use immutable `Haru-Kay/LeagueDatamines` commit `9245fd616059c6c658d1faa1029f0e18ea179154`, explicitly named `LIVE 26.16 (#17)`, as the patch-pinned Riot-game-file datamine source;
- cross-check exposed base attack speed and attack-speed growth fields against Data Dragon 16.16.1;
- preserve Jhin as an explicit native attack-speed special case.

Formula provenance decision:
- accept the 0.7025 / 0.0175 growth expression for standard levels 1-18 as `VALIDATED_COMMUNITY_FORMULA_WITH_RIOT_ANCHORS`;
- do not describe those coefficients as directly published by the Riot Developer Portal;
- retain level-1 and level-18 numeric invariants as validation anchors.

Levels 19-20:
- Riot 26.1 confirms a Top role quest can raise the level cap to 20;
- Phase 2D does not claim the standard native-stat growth expression is authoritatively frozen above level 18;
- native growth stats at levels 19-20 remain `UNRESOLVED_TOP_QUEST_LEVEL_FORMULA`;
- this is an accepted scope boundary, not a blocker for the standard-level Phase 2D freeze.

Out of scope:
- spell damage formulas;
- item/rune application;
- temporary champion states and buffs;
- resistance/penetration damage rules;
- shields;
- summoner-spell combat effects;
- Damage Engine;
- Burst / TTK;
- composition/build/rune recommendations;
- ML.

Rules:
- prefer unresolved/unsupported output over extrapolated certainty;
- preserve immutable source provenance for Attack Speed Ratio;
- do not reopen frozen Champion Knowledge to insert the missing ratio;
- do not modify Phase 2D without a demonstrated correctness bug, patch/source compatibility need, strictly necessary downstream integration change, or explicit project review.

Status:
FROZEN.

## Project review - Next factual layer after Phase 2D
Decision:
The next major factual layer is Combat Resistance / Penetration Rules Foundation Phase 2E.

Reason:
- Phase 2D now provides native champion stats by standard level.
- A future Damage Engine still lacks a validated generic contract for armor, magic resistance, resistance reduction, penetration, lethality, and post-mitigation resistance math.
- This generic math is more foundational than executing any one champion spell and can be validated independently.

Scope rule:
- Phase 2E must remain generic and deterministic.
- It must not execute champion spells, item passives, rune effects, crits, shields, damage modifiers, or Burst/TTK.
- Current lethality uses Riot Patch 14.1's 1:1 flat armor penetration rule.
- Community-documented resistance formulas/order retain explicit community provenance.
- Phase 2D and all earlier frozen layers remain untouched.

Freeze:
Not yet. Phase 2E requires implementation, tests, full audit, and project review.

## Combat Resistance / Penetration Rules Foundation Phase 2E v1 - FROZEN
Decision:
Freeze Phase 2E v1 as the generic factual resistance/reduction/penetration rules layer.

Reasons:
- synthetic checks PASS 12/12;
- precision checks PASS 10/10;
- full deterministic audit PASS;
- 141 resistance-multiplier sweep cases;
- 112 armor matrix cases;
- 112 magic-resistance matrix cases;
- 0 blocking issues;
- 0 review items;
- frozen-layer guard PASS;
- no previously frozen production module was modified.

Core rules:
- penetration must not fabricate negative resistance;
- flat resistance reduction may produce negative resistance;
- if reduction already yields non-positive resistance, later penetration layers do not create additional benefit;
- percentage effects stack multiplicatively;
- current lethality is 1:1 flat armor penetration;
- bonus armor penetration requires a known base/bonus split;
- explicit unresolved output is preferred to guessing missing armor components.

Provenance decision:
- Riot Patch 14.1 is the official source for current 1:1 lethality;
- generic resistance formulas and penetration ordering remain explicitly community-documented;
- do not relabel community formulas as Riot Developer Portal formulas.

Accepted scope boundary:
Phase 2E does not execute champion spells, item/rune effects, crits, damage modifiers, shields, executes, healing, on-hit ordering, Burst/TTK, recommendations, or ML.

Rules:
- use Phase 2E as a generic downstream dependency;
- do not duplicate or silently redefine its resistance/penetration math in later modules;
- do not modify Phase 2E without a demonstrated correctness bug, patch/rules compatibility need, strictly necessary downstream integration change, or explicit project review.

Status:
FROZEN.
