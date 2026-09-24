# LAST RUN

## All-champion Build Optimizer coverage — 2026-09-24

- Added a generic champion-class profile fallback using exact-patch Data Dragon
  tags while retaining reviewed Shyvana and Viego profiles.
- Generalized the item-semantic candidate pool from the existing reviewed
  whitelists and made armor/MR/frontline contextual responses champion-neutral.
- The contextual replay now defaults to every local SoloQ champion and accepts
  any champion filter. Unsupported patches and missing class metadata still
  abstain; Build / Itemization Analyzer v22 itself was not changed.
- Updated the match Build Optimizer panel to identify generic class profiles
  and show their lower personalization; Viego-only limitations are no longer
  shown on other champions.
- Focused checks passed (7 contextual, 23 optimizer); the first all-champion
  replay covered 96/143 games on the original four patches. It was superseded
  by the nine-patch run below.
- Read-only audit: all champion catalog records receive a profile on each of
  nine exact cached patches (172–233/patch). Existing Shyvana fingerprints
  match all; Viego has 11/12 matches on 16.8–16.15 and 12/12 on 16.16–16.18.
  Viego item 6610 fails price/recipe fingerprint on the older patches and is
  excluded. Unsupported patch games fell from 47 to 0.
- Final replay: 143 games, 572 snapshots, all 143 games got a champion profile;
  39 games used generic class profiles. It emitted 92 recommendations across
  41 games and 7 champions; zero invalid purchases, future leaks, score errors
  or untraceable explanations. 480 snapshots abstained, chiefly due to
  unreliable reconstructed inventory (469; counters overlap).
- A read-only shop-only inventory experiment changed 379/572 reconstructed
  states and produced 374 over-capacity warnings (versus 58 with the full
  event stream), so ambiguous destruction events were not dropped to force more
  recommendations. The UI now explains abstentions in player-facing language.
- Full gate: 43/43 suites, Stable Base, recipe/golden/historical/contextual
  replay, 89 frozen paths unchanged, 204 files scanned, `git diff --check` all
  PASS. Final state remains **REVIEW_REQUIRED / NO FREEZE** for human gameplay
  review of the generalized recommendations.

## Player coaching v1 — 2026-09-24

- Upgraded the match Coach tab from short analyzer findings to a player-facing
  review: what was observed, why it is worth revisiting, evidence tied to the
  matching event/phase, and one next-game experiment.
- Added dedicated cautious wording for death-cost signals, tempo/pathing phases,
  and post-shop production signals. Cards state the limits of each signal and
  retain analyzer/version traceability; unsupported findings remain excluded.
- The match overview shows the leading review prompt. Empty/partial data explains
  why ZiRcoN is abstaining rather than inventing advice.
- This remains deterministic coaching over existing cached findings, not an
  ML model or a causal diagnosis. Analyzer outputs, optimizer scoring and FROZEN
  files were not changed.
- No tests or runtime validation were run in this turn. Human product review is
  still required before any coaching freeze.

## Match reference follow-up — 2026-09-23

- Added a mirrored ten-player scoreboard inspired by the supplied reference:
  slate surface, team totals, saved Riot names, champion portraits, colored KDA,
  CS/gold, kill participation, vision and two-row item builds with trinkets.
- History compositions now occupy two compact rows of five portraits.
- Missing ranks, bans, spells and runes are not fabricated.
- UI smoke and 30 visual captures: PASS. `main.py`: PASS.
- Full stabilization run: 42/43 passed initially. The remaining regression was
  the changed minimum window width; restoring 1100x700 and the sync-label bound
  fixed it. Its 22 tests passed on rerun. 89 frozen paths unchanged.
- Human visual review remains required; no freeze or main merge.
- Final complete rerun after the fix: PASS, 43/43 suites, 89 frozen paths
  unchanged, secret scan and git diff check passed.

## Status

PASS / REVIEW_REQUIRED FOR BUILD OPTIMIZER V1 FREEZE. No freeze or merge.

## Native PySide6 UI/UX pass

- Removed `qt-material`; the app now uses only PySide6 plus the local ZiRcoN QSS
  design system.
- Corrected startup repaint/reload behavior with one-page startup, one-time lazy
  page creation, explicit refresh-after-data-change, cache-first shared asset
  workers and a single-instance process lock.
- Instrumented startup builds 1 page and 6 match cards in about 0.88 seconds.
  History creates 24 rows on first access, with explicit incremental loading.
- Dashboard, sidebar, top bar and History were rebuilt around compact surfaces,
  stable spacing and a fixed 98 px match grid.
- Match rows now use champion/item portraits and 5v5 image-driven compositions
  with tooltips; status metadata is visually secondary.
- Visual check: PASS, 30 captures at 1600x900 and 1180x720, including all
  post-game tabs and the populated Build Optimizer view.
- Frozen backend files modified: 0. Build Optimizer and analyzer behavior remain
  unchanged. Human visual review is still required; see `UI_UX_REDESIGN_REPORT.md`.

## Viego contextual pass

- `viego_timeline_provenance_audit_v1` inspected 30 local SoloQ Viego games:
  527 own shop transactions (514 purchases, 2 sales, 11 undos) and 4,279
  `ITEM_DESTROYED` events. The latter are excluded from the Viego permanent
  inventory projection because they are possession/runtime-sensitive.
- `PERMANENT_SHOP_INVENTORY` is an observed prefix reconstructed only from
  player-scoped `ITEM_PURCHASED`, `ITEM_SOLD` and `ITEM_UNDO`. It is not a
  claim about the temporary possessed champion inventory or shop access.
- Viego frame `championStats` remain possession-sensitive and are not used as
  personal scoring inputs. Enemy observations remain separately scoped.
- `viego_build_profile_v1` supplies twelve exact-patch, ID/price/direct-recipe
  fingerprinted semantic profiles spanning AD, attack speed, on-hit, crit,
  anti-frontline/armor penetration and physical/magic survivability.
- Viego-only chronological replay: 30 games, 26 exact-patch games, 104
  snapshots, 34 nonempty recommendations and 70 abstentions. The 34 emitted
  rows have 0 invalid purchases, future leaks, score recomputation failures or
  untraceable explanations. Target distribution: Blade of the Ruined King 11,
  Wit's End 10, Terminus 6, Kraken Slayer 3, Lord Dominik's Regards 2 and
  The Collector 2.

## Correction found during replay

The independent replay invoice counted each stacked consumable as a distinct
slot, while the frozen v22 planner correctly counts a stack as one slot. The
audit now uses the same frozen slot contract. This preserves slot safety and
allows valid plans with stacked potions; non-stackable over-capacity plans are
still rejected.

## Final validation

- contextual checks: PASS (7 tests)
- optimizer unit/scenario checks: PASS (23 tests)
- adversarial gate checks: PASS (15 tests)
- Viego audit: PASS with explicit product limitations
- Viego contextual replay: PASS / 34 emitted rows
- `python main.py`: PASS; 89 FROZEN paths unchanged
- `python -m build_optimizer.validation`: technical PASS. Stable Base, unit,
  adversarial, real-catalog, Golden, batch and generalized contextual replay
  all passed. It produced 53 nonempty contextual recommendations overall,
  including the 34 Viego rows; zero invalid emitted buys, future leaks, score
  recomputation failures or unexplained recommendations.

The final zero gate is `REVIEW_REQUIRED / NO FREEZE` solely because gameplay
quality remains a human product review. It passes the 20-row coverage target,
recipe/slot/budget validity, temporal integrity and explanation traceability.

Implementation commit: `871e338fdc0c36de3646cc119e86b8b6501cd798`, pushed to
`origin/feature/build-optimizer`. No merge into `main` was performed.

## Post-game match recap UI

- The first post-game tab now presents both teams with champion, role, K/D/A,
  CS, gold, damage and final item strips.
- The contextual recommendation keeps a separate, dated frame-only opponent
  display (champions plus observed HP/armor), and its reasons are shown as the
  explanation for that composition. Final-match information is never fed back
  into the historical optimizer decision.

## Professional UX pass

- Added an action-oriented dashboard review entry point, history filters and
  local match favorites/notes.
- Added post-game direct-role comparison and a factual local team-gold
  timeline with observed objectives. Missing local timeline data fails closed
  in the UI; no synthetic graph is rendered.
