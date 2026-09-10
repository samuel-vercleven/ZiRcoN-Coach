# LAST RUN

## Status

PASS / REVIEW_REQUIRED FOR BUILD OPTIMIZER V1 FREEZE. No freeze or merge.

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
