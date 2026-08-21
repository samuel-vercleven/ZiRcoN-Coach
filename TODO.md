# ZiRcoN Coach - TODO

## Model recommendation
Codex: Terra, medium reasoning.

## Current task
COMPLETED - Phase 2F graph-inventory precision correction.

This is a narrow correction of the completed Champion Spell Calculation Source Foundation Phase 2F.
Do NOT start a new phase and do NOT freeze Phase 2F yet.

## Why this correction is required
The real Phase 2F audit is excellent:
- 173/173 champions;
- 692/692 Q/W/E/R primary slots;
- 692 exact key mappings;
- 0 missing/ambiguous slots;
- 0 source failures;
- full audit PASS.

However, `knowledge/champion_spell_source.py` currently appends an entry to
`calculation_nodes` only when a dictionary contains `~class`.

Therefore the audit label `Calculation graph nodes` currently counts class-bearing
dictionary nodes, not every dictionary calculation node under `mSpellCalculations`.
That is narrower than the Phase 2F contract and must be corrected before freeze.

There is also one missing explicit precision fixture for
`NamedDataValueCalculationPart`.

## A - Graph inventory correction
Modify only the Phase 2F files and the development harness/docs required for this task.

In `knowledge/champion_spell_source.py`:

1. Inventory every DICTIONARY node recursively under `mSpellCalculations`,
   whether or not it exposes `~class`.
2. Lists are traversal containers and scalar values are fields, not separate graph nodes.
3. Every dictionary-node inventory record must preserve:
   - `graph_path`;
   - nullable `calculation_class`;
   - `field_names`;
   - `raw_node_payload`;
   - named DataValue references when present;
   - stat references when present;
   - coefficient/ratio/multiplier fields when present;
   - an explicit interpretation status.
4. A dictionary node without `~class` must remain explicit and must not be silently
   discarded. Use a conservative status such as `NO_CALCULATION_CLASS_EXPOSED`.
5. A node with `~class` remains `UNINTERPRETED_CALCULATION_CLASS`.
6. Keep the full `raw_m_spell_calculations` graph unchanged/lossless.
7. Do not execute or interpret any formula.

## B - Empty calculation mapping
Treat:

`mSpellCalculations = {}`

as `NO_CALCULATIONS_EXPOSED`, not `CALCULATIONS_EXPOSED`.

Add a deterministic test for this case.

## C - Audit accounting
Update `knowledge/champion_spell_source_full_audit.py` so that it reports separately:

- total dictionary graph nodes;
- dictionary nodes with `~class`;
- dictionary nodes without `~class`;
- unique calculation classes;
- count per non-null calculation class.

Do not include `None` in class counts.

Do not target the previous `4,687` graph-node count. Recompute the real baseline.

Keep all existing hard invariants:
- 173 champions;
- 692 primary slots;
- exact pinned commit;
- no fuzzy mapping;
- 0 source failures;
- 0 missing/ambiguous slots.

## D - Missing precision fixture
In `knowledge/champion_spell_source_precision_checks.py`, add an explicit fixture using:

`~class = "NamedDataValueCalculationPart"`

Verify:
- the class name is preserved exactly;
- `mDataValue` is preserved exactly;
- its graph path is preserved;
- it remains non-executable / uninterpreted.

Do not replace the existing stat-based fixture; add this coverage.

## E - Synthetic coverage
Add/adjust deterministic checks for:
- classless dictionary nodes are inventoried;
- nested classless dictionary nodes preserve raw fields/path;
- empty `mSpellCalculations` -> `NO_CALCULATIONS_EXPOSED`;
- existing exact mapping/no-fallback behaviors remain unchanged.

## F - Frozen boundaries
Do NOT modify production logic in:
- Death Analyzer v11;
- Jungle Tempo / Pathing v17;
- Objective Analyzer v20;
- Recall / Reset Analyzer v21;
- Build / Itemization Analyzer v22 Phase 1;
- Item Knowledge Phase 2A;
- Champion Knowledge Phase 2B1;
- Rune Knowledge Phase 2C1-B;
- Level-Resolved Champion Stats Phase 2D v4;
- Combat Resistance Phase 2E v1.

Phase 2F itself is not frozen yet, so its four files may be corrected.

## G - Validation
Run:
- py_compile;
- Phase 2F synthetic checks;
- Phase 2F precision checks;
- full real pinned-source audit;
- `python main.py`;
- FROZEN guard;
- `git diff --check`.

Update:
- `PROJECT_STATE.md`;
- `LAST_RUN.md`;
- `TODO.md` -> COMPLETED when clean.

Do NOT declare Phase 2F FROZEN.

Commit and push if clean.

Suggested commit:
`Harden champion spell source graph inventory`

Finish with REVIEW_REQUIRED for ChatGPT/project freeze review.

## Completion status
PASS - Narrow graph-inventory correction completed and real audit rerun on 2026-08-22.

REVIEW_REQUIRED - Only ChatGPT/project review may freeze Phase 2F.

- Every dictionary node under `mSpellCalculations` is now inventoried, including classless nodes.
- Empty `{}` calculation mappings return `NO_CALCULATIONS_EXPOSED`.
- Real audit: 5,318 dictionary nodes = 4,687 with `~class` + 631 without `~class`.
- Hard invariants remain clean: 173/173 champions, 692/692 exact primary mappings, 0 source failures, 0 missing/ambiguous slots, 0 malformed graphs.
- Validation: synthetic PASS 10/10, precision PASS 4/4, full audit PASS, `python main.py` PASS, FROZEN guard PASS.
