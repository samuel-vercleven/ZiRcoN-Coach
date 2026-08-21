# ZiRcoN Coach — TODO

## Current task
COMPLETED - Freeze Level-Resolved Champion Stat Formula Foundation Phase 2D v4.

## Completion status
FROZEN.

Validated freeze baseline:
- Level stats version: `champion_level_stats_phase2d_v4`.
- Champion Knowledge input: `champion_knowledge_phase2b1_c_v1`.
- Data Dragon: 16.16.1.
- Locale: fr_FR.
- Champions: 173.
- Standard level rows 1-18: 3114.
- Synthetic checks: PASS 7/7.
- Precision checks: PASS 8/8.
- Full catalog audit: PASS.
- Blocking issues: 0.
- Review items: 0.
- Attack Speed Ratio source: `PINNED_LEAGUE_DATAMINE_LIVE_26_16`.
- Attack Speed Ratios: 173/173 resolved.
- Cross-source mismatches: 0.
- Standard attack-speed rows: 2907 ratio-resolved, 173 level-1 resolved, 34 zero-growth resolved.
- FROZEN guard: PASS.

Permanent limitations:
- Standard native-stat formula is frozen for levels 1-18 only.
- Formula provenance remains `VALIDATED_COMMUNITY_FORMULA_WITH_RIOT_ANCHORS`, not a claim that Riot Developer Portal publishes the numeric coefficients directly.
- Levels 19-20 native growth remain `UNRESOLVED_TOP_QUEST_LEVEL_FORMULA`.
- No item/rune application, champion spell formulas, buffs, penetration, shields, damage, Burst/TTK, recommendations, or ML is part of Phase 2D.

Freeze rule:
Do not modify Phase 2D unless there is a demonstrated factual correctness bug, patch/source compatibility requirement, strictly necessary downstream integration change, or explicit project review request.

## Next major task
PROJECT REVIEW - Define the next factual combat-input / formula layer.

Before starting Combat / Damage Engine, decide and validate the next missing factual dependency. Do not jump directly to Burst/TTK, composition recommendations, build recommendations, or ML.

## Completion status
FROZEN.

Validated freeze baseline:
- Level stats version: `champion_level_stats_phase2d_v4`.
- Champion Knowledge input: `champion_knowledge_phase2b1_c_v1`.
- Data Dragon: 16.16.1.
- Locale: fr_FR.
- Champions: 173.
- Standard level rows 1-18: 3114.
- Synthetic checks: PASS 7/7.
- Precision checks: PASS 8/8.
- Full catalog audit: PASS.
- Blocking issues: 0.
- Review items: 0.
- Attack Speed Ratio source: `PINNED_LEAGUE_DATAMINE_LIVE_26_16`.
- Attack Speed Ratios: 173/173 resolved.
- Cross-source mismatches: 0.
- Standard attack-speed rows: 2907 ratio-resolved, 173 level-1 resolved, 34 zero-growth resolved.
- FROZEN guard: PASS.

Permanent limitations:
- Standard native-stat formula is frozen for levels 1-18 only.
- Formula provenance remains `VALIDATED_COMMUNITY_FORMULA_WITH_RIOT_ANCHORS`, not a claim that Riot Developer Portal publishes the numeric coefficients directly.
- Levels 19-20 native growth remain `UNRESOLVED_TOP_QUEST_LEVEL_FORMULA`.
- No item/rune application, champion spell formulas, buffs, penetration, shields, damage, Burst/TTK, recommendations, or ML is part of Phase 2D.

Freeze rule:
Do not modify Phase 2D unless there is a demonstrated factual correctness bug, patch/source compatibility requirement, strictly necessary downstream integration change, or explicit project review request.

## Next major task
PROJECT REVIEW - Define the next factual combat-input / formula layer.

Before starting Combat / Damage Engine, decide and validate the next missing factual dependency. Do not jump directly to Burst/TTK, composition recommendations, build recommendations, or ML.

## Goal

Harden Rune Knowledge Phase 2C1 before freeze.

The factual static foundation is accepted:

- runesReforged schema loading;
- patch-aware static catalog resolution;
- raw tree / slot / rune preservation;
- descriptions;
- numeric fragments;
- conditions;
- var1 / var2 / var3 preservation;
- statPerk non-interpretation;
- Magical Footwear compatibility;
- RUNE_FORMULA_INCOMPLETE policy.

Do NOT redesign these parts without a demonstrated bug.

---

# A — Historical rune mapping must be patch-aware

Current historical audit links every observed perk ID against one current
catalog.

This is insufficient for historical correctness.

For each historical match:

1. read the Riot gameVersion;
2. derive the requested major.minor patch;
3. resolve the corresponding Data Dragon version;
4. use the rune catalog for THAT patch;
5. link observed perk IDs against that patch-specific catalog.

Cache catalogs by resolved Data Dragon version.

Do not repeatedly download the same patch.

Explicit statuses must distinguish:

- PATCH_EXACT_RUNE_LINK
- PATCH_EXACT_STYLE_LINK
- PATCH_CATALOG_UNAVAILABLE
- PATCH_FALLBACK_USED
- PERK_NOT_FOUND_ON_MATCH_PATCH
- STYLE_NOT_FOUND_ON_MATCH_PATCH
- GAME_VERSION_UNKNOWN

A current-catalog match is not enough to call historical data patch-correct.

If Data Dragon no longer provides an old requested version:

preserve the observed Riot ID and mark the linkage unresolved / fallback.

Never silently reinterpret it with latest data.

---

# B — Historical patch audit

Report:

- unique Riot game versions;
- unique major.minor patches;
- resolved Data Dragon versions;
- matches per patch;
- selections with exact-patch static linkage;
- selections using fallback;
- selections unresolved because patch catalog is unavailable;
- perk IDs absent from their actual match patch;
- style IDs absent from their actual match patch.

Compare this to the old:

6240 LINKED_RUNE_CATALOG

and clearly explain how many are truly patch-validated.

Do not use Win/Loss.

---

# C — Synthetic historical patch tests

Create deterministic no-network fixtures with at least two patches.

Example:

Patch A:
- rune 9001 exists as Rune Alpha

Patch B:
- rune 9001 changed/removed/replaced

A match from Patch A must use Patch A's static knowledge.

It must never silently inherit Patch B/latest semantics.

Test:

- exact-patch resolution;
- missing historical rune;
- unavailable patch;
- fallback explicit;
- unknown gameVersion.

---

# D — Add a factual observed rune-page resolver

Create a reusable consumer-facing factual resolver, not just aggregate audit.

Conceptually:

resolve_observed_rune_page(participant_perks, catalog)

or a patch-aware equivalent.

Return an auditable structure containing:

- primary style ID;
- secondary style ID;
- observed style order / description;
- each selected perk ID;
- linked static rune record when valid;
- link status;
- var1;
- var2;
- var3;
- meaning_status = RIOT_OBSERVED_UNINTERPRETED;
- offense statPerk ID;
- flex statPerk ID;
- defense statPerk ID;
- statPerk mapping status;
- Data Dragon version used;
- Riot match version.

This resolver must be usable later by the Combat Engine.

It must NOT calculate rune effects.

---

# E — Keystone vs minor rune

Add explicit factual rune-role metadata.

Audit current Data Dragon structure first.

If the current Riot schema consistently represents keystones as slot 0,
derive:

- KEYSTONE
- MINOR_RUNE

with provenance such as:

DDRAGON_TREE_SLOT_STRUCTURE

Do not hardcode rune IDs.

Important:

PRIMARY and SECONDARY are NOT intrinsic rune properties.

A rune's tree may be selected as primary in one page and secondary in another.

Store primary/secondary only in observed rune-page context.

Report the structural evidence used to derive KEYSTONE.

---

# F — Conservative semantic completeness

Bring Rune Knowledge to the same standard as frozen Item and Champion Knowledge.

A fragment containing one recognized mechanic must NOT automatically mean
the whole fragment is understood.

Example:

"Inflige 100 dégâts et applique un effet solaire inconnu."

Expected:

- damage extracted;
- unknown mechanic preserved;
- PARTIALLY_STRUCTURED.

Handle multiple mechanics in the same sentence conservatively.

Preserve:

- original source text;
- recognized effects;
- unresolved clauses;
- partial details.

Numeric fragments or detected conditions alone must NOT prove that the
semantic meaning of the text is FULLY_STRUCTURED.

It is acceptable for the current:

18 FULLY_STRUCTURED
44 PARTIALLY_STRUCTURED

distribution to become more conservative.

Do not optimize counts.

---

# G — Stat semantics must distinguish modification from reference

Audit these current semantic families carefully:

- HEALTH
- ARMOR
- MAGIC_RESISTANCE
- ATTACK_SPEED
- ABILITY_HASTE
- ADAPTIVE_FORCE
- MANA
- ENERGY

A simple mention of a stat must not automatically mean the rune grants or
modifies that stat.

Examples:

"deal more damage to targets with more health"
must NOT mean the rune grants HEALTH.

"deal damage based on enemy armor"
must NOT mean the player gains ARMOR.

"gain 10 armor"
may represent an actual self stat gain.

Use one of these conservative approaches:

1. require explicit stat modification evidence; or
2. distinguish structured roles such as:
   - STAT_GAIN
   - STAT_REDUCTION_TARGET
   - STAT_REFERENCE
   - STAT_SCALING_REFERENCE
   - UNKNOWN_STAT_RELATION

Do not invent ownership.

Source text and subject/target evidence must remain auditable.

---

# H — Condition semantics remain non-executable

Preserve current:

execution_status = NOT_EXECUTED

Do not calculate triggers.

But ensure a condition record does not imply that the complete mechanic has
been understood.

Condition extraction and semantic completeness are separate concepts.

---

# I — Stat shards remain unresolved

Do NOT hardcode meanings or values for:

5005
5008
5007
5001
5010
5011
5013

unless an official validated source is actually introduced by project review.

For Phase 2C1-B keep current conservative status:

STAT_PERK_NOT_EXPOSED_BY_DDRAGON_RUNE_CATALOG

Historical observed IDs remain useful facts.

---

# J — Magical Footwear

Preserve:

rune 8304
→ static Rune Knowledge record

and compatibility with frozen Itemization:

item 2422
→ RUNE_GRANT
→ DERIVED_INFERRED

Do not modify frozen Itemization v22.

---

# K — Full real audit

Rerun the current static rune catalog.

Report:

- trees;
- slots;
- runes;
- keystones;
- minor runes;
- semantic effects;
- stat modification vs reference counts;
- numeric fragments;
- conditions;
- FULLY / PARTIALLY / UNPARSED;
- formula statuses;
- duplicate IDs;
- malformed records.

Then rerun historical audit with patch-aware mapping.

Report exact patch-validation coverage.

---

# L — Frozen boundaries

Do NOT modify:

- Death Analyzer v11
- Jungle Tempo / Pathing v17
- Objective Analyzer v20
- Recall / Reset Analyzer v21
- Build / Itemization Analyzer v22 Phase 1
- Item Knowledge Base Phase 2A
- Champion Knowledge Base Phase 2B1

If a frozen layer requires modification:

stop and return REVIEW_REQUIRED.

---

# Do NOT start

- stat shard hardcoded meanings;
- exact stats by level;
- executable rune formulas;
- executable champion formulas;
- damage simulation;
- combos;
- Burst / TTK;
- composition analysis;
- rune recommendations;
- build recommendations;
- ML.

---

# Freeze criteria

Rune Knowledge Phase 2C1 becomes freeze-ready if:

- historical rune linkage is patch-aware;
- cross-patch linkage never silently uses current/latest semantics;
- reusable observed rune-page resolution exists;
- keystone/minor structure is explicit with provenance;
- primary/secondary remains page context, not rune identity;
- semantic completeness is conservative;
- stat references are not confused with self stat grants;
- statPerks remain explicit unknowns;
- Magical Footwear compatibility remains valid;
- all tests and real audits pass;
- frozen layers remain untouched.

UNKNOWN / PARTIAL is preferred to a false fact.

---

# Testing

Run:

- py_compile;
- Rune Knowledge synthetic checks;
- Rune Knowledge precision checks;
- patch-aware history fixtures;
- same-sentence partial tests;
- stat reference/modification positive and negative tests;
- full current rune catalog audit;
- full historical patch-aware rune audit.

pytest is not required if unavailable.

If using a direct test runner, report exactly what ran.

---

# Reporting

Update:

- PROJECT_STATE.md
- TODO.md → COMPLETED
- LAST_RUN.md

LAST_RUN must report:

- static baseline;
- before/after completeness;
- keystone/minor counts;
- stat semantic precision findings;
- unique historical patches;
- exact-patch linkage rate;
- fallback/unresolved linkage;
- observed rune-page resolver validation;
- statPerk coverage;
- Magical Footwear compatibility;
- tests;
- limitations;
- freeze-readiness.

Finish:

REVIEW_REQUIRED

Do not freeze Phase 2C1 yourself.

---

# Git

Commit and push.

Suggested commit:

Harden rune knowledge patch and semantic precision