# LAST RUN

## Status
PASS — technical stabilization checks.
REVIEW_REQUIRED — Stable Base scope / latest-patch compatibility; not a freeze.

## Date
2026-09-07 21:30 local

## Command
`python -m app.stabilization_checks final`, real knowledge audits, pinned Phase 2D
audit, Golden Games, full local batch, V0.1 audits, native UI checks, and
`python run_app.py`. The regression runner executes `python main.py`.

## Runtime
- Completed; main.py rerun in the final validation stack.
- Raw main output: `logs/latest_full_run.txt`.
- Detailed regression/audit logs and recoverable snapshots: `logs/stabilization/`.

## Files changed
- Additive scoped cache, GameContext boundary, services/DTO uncertainty handling.
- API/profile/sync robustness, cache errors, confined assets, full key masking.
- Qt stale-card lifecycle, bounded badges/header, scrollable Settings.
- Stabilization inventory, golden expectations, regression/audit runners and docs.
- No FROZEN file or main.py changed; no analyzer removed.
- User's existing TODO.md deletion is preserved locally and excluded from commits.

## Tests executed
- Compile 159 Python modules: PASS.
- Existing baseline: 41/41 command suites; final: 43/43 command suites: PASS.
- New focused unittest regressions: 22/22 PASS.
- Golden E2E: 7/7 real games, 33 deaths, 35 reports: PASS.
- Complete local input/death audit: 118 games, 680/680 raw/frozen deaths: PASS.
- Real five-match adapter/cache parity audit: PASS; 20 Tempo phases, 38 objective
  events, 50 resets, five builds. Counts are not mislabeled as independent N/N coverage.
- Default real knowledge audit commands: 21/22 PASS, one REVIEW_REQUIRED (below).
- Exact frozen Phase 2D 16.16.1 audit: PASS, 173/173 ratios, no blocking/review.
- Alpha service/API mocks, account scope, adapters, UI/status, offscreen smoke,
  V0.1 audit: PASS.
- Native Qt captures: 22 generated; product pages inspected at 1400x850/1100x700.
- python run_app.py: real native window opened, confirmed, closed normally, exit 0.
- main.py and 89-path baseline-aware FROZEN guard: PASS.
- Secret scan and git diff --check: PASS.

## Errors encountered
- Three initial regression failures demonstrated unscoped reports and NULL -> LOSS.
- Golden Support assumption EXACT disproved by v22's real missing item 3871;
  preserved PARTIAL and added an explicit assertion; raw expected facts unchanged.
- A new Qt cleanup initially released the widget reference after reparenting;
  retained a local reference and reran native/repeated-refresh checks successfully.
- The new overlap fixture initially lacked two required v11 fields; fixture
  completed according to the actual contract, without frozen changes.
- Minimum-size test now uses the real application stylesheet.
- Final review reproduced legacy global sync attribution for a selected account
  with no local games. Status now uses the selected PUUID or stays OFFLINE;
  regression includes both an unresolved identity and an account without games.
- Phase 2D default audit selected latest 16.17.1 while its ratio source is pinned
  to 16.16. It correctly refuses incompatible AS resolution, not a Python crash.

## Main analyzer results
### Death Analyzer
- v11 unchanged: 680 observed deaths, 680 measured rows, no missing death on this corpus.
- Golden timestamps/frame resource projections and bracket Gold arithmetic
  independently cross-checked against raw Riot data.
- Same-game/future leakage and overlapping objective deduplication checks pass.
- Bracket cost/composite interpretation explicitly EXPERIMENTAL, not causal.

### Current product
- Final presentation versions: Death/Tempo/Objectives/Build v4, Reset v3.
- Latest 20 cache: 100 reports; 20 Death AVAILABLE; each Jungle-only analyzer
  18 AVAILABLE and 2 UNAVAILABLE; Build 2 AVAILABLE and 18 PARTIAL.
- Global match badges: 1 AVAILABLE / 19 PARTIAL. Coverage was not preserved
  at the expense of interval reliability.
- Missing data, wrong-account reports, team-context fault labels and stale global
  sync attribution fail closed. Frozen provenance/status remain distinguishable.

## Suspicious findings
- Support final item 3871 is not reconstructed in EUW1_7959361127; PARTIAL retained.
- Exact final inventory does not imply reliable intermediate inventory.
- Latest-patch attack speed cannot use a pinned older ratio source.

## Methodological concerns
- No causal death/reset/objective claim; no threshold/FDR/leakage retuning.
- No stat-owner research reopened, no owner promoted, no stat evaluator or optimizer.
- Frozen validation is patch-scoped; it is not latest-patch combat completeness.

## Remaining issues
- Phase 2D latest 16.17: 0/173 accepted ratios and 2907 unresolved AS rows;
  separate pinned 16.16.1 regression passes.
- Legacy SQL projections/latest helpers remain; future consumers must honor
  explicit admission, version and reliability contracts.
- Golden raw fixtures are local-only; missing fixtures elsewhere fail explicitly.
- No live Riot key validation or Riot sync was performed in this pass (mocks and
  local history used); public Data Dragon catalog loading was real.

## Codex technical recommendation
Review STABILIZATION_REPORT.md before any stable-base tag.
NO-GO for a generic current-patch Build Optimizer without reviewed admissibility
contracts. No successor feature has been started.

## Review request
REVIEW_REQUIRED for Stable Base scope and accepted limitations. Do not self-freeze.
