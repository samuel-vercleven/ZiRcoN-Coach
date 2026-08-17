# ZiRcoN Coach — TODO

## Current task
COMPLETED - Freeze Build / Itemization Analyzer v22 — Phase 1.

Status:
- Documentation freeze completed by Codex.
- Build / Itemization Analyzer v22 Phase 1 is documented as FROZEN.
- No Python file was modified.
- No Phase 2 task is defined here.
- Next major task remains for project review.

## Decision

Project review accepts Phase 1D as the freeze baseline.

Build / Itemization Analyzer v22 — Phase 1 is now approved for FROZEN status.

This freeze covers factual item/inventory reconstruction only.

It does NOT freeze future:
- item semantic knowledge;
- champion semantic knowledge;
- composition analysis;
- contextual item reasoning;
- build recommendations;
- ML.

Those belong to later phases.

---

## Freeze evidence

Historical validation:

- 87 Jungle games
- 4277 player item events
- 1536 purchases
- 11 sells
- 45 undo events
- 2685 destroyed events

Final inventory:

- 86 EXACT
- 1 EXACT_WITH_EXPLAINED_GRANT
- 0 PARTIAL
- 0 MISMATCH
- 0 UNKNOWN
- 98.9% observed exact
- 100.0% observed-or-explained

Accepted features:

- ITEM_PURCHASED reconstruction
- ITEM_SOLD reconstruction
- ITEM_UNDO reconstruction
- restoration of components after undone completed-item purchase
- transitive component consumption
- boots / consumables / trinkets / jungle-item handling
- completed-major milestones
- six-slot multiset + separate trinket
- Data Dragon patch-aware item catalog
- factual shop/reset proxy association
- final Riot inventory validation
- Magical Footwear rune grant handling
- generic inventory reliability intervals

Accepted reliability states:

- RELIABLE
- AMBIGUOUS_TEMPORARY_STATE
- UNRESOLVED_TRANSFORMATION

Future consumers MUST NOT silently treat unreliable intervals as factual inventory.

---

## Permanent limitations

Document explicitly:

1. Riot ITEM_DESTROYED semantics are not always equivalent to permanent item removal.

2. Some temporary or transformation states cannot be reconstructed exactly from Riot timeline data.

3. Viego possession inventory is not reliably reconstructible.
   Use the generic reliability mechanism.
   Do not specialize the main analyzer around Viego.

4. One observed non-Viego REAL_MISSED_TRANSFORMATION interval cannot be safely materialized.
   It remains UNRESOLVED_TRANSFORMATION instead of inventing an item event.

5. Remaining component-destroy / later-consumption ambiguity is represented through reliability intervals.

6. Magical Footwear item 2422 can be identified as:
   source = RUNE_GRANT
   perk = 8304
   purchase_event = NONE

7. Magical Footwear derived timing remains DERIVED_INFERRED and must never be presented as a Riot-observed ITEM event.

8. Exact slot ordering is not reconstructed; inventory is a six-slot multiset plus trinket.

Correct uncertainty is part of the frozen methodology.

---

## Documentation changes

Update PROJECT_STATE.md:

Build / Itemization Analyzer v22 — Phase 1: FROZEN.

Move it out of "In development" and into the frozen analyzers list.

Preserve the final Phase 1D metrics and permanent limitations.

Update DECISIONS.md with the formal freeze decision and rationale.

The existing Phase 1D reliability policy becomes part of the frozen methodology.

Update TODO.md to COMPLETED.

Update LAST_RUN.md with a documentation-only freeze record.

---

## Frozen boundary

After this commit, do not modify Phase 1 production reconstruction unless:

- a demonstrated correctness bug is found;
- integration with a later phase requires a strictly necessary compatibility change;
- project review explicitly reopens it.

Do not retune behavior merely to reduce warning or ambiguity counts.

---

## Existing frozen analyzers

Remain untouched:

- Death Analyzer v11
- Jungle Tempo / Pathing v17
- Objective Analyzer v20
- Recall / Reset Analyzer v21

---

## Python

Do NOT modify production Python for this task.

No full historical rerun is required because this is a documentation-only freeze
and the Phase 1D full run has already passed.

If Python changes unexpectedly become necessary:
stop and return REVIEW_REQUIRED instead of silently modifying the frozen baseline.

---

## Git

Commit and push.

Suggested commit:

Freeze itemization reconstruction phase 1
