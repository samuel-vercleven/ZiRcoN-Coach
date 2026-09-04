# ZiRcoN Coach — V0.1 Alpha Product Completion
## Polished desktop UI + dynamic Riot API key + async sync + full trusted post-game coaching

### Recommended Codex model
GPT-5.6 Sol

### Reasoning
HIGH

This is intentionally one large coherent product milestone with checkpoint commits.

Do NOT spend this run extending the combat reverse-engineering roadmap.
The goal is to turn ZiRcoN Coach into a genuinely usable local desktop coaching product.

---

# 0. Current exact working state

Repository:
`samuel-vercleven/ZiRcoN-Coach`

Current work branch:
`v01-alpha-wip`

Expected committed HEAD before the local Batch 1 files:
`680fa07d478cb08882ba3433e4094979191a62b4`

Commit:
`WIP ZiRcoN Coach V0.1 Alpha`

That WIP is based directly on frozen main:
`cdbcdf4269a4ed50427014bff078e0026b19f346`
`Record Phase 2I freeze verification`

IMPORTANT:
There are expected LOCAL UNCOMMITTED Batch 1 GUI files on top of `680fa07...`.

They include a first runnable PySide6 shell such as:
- `run_app.py`
- `app/application.py`
- `app/bootstrap.py`
- `ui/main_window.py`
- `ui/theme.py`
- `ui/pages/*`
- `ui/components/*`
- `app/v01_alpha_smoke.py`

Do not reset, discard, stash-and-forget, or overwrite those blindly.

The current visible Batch 1 UI already:
- opens successfully;
- reads the real local SQLite data;
- shows Riot ID;
- shows ~104 local matches in the observed development DB;
- shows win rate, KDA, CS/min;
- shows recent matches;
- has Dashboard / Matches / Progress / Settings navigation.

But visually it is still a developer prototype:
- plain tables;
- very large empty areas;
- little information hierarchy;
- no champion/item/profile images;
- no rank/profile hero;
- no sync action;
- no dynamic Riot API key replacement;
- no real post-game analyzer integration yet.

This milestone must transform that prototype into a proper Alpha product.

---

# 1. Frozen project boundary

All previously frozen backend production/validation behavior through Phase 2I remains immutable.

Frozen product/research layers include:
- Death Analyzer v11
- Jungle Tempo / Pathing v17
- Objective Analyzer v20
- Recall / Reset Analyzer v21
- Build / Itemization Analyzer v22 Phase 1
- Item Knowledge Phase 2A
- Champion Knowledge Phase 2B1
- Rune Knowledge Phase 2C1-B
- Level Stats Phase 2D
- Combat Resistance Phase 2E
- Spell Source Phase 2F
- Combat Formula Foundation Phase 2G
- Stat Reference Semantics Phase 2H
- Stat Owner Semantics Phase 2I

Phase 2I remains a zero-gate frozen result:
- no executable concrete stat owner;
- no stat-scaling executor;
- no fabricated spell-damage completion.

Do not reopen 2I.
Do not start 2J.
Do not modify frozen analyzers just to make UI integration convenient.

Build adapters/services around frozen code.

If an integration would truly require changing frozen behavior:
leave the affected UI section explicit `UNAVAILABLE / REVIEW_REQUIRED` and continue other sections.

---

# 2. Preserve `main.py`

`main.py` remains the backend/FROZEN validation harness.

Do NOT turn it into the GUI launcher.

The application entry point remains:

```powershell
python run_app.py
```

The final run must still include:

```powershell
python main.py
```

and it must PASS.

---

# 3. Mandatory startup sequence

Read fully before editing:

1. `AGENTS.md`
2. `PROJECT_STATE.md`
3. `TODO.md`
4. `DECISIONS.md`
5. `LAST_RUN.md`
6. `main.py`

Then inspect:
- `run_app.py`
- `app/`
- `ui/`
- `services/`
- `viewmodels/`
- `requirements.txt`
- `.gitignore`

Inspect existing Riot/data stack:
- `riot/riot_api.py`
- `riot/data_dragon.py`
- `config/settings.py`
- `database/database.py`
- `database/death_reader.py`
- `database/tempo_reader.py`
- `database/event_reader.py`

Inspect frozen analyzer APIs in read-only mode:
- `analysis/death_cost_analyzer.py`
- `analysis/jungle_tempo_analyzer.py`
- `analysis/objective_analyzer.py`
- `analysis/reset_analyzer.py`
- `analysis/itemization_analyzer.py`

Also inspect existing non-frozen aggregation/presentation helpers where useful:
- `analysis/coaching_engine.py`
- related feature/benchmark modules

Before modifications run:

```text
git status
git diff
git diff --stat
git log --oneline --decorate -15
git rev-parse HEAD
git rev-parse origin/v01-alpha-wip
git rev-parse origin/main
```

Expected:
- branch `v01-alpha-wip`
- committed HEAD may still be `680fa07...`
- local tree may be dirty because Batch 1 GUI is intentionally uncommitted
- `origin/main` remains the Phase 2I freeze baseline

DO NOT run destructive reset/clean commands.

---

# 4. First checkpoint — stabilize existing Batch 1

Before the large redesign:
1. inspect every existing local Batch 1 file;
2. run:
   - `python -m app.v01_alpha_smoke`
   - `python run_app.py` if GUI environment permits;
3. fix ordinary Batch 1 bugs;
4. confirm no frozen file was touched;
5. commit the working shell.

Suggested checkpoint commit:

`Stabilize ZiRcoN Coach alpha GUI shell`

Do not include accidental historical TODO backup files in the final product branch.

The existing WIP accidentally tracked:
- `TODO.before_phase2i.md`
- `TODO.before_v01_alpha.md`

Remove these backup artifacts from the product branch unless AGENTS/project review explicitly requires them.
Do not remove canonical project documentation.

---

# 5. Product target

At the end, ZiRcoN Coach V0.1 Alpha should feel like a real desktop product.

Primary experience:

```text
Launch app
→ See player identity + rank + current local stats
→ Click Sync
→ Current Riot data imports asynchronously
→ New matches and timelines are cached locally
→ Trusted post-game analyzers run
→ Dashboard refreshes
→ Open a match
→ See rich post-game page
→ Death / Tempo / Objectives / Recall / Build sections
→ See exact evidence and actionable summaries
→ Restart offline and still browse cached local analyses
```

The application should not feel like a SQL table viewer.

---

# 6. Visual redesign requirements

The current Batch 1 screenshot is functional but too plain.

Do a substantial visual pass.

Design direction:
- original ZiRcoN Coach visual identity;
- dark gaming analytics dashboard;
- polished but restrained;
- information-dense without being cluttered;
- clear hierarchy;
- custom cards rather than raw database tables;
- strong win/loss and severity semantics;
- consistent spacing and rounded surfaces;
- readable at 1080p;
- good resizing behavior.

Do not clone OP.GG, Mobalytics, Porofessor, U.GG or other products.
Use them only as general UX inspiration.

Suggested palette:
- very dark neutral background;
- slightly lighter sidebar/surfaces;
- one ZiRcoN accent;
- green victory/positive;
- red defeat/critical;
- amber caution/partial;
- blue/grey information/unknown.

Do not use excessive neon/glow effects.

---

# 7. Main shell redesign

Target:
- default around 1400×850;
- sensible minimum around 1100×700;
- resizable;
- no clipping;
- no giant dead areas.

Left sidebar:
- ZiRcoN Coach brand;
- Dashboard;
- Matches;
- Progress;
- Settings;
- version/status near bottom.

Top bar:
- current page title;
- compact player identity;
- API status badge;
- last sync status;
- prominent Sync button;
- optional compact refresh/spinner status.

The user should always know whether data is:
- local;
- syncing;
- current;
- API-unavailable.

---

# 8. Dashboard redesign

Replace the plain "four cards + huge table" feel.

## 8.1 Player hero

Show when available:
- profile icon;
- Riot ID;
- summoner level;
- queue;
- rank tier/division;
- LP;
- ranked W/L;
- ranked WR;
- API/local status;
- last sync.

If rank endpoint is unavailable:
show an explicit clean unavailable state.

Never invent rank.

## 8.2 Main performance cards

Use real local data:
- loaded SoloQ games;
- win rate;
- KDA;
- CS/min;
- deaths/game;
- optional average duration.

Show period label:
`Local sample` / `Last 20` / `All loaded`.

## 8.3 Recent form

Add a compact last-N visual:
- W/L chips;
- recent WR;
- current champion mix.

## 8.4 Recent matches

Do NOT use a giant generic table as the main dashboard experience.

Build reusable custom `MatchCard` / row widgets.

Each recent match card should show where data exists:
- champion icon;
- champion name;
- role;
- victory/defeat accent;
- K/D/A;
- KDA;
- CS/min;
- duration;
- item icons;
- played time;
- analysis status;
- click to open post-game.

Use a clean empty state if none.

---

# 9. Data Dragon visual assets

Create/rework an `AssetService`.

Use Riot Data Dragon for:
- champion icons;
- item icons;
- profile icons where appropriate.

Rules:
- local cache first;
- no network blocking on Qt main thread;
- safe placeholder;
- failed image download never crashes page;
- cache directory ignored by Git.

Recommended runtime cache:
`.cache/zircon/assets/`

If `.gitignore` does not cover it:
add it.

IMPORTANT:
The UI asset Data Dragon version may track current/display assets separately from the frozen knowledge semantic version.
Do NOT silently change frozen Item/Champion knowledge versions just to get current icons.

Document this separation.

---

# 10. Dynamic Riot API key management

This is mandatory.

The user regularly has to replace an expiring Riot development API key.

The application must make this painless.

## 10.1 Settings UI

Add a polished Riot API section:

```text
Riot API
Status: Valid / Invalid / Expired / Not configured / Rate limited / Unknown

[ masked key field __________________ ]
[ Validate ] [ Save / Replace Key ]
```

Requirements:
- password/secret echo mode;
- never show the full existing key;
- never log it;
- never put it in exceptions displayed to the user;
- never commit it;
- optionally show only a safe suffix such as `••••ABCD`.

## 10.2 Storage

For this local dev Alpha, continue using project-root `.env` unless the existing architecture clearly provides a safer local mechanism.

Use `python-dotenv` APIs such as `set_key` or an equivalent safe implementation.

Do not rewrite unrelated `.env` values.

`.env` stays gitignored.

## 10.3 Runtime refresh

Saving a new API key must take effect WITHOUT restarting the app.

Do not rely on the old import-time `config.settings.RIOT_API_KEY` constant for the new GUI sync workflow if that prevents hot replacement.

Preferred:
create a new dynamic UI/service-layer Riot client that takes the key explicitly at runtime.

The legacy Riot module may remain untouched for old harness compatibility.

## 10.4 Validation

Validate the proposed key with a real safe Riot request.

Prefer validating through the configured Riot account or another low-cost endpoint.

Typed outcomes:
- VALID
- NOT_CONFIGURED
- UNAUTHORIZED / EXPIRED
- FORBIDDEN
- RATE_LIMITED
- NETWORK_ERROR
- RIOT_SERVER_ERROR
- ACCOUNT_NOT_FOUND where relevant

Do not treat 429 as "invalid key".

Do not save an invalid key silently.

Allow user to replace an expired key quickly.

---

# 11. New dynamic Riot client/service

Create a V0.1 service such as:

```text
services/riot_client.py
services/riot_sync_service.py
```

or equivalent.

Do not put HTTP code in widgets.

Requirements:
- explicit API key;
- `requests.Session` or clean equivalent;
- proper timeout;
- finite retries;
- 429 uses `Retry-After`;
- no infinite loop;
- typed errors;
- no secret in repr/logs;
- account-v1;
- match-v5 IDs;
- match details;
- timeline;
- summoner/profile endpoint if needed;
- ranked league endpoint if needed.

Use the correct platform/regional routing for EUW.

Where endpoint semantics are uncertain:
verify against the current official Riot API behavior before hardcoding.

Do not change existing frozen data semantics.

---

# 12. Riot ID / player configuration

Settings should show/edit the Riot ID.

Format:
`GameName#TagLine`

Default:
- discover from current local player when possible;
- preserve current account if valid.

The user should not edit Python code to change account.

Persist non-secret player settings in a runtime-local settings file or another clean untracked mechanism.

Do not commit personal runtime state.

---

# 13. Asynchronous sync UX

The Sync button is mandatory.

No Riot request on the Qt main thread.

Use a proper Qt worker architecture:
- `QThreadPool + QRunnable`, or
- `QThread` with signals.

The main window should remain responsive.

Sync states:
- Idle
- Validating API
- Fetching profile
- Fetching match IDs
- Downloading match X/Y
- Downloading timelines X/Y
- Running post-game analysis X/Y
- Refreshing UI
- Complete
- Partial failure
- Failed

Show a progress indicator and short status text.

Disable duplicate concurrent syncs.

A failed sync must not destroy local data.

---

# 14. Sync scope

Default practical V0.1 behavior:
- request latest 20 SoloQ matches;
- import only missing match details;
- backfill missing timeline/analysis data for recent matches;
- preserve older local history.

Allow a simple scope choice in Settings or Sync menu if easy:
- 20
- 50
- 100

Do not fetch hundreds unnecessarily every launch.

Queue target:
420 SoloQ by default.

---

# 15. Existing database integration

Reuse existing trusted database functions where appropriate, including current match persistence.

Do not rewrite all DB logic.

Current schema already contains:
- matches;
- participants;
- raw match JSON.

Use existing `save_match` when safe.

For new V0.1 cache/persistence needs, prefer NEW additive modules/tables rather than rewriting old DB behavior.

---

# 16. Timeline persistence

Post-game analyzers need timeline/event data.

Audit what is already persisted.

If timeline raw JSON is not persistently available:
add a new additive cache table/module such as:

```text
match_timelines
- match_id PRIMARY KEY
- fetched_at
- source_version/game_version if useful
- raw_json
```

Do NOT modify a frozen analyzer to own persistence.

Requirements:
- existing matches can be backfilled;
- no repeated timeline download when cached;
- offline post-game works after timeline was cached;
- malformed cache fails closed and can be refreshed.

---

# 17. Post-game analysis orchestration

This is mandatory.

Create a new UI-facing orchestration layer, e.g.:

```text
services/post_game_analysis_service.py
services/coaching_service.py
```

It must adapt frozen analyzers without modifying them.

Integrate, where their exact frozen input contracts can be satisfied:

1. Death Analyzer
2. Jungle Tempo / Pathing Analyzer
3. Objective Analyzer
4. Recall / Reset Analyzer
5. Build / Itemization Analyzer

Also inspect whether the existing deterministic coaching engine can safely add a top-level historical coaching summary without conflicting with frozen outputs.

Do not use an LLM.

---

# 18. Analyzer integration method

For EACH frozen analyzer:

1. inspect the exact public functions/classes;
2. identify required input:
   - match detail;
   - timeline;
   - participant/puuid;
   - role;
   - local history;
   - item data;
3. build a new adapter;
4. preserve original status/evidence;
5. normalize only for presentation;
6. fail closed if required data is absent.

Do not derive new causal claims.

A UI adapter may simplify names but must not alter meaning.

Example normalized record:

```text
InsightViewModel
- category
- title
- summary
- severity
- status
- timestamp/window
- evidence
- source_module
- source_version
- raw/reference identity if useful
```

---

# 19. Analysis caching

The user should not have to recompute every analyzer on every UI repaint.

Implement persistent or deterministic cached post-game reports.

Recommended additive table:

```text
analysis_reports
- match_id
- analyzer_name
- analyzer_version
- generated_at
- status
- report_json
PRIMARY KEY(match_id, analyzer_name, analyzer_version)
```

If a different cache design better fits current repo, use it.

Cache requirements:
- analyzer version in key;
- stale result invalidated when analyzer version changes;
- cached result readable offline;
- UI never treats stale incompatible version as current.

No analyzer calculation in paint/render callbacks.

---

# 20. Post-game page redesign

The current placeholder message is not acceptable for completed V0.1.

Build a rich post-game page.

## 20.1 Header

Show:
- champion icon;
- champion name;
- VICTORY / DEFEAT;
- role;
- K/D/A;
- KDA;
- CS / CS/min;
- duration;
- date;
- item build as actual icons;
- analysis status.

## 20.2 Summary

A top `Coach Summary` section:
- 2–4 highest-signal supported takeaways;
- concise;
- evidence-gated;
- no speculation.

Categories visually identified:
- Death
- Tempo
- Objectives
- Recall
- Build

If nothing actionable:
say that no high-confidence issue was identified in available analyzers.

Do not invent advice just to fill space.

## 20.3 Analyzer navigation

Use tabs, segmented control, or well-designed collapsible cards.

Required sections when supported:

### Overview
- factual match performance;
- key supported insights;
- status of each analyzer.

### Deaths
- analyzed death count;
- timestamps;
- classifications;
- cost/impact evidence exposed by frozen analyzer;
- severity;
- expandable technical evidence.

### Tempo / Pathing
- important windows/events;
- tempo loss/gain classifications;
- supported pathing context.

### Objectives
- objective preparation/timing facts;
- major supported findings.

### Recalls / Resets
- recall/reset events;
- supported outcome quality;
- timing/context.

### Build
- item purchase/order/timing where known;
- factual analyzer findings;
- item knowledge details;
- no unvalidated optimal-build recommendation.

Every section needs:
- LOADING
- AVAILABLE
- PARTIAL
- UNAVAILABLE
- ERROR

states.

---

# 21. Coaching severity and status semantics

Create consistent display semantics.

Example status badges:
- EXACT / RESOLVED
- SUPPORTED
- PARTIAL
- UNKNOWN
- UNAVAILABLE

Severity:
- Positive
- Info
- Warning
- Critical

Do not equate `PARTIAL` with "bad play".
Status is epistemic confidence/data availability.
Severity is gameplay impact only when analyzer supports it.

---

# 22. Match History redesign

Upgrade from a raw table.

Preferred:
custom scrollable match rows/cards.

Each row:
- champion icon;
- result color rail;
- champion + role;
- K/D/A;
- CS/min;
- duration;
- item icons;
- date;
- analyzer readiness badge;
- click target.

Filters:
- All
- Wins
- Losses

Optional if clean:
- champion filter;
- analyzed/not analyzed.

Do not overbuild filtering.

---

# 23. Profile and rank

During sync fetch current player profile/rank when the Riot APIs support it.

Display:
- profile icon;
- summoner level;
- SoloQ tier/division/LP;
- wins/losses.

If unranked:
show `Unranked`.

If API unavailable:
retain last cached profile if available, clearly marked cached.

Do not fake current rank from local match history.

---

# 24. Profile cache

Persist non-secret profile metadata locally so the app still looks complete offline.

Cache fields may include:
- Riot ID;
- puuid;
- profile icon ID;
- summoner level;
- rank/tier/division;
- LP;
- ranked wins/losses;
- fetched timestamp.

Clearly mark cached/stale data when offline if appropriate.

Do not store API key in profile cache.

---

# 25. Progress page — product quality

Improve the current raw champion table.

Minimum:
- selectable window: Last 10 / 20 / 50 / All;
- win rate;
- KDA;
- CS/min;
- deaths/game;
- recent vs previous equivalent window.

Add 2–3 lightweight trend visualizations:
- win result / rolling WR;
- CS/min;
- deaths or KDA.

Use Qt-native drawing/custom widget if practical.
Avoid a heavyweight dependency solely for charts.

Champion pool section:
- champion icon;
- games;
- WR;
- KDA;
- CS/min.

No personal "tier rating" yet.

---

# 26. Asset/image loading

Do not freeze UI while images download.

Use:
- background worker; or
- Qt network manager.

Prefer local cached pixmaps.

Image UI should not resize/jump badly after load.

Use rounded square/circle masks where visually appropriate.

---

# 27. Settings page redesign

Make it a proper settings/data control page, not a plain form dump.

Sections:

## Account
- Riot ID edit
- Save

## Riot API
- API status
- masked replacement field
- Validate
- Save/Replace
- last validation message

## Sync
- latest match count target (20/50/100)
- Sync Now
- optional Backfill Analyses

## Local data
- DB path
- loaded match count
- latest local match
- timeline cache count
- analyzed match count
- last successful sync

## App
- V0.1 Alpha
- frozen backend baseline summary

Never show full secrets.

---

# 28. Expired-key experience

This matters because Riot development keys expire frequently.

When Riot returns unauthorized/forbidden due to key:

Top bar/banner should clearly show:

`Riot API key invalid or expired — Replace key in Settings`

Provide a one-click route to Settings.

The application must keep local data usable.

After replacing a key successfully:
- banner clears;
- API badge becomes Valid;
- no restart;
- user can immediately Sync.

---

# 29. Error handling

Normal user UI must never display raw Python tracebacks.

Map errors to human-readable messages.

Detailed technical exceptions may go to local logs, without secrets.

Handle:
- missing DB;
- empty DB;
- DB locked;
- malformed row;
- invalid match JSON;
- missing timeline;
- invalid/expired API key;
- account not found;
- network timeout;
- 429;
- Riot 5xx;
- DDragon failure;
- analyzer exception;
- partial analyzer support.

One analyzer failure must not break the whole post-game page.

---

# 30. Offline-first acceptance

Test this explicitly:

1. sync at least fixture data / create realistic test cache;
2. disable Riot/network in test;
3. relaunch app;
4. Dashboard still loads local data;
5. Matches still load;
6. cached post-game analyses still load;
7. Settings shows API/network unavailable cleanly.

Riot API must NOT be required to bootstrap the app.

Do not import a module at application startup that raises solely because `RIOT_API_KEY` is absent.

---

# 31. Performance and responsiveness

Target development database:
~100–200 matches.

Goals:
- app opens quickly;
- switching pages responsive;
- match list scroll smooth;
- no repeated full DB scan on every repaint;
- no analyzer recompute on page paint;
- all network work asynchronous;
- expensive analysis runs in worker.

Introduce lightweight in-memory caching where useful.

Do not prematurely build complex pagination infrastructure unless required.

---

# 32. Code architecture target

A reasonable V0.1 architecture may look like:

```text
app/
    application.py
    bootstrap.py
    paths.py
    runtime_settings.py
    v01_alpha_audit.py
    v01_alpha_smoke.py

services/
    local_data.py
    riot_client.py
    riot_sync_service.py
    asset_service.py
    post_game_analysis_service.py
    coaching_service.py
    profile_service.py
    analysis_cache.py
    timeline_cache.py

viewmodels/
    models.py
    # optional presentation-specific modules

ui/
    main_window.py
    theme.py
    workers.py
    components/
        sidebar.py
        topbar.py
        profile_hero.py
        stat_card.py
        status_badge.py
        match_card.py
        item_strip.py
        insight_card.py
        loading_state.py
        empty_state.py
        trend_chart.py
    pages/
        dashboard_page.py
        matches_page.py
        match_detail_page.py
        progress_page.py
        settings_page.py

run_app.py
```

Do not force this exact file count if a cleaner equivalent fits.

Avoid god objects.

Widgets should not own HTTP, SQL schema migrations, or frozen analyzer logic.

---

# 33. Data/viewmodel improvements

Expand current dataclasses as needed.

Useful UI contracts:

## PlayerViewModel
- riot_id
- puuid
- profile_icon
- level
- queue
- tier
- division
- lp
- ranked_wins
- ranked_losses
- fetched_at/cache_status

## MatchSummaryViewModel
- match_id
- champion
- champion_id
- champion_icon
- role
- result
- K/D/A
- KDA
- CS
- CS/min
- duration
- timestamp
- items
- analysis_status

## MatchDetailViewModel
- match summary
- items
- raw factual secondary stats where available
- coaching report

## CoachingReport
- per-analyzer sections
- top takeaways
- overall availability
- evidence/provenance

Keep models deterministic and serializable where useful.

---

# 34. Testing — API key

Create tests using temp files and mocked HTTP.

Required:
1. missing `.env` -> NOT_CONFIGURED
2. masked UI never exposes full test key
3. valid mock response -> VALID
4. 401/403 -> INVALID/EXPIRED
5. 429 -> RATE_LIMITED, not INVALID
6. save replacement key preserves other `.env` entries
7. runtime client uses replacement key without restart
8. exceptions/logs do not include key

Never use the real key in committed tests.

---

# 35. Testing — sync

Mock Riot HTTP.

Test:
- new IDs imported;
- existing matches not re-fetched unnecessarily;
- timeline cached;
- timeline backfilled for existing match;
- partial match failure continues;
- API invalid leaves DB untouched;
- refresh signals emitted;
- no duplicate concurrent sync;
- progress accounting correct.

---

# 36. Testing — analyzers

For each integrated frozen analyzer:
- use a real pinned/local fixture or minimized exact fixture;
- call through the NEW adapter/service;
- assert source module/version retained;
- assert normalized status;
- assert no fabricated fields;
- assert missing prerequisites become explicit unavailable/partial.

Do not rewrite frozen tests.

---

# 37. Testing — UI

Use:

```text
QT_QPA_PLATFORM=offscreen
```

Required smoke checks:
- QApplication construction;
- main window;
- navigation;
- Dashboard empty;
- Dashboard with sample data;
- Match list with cards;
- Match detail;
- all analyzer tabs/sections construct;
- Settings API field is masked;
- API invalid banner state;
- syncing state;
- progress page;
- clean shutdown.

No network required for smoke suite.

---

# 38. Manual visual verification

Because this is now a visual product milestone, manual visual validation is mandatory if environment permits.

Actually launch:

```powershell
python run_app.py
```

Inspect at minimum:
- 1400×850;
- near minimum size;
- Dashboard;
- Matches;
- Post-game;
- Progress;
- Settings;
- long Riot IDs;
- long analyzer summary text;
- empty states;
- partial states.

Check:
- no clipped text;
- no overlapping cards;
- no giant pointless blank table;
- icons aligned;
- win/loss readable;
- scroll behavior works;
- dark theme consistent;
- content hierarchy is obvious.

Do not claim manual visual verification if environment cannot display GUI.

---

# 39. Current user data acceptance

The current local development DB observed through Batch 1 contains roughly 104 local matches and correctly resolves the current player Riot ID.

Do not hardcode that count.

After sync with a valid current Riot key:
the Dashboard must update automatically to the actual local count.

A successful sync should not require restarting the GUI.

---

# 40. `Sync` user acceptance scenario

This exact scenario should work:

1. launch `python run_app.py`;
2. current local Dashboard loads;
3. click Settings;
4. paste new Riot development API key into masked field;
5. click Validate;
6. app reports valid;
7. click Save/Replace;
8. no restart;
9. return Dashboard;
10. click Sync;
11. progress visibly updates;
12. new matches are saved;
13. timelines/analyses are cached;
14. Dashboard/match history refresh;
15. open newest match;
16. post-game analyzer sections show supported results.

This is a core Alpha acceptance test.

---

# 41. Post-game trust acceptance

For a match with all required data:
the user should see actual frozen-analyzer information.

For a match lacking timeline/analyzer prerequisites:
the page should say exactly why.

Never show a made-up generic recommendation to hide missing data.

---

# 42. Security audit

Before final commit:
search tracked files/diff for:
- `RGAPI-`
- current API key pattern if detectable without printing it
- `.env` contents
- Authorization/X-Riot token literals containing secrets

Use safe commands that do not echo the actual secret.

Verify:
- `.env` untracked/ignored;
- runtime cache ignored;
- logs do not contain key;
- screenshots/docs do not contain key.

Do not print the user's real key in final response.

---

# 43. V0.1 audit

Build/update a central audit:

`app/v01_alpha_audit.py`

Report:

## Product
- launcher exists
- shell constructs
- all required pages present
- custom match cards present
- post-game sections present

## Riot
- dynamic client
- key replace workflow
- async sync
- typed errors
- offline bootstrap

## Data
- local matches
- timeline cache
- analysis cache
- profile cache

## Coaching
- Death integration
- Tempo integration
- Objective integration
- Recall integration
- Build integration
- provenance preservation
- unsupported states fail closed

## Safety
- frozen modifications = 0
- secret scan = pass

## Tests
- service/unit
- UI smoke
- `python main.py`
- `git diff --check`

Final:
`PASS / REVIEW_REQUIRED FOR ALPHA FREEZE`
or
`REVIEW_REQUIRED`

Do not self-freeze.

---

# 44. Documentation

Update:
- `PROJECT_STATE.md`
- `TODO.md`
- `LAST_RUN.md`

Update `DECISIONS.md` only for durable choices such as:
- dynamic Riot GUI client separate from legacy import-time config;
- timeline/analysis caching;
- UI asset version separated from frozen knowledge version;
- offline-first policy.

Document how to run:

```powershell
.\.venv\Scripts\Activate.ps1
python run_app.py
```

Document tests.

Document API replacement workflow without including a key.

---

# 45. Git strategy

Remain on:
`v01-alpha-wip`

Do NOT merge to main in this run.

The goal is a reviewable Alpha branch.

Suggested checkpoint commits:

1. `Stabilize ZiRcoN Coach alpha GUI shell`
2. `Add dynamic Riot sync and API key management`
3. `Integrate trusted post-game analyzers`
4. `Polish ZiRcoN Coach alpha product UI`
5. `Validate ZiRcoN Coach V0.1 Alpha`

Commit names may differ if logically equivalent.

Push:
`origin/v01-alpha-wip`

At final:

```text
git status --short
git diff --check
git rev-parse HEAD
git rev-parse origin/v01-alpha-wip
git rev-parse origin/main
```

HEAD must equal `origin/v01-alpha-wip`.

Main should remain unchanged during this run.

---

# 46. Do not implement in this milestone

Do NOT add:
- Overwolf/live overlay;
- live-game jungle timers;
- pre-game optimal pick;
- live voice assistant;
- LLM-generated coaching;
- ML;
- build optimizer;
- full combat simulator;
- Burst/TTK;
- new rune execution;
- item passive combat engine;
- stat-owner research;
- cloud account;
- installer/exe packaging;
- auto-updater.

Focus on making the current trusted backend visible and useful.

---

# 47. Autonomous work policy

Fix ordinary issues autonomously:
- PySide6 layout;
- signals/slots;
- async worker bugs;
- SQLite locking;
- migrations;
- API adapters;
- Data Dragon caching;
- test fixtures;
- styles;
- DTO conversions;
- analyzer adapter shape;
- error messages;
- performance.

Do not stop for minor implementation choices.

Stop only an affected branch if:
- a frozen change is truly required;
- a frozen analyzer contract cannot be safely satisfied;
- an API behavior cannot be established without guessing;
- a methodological contradiction is discovered.

Continue independent work whenever possible.

---

# 48. Token-efficiency instruction

This is a large Sol run.

Avoid wasting tokens by repeatedly narrating progress.

Work in checkpoints:
- inspect;
- implement;
- test;
- commit;
- continue.

Do not ask the user routine questions that the repository/current data can answer.

Do not restart from scratch.

Reuse the current Batch 1 shell and existing backend.

---

# 49. Final Codex response

Report concisely but completely:

- final branch
- final HEAD
- origin branch SHA
- checkpoint commits
- main unchanged confirmation
- launcher command
- visual redesign summary
- profile/rank support
- API key replacement behavior
- key validation outcomes handled
- sync behavior
- timeline caching
- analysis caching
- Death integration
- Tempo integration
- Objective integration
- Recall integration
- Build integration
- coaching summary logic
- offline behavior
- Data Dragon asset behavior
- UI smoke test results
- service/unit test results
- manual visual verification
- `python main.py`
- FROZEN guard
- secret scan
- `git diff --check`
- known Alpha limitations

Final status:
`PASS / REVIEW_REQUIRED FOR ALPHA FREEZE`

Do NOT merge main.
Do NOT freeze V0.1 yourself.
Do NOT start V0.2.

---

# Final principle

ZiRcoN Coach V0.1 Alpha should no longer look or behave like a development harness.

It should be a credible desktop coaching application backed by the real local match history and the trusted analyzers already built.

Polish is important, but truthfulness is more important.

---

# Completion status

`COMPLETED / PASS / REVIEW_REQUIRED FOR ALPHA FREEZE`

Completed on 2026-09-04 on branch `v01-alpha-wip`.

- `python run_app.py` opens the PySide6 desktop product; `main.py` remains the backend harness.
- Dashboard, custom Match History, rich Post-game, Progress, and Settings/Data screens are implemented with real local data.
- Dynamic masked key validation/replacement, non-blocking latest-20 sync, match/timeline backfill, profile cache, analysis cache, and offline browsing are implemented.
- Real Riot validation returned `VALID`; real latest-20 sync returned `COMPLETE` with 0 failures.
- Death v11, Tempo/Pathing v17, Objective v20, Reset v21, and Itemization v22 are consumed through adapters; 5/5 sections were available on a real recent match.
- No frozen production/validation file was modified, Phase 2I remains closed, and no combat semantics were added.
- V0.1 is not FROZEN. No V0.2 or new backend phase has started.

A beautiful card that says `PARTIAL — timeline missing` is better than a fake coaching recommendation.
