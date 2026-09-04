# ZiRcoN Coach — V0.1 Alpha
## First Usable Desktop Application

### Model recommendation
Codex: GPT-5.6 Sol
Reasoning: HIGH

# 0. Starting baseline
Repository: `samuel-vercleven/ZiRcoN-Coach`
Expected starting HEAD/origin/main:
`cdbcdf4269a4ed50427014bff078e0026b19f346`
Commit: `Record Phase 2I freeze verification`

All backend layers through Phase 2I are FROZEN. Do not modify frozen production/validation behavior.

Accepted Phase 2I limitation remains part of the product truth:
- 569 stat-owner occurrences audited;
- 567 OWNER_CONTEXT_DEPENDENT;
- 2 OWNER_UNRESOLVED;
- 0 execution-eligible concrete owners;
- no stat-scaling arithmetic;
- no fabricated numeric replay.

Do not reopen stat-owner research in V0.1.

# 1. Mission
Build ZiRcoN Coach V0.1 Alpha as a real local PySide6 desktop application.

At the end, this command must open the app:

```powershell
python run_app.py
```

The app must provide a useful first product experience around the existing real local data and frozen analyzers.

Required screens:
1. Dashboard
2. Match History
3. Match Detail / Post-game
4. Progress
5. Settings / Data Status

# 2. Product rules
- Real data over mock data.
- Local-first.
- Read-only integration first.
- No fake coaching claims.
- No fake spell damage/combat values.
- PARTIAL / UNKNOWN / UNAVAILABLE must remain explicit.
- UI must remain usable offline when local DB data exists.
- Never expose/commit Riot API keys.

# 3. Mandatory startup
Read fully:
- AGENTS.md
- PROJECT_STATE.md
- TODO.md
- DECISIONS.md
- LAST_RUN.md
- main.py

Inspect repository tree and identify:
- Riot API/client modules;
- config/environment loading;
- SQLite/database modules and schema;
- current match import pipeline;
- Data Dragon helpers/cache;
- analyzer public functions;
- dependency management.

Run:
```text
git status
git diff
git log --oneline --decorate -15
git rev-parse HEAD
git rev-parse origin/main
```

Expected both SHAs:
`cdbcdf4269a4ed50427014bff078e0026b19f346`

Do not silently reset user work.

# 4. Frozen boundary
Treat all current frozen files as immutable.

If UI integration would require a frozen change:
- do not change it;
- create an adapter/service/view-model;
- if impossible, mark that branch REVIEW_REQUIRED.

Do not copy analyzer logic into widgets.

# 5. Keep main.py as validation harness
Do NOT replace current `main.py` with the GUI launcher.

Create:
`run_app.py`

Target shape:
```python
from app.application import ZirconCoachApplication

if __name__ == "__main__":
    raise SystemExit(ZirconCoachApplication().run())
```

`python main.py` must continue to validate the frozen backend.

# 6. New app architecture
Prefer a clean structure similar to:

```text
app/
  __init__.py
  application.py
  bootstrap.py
  paths.py

ui/
  __init__.py
  main_window.py
  theme.py
  components/
    sidebar.py
    topbar.py
    stat_card.py
    status_badge.py
    empty_state.py
    loading_state.py
    match_card.py
    insight_card.py
  pages/
    dashboard_page.py
    matches_page.py
    match_detail_page.py
    progress_page.py
    settings_page.py

services/
  player_service.py
  match_service.py
  coaching_service.py
  progress_service.py
  asset_service.py
  sync_service.py
  health_service.py

viewmodels/
  player.py
  match_summary.py
  match_detail.py
  coaching.py
  progress.py
  status.py

run_app.py
```

Adapt to existing repo conventions if they are better. Do not over-engineer.

# 7. PySide6
Use PySide6.

Inspect current dependency management first.
If needed, add a simple dependency manifest appropriate for the repo.
Do not commit `.venv`.
Install PySide6 in the active venv if necessary for validation.

No Qt Designer requirement for V0.1.

# 8. Visual direction
Create an original ZiRcoN Coach UI:
- dark;
- clean;
- modern;
- compact gaming-stat density;
- readable hierarchy;
- restrained accent;
- green/red result indications;
- clear status badges.

Do not copy Mobalytics/OP.GG/Porofessor layouts or proprietary assets.

# 9. Main window
Required shell:
- left sidebar;
- ZiRcoN Coach title;
- central stacked page area;
- global sync/data status.

Sidebar:
```text
Dashboard
Matches
Progress
Settings
```

Match Detail opens from Match History.

Requirements:
- resizable;
- sensible 1080p layout;
- no clipped controls;
- long text wraps.

# 10. Bootstrap/service architecture
Build a single bootstrap layer resolving:
- config;
- DB path;
- Riot integration if configured;
- services;
- app theme;
- main window.

Do not instantiate Riot/database clients randomly inside widgets.
Avoid mutable globals.

# 11. Player identity
Reuse existing configured Riot ID/account logic where available.
The user must not need to edit Python source to change account identity.

Never commit/display the Riot API key.
Settings may show only `API configured: Yes/No`.

# 12. Dashboard
Landing page goal: "How am I doing and what should I look at?"

Player header when available:
- Riot ID;
- profile icon;
- rank/tier/division;
- LP;
- queue;
- recent W/L.

Recent performance when supported:
- wins/losses;
- win rate;
- KDA;
- CS/min;
- average duration;
- champion distribution.

Show latest ~5 matches with:
- champion;
- result;
- K/D/A;
- duration;
- CS or CS/min;
- date;
- click to detail.

Add a small Coaching Highlights area sourced only from frozen analyzers.

# 13. Match History
Build a real scrollable history.

Each row/card where available:
- champion icon/name;
- win/loss;
- K/D/A;
- KDA;
- CS;
- CS/min;
- duration;
- queue;
- date.

Filters minimum:
- All
- Wins
- Losses

Click => Match Detail.

# 14. Match Detail / Post-game
This is the main V0.1 product screen.

Header:
- champion;
- result;
- K/D/A;
- duration;
- date;
- queue.

Then integrate existing frozen analyzer outputs through a UI adapter:

## Death
Show analyzer-supported death impact/cost labels and concise evidence.

## Jungle Tempo / Pathing
Show relevant tempo events/windows and supported summaries.

## Objectives
Show supported objective preparation/timing facts.

## Recall / Reset
Show reset events and supported outcome classifications.

## Build / Itemization
Show items/order/timing and factual analyzer findings.
Do not add "best build" recommendations.

# 15. Unified CoachingService
Create a non-frozen UI-facing adapter such as:

```python
class CoachingService:
    def get_match_insights(self, match_id) -> CoachingReport:
        ...
```

Normalize insights to fields like:
- category
- title
- summary
- severity
- status/confidence
- evidence
- source_module

Preserve source analyzer provenance/status.

# 16. Coaching wording
Translate technical analyzer statuses into concise player-facing wording without changing meaning.

Do not use an LLM for V0.1.
Use deterministic templates.

Detailed evidence may be expandable.

# 17. Progress
Build progress from actual local match history.

Minimum metrics:
- win rate;
- KDA;
- CS/min;
- deaths/match;
- optional average duration;
- stable analyzer-derived counts/rates if easily available.

Windows if enough data:
- last 10
- last 20
- last 50
- all

At minimum compare recent window vs previous equivalent window.
If sample too small, state it.

# 18. Charts
Add 2–3 useful charts max for V0.1, e.g.:
- win rate trend;
- CS/min trend;
- deaths or KDA trend.

Use Qt-native drawing or matplotlib if appropriate.
No heavy chart dependency unless necessary.

Charts must handle empty/one-row/missing data safely.

# 19. Champion pool summary
Show descriptive stats only:
- champion;
- games;
- wins;
- win rate;
- KDA;
- CS/min.

No personal tier score yet.

# 20. Combat Beta boundary
Do NOT build a new combat engine.
Do NOT reopen Phase 2I.

Allowed only if useful:
- display frozen formula resolution status;
- show RESOLVED/PARTIAL/UNKNOWN reasons.

Example:
```text
Formula status: PARTIALLY_RESOLVED
Reason: stat owner not execution eligible
```

Combat BETA is P2; post-game coaching is higher priority.

# 21. Assets
Use Riot/Data Dragon static assets where appropriate:
- champion icons;
- item icons;
- profile icon.

Prefer existing helpers/version.
Create AssetService with local cache + fallback.
Do not commit generated cache.
Do not block Qt main thread for downloads.

# 22. Threading
No blocking Riot/Data Dragon request on Qt main thread.
Use a clean Qt worker design (`QThreadPool`/`QRunnable` or `QThread`).

Worker failures return readable UI states.

# 23. Sync
Provide a simple Sync/Refresh action.

Behavior:
1. show syncing state;
2. reuse existing Riot import pipeline;
3. update local DB;
4. refresh pages;
5. show success/failure.

Do not duplicate API pipeline in widget code.

Missing/expired key and rate limit must be readable.

# 24. Offline behavior
If network/API unavailable but local DB contains matches:
- app opens;
- match history works;
- progress works;
- local analyzer outputs work.

Settings/Data Status should show:
- DB available/unavailable;
- loaded match count;
- Riot API configured/unconfigured;
- last sync state if known.

# 25. Empty/error/loading states
Handle without crash:
- no DB;
- empty DB;
- missing .env;
- invalid Riot key;
- no network;
- missing icon;
- malformed one match;
- missing analyzer result;
- partial analyzer result.

No raw traceback in normal UI.

# 26. Settings / Data Status
Minimum:
- current Riot ID/account;
- queue if configured;
- DB path;
- loaded match count;
- latest local match date;
- API configured Yes/No;
- V0.1 Alpha version;
- backend/frozen baseline summary.

No secret value display.

# 27. View-model contracts
Do not pass giant raw Riot JSON directly to widgets.

Create dataclasses/DTOs such as:
- PlayerViewModel
- MatchSummaryViewModel
- MatchDetailViewModel
- InsightViewModel
- ProgressViewModel

Keep UI independent from raw storage shapes.

# 28. Performance
Target smooth use with roughly 100 local matches.

Avoid:
- DB full reload on every repaint;
- analyzer rerun on every widget paint;
- network on main thread.

In-memory per-match caching is acceptable.

# 29. UI smoke tests
Create headless tests/checks using:
`QT_QPA_PLATFORM=offscreen`

Minimum:
- QApplication initializes;
- main window constructs;
- all pages construct;
- navigation works;
- empty state does not crash;
- sample view models render;
- Match Detail accepts a match;
- service error state renders;
- close cleanly.

# 30. Service tests
Test/check:
- DTO conversion;
- progress calculations;
- coaching adapter normalization;
- missing fields;
- malformed row;
- offline mode;
- config without secret;
- analyzer provenance/status preservation.

Do not modify frozen test files.

# 31. Manual visual validation
If environment permits, launch:

```powershell
python run_app.py
```

Check basic layout and navigation.
If GUI cannot be visually inspected, use offscreen tests and say so explicitly.
Do not claim visual validation if not actually done.

# 32. V0.1 audit
Create a non-frozen audit/check such as:
`app/v01_alpha_audit.py`

Verify:
- run_app.py exists;
- PySide6 available;
- app bootstraps;
- required pages exist;
- services callable;
- offline bootstrap path works;
- offscreen main window PASS;
- navigation PASS;
- empty state PASS;
- frozen modifications = 0;
- no secret committed/exposed.

Final technical status:
`PASS / REVIEW_REQUIRED FOR ALPHA FREEZE`
or `REVIEW_REQUIRED`.

Do not self-freeze.

# 33. Existing backend validation
Run:

```powershell
python main.py
```

It must remain PASS.

Also run all new V0.1 checks.

# 34. Central acceptance test
Required user-facing command:

```powershell
python run_app.py
```

Expected:
- real main window opens;
- if local data exists, Dashboard loads it;
- otherwise clean onboarding/empty state;
- navigation works;
- no terminal-only product experience.

# 35. First launch onboarding
If no local profile/data:
show a small useful onboarding state:

```text
ZiRcoN Coach
No local player data found.
1. Configure Riot ID
2. Add RIOT_API_KEY to .env
3. Sync matches
```

Settings must remain accessible.

# 36. Priority order
P0:
1. app launch
2. shell/navigation
3. local match history
4. match detail
5. frozen analyzer coaching cards
6. offline/error states

P1:
7. Dashboard stats
8. Progress
9. Sync
10. icons/assets

P2:
11. Combat Beta status
12. extra visual polish

Finish P0/P1 cleanly before P2.

# 37. Out of scope
Do NOT implement:
- Overwolf/live overlay;
- live game coaching;
- pre-game recommendation engine;
- optimal pick engine;
- voice assistant;
- LLM coaching;
- ML;
- build recommendation engine;
- full spell simulator;
- Burst/TTK;
- new item passive/rune engine;
- owner research;
- Windows installer/exe packaging;
- cloud accounts;
- duo view.

# 38. Documentation
Update:
- PROJECT_STATE.md
- TODO.md
- LAST_RUN.md

Update DECISIONS.md only for durable decisions.

Document run:
```powershell
.\.venv\Scripts\Activate.ps1
python run_app.py
```

Document validation and dependency setup.

# 39. Git strategy
Suggested commits:
1. `Build ZiRcoN Coach alpha application shell`
2. `Integrate player and match data into alpha UI`
3. `Integrate post-game coaching and progress views`
4. `Validate ZiRcoN Coach V0.1 alpha`

Do not commit:
- .env
- Riot key
- .venv
- runtime DB
- asset cache
- logs

At end:
```text
git status --short
git diff --check
git rev-parse HEAD
git rev-parse origin/main
```

Push to origin/main.
HEAD and origin/main must match.
No force push.

# 40. Final Codex response
Report:
- commits and final SHA;
- architecture/files;
- dependency changes;
- exact launch command;
- Dashboard status;
- Match History status;
- Match Detail status;
- frozen analyzer integrations;
- Progress status;
- Settings status;
- offline behavior;
- sync behavior;
- manual visual validation performed/not performed;
- UI smoke tests;
- service tests;
- V0.1 audit;
- `python main.py`;
- FROZEN guard;
- `git diff --check`;
- secret check;
- push status;
- HEAD/origin SHA;
- remaining limitations.

End as:
`PASS / REVIEW_REQUIRED FOR ALPHA FREEZE`

Do NOT freeze V0.1 yourself.
Do NOT start V0.2.
Do NOT start Phase 2J/2K/etc.

# Final principle
A smaller application backed by real data and trusted analyzers is better than a beautiful dashboard full of fake information.

V0.1 succeeds when the user can launch ZiRcoN Coach, inspect real matches, open a post-game analysis, see trusted coaching information, and understand clearly when data is unavailable.
