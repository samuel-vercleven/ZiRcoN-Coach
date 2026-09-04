# ZiRcoN Coach - Project State

## Frozen modules / knowledge layers
- Death Analyzer: v11 - FROZEN.
- Jungle Tempo / Pathing Analyzer: v17 - FROZEN.
- Objective Analyzer: v20 - FROZEN.
- Recall / Reset Analyzer: v21 - FROZEN.
- Build / Itemization Analyzer: v22 Phase 1 - FROZEN.
- Item Knowledge Base: Phase 2A - FROZEN.
- Champion Knowledge Base: Phase 2B1 - FROZEN.
- Rune Knowledge Base: Phase 2C1-B - FROZEN.
- Level-Resolved Champion Stat Formula Foundation: Phase 2D v4 - FROZEN.
- Combat Resistance / Penetration Rules Foundation: Phase 2E v1 - FROZEN.
- Champion Spell Calculation Source Foundation: Phase 2F v1 - FROZEN.
- Executable Combat Formula Foundation: Phase 2G v2 - FROZEN.

- Champion Spell Stat Reference Semantics Foundation: Phase 2H v1 - FROZEN.
- Champion Spell Stat Owner Semantics Foundation: Phase 2I v1 - FROZEN.

Frozen means: no retuning/refactor without a demonstrated correctness or integration bug or explicit project review request.

## In development
- No production module is currently under development.
- Any successor phase, stat execution without new owner proof, Burst/TTK, item/rune execution, combo engine, recommendations, ML, and UI remain out of scope.

## Stat Owner Semantics Foundation Phase 2I v1
- Status: FROZEN by project review; version `champion_spell_stat_owner_semantics_phase2i_v1`, top foundation `stat_scaling_formula_foundation_phase2i_v1`.
- Latest official-freeze runtime: `python main.py` PASS on 2026-09-04 in 2.77s; compilation, 10/10 synthetic checks, 61/61 precision assertions, provenance research audit, full owner audit, top Phase 2I audit, and expanded FROZEN guard passed.
- Research conclusion: reverse-engineered interfaces and independent implementations show that stat parts read a unit/champion supplied by the evaluation context, but no patch-specific client call-site proof establishes that this unit is universally the caster or target.
- Exact inventory: all 569 Phase 2H stat rows preserved with class/signature, graph/root/parent/ancestor context, siblings, child/subpart structure, tooltip linkage, frozen stat/formula results, and pinned provenance.
- Owner contracts: 88 exact `class + signature + structural context` groups; 86 contracts are `OWNER_CONTEXT_DEPENDENT` and 2 hashed-field variants are `OWNER_UNRESOLVED`.
- Occurrence statuses: 567 `OWNER_CONTEXT_DEPENDENT`, 2 `OWNER_UNRESOLVED`, 0 validated caster, 0 validated target, 0 validated source-level/other, 0 strongly supported, 0 ambiguous, and 0 contradicted.
- Owner execution eligibility: 0/569. The accepted gate blockers are 467 owner, 101 frozen Phase 2H stat ID, and 1 frozen Phase 2H formula ID.
- Exact stat signature counts: NamedDataValue 279, Coefficient 271, SubPart 19 across eight signatures; the two signatures containing unknown `0xa8cb9c14` remain unresolved.
- Tooltip audit: 461/569 stat rows have an exact pinned calculation-token link in the serialized tooltip data.
- Formula replay: the 1,443-calculation inventory and frozen Phase 2G baseline (13 resolved, 720 partial, 493 unsupported signature, 217 unsupported class) were confirmed. Numeric Phase 2I replay was correctly not run because the accepted gate has no validated real owner contract.
- Safety: 0 caster guesses, 0 target-as-owner substitutions, 0 stat arithmetic, 0 non-validated stat/formula executions, 0 partial snapshot exact-use, and 0 FROZEN modifications.
- Compatibility: Phase 2G and Phase 2H production/validation files are unchanged. `main.py` guards all seven Phase 2I production/validation files in addition to every earlier frozen file.
- Accepted limitations: new patch-specific runtime/call-site evidence is required before any future owner execution change; AP remains outside execution because frozen Phase 2H did not promote raw `mStat=0`.

## Champion Spell Stat Reference Semantics Foundation Phase 2H v1
- Status: FROZEN by project review; version `champion_spell_stat_semantics_phase2h_v1`.
- Latest official-freeze runtime: `python main.py` PASS on 2026-08-31 (2.02s); compile, 21/21 synthetic checks, 31/31 precision assertions, research audit, exact inventory audit, full semantics audit, and the expanded FROZEN guard all passed.
- Exact source remains Phase 2F commit `9245fd616059c6c658d1faa1029f0e18ea179154`, Data Dragon 16.16.1/fr_FR. Public provenance is recorded with immutable commits where available; structural `UInt8` evidence is not treated as enum meaning.
- Inventory invariant: 885 field occurrences = 569 `mStat` + 316 explicit `mStatFormula`; 16 explicit raw stat IDs: `[1, 2, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 18, 29, 31]`.
- Execution-eligible stat mappings: `1 -> ARMOR`, `2 -> ATTACK_DAMAGE`, `12 -> HEALTH`; 468/569 occurrences (82.25%).
- Strongly supported but non-executable: `4 -> ATTACK_SPEED`, `6 -> MAGIC_RESISTANCE`, `7 -> MOVE_SPEED`, `8 -> CRITICAL_STRIKE_CHANCE`, `9 -> CRITICAL_STRIKE_DAMAGE_MULTIPLIER`, `10 -> COOLDOWN_REDUCTION`, `18 -> LIFE_STEAL`, `29 -> PHYSICAL_LETHALITY`, `31 -> ATTACK_RANGE`.
- Unresolved raw stat IDs: `[13, 14, 15, 16]`; no neighbour-position inference is allowed. Raw ID 0 is preserved as a legitimate enum value when present but remains below execution eligibility without an explicit primary occurrence.
- Effective `mStatFormula` values are `[0, 1, 2]`: `0 -> TOTAL_STAT` and `2 -> BONUS_STAT` are validated for exact pinned fixtures; value 1 is `CONTRADICTED` by incompatible public tables and remains non-executable. Validated formula coverage is 568/569 (99.82%).
- Ownership: 0 caster, 0 target, 0 source-level, 0 context-dependent, 569 unresolved. Therefore real fully composed snapshot references remain 0 and no stat-based formula execution was introduced.
- Six Phase 2G fields can be composed only after future owner proof: armor/armor bonus, AD total/bonus, and max/bonus health. Internal `BASE_STAT` is not equated to Phase 2G native-at-level fields.
- AbilityResource is isolated: 8 class nodes, one explicit raw `mAbilityResource=4`, all `RESOURCE_ENUM_RESEARCH_ONLY`.
- Safety audit: 0 key-name-only mappings admitted, 0 ambiguous/contradicted mappings in execution maps, 0 owner assumptions, 0 FROZEN modifications.
- Compatibility: all Phase 2G v2 production and validation files remain unchanged; `main.py` guards all seven Phase 2H production/validation files and runs only the Phase 2H validation stack plus the FROZEN guard.
- Accepted frozen limitation: IDs 13-16, formula 1, resource enum semantics, and all owner identities remain non-executable. Do not expand coverage without a reviewed, patch-specific proof.

## Executable Combat Formula Foundation Phase 2G v2
- Status: FROZEN by project review.
- Version: `combat_formula_foundation_phase2g_v2`.
- Latest real runtime: `python main.py` PASS on 2026-08-23 (325.65s); every Phase 2G synthetic, precision, individual real audit, top audit, and FROZEN guard passed after freeze.
- Frozen inputs remained unchanged: Item 2A-C v1, Champion 2B1-C v1, Rune 2C1-B v3, Level Stats 2D v4, Resistance 2E v1, and Spell Source 2F v1.
- Pinned source invariants: 173 champions, 692 Q/W/E/R slots, 1,443 calculations, 5,318 graph nodes, 25 classes, Data Dragon 16.16.1/fr_FR, exact commit `9245fd616059c6c658d1faa1029f0e18ea179154`.
- Taxonomy: 109 observed structural signatures and six exact executable signatures. Arithmetic is fail-closed for any unregistered field/signature; no arithmetic occurred under an unregistered signature.
- DataValue audit: 1,464/1,829 exact references resolved; 361 not found and 4 unsupported shapes; no fuzzy matching.
- Stat-reference audit: 885 occurrences across 16 IDs; 0 mapped and 16 unresolved because no authoritative enum/owner mapping was established.
- Formula evaluator: 13 RESOLVED, 720 PARTIALLY_RESOLVED, 493 UNSUPPORTED_SIGNATURE, 217 UNSUPPORTED_CLASS; 0 unexpected exceptions.
- Static snapshot audit: 6,920 rows across all 173 champions and levels 1/6/11/18 with representative item sets; 4,844 fully resolved and 2,076 partial. Description-derived ability haste, lethality, armor penetration %, and magic penetration % are explicitly excluded/partial rather than silently represented as zero.
- Percentage penetration preserves source multiplicity; the deterministic 30% + 20% regression passes as 44% and 56 effective armor from 100 through frozen Phase 2E.
- Damage evidence across 692 spells: 345 high confidence, 195 multiple candidates, 125 not identified, 27 insufficient. Evidence tiers: 791 component-local structural links, 40 key-name-only candidates, and 4 spell-level-type-only cases.
- Damage execution: 0 RAW_DAMAGE_RESOLVED and 831 DAMAGE_UNRESOLVED; consequently 0 post-mitigation real components and 0 real totals. Key text alone can never emit raw damage.
- Cast metadata: cooldown 680/692 resolved, adjusted cooldown 680 resolved / 12 unresolved, raw cost 568/692 resolved, range 661/692 resolved. Incomplete ability haste withholds adjusted cooldown without invalidating independent exact facts.
- Total composability requires a structured `COMPOSABILITY_VALIDATED` decision covering every component, carrying evidence and `PROJECT_VALIDATED` provenance. A bare boolean or caller assertion cannot emit a total.
- Optional `.cache/zircon` catalog cache is exact-keyed and checksum-validated; it is ignored and never changes Phase 2F semantics.
- Known limitations: no validated stat enum mapping; conditional mechanics, excluded description-derived item stats, rune effects, ticks, alternate forms, mixed damage, and totals remain unresolved unless exact evidence and project-validated contracts exist.
- Freeze rule: do not modify the Phase 2G files protected by `main.py` without a demonstrated correctness/integration bug or explicit project review request. Do not infer Phase 2H from this freeze.

## Champion Spell Calculation Source Foundation Phase 2F
- Status: FROZEN by project review.
- Version: `champion_spell_source_phase2f_v1`.
- Latest real runtime: `python main.py` PASS on 2026-08-22 (83.69s).
- Source provenance: community export/datamine of Riot game files, pinned to `Haru-Kay/LeagueDatamines` commit `9245fd616059c6c658d1faa1029f0e18ea179154` (`LIVE 26.16 (#17)`), target patch 16.16 / Riot 26.16.
- Frozen Champion Knowledge cross-check: `champion_knowledge_phase2b1_c_v1`, Data Dragon 16.16.1, locale fr_FR; 173 champions and 692 Q/W/E/R records.
- Real source audit: 173/173 champions; 692/692 primary slots; 692 exact-key mappings; 0 objectPath fallbacks; 0 missing or ambiguous slots; 0 source failures.
- Structure inventory: 631 slots with calculations, 61 without; 1,443 raw calculation records; 5,318 dictionary graph nodes (4,687 with `~class`, 631 without); 25 uninterpreted calculation classes; 5,063 raw DataValues; 0 malformed graphs.
- Empty `mSpellCalculations = {}` is explicit `NO_CALCULATIONS_EXPOSED`; classless dictionaries are preserved with `NO_CALCULATION_CLASS_EXPOSED` rather than discarded.
- Validation: synthetic checks PASS 10/10, precision checks PASS 4/4, full audit PASS, FROZEN guard PASS.
- Design boundary: preserves raw spell graphs and all observed fields/classes without evaluating formulas, stats, scaling, or damage.
- Compatibility: `main.py` now guards all frozen Phase 2E files in addition to the existing frozen layers.
- Freeze baseline: the accepted v1 source/structure contract is read-only for Phase 2G.

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

## Rune Knowledge Base Phase 2C1-B
Status: FROZEN by project review after the refined stat-semantics full-catalog validation.

Purpose:
- UI-agnostic, patch-aware factual knowledge layer for Data Dragon runes and Riot-observed perk selections.
- Preserves rune trees/styles, slots, IDs, keys, icons, names, shortDesc, longDesc, cleaned descriptions, raw rune JSON, raw style/slot JSON, numeric fragments, condition text, conservative semantic evidence, unresolved text, and provenance.
- Links Riot match `perks.styles[].selections[].perk` IDs to the static rune catalog using the match patch.
- Audits `perks.statPerks.offense`, `perks.statPerks.flex`, and `perks.statPerks.defense` separately without inventing shard meanings or values.
- Does not calculate executable rune formulas, champion level stats, damage, Burst/TTK, composition effects, rune recommendations, item recommendations, or ML.

Implementation:
- Main module: knowledge/rune_knowledge.py.
- Synthetic checks: knowledge/rune_knowledge_synthetic_checks.py.
- Precision checks: knowledge/rune_knowledge_precision_checks.py.
- Full-catalog audit: knowledge/rune_knowledge_full_audit.py.
- Development harness: main.py.
- Historical rune linking is patch-aware and never silently falls back to latest when a historical patch catalog is unavailable.
- KEYSTONE vs MINOR is derived structurally from Data Dragon slot position with provenance.
- PRIMARY vs SECONDARY is preserved as Riot page context and is never used to infer rune role.
- Semantic parsing is explicitly fr_FR-only; unsupported locales preserve raw text and skip French semantic parsing.
- Conditions are stored as source text with `execution_status = NOT_EXECUTED`.
- Riot `var1`, `var2`, and `var3` remain `RIOT_OBSERVED_UNINTERPRETED`.
- All rune formulas remain `RUNE_FORMULA_INCOMPLETE`.
- Magical Footwear 8304 compatibility with frozen Itemization v22 is source-contract-only: item 2422 remains RUNE_GRANT with DERIVED_INFERRED timing, not an observed Riot purchase.

Validated freeze baseline:
- Commit carrying validated code: 5efcbd1555195e473dfca7d33b4d8ab23268f3f6.
- Rune knowledge version: rune_knowledge_phase2c1_b_v3.
- Data Dragon version: 16.16.1.
- Locale: fr_FR.
- Total rune trees/styles: 5.
- Total slots: 20.
- Total rune records: 62.
- Full catalog audited: 62/62.
- Synthetic checks: PASS 13/13.
- Precision checks: PASS 10/10.
- Real Rune Knowledge audit: PASS.
- Full catalog audit: PASS.
- Full catalog blocking issues: 0.
- Full catalog review cases: 0.
- Legacy generic stat tags: 0.
- Previously frozen module guard: PASS.
- Historical raw JSON audited: 104 matches.
- Participants audited: 1040.
- Historical rune selections: 6240.
- Rune catalog links: 6240 LINKED_RUNE_CATALOG, 0 UNKNOWN_PERK_ID.
- Rune style links: 2080 LINKED_RUNE_STYLE, 0 UNKNOWN_RUNE_STYLE_ID.
- Historical rune page resolution remained fully resolved on the validated dataset.
- Magical Footwear observed: 211 participant selections across 97 matches.
- Magical Footwear itemization compatibility: PASS.

Validated semantic relation families:
- HEALTH: STAT_GAIN, THRESHOLD_REFERENCE, SCALING_REFERENCE, REFERENCE.
- ARMOR: STAT_GAIN, REDUCTION_TARGET, SCALING_REFERENCE, REFERENCE.
- MAGIC_RESISTANCE: STAT_GAIN, REDUCTION_TARGET, SCALING_REFERENCE, REFERENCE.
- MOVE_SPEED: STAT_GAIN, BONUS_AMPLIFICATION, REFERENCE.
- ATTACK_SPEED: STAT_GAIN, SCALING_REFERENCE, REFERENCE.
- ABILITY_HASTE: STAT_GAIN, REFERENCE.
- ADAPTIVE_FORCE: STAT_GAIN, REFERENCE.
- MANA: MANA_MAX_STAT_GAIN, MANA_RESTORE, MANA_REFERENCE.
- ENERGY / TENACITY are not fabricated when no validated relation case exists in the current audited catalog.

Permanent Phase 2C1-B limitations:
- Data Dragon rune descriptions are factual text, not a complete executable gameplay-rules contract.
- All 62 runes intentionally remain RUNE_FORMULA_INCOMPLETE.
- Numeric fragments are evidence and must not be treated as executable formulas.
- Rune conditions are not evaluated by this layer.
- Riot `var1` / `var2` / `var3` remain uninterpreted telemetry.
- Data Dragon `runesReforged.json` does not expose validated stat-shard meanings/values for this layer; do not infer them from memory.
- PARTIALLY_STRUCTURED_RUNE_TEXT and UNPARSED_RUNE_TEXT are explicit uncertainty and must be handled or ignored by future consumers.
- Semantic effect tags are parser-derived factual evidence with provenance, not strength labels or gameplay recommendations.
- The full-catalog PASS means the audited invariants and semantic checks passed; it does not turn Data Dragon text into a complete formal rules engine.

Freeze rule:
- Do not modify Phase 2C1-B without a demonstrated factual correctness bug, Riot/Data Dragon compatibility requirement, strictly necessary downstream integration change, or explicit project review request.

## Architecture
- main.py remains a dev/integration harness.
- Final UI later with PySide6.
- Analysis modules should remain UI-agnostic.
- Itemization v22 logic lives in analysis/itemization_analyzer.py; synthetic checks live in analysis/itemization_synthetic_checks.py.
- Item Knowledge Base Phase 2A lives in knowledge/item_knowledge.py; synthetic checks live in knowledge/item_knowledge_synthetic_checks.py and knowledge/item_knowledge_precision_checks.py.
- Champion Knowledge Base Phase 2B1 lives in knowledge/champion_knowledge.py; synthetic checks live in knowledge/champion_knowledge_synthetic_checks.py and knowledge/champion_knowledge_precision_checks.py.
- Rune Knowledge Base Phase 2C1-B is FROZEN in knowledge/rune_knowledge.py; validation lives in knowledge/rune_knowledge_synthetic_checks.py, knowledge/rune_knowledge_precision_checks.py, and knowledge/rune_knowledge_full_audit.py.

## Handoff rule
Codex must update this file after each completed task.

## Level-Resolved Champion Stat Formula Foundation Phase 2D v4
Status: FROZEN by project review.

Purpose:
- Consume frozen Champion Knowledge Phase 2B1-C base/growth facts and resolve factual champion native stats at a requested standard Summoner's Rift level.
- Provide a factual prerequisite for later combat/formula work without starting a Damage Engine.

Validated scope:
- 173 champions.
- Standard levels 1-18: 3114 champion-level rows.
- Data Dragon: 16.16.1.
- Locale: fr_FR.
- Level stats version: champion_level_stats_phase2d_v4.
- Formula provenance: VALIDATED_COMMUNITY_FORMULA_WITH_RIOT_ANCHORS.
- Standard growth expression:
  `base + growth * (level - 1) * (0.7025 + 0.0175 * (level - 1))`.
- Level-1 invariant: resolved growth stats equal base values.
- Level-18 invariant: resolved growth stats equal `base + 17 * growth`.
- Native growth fields resolved for health, health regen, resource, resource regen, attack damage, armor, magic resistance, and crit.
- Flat move speed and attack range remain factual non-growth values.

Attack Speed:
- Attack Speed Ratio is not fabricated from Data Dragon base attack speed.
- Ratio source is an immutable LIVE 26.16 Riot-game-file datamine snapshot:
  `Haru-Kay/LeagueDatamines` commit `9245fd616059c6c658d1faa1029f0e18ea179154`.
- Source status: PINNED_LEAGUE_DATAMINE_LIVE_26_16.
- Attack ratios resolved: 173/173.
- Cross-source Data Dragon / datamine mismatches: 0.
- Attack-speed statuses across standard levels:
  - 2907 RESOLVED_ATTACK_SPEED_WITH_RATIO;
  - 173 RESOLVED_LEVEL1_ATTACK_SPEED;
  - 34 RESOLVED_ZERO_GROWTH_ATTACK_SPEED.
- Jhin native attack-speed growth remains an explicit special-case formula rather than abusing a zero datamined ratio.

Validation:
- Compilation: PASS.
- Synthetic checks: PASS 7/7.
- Precision checks: PASS 8/8.
- Full catalog audit: PASS.
- Blocking issues: 0.
- Review items: 0.
- FROZEN guard: PASS.

Permanent limitations:
- The numeric 0.7025 / 0.0175 coefficients are preserved as a community-documented formula with Riot terminology and numeric anchors; they are not mislabeled as a Riot Developer Portal publication.
- Riot 26.1 allows the Top role quest to raise the level cap to 20, but Phase 2D does not freeze a native-stat growth coefficient contract above level 18.
- Native growth stats at levels 19-20 remain `UNRESOLVED_TOP_QUEST_LEVEL_FORMULA`.
- Flat non-growth facts may still be returned at levels 19-20.
- This layer does not apply item stats, rune stats/effects, spell formulas, buffs/debuffs, penetration, shields, damage, Burst/TTK, recommendations, or ML.

Freeze rule:
- Do not modify Phase 2D production files unless there is a demonstrated factual correctness bug, source/patch compatibility requirement, strictly necessary downstream integration change, or explicit project review request.

## Combat Resistance / Penetration Rules Foundation Phase 2E
Status: FROZEN by project review.

Purpose:
- Deterministic generic resistance/reduction/penetration math required before champion spell execution or a full Damage Engine.
- UI-agnostic and independent from champion-specific, item-specific, and rune-specific effect execution.

Validated baseline:
- Version: combat_resistance_phase2e_v1.
- Synthetic checks: PASS 12/12.
- Precision checks: PASS 10/10.
- Full deterministic audit: PASS.
- Resistance multiplier sweep: 141 cases.
- Armor matrix: 112 cases.
- Magic-resistance matrix: 112 cases.
- Blocking issues: 0.
- Review items: 0.
- FROZEN guard: PASS.

Validated factual contract:
- positive armor/MR multiplier: `100 / (100 + R)`;
- negative resistance branch preserved;
- flat resistance reduction before percentage resistance reduction;
- percentage penetration before flat penetration;
- percentage reduction / penetration sources combine multiplicatively;
- penetration cannot create negative effective resistance;
- resistance reduction can create negative resistance;
- current lethality rule: 1 lethality = 1 flat armor penetration;
- percentage bonus armor penetration requires a known base/bonus armor split;
- missing base/bonus split returns explicit `BONUS_ARMOR_COMPONENT_REQUIRED`;
- true damage bypasses armor/MR within this resistance layer.

Precision anchors:
- 100 resistance -> 0.5 damage multiplier.
- -100 resistance -> 1.5 damage multiplier.
- 30% + 20% -> 44% combined effect.
- 18 lethality -> 18 flat armor penetration.
- 300 armor = 100 base + 200 bonus, then 30 flat reduction, 30% reduction, 45% bonus armor penetration, 10 flat penetration -> 122.3 effective armor.

Provenance:
- lethality 1:1: Riot official Patch 14.1.
- resistance formulas and penetration ordering: explicitly marked COMMUNITY_DOCUMENTED rather than mislabeled as Riot Developer Portal formulas.

Permanent limitations:
- no champion spell formulas;
- no item passive/active execution;
- no rune execution;
- no crit rules;
- no damage amplification/reduction modifiers;
- no shields;
- no executes;
- no healing;
- no on-hit/on-attack ordering;
- no temporary champion-state execution;
- no Burst/TTK;
- no recommendations;
- no ML.

Freeze rule:
- Do not modify Phase 2E production files unless there is a demonstrated factual correctness bug, patch/rules compatibility requirement, strictly necessary downstream integration change, or explicit project review request.
