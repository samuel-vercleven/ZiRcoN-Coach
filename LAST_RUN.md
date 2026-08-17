# LAST RUN

## Status
REVIEW_REQUIRED

## Date
2026-08-17 23:00 local

## Command
python main.py

## Runtime
- completed
- approximate duration: 74 seconds
- raw terminal output saved to logs/latest_full_run.txt
- dedicated itemization audit also saved to logs/itemization_v22_phase1_audit.txt

## Files changed
- analysis/itemization_analyzer.py
- analysis/itemization_synthetic_checks.py
- main.py
- TODO.md
- PROJECT_STATE.md
- LAST_RUN.md

## Tests executed
- `.venv\Scripts\python.exe -m py_compile analysis\itemization_analyzer.py analysis\itemization_synthetic_checks.py main.py`
- `.venv\Scripts\python.exe -m analysis.itemization_synthetic_checks`
- `.venv\Scripts\python.exe -m analysis.itemization_analyzer`
- `.venv\Scripts\python.exe main.py`

## Errors encountered
- No runtime traceback.
- Initial historical reconstruction left many extra components; fixed by consuming Data Dragon component trees transitively when a completed item is purchased.
- Initial historical reconstruction kept elixirs as slot items; fixed by treating Data Dragon `consumeOnFull` consumables as consumed on purchase.

## Main analyzer results
### Death Analyzer
- v11 not modified; remains FROZEN.

### Tempo / Pathing
- v17 not modified; remains FROZEN.

### Objective Analyzer
- v20 not modified; remains FROZEN.

### Recall / Reset Analyzer
- v21 not modified; remains FROZEN.
- Itemization uses the frozen v21 shop-cluster gap constant only to attach factual shop/reset proxy visit IDs.

### Current analyzer
- Build / Itemization Analyzer v22 Phase 1 implemented as factual reconstruction only.
- Processed 87 Jungle games and 4277 player item events.
- Event counts: 1536 purchases, 11 sells, 45 undo events, 2685 destroyed events.
- Final inventory validation: 86 EXACT, 1 PARTIAL, 0 MISMATCH, 0 UNKNOWN.
- Exact final inventory rate: 98.9%.
- Target match EUW1_7951911875: EXACT final inventory reconstruction.
- Target milestones: first completed major Tueur de krakens at 09:24, Percepteur at 19:06, Arc-bouclier immortel at 21:57.
- Data Dragon metadata is used for names, costs, tags, `from`/`into`, consumables, boots, and component graph traversal.

## Suspicious findings
- One PARTIAL game remains: EUW1_7836627546 has Riot final item 2422 / Magical Footwear but no player ITEM_PURCHASED/UNDO/SOLD event exposing that grant in the stored timeline.
- Viego generates many normal ITEM_DESTROYED events that look like temporary copied/possession inventory state; these are preserved as AMBIGUOUS and are not treated as permanent deletion.

## Methodological concerns
- REVIEW_REQUIRED: Riot can expose non-purchasable/granted final items without a corresponding item transaction event, at least for 2422.
- REVIEW_REQUIRED: normal ITEM_DESTROYED events cannot be globally interpreted as permanent inventory removal; doing so breaks Viego and several final inventories.

## Remaining issues
- Decide whether v22 should model known non-purchasable grants such as Magical Footwear from final/rune context, or keep them UNKNOWN/AMBIGUOUS until a reliable source is added.
- Decide whether ambiguous normal ITEM_DESTROYED events should remain warnings only, or receive champion/mechanic-specific handling in a later review.

## Codex technical recommendation
- Keep v22 Phase 1 in validation, with current factual reconstruction as the baseline.
- Do not start recommendation logic until project review accepts how to handle unobserved grants and ambiguous destroyed events.

## Review request
- REVIEW_REQUIRED because one real-history final inventory remains PARTIAL due to an unobserved non-purchasable item grant, and because Riot ITEM_DESTROYED semantics remain ambiguous for normal items.
