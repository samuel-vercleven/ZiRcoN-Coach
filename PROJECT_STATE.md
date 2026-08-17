# ZiRcoN Coach - Project State

## Frozen analyzers
- Death Analyzer: v11 - FROZEN.
- Jungle Tempo / Pathing Analyzer: v17 - FROZEN.
- Objective Analyzer: v20 - FROZEN.
- Recall / Reset Analyzer: v21 - FROZEN.

Frozen means: no retuning/refactor without a demonstrated correctness or integration bug or explicit project review request.

## In development
- None currently documented.

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
- Boundary guard +/-60s.
- 1 weak minute = WATCH; sustained about 2+ min = pathing-hole candidate.
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
Status: FROZEN by project review.

Design:
- Uses SHOP/RESET proxy from purchase clusters, not exact recall lifecycle.
- Separates post-death shop sequences from voluntary reset proxies.
- Analyzes about 120s before/after.
- Reentry Score is historical-only and measures observed post-reset production, not causal recall quality.
- Current Gold before reset is exploratory/contextual only.
- Objective proximity remains context only and is never an automatic player-mistake label.

Current technical state:
- Latest full runtime verification completed on 2026-08-17 on 87 Jungle games.
- Production v21 remains unchanged at SHOP_CLUSTER_GAP_SECONDS = 20.
- Production dataset: 891 shop/reset proxy sequences.
- Origins: 509 voluntary reset proxies, 382 post-death shops.
- Historical references: 339 CHAMPION_PHASE_ORIGIN_TIME, 282 PHASE_ORIGIN_TIME, 32 CHAMPION_PHASE_ORIGIN, 11 PHASE_ORIGIN, 227 WARMUP.
- Unscored reentries: 263 total; 227 warmup plus 36 with missing +120s post window.
- Global personal reentry measures previously showed robust Win/Loss association under existing validation; strongest was XP vs JGL/min after voluntary reset, Cliff +0.658, CV 77.8%, walk-forward 80.8%, FDR q 0.0006.

Final threshold-independent clustering audit:
- 24 consecutive player shop-cluster pairs had 20s < gap <= 45s.
- Classification no longer uses 20s/30s/45s or any gap cutoff; gap is reported only after classification.
- Audit-only classification: 13 SEPARATE_VISITS, 11 UNRESOLVED, 0 SAME_VISIT_CANDIDATE.
- Riot frame resolution: 13 same-frame pairs, 11 distinct-frame pairs.
- Evidence reasons: 11 same-frame UNRESOLVED, 6 player K/A/D events, 3 major objective/building events on distinct frames, 3 observable OUTSIDE_BASE intermediate frames, 1 resource-progression case.
- Gap-bin results after classification: 20-25s = 0 SAME / 1 SEPARATE / 6 UNRESOLVED; 25-30s = 0 / 1 / 2; 30-35s = 0 / 4 / 1; 35-40s = 0 / 2 / 1; 40-45s = 0 / 5 / 1.
- 20s production clustering threshold retained conservatively.
- Rationale: raising the threshold would merge some independently supported separate visits, while same-frame unresolved cases are insufficient evidence for merging.
- Objective <=5s technical check passed: 6/6 timings measured from cluster end, 6/6 objectives after complete cluster, 6/6 extraction/order checks OK.
- Target match EUW1_7951911875 remained stable: 7 sequences, 4 voluntary, 3 post-death, 0 near-threshold pairs, 2 tight-pre-objective proxies.

Permanent v21 limitations:
- Riot data does not expose a perfect recall lifecycle.
- Purchase clusters remain SHOP/RESET proxies.
- Same-frame Riot gaps may remain unresolved.
- Current Gold is exploratory context only.
- Objective proximity is context, not player fault.
- Reentry Score is not a causal recall-quality score.

Technical fixes / audit support:
- main.py can fall back to existing local SQLite history when Riot account/match lookup is unavailable.
- main.py configures stdout/stderr as UTF-8 to avoid Windows console encoding failures while rendering analyzer reports.
- analysis/reset_audit.py provides audit-only threshold-independent clustering diagnostics and threshold sensitivity; it does not change production logic.
- .gitignore ignores .env, .venv, *.db, __pycache__, and logs/ so local secrets, DBs, and logs are not staged accidentally.

## Architecture
- main.py remains a dev/integration harness.
- Final UI later with PySide6.
- Analysis modules should remain UI-agnostic.

## Handoff rule
Codex must update this file after each completed task.
