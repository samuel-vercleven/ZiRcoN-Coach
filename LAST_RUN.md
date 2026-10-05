# LAST RUN

## Status
TECHNICAL PASS / REVIEW_REQUIRED for display and gameplay review — NO FREEZE

## Date
2026-10-05 22:31 Europe/Paris

## Command
- python -m app.quick_checks
- python -m app.stabilization_checks final
- python run_app.py --qml --smoke-check --smoke-output logs/qml-smoke.json
- Same QML smoke with isolated ZIRCON_DATA_DIR (fresh profile)

## Runtime
- Full source regression: 44/44 command suites PASS, including real main.py.
- Nine focused QML bridge tests PASS. QML smoke: three real matches, 30 captures
  at 1600×960 and 1120×720; zero QML warnings or Python callback errors.
- Fresh-profile smoke: zero matches, six captures, classic-settings round trip
  and clean shutdown. Existing history was not replaced.
- Classic UI smoke/semantics pass in the full regression. One QML root survives
  navigation; repeat match selection reuses the optimizer result.
- All 89 FROZEN paths unchanged; secret scan and whitespace checks pass.
- Eight optimizer gates were not rerun: no scoring, inventory, recipe, semantic
  profile, temporal threshold or analyzer code changed. Their prior accepted
  results remain in BUILD_OPTIMIZER_AUDIT/EVALUATION and the rc2 run.

## Files changed
- ui/quick/bridge.py: player-facing DTOs, cached images, bounded workers,
  GUI-thread delivery, stale-result and account guards.
- ui/quick/qml/*: native surfaces, real history/teams, gold chart, coaching
  disclosures, build/context and alternatives, reduced-motion option.
- app/quick_application.py, run_app.py, Essayer-interface-QML.vbs: opt-in launch,
  shared instance lock, classic round trip and render smoke.
- app/quick_checks.py, app/stabilization_checks.py: validation.
- packaging/zircon.spec: include QML sources in future builds.
- README, QML_PREVIEW, PROJECT_STATE, TODO and DECISIONS updated.

## Tests executed
- Missing KDA/CS/or/result stay missing; empty items stay invisible.
- Chart retains gaps and real timestamps; signed segments split at zero.
- Build keeps the existing dated enemy snapshot, not final rosters.
- Tuple-backed reasons/opponents/purchases converted to QML arrays.
- Delayed completion cannot overwrite another game or populate a new account's
  UI cache; refresh clears prior presentation state.
- Worker delivery checked against the application's GUI thread.
- Desktop/minimum history, summary and real Viego purchase captures inspected.
- Normal Windows QML launch and actual live home capture inspected; one visible
  ZiRcoN window remains open for the user. Automated match checks use software.
- Longer explanations collapse while full evidence remains accessible.

## Errors encountered
- Development QML name collisions and invalid compact separators fixed.
- Visual inspection caught missing tuple-backed build fields and narrow-team
  item/stat overlap; corrected and rerendered.
- Alternative disclosure scope and teardown bindings corrected.
- Final QML smoke includes shutdown and has zero warnings.

## Main analyzer results
- Same backend services and strict historical/patch/legality gates. No new
  analytical inference or formula in this frontend.
- Actual Viego match EUW1_7986552283 displays Kraken advice at 09:00 on 16.18,
  dated enemy stats, conditional purchases and alternatives.

## Suspicious findings
- None in final checks. Visual polish is not proof of coaching quality.

## Methodological concerns
- No frozen or scoring changes. Missing/unsupported inputs still abstain.

## Remaining issues
- Opt-in exploration, not a full QML migration: settings/imports, notes and
  advanced legacy details use the classic UI in the same process.
- Software-render QA completed; human display/GPU/DPI/gameplay review remains.
- Prior portable rc3 ZIP unchanged. New QML bundle not rebuilt or verified.

## Codex technical recommendation
Try Essayer-interface-QML.vbs and compare the real match pages on the user's PC.

## Review request
REVIEW_REQUIRED for product/display acceptance, NO FREEZE.
Commit/push only on feature/build-optimizer; no merge into main.
