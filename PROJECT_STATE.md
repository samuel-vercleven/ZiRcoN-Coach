# ZiRcoN Coach - Project State

## Frozen analyzers
- Death Analyzer: v11 - FROZEN.
- Jungle Tempo / Pathing Analyzer: v17 - FROZEN.
- Objective Analyzer: v20 - FROZEN.
- Recall / Reset Analyzer: v21 - FROZEN.
- Build / Itemization Analyzer: v22 Phase 1 - FROZEN.

Frozen means: no retuning/refactor without a demonstrated correctness or integration bug or explicit project review request.

## In development
- Item Knowledge Base Phase 2A: implemented and awaiting project review.
- Status: REVIEW_REQUIRED, not FROZEN.
- Next major task remains for project review / TODO.md.

## Dataset
- Main historical validation set: 87 Jungle games with exploitable timelines.
- Queue 420.
- Primary profile: ZiRcoN1977#EUW.
- Windows / Python.

## Death Analyzer v11
- Historical-only scoring.
- Death volume and per-death Gold/XP costs separated.
- Association language only.
Known limits: minute-level Riot frames, overlapping episode costs, contextual trade semantics, chain percolation.

## Jungle Tempo / Pathing v17
- Global tempo outside death contamination.
- Personal FARMABLE pathing = own XP + Jungle CS.
- MIRRORED for neutral direct comparison.
- Time-local references.
- Boundary guard +/-60s.
- 1 weak minute = WATCH; sustained about 2+ min = pathing-hole candidate.
Known limits: no exact camps/routes; shop/reset proxy; lane-catch heuristic.

## Objective Analyzer v20
- Preparation + conversion windows.
- Gold/XP/JCS personal and relative.
- Death v11 + Tempo v17 integration.
- Directional before/after trade logic.
- Spatial contest evidence.
- Historical-only scoring, minimum 20 references.
Known limits: proximity != intent; close objective sequences may share fight context; compensation thresholds are heuristic.

## Recall / Reset Analyzer v21
Status: FROZEN by project review.

Design:
- Uses SHOP/RESET proxy from purchase clusters, not exact recall lifecycle.
- Separates post-death shop sequences from voluntary reset proxies.
- Analyzes about 120s before/after.
- Reentry Score is historical-only and measures observed post-reset production, not causal recall quality.
- Current Gold before reset is exploratory/contextual only.
- Objective proximity remains context only and is never an automatic player-mistake label.

Current technical state:
- Latest full runtime verification completed on 2026-08-17 on 87 Jungle games.
- Production v21 remains unchanged at SHOP_CLUSTER_GAP_SECONDS = 20.
- Production dataset: 891 shop/reset proxy sequences.
- Origins: 509 voluntary reset proxies, 382 post-death shops.
- Historical references: 339 CHAMPION_PHASE_ORIGIN_TIME, 282 PHASE_ORIGIN_TIME, 32 CHAMPION_PHASE_ORIGIN, 11 PHASE_ORIGIN, 227 WARMUP.
- Unscored reentries: 263 total; 227 warmup plus 36 with missing +120s post window.
- Global personal reentry measures previously showed robust Win/Loss association under existing validation; strongest was XP vs JGL/min after voluntary reset, Cliff +0.658, CV 77.8%, walk-forward 80.8%, FDR q 0.0006.

Final threshold-independent clustering audit:
- 24 consecutive player shop-cluster pairs had 20s < gap <= 45s.
- Classification no longer uses 20s/30s/45s or any gap cutoff; gap is reported only after classification.
- Audit-only classification: 13 SEPARATE_VISITS, 11 UNRESOLVED, 0 SAME_VISIT_CANDIDATE.
- Riot frame resolution: 13 same-frame pairs, 11 distinct-frame pairs.
- Evidence reasons: 11 same-frame UNRESOLVED, 6 player K/A/D events, 3 major objective/building events on distinct frames, 3 observable OUTSIDE_BASE intermediate frames, 1 resource-progression case.
- Gap-bin results after classification: 20-25s = 0 SAME / 1 SEPARATE / 6 UNRESOLVED; 25-30s = 0 / 1 / 2; 30-35s = 0 / 4 / 1; 35-40s = 0 / 2 / 1; 40-45s = 0 / 5 / 1.
- 20s production clustering threshold retained conservatively.
- Rationale: raising the threshold would merge some independently supported separate visits, while same-frame unresolved cases are insufficient evidence for merging.
- Objective <=5s technical check passed: 6/6 timings measured from cluster end, 6/6 objectives after complete cluster, 6/6 extraction/order checks OK.
- Target match EUW1_7951911875 remained stable: 7 sequences, 4 voluntary, 3 post-death, 0 near-threshold pairs, 2 tight-pre-objective proxies.

Permanent v21 limitations:
- Riot data does not expose a perfect recall lifecycle.
- Purchase clusters remain SHOP/RESET proxies.
- Same-frame Riot gaps may remain unresolved.
- Current Gold is exploratory context only.
- Objective proximity is context, not player fault.
- Reentry Score is not a causal recall-quality score.

Technical fixes / audit support:
- main.py can fall back to existing local SQLite history when Riot account/match lookup is unavailable.
- main.py configures stdout/stderr as UTF-8 to avoid Windows console encoding failures while rendering analyzer reports.
- analysis/reset_audit.py provides audit-only threshold-independent clustering diagnostics and threshold sensitivity; it does not change production logic.
- .gitignore ignores .env, .venv, *.db, __pycache__, and logs/ so local secrets, DBs, and logs are not staged accidentally.

## Build / Itemization Analyzer v22
Status: Phase 1 factual reconstruction - FROZEN by project review after Phase 1D.

Design:
- New UI-agnostic analyzer reconstructs factual item state from Riot timeline item events.
- Handles ITEM_PURCHASED, ITEM_SOLD, ITEM_UNDO, and ITEM_DESTROYED.
- Uses Data Dragon metadata for names, costs, tags, consumables, boots, and item `from` / `into` graph.
- Consumes component trees transitively, so held subcomponents are removed when a completed item is bought through an implicit intermediate component.
- Treats Data Dragon `consumeOnFull` consumables, such as elixirs, as consumed on purchase.
- Tracks a six-slot item multiset plus trinket state; exact slot ordering is not fabricated.
- Associates purchase events with frozen Recall / Reset v21 shop/reset proxy visit IDs for factual context only.
- Models confirmed non-purchase final grants separately from Riot-observed item transactions.
- Magical Footwear item 2422 is classified as RUNE_GRANT / MAGICAL_FOOTWEAR only when rune 8304 is present.
- Derived grant timing is stored as derived/inferred evidence, never as an observed Riot transaction.
- Destroyed-event audit is evidence-based and records before/after inventory state, same-timestamp events, previous/next item transactions, later repurchase, transformation candidates, final inventories, and classification evidence.
- Viego-specific handling is isolated to audit context; it does not change normal champion reconstruction.
- Undo now restores the actual components consumed by the undone purchase when Riot emits ITEM_UNDO after a completed-item purchase.
- Phase 1D adds generic inventory reliability states for future consumers: RELIABLE, AMBIGUOUS_TEMPORARY_STATE, UNRESOLVED_TRANSFORMATION.
- Unreliable intervals are marked explicitly instead of fabricating corrected item events.
- Future consumers must ignore or explicitly handle inventory states that are not RELIABLE.

Freeze baseline:
- `python main.py` completed on 2026-08-18 after v22 Phase 1D updates; this is the validated freeze baseline.
- Full Jungle history: 87 games, 4277 player item events.
- Event counts: 1536 purchases, 11 sells, 45 undo events, 2685 destroyed events.
- Final inventory validation: 86 EXACT, 1 EXACT_WITH_EXPLAINED_GRANT, 0 PARTIAL, 0 MISMATCH, 0 UNKNOWN.
- Observed exact final inventory rate: 98.9%.
- Observed or explained final inventory rate: 100.0%.
- Target match EUW1_7951911875: EXACT final inventory reconstruction.
- Target match EUW1_7836627546: EXACT_WITH_EXPLAINED_GRANT because rune 8304 Magical Footwear is present and final item 2422 has no Riot purchase/undo/sell event.
- EUW1_7836627546 derived grant timestamp: 09:45, DERIVED_INFERRED from Magical Footwear base timing and 3 observed takedowns.
- Non-purchase final grants: 1 match, source RUNE_GRANT, grant type MAGICAL_FOOTWEAR.
- ITEM_DESTROYED audit: 2685 total, 1085 confidently explained, 1600 remaining evidence records.
- Evidence-based destroyed classifications: 818 CONFIRMED_OR_STRONG_TEMPORARY_STATE, 658 UNRESOLVED_TEMPORARY_POSSIBLE, 79 MISSED_TRANSFORMATION, 45 CONSUMABLE_DESTROYED_NOT_HELD_RIOT_REPRESENTATION, 0 plain UNRESOLVED.
- MISSED_TRANSFORMATION root causes: 60 TEMPORARY_MECHANIC, 9 EVENT_ORDER_DUPLICATE, 8 VIEGO_TEMPORARY_POSSIBLE, 1 ALREADY_HANDLED_BY_PURCHASE_COMPONENT_CONSUMPTION, 1 REAL_MISSED_TRANSFORMATION.
- Held-before-destroy classifications: 512 UNRESOLVED_TEMPORARY_POSSIBLE and 3 MISSED_TRANSFORMATION.
- Not-held classifications: 818 CONFIRMED_OR_STRONG_TEMPORARY_STATE, 146 UNRESOLVED_TEMPORARY_POSSIBLE, 76 MISSED_TRANSFORMATION, 45 CONSUMABLE_DESTROYED_NOT_HELD_RIOT_REPRESENTATION.
- Viego audit: 9 games, 1384 ITEM_DESTROYED events, 1189 ambiguous events; evidence classifications are 605 UNRESOLVED_TEMPORARY_POSSIBLE, 572 CONFIRMED_OR_STRONG_TEMPORARY_STATE, 28 CONSUMABLE_DESTROYED_NOT_HELD_RIOT_REPRESENTATION, 12 MISSED_TRANSFORMATION.
- SELL_ITEM_NOT_RECONSTRUCTED_AS_HELD warnings: 0 after undo component-restore fix.
- Restored-component sell case resolved: EUW1_7839112939 Shyvana, undo Steelcaps at 15:33 restored Cloth Armor, later sold at 25:13.
- Intermediate contradiction audit: 68 component-consumed-after-ignored-destroy cases and 3 retained-after-missed-transformation cases.
- Phase 1D retained-after-missed details: 1 real non-Viego transformation interval and 2 Viego temporary-possible intervals.
- Inventory reliability intervals: 509 AMBIGUOUS_TEMPORARY_STATE and 47 UNRESOLVED_TRANSFORMATION.
- Reliability reasons: 506 RETAINED_TEMPORARY_STATE_POSSIBLE, 65 COMPONENT_CONSUMED_AFTER_IGNORED_DESTROY, 46 DERIVED_RUNE_GRANT_NOT_MATERIALIZED_AS_RIOT_EVENT, 3 RETAINED_AFTER_MISSED_TRANSFORMATION.
- Affected transaction states: 2635 RELIABLE, 1396 AMBIGUOUS_TEMPORARY_STATE, 246 UNRESOLVED_TRANSFORMATION.
- Major item milestone audit: 265 completed-major milestones, 0 unusual excluded-category milestones.

Permanent Phase 1 limitations:
- ITEM_DESTROYED does not globally imply permanent item removal.
- Normal ITEM_DESTROYED events are preserved as auditable AMBIGUOUS cases unless explained by same-timestamp component completion, consumable removal, jungle-item removal, or trinket-use handling.
- AMBIGUOUS_TEMPORARY_STATE intervals remain unreliable for factual item reasoning unless a future consumer explicitly handles them.
- UNRESOLVED_TRANSFORMATION intervals remain unreliable; one non-Viego REAL_MISSED_TRANSFORMATION interval is intentionally not materialized as a fabricated item event.
- Viego possession / copied inventory remains TEMPORARY_POSSESSION_INVENTORY_UNRELIABLE and uses the same generic reliability mechanism.
- Magical Footwear item 2422 is a RUNE_GRANT only when rune 8304 is present; its timestamp remains DERIVED_INFERRED and must not be presented as a Riot-observed ITEM event.
- Plain UNRESOLVED destroyed records are 0 in the Phase 1D baseline; the previous 13-case family was explained as consumable Riot representation, and the full current count is 45 consumable not-held representations.
- No LIKELY_REAL_REMOVAL evidence was found in the Phase 1D audit.

## Item Knowledge Base Phase 2A
Status: implemented, REVIEW_REQUIRED, not FROZEN.

Purpose:
- UI-agnostic, patch-aware factual knowledge layer for all Data Dragon items.
- Answers what an item contains/does according to patch-aware Data Dragon data.
- Does not use personal history, Win/Loss statistics, champions, compositions, recommendations, item scores, or ML.

Implementation:
- New package: knowledge/.
- Main module: knowledge/item_knowledge.py.
- Synthetic checks: knowledge/item_knowledge_synthetic_checks.py.
- Reuses riot/data_dragon.py for version and item catalog loading.
- Preserves raw Data Dragon facts per item: raw description, plaintext, raw stats, raw effect fields, gold, tags, maps, components/upgrades, consumed fields, and audit metadata.
- Resolves requested game version to Data Dragon version with explicit status: LATEST, EXACT_VERSION, EXACT_PATCH, FALLBACK_LATEST, or NO_VERSIONS_AVAILABLE.
- Normalizes reliable stats into canonical fields while preserving source field, confidence, and Data Dragon version.
- Preserves unmapped structured stats as UNKNOWN instead of discarding them.
- Cleans item HTML descriptions and extracts stats/passive/active/rules sections where exposed.
- Extracts factual mechanics with evidence and confidence; description-derived effects remain DESCRIPTION_EXPLICIT, not recommendation logic.
- Keeps unknown description mechanics as UNPARSED_EFFECT_TEXT.
- Builds item graph facts: direct components, recursive component tree, direct upgrades, final upgrade descendants, item depth, component gold contribution, combine cost where derivable, and graph issues.
- Classifies applicability without deleting records: Summoner's Rift purchasable, boots, starter/basic component, jungle starter, consumable, trinket, special/generated, mode-specific/non-SR, champion-specific, non-purchasable, special recipe.

Real Data Dragon audit baseline:
- Command: python -m knowledge.item_knowledge.
- Locale: fr_FR.
- Resolved Data Dragon version: 16.16.1.
- Total item records: 868.
- Purchasable Summoner's Rift items: 254.
- Items with normalized stats: 655.
- Items with extracted effects: 480.
- Items with description-only effects: 386.
- Items with unparsed effect text: 279.
- Items with UNKNOWN metadata: 0.
- Items with unknown raw stats preserved: 0.
- Graph inconsistencies: 0.
- Duplicate IDs: 0.
- Duplicate names: present in Data Dragon across variants/modes and reported for transparency, not deduplicated.
- Mode-specific / non-SR items: 552.
- Champion-specific items: 7.
- Non-purchasable items: 172.
- Representative diagnostics coverage: 18/18 required item families.

Coverage highlights:
- Canonical stats found include health, ability_haste, attack_damage, ability_power, armor, magic_resistance, attack_speed_percent, mana, percent_move_speed, critical_strike_chance, mana_regen, health_regen, lethality, flat_move_speed, life_steal, omnivamp, tenacity, magic_penetration_flat, armor_penetration_percent, and magic_penetration_percent.
- Extracted effect families include ON_HIT_DAMAGE, MOVEMENT_SPEED_TRIGGER, SLOW, STACKING_EFFECT, LIFE_STEAL_EFFECT, OMNIVAMP_EFFECT, CRITICAL_STRIKE_EFFECT, PERCENT_MAX_HEALTH_DAMAGE, TENACITY, active effects, TRANSFORMATION, HARD_CC, GRIEVOUS_WOUNDS, HEAL, SPELLBLADE, QUEST_OR_SPECIAL_MECHANIC, TRUE_DAMAGE, EXECUTE, LIFELINE_SHIELD, CLEANSE, STASIS, SPELL_SHIELD, penetration mechanics, and SHIELD_REDUCTION.

Known Phase 2A limitations:
- Description parsing is factual evidence extraction, not validated gameplay advice.
- DESCRIPTION_EXPLICIT effects remain parser-derived from Data Dragon text and must stay auditable through evidence_text.
- 279 items still contain UNPARSED_EFFECT_TEXT; future consumers must explicitly handle or ignore those fragments.
- Duplicate item names are preserved because Data Dragon exposes separate item IDs/variants.
- No champion semantic knowledge, composition analysis, build recommendation, GOOD/BAD label, item score, personal win-rate adjustment, or ML has been started.
- Phase 2A is ready for project review, not freeze.

## Architecture
- main.py remains a dev/integration harness.
- Final UI later with PySide6.
- Analysis modules should remain UI-agnostic.
- Itemization v22 logic lives in analysis/itemization_analyzer.py; synthetic checks live in analysis/itemization_synthetic_checks.py.
- Item Knowledge Base Phase 2A lives in knowledge/item_knowledge.py; synthetic checks live in knowledge/item_knowledge_synthetic_checks.py.

## Handoff rule
Codex must update this file after each completed task.
