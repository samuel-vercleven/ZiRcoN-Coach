# ZiRcoN Coach — Project State

## Frozen analyzers
- Death Analyzer: v11 — FROZEN.
- Jungle Tempo / Pathing Analyzer: v17 — FROZEN.
- Objective Analyzer: v20 — FROZEN.

Frozen means: no retuning/refactor without a demonstrated correctness or integration bug.

## In development
- Recall / Reset Analyzer: v21.

## Dataset
- Main historical validation set: 87 Jungle games with exploitable timelines.
- Queue 420.
- Primary profile: ZiRcoN1977#EUW.
- Windows / Python.

## Death Analyzer v11
- Historical-only scoring.
- Death volume and per-death Gold/XP costs separated.
- Association language only.
Known limits: minute-level Riot frames, overlapping episode costs, contextual trade semantics, chain percolation.

## Jungle Tempo / Pathing v17
- Global tempo outside death contamination.
- Personal FARMABLE pathing = own XP + Jungle CS.
- MIRRORED for neutral direct comparison.
- Time-local references.
- Boundary guard ±60s.
- 1 weak minute = WATCH; sustained ≈2+ min = pathing-hole candidate.
Known limits: no exact camps/routes; shop/reset proxy; lane-catch heuristic.

## Objective Analyzer v20
- Preparation + conversion windows.
- Gold/XP/JCS personal and relative.
- Death v11 + Tempo v17 integration.
- Directional before/after trade logic.
- Spatial contest evidence.
- Historical-only scoring, minimum 20 references.
Known limits: proximity != intent; close objective sequences may share fight context; compensation thresholds are heuristic.

## Recall / Reset Analyzer v21
Status: validated on the real local history, REVIEW_REQUIRED before any freeze decision.

Design:
- Uses SHOP/RESET proxy from purchase clusters.
- Separates post-death shop vs voluntary reset proxy.
- Analyzes ~120s before/after.
- Reentry Score is historical-only.
- Current Gold before reset is exploratory/contextual only.

Latest run:
- 2026-08-17: main.py completed on local SQLite history.
- Dataset: 87 Jungle games, 891 shop/reset proxy sequences.
- Origins: 509 voluntary reset proxies, 382 post-death shops.
- Historical references: 339 CHAMPION_PHASE_ORIGIN_TIME, 282 PHASE_ORIGIN_TIME, 32 CHAMPION_PHASE_ORIGIN, 11 PHASE_ORIGIN, 227 WARMUP.
- Unscored reentries: 263 total; 227 warmup plus 36 with missing +120s post window.
- Global personal reentry measures all showed robust Win/Loss association under existing validation; strongest was XP vs JGL/min after voluntary reset, Cliff +0.658, CV 77.8%, walk-forward 80.8%, FDR q 0.0006.
- Objective proximity remains context only: reset <=45s before objective did not pass robust global context validation.
- Current Gold remains exploratory only: FDR q 1.0000 and low reliability; it is not an automatic mistake label.
- Purchase clustering: no merge evidence found (max cluster duration 20.54s), but 24 separated shop gaps were <=45s with minimum 20.11s, so near-threshold split risk should be reviewed before freezing.
- Latest target match EUW1_7951911875: 7 sequences, split into 4 voluntary proxies and 3 POST_DEATH_SHOP; post-death shops remained separated from voluntary reset classifications.
- Freeze status: NOT FROZEN by Codex; project review must decide whether v21 is freeze-ready.

Technical fixes during validation:
- main.py now falls back to existing local SQLite history when Riot account/match lookup is unavailable. The final full run did not reproduce the initial 401, but this keeps stored-history validation usable if live lookup fails again.
- main.py configures stdout/stderr as UTF-8 to avoid Windows console encoding failures while rendering analyzer reports.

## Architecture
- main.py remains a dev/integration harness.
- Final UI later with PySide6.
- Analysis modules should remain UI-agnostic.

## Handoff rule
Codex must update this file after each completed task.
