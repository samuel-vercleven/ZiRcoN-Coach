# ZiRcoN native UI/UX redesign

Player coaching v1 adds player-facing review cards to Match Overview and Coach.
Each card separates the observed signal, why it is worth revisiting, a replay or
next-game experiment, and event/phase evidence. Wording is tailored to death,
tempo/pathing, and post-shop production signals while clearly stating what those
signals cannot prove. Only findings explicitly marked supported are included;
missing/partial evidence produces an abstention message. This is deterministic
presentation logic, not an ML model. Human review remains necessary before any
coaching freeze.

The Build Optimizer match panel now distinguishes reviewed champion-specific
profiles from the broader Data Dragon class fallback and only shows Viego's
possession limitation for Viego. The nine-patch all-champion replay and technical
gates pass; generic gameplay quality still requires human review. Exact-patch
support remains limited to the catalogs listed in `PROJECT_STATE.md`.

Historical note: the validation figures below apply to the earlier UI redesign,
not to the original coaching implementation. The current all-champion gate also
reran the 43-suite Stable Base and UI smoke/semantics checks. Coach wording and
gameplay usefulness still need human review.

Reference follow-up, 2026-09-23: the match overview now uses a slate mirrored
scoreboard with saved participant names, colored KDA, CS/gold, kill participation,
vision and central item grids. History uses two rows of five portraits. Unavailable
rank/bans/spell/rune information is omitted. Main runtime and visual checks pass;
the complete stabilization run passed 42/43 initially, with the remaining minimum
window regression corrected and all 22 focused regression tests passing afterward.

## Status

`PASS / REVIEW_REQUIRED` for human visual review. No backend freeze and no merge
to `main`.

## Scope

- Pure PySide6 desktop rendering with the local ZiRcoN QSS design system.
- `qt-material` removed from code, requirements and the local virtual environment.
- No third-party UI theme dependency remains.
- Frozen analyzers, knowledge foundations and Build Optimizer behavior are unchanged.

## Startup correction

The previous shell built Dashboard, History, Progress, Settings and Match Detail
before showing the window. Their constructors performed initial refreshes, History
could build every match card, and each icon started its own worker even when an
identical asset was already loading. This made the first paint look like repeated
open/close or reload cycles.

The new contract is:

1. Dashboard is the only page created at startup.
2. History, Progress, Settings and Match Detail are created once, at first use.
3. Navigation only changes the visible page.
4. Sync/settings changes explicitly refresh pages that already exist.
5. Assets render a placeholder immediately, read the cache first, and share one
   background request for a missing identical asset.
6. The global worker pool is limited to six concurrent jobs.
7. A process lock prevents repeated launches from creating competing windows.

Instrumented local result at 1600x900/offscreen:

- usable dashboard construction: about 0.88 seconds;
- pages initialized at startup: 1 (previously 5);
- match cards initialized at startup: 6;
- History first render: 24 cards, then explicit `Afficher plus` pages of 24;
- two-launch check: first process remained active, second exited cleanly.

## Visual system

- Centralized native color tokens in `ui/theme.py`.
- Segoe UI hierarchy, 4/8/12/16/20/24/32 spacing rhythm, subtle surfaces and
  borders, restrained cyan accent, and a compact native scrollbar.
- 220 px sidebar with a clear active state and quiet local-data footer.
- Simplified top bar: page context, local status and one synchronization action.
- Compact player hero, KPI cards and factual coaching call-to-action.
- Consistent primary, secondary, ghost and danger button styles.

## Match history

- One fixed-height card component is shared by Dashboard and History.
- Fixed desktop grid: champion, result, KDA, CS/min, duration, items, composition,
  date and action.
- 48 px champion anchor; 30 px item strip; separate trinket.
- Ally/enemy compositions use 24 px champion portraits with role/name tooltips.
- The local player's champion is accented inside the allied composition.
- Win/loss uses only a slim green/red left rail and result text.
- Analysis availability is secondary text rather than a dominant badge.
- Search and filters are stable, compact and debounced.

## Visual validation

`python -m app.v01_visual_check` generates 30 screenshots in
`.cache/zircon/visual-check`, covering:

- Dashboard;
- History;
- Progress;
- Settings;
- Match Overview;
- every post-game tab, including Build Optimizer.

Each view is rendered at 1600x900 and 1180x720. The representative desktop
captures were manually inspected for alignment, clipping, spacing, fixed match
card heights, portraits, items, compositions and scroll behavior.

## Known UI limitations

- The 1180 px fallback hides composition portraits inside narrow match cards;
  the full grid is designed for large desktop screens.
- A missing uncached Data Dragon image still begins as a text placeholder and
  appears progressively when the request completes.
- Human review on the user's actual display scaling remains required before an
  Alpha UI freeze.
