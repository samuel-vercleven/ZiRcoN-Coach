# ZiRcoN Coach — TODO

## Current task
Build / Itemization Analyzer v22 — Phase 1:
Reliable item timeline and inventory reconstruction.

Status: COMPLETED by Codex on 2026-08-17.
Outcome: REVIEW_REQUIRED before freeze / Phase 2 because one real-history non-purchasable item grant remains unobserved in Riot item events and normal ITEM_DESTROYED semantics remain ambiguous.

## Long-term objective

The final ZiRcoN Coach itemization system must eventually recommend a contextual build for the current match using:

- player's champion;
- allied team composition;
- enemy team composition;
- AP / AD / true-damage profile;
- burst vs sustained DPS;
- tanks / squishies;
- armor / magic resistance;
- healing / sustain / shielding;
- crowd control;
- auto-attack / crit / on-hit threats;
- assassins / burst threats;
- frontline needs;
- allied damage profile;
- allied missing roles or weaknesses;
- current game state;
- items already purchased;
- later, validated personal historical tendencies when useful.

The eventual output should be able to recommend and explain:

- starting item;
- boots;
- first major item;
- second major item;
- third major item;
- later situational items;
- defensive adaptations;
- penetration;
- anti-heal;
- anti-tank choices;
- survivability choices.

Example future reasoning:

Enemy team:
- heavy magic damage;
- important CC;
- durable frontline;
- sustained fights expected.

Allied team:
- already high AP damage;
- limited frontline.

Possible contextual explanation:
- Mercury's Treads prioritized because of magic threats + CC.
- Tank-shred / sustained-damage item prioritized because fights are expected to last.
- Another pure AP item may have lower priority because allied damage is already heavily magic-based.

IMPORTANT:
This long-term goal is context only.

DO NOT implement build recommendations in Phase 1.

Phase 1 must establish a reliable factual item-history layer first.

---

# Phase 1 goal

Reconstruct, as reliably and auditably as possible, the player's item state throughout every historical match.

The system should eventually be able to answer:

"At 17:42 in this match, what items/components did ZiRcoN actually have?"

This factual foundation must be validated before any item-quality or build recommendation logic is added.

---

## Part A — Riot item-event extraction

Use the Riot timeline events relevant to inventory changes, including where available:

- ITEM_PURCHASED
- ITEM_SOLD
- ITEM_UNDO
- ITEM_DESTROYED

Investigate other Riot item-related event types if they occur in the stored history.

For every transaction preserve:

- match_id;
- game_creation;
- champion;
- timestamp;
- minute;
- event type;
- item ID;
- item name;
- Riot/Data Dragon metadata;
- event index/frame context where available.

Keep raw event information auditable.

Do not discard events merely because they are unusual.

---

## Part B — Data Dragon item metadata

Reuse the existing Data Dragon integration.

Resolve item IDs to item metadata where possible.

At minimum expose:

- item ID;
- item name;
- total Gold cost;
- base Gold cost if useful;
- purchasable status;
- item tags;
- `from` components;
- `into` upgrades;
- description/plaintext if useful for debugging;
- boots / consumable / trinket / jungle-item characteristics where available.

Do not hardcode normal item names when Data Dragon provides them.

If Riot uses special IDs not represented correctly in Data Dragon, document them explicitly.

---

## Part C — Inventory reconstruction

Build a deterministic chronological inventory reconstruction for the player.

Maintain the inferred inventory after every item transaction.

Correctly handle:

- normal purchases;
- components;
- completed items;
- boots;
- consumables;
- wards/trinkets;
- jungle pets/items;
- sells;
- undo transactions;
- item transformations;
- upgrades;
- automatic replacements when Riot represents them through item events;
- temporary/special items where applicable.

Do NOT assume:

`ITEM_PURCHASED = permanent new inventory slot`

Some items transform, combine, disappear, upgrade, or are consumed.

If reconstruction cannot be determined safely, use explicit states such as:

- UNKNOWN;
- AMBIGUOUS;
- RECONSTRUCTION_WARNING.

Never silently invent an inventory state.

---

## Part D — Inventory slots

Where technically practical, represent a reconstructed six-slot inventory plus trinket/special state.

However, do not fabricate exact slot positions if Riot data only supports the set/multiset of held items.

Separate:

- factual held-item multiset;
- exact slot ordering if actually knowable.

The factual inventory content matters more than cosmetic slot ordering.

---

## Part E — Component / completed-item distinction

Build a reliable distinction between:

- components;
- completed major items;
- boots;
- consumables;
- trinkets;
- jungle-specific progression;
- special items.

Use Data Dragon's item graph (`from` / `into`) where useful.

Do not classify an item as a "major completed item" only because of price.

Document special cases.

---

## Part F — Item completion milestones

For every match derive itemization milestones such as:

- first meaningful purchase;
- boots purchase;
- boots upgrade;
- first completed major item;
- second completed major item;
- third completed major item;
- fourth+ completed major items;
- approximate completion timestamp;
- approximate cumulative known Gold invested.

Keep components visible.

Example:

12:03
- Blasting Wand
- Amplifying Tome
- Boots

15:41
- completed major item X

Do not hide the component path.

---

## Part G — Purchase-visit integration

Reuse Recall / Reset Analyzer v21 only as a frozen dependency/context source if useful.

Do NOT modify Reset Analyzer v21.

Where possible, associate item transactions with existing SHOP/RESET proxy clusters.

This could later allow ZiRcoN Coach to understand:

- what was purchased on each base/shop visit;
- which item spike was completed;
- how much Gold was converted into items.

For Phase 1 this remains factual reconstruction only.

Do not judge whether the purchase was good or bad.

---

## Part H — Final inventory validation

For every exploitable historical game:

compare the reconstructed final inventory with Riot's final participant inventory from match data.

Report:

- EXACT;
- PARTIAL;
- MISMATCH;
- UNKNOWN.

Define these categories explicitly.

For every mismatch provide detailed diagnostics:

- match ID;
- champion;
- reconstructed final items;
- Riot final items;
- complete relevant transaction sequence;
- sells;
- undo operations;
- destroyed/transformed items;
- jungle/trinket/special-item involvement;
- probable reason for mismatch;
- unresolved ambiguity.

The target is very high reconstruction reliability.

Do not simply report an accuracy percentage and move on.

Inspect real mismatches.

---

## Part I — Intermediate-state validation

Final inventory matching alone is insufficient.

Add sanity/invariant checks throughout the transaction timeline.

Examples:

- inventory should not exceed legal capacity unless an explicitly modeled special case explains it;
- selling an item should normally require it to be reconstructably held;
- undo should reverse the relevant shop transaction when Riot data supports it;
- component consumption into a completed item should be explainable;
- Gold/inventory transitions should remain internally coherent where data allows verification;
- item transformations should not create impossible duplicate states.

Report invariant violations separately.

Do not auto-correct suspicious states silently.

---

## Part J — Historical itemization dataset

Create a reusable UI-agnostic dataset for later phases.

Suggested fields include:

- match_id
- game_creation
- champion
- opponent_champion
- win
- timestamp
- minute
- event_type
- item_id
- item_name
- item_category
- item_cost
- inventory_after
- major_items_after
- components_after
- boots_after
- trinket_after
- jungle_item_after
- known_inventory_gold
- shop/reset proxy id if available
- reconstruction_status
- reconstruction_warnings

The exact schema may evolve if a better representation is justified.

Keep raw factual data separate from future coaching labels.

---

## Part K — Full-history audit

Run the reconstruction across the full available Jungle history.

Report at minimum:

- number of games processed;
- number of item events processed;
- total purchases;
- total sells;
- total undo events;
- item-destroyed / transformation cases;
- EXACT final inventories;
- PARTIAL final inventories;
- MISMATCH inventories;
- UNKNOWN inventories;
- exact-match percentage;
- invariant violations;
- most common mismatch causes;
- most common special-item cases;
- champion breakdown.

Inspect mismatch categories individually.

---

## Part L — Target match audit

Provide a detailed reconstruction for:

`EUW1_7951911875`

Show chronologically:

- purchase timestamp;
- item bought/sold/undone;
- inventory after transaction;
- detected shop/reset visit when available;
- completed-item milestones;
- final reconstructed inventory;
- Riot final inventory;
- validation result.

This target-match report must be readable enough for manual verification.

---

# Architecture

Prefer new dedicated modules such as:

- `analysis/itemization_analyzer.py`
- `analysis/itemization_statistics.py` only if actually needed at this phase

A dedicated reader/helper may be added if technically justified.

Do not overload `main.py` with business logic.

`main.py` may integrate/report the analyzer as part of the development harness.

Keep analysis logic UI-agnostic.

---

# Frozen modules

The following are FROZEN and must not be modified:

- Death Analyzer v11
- Jungle Tempo / Pathing Analyzer v17
- Objective Analyzer v20
- Recall / Reset Analyzer v21

They may be consumed as dependencies/context.

Do not duplicate or redefine their concepts unnecessarily.

If a genuine integration bug forces a frozen-module change:
- make the smallest possible change;
- mark REVIEW_REQUIRED;
- document it.

---

# Methodology restrictions

Phase 1 is factual measurement/reconstruction only.

DO NOT yet:

- classify an item as GOOD/BAD;
- recommend an item;
- recommend boots;
- recommend a full build;
- compare the player's build to a theoretical optimal build;
- use Win/Loss to define item quality;
- infer AP/AD composition;
- infer burst/DPS profile;
- infer enemy healing;
- infer armor/MR needs;
- infer anti-heal needs;
- infer penetration needs;
- infer anti-tank needs;
- build an Itemization Score;
- introduce machine learning;
- use popularity/meta builds as ground truth.

Those belong to later phases after reconstruction is validated.

---

# Future phases — DO NOT IMPLEMENT YET

These are architectural context only.

## Phase 2 — Champion/item semantic knowledge

Build factual item/champion characteristics needed for reasoning.

Examples:
- AP/AD;
- armor/MR;
- health;
- penetration;
- anti-heal;
- anti-shield;
- attack speed;
- crit;
- on-hit;
- sustain;
- burst/sustained synergy;
- tank-shred characteristics.

## Phase 3 — Team composition analyzer

Analyze BOTH teams.

Enemy:
- physical/magic/true damage;
- burst vs sustained;
- CC;
- frontline;
- healing/shielding;
- armor/MR;
- assassins;
- auto attackers;
- tanks;
- squishies.

Allies:
- team damage split;
- existing frontline;
- engage;
- CC;
- burst/DPS balance;
- damage redundancy;
- missing defensive/offensive needs.

## Phase 4 — Contextual build reasoning

Combine:
- champion;
- allied composition;
- enemy composition;
- game state;
- current items;
- current Gold/shop opportunity;
- validated analyzer context.

Generate item priorities with explanations.

## Phase 5 — Build recommendation

Eventually output:

- starting item;
- boots;
- item 1;
- item 2;
- item 3;
- item 4;
- item 5;
- situational alternatives;
- explanation for each decision.

The final system must recommend a build for THAT match, not merely reproduce the most popular public build.

Again: DO NOT IMPLEMENT Phases 2–5 in the current task.

---

# Testing

Perform:

1. compile modified Python files;
2. focused synthetic tests for:
   - purchase;
   - sell;
   - undo;
   - component completion;
   - special/jungle/trinket cases where possible;
3. full historical reconstruction audit;
4. inspect all meaningful mismatches;
5. run `python main.py` if integrated into the normal harness.

Do not claim reconstruction is reliable from synthetic tests alone.

Real-history validation is mandatory.

---

# Success criteria

Phase 1 is potentially freeze-ready only if:

- reconstruction semantics are clear;
- final inventory agreement is very high;
- remaining mismatch cases are understood;
- sells/undo/component transformations are handled coherently;
- special jungle/trinket cases are documented;
- intermediate invariants do not reveal systemic errors;
- target match reconstruction is plausible;
- no frozen analyzer was altered unnecessarily.

If significant correctness problems remain:

`REVIEW_REQUIRED`

Do not automatically continue to Phase 2.

---

# Reporting

At completion update:

- `LAST_RUN.md`
- `PROJECT_STATE.md`
- `TODO.md` → mark current task completed only

`LAST_RUN.md` must include:

- tests;
- runtime status;
- games/events processed;
- exact/partial/mismatch/unknown counts;
- major mismatch causes;
- special item cases;
- target-match result;
- suspicious findings;
- remaining issues;
- whether REVIEW_REQUIRED is needed.

Do not invent the next major task.

---

# Git

Verify secrets before commit.

Allowed League match-analysis metadata may be committed according to AGENTS.md.

Never commit:
- `.env`
- Riot API keys
- credentials
- `.venv`
- SQLite DB files
- secrets

Commit and push tested work.

Suggested commit:

`Add itemization timeline reconstruction`
