# ZiRcoN Coach - Project State

## Frozen analyzers
- Death Analyzer: v11 - FROZEN.
- Jungle Tempo / Pathing Analyzer: v17 - FROZEN.
- Objective Analyzer: v20 - FROZEN.
- Recall / Reset Analyzer: v21 - FROZEN.

Frozen means: no retuning/refactor without a demonstrated correctness or integration bug or explicit project review request.

## In development
- Build / Itemization Analyzer v22 Phase 1 - implemented, in validation, REVIEW_REQUIRED.
- Scope is factual item timeline / inventory reconstruction only; no recommendation logic, item-quality label, or build scoring.

## Dataset
- Main historical validation set: 87 Jungle games with exploitable timelines.
- Queue 420.
- Primary profile: ZiRcoN1977#EUW.
- Windows / Python.

## Death Analyzer v11
- Historical-only scoring.
- Death volume and per-death Gold/XP costs separated.
- Association language only.
Known limits: minute-level Riot frames, overlapping episode costs, contextual trade semantics, chain percolation.

## Jungle Tempo / Pathing v17
- Global tempo outside death contamination.
- Personal FARMABLE pathing = own XP + Jungle CS.
- MIRRORED for neutral direct comparison.
- Time-local references.
- Boundary guard +/-60s.
- 1 weak minute = WATCH; sustained about 2+ min = pathing-hole candidate.
Known limits: no exact camps/routes; shop/reset proxy; lane-catch heuristic.

## Objective Analyzer v20
- Preparation + conversion windows.
- Gold/XP/JCS personal and relative.
- Death v11 + Tempo v17 integration.
- Directional before/after trade logic.
- Spatial contest evidence.
- Historical-only scoring, minimum 20 references.
Known limits: proximity != intent; close objective sequences may share fight context; compensation thresholds are heuristic.

## Recall / Reset Analyzer v21
Status: FROZEN by project review.

Design:
- Uses SHOP/RESET proxy from purchase clusters, not exact recall lifecycle.
- Separates post-death shop sequences from voluntary reset proxies.
- Analyzes about 120s before/after.
- Reentry Score is historical-only and measures observed post-reset production, not causal recall quality.
- Current Gold before reset is exploratory/contextual only.
- Objective proximity remains context only and is never an automatic player-mistake label.

Current technical state:
- Latest full runtime verification completed on 2026-08-17 on 87 Jungle games.
- Production v21 remains unchanged at SHOP_CLUSTER_GAP_SECONDS = 20.
- Production dataset: 891 shop/reset proxy sequences.
- Origins: 509 voluntary reset proxies, 382 post-death shops.
- Historical references: 339 CHAMPION_PHASE_ORIGIN_TIME, 282 PHASE_ORIGIN_TIME, 32 CHAMPION_PHASE_ORIGIN, 11 PHASE_ORIGIN, 227 WARMUP.
- Unscored reentries: 263 total; 227 warmup plus 36 with missing +120s post window.
- Global personal reentry measures previously showed robust Win/Loss association under existing validation; strongest was XP vs JGL/min after voluntary reset, Cliff +0.658, CV 77.8%, walk-forward 80.8%, FDR q 0.0006.

Final threshold-independent clustering audit:
- 24 consecutive player shop-cluster pairs had 20s < gap <= 45s.
- Classification no longer uses 20s/30s/45s or any gap cutoff; gap is reported only after classification.
- Audit-only classification: 13 SEPARATE_VISITS, 11 UNRESOLVED, 0 SAME_VISIT_CANDIDATE.
- Riot frame resolution: 13 same-frame pairs, 11 distinct-frame pairs.
- Evidence reasons: 11 same-frame UNRESOLVED, 6 player K/A/D events, 3 major objective/building events on distinct frames, 3 observable OUTSIDE_BASE intermediate frames, 1 resource-progression case.
- Gap-bin results after classification: 20-25s = 0 SAME / 1 SEPARATE / 6 UNRESOLVED; 25-30s = 0 / 1 / 2; 30-35s = 0 / 4 / 1; 35-40s = 0 / 2 / 1; 40-45s = 0 / 5 / 1.
- 20s production clustering threshold retained conservatively.
- Rationale: raising the threshold would merge some independently supported separate visits, while same-frame unresolved cases are insufficient evidence for merging.
- Objective <=5s technical check passed: 6/6 timings measured from cluster end, 6/6 objectives after complete cluster, 6/6 extraction/order checks OK.
- Target match EUW1_7951911875 remained stable: 7 sequences, 4 voluntary, 3 post-death, 0 near-threshold pairs, 2 tight-pre-objective proxies.

Permanent v21 limitations:
- Riot data does not expose a perfect recall lifecycle.
- Purchase clusters remain SHOP/RESET proxies.
- Same-frame Riot gaps may remain unresolved.
- Current Gold is exploratory context only.
- Objective proximity is context, not player fault.
- Reentry Score is not a causal recall-quality score.

Technical fixes / audit support:
- main.py can fall back to existing local SQLite history when Riot account/match lookup is unavailable.
- main.py configures stdout/stderr as UTF-8 to avoid Windows console encoding failures while rendering analyzer reports.
- analysis/reset_audit.py provides audit-only threshold-independent clustering diagnostics and threshold sensitivity; it does not change production logic.
- .gitignore ignores .env, .venv, *.db, __pycache__, and logs/ so local secrets, DBs, and logs are not staged accidentally.

## Build / Itemization Analyzer v22
Status: Phase 1B implemented, REVIEW_REQUIRED, not frozen.

Design:
- New UI-agnostic analyzer reconstructs factual item state from Riot timeline item events.
- Handles ITEM_PURCHASED, ITEM_SOLD, ITEM_UNDO, and ITEM_DESTROYED.
- Uses Data Dragon metadata for names, costs, tags, consumables, boots, and item `from` / `into` graph.
- Consumes component trees transitively, so held subcomponents are removed when a completed item is bought through an implicit intermediate component.
- Treats Data Dragon `consumeOnFull` consumables, such as elixirs, as consumed on purchase.
- Tracks a six-slot item multiset plus trinket state; exact slot ordering is not fabricated.
- Associates purchase events with frozen Recall / Reset v21 shop/reset proxy visit IDs for factual context only.
- Models confirmed non-purchase final grants separately from Riot-observed item transactions.
- Magical Footwear item 2422 is classified as RUNE_GRANT / MAGICAL_FOOTWEAR only when rune 8304 is present.
- Derived grant timing is stored as derived/inferred evidence, never as an observed Riot transaction.

Latest verification:
- `python main.py` completed on 2026-08-17 after v22 Phase 1B updates.
- Full Jungle history: 87 games, 4277 player item events.
- Event counts: 1536 purchases, 11 sells, 45 undo events, 2685 destroyed events.
- Final inventory validation: 86 EXACT, 1 EXACT_WITH_EXPLAINED_GRANT, 0 PARTIAL, 0 MISMATCH, 0 UNKNOWN.
- Observed exact final inventory rate: 98.9%.
- Observed or explained final inventory rate: 100.0%.
- Target match EUW1_7951911875: EXACT final inventory reconstruction.
- Target match EUW1_7836627546: EXACT_WITH_EXPLAINED_GRANT because rune 8304 Magical Footwear is present and final item 2422 has no Riot purchase/undo/sell event.
- EUW1_7836627546 derived grant timestamp: 09:45, DERIVED_INFERRED from Magical Footwear base timing and 3 observed takedowns.
- Non-purchase final grants: 1 match, source RUNE_GRANT, grant type MAGICAL_FOOTWEAR.
- ITEM_DESTROYED audit: 2685 total, 1085 confidently explained, 1600 remaining audit-only ambiguous/unexplained.
- Remaining destroyed classifications: 1582 TEMPORARY_OR_NON_PERMANENT_STATE, 18 UNRESOLVED.
- Warning buckets: 1189 understood expected mechanic, 1085 harmless Riot representation limitation, 515 unresolved final-safe ambiguity, 1 unresolved.
- Viego audit: 9 games, 1384 ITEM_DESTROYED events, 1189 ambiguous destroyed events, 357 permanent-build item destroyed events ignored as ambiguous.
- Major item milestone audit: 265 completed-major milestones, 0 unusual excluded-category milestones.

Known remaining issues:
- Phase 1B is technically ready for review but not frozen; freeze decision belongs to project review.
- Normal ITEM_DESTROYED events are preserved as auditable AMBIGUOUS cases unless explained by same-timestamp component completion, consumable removal, jungle-item removal, or trinket-use handling.
- Viego produces many normal destroyed-item events consistent with temporary copied/possession inventory state; these are not treated as permanent deletion.
- Viego temporary possession inventory remains TEMPORARY_POSSESSION_INVENTORY_UNRELIABLE.
- 18 ITEM_DESTROYED cases and 1 sell warning remain unresolved in audit output, with no final inventory mismatch.
- The analyzer is not frozen until project review accepts the non-purchase grant policy and ambiguous normal ITEM_DESTROYED semantics.

## Architecture
- main.py remains a dev/integration harness.
- Final UI later with PySide6.
- Analysis modules should remain UI-agnostic.
- Itemization v22 logic lives in analysis/itemization_analyzer.py; synthetic checks live in analysis/itemization_synthetic_checks.py.

## Handoff rule
Codex must update this file after each completed task.
