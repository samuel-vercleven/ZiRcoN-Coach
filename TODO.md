# ZiRcoN Coach - TODO

## Current task
COMPLETED - Phase 2A-B - Item Knowledge precision audit before freeze.

## Status
- Implemented by Codex.
- Finished as REVIEW_REQUIRED for project review.
- Phase 2A is still not FROZEN.
- No FROZEN analyzer was modified.
- No champion knowledge, composition analysis, build recommendation, GOOD/BAD label, Itemization Score, statistical learning, or ML was started.

## Completed scope
- Audited and hardened high-risk semantic effect rules.
- Removed the false implication that a Data Dragon `OnHit` tag alone means ON_HIT_DAMAGE.
- Required contextual damage evidence for `*DAMAGE` semantic effects.
- Prevented "achève une quête" from producing EXECUTE.
- Distinguished active shield grants from shield reduction.
- Required CC/debuff context for CLEANSE.
- Avoided treating generic "améliore" text as TRANSFORMATION.
- Preserved mixed parsed/unparsed sections as PARTIALLY_PARSED_EFFECT_TEXT.
- Added fully / partially / completely unparsed section coverage.
- Preserved recursive component multiplicity and exposed recursive_component_counts.
- Made the locale contract explicit: semantic parsing is SUPPORTED for fr_FR and UNSUPPORTED_LOCALE otherwise.
- Added positive and negative semantic precision tests.
- Added component multiplicity tests.
- Reran the real Data Dragon catalog audit and sensitive semantic diagnostics.

## Important result
- Resolved Data Dragon version: 16.16.1.
- Item knowledge version: item_knowledge_phase2a_b_v1.
- Total Data Dragon item records audited: 868.
- Purchasable Summoner's Rift items: 254.
- Items with extracted effects: 414.
- Items with description effects: 357.
- Items with UNPARSED/PARTIAL effect text: 396.
- Fully parsed sections: 198.
- Partially parsed sections: 151.
- Completely unparsed sections: 384.
- Graph inconsistencies: 0.
- Repeated direct-component recipes: 45.
- Repeated recursive-component recipes: 170.
- Representative diagnostics coverage: 18/18.

## Review handoff
Project review should inspect:
- LAST_RUN.md.
- PROJECT_STATE.md.
- knowledge/item_knowledge.py.
- knowledge/item_knowledge_synthetic_checks.py.
- knowledge/item_knowledge_precision_checks.py.
- logs/item_knowledge_phase2ab_precision_audit.txt if local raw audit details are needed.

## Next task
Not defined by Codex.

Next major task remains for ChatGPT / project review.
