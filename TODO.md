# ZiRcoN Coach — TODO

## Current task
COMPLETED — Phase 2A-C — Conservative semantic completeness fix before freeze.

## Status

Completed by Codex on 2026-08-18.

Result: REVIEW_REQUIRED.

No next major task is defined here; project review should decide whether Phase 2A-C is freeze-ready.

## Goal

Fix one remaining semantic completeness issue in Item Knowledge.

Phase 2A-B is otherwise accepted.

Do NOT redesign the parser.
Do NOT expand the semantic taxonomy.
Do NOT start champion knowledge.

---

## Problem

Current partial parsing splits section text mainly on:

- newline
- .
- ;
- !
- ?

A fragment is then considered parsed if it contains a matched semantic phrase.

This can incorrectly mark a multi-mechanic sentence as fully understood.

Example:

"Inflige 100 dégâts et vous confère 30% de vitesse d'attaque pendant 4 sec."

If ACTIVE_DAMAGE is recognized but the temporary attack-speed buff is not,
the whole sentence must NOT be considered fully parsed.

A recognized phrase inside a fragment is not evidence that every mechanic
inside that fragment is understood.

---

## Part A — Conservative completeness semantics

Make section completeness conservative.

A section may be FULLY_PARSED only when the parser has sufficient evidence
that no meaningful mechanic text remains unexplained.

If completeness cannot be demonstrated:

mark it PARTIALLY_PARSED
and preserve the original section text / unresolved text.

Do not attempt aggressive natural-language interpretation.

It is acceptable for FULLY_PARSED counts to decrease significantly.

Precision and auditability are more important than coverage.

---

## Part B — Same-sentence multi-mechanic tests

Add deterministic tests for cases such as:

1.

"Inflige 100 dégâts magiques et vous confère 30% de vitesse d'attaque."

Expected:
- ACTIVE_DAMAGE extracted
- section NOT FULLY_PARSED
- attack-speed-related remaining text preserved

2.

"Vous gagnez un bouclier et votre prochaine attaque ralentit la cible."

If only part of the mechanics are understood:
- recognized effects preserved
- remaining mechanic preserved
- section PARTIALLY_PARSED

3.

A genuinely simple section containing only one fully recognized mechanic.

Example:
"Inflige 100 dégâts magiques à la cible."

This MAY be FULLY_PARSED if the implementation can safely demonstrate it.

4.

Completely unknown sentence:
- COMPLETELY_UNPARSED
- original text preserved

---

## Part C — No silent text loss invariant

Add an explicit synthetic invariant:

Semantic parsing must never discard source effect text merely because one
effect was extracted from the same sentence.

For every description effect section, future consumers must always have access
to:

- original section text
- extracted effects
- parse completeness
- unresolved text when completeness is not proven

Raw source text must remain available regardless.

---

## Part D — Real catalog audit

Rerun the full current Data Dragon catalog.

Report:

- resolved version
- total items
- items with effects
- FULLY_PARSED sections
- PARTIALLY_PARSED sections
- COMPLETELY_UNPARSED sections
- unsupported locale sections
- graph issues
- representative diagnostics

Specifically inspect several sections containing multiple mechanics in one
sentence.

Do not optimize the counts.

A rise in PARTIALLY_PARSED is acceptable and may be desirable.

---

## Accepted Phase 2A-B work

Do not reopen without a demonstrated bug:

- semantic false-positive hardening
- EXECUTE quest fix
- percent-health damage contextual checks
- ACTIVE_DAMAGE contextual checks
- ACTIVE_SHIELD vs shield reduction
- CLEANSE contextual checks
- TRANSFORMATION contextual checks
- ON_HIT_DAMAGE damage requirement
- explicit fr_FR parser contract
- recursive component multiplicity
- patch-aware Data Dragon data
- provenance/raw data preservation

---

## Frozen boundary

Do NOT modify:

- Death Analyzer v11
- Jungle Tempo / Pathing v17
- Objective Analyzer v20
- Recall / Reset Analyzer v21
- Build / Itemization Analyzer v22 Phase 1

---

## Do NOT start

- champion knowledge
- rune knowledge
- damage simulation
- Burst / TTK
- composition analysis
- contextual builds
- recommendations
- ML

Burst / TTK remains a future feature after the knowledge/data layers are frozen.

---

## Testing

Run:

- py_compile
- existing synthetic checks
- existing precision checks
- new same-sentence completeness tests
- real Data Dragon catalog audit

---

## Reporting

Update:

- LAST_RUN.md
- PROJECT_STATE.md
- TODO.md → completed

Finish with:

REVIEW_REQUIRED

Do not freeze Phase 2A yourself.

---

## Git

Commit and push.

Suggested commit:

Make item semantic completeness conservative
