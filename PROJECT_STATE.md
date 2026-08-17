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
Status: first PRO implementation exists and requires real-history validation.

Design:
- Uses SHOP/RESET proxy from purchase clusters.
- Separates post-death shop vs voluntary reset proxy.
- Analyzes ~120s before/after.
- Reentry Score is historical-only.
- Current Gold before reset is exploratory/contextual only.

## Architecture
- main.py remains a dev/integration harness.
- Final UI later with PySide6.
- Analysis modules should remain UI-agnostic.

## Handoff rule
Codex must update this file after each completed task.
