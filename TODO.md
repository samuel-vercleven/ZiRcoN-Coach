# ZiRcoN Coach — TODO Phase 2H
## Champion Spell Stat Reference Semantics Foundation

### Model recommendation
Codex: GPT-5.6 Sol
Reasoning: HIGH

---

# 0. Mission

Build Phase 2H as a NEW, provenance-first semantic layer for champion spell stat references.

The objective is to determine, only when defensible:

- what each raw `mStat` ID means;
- what each raw `mStatFormula` value means;
- who owns the referenced stat when that can be proven;
- how a validated `(mStat, mStatFormula, owner)` combination maps to an existing frozen combat-snapshot field.

The objective is NOT to increase formula or damage coverage by guessing.

If a mapping cannot be proven, it must remain `UNKNOWN` / `UNRESOLVED`.

Phase 2G v2 is FROZEN.

Do not modify any frozen Phase 2G production or validation file.

Do not start Phase 2I.

---

# 1. Current frozen baseline

Repository:
`samuel-vercleven/ZiRcoN-Coach`

Current remote baseline:
`a1daaf80ba03ecaa879a597e517f1a9b9599ea07`

Commit:
`Freeze executable combat formula foundation phase 2G`

Accepted frozen inputs:

- Item Knowledge Phase 2A
- Champion Knowledge Phase 2B1
- Rune Knowledge Phase 2C1-B
- Level Stats Phase 2D v4
- Combat Resistance Phase 2E v1
- Champion Spell Source Phase 2F v1
- Executable Combat Formula Foundation Phase 2G v2

Important Phase 2G stat baseline:

- 173 champions
- 692 primary Q/W/E/R slots
- 1,443 raw calculations
- 5,318 graph nodes
- 25 calculation classes
- 885 stat-reference occurrences
- 16 distinct raw `mStat` IDs
- 0 mapped
- 16 unresolved

Frozen evaluator baseline:

- 13 `RESOLVED`
- 720 `PARTIALLY_RESOLVED`
- 493 `UNSUPPORTED_SIGNATURE`
- 217 `UNSUPPORTED_CLASS`

Do not modify these frozen counts by changing Phase 2G.

---

# 2. Mandatory startup

Before coding:

Read completely:

1. `AGENTS.md`
2. `PROJECT_STATE.md`
3. `TODO.md`
4. `DECISIONS.md`
5. `LAST_RUN.md`
6. `main.py`

Then inspect read-only:

- `knowledge/champion_spell_source.py`
- `knowledge/champion_spell_source_full_audit.py`
- `knowledge/champion_spell_formula_taxonomy.py`
- `knowledge/champion_spell_formula_evaluator.py`
- `knowledge/champion_spell_formula_evaluator_full_audit.py`
- `knowledge/champion_spell_stat_reference.py`
- `knowledge/champion_spell_stat_reference_full_audit.py`
- `knowledge/combat_stat_snapshot.py`
- `knowledge/combat_formula_foundation_full_audit.py`
- `knowledge/champion_level_stats.py`
- `knowledge/champion_knowledge.py`

Search the repository for:

- `mStat`
- `mStatFormula`
- `stat_references`
- `VALIDATED_STAT_REFERENCES`
- `resolve_stat_reference`
- `UNRESOLVED_STAT_REFERENCE`
- `STAT_OWNER_UNRESOLVED`

Also inspect immediately:

```text
git status
git diff
git log --oneline --decorate -15
git log origin/main..HEAD --oneline
If Phase 2H work already exists locally, reuse and review it.

Do not restart from zero unnecessarily.

3. Frozen boundaries

Do NOT modify any frozen production/validation file from Phase 2A through Phase 2G.

In particular, do NOT modify:

knowledge/champion_spell_stat_reference.py
knowledge/champion_spell_formula_evaluator.py
knowledge/combat_stat_snapshot.py
knowledge/combat_formula_foundation_full_audit.py

Phase 2H must live in new files.

If a frozen change is genuinely required:

stop that branch;
mark REVIEW_REQUIRED;
continue all independent safe work.
4. Exact source baseline

Primary exact game-structure source:

Repository:
Haru-Kay/LeagueDatamines

Pinned commit:
9245fd616059c6c658d1faa1029f0e18ea179154

Label:
LIVE 26.16 (#17)

Target:

Riot patch 26.16
Data Dragon 16.16.1
locale fr_FR

This source is a community datamine/export of Riot game files.

Do not describe it as Riot Developer API data.

Use the exact pinned source for current-patch inventory and structural evidence.

5. Research source hierarchy

Use sources in this order:

Tier 1

Exact pinned 26.16 game-file data.

Tier 2

Riot official documentation when it explicitly defines a mechanic.

Tier 3

Technical reverse-engineering/meta sources, preferably immutable commits:

LeagueToolkit/lol-meta-classes
moonshadow565/calcrev
CommunityDragon / CDTB
HextechDocs
Tier 4

Independent cross-validation against exact champion formulas/documented ratios.

Tier 5

Unresolved.

A field type such as UInt8 proves representation, not enum semantics.

Do not infer enum meaning from:

frequency;
coefficient magnitude;
champion archetype;
damage type;
calculation key text alone.
6. Existing community hypothesis to verify

Historical reverse-engineering documentation has described mStatFormula as:

0 = Base
1 = Bonus
2 = Total

Treat this as a hypothesis only.

Do not make it execution-eligible until it is cross-validated against the pinned 26.16 dataset.

Audit every actual mStatFormula value first.

Likewise, do not import an old mStat enum table blindly.

Validate current 26.16 independently.

7. New Phase 2H files

Create a new layer, for example:

knowledge/champion_spell_stat_semantics.py
knowledge/champion_spell_stat_semantics_sources.py
knowledge/champion_spell_stat_semantics_synthetic_checks.py
knowledge/champion_spell_stat_semantics_precision_checks.py
knowledge/champion_spell_stat_semantics_full_audit.py

Optional helper:

knowledge/champion_spell_stat_semantics_research_audit.py

Version:

champion_spell_stat_semantics_phase2h_v1

Do not add Phase 2H files to FROZEN_FILES yet.

8. Checkpoint A — exhaustive real inventory

Inventory every one of the 885 stat-reference occurrences.

For every occurrence preserve:

champion ID;
champion name if available;
slot;
source spell path;
calculation key;
graph path;
calculation class;
raw mStat;
raw mStatFormula;
all sibling fields;
coefficient/value fields;
DataValue reference if present;
parent/root calculation;
tooltip/component-local linkage if available;
Phase 2F source version;
pinned source commit.

Group by:

mStat
mStatFormula
(mStat, mStatFormula)
class
champion
slot

Hard current-baseline invariants:

total occurrences = 885
distinct raw mStat IDs = 16

Do not pre-hardcode the actual 16 numeric IDs.

Discover and report them from the real source.

If these invariants differ:

REVIEW_REQUIRED

9. Checkpoint B — mStatFormula semantics

Build explicit semantic records for every raw mStatFormula.

Semantic vocabulary:

BASE_STAT
BONUS_STAT
TOTAL_STAT
STAT_FORMULA_UNRESOLVED

Status vocabulary:

VALIDATED
STRONGLY_SUPPORTED
AMBIGUOUS
CONTRADICTED
UNRESOLVED

Each record must contain:

raw value;
semantic meaning;
status;
confidence/evidence tier;
evidence;
contradictions;
provenance;
representative real examples;
execution_eligible.

Rules:

only VALIDATED can be execution-eligible;
enum value 0 is legitimate and must never be confused with missing;
do not assume only values 0/1/2 exist before auditing.
10. Checkpoint C — mStat semantics

Prefer two-dimensional semantics:

mStat -> stat family

plus:

mStatFormula -> base/bonus/total

Example only:

ATTACK_DAMAGE + TOTAL_STAT

rather than encoding TOTAL_ATTACK_DAMAGE directly into raw mStat if the game structure is actually separated.

Candidate canonical stat families may include:

ATTACK_DAMAGE
ABILITY_POWER
HEALTH
ARMOR
MAGIC_RESISTANCE
ATTACK_SPEED
MOVE_SPEED
MANA
other exact proven stats

Do not create a mapping merely because a candidate sounds plausible.

A raw mStat ID can be VALIDATED only with strong evidence.

Preferred evidence pattern:

exact 26.16 occurrences;
several unrelated champions/spells where available;
independently documented exact scaling;
structural consistency;
no credible contradictory occurrence;
explicit provenance.

If evidence is weak:

leave it unresolved.

No minimum mapping percentage.

11. Checkpoint D — contradiction search

For every proposed mStat mapping:

scan all occurrences of that raw ID.

Actively search for a counterexample.

Example:

if candidate raw ID X = ATTACK_DAMAGE,
look for any strongly evidenced spell using X that clearly scales with:

AP;
HP;
armor;
MR;
movement speed;
another incompatible stat.

If contradiction exists:

preserve champion;
slot;
calculation key;
graph path;
source evidence;

and downgrade to:

CONTRADICTED
or
AMBIGUOUS.

Contradicted or ambiguous IDs must never be execution-eligible.

12. Checkpoint E — owner/source semantics

Audit who owns the referenced stat.

Do not assume every stat reference uses caster stats.

Possible owner statuses:

OWNER_VALIDATED_CASTER
OWNER_VALIDATED_TARGET
OWNER_VALIDATED_SOURCE_LEVEL
OWNER_CONTEXT_DEPENDENT
OWNER_UNRESOLVED

Owner semantics must remain separate from mStatFormula.

Do not infer owner merely because most ratios in League use the caster.

If owner cannot be proven:

leave unresolved.

13. Checkpoint F — class-specific audit

Focus on stat-related classes, especially:

StatByCoefficientCalculationPart
StatByNamedDataValueCalculationPart
StatBySubPartCalculationPart

For each class audit:

exact structural signatures;
raw mStat values;
raw mStatFormula values;
coefficients;
DataValues;
nested subparts;
owner evidence;
representative real examples.

Do NOT execute these classes in Phase 2H.

Phase 2H is semantic/source only.

14. Checkpoint G — AbilityResource branch

If AbilityResourceByCoefficientCalculationPart appears:

inventory it separately.

Do not confuse:

mAbilityResource

with:

mStat

If resource enum semantics are not fully established:

use a research-only status such as:

RESOURCE_ENUM_RESEARCH_ONLY

Do not let this branch block completion of the primary 16 mStat IDs.

15. Structured mapping records

Do not store only bare mappings.

Example stat record:

{
    "raw_stat_id": 2,
    "semantic_stat": "ATTACK_DAMAGE",
    "status": "VALIDATED",
    "execution_eligible": True,
    "evidence": [...],
    "contradictions": [],
    "provenance": {...},
}

Example formula record:

{
    "raw_formula_id": 2,
    "semantic_formula": "TOTAL_STAT",
    "status": "VALIDATED",
    "execution_eligible": True,
    "evidence": [...],
    "contradictions": [],
    "provenance": {...},
}

Expose convenience functions only from validated records:

get_validated_stat_mapping()
get_validated_stat_formula_mapping()

Never leak:

strongly supported;
ambiguous;
contradicted;
unresolved

into execution-ready output.

16. Snapshot-reference composition

Create a new deterministic function that combines:

raw mStat
raw mStatFormula
owner

into an existing frozen Phase 2G combat snapshot field only if every semantic dependency is validated.

Statuses:

SEMANTIC_REFERENCE_RESOLVED
STAT_ID_UNRESOLVED
STAT_FORMULA_UNRESOLVED
STAT_OWNER_UNRESOLVED
SNAPSHOT_FIELD_UNAVAILABLE
SEMANTIC_COMBINATION_UNSUPPORTED

Possible examples only if proven:

ATTACK_DAMAGE + BASE_STAT -> attack_damage_native
ATTACK_DAMAGE + BONUS_STAT -> attack_damage_bonus
ATTACK_DAMAGE + TOTAL_STAT -> attack_damage_total

Be careful:

"native at level" and Riot's internal "base" may not be identical in every mechanic.

Do not force equivalence.

Health must be treated carefully:

max HP
bonus HP
current HP
missing HP

are different semantics.

Do not rebuild attack-speed arithmetic.

Phase 2D remains frozen.

17. Critical execution boundary

Do NOT modify frozen Phase 2G evaluator.

Do NOT make stat formula classes executable yet.

Specifically do NOT implement stat execution inside:

champion_spell_formula_evaluator.py
champion_spell_formula_runtime.py

Phase 2I will later consume:

frozen Phase 2G formula graph/evaluator contracts;
frozen Phase 2G combat snapshots;
Phase 2H validated stat semantics;

to create a new stat-scaling execution layer.

Do not start that phase now.

18. Synthetic tests

At minimum test:

validated stat mapping;
unresolved stat ID;
validated mStatFormula;
unknown mStatFormula;
owner unresolved blocks complete semantic reference;
base/bonus/total stay distinct;
raw mStat = 0 is not missing;
raw mStatFormula = 0 is not missing;
no fuzzy matching;
ambiguous mapping excluded from execution map;
contradicted mapping excluded;
strongly-supported-only mapping excluded;
validated snapshot-field composition;
missing snapshot field explicit;
provenance preserved;
weak single evidence cannot become VALIDATED;
contradiction downgrades a mapping;
magic damage does not imply AP;
physical damage does not imply AD;
coefficient size does not identify stat.
19. Precision tests

Use minimized exact pinned 26.16 real structures.

For every raw stat ID declared VALIDATED:

at least one real-source precision fixture;
several unrelated champion examples for high-frequency IDs where practical.

Fixture metadata must record:

champion;
slot;
calculation key;
graph path;
raw mStat;
raw mStatFormula;
independently expected semantic;
source/provenance.

Do not derive expected semantic by calling production code.

No circular validation.

20. External source registry

Create:

knowledge/champion_spell_stat_semantics_sources.py

For every source used, record:

source name;
repository/site;
exact commit/URL if available;
source tier;
what fact it supports;
limitations.

Investigate:

Haru-Kay/LeagueDatamines
LeagueToolkit/lol-meta-classes
moonshadow565/calcrev
CommunityDragon/CDTB
HextechDocs

Historical evidence may support a hypothesis but exact 26.16 evidence remains primary.

21. Cross-patch stability

Where useful, compare candidate enum semantics against older/newer technical sources.

Classify:

STABLE_ACROSS_CHECKED_VERSIONS
CHANGED_ACROSS_VERSIONS
CROSS_PATCH_UNCERTAIN

Do not use a different patch's mapping as a silent fallback for 26.16.

22. Hash/unknown-field policy

If related fields are hashed:

preserve raw hash;
resolve only through known hash dictionaries or exact technical sources;
record provenance;
unresolved hashes stay unresolved.

No guessed hash name may enter execution semantics.

23. Full audit

Create:

knowledge/champion_spell_stat_semantics_full_audit.py

Report:

Source
Phase 2H version
Phase 2F source version
Phase 2G frozen version
exact LeagueDatamines commit
Data Dragon version
locale
Inventory
total occurrences
distinct mStat IDs
exact ID list
count per ID
raw mStatFormula values
count per formula value
(mStat, mStatFormula) matrix
Stat mappings
VALIDATED
STRONGLY_SUPPORTED
AMBIGUOUS
CONTRADICTED
UNRESOLVED
execution-eligible IDs
validated occurrence coverage
Formula mappings
validated formula IDs
unresolved formula IDs
contradicted formula IDs
Owner semantics
caster validated
target validated
source-level validated
context-dependent
unresolved
Snapshot composition
resolved canonical fields
unsupported combinations
unavailable snapshot fields
Safety invariants
key-name-only mappings admitted = 0
ambiguous mappings in execution map = 0
contradicted mappings in execution map = 0
strongly-supported-only mappings in execution map = 0
unproven owner assumptions = 0
frozen file modifications = 0
Result
blocking issues
review items
status

No mapping-coverage threshold.

A low-coverage but defensible result can PASS.

24. main.py development harness

Phase 2H becomes the only active development phase.

Keep all previous frozen guards.

Run:

py_compile Phase 2H files
Phase 2H synthetic checks
Phase 2H precision checks
Phase 2H research/inventory audit
Phase 2H full audit
FROZEN guard

Do not print all old Phase 2G reports unnecessarily.

Do not add Phase 2H files to frozen list yet.

25. Documentation

Update:

PROJECT_STATE.md
LAST_RUN.md
TODO.md

Update DECISIONS.md only for durable source/methodology decisions.

Do not declare Phase 2H FROZEN.

Final state should be:

PASS / REVIEW_REQUIRED FOR FREEZE

or

REVIEW_REQUIRED

with exact blockers.

26. LAST_RUN required content

Record:

exact Phase 2H version;
commits;
exact external source URLs/commits;
runtime;
total stat occurrences;
distinct raw stat IDs;
actual raw stat ID list;
actual mStatFormula values;
validated stat mappings;
strongly supported;
ambiguous;
contradicted;
unresolved;
validated occurrence coverage;
mStatFormula coverage;
owner coverage;
snapshot composition coverage;
synthetic count;
precision count;
full audit;
FROZEN guard;
git diff --check;
remaining limitations.

Do not report guessed AD/AP mappings as facts.

27. Git strategy

Before commits:

git status
git diff
git diff --check

Never stage:

.env
Riot API keys
DB files
logs
.cache
downloaded game archives
credentials

Suggested commits:

Inventory champion spell stat references phase 2H
Validate champion spell stat semantics phase 2H
Audit champion spell stat semantics phase 2H

Use fewer commits if cleaner.

Push to:

origin/main

No force push.

At the end verify:

git status
git log -5 --oneline
git rev-parse HEAD
git rev-parse origin/main

HEAD and origin/main must match after successful push.

28. Explicitly out of scope

Do NOT implement:

stat-based formula execution;
new damage execution;
item passive/active execution;
rune execution;
stat shards;
buffs;
conditions;
tick simulation;
transformations;
combo engine;
Burst/TTK;
build recommendations;
ML;
UI;
Phase 2I.
29. Completion behavior

Routine coding/test problems:

fix autonomously.

If one stat ID remains unresolved:

continue.

If owner semantics remain largely unresolved:

continue and report honestly.

If a source contradiction exists:

preserve it and downgrade the mapping.

Do not stop the whole phase because coverage is incomplete.

Stop only for a genuine methodology/frozen-boundary blocker.

30. Final Codex response

Report concisely:

commit SHAs;
files created/modified;
actual 16 raw mStat IDs;
actual mStatFormula values;
VALIDATED stat mappings;
STRONGLY_SUPPORTED mappings;
AMBIGUOUS mappings;
CONTRADICTED mappings;
UNRESOLVED mappings;
execution-eligible occurrence coverage;
owner semantics coverage;
tests;
audits;
FROZEN guard;
git diff check;
push status;
HEAD/origin SHA;
remaining blockers.

Do not choose or start Phase 2I.

Project review decides what comes next.

Final rule

This phase is reverse engineering with a strict evidence burden.

Do not optimize for how many IDs can be mapped.

Optimize for how many mappings can be defended.

When evidence ends:

UNKNOWN.

A correct unresolved enum is better than a plausible wrong stat.