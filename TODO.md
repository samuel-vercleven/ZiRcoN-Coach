# ZiRcoN Coach — TODO

## Current task
Status: COMPLETED / REVIEW_REQUIRED.

Completion summary:
- 79 MISSED_TRANSFORMATION records grouped by root cause.
- 3 retained_after_missed_transformation cases inspected and marked with reliability intervals.
- component_consumed_after_ignored_destroy audit fixed to ignore stale destroys followed by clear reacquisition.
- plain UNRESOLVED destroyed records resolved as consumable Riot representations.
- generic inventory reliability states added for future consumers.
- full 87-game audit and `python main.py` passed.
- v22 is not frozen; project review must decide next.

Build / Itemization Analyzer v22 — Phase 1D:
Resolve remaining generic intermediate inventory transformations before freeze.

## Context

Phase 1C currently has:

- 87 Jungle games
- 4277 player item events
- 86 EXACT final inventories
- 1 EXACT_WITH_EXPLAINED_GRANT
- 0 PARTIAL
- 0 MISMATCH
- 0 UNKNOWN
- 100% observed-or-explained final inventory agreement

Accepted:
- Magical Footwear grant handling
- purchase reconstruction
- sell reconstruction
- undo reconstruction, including restoration of consumed components
- component trees
- final inventory validation
- Viego-specific uncertainty remains isolated from generic reconstruction

Remaining audit findings:

- 79 MISSED_TRANSFORMATION records
- 13 plain UNRESOLVED destroyed records
- 78 component_consumed_after_ignored_destroy contradictions
- 3 retained_after_missed_transformation contradictions
- 0 LIKELY_REAL_REMOVAL
- 0 SELL_ITEM_NOT_RECONSTRUCTED_AS_HELD after the Phase 1C fix

This task must focus on generic intermediate inventory correctness.

Do NOT redesign the analyzer and do NOT start recommendation logic.

---

# Part A — Audit the 79 MISSED_TRANSFORMATION records

Inspect all 79 records individually/programmatically and group them by root cause.

For each group report:

- champion
- item destroyed
- timestamp
- inventory before
- inventory after
- associated purchase/transformation
- time difference
- Data Dragon from/into relationship
- whether the source item was actually held
- whether the target item appeared through ITEM_PURCHASED
- whether current production already consumes the source through purchase logic
- whether ignoring ITEM_DESTROYED creates an actually incorrect inventory state

Group into categories such as:

- EVENT_ORDER_DUPLICATE
- ALREADY_HANDLED_BY_PURCHASE_COMPONENT_CONSUMPTION
- REAL_MISSED_TRANSFORMATION
- TEMPORARY_MECHANIC
- VIEGO_TEMPORARY_POSSIBLE
- UNRESOLVED

Do not treat an audit classification as a production bug until the inventory chronology demonstrates one.

---

# Part B — Resolve the 3 retained-after-missed-transformation cases

These are highest priority.

For each of the 3 cases show:

- match
- champion
- timestamp
- source item
- target/replacement item
- inventory immediately before
- current inventory immediately after
- expected inventory if transformation is applied
- subsequent item transactions
- final inventory

Determine whether the source item genuinely remains incorrectly held.

If yes:
- implement the smallest generic evidence-based correction;
- add regression coverage;
- rerun all 87 games.

If no:
- explain why the audit is a false positive and fix the audit classification only.

No champion-specific fix unless the mechanic itself is genuinely champion-specific.

---

# Part C — Investigate the 78 component-consumed-after-ignored-destroy cases

Do NOT assume all 78 are errors.

Determine whether they mainly follow this Riot pattern:

ITEM_DESTROYED(component)
...
ITEM_PURCHASED(completed item)

while the production model intentionally keeps the component until the
purchase event consumes it.

For every root-cause family determine:

- whether the inferred inventory between destroy and purchase is materially wrong;
- typical time gap;
- whether both events are effectively part of one shop/item-combination operation;
- whether Riot ordering explains the apparent contradiction;
- whether any case leaves an impossible inventory for a meaningful duration.

Report:

- harmless representation cases
- genuine intermediate reconstruction errors
- unresolved cases

If a deterministic, generic rule can safely resolve genuine cases, implement it.

Do not globally apply every ITEM_DESTROYED event as permanent removal.

---

# Part D — Audit the 13 plain UNRESOLVED events

Inspect all 13.

For each determine whether it can now be explained through:

- item graph
- transaction ordering
- component combination
- automatic transformation
- granted item
- consumable/trinket/jungle progression
- temporary mechanic

If Riot data remains insufficient, preserve UNRESOLVED.

Uncertainty is acceptable.

Future consumers must be able to know an interval is unreliable.

---

# Part E — Reliability intervals

Add or formalize a generic way for future code to know whether the reconstructed inventory is reliable at a given point.

Suggested concept:

inventory_reliability =
- RELIABLE
- AMBIGUOUS_TEMPORARY_STATE
- UNRESOLVED_TRANSFORMATION

or equivalent.

Do not fabricate corrected inventory inside unresolved intervals.

This is important because future build coaching must not reason from an inventory
state known to be unreliable.

Viego possession uncertainty should use the same generic reliability mechanism,
not force the entire analyzer to become Viego-specific.

---

# Part F — Champion-agnostic requirement

The production Itemization Analyzer must remain generic.

Do NOT optimize around Viego.

Viego is only an exceptional mechanic used to test reliability.

Any generic purchase/sell/undo/component/transformation logic must work for:
- Shyvana
- Bel'Veth
- Mundo
- Viego
- any other champion

Champion-specific handling is allowed only when Riot exposes a genuinely
champion-specific temporary mechanic, and it must remain isolated.

---

# Part G — Regression validation

After any production fix, rerun the full 87-game history.

Required results:

- final inventory validation counts
- intermediate contradiction counts before vs after
- MISSED_TRANSFORMATION count before vs after
- retained-after-missed-transformation count before vs after
- component-consumed-after-ignored-destroy count before vs after
- unresolved count
- warning counts
- target EUW1_7951911875
- Magical Footwear target EUW1_7836627546

Final inventory correctness must not regress.

---

# Freeze criteria

Phase 1 is freeze-ready if:

- final 87-game inventory validation remains fully explained;
- the 3 retained-after-missed-transformation cases are resolved or demonstrated false positives;
- no systematic generic intermediate inventory corruption remains;
- the 78 component cases are understood and any genuine generic bug is fixed;
- remaining unresolved cases are explicitly marked unreliable;
- future code can distinguish reliable vs ambiguous inventory intervals;
- Viego uncertainty remains isolated;
- no frozen analyzer is modified.

Do not demand zero ambiguity when Riot data cannot provide it.

Correct uncertainty is acceptable.

---

# Restrictions

Do NOT modify:

- Death Analyzer v11
- Jungle Tempo / Pathing v17
- Objective Analyzer v20
- Recall / Reset Analyzer v21

Do NOT implement:

- champion matchup analysis
- allied/enemy composition analysis
- item recommendations
- boots recommendations
- GOOD/BAD build labels
- Itemization Score
- ML

---

# Testing

Run:

- compile checks
- synthetic itemization checks
- focused transformation regression tests
- focused 79-case audit
- full 87-game historical audit
- python main.py if production code changes

---

# Reporting

Update:

- LAST_RUN.md
- PROJECT_STATE.md
- TODO.md → completed only

LAST_RUN must clearly report:

- root causes of the 79 MISSED_TRANSFORMATION records
- detailed resolution of the 3 retained cases
- analysis of the 78 component cases
- status of the 13 unresolved cases
- production code changes
- reliability-state implementation if added
- before/after contradiction counts
- final inventory validation
- target-match results
- whether Phase 1 is now freeze-ready

Finish with:

REVIEW_REQUIRED

Do not freeze v22 yourself.

---

# Git

Commit and push tested work.

Suggested commit:

Resolve itemization intermediate transformations
