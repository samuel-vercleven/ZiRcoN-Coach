# Build Optimizer v1 — Viego evaluation and product gate

## Result

**TECHNICAL PASS / REVIEW_REQUIRED / NO FREEZE.**

## All-champion extension — technical PASS, gameplay REVIEW_REQUIRED

The full gate passed after expanding exact-patch support to all nine locally
cached catalogs: 16.8, 16.9, 16.11, 16.12, 16.14, 16.15, 16.16, 16.17 and
16.18. Every champion record in those catalogs has a reviewed Shyvana/Viego or
generic Data Dragon class profile (172–233 champion records per patch).

| Measure | Result |
|---|---:|
| Local SoloQ games | 143 |
| Games with an admitted champion profile | 143 |
| Generic class-profile games | 39 |
| Snapshots replayed | 572 |
| Nonempty recommendations | 92 |
| Games with at least one recommendation | 41 |
| Champions with at least one recommendation | 7 of 11 |
| Invalid emitted purchases / temporal leaks | 0 / 0 |
| Score recomposition errors / untraceable explanations | 0 / 0 |
| Unsupported-patch games after expansion | 0 |

The 480 snapshot abstentions are intentional gates, not missing champion
profiles. `INVENTORY_UNRELIABLE` appeared on 469 abstentions and
`HISTORICAL_BASELINE_UNAVAILABLE` on 112 (reasons overlap). A read-only
shop-only experiment changed 379/572 reconstructed inventory states and caused
374 over-capacity warnings, so the ambiguous event stream was not discarded to
inflate recommendation coverage. The UI now states abstention reasons in player
language. The 92 outputs satisfy technical invariants, not gameplay quality.

The earlier Viego-only replay results below are historical evidence for that
prior implementation and are not a separate validation of all class-specific
gameplay advice. Status remains **TECHNICAL PASS / REVIEW_REQUIRED / NO FREEZE**.

The contextual engine emits real, nonempty Viego recommendations under the
explicit heuristic contract. This is not a validation that those recommendations
are gameplay-optimal; human gameplay review remains required.

## Reproducible Viego replay

| Measure | Result |
|---|---:|
| Local Viego SoloQ games | 30 |
| Exact-patch eligible games | 26 |
| Candidate snapshots | 104 |
| Nonempty Viego recommendations | 34 |
| Abstentions | 70 |
| Invalid emitted purchases | 0 |
| Future-information leaks | 0 |
| Score recomputation errors | 0 |
| Untraceable explanations | 0 |

The 34-row review target exceeds the minimum 20. Target distribution: Blade of
the Ruined King 11, Wit's End 10, Terminus 6, Kraken Slayer 3, Lord Dominik's
Regards 2 and The Collector 2. Rows retain `PERMANENT_SHOP_INVENTORY`,
`VIEGO_FRAME_STATS_POSSESSION_SENSITIVE` and
`VIEGO_POSSESSION_RUNTIME_STATE_UNOBSERVED` as visible limitations.

Each emitted row is checked against the exact target recipe, observed permanent
shop prefix inventory, frame-sampled gold, six-slot v22 contract, and a future
timeline mutation. The planner reports a conditional `buy_now` plan only for
the current gold **if shopping now**; no current shop location is inferred.

## Gate status

| Gate | Status |
|---|---|
| FROZEN foundation guard | PASS — 89 paths unchanged |
| Contextual unit checks | PASS — 7 |
| Existing optimizer checks | PASS — 23 |
| Adversarial recipe/gate checks | PASS — 15 |
| Viego provenance audit | PASS with explicit limitations |
| Exact-patch Viego profiles | PASS |
| Recipes, budget and slots on emitted rows | PASS |
| Temporal prefix/future mutation integrity | PASS |
| Real Viego recommendations | PASS — 34/20 |
| Score and explanation traceability | PASS |
| Human gameplay quality review | REVIEW_REQUIRED |
| Build Optimizer freeze | **NO FREEZE** |

Final validation passed Stable Base, unit, adversarial, real-catalog, Golden,
batch and generalized contextual replay gates. It exercised 53 nonempty
contextual rows overall, including the Viego-only 34 rows. A green technical
replay cannot convert the heuristic into an optimality claim or auto-freeze the
product.
