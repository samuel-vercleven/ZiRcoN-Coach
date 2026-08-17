# ZiRcoN Coach - Decisions Log

## Development philosophy
Develop and validate major analyzers one by one.
Freeze when measurement semantics are coherent, real-game audit is plausible, no major correctness bug remains, validation is appropriate, and limitations are documented.

## Death Analyzer v11 - FROZEN
Reasons:
- historical-only scoring;
- exact death-count conditioning;
- game-level CV, walk-forward, bootstrap, FDR;
- volume separated from per-death cost.
Rule: never phrase cumulative resource loss as causal net cost.

## Jungle Tempo / Pathing v17 - FROZEN
Reasons:
- personal pathing separated from enemy success;
- FARMABLE vs MIRRORED;
- time-local references;
- +/-60s boundary guard;
- sustained alerts became rare and plausible.
Rule: pathing score is a historical composite, not a probability.

## Objective Analyzer v20 - FROZEN
Reasons:
- stable extraction;
- preparation/conversion separation;
- BEFORE vs AFTER trade direction fixed;
- spatial contest;
- meaningful resource-compensation thresholds;
- historical minimum 20.
Rule: contest is evidence, not ground truth; lost objective != automatic player error.

## Recall / Reset Analyzer v21 - FROZEN
Decision:
Freeze Recall / Reset Analyzer v21 with production SHOP_CLUSTER_GAP_SECONDS retained at 20.

Reasons:
- voluntary reset proxies and post-death shop sequences are separated credibly on real history;
- Reentry Score is historical-only;
- real-history validation passed on the local 87-game Jungle dataset;
- threshold-independent clustering audit completed;
- final audit found 13 SEPARATE_VISITS, 11 UNRESOLVED, and 0 SAME_VISIT_CANDIDATE among the 24 pairs with 20s < gap <= 45s;
- 20s clustering threshold is retained conservatively;
- no independent evidence justified increasing the production threshold;
- raising the threshold would merge some independently supported separate visits;
- unresolved same-frame Riot cases are insufficient evidence for merging;
- objective-near reset audit found no extraction/order bug;
- target match EUW1_7951911875 remained stable.

Permanent limitations:
- Riot does not expose a perfect recall lifecycle;
- purchase clusters are SHOP/RESET proxies, not exact recalls;
- same-frame Riot gaps may remain unresolved;
- current Gold is exploratory/contextual only;
- objective proximity is context, not a player-mistake label;
- Reentry Score measures observed post-reset production, not causal recall quality.

Rules:
- Do not change the 20s clustering threshold without explicit project review.
- Do not describe reset proxies as exact recalls.
- Do not convert current Gold, objective proximity, or low Reentry Score into automatic fault labels.
- Keep raw reset components auditable alongside any explanatory composite.
