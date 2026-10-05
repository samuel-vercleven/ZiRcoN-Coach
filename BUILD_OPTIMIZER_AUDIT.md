# Build Optimizer v1 — audit

## Patch 26.19 compatibility review — 2026-10-05

- Riot's current release is [26.19](https://www.leagueoflegends.com/en-us/news/game-updates/league-of-legends-patch-26-19-notes/),
  with exact Data Dragon version 16.19.1, verified against its versions API.
- Exact French [item](https://ddragon.leagueoflegends.com/cdn/16.19.1/data/fr_FR/item.json)
  and [champion](https://ddragon.leagueoflegends.com/cdn/16.19.1/data/fr_FR/champion.json)
  catalogs are cached and included in the portable delivery. No latest-patch fallback.
- All 20 reviewed whitelist records are fully identical to 16.18.1, including
  descriptions, stats, tags, prices, recipes and applicability. The five verified
  recall/quest marker records retain their relevant identity/applicability facts.
  Patch notes change support quest items outside this recommendation whitelist.
- New 16.19 semantic admission additionally requires a reviewed SHA-256 of the
  complete raw item record (canonical UTF-8 JSON, sorted keys, compact separators).
  A same-price, same-recipe tooltip/stat/applicability change therefore abstains.
  Older patch behavior and all FROZEN foundations stay unchanged.
- All 173 champion catalog records admit their reviewed or generic class profile;
  this does not imply 173 individually reviewed champion builds.
- Controlled cases cover six champions, real recipes, alternatives, legal purchases,
  score recomposition, future-data mutation and the UI presentation bridge.
  Recipe audit covers 2,795 cases on 16.19, including budgets and inventory slots.
- There is no real 16.19 game in the current 143-game local history. New-patch
  verification is controlled, while historical replay covers existing older games.
  Insufficient same-patch prior matches still abstain; no cross-patch borrowing.

Catalog provenance (SHA-256 of JSON with sorted keys, ensure_ascii=False,
default separators; distinct from the compact item fingerprint convention):
items `41853c6c272a50f763888b273bae98c83fba7fdb5bcf1df74fdfa2adb79488e3`;
champions `7f9b1adad10a0b3009d198a51553733f18037234c993071d0f236996683ece52`.

## Scope and frozen boundary

The original Viego contextual pass extended only `build_optimizer/`. The later
all-champion coverage extension also updates its local presentation/replay
bridge, but does not modify frozen analyzer foundations. Death v11, Tempo v17, Objectives
v20, Reset v21, Itemization v22 and knowledge foundations 2A–2I remain
FROZEN. The existing prefix projection, frozen Item Knowledge and v22 recipe
consumption are reused; no UI, network access, ML, damage simulator or hidden
text parsing is added.

The product contract remains `DETERMINISTIC_CONTEXTUAL_HEURISTIC_V1`:
deterministic, bounded and explainable, but neither a combat calculation nor a
proof of an optimal build. A recommendation is conditional on
`IF_SHOPPING_NOW`; shop access itself remains unmodeled.

## Champion coverage extension — REVIEW_REQUIRED

The frozen v22 match itemization reconstruction is champion-agnostic. The
contextual recommender now retains its reviewed Shyvana and Viego profiles and
adds a generic fallback for any champion with exact-patch Data Dragon class
tags (`Fighter`, `Mage`, `Assassin`, `Tank`, `Marksman`, `Support`). Generic
champion fit is deliberately class-level, not a champion-specific build or kit
model. It uses the existing exact-patch reviewed item declarations as a broad
candidate whitelist and generalizes enemy armor/MR/frontline response by item
traits. Unknown class metadata and unsupported patches still abstain.

The fallback does not make every item relevant to every champion, nor does it
validate build quality. Candidate/semantic coverage is reported separately.
The audited local catalogs now include exact patches 16.8, 16.9, 16.11, 16.12,
16.14, 16.15, 16.16, 16.17, 16.18 and 16.19. All existing Shyvana fingerprints match
these catalogs; Viego has 11/12 matching item fingerprints on 16.8–16.15 (item
6610 fails closed) and 12/12 on 16.16–16.19. The all-champion replay and human
gameplay review remain required before acceptance or freeze.

## Viego possession audit

`python -m build_optimizer.viego_audit` reads 30 local Viego SoloQ timelines.
It observes 527 own shop transactions: 514 `ITEM_PURCHASED`, 2 `ITEM_SOLD`
and 11 `ITEM_UNDO`, alongside 4,279 own `ITEM_DESTROYED` events and 271 Viego
kill opportunities. No event, frame or champion-stat field names a possession
state, start/end interval or inventory owner.

The admitted contract is therefore deliberately narrow:

```text
PERMANENT_SHOP_INVENTORY
  = prefix reconstruction of this player's ITEM_PURCHASED / ITEM_SOLD / ITEM_UNDO
  ≠ possession runtime inventory
  ≠ proof of current shop access
```

`ITEM_DESTROYED` is excluded for Viego because its high-volume discontinuities
are possession/runtime-sensitive. Viego's own frame `championStats` are marked
`VIEGO_FRAME_STATS_POSSESSION_SENSITIVE` and removed from personal scoring.
Enemy frame observations remain independently scoped and can provide only the
declared contextual signals. No possession passive/reset/damage calculation is
claimed.

## Prefix reliability follow-up — 2026-09-30

Some non-Viego timeline `ITEM_DESTROYED` rows represent action/progression
markers rather than shop inventory. Exact-patch catalog checks across all nine
supported local patches verified IDs 1201 (mid quest), 1203 (support quest),
1204 (jungle quest), 2001 (recall) and 2002 (enhanced recall) as generated,
non-purchasable, and outside the store. The prefix projector ignores only these
exact ID/name/catalog-fingerprint combinations. Unknown items, ordinary item
destructions, catalog blockers and changed marker records still fail closed.

Magical Footwear uses the frozen itemization helper's derived grant timing over
only takedowns observed by the snapshot. A derived grant strictly after the
snapshot is noted but does not contaminate that earlier permanent inventory
prefix. At or before the grant (or when timing is not reliable), inventory
uncertainty remains. No rune-granted boots purchase event is synthesized and a
derived timestamp is not represented as an observed timeline event.

The 2026-09-30 all-champion replay therefore grows from 92 to 172 nonempty rows
on the same 143-game / 572-snapshot corpus, with 400 remaining abstentions.
It emits on 9/11 locally played champions; Viego contributes 60 rows. All
emitted plans pass exact recipe, budget/slot, temporal-prefix, score and reason
traceability checks. This is improved data admission, not a gameplay-quality
claim; human review and NO FREEZE remain required.

## Exact-patch semantic and purchase contracts

`viego_build_profile_v1` allows twelve reviewed major-item semantic profiles:
Blade of the Ruined King, Kraken Slayer, Terminus, Black Cleaver, Lord
Dominik's Regards, Death's Dance, Maw of Malmortius, Sundered Sky, Trinity
Force, Wit's End, Immortal Shieldbow and The Collector (catalog applicability
can still structurally reject a profile). Their traits are literal declarations,
not runtime substring parsing. Every candidate must match exact patch, ID,
price and direct recipe fingerprints on 16.9/16.16/16.17/16.18.

The whitelist spans AD, attack speed, on-hit, crit, sustained damage,
anti-HP, percentage/flat armor penetration, health, armor, MR, lifesteal and
survivability. Unsupported patches, stale prices/recipes, unsupported items,
duplicate owned targets, unresolved inventory/gold, blocked graph, unknown
restriction or search truncation fail closed.

## Contextual decision contract

Champion fit uses centrally declared Viego traits (AD, AS, on-hit, sustained
damage, lifesteal and crit), so different candidates do not all receive 30/30.
Enemy response is directional and explicit: frontline rewards anti-HP/sustained
damage, armor rewards percentage armor penetration, low-frontline rewards
crit/burst, and very high AD/AP threat rewards compatible armor/MR defense.
Current reviewed-build overlap, observed team-gold state, recipe spike,
recipe coverage and exact-whitelist feasibility form the remaining bounded
contributions. All outputs expose a recomputable score breakdown and only cite
reasons attached to contributions.

The replay invoice now uses frozen v22 `_slot_count`, preventing a false slot
failure where stacked consumables had been counted as separate slots. It still
rejects non-stackable over-capacity states, bad component credits, invalid IDs,
budget overruns and off-recipe steps.
