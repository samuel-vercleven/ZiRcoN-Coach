# ZiRcoN Coach - Project State

## Frozen modules / knowledge layers
- Death Analyzer: v11 - FROZEN.
- Jungle Tempo / Pathing Analyzer: v17 - FROZEN.
- Objective Analyzer: v20 - FROZEN.
- Recall / Reset Analyzer: v21 - FROZEN.
- Build / Itemization Analyzer: v22 Phase 1 - FROZEN.
- Item Knowledge Base: Phase 2A - FROZEN.
- Champion Knowledge Base: Phase 2B1 - FROZEN.

Frozen means: no retuning/refactor without a demonstrated correctness or integration bug or explicit project review request.

## In development
- No active analyzer/knowledge layer is currently under development.
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
Status: FROZEN by project review after Phase 2A-C.

Purpose:
- UI-agnostic, patch-aware factual knowledge layer for all Data Dragon items.
- Answers what an item contains/does according to patch-aware Data Dragon data.
- Does not use personal history, Win/Loss statistics, champions, compositions, recommendations, item scores, or ML.
- Freeze covers factual item knowledge only.
- Phase 2B champion knowledge, rune knowledge, spell formulas, composition analysis, damage simulation, Burst/TTK, contextual builds, recommendations, and ML remain out of scope.

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
- Phase 2A-B prioritizes semantic precision over recall for high-risk families.
- Phase 2A-C makes section completeness conservative: a matched phrase inside a sentence is not enough to mark the whole section FULLY_PARSED.
- Same-sentence clauses split by simple connectors such as commas, "et", "puis", "mais", "ainsi que", and "tout en" must each have matched semantic evidence, otherwise the section is PARTIALLY_PARSED.
- PARTIALLY_PARSED records preserve original section text, unresolved clauses, matched effects, matched texts, and partial fragment details.
- Semantic parse details now expose section text and unresolved_text for future consumers.
- `OnHit` Data Dragon tags no longer imply ON_HIT_DAMAGE without explicit damage evidence.
- `*DAMAGE` semantic effects require damage action evidence in the same section/clause.
- EXECUTE excludes quest-completion wording such as "achève une quête".
- ACTIVE_SHIELD distinguishes shield grants from enemy shield reduction.
- CLEANSE requires CC/debuff/removal context.
- TRANSFORMATION no longer fires from generic "améliore" wording alone.
- Locale contract is explicit: semantic description parsing is SUPPORTED for fr_FR and UNSUPPORTED_LOCALE otherwise; raw data remains available.
- Keeps unknown description mechanics as UNPARSED_EFFECT_TEXT and mixed sections as PARTIALLY_PARSED_EFFECT_TEXT.
- Builds item graph facts: direct components, recursive component tree preserving multiplicity, recursive component counts, direct upgrades, final upgrade descendants, item depth, component gold contribution, combine cost where derivable, and graph issues.
- Classifies applicability without deleting records: Summoner's Rift purchasable, boots, starter/basic component, jungle starter, consumable, trinket, special/generated, mode-specific/non-SR, champion-specific, non-purchasable, special recipe.

Freeze baseline:
- Command: python -m knowledge.item_knowledge.
- Locale: fr_FR.
- Resolved Data Dragon version: 16.16.1.
- Item knowledge version: item_knowledge_phase2a_c_v1.
- Total item records: 868.
- Purchasable Summoner's Rift items: 254.
- Items with normalized stats: 655.
- Items with extracted effects: 414.
- Items with description-only effects: 357.
- Items with unparsed effect text: 443.
- Items with UNKNOWN metadata: 0.
- Items with unknown raw stats preserved: 0.
- Description effect sections fully parsed: 96.
- Description effect sections partially parsed: 253.
- Description effect sections completely unparsed: 384.
- Semantic parser statuses: SUPPORTED 868.
- Graph inconsistencies: 0.
- Same-sentence partial parse fragments with a recognized effect and unresolved clauses: 201.
- Recipes with repeated direct components: 45.
- Recipes with repeated recursive components: 170.
- Duplicate IDs: 0.
- Duplicate names: present in Data Dragon across variants/modes and reported for transparency, not deduplicated.
- Mode-specific / non-SR items: 552.
- Champion-specific items: 7.
- Non-purchasable items: 172.
- Representative diagnostics coverage: 18/18 required item families.

Coverage highlights:
- Canonical stats found include health, ability_haste, attack_damage, ability_power, armor, magic_resistance, attack_speed_percent, mana, percent_move_speed, critical_strike_chance, mana_regen, health_regen, lethality, flat_move_speed, life_steal, omnivamp, tenacity, magic_penetration_flat, armor_penetration_percent, and magic_penetration_percent.
- Extracted effect families include SLOW, LIFE_STEAL_EFFECT, MOVEMENT_SPEED_TRIGGER, STACKING_EFFECT, OMNIVAMP_EFFECT, CRITICAL_STRIKE_EFFECT, TENACITY, ON_HIT_DAMAGE, ACTIVE_DAMAGE, TRANSFORMATION, HARD_CC, GRIEVOUS_WOUNDS, HEAL, SPELLBLADE, QUEST_OR_SPECIAL_MECHANIC, TRUE_DAMAGE, LIFELINE_SHIELD, ACTIVE_MOVEMENT, MISSING_HEALTH_SCALING, PERCENT_MAX_HEALTH_DAMAGE, ACTIVE_SHIELD, CLEANSE, EXECUTE, PERCENT_CURRENT_HEALTH_DAMAGE, STASIS, SPELL_SHIELD, penetration mechanics, and SHIELD_REDUCTION.
- Targeted semantic deltas vs Phase 2A baseline: ON_HIT_DAMAGE -130, PERCENT_MAX_HEALTH_DAMAGE -36, MOVEMENT_SPEED_TRIGGER -20, STACKING_EFFECT -11, ACTIVE_DAMAGE -6, EXECUTE -6, TRANSFORMATION -6, CLEANSE -3, ACTIVE_SHIELD -2, PERCENT_CURRENT_HEALTH_DAMAGE -1, HARD_CC 0.

Known Phase 2A limitations:
- Description parsing is factual evidence extraction, not validated gameplay advice.
- DESCRIPTION_EXPLICIT effects remain parser-derived from Data Dragon text and must stay auditable through evidence_text.
- 443 items still contain UNPARSED_EFFECT_TEXT / PARTIALLY_PARSED_EFFECT_TEXT; future consumers must explicitly handle or ignore those fragments.
- FULLY_PARSED counts intentionally decreased after Phase 2A-C; this is preferred over silently treating unrecognized same-sentence mechanics as understood.
- UNKNOWN, UNPARSED_EFFECT_TEXT, and PARTIALLY_PARSED_EFFECT_TEXT are preferred to false certainty.
- The 201 same-sentence partial cases are intentionally preserved as incomplete rather than over-parsed.
- Raw Data Dragon descriptions, raw stats, normalized facts, effect evidence, and Data Dragon version provenance remain authoritative for audit.
- Repeated direct and recursive components preserve multiplicity and must not be deduplicated away by consumers.
- Duplicate item names are preserved because Data Dragon exposes separate item IDs/variants.
- Semantic parser support is currently explicit for fr_FR only.
- No champion semantic knowledge, composition analysis, build recommendation, GOOD/BAD label, item score, personal win-rate adjustment, or ML has been started.
- Phase 2A is FROZEN; do not modify it without a demonstrated factual correctness bug, Riot/Data Dragon compatibility need, strictly necessary downstream integration change, or explicit project review request.

## Champion Knowledge Base Phase 2B1
Status: FROZEN by project review after Phase 2B1-C.

Purpose:
- UI-agnostic, patch-aware factual knowledge layer for all Data Dragon champions.
- Preserves champion identity, raw individual champion JSON, base stats, growth fields, passive, spells, tooltips, cooldowns, costs, ranges, effects, effectBurn, vars, images, metadata, semantic evidence, unresolved text, placeholder resolution, formula fragments, and complexity flags.
- Does not calculate level-resolved stats, damage, combos, Burst/TTK, composition scores, champion strength, item recommendations, runes, or ML.

Implementation:
- Main module: knowledge/champion_knowledge.py.
- Synthetic checks: knowledge/champion_knowledge_synthetic_checks.py.
- Precision checks: knowledge/champion_knowledge_precision_checks.py.
- Loads champion.json plus every individual champion JSON from Data Dragon.
- Normalizes base and growth stat fields with provenance; growth fields are stored as factual per-level fields, not evaluated into level stats.
- Q/W/E/R slot assignment is inferred only from Data Dragon array order when the champion has exactly 4 spells.
- Tooltip placeholders preserve original text and add annotated resolution records for eN effectBurn placeholders and aN/fN vars when resolvable.
- All final spell formulas remain non-executable; unresolved or incomplete formula data is marked FORMULA_INCOMPLETE.
- Semantic parsing remains conservative and fr_FR-only.
- Phase 2B1-B evaluates sensitive semantics at clause/fragment level where practical: damage type, percent-health damage, shield, heal, reveal, execute, and damage reduction.
- Phase 2B1-C separates generic transformation semantics from champion form/kit complexity.
- TRANSFORMATION means a transformation mechanic is factually described; it must not be interpreted as champion form change by future consumers.
- ALTERNATE_FORM_POSSIBLE requires separate subject/state evidence that the champion itself enters or owns an alternate form, named form, stance, or kit state.
- Rejected sensitive matches are preserved in partial/unparsed records so source text is not silently treated as understood.
- SHIELD now requires grant/create/obtain/apply/absorb/protect evidence, not the word "bouclier" alone.
- DAMAGE_TYPE_UNRESOLVED now requires outgoing damage action and excludes defensive/reduction/immunity/absorbed-damage contexts.
- Percent-health damage now requires HP reference and outgoing damage evidence in the same clause/mechanic.
- REVEAL no longer uses generic "vision" wording.
- Generic "transforme" and generic "forme de" wording no longer create ALTERNATE_FORM_POSSIBLE by themselves.
- Transformations of damage, targets, marks, resources, effects, terrain, summoned entities, seeds/plants, weapons, or abilities remain possible TRANSFORMATION semantics but are not champion alternate-form evidence.
- Complexity flags are conservative warnings with provenance, not exhaustive truth.
- No champion-specific production hacks are part of the frozen layer.

Real Data Dragon audit baseline:
- Command: python -m knowledge.champion_knowledge.
- Locale: fr_FR.
- Resolved Data Dragon version: 16.16.1.
- Champion knowledge version: champion_knowledge_phase2b1_c_v1.
- Total champions: 173.
- Individual champion files loaded: 173.
- Missing champion detail files: 0.
- Champions with normalized base/growth stats: 173.
- Passive records: 173.
- Total spells: 692.
- Spell-count distribution: 4 spells = 173 champions.
- Champions not represented as normal 4-spell kits: 0.
- Slot assignment uncertain records: 0.
- Canonical stat coverage: all 20 mapped base/growth fields present for all 173 champions.
- Unknown stat fields: 0.
- Placeholder resolution: 4479 UNKNOWN_PLACEHOLDER intentionally preserved, 33 RESOLVED_EFFECT_BURN, 10 UNRESOLVED_VAR.
- UNKNOWN placeholder families: 2902 likely_formula_related_but_unresolved, 1257 formatting_or_display_placeholder, 308 unknown, 12 calculated_or_custom_ddragon_placeholder.
- Top UNKNOWN keys: spellmodifierdescriptionappend 692, cost 567, abilityresourcename 557, totaldamage 200, slowduration 90.
- Formula status counts: 692 FORMULA_INCOMPLETE by design.
- Formula fragment status counts: 6920 FORMULA_FRAGMENT_STRUCTURED, 4489 FORMULA_INCOMPLETE.
- Semantic parse completeness: 61 FULLY_PARSED, 1297 PARTIALLY_PARSED, 199 COMPLETELY_UNPARSED.
- Sensitive semantic counts vs Phase 2B1 baseline: SHIELD 128 -> 41, DAMAGE_TYPE_UNRESOLVED 314 -> 359, PERCENT_MAX_HEALTH_DAMAGE 83 -> 62, PERCENT_CURRENT_HEALTH_DAMAGE 13 -> 13, MISSING_HEALTH_DAMAGE 48 -> 21, REVEAL 68 -> 27, TRANSFORMATION 40 -> 53.
- Current semantic highlights: MAGIC_DAMAGE 554, DAMAGE_TYPE_UNRESOLVED 359, PHYSICAL_DAMAGE 271, SHIELD 41, REVEAL 27, TRUE_DAMAGE 25.
- Complexity flags after Phase 2B1-C: 154 STANDARD_KIT, 19 COMPLEX_KIT_UNDERMODELED, 16 ALTERNATE_FORM_POSSIBLE, 3 COPIED_OR_DYNAMIC_ABILITY.
- Phase 2B1-B non-standard baseline audited: 31 champion cases.
- Baseline audit status after subject-aware classification: 13 CONFIRMED_COMPLEX_MECHANIC, 6 PLAUSIBLE_BUT_UNDERMODELED, 12 FALSE_POSITIVE.
- Remaining ALTERNATE_FORM_POSSIBLE champions: Anivia, Bel'Veth, Elise, Galio, Gnar, Irelia, Jax, Kennen, Maokai, Nidalee, Rammus, Senna, Shyvana, Swain, Udyr, Volibear.
- Remaining COPIED_OR_DYNAMIC_ABILITY champions: Wukong, Sylas, Viego.
- Removed Phase 2B1-B alternate-form false positives by generic evidence rules: Ambessa, Ashe, Aurelion Sol, Jarvan IV, Jayce, Jhin, K'Santé, Lissandra, Lulu, Yorick, Zeri, Zyra.
- Targeted audit examples: Lissandra enemy-servant transformation, Lulu polymorph target, Zeri projectile-to-laser, and Zyra seed-to-plant are no longer champion alternate-form evidence; Nidalee is retained via named form evidence using fr_FR "couguar".
- Xerath "dévoile sa forme véritable" and Renekton generic true/tyrant-form wording are not newly promoted unless the text shows the champion entering/activating the form under the current generic rules.
- Metadata warnings: 0.
- Representative diagnostics include required fixed champions plus shield, healing, transformation, copied/dynamic, true damage, percent-health damage, hard CC, and stealth/reveal categories.

Permanent Phase 2B1 limitations:
- Data Dragon champion descriptions are not executable combat formulas.
- Level-resolved champion stats are not calculated yet.
- All 692 spells remain FORMULA_INCOMPLETE until a later validated formula/combat layer resolves them.
- UNKNOWN_PLACEHOLDER keys are audited but not artificially resolved.
- Semantic effects are parser-derived factual evidence, not champion strength labels.
- DAMAGE_TYPE_UNRESOLVED count increased because clause-local parsing now records untyped outgoing damage clauses even when nearby tooltip text exposes typed damage elsewhere; this is evidence granularity, not damage simulation.
- TRANSFORMATION count remains generic factual transformation evidence and is intentionally separate from champion alternate-form complexity.
- Some true kit-state cases may remain STANDARD_KIT when Data Dragon wording describes transformed weapons/abilities rather than an explicit champion-owned form/state; these Data Dragon false negatives are accepted for the frozen baseline.
- Tags such as Fighter, Tank, Assassin, Mage, or Support remain Riot metadata only and are not recommendations.
- Complex kits are flagged generically and intentionally under-modeled rather than solved with champion-specific architecture.
- Do not add champion-specific hacks to improve complexity coverage.
- Do not modify Phase 2B1 without a demonstrated factual correctness bug, Riot/Data Dragon compatibility need, strictly necessary downstream integration change, or explicit project review request.

## Architecture
- main.py remains a dev/integration harness.
- Final UI later with PySide6.
- Analysis modules should remain UI-agnostic.
- Itemization v22 logic lives in analysis/itemization_analyzer.py; synthetic checks live in analysis/itemization_synthetic_checks.py.
- Item Knowledge Base Phase 2A lives in knowledge/item_knowledge.py; synthetic checks live in knowledge/item_knowledge_synthetic_checks.py and knowledge/item_knowledge_precision_checks.py.
- Champion Knowledge Base Phase 2B1 lives in knowledge/champion_knowledge.py; synthetic checks live in knowledge/champion_knowledge_synthetic_checks.py and knowledge/champion_knowledge_precision_checks.py.

## Handoff rule
Codex must update this file after each completed task.
