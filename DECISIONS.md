# ZiRcoN Coach — Decisions Log

## Development philosophy
Develop and validate major analyzers one by one.
Freeze when measurement semantics are coherent, real-game audit is plausible, no major correctness bug remains, validation is appropriate, and limitations are documented.

## Death Analyzer v11 — FROZEN
Reasons:
- historical-only scoring;
- exact death-count conditioning;
- game-level CV, walk-forward, bootstrap, FDR;
- volume separated from per-death cost.
Rule: never phrase cumulative resource loss as causal net cost.

## Jungle Tempo / Pathing v17 — FROZEN
Reasons:
- personal pathing separated from enemy success;
- FARMABLE vs MIRRORED;
- time-local references;
- ±60s boundary guard;
- sustained alerts became rare and plausible.
Rule: pathing score is a historical composite, not a probability.

## Objective Analyzer v20 — FROZEN
Reasons:
- stable extraction;
- preparation/conversion separation;
- BEFORE vs AFTER trade direction fixed;
- spatial contest;
- meaningful resource-compensation thresholds;
- historical minimum 20.
Rule: contest is evidence, not ground truth; lost objective != automatic player error.

## Recall / Reset Analyzer v21 — IN VALIDATION
Decision:
Use SHOP/RESET proxy, not “exact recall”.

Reasons:
- purchase events are available; perfect recall lifecycle is not.
- post-death shop must be separated from voluntary reset.
- current Gold from Riot frames is contextual/exploratory only.

Freeze criteria:
- clustering is credible on real games;
- voluntary vs post-death classification is credible;
- objective-near reset audit has low false-positive risk;
- reentry score is historical-only and sufficiently populated;
- no automatic “bad recall” label from current Gold alone.
