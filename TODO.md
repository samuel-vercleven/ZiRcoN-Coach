# ZiRcoN Coach — TODO

## Current task
Build / Itemization Analyzer v22 — Phase 1B:
Final factual inventory audit and non-purchase item grants before freeze.

Status: COMPLETED by Codex on 2026-08-17.
Outcome: REVIEW_REQUIRED. Phase 1B audit implemented and tested; no Phase 2 or recommendation logic added.

## Important scope

This task is still ONLY factual item reconstruction.

Do NOT yet evaluate item quality against:
- enemy champion;
- enemy team composition;
- allied team composition;
- AP/AD damage profile;
- burst/DPS;
- CC;
- armor/MR;
- healing;
- tanks;
- assassins.

The analyzer may store champion/team information for future use,
but Phase 1 must not use it to recommend or judge items.

---

# Current verified state

Phase 1 currently reconstructs:

- 87 Jungle games;
- 4277 player item events;
- 1536 purchases;
- 11 sells;
- 45 undo events;
- 2685 ITEM_DESTROYED events.

Final inventory validation:

- 86 EXACT;
- 1 PARTIAL;
- 0 MISMATCH;
- 0 UNKNOWN;
- 98.9% exact final reconstruction.

Target match:
EUW1_7951911875 = EXACT.

Remaining PARTIAL:
EUW1_7836627546.

Riot final inventory contains:
2422 / Slightly Magical Boots

but no normal ITEM_PURCHASED event exposes that item.

This is expected to be related to the Magical Footwear rune.

---

# Part A — Magical Footwear / granted item support

Inspect the participant perks/runes stored in the Riot match raw data for:

EUW1_7836627546

Determine whether the player selected:

Magical Footwear

If yes:

classify item 2422 as:

source = RUNE_GRANT
grant_type = MAGICAL_FOOTWEAR
purchase_event = NONE

Do NOT treat the absence of ITEM_PURCHASED as a reconstruction error.

Do NOT fabricate an exact Riot item event.

## Acquisition timestamp

If the rune is confirmed, it is acceptable to compute a separate:

derived_grant_timestamp

using the known Magical Footwear rule and observable takedown history,
provided the implementation clearly labels the value as DERIVED / INFERRED.

Never present a derived timestamp as a Riot-observed event.

Keep fields conceptually separated:

- observed_timestamp
- derived_timestamp
- source
- confidence / evidence

If the exact grant timing cannot be derived reliably:
keep timestamp UNKNOWN.

---

# Part B — Generic non-purchase grants

Search all 87 games for final items which:

- appear in Riot final inventory;
- were not reconstructed through normal item transactions;
- are non-purchasable or likely granted by game mechanics.

Report all such cases.

Create an explicit factual source classification where justified:

- PURCHASE
- RUNE_GRANT
- AUTOMATIC_TRANSFORMATION
- GAME_MECHANIC_GRANT
- UNKNOWN_GRANT

Do not hardcode arbitrary final items into earlier inventories.

A final-item observation must not be used to invent a historical acquisition time.

---

# Part C — ITEM_DESTROYED audit

Audit every ITEM_DESTROYED not already explained confidently as:

- component consumed by completed-item purchase;
- consumable removal;
- jungle item progression/removal;
- trinket-use handling;
- another validated deterministic transformation.

For remaining events report:

- total count;
- games affected;
- champion;
- item ID/name;
- whether item was reconstructed as held;
- inventory before event;
- same-timestamp item events;
- later transactions involving the item;
- final Riot inventory;
- whether ignoring the destroy is required for final correctness.

Audit-only classification:

- TEMPORARY_OR_NON_PERMANENT_STATE
- LIKELY_REAL_REMOVAL
- MISSED_TRANSFORMATION
- UNRESOLVED

Do not globally interpret ITEM_DESTROYED as permanent deletion.

---

# Part D — Viego special audit

Audit Viego separately.

Because Viego can temporarily use another champion's state/items,
ITEM_DESTROYED events may reflect temporary possession state rather than
ZiRcoN's permanent inventory.

Report:

- Viego games;
- Viego ITEM_DESTROYED count;
- normal ambiguous destroyed count;
- items involved;
- whether those items belong to ZiRcoN's permanent reconstructed build;
- whether events are compatible with temporary possession states.

If temporary possession inventory cannot be reconstructed reliably,
document:

TEMPORARY_POSSESSION_INVENTORY_UNRELIABLE

Future item coaching must ignore temporary possession inventory
when evaluating Viego's permanent build.

Do not create champion-specific inventory logic unless evidence requires it.

---

# Part E — Held-item ITEM_DESTROYED risk

Inspect every:

DESTROYED_NORMAL_HELD_IGNORED_AS_AMBIGUOUS

For each case determine whether production currently leaves an item in inventory
that should clearly have disappeared.

Check:

- subsequent sell;
- subsequent upgrade;
- repeated purchase;
- inventory capacity;
- final inventory;
- same-timestamp transformations.

If clear evidence shows a real permanent removal is being ignored:
apply the smallest evidence-backed fix and rerun all 87 games.

Otherwise leave the event explicitly ambiguous.

---

# Part F — Intermediate inventory invariants

Audit the reconstructed timeline for:

- >6 permanent inventory slots;
- item sold but never held;
- impossible duplicate completed items;
- component upgrade without plausible ingredients;
- ignored destroyed item creating an impossible long-lived state;
- undo inconsistent with current inventory;
- unknown item metadata;
- contradictory later transactions.

Report all warning codes and counts.

Separate warnings into:

- understood expected mechanic;
- harmless Riot representation limitation;
- genuine reconstruction bug;
- unresolved.

Zero warnings is NOT required.

Every important warning family must be understood.

---

# Part G — Major item milestone audit

Validate completed-major classification.

Ensure ordinary cases such as:

- trinkets;
- potions/elixirs;
- jungle starter/pet items;
- ordinary components;
- granted boots;
- non-major special items

are not incorrectly counted as completed major-item milestones.

Report unusual COMPLETED_MAJOR classifications.

Do not redesign the item category system without concrete evidence.

---

# Part H — Target matches

## EUW1_7951911875

Confirm:

- EXACT reconstruction;
- chronological inventory remains coherent;
- Kraken Slayer completion;
- Collector completion;
- Immortal Shieldbow completion;
- no unexplained ITEM_DESTROYED changes the conclusion.

## EUW1_7836627546

Show:

- selected runes;
- Magical Footwear presence or absence;
- item 2422 source;
- observed vs derived timestamp status;
- reconstructed final inventory;
- Riot final inventory;
- final validation classification.

If Magical Footwear explains the missing item,
do not classify this case as a normal reconstruction failure.

---

# Part I — Final validation policy

Introduce/clarify validation states if useful:

- EXACT_OBSERVED
- EXACT_WITH_EXPLAINED_GRANT
- PARTIAL
- MISMATCH
- UNKNOWN

For example:

A game whose only difference is a confirmed Magical Footwear rune grant
may become:

EXACT_WITH_EXPLAINED_GRANT

rather than forcing a fake ITEM_PURCHASED event.

Do not merge observed and inferred facts silently.

---

# Freeze criteria

Phase 1 can be freeze-ready if:

- normal purchases/sells/undo/component reconstruction remains reliable;
- non-purchase grants are explicitly modeled rather than fabricated;
- Magical Footwear case is explained correctly if rune evidence supports it;
- ITEM_DESTROYED does not hide a systemic permanent-inventory bug;
- Viego temporary state limitations are documented;
- intermediate inventory invariants show no systemic corruption;
- major-item milestones remain credible;
- target match remains exact;
- no frozen analyzer was modified.

100% observed transaction reconstruction is NOT required when Riot itself
does not expose a grant as a transaction.

Correct uncertainty is preferable to invented precision.

---

# Frozen modules

Do NOT modify:

- Death Analyzer v11
- Jungle Tempo / Pathing v17
- Objective Analyzer v20
- Recall / Reset Analyzer v21

---

# Do NOT implement yet

Do NOT implement:

- enemy champion item counter logic;
- allied/enemy composition analysis;
- item recommendations;
- boots recommendations;
- anti-heal logic;
- armor/MR reasoning;
- anti-tank logic;
- AP/AD composition logic;
- GOOD/BAD labels;
- Itemization Score;
- ML.

These belong to later phases.

---

# Testing

Run:

- compile checks;
- existing synthetic itemization checks;
- focused rune/grant checks;
- focused ITEM_DESTROYED audit;
- full 87-game reconstruction audit;
- python main.py if production code changes.

---

# Reporting

Update:

- LAST_RUN.md
- PROJECT_STATE.md
- TODO.md → completed only

LAST_RUN must include:

- final inventory validation counts;
- Magical Footwear conclusion;
- non-purchase grant counts;
- ITEM_DESTROYED audit counts;
- Viego results;
- warning-code counts;
- intermediate invariant violations;
- major-item milestone findings;
- target-match result;
- freeze-readiness recommendation.

Finish with:

REVIEW_REQUIRED

Do not freeze Phase 1 yourself.

---

# Git

Commit and push tested work.

Suggested commit:

Audit item grants and destroyed events
