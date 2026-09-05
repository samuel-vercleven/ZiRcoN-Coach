# LAST RUN

## Status
PASS / REVIEW_REQUIRED FOR ALPHA FREEZE

## Date
2026-09-05 02:43 local

## Command
Death v11 V0.1 adapter audit, complete Alpha validation stack, then `.\.venv\Scripts\python.exe main.py`.

## Runtime
- completed
- final `python main.py`: 2.31 seconds wall-clock; harness-reported duration 2.20 seconds

## Files changed
- `services/post_game_analysis.py`: exact Death v11 field mapping and independent adapter-cache version
- `app/v01_death_adapter_check.py`: regression coverage for present versus genuinely absent v11 fields
- `app/v01_alpha_checks.py`: cache/provenance compatibility update
- `ui/pages/match_detail_page.py`: stable multi-label summary layout and immediate stale-widget removal/reset
- `PROJECT_STATE.md`, `TODO.md`, `DECISIONS.md`, `LAST_RUN.md`: audit evidence and durable adapter rule
- no Death Analyzer v11 or other FROZEN production/validation file changed

## Tests executed
- raw Death v11 audit on five real matches with 11 deaths each: 55 rows; 55/55 pre-death states available; 0 raw missing state
- current V0.1 report regeneration: 22 matches; all five 11-death reports `AVAILABLE`, 11 evidence rows each, 0 `UNKNOWN` state
- `python -m app.v01_death_adapter_check`: PASS
- Python compilation of all Alpha modules: PASS
- `python -m app.v01_alpha_checks`: PASS
- `QT_QPA_PLATFORM=offscreen python -m app.v01_alpha_smoke`: PASS
- `python -m app.v01_analyzer_adapter_check`: PASS (5/5 frozen analyzer sections)
- `QT_QPA_PLATFORM=offscreen python -m app.v01_visual_check`: PASS (9 screenshots)
- native Windows render of the real 11-death post-game: PASS; state/cost/context evidence readable with no overlap
- `python -m app.v01_alpha_audit`: PASS / REVIEW_REQUIRED FOR ALPHA FREEZE (122 matches, 118 timelines, 22 analyzed matches, 5/5 adapters)
- `python main.py`: PASS, including Phase 2I validation and FROZEN guard

## Errors encountered
- the audit proved an adapter mapping bug: it requested nonexistent aliases `death_advantage_state` / `advantage_state` and `personal_cost_score` / `death_cost_score`
- v11 actually exposes `advantage_state_before_death` and `resource_cost_score`; the adapter was corrected without changing v11
- native render exposed a transient empty-state overlay and summary-height issue; both were fixed in the Alpha page and revalidated

## Main analyzer results

### Death Analyzer
- FROZEN v11 remains unchanged
- real audited fields include pre-death advantage state, historical resource-cost score/label, killer and role, approximate zone, impact interval, relative Gold/CS/XP costs, trade/objective/tower context, death-chain and death-spiral evidence
- v11 does not expose a generic causal `cause`; the UI therefore presents factual killer/context evidence only
- five audited 11-death matches: 55/55 states mapped, 0 adapter-created `UNKNOWN`

### Current product
- Death adapter cache version is `death_analyzer_v11__v01_adapter_v2`; frozen provenance displayed to the user remains `death_analyzer_v11`
- stale v1 payloads are retained in SQLite but fail closed and are not treated as current
- current compatible cache: 110 reports across 22 matches

## Suspicious findings
- none

## Methodological concerns
- approximate zone, post-death events, trade and chain/spiral fields remain labeled as v11 context/evidence, not causal explanations
- `UNKNOWN` is emitted only when `advantage_state_before_death` is genuinely absent from the frozen output

## Remaining issues
- V0.1 Alpha remains unfrozen pending project review
- no new Death v11 limitation was identified by this adapter audit

## Codex technical recommendation
- review the corrected V0.1 Alpha Death presentation for Alpha freeze; do not reopen frozen Death v11

## Review request
- REVIEW_REQUIRED FOR ALPHA FREEZE because the product milestone is not self-frozen by Codex
