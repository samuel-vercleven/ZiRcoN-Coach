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
Status: validated on the real local history; pre-freeze clustering audit completed; REVIEW_REQUIRED before any freeze decision.

Design:
- Uses SHOP/RESET proxy from purchase clusters.
- Separates post-death shop vs voluntary reset proxy.
- Analyzes ~120s before/after.
- Reentry Score is historical-only.
- Current Gold before reset is exploratory/contextual only.

Current technical state:
- 2026-08-17 full run completed on 87 Jungle games.
- Production v21 remains unchanged at SHOP_CLUSTER_GAP_SECONDS = 20.
- Production dataset: 891 shop/reset proxy sequences.
- Origins: 509 voluntary reset proxies, 382 post-death shops.
- Historical references: 339 CHAMPION_PHASE_ORIGIN_TIME, 282 PHASE_ORIGIN_TIME, 32 CHAMPION_PHASE_ORIGIN, 11 PHASE_ORIGIN, 227 WARMUP.
- Unscored reentries: 263 total; 227 warmup plus 36 with missing +120s post window.
- Global personal reentry measures previously showed robust Win/Loss association under existing validation; strongest was XP vs JGL/min after voluntary reset, Cliff +0.658, CV 77.8%, walk-forward 80.8%, FDR q 0.0006.
- Current Gold remains exploratory only; it is not an automatic mistake label.
- Objective proximity remains context only; no reset is labeled a mistake because an objective follows.

Pre-freeze clustering audit:
- 24 consecutive player shop-cluster pairs had 20s < gap <= 45s.
- Audit-only classification: 10 LIKELY_SAME_SHOP_VISIT, 14 LIKELY_SEPARATE_VISITS, 0 AMBIGUOUS.
- Gap bins: 20-25s 7, 25-30s 3, 30-35s 5, 35-40s 3, 40-45s 6.
- 30s sensitivity would merge 10 sequences: 881 total, 509 voluntary, 372 post-death.
- 45s sensitivity would merge 24 sequences: 867 total, 508 voluntary, 359 post-death.
- Game-level median reentry stats changed little, but post-death sequence volume changed materially enough to require review.
- All 54 voluntary tight-pre-objective resets were audited: 33 ENEMY, 20 ALLY, 1 UNKNOWN.
- Tight-objective checks found 0 misclassified post-death candidates, 0 split-purchase-cluster candidates, and 6 objective-timing artifact candidates with next objective <=5s.
- Target match EUW1_7951911875 remains 7 sequences: 4 voluntary, 3 post-death, 0 near-threshold split candidates, 2 tight-pre-objective proxies.
- Freeze status: NOT FROZEN by Codex; project review must decide whether threshold changes or freeze are appropriate.

Technical fixes / audit support:
- main.py can fall back to existing local SQLite history when Riot account/match lookup is unavailable.
- main.py configures stdout/stderr as UTF-8 to avoid Windows console encoding failures while rendering analyzer reports.
- analysis/reset_audit.py provides audit-only reporting and threshold sensitivity; it does not change production logic.
- .gitignore now correctly ignores .env, .venv, *.db, __pycache__, and logs/ so private local DB/log output is not staged accidentally.

## Architecture
- main.py remains a dev/integration harness.
- Final UI later with PySide6.
- Analysis modules should remain UI-agnostic.

## Handoff rule
Codex must update this file after each completed task.
