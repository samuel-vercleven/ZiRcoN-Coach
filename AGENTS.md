# ZiRcoN Coach — Codex Project Instructions

## Role
You are the coding/execution agent for ZiRcoN Coach.

Before changing code:
1. Read AGENTS.md.
2. Read PROJECT_STATE.md.
3. Read TODO.md.
4. Read DECISIONS.md when architecture/methodology is relevant.
5. Inspect the existing implementation before editing.

After changing code:
1. Compile all modified Python files.
2. Run relevant smoke/unit tests.
3. Run `python main.py` when practical.
4. Fix obvious runtime errors caused by the current change.
5. Update PROJECT_STATE.md.
6. Rewrite TODO.md with the next concrete task.
7. Update DECISIONS.md if a lasting design decision changed.

## Project
- Windows desktop project.
- Python / VS Code.
- Local-first.
- Riot API + Data Dragon + local Riot timeline data.
- SQLite/local history.
- PySide6 UI later.
- main.py is currently a verbose integration/test harness, not the final UI.

## Frozen modules
Do not modify these unless a demonstrated correctness/integration bug requires a minimal change:
- Death Analyzer: FROZEN v11.
- Jungle Tempo / Pathing: FROZEN v17.
- Objective Analyzer: FROZEN v20.

## Current module in development
- Recall / Reset Analyzer: v21.

## Methodology
- Association != causality.
- Never weaken thresholds merely to make a signal pass.
- Historical scoring must never use future games.
- Same-game observations must not influence their own historical reference.
- Team objectives/towers are context unless explicitly validated as personal signals.
- Composite scores are explanatory, not calibrated probabilities.
- Context heuristics must be labelled as heuristics/evidence, not ground truth.
- Riot frame timing is coarse; do not overclaim exact path, intent, recall timing, camp sequence, vision, or cause.

## Final Codex report
At the end of each task report:
- changed files;
- what changed;
- tests executed;
- results;
- remaining issues;
- exact next recommended task.

Keep PROJECT_STATE.md concise enough that ChatGPT can re-read it quickly.
