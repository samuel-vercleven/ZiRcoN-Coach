# ZiRcoN Coach - TODO

## Current task
COMPLETED - Phase 2C1 Rune Knowledge Base.

## Completion status
REVIEW_REQUIRED.

Implemented factual, patch-aware Rune Knowledge Base Phase 2C1:
- Data Dragon `runesReforged.json` schema inspected and documented.
- Rune trees/styles, slots, IDs, names, keys, icons, shortDesc, longDesc, cleaned text, raw rune JSON, raw style/slot JSON, numeric fragments, condition text, parser evidence, and unresolved text are preserved.
- All 62 runes are marked RUNE_FORMULA_INCOMPLETE by design.
- fr_FR semantic parser contract is explicit; unsupported locales preserve raw text and skip French semantic parsing.
- Conditions are structured as text with NOT_EXECUTED status.
- Riot match `perks.styles[].selections[].perk` IDs are linked to the static Data Dragon catalog.
- Riot `var1`, `var2`, and `var3` are preserved as RIOT_OBSERVED_UNINTERPRETED.
- `perks.statPerks.offense/flex/defense` are audited separately and not assigned names or values from memory.
- Magical Footwear 8304 compatibility with frozen Itemization v22 was verified without modifying itemization logic: item 2422 remains RUNE_GRANT with DERIVED_INFERRED timing only.

Validation completed:
- Python compile passed for the new Rune Knowledge files.
- 15 direct synthetic/precision checks passed.
- Real Data Dragon catalogue audit passed.
- Historical observed-rune audit passed on 104 matches / 1040 participants / 6240 rune selections.

Baseline requiring project review:
- Data Dragon version: 16.16.1.
- Rune records: 62.
- Styles: 5.
- Slots: 20.
- Rune catalog link statuses: 6240 LINKED_RUNE_CATALOG, 0 UNKNOWN_PERK_ID.
- statPerks are not exposed in `runesReforged.json`.
- statPerks.offense: 5005 552, 5008 378, 5007 110.
- statPerks.flex: 5001 90, 5008 905, 5010 45.
- statPerks.defense: 5001 793, 5011 216, 5013 31.
- Magical Footwear observed: 211 participant selections across 97 matches.

Do not start Phase 2D, rune formulas, stat shard meaning, Burst/TTK, damage,
composition analysis, recommendations, or ML until project review defines the
next task.
