ZiRcoN Coach - TODO

Model recommendation

Codex: GPT-5.6 Sol, high reasoning.

Current task

COMPLETED - Champion Spell Calculation Source Foundation Phase 2F.

Why this is the next factual layer

The project now has frozen factual layers for:

Item Knowledge Phase 2A;

Champion Knowledge Phase 2B1;

Rune Knowledge Phase 2C1-B;

Level-Resolved Champion Stats Phase 2D v4;

Combat Resistance / Penetration Rules Phase 2E v1.

Champion Knowledge still intentionally marks champion spell formulas as incomplete. Before building an executable Damage Engine, the project needs a patch-pinned and auditable source of the actual Riot game-file spell calculation graphs.

Phase 2F is therefore a SOURCE / STRUCTURE layer only.

Do NOT execute spell formulas yet.

A - Correct the frozen guard first

main.py currently protects Phase 2D files but does not yet list the four frozen Phase 2E production files in FROZEN_FILES.

Add exactly:

knowledge/combat_resistance_rules.py

knowledge/combat_resistance_synthetic_checks.py

knowledge/combat_resistance_precision_checks.py

knowledge/combat_resistance_full_audit.py

This is a harness guard correction only.

Do NOT modify Phase 2E production code.

B - Exact patch-pinned spell source

Create a new UI-agnostic source layer using the immutable LeagueDatamines LIVE 26.16 commit already accepted by the project for Riot game-file provenance:

Repository:
Haru-Kay/LeagueDatamines

Commit:
9245fd616059c6c658d1faa1029f0e18ea179154

Commit label:
LIVE 26.16 (#17)

Target project static patch:

Data Dragon 16.16.1

game-file/datamine patch 16.16 / Riot 26.16

Per champion, use the pinned files:

champions/<slug>/BaseStats.json

champions/<slug>/Spells.json

Do NOT use:

a moving master / latest source;

previous-patch fallback;

current/latest semantics if the exact pinned source is unavailable.

If the exact source cannot be obtained, preserve an explicit source-unavailable status and return REVIEW_REQUIRED.

Provenance must clearly say that this is a community datamine/export of Riot game files, not a Riot Developer Portal endpoint.

C - Primary Q/W/E/R mapping

Use CharacterRecords/Root from each champion's pinned BaseStats.json.

Audit and consume its primary spell path list (spells) as the source for the four champion ability slots in order:

Q

W

E

R

Cross-check the companion spellNames list when exposed.

For each expected primary path:

prefer an exact key match in Spells.json;

if needed, allow an exact objectPath equality match;

never use fuzzy semantic/name guessing to force a link.

Explicit mapping statuses must include at least:

EXACT_PRIMARY_SPELL_PATH

EXACT_OBJECT_PATH_MATCH

PRIMARY_SPELL_OBJECT_NOT_FOUND

PRIMARY_SPELL_PATH_AMBIGUOUS

The expected frozen project baseline is:

173 champions;

4 primary slots per champion;

692 primary Q/W/E/R slots.

A slot mapping failure is a real review item.

D - Extract raw spell calculation source without executing it

Create:

knowledge/champion_spell_source.py

For every mapped primary spell preserve, when exposed:

champion ID / name;

slot Q/W/E/R;

exact internal spell path;

ObjectName;

mScriptName;

objectPath;

pinned repository / commit / patch provenance;

raw DataValues;

raw mSpellCalculations;

raw calculation names/keys;

every nested ~class calculation-node type;

calculation node paths inside the raw graph;

field names present on each calculation node;

unknown or hashed fields rather than deleting them.

The layer must never convert a raw formula graph into damage merely because some fields look interpretable.

Useful factual statuses should distinguish at least:

CALCULATIONS_EXPOSED

NO_CALCULATIONS_EXPOSED

MALFORMED_CALCULATION_GRAPH

UNINTERPRETED_CALCULATION_CLASS

NO_CALCULATIONS_EXPOSED is allowed and is not automatically a bug: some primary abilities may have calculations elsewhere or may not expose a direct calculation block in this source.

Unknown calculation classes are also allowed in Phase 2F if their raw payload and class are preserved audibly.

Do not optimize formula coverage numbers.

E - Calculation graph inventory

Recursively inventory the exact calculation graph structure.

For every node under mSpellCalculations, preserve:

graph path;

~class when present;

raw node payload;

child/subpart structure;

named data-value references;

stat references/coefficient fields when present;

unknown fields.

The full audit must report:

total primary slots;

mapped primary slots;

slots exposing calculations;

slots without calculations;

total calculation records;

total calculation graph nodes;

unique ~class values;

count per calculation class;

unknown/uninterpreted calculation classes;

malformed calculation graphs;

raw DataValues count;

duplicate/ambiguous primary paths;

exact source failures.

Phase 2F is successful when the graph is losslessly catalogued and auditable, not when every class is executable.

F - Frozen Champion Knowledge cross-check

Consume frozen Champion Knowledge Phase 2B1-C without editing it.

Validate:

champion_knowledge_phase2b1_c_v1 is still the consumed version;

Data Dragon remains 16.16.1 / fr_FR;

173 champions are present;

each champion still has four Q/W/E/R Data Dragon spell records;

total frozen Data Dragon primary spell count remains 692.

Link Phase 2F source records to the frozen Champion Knowledge champion + slot context.

Do not copy datamine formula data back into champion_knowledge.py.

Do not change the frozen FORMULA_INCOMPLETE contract there.

G - Synthetic checks

Create:

knowledge/champion_spell_source_synthetic_checks.py

Use deterministic no-network fixtures.

Cover at least:

exact BaseStats Q/W/E/R order mapping;

exact Spells.json key match;

exact objectPath fallback;

missing primary spell object remains unresolved;

ambiguous exact objectPath remains explicit;

DataValues preservation;

multiple mSpellCalculations preservation;

recursive nested calculation-node class inventory;

unknown calculation class preserved as raw/uninterpreted;

hashed/unknown fields preserved;

calculation-free spell returns NO_CALCULATIONS_EXPOSED;

no previous/latest patch fallback exists.

H - Precision checks

Create:

knowledge/champion_spell_source_precision_checks.py

Use focused fixtures modeled on real Riot game-file structures observed in the pinned datamine.

At minimum verify:

NamedDataValueCalculationPart source structure is preserved;

a stat/coefficient calculation node remains structured raw evidence without being executed;

nested/subpart graphs retain all children;

zero numeric values are not mistaken for missing values;

formula names/keys are not normalized away;

slot Q/W/E/R identity comes from BaseStats order, not guessed from display text;

exact patch/commit provenance is attached to every resolved spell source record;

an uninterpreted class never becomes an executable result.

I - Full real audit

Create:

knowledge/champion_spell_source_full_audit.py

Run against the real pinned LIVE 26.16 source.

Minimum report:

spell source version;

frozen Champion Knowledge version;

Data Dragon version / locale;

pinned LeagueDatamines repository;

pinned commit;

target patch;

champions expected/resolved;

primary slots expected/resolved;

exact key vs exact objectPath mapping counts;

missing/ambiguous primary slots;

slots with/without calculations;

calculation record count;

calculation graph node count;

unique calculation classes + counts;

uninterpreted class count;

DataValues count;

malformed graph count;

source failures;

blocking issues;

review items;

STATUS.

Do not fabricate a target number for calculation-bearing spells/classes before the real audit runs.

Expected hard invariants:

173 champions;

692 primary Q/W/E/R slots;

exact pinned source only;

no silent fuzzy spell mapping;

no malformed graph silently ignored;

0 modifications to frozen production layers.

If exact source retrieval or primary slot mapping is incomplete, return REVIEW_REQUIRED rather than forcing PASS.

J - main.py development harness

Switch the current development harness to Phase 2F only.

Run:

py_compile of Phase 2F files;

synthetic checks;

precision checks;

real full source audit;

FROZEN guard.

The FROZEN guard must include all previously frozen Phase 2D and Phase 2E files.

Do not print all older analyzer reports.

K - Frozen boundaries

Do NOT modify production logic in:

Death Analyzer v11;

Jungle Tempo / Pathing v17;

Objective Analyzer v20;

Recall / Reset Analyzer v21;

Build / Itemization Analyzer v22 Phase 1;

Item Knowledge Phase 2A;

Champion Knowledge Phase 2B1;

Rune Knowledge Phase 2C1-B;

Level-Resolved Champion Stats Phase 2D v4;

Combat Resistance / Penetration Rules Phase 2E v1.

If a genuine compatibility requirement appears, stop and return REVIEW_REQUIRED before changing the frozen layer.

L - Explicitly out of scope

Do NOT start in Phase 2F:

evaluation/execution of champion spell formulas;

actual spell damage numbers;

AP / AD scaling evaluation;

item stat aggregation into a combat state;

rune effect execution;

stat shard hardcoding;

crit rules;

shields;

damage amplification/reduction effects;

on-hit ordering;

combos;

Burst / TTK;

composition analysis;

build/rune recommendations;

ML.

The next phase after project review may define an evaluator for a validated subset of calculation classes, but Phase 2F must remain a factual source catalog.

M - Documentation / reporting

After implementation and tests:

Update:

PROJECT_STATE.md;

LAST_RUN.md;

TODO.md -> COMPLETED / REVIEW_REQUIRED as appropriate.

Update DECISIONS.md only if a durable source/mapping decision had to be made beyond this task definition.

LAST_RUN must report the real source audit counts and limitations.

Do not declare Phase 2F FROZEN yourself.

Finish with:

PASS if technical execution and audit are clean, followed by REVIEW_REQUIRED for project freeze decision if that is the project convention; or

REVIEW_REQUIRED with concrete unresolved cases.

ChatGPT/project review decides whether Phase 2F freezes.

N - Git

Before commit:

inspect git status;

inspect git diff;

run git diff --check;

verify no .env, DB, logs, cache, credentials, or temporary download files are staged.

After a clean implementation and real audit, commit and push.

Suggested commit:

Build champion spell calculation source phase 2F

Completion status

PASS - Technical implementation and real pinned-source audit completed on 2026-08-22.

REVIEW_REQUIRED - Project review must decide whether Phase 2F becomes FROZEN.

Validated technical baseline:

- Version: `champion_spell_source_phase2f_v1`.
- Frozen Champion Knowledge context: `champion_knowledge_phase2b1_c_v1`, Data Dragon 16.16.1, `fr_FR`.
- Exact pinned source: `Haru-Kay/LeagueDatamines` commit `9245fd616059c6c658d1faa1029f0e18ea179154` (`LIVE 26.16 (#17)`).
- 173/173 champions resolved; 692/692 primary Q/W/E/R slots resolved.
- Mapping: 692 exact primary-path keys, 0 objectPath fallbacks, 0 missing/ambiguous slots.
- 631 slots expose calculations; 61 expose no calculation block.
- 1,443 raw calculation records, 4,687 graph nodes, 25 calculation classes, 5,063 raw DataValues.
- 0 malformed graphs, 0 source failures, 0 blocking issues, 0 technical review items.
- Synthetic checks: PASS 8/8. Precision checks: PASS 3/3. `python main.py`: PASS.

Phase 2F remains a raw source/structure catalog only. No spell formula, stat, or damage result is executed.
