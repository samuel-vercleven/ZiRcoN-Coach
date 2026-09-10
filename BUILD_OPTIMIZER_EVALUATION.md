# Build Optimizer v1 — Viego evaluation and product gate

## Result

**TECHNICAL PASS / REVIEW_REQUIRED / NO FREEZE.**

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
