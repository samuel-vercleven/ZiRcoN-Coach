# ZiRcoN Coach - TODO

## Current task
IN DEVELOPMENT - Combat Resistance / Penetration Rules Foundation Phase 2E.

## Why this is the next factual layer
Phase 2D now resolves native champion stats by level, but the project still has
no validated generic contract for turning armor / magic resistance plus
reductions and penetration into effective resistance and post-mitigation
physical / magic damage.

Do not start champion spell execution or a full Damage Engine before this
generic rules layer is validated.

## Scope
Create a UI-agnostic deterministic factual rules layer for:

- physical, magic, and true damage resistance behavior;
- armor and magic-resistance damage multipliers;
- negative resistance behavior;
- flat armor / MR reduction;
- percentage armor / MR reduction;
- percentage armor / magic penetration;
- flat armor / magic penetration;
- current lethality behavior;
- percentage bonus armor penetration when the base/bonus armor split is known;
- multiplicative stacking of percentage reduction / penetration sources;
- explicit calculation stages and provenance.

## Required current rule
Riot Patch 14.1 changed lethality to:

`1 lethality = 1 flat armor penetration`

at every level.

Do NOT reintroduce old level-scaled lethality.

## Precision / UNKNOWN rules
- Penetration must never fabricate negative resistance.
- Flat resistance reduction may produce negative resistance.
- If flat reduction already takes the target to non-positive resistance,
  preserve that state and do not invent extra penetration benefit.
- Bonus armor penetration requires a known base/bonus armor split.
- If that split is unavailable, return an explicit unresolved state instead of
  pretending all armor is bonus armor.
- Keep source provenance explicit.
- Community-documented formulas must not be mislabeled as Riot Developer
  Portal formulas.

## Out of scope
Do NOT implement in Phase 2E:

- champion spell formulas;
- item passive/active execution;
- rune effect execution;
- stat-shard interpretation;
- critical-strike rules;
- basic-attack special cases;
- damage amplification/reduction modifiers;
- shields;
- executes;
- healing;
- on-hit/on-attack ordering;
- temporary champion forms/buffs;
- Burst / TTK;
- composition analysis;
- build/rune recommendations;
- ML.

## Frozen boundaries
Do NOT modify:

- Death Analyzer v11;
- Jungle Tempo / Pathing v17;
- Objective Analyzer v20;
- Recall / Reset Analyzer v21;
- Build / Itemization Analyzer v22 Phase 1;
- Item Knowledge Phase 2A;
- Champion Knowledge Phase 2B1;
- Rune Knowledge Phase 2C1-B;
- Level-Resolved Champion Stat Formula Foundation Phase 2D v4.

If a frozen production file needs a real compatibility change, stop and return
REVIEW_REQUIRED.

## Required implementation
Create:

- `knowledge/combat_resistance_rules.py`
- `knowledge/combat_resistance_synthetic_checks.py`
- `knowledge/combat_resistance_precision_checks.py`
- `knowledge/combat_resistance_full_audit.py`

Use `main.py` only as the current development validation harness.

## Validation
Run:

- py_compile;
- synthetic checks;
- precision checks;
- full deterministic rule audit;
- FROZEN guard;
- `python main.py`.

Minimum precision anchors:

- 100 armor -> 0.5 damage multiplier;
- -100 armor -> 1.5 damage multiplier;
- 30% + 20% percent effects -> 44% combined;
- Riot-current lethality 18 -> 18 flat armor penetration;
- penetration cannot take positive armor/MR below 0;
- reduction can take resistance below 0;
- known armor order example:
  300 total = 100 base + 200 bonus,
  30 flat reduction,
  30% reduction,
  45% bonus armor penetration,
  10 flat penetration
  -> 122.3 effective armor;
- true damage bypasses armor/MR in this resistance layer.

## Freeze criteria
Phase 2E becomes freeze-ready when:

- all focused tests pass;
- full rule audit has 0 blocking issues;
- full rule audit has 0 unresolved review items;
- calculation order is explicit and auditable;
- lethality uses the current 1:1 rule;
- bonus armor penetration never guesses a missing component split;
- negative-resistance behavior is preserved correctly;
- frozen modules remain untouched.

After the run, return the exact audit output to ChatGPT for project review.
Do not freeze Phase 2E automatically.
