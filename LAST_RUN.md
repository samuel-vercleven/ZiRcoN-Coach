# LAST RUN

## Status
PASS / REVIEW_REQUIRED FOR BUILD OPTIMIZER V1 FREEZE.
Contextual heuristic technical gates PASS; gameplay review and coverage remain open.

## Date
2026-09-10 local

## Command
`python -m build_optimizer.validation`:
- `python -m app.stabilization_checks final` (includes `python main.py`);
- `python -m build_optimizer.checks`;
- `python -m build_optimizer.gate_checks`;
- `python -m build_optimizer.catalog_checks`;
- `python -m build_optimizer.replay --mode golden`;
- `python -m build_optimizer.replay --mode batch`.
- `python -m build_optimizer.contextual_replay`.

## Runtime
- All seven child commands completed successfully; about 228 seconds combined.
- Latest main.py: PASS, via the Stable Base runner.
- Validation intentionally returns nonzero for the blocked product gate.
- Main raw output: logs/latest_full_run.txt.
- Baseline: logs/build_optimizer/baseline/.
- Final logs/gate: logs/build_optimizer/final/zero_gate.json and command logs.

## Files changed
- New build_optimizer/: catalog view, prefix context, recipe planner, diagnostic
  scoring, abstaining headless API, unit/scenario checks and real audit runners.
- BUILD_OPTIMIZER_AUDIT.md, BUILD_OPTIMIZER_EVALUATION.md, TODO.md,
  PROJECT_STATE.md, DECISIONS.md, LAST_RUN.md.
- No main.py, existing analyzer, knowledge layer, service or UI file modified.
- Six pre-existing stabilization-document deletions remain unstaged user changes.

## Tests executed
- Baseline main.py + 43/43 Stable Base suites: PASS.
- Final compile: 169 modules; 43/43 Stable Base suites: PASS.
- 23 new unittest methods including ten scenario subcases: PASS.
- 15 adversarial product-gate checks: PASS.
- Contextual Shyvana AP checks, exact 16.18.1 item profiles: PASS.
- Chronological Shyvana replay: 14 nonempty / 166 abstentions, 0 invalid
  purchases, future leaks, score recomputation errors or untraceable reasons.
- Real catalog recipes: 3 patches, 8,385 controlled cases, 13,552 steps: PASS.
- Seven Golden Games: 28 nominal and 28 preceding-frame temporal checks: PASS.
  No admissible own inventory for recipe execution on those seven games;
  Golden recipe result explicitly NOT_EXERCISED, not a vacuous PASS.
- Batch: 129 local SoloQ games, 516 nominal checks + 516 preceding-frame
  mutation checks, 516 prefix-sensitivity checks: PASS.
- 50 observed-frame snapshots admit recipe diagnostics: 10,760 plans,
  13,942 steps, 1,482 model-completable targets; invoice/slot invariants PASS.
- Frozen guard: all 89 baseline paths unchanged.
- Secret scan and git diff --check against pre-optimizer baseline: PASS.

## Errors encountered
- Initial baseline launch blocked by temporary authorization-service usage limit;
  succeeded after user continuation.
- Initial frame-gap check rejected Riot's ordinary millisecond drift; fixed to
  the existing GameContext 90-second admission contract and regression-tested.
- Gold at a nominal minute is not interpolated or borrowed from a later frame.
  Earlier sampled budgets are tested with the complete earlier inventory.
- Trailing EOF blank lines in the first checkpoint were found and corrected;
  final baseline-relative diff check passes.
- Recipe audit gap found: its prior independent invoice accepted unrelated,
  duplicate/excess and ancestor+descendant component credits. Fixed by a
  separately traversed target recipe tree; off-recipe steps and invalid IDs are
  now rejected. No frozen code changed.

## Main analyzer results
- Frozen v11/v22 and Phases 2A–2I unchanged.
- v22 reconstruction reused on event prefixes, with no final inventory reference;
  retrospective reliability is not admitted as contemporaneous evidence.
- Ambiguous item events, unobserved rune grants and possession stay PARTIAL.
- Contextual heuristic outputs: 14 real nonempty Shyvana AP recommendations;
  their scores and reasons are recomputed from explicit contributions.
- All requested scenario names remain evidence-gated; observed synthetic
  HP/AD/AP/MR do not manufacture a matchup utility function.

## Suspicious findings
- v22 full-history reliability consults later acquisitions/replacements and
  final inventory; filtering its output afterwards would leak information.
- Item Knowledge applicability does not prove all client purchase restrictions.
- 7 Golden / 39 batch requests fall after the last observed frame; no current
  state is invented. Earlier snapshots are identified separately.
- Golden and batch overlap; timestamp counts are not independent game outcomes.
- The ignored local DB contained 129 SoloQ games on this final run (118 in the
  prior checkpoint); the current count is reported as local audit coverage, not
  a frozen dataset invariant.

## Methodological concerns
- No owner promotion, stat arithmetic, LLM, ML or new combat model.
- EconomyValue weight 1 only preserves recipe-coverage-fraction units;
  eight gameplay/legality factors remain null/UNMODELED.
- Diagnostic subtotal is not a final utility score. No price-ranked best item.
- Empty buy_now means zero emitted invalid purchases, not validated legality.
- The Zero Gate marks four product lines BLOCKED instead of converting empty
  outputs into zero-error PASS counts.

## Remaining issues
- Gameplay quality needs human review; heuristic is not a combat/optimality proof.
- Local exact-patch replay has 14/20 nonempty rows, below the requested review target.
- Shop access remains UNMODELED; plans are conditional on shopping now.
- Golden raw fixtures and DB remain local-only.

## Codex technical recommendation
Review the 14 contextual rows in BUILD_OPTIMIZER_EVALUATION.md before a freeze
decision. No successor work started.

## Review request
REVIEW_REQUIRED: product quality and coverage threshold require human review;
Build Optimizer v1 is not frozen.
