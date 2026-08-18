# ZiRcoN Coach — TODO

## Current task
COMPLETED - Phase 2B1-C — Separate generic transformations from champion form complexity.

## Completion status

REVIEW_REQUIRED.

Implemented and tested the Phase 2B1-C freeze-blocker fix:
- TRANSFORMATION remains a generic factual semantic meaning some transformation mechanic is described.
- ALTERNATE_FORM_POSSIBLE now requires separate subject/state evidence that the champion enters or owns an alternate form, stance, or kit state.
- Generic transformations of damage, targets, marks, resources, effects, terrain, summoned entities, seeds/plants, or weapons no longer create champion alternate-form complexity by keyword alone.
- The 31 Phase 2B1-B non-standard champion baseline cases were re-audited in logs/latest_full_run.txt.
- Full 173-champion Data Dragon audit passed.
- Frozen modules and frozen knowledge layers were not modified.

No next major task is defined here; next direction remains for project review.

## Goal

Fix the last known Champion Knowledge freeze blocker.

Phase 2B1-B factual structure and sensitive semantic fixes are accepted.

Do NOT reopen:
- stats;
- Data Dragon loading;
- spell records;
- placeholders;
- formula policy;
- SHIELD;
- damage semantics;
- percent-health locality;
- REVEAL;

unless a concrete regression is found.

This task is ONLY about TRANSFORMATION semantics and champion complexity flags.

---

## Problem

Current complexity rules can infer:

ALTERNATE_FORM_POSSIBLE

from generic words such as:

"transforme"

even when the champion does not transform themselves or change ability form.

Examples of concepts that must NOT automatically mean alternate champion form:

- transforms damage;
- transforms a target;
- transforms a mark;
- transforms a resource;
- transforms an effect;
- transforms terrain/object/etc.

A generic transformation mechanic may be real,
but it is not automatically a champion alternate-form mechanic.

---

## A — Separate two concepts

Distinguish:

1. GENERIC TRANSFORMATION SEMANTIC

A spell/passive can factually transform something.

This may keep the semantic effect:

TRANSFORMATION

when evidence supports it.

2. CHAMPION FORM / KIT COMPLEXITY

ALTERNATE_FORM_POSSIBLE must require evidence that:

- the champion transforms themselves;
- the champion enters/leaves another form;
- a named champion form is entered;
- the champion switches stance/form in a way that changes their state/kit;
- the ability set changes because of that form.

Do not derive ALTERNATE_FORM_POSSIBLE from generic TRANSFORMATION alone.

---

## B — Self / subject-aware evidence

Complexity evidence should be conservative.

Positive concepts:

- "se transforme en..."
- "prend sa forme de dragon"
- "alterne entre forme humaine et..."
- "change de forme"
- "change de posture" only when the champion's own combat state/ability set is affected

Negative concepts:

- "transforme les dégâts..."
- "transforme la cible..."
- "transforme la marque..."
- "transforme la ressource..."
- "transforme l'effet..."
- "l'ennemi est transformé..."
- generic linguistic use of "forme"

If subject/state ownership cannot be established:

do NOT mark CONFIRMED alternate form.

Prefer:
PLAUSIBLE_BUT_UNDERMODELED
or no alternate-form flag.

---

## C — Complexity evidence classification

Do not label evidence CONFIRMED merely because a keyword rule matched.

CONFIRMED_COMPLEX_MECHANIC should require evidence whose semantics itself
supports champion kit/state complexity.

Keep:

- CONFIRMED_COMPLEX_MECHANIC
- PLAUSIBLE_BUT_UNDERMODELED
- FALSE_POSITIVE
- UNRESOLVED

but make their assignment evidence-based rather than keyword-self-confirming.

---

## D — Re-audit current 31 complex champions

Current Phase 2B1-B baseline:

- 142 STANDARD_KIT
- 31 COMPLEX_KIT_UNDERMODELED
- 28 ALTERNATE_FORM_POSSIBLE
- 3 COPIED_OR_DYNAMIC_ABILITY

Audit every current non-standard champion.

For each report:

- champion
- final flags
- source passive/spell
- exact evidence text
- what entity/state is being transformed or copied
- review status

Particularly inspect champions currently reported as confirmed but whose
normal kit does not obviously contain alternate forms, including:

- Ashe
- Jarvan IV
- Jhin
- Kennen
- Lissandra
- Lulu
- Maokai
- Senna
- Volibear
- Yorick
- Zeri
- Zyra

Do NOT hardcode these champion names into production rules.

They are audit targets only.

---

## E — Expected genuinely complex examples

The generic rules should still be capable of surfacing real complex structures
when supported by Data Dragon evidence, for example:

- alternate/self forms;
- stance systems;
- copied abilities;
- possession/dynamic ability kits.

Do not weaken genuine cases merely to reduce counts.

---

## F — Synthetic tests

Add deterministic tests:

Positive alternate form:
"Shifts into dragon form and changes abilities."
→ ALTERNATE_FORM_POSSIBLE

Positive self transformation:
"The champion transforms into another form."
→ alternate-form evidence

Negative generic transformation:
"Transforms 20% of damage into magic damage."
→ may have TRANSFORMATION semantic
→ must NOT produce ALTERNATE_FORM_POSSIBLE

Negative target transformation:
"Transforms the enemy into a harmless creature."
→ transformation mechanic possible
→ champion itself NOT alternate form

Negative resource transformation:
"Transforms Fury into a shield."
→ no alternate-form flag

Copied ability:
preserve COPIED_OR_DYNAMIC_ABILITY when explicitly supported.

---

## G — TRANSFORMATION semantic

Do not necessarily remove TRANSFORMATION as a factual spell semantic.

Instead make clear what it means:

TRANSFORMATION = some transformation mechanic is described.

It must NOT be interpreted by future consumers as:

"the champion changes form"

unless champion-form complexity evidence separately supports that.

Document this distinction.

---

## H — Real catalog audit

Rerun all 173 champions.

Report before/after:

- STANDARD_KIT
- COMPLEX_KIT_UNDERMODELED
- ALTERNATE_FORM_POSSIBLE
- COPIED_OR_DYNAMIC_ABILITY
- TRANSFORMATION semantic count

List every remaining ALTERNATE_FORM_POSSIBLE champion with evidence.

List every remaining COPIED_OR_DYNAMIC_ABILITY champion with evidence.

List removed false positives.

The goal is credibility, not a specific count.

---

## I — Freeze boundary

Do NOT modify:

- Death Analyzer v11
- Jungle Tempo / Pathing v17
- Objective Analyzer v20
- Recall / Reset Analyzer v21
- Build / Itemization Analyzer v22 Phase 1
- Item Knowledge Phase 2A

Do NOT start:

- runes
- level-resolved stats
- executable formulas
- damage engine
- Burst / TTK
- composition
- recommendations
- ML

---

## Freeze criteria

Champion Knowledge Phase 2B1 becomes freeze-ready if:

- generic transformation no longer implies champion alternate form;
- remaining complexity flags have evidence that actually supports the flag;
- no champion-specific production hacks are used;
- raw TRANSFORMATION semantics and champion-form complexity are clearly separated;
- tests pass;
- 173-champion audit passes;
- frozen layers remain unchanged.

Do not demand zero uncertainty.

---

## Testing

Run:

- py_compile
- Champion Knowledge synthetic checks
- Champion Knowledge precision checks
- new transformation/complexity tests
- full 173 champion audit

---

## Reporting

Update:

- PROJECT_STATE.md
- TODO.md → COMPLETED
- LAST_RUN.md

Finish:

REVIEW_REQUIRED

Do not freeze yourself.

---

## Git

Commit and push.

Suggested commit:

Separate champion forms from transformation semantics
