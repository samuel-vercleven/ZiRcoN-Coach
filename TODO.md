# ZiRcoN Coach — TODO

## Current task
Build / Itemization Analyzer v22 — Phase 1C:
Evidence-based ITEM_DESTROYED final audit.

Status: COMPLETED by Codex on 2026-08-18.
Outcome: REVIEW_REQUIRED. Evidence-based ITEM_DESTROYED audit implemented, sell-warning bug fixed, no build recommendation logic added.

## Context

Phase 1B currently achieves:

- 87 Jungle games
- 4277 item events
- 86 EXACT final inventories
- 1 EXACT_WITH_EXPLAINED_GRANT
- 0 PARTIAL
- 0 MISMATCH
- 0 UNKNOWN
- 100% observed-or-explained final inventory agreement

Magical Footwear is now correctly identified as a confirmed RUNE_GRANT
when perk 8304 is present.

This part is accepted.

The remaining review problem is the ITEM_DESTROYED audit methodology.

## Problem found during project review

Current `_classify_unexplained_destroyed()` is not sufficiently
evidence-based.

In particular:

- every Viego unexplained destroy is automatically classified
  TEMPORARY_OR_NON_PERMANENT_STATE;
- every not-held destroy is automatically classified temporary;
- a held destroy may be classified temporary simply because the item is
  present in the final inventory;
- the function currently has no meaningful path which can classify a case as:
  - LIKELY_REAL_REMOVAL
  - MISSED_TRANSFORMATION

Therefore the current:

1582 TEMPORARY_OR_NON_PERMANENT_STATE
18 UNRESOLVED

must NOT be used as freeze evidence by itself.

The purpose of this task is to make the audit genuinely evidence-based.

Do NOT change production reconstruction unless the new audit reveals a
demonstrated reconstruction bug.

---

# Part A — Remove circular audit assumptions

Modify the audit classifier only.

Do NOT classify an event as temporary solely because:

- champion == Viego;
- item is present in final inventory;
- final reconstruction status is EXACT;
- item was not currently reconstructed as held.

Those facts may be supporting context, but not sufficient proof.

Final inventory correctness must not be used as proof that the
intermediate inventory was correct.

---

# Part B — Evidence-based classifications

For every unexplained normal ITEM_DESTROYED event classify as one of:

## CONFIRMED_OR_STRONG_TEMPORARY_STATE

Require positive evidence such as:

- item never belongs to the player's permanent purchased build;
- event occurs inside an identifiable temporary mechanic/state;
- repeated temporary item event pattern clearly incompatible with permanent ownership;
- surrounding events strongly support temporary/copied inventory;
- Viego possession context is observable from timeline events if available.

Champion identity alone is NOT sufficient.

## LIKELY_REAL_REMOVAL

Use when evidence supports that the player's permanently held item actually
ceased being held.

Examples:

- held before destroy;
- no simultaneous replacement/transformation;
- subsequent inventory behavior is only coherent if it was removed;
- later repurchase strongly supports that the old copy disappeared;
- sale/upgrade/capacity chronology contradicts keeping it.

## MISSED_TRANSFORMATION

Use when:

- destroy is associated with another item appearing;
- component/upgrade graph explains the transition;
- same or nearby timestamp indicates transformation;
- current production deterministic handling missed the relationship.

## UNRESOLVED

Use when current Riot data cannot reliably distinguish the possibilities.

Do not force a classification.

---

# Part C — Reconstruct before/after evidence

For every unexplained destroy record:

- match_id
- champion
- timestamp
- item ID/name
- reconstructed inventory immediately before
- reconstructed inventory immediately after under current production model
- whether item was considered held before
- same-timestamp ITEM_PURCHASED
- same-timestamp ITEM_SOLD
- same-timestamp ITEM_UNDO
- item transformations/upgrades around event
- next transaction involving same item
- previous transaction involving same item
- later repurchase of same item
- final Riot inventory
- reconstructed final inventory
- slot count before/after
- classification
- classification evidence/reason

Classification must be auditable from these fields.

---

# Part D — Held normal destroyed events

Audit ALL:

DESTROYED_NORMAL_HELD_IGNORED_AS_AMBIGUOUS

These are the highest priority.

Do not infer safety from final inventory alone.

Specifically detect situations like:

purchase item
→ ITEM_DESTROYED
→ item absent for a meaningful period
→ later repurchase

because keeping the first copy through that interval would produce an
incorrect intermediate inventory even if final inventory happens to match.

Report:

- total held-destroyed cases;
- Viego vs non-Viego;
- confirmed temporary;
- likely real removal;
- missed transformation;
- unresolved.

---

# Part E — Viego evidence audit

Do not automatically classify Viego events as temporary.

For each Viego ambiguous ITEM_DESTROYED family determine whether there is
positive evidence compatible with possession/copied inventory.

Use available timeline context if possible.

If exact possession windows cannot be identified reliably:

classify those cases UNRESOLVED_TEMPORARY_POSSIBLE

or equivalent,

rather than claiming temporary state as fact.

Permanent limitation may remain:

TEMPORARY_POSSESSION_INVENTORY_UNRELIABLE

Future coaching can ignore unreliable intervals.

The goal is honest uncertainty, not reconstructing Viego possession perfectly.

---

# Part F — Investigate the remaining sell warning

There is currently:

1 SELL_ITEM_NOT_RECONSTRUCTED_AS_HELD

Inspect this exact case manually.

Report:

- match
- champion
- timestamp
- item
- previous item events
- previous destroy events
- reconstructed inventory
- actual likely explanation

Determine whether this warning exposes:

- a real ignored ITEM_DESTROYED removal;
- temporary mechanic;
- transformation issue;
- missing grant;
- Riot event-order issue;
- unresolved ambiguity.

Do not leave this single warning unexplored.

---

# Part G — Intermediate-state contradiction tests

Explicitly search all 87 games for:

- >6 permanent slots;
- duplicate major item impossible states;
- sell of an item not held;
- upgrade requiring impossible prior state;
- later purchase of an item already incorrectly retained;
- item retained long after strong evidence of removal;
- impossible component consumption caused by ignored destroy;
- contradictory undo.

Report counts and affected matches.

Final inventory agreement alone is not sufficient.

---

# Part H — Magical Footwear policy

Keep the confirmed Magical Footwear source handling.

Accepted factual policy:

item 2422
source = RUNE_GRANT
perk = 8304
purchase_event = NONE

Do NOT fabricate a Riot-observed transaction.

The derived acquisition timestamp must remain clearly separate:

DERIVED_INFERRED

Do not use the derived timestamp as factual Riot event evidence.

Because rune rules can vary by patch, the derived timestamp must not become a
freeze-critical factual dependency unless the rule is version-aware.

For Phase 1 freeze, knowing the grant source is sufficient.
Exact inferred grant timing is optional.

---

# Part I — Production changes

Do NOT modify production ITEM_DESTROYED behavior merely because the audit
classification changes.

Only modify production reconstruction if the evidence-based audit reveals a
specific demonstrated correctness bug.

If production code is changed:

- document exact bug;
- add synthetic regression test;
- rerun all 87 games;
- compare final and intermediate results.

---

# Freeze criteria

Phase 1 can be recommended for freeze when:

- Magical Footwear grant handling remains correct;
- all final inventories remain explained;
- ITEM_DESTROYED audit does not rely on final-state circular reasoning;
- held destroyed events are evidence-audited;
- the remaining sell warning is understood;
- no systemic intermediate inventory corruption is found;
- unresolved Viego temporary states are explicitly isolated rather than
  falsely reconstructed;
- major milestones remain correct;
- target match remains coherent.

UNRESOLVED events are acceptable if future coaching can identify and ignore
unreliable intervals.

Correct uncertainty is preferred over false precision.

---

# Restrictions

Do NOT modify:

- Death Analyzer v11
- Jungle Tempo / Pathing v17
- Objective Analyzer v20
- Recall / Reset Analyzer v21

Do NOT start:

- champion matchup reasoning
- team composition analysis
- item recommendations
- build scoring
- ML

---

# Tests

Run:

- compile checks
- existing synthetic checks
- new focused destroyed-event audit
- full 87-game audit
- regression tests if production behavior changes
- python main.py if production code changes

---

# Reporting

Update:

- LAST_RUN.md
- PROJECT_STATE.md
- TODO.md → completed only

LAST_RUN must include:

- evidence-based destroyed classifications;
- held destroyed classifications;
- Viego-specific results;
- detailed conclusion for the single sell warning;
- intermediate contradiction counts;
- whether production logic changed;
- final inventory validation counts;
- target-match confirmation;
- freeze-readiness recommendation.

Finish with:

REVIEW_REQUIRED

Do not freeze v22 yourself.

---

# Git

Commit and push tested work.

Suggested commit:

Strengthen itemization destroyed-event audit

## Important — Viego is an exception audit, not the analyzer target

Do NOT specialize the general itemization architecture around Viego.

Viego is audited separately only because his possession mechanic can expose
temporary/copied item states through Riot timeline events.

The production itemization analyzer must remain champion-agnostic and work
correctly for every champion.

Viego-specific handling is allowed only when:
- Riot data demonstrates a mechanic-specific representation;
- the handling is isolated from normal champion reconstruction;
- it does not change normal ITEM_DESTROYED semantics for other champions.

Do not require additional Viego games for the analyzer to function.

Do not optimize reconstruction accuracy specifically for Viego at the expense
of Shyvana, Bel'Veth, Mundo, or other champions.

The goal is:
GENERAL ITEM RECONSTRUCTION
+
isolated handling/uncertainty for exceptional champion mechanics.
