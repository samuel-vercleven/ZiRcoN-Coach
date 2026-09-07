# Stable Base v1 — initial audit

Baseline: `ca119d1ed304594345ae17c09dbadff142fb5f5f`, restoration tag
`pre-stabilization-v1`, branch `stabilization/stable-base-v1`.
The user-supplied stabilization pack supersedes the completed Alpha TODO;
the local deletion of TODO.md is preserved, not restored over user work.

## Strengths

- Separate desktop launcher, local SQLite browsing, runtime key replacement.
- Frozen knowledge preserves patch provenance and unresolved semantics.
- Death v11 uses a pre-death frame and a strictly post-death frame, not interpolation.
- Death historical reference is appended by whole game; outcome validation uses game summaries.
- Existing Alpha service checks pass before corrections.

## Confirmed integration defects and correction order

1. Reports are keyed only by match/analyzer/version. Two accounts in the same game
   can share the wrong player's report. Add account-bound payload provenance and
   fail closed for legacy unscoped reports; preserve old rows.
2. Empty Death output is AVAILABLE without verifying raw death count or timeline.
   Check raw/normalized input completeness before admitting an analyzer report.
   Dependency exceptions currently become empty inputs for downstream analyzers.
3. Local match DTOs convert NULL KDA/CS/duration/result to zeros/loss. Preserve
   missing values and exclude incomplete inputs from affected aggregates.
4. Existing real adapter audit compares a cache to the same projection and prints
   available/available counts. This is cache parity, not independent field coverage.
   Add independent golden raw-to-SQL-to-frozen-to-report checks.

## Death measurement boundaries (no frozen edits)

`*_cost_60` retains a legacy name: it is the observed **frame bracket** around a
death, not 60 seconds of causal post-death loss. Frames may cover actions before
the death and deaths can share brackets. Recovery, event windows and chains are
contextual/proxy evidence. Summed episode losses are not net loss. Present these
interpretations as `EXPERIMENTAL`, retain raw components, and never infer fault.
Game-level inference already controls outcome pseudoreplication; this does not
make overlapping within-game resource episodes additive independent effects.

## Duplication / debt

Database readers expose multiple JSON/SQL projections; Tempo's NULL resource
fallback is zero. Legacy Data Dragon version helper falls back to latest.
Frozen knowledge has stricter patch handling: future consumers must use it.
Add a small non-mutating GameContext boundary, not a frozen-reader rewrite.
The GUI services accept an injected database, while frozen readers use the
legacy global DB path: do not claim arbitrary-DB analyzer support without a guard.
`main.py` executes Phase 2I only; run the broader checks separately.
Its FROZEN guard examines uncommitted status only; additionally compare Git blobs
to the restoration baseline to cover checkpointed modifications.

## Checkpoint results

Seven Golden Games passed the full raw -> SQL -> GameContext -> Death -> knowledge
-> cached report path (33 deaths, 35 reports). The initial extra assumption that
every role would reconstruct EXACT was disproved: Support match EUW1_7959361127
has final Riot item 3871 absent from frozen v22 reconstruction. Its PARTIAL status
and missing-counter are now asserted explicitly; raw golden expectations were
not changed. Six other games retain EXACT / EXACT_WITH_EXPLAINED_GRANT.

Three new regression tests first failed on baseline (cross-account API missing,
legacy report falsely current, NULL result treated as LOSS), then passed after
the additive scoped cache / missing-metric corrections. Nine focused checks now
covered those defects and the GameContext boundary at that checkpoint. The final
stack contains 22 focused checks; see STABILIZATION_REPORT.md. Existing cache fixture writes
were given their known test PUUID; their semantic assertions were preserved.

Legacy cache APIs remain available for diagnostic callers only. Desktop reads
require explicit PUUID and never fall back to another player's or unscoped rows.

## Final disposition

Technical corrections pass. Full latest-patch acceptance remains REVIEW_REQUIRED
for the pinned Phase 2D AS-source mismatch (16.17 vs 16.16); its exact frozen
baseline audit passes. The final report records this separately, not as a hidden
or weakened test. No blanket claim of latest-patch combat readiness is made.

## Exit policy (unchanged)

No optimizer, semantic promotion, statistical retuning, self-freeze or broad
refactor. Stable-base readiness remains unapproved until golden, robustness,
knowledge and end-to-end validations actually complete. Initial inventory status
is conservative; a structural inventory is not a claim of exhaustive behavioral validation.
