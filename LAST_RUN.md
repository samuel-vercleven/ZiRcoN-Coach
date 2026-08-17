# LAST RUN

## Status
REVIEW_REQUIRED

## Date
2026-08-17 17:18 local

## Command
.\.venv\Scripts\python.exe main.py

## Runtime
- completed
- approximate duration: 90s
- full terminal output saved to logs/latest_full_run.txt

## Files changed
- main.py
- database/database.py
- logs/latest_full_run.txt
- LAST_RUN.md
- PROJECT_STATE.md
- TODO.md

## Tests executed
- .\.venv\Scripts\python.exe -m compileall main.py analysis database riot config
- .\.venv\Scripts\python.exe -m compileall main.py database\database.py analysis\reset_analyzer.py analysis\reset_statistics.py
- .\.venv\Scripts\python.exe -m compileall main.py database\database.py
- .\.venv\Scripts\python.exe main.py
- focused in-memory Reset v21 audit on local SQLite history

## Errors encountered
- `python` was not on PATH; used the project venv interpreter.
- Riot API returned 401 Unknown apikey during the first attempted run. Added a main.py local-history fallback using existing SQLite data; the final full run did not reproduce the 401.
- Windows stdout hit UnicodeEncodeError on frozen Tempo v17 rendered text. Fixed by configuring main.py stdout/stderr as UTF-8; frozen analyzers were not modified.

## Main analyzer results
### Death Analyzer
- v11 not modified.
- Built 491 exploitable death rows during the full run.

### Tempo / Pathing
- v17 not modified.
- Built 2,604 tempo intervals during the full run.

### Objective Analyzer
- v20 not modified.
- Built 628 objective sequences during the full run.

### Current analyzer
- Recall / Reset Analyzer v21 completed on 87 Jungle games.
- Total SHOP/RESET proxy sequences: 891.
- Origins: 509 VOLUNTARY_RESET_PROXY, 382 POST_DEATH_SHOP.
- Historical reference scopes: CHAMPION_PHASE_ORIGIN_TIME 339, PHASE_ORIGIN_TIME 282, WARMUP 227, CHAMPION_PHASE_ORIGIN 32, PHASE_ORIGIN 11.
- Unscored reentries: 263 total; 227 warmup, 36 with references but unavailable +120s post window.
- Outcome evidence: all personal raw reentry measures passed robust criteria globally. Strongest was XP vs JGL/min after voluntary reset, Cliff +0.658, CV 77.8%, walk-forward 80.8%, FDR q 0.0006.
- Phase validation: several LATE signals passed robust criteria; additional phase signals are promising but explicitly non-frozen.
- Resets <=45s before objective: 126 total, split into 54 voluntary and 72 post-death shops. Voluntary tight objectives: 33 ENEMY, 20 ALLY, 1 UNKNOWN.
- 15 weakest voluntary reentries were score 1-7/100; they are listed in logs/latest_full_run.txt.
- Latest target match EUW1_7951911875: 7 sequences, 4 voluntary proxies and 3 POST_DEATH_SHOP; post-death shops were not presented as voluntary mistakes.

## Suspicious findings
- Purchase clustering showed no merge evidence: max cluster duration 20.54s; no cluster exceeded 45s.
- Split risk is low but not zero: no separated shop gap was <=20s, but 24 gaps were <=45s, with minimum 20.11s. This is near the current 20s threshold and should be reviewed before freezing.
- High currentGold is mixed, not a reliable error label: 141 voluntary highGold contexts, 84 scored, including 29 low reentries and 11 excellent reentries.

## Methodological concerns
- Current Gold remains exploratory only. Global exploratory validation had FDR q 1.0000 and low reliability.
- Objective proximity remains context only. Reset <=45s before objective did not pass robust context validation globally (FDR q 0.1124; CI crossed 0).
- Deciding whether v21 is freeze-ready is a project-review decision, not a Codex decision.

## Remaining issues
- Riot API availability/key state was inconsistent during validation; local-history fallback now exists for already stored data.
- Near-threshold shop gaps should be manually reviewed before changing any clustering threshold.
- v21 is not declared FROZEN by Codex.

## Codex technical recommendation
- Review the near-threshold purchase gaps and the 54 voluntary tight-objective resets before any freeze decision.

## Review request
- REVIEW_REQUIRED because v21 freeze readiness and any clustering-threshold change are methodology/project-review decisions.
