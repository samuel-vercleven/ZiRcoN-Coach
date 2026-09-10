# Build Optimizer v1 — audit

## Scope and frozen boundary

This pass extends only `build_optimizer/`. Death v11, Tempo v17, Objectives
v20, Reset v21, Itemization v22 and knowledge foundations 2A–2I remain
FROZEN. The existing prefix projection, frozen Item Knowledge and v22 recipe
consumption are reused; no UI, network access, ML, damage simulator or hidden
text parsing is added.

The product contract remains `DETERMINISTIC_CONTEXTUAL_HEURISTIC_V1`:
deterministic, bounded and explainable, but neither a combat calculation nor a
proof of an optimal build. A recommendation is conditional on
`IF_SHOPPING_NOW`; shop access itself remains unmodeled.

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
