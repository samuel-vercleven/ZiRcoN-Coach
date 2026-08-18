# LAST RUN

## Status
REVIEW_REQUIRED

## Date
2026-08-18 17:29 local

## Command
python -m knowledge.item_knowledge

## Runtime
- completed
- approximate duration: about 1-2 seconds for the real Data Dragon catalog audit
- `python main.py` was not run because Phase 2A-B did not integrate with the dev harness
- raw Phase 2A-B audit output saved locally to logs/item_knowledge_phase2ab_precision_audit.txt

## Files changed
- knowledge/item_knowledge.py
- knowledge/item_knowledge_synthetic_checks.py
- knowledge/item_knowledge_precision_checks.py
- PROJECT_STATE.md
- TODO.md
- LAST_RUN.md

## Tests executed
- `.venv\Scripts\python.exe -m py_compile knowledge\item_knowledge.py knowledge\item_knowledge_synthetic_checks.py knowledge\item_knowledge_precision_checks.py`
- `.venv\Scripts\python.exe -m knowledge.item_knowledge_synthetic_checks`
- `.venv\Scripts\python.exe -m knowledge.item_knowledge_precision_checks`
- `.venv\Scripts\python.exe -X utf8 -m knowledge.item_knowledge`

## Errors encountered
- Initial non-escalated Python commands failed because the venv points to Python under AppData and the sandbox denied access.
- Re-ran the same commands with required escalation; compile/tests/audit passed.
- Precision tests exposed one missing DAMAGE_REDUCTION phrasing; fixed by recognizing "dégâts subis sont réduits".
- Real audit exposed additional false-positive risks in ACTIVE_DAMAGE and PERCENT_MAX_HEALTH_DAMAGE; tightened damage-action and threshold-context checks, then reran tests and audit.

## Main analyzer results
### Death Analyzer
- v11 not modified; remains FROZEN.

### Tempo / Pathing
- v17 not modified; remains FROZEN.

### Objective Analyzer
- v20 not modified; remains FROZEN.

### Recall / Reset Analyzer
- v21 not modified; remains FROZEN.

### Current analyzer
- Build / Itemization Analyzer v22 Phase 1 not modified; remains FROZEN.
- Item Knowledge Base Phase 2A-B precision pass implemented.
- No champion knowledge, composition analysis, build recommendation, item GOOD/BAD label, Itemization Score, personal/global statistical learning, or ML was added.

Phase 2A-B audit:
- Item knowledge version: item_knowledge_phase2a_b_v1.
- Locale: fr_FR.
- Semantic parser status: SUPPORTED for 868 records.
- Requested game version: LATEST.
- Resolved Data Dragon version: 16.16.1.
- Version resolution: LATEST.
- Fallback used: False.
- Total item records: 868.
- Purchasable Summoner's Rift items: 254.
- Items with normalized stats: 655.
- Items with extracted effects: 414.
- Items with description effects: 357.
- Items with unparsed / partial effect text: 396.
- Items with UNKNOWN metadata: 0.
- Items with unknown raw stats preserved: 0.
- Fully parsed description effect sections: 198.
- Partially parsed description effect sections: 151.
- Completely unparsed description effect sections: 384.
- Unsupported-locale sections in this fr_FR audit: 0.
- Graph inconsistencies: 0.
- Repeated direct-component recipes: 45.
- Repeated recursive-component recipes: 170.
- Duplicate IDs: 0.
- Duplicate names: reported and preserved as Data Dragon variants.
- Mode-specific / non-SR items: 552.
- Champion-specific items: 7.
- Non-purchasable items: 172.
- Representative diagnostics coverage: 18/18 required families, none missing.

Targeted semantic deltas vs Phase 2A baseline:
- ON_HIT_DAMAGE: -130.
- PERCENT_MAX_HEALTH_DAMAGE: -36.
- MOVEMENT_SPEED_TRIGGER: -20.
- STACKING_EFFECT: -11.
- ACTIVE_DAMAGE: -6.
- EXECUTE: -6.
- TRANSFORMATION: -6.
- CLEANSE: -3.
- ACTIVE_SHIELD: -2.
- PERCENT_CURRENT_HEALTH_DAMAGE: -1.
- HARD_CC: 0.

## Suspicious findings
- 396 items retain UNPARSED_EFFECT_TEXT or PARTIALLY_PARSED_EFFECT_TEXT. This is intentional and preferable to false semantic certainty.
- Some active consumables still classify as ACTIVE_DAMAGE only when their section includes explicit damage-action evidence; project review should inspect these examples.
- 45 direct and 170 recursive repeated-component recipes are now visible instead of being deduplicated away.

## Methodological concerns
- REVIEW_REQUIRED because Phase 2A-B changes the semantic parser/taxonomy behavior and should be reviewed before freeze.
- The parser is explicitly fr_FR-only for description semantics.
- Description-derived effects remain parser outputs with evidence, not gameplay advice.

## Remaining issues
- Phase 2A is still not FROZEN.
- No Phase 2B champion/composition/recommendation work was started.
- Future consumers must explicitly handle UNKNOWN, UNPARSED_EFFECT_TEXT, and PARTIALLY_PARSED_EFFECT_TEXT.

## Codex technical recommendation
- Project review should inspect the sensitive semantic diagnostics, especially ACTIVE_DAMAGE and percent-health families, before declaring Phase 2A freeze-ready.

## Review request
REVIEW_REQUIRED because Phase 2A-B is implemented and tested, but semantic precision and parser coverage require project review before freeze.
