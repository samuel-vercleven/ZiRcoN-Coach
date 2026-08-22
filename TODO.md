ZiRcoN Coach - MASSIVE SOL TODO

Model recommendation

Codex model: GPT-5.6 Sol
Reasoning: HIGH

This task is intentionally large.

The goal is to use one strong Sol session for a coherent multi-checkpoint combat-formula milestone instead of repeatedly reloading the repository context for many tiny tasks.

Do NOT reduce the task to a small prototype unless a genuine methodology blocker makes the later checkpoints impossible.

Do NOT rush by inventing missing semantics.

The correct behavior is:

solve everything that can be established cleanly;

keep unsupported cases explicit;

continue through later checkpoints whenever unsupported cases do not invalidate them;

create technical checkpoint commits as milestones become clean;

stop only when a frozen-layer change or an unresolvable methodology decision is genuinely required.

0. Mandatory reading before any code change

Read in this order:

AGENTS.md

PROJECT_STATE.md

TODO.md

DECISIONS.md

LAST_RUN.md

main.py

Then inspect these frozen foundations in read-only mode:

knowledge/item_knowledge.py

knowledge/champion_knowledge.py

knowledge/rune_knowledge.py

knowledge/champion_level_stats.py

knowledge/champion_attack_speed_source.py

knowledge/combat_resistance_rules.py

Then inspect the completed Phase 2F implementation:

knowledge/champion_spell_source.py

knowledge/champion_spell_source_synthetic_checks.py

knowledge/champion_spell_source_precision_checks.py

knowledge/champion_spell_source_full_audit.py

Search all repository usages before changing any shared interface.

Do not code from assumptions.

1. Existing frozen project baseline

Treat these modules/layers as FROZEN and read-only unless this TODO explicitly authorizes only documentation/guard changes:

Death Analyzer v11

Jungle Tempo / Pathing Analyzer v17

Objective Analyzer v20

Recall / Reset Analyzer v21

Build / Itemization Analyzer v22 Phase 1

Item Knowledge Phase 2A

Champion Knowledge Phase 2B1-C

Rune Knowledge Phase 2C1-B

Level-Resolved Champion Stat Formula Foundation Phase 2D v4

Combat Resistance / Penetration Rules Foundation Phase 2E v1

Important frozen versions already accepted by project review:

Item Knowledge: item_knowledge_phase2a_c_v1

Champion Knowledge: champion_knowledge_phase2b1_c_v1

Rune Knowledge: rune_knowledge_phase2c1_b_v3

Level Stats: champion_level_stats_phase2d_v4

Combat Resistance: combat_resistance_phase2e_v1

Do not retune, clean up, refactor, or reinterpret them while doing this task.

If a new layer needs information that a frozen layer does not expose:

first determine whether the information can live in the new layer;

prefer an adapter/new module;

do not modify the frozen layer for convenience;

if a true compatibility change to frozen production code is unavoidable, stop that branch of work and mark REVIEW_REQUIRED.

2. Phase 2F review decision: accept and freeze first

Project review now accepts the completed Champion Spell Calculation Source Foundation Phase 2F as freeze-ready.

Validated baseline from the latest real run:

source version: champion_spell_source_phase2f_v1

pinned repository: Haru-Kay/LeagueDatamines

pinned commit: 9245fd616059c6c658d1faa1029f0e18ea179154

commit label: LIVE 26.16 (#17)

target static patch: Data Dragon 16.16.1 / Riot 26.16

Champions: 173/173

primary Q/W/E/R slots: 692/692

exact primary key mappings: 692

objectPath fallbacks: 0

missing/ambiguous mappings: 0

source failures: 0

slots with calculation graph data: 631

slots without calculation graph data: 61

raw calculation records: 1,443

raw DataValues: 5,063

dictionary graph nodes: 5,318

dictionary nodes with ~class: 4,687

dictionary nodes without ~class: 631

unique non-null calculation classes: 25

malformed graphs: 0

synthetic checks: PASS 10/10

precision checks: PASS 4/4

full real audit: PASS

FROZEN guard: PASS

git diff --check: PASS

2.1 Freeze Phase 2F

Checkpoint status: COMPLETED - Phase 2F v1 frozen, guard expanded, real harness PASS.

Before beginning new production modules:

Update PROJECT_STATE.md to mark Phase 2F v1 FROZEN.

Add a durable freeze decision to DECISIONS.md.

Update AGENTS.md frozen-layer list.

Add the four Phase 2F production/validation files to main.py FROZEN_FILES:

knowledge/champion_spell_source.py

knowledge/champion_spell_source_synthetic_checks.py

knowledge/champion_spell_source_precision_checks.py

knowledge/champion_spell_source_full_audit.py

Do NOT change Phase 2F production behavior while freezing it.

Run the existing Phase 2F harness after the guard change.

Commit this checkpoint separately.

Suggested checkpoint commit:

Freeze champion spell calculation source phase 2F

After this checkpoint, Phase 2F is read-only for the rest of the mission.

3. New milestone

Phase 2G - Executable Combat Formula Foundation

This is a large multi-checkpoint milestone.

The purpose is to move from:

raw, pinned spell-calculation graphs

to:

conservatively executable generic calculation graphs + explicit static combat state + an end-to-end formula execution API

without pretending that every League mechanic is already understood.

The core design rule is:

unsupported is a valid result; fabricated certainty is not.

This phase must NOT silently turn partial calculations into exact damage.

4. Source/provenance hierarchy

Use this hierarchy whenever formula semantics must be established.

Tier 1 - exact pinned game-file source

Primary structural/data source:

Repository:
Haru-Kay/LeagueDatamines

Commit:
9245fd616059c6c658d1faa1029f0e18ea179154

Patch:
LIVE 26.16 (#17)

This is a community datamine/export of Riot game files, not a Riot Developer Portal endpoint.

Never call it official Riot API data.

Tier 2 - Riot official documentation/patch notes

Use Riot official material when it explicitly defines a mechanic.

Record exact URL/title/patch provenance.

Tier 3 - established community technical documentation

League Wiki / equivalent may be used for generic formulas when Riot does not publish executable equations.

Label this provenance explicitly as community-documented.

Tier 4 - unresolved

If semantics are not established by evidence:

do not infer from a class name alone;

do not guess from one champion;

do not derive an enum mapping by wishful pattern matching;

mark unsupported/unresolved;

keep raw evidence.

Never use moving latest data to fill a pinned 16.16 gap.

5. Global implementation rules

The new execution system must be:

deterministic;

patch-pinned;

UI-agnostic;

auditable;

typed where practical;

recursive where required;

cycle-safe;

explicit about missing context;

explicit about source/provenance;

explicit about unsupported semantics;

independent from Win/Loss analyzers;

independent from recommendations;

independent from ML.

Every successful numeric result must be traceable to:

source spell/champion/slot;

calculation key;

source commit;

input context;

evaluated calculation nodes;

unresolved branches if any;

final status.

A caller must be able to inspect how the number was obtained.

6. Checkpoint A - Full calculation-class taxonomy

Checkpoint status: COMPLETED - dynamic 25-class / 109-signature real audit PASS.

Create a dedicated taxonomy/audit layer.

Suggested files:

knowledge/champion_spell_formula_taxonomy.py

knowledge/champion_spell_formula_taxonomy_synthetic_checks.py

knowledge/champion_spell_formula_taxonomy_full_audit.py

6.1 Discover real classes dynamically

Consume frozen Phase 2F output.

Do not hardcode "25 classes" as a permanent universal truth.

For the pinned baseline, the audit should reproduce the actual observed set and counts.

For every non-null ~class observed under the 1,443 calculation records:

collect:

class name;

occurrence count;

champions using it;

spell slots using it;

calculation keys using it;

graph depths;

parent classes/fields;

all observed field names;

field-type distributions;

representative raw examples;

all distinct structural signatures;

whether class appears as root calculation, formula part, nested part, conditional part, etc.;

references to DataValues;

references to named calculations;

stat reference fields;

coefficient/multiplier fields;

level-dependent fields;

target/caster-dependent fields;

unknown hashed fields.

6.2 Classify semantics conservatively

Every class gets one of these statuses:

SEMANTICS_VALIDATED_EXECUTABLE

SEMANTICS_PARTIALLY_VALIDATED

CONTEXT_DEPENDENT_NOT_EXECUTABLE

STRUCTURAL_CONTAINER_ONLY

UNRESOLVED_CLASS_SEMANTICS

NON_NUMERIC_OR_NOT_RELEVANT

Do NOT label a class executable just because its name looks understandable.

For executable classes record:

exact semantic contract;

required inputs;

output type;

supported field shapes;

unsupported field shapes;

source provenance;

evidence examples.

6.3 Field-shape contract

A class may have several structural variants.

Do not make one implementation support all variants unless each is validated.

Represent supported signatures separately if needed.

Example:

Class X signature A -> supported
Class X signature B -> unsupported field combination

6.4 Coverage report

Audit must report:

observed class count;

occurrence count per class;

executable occurrences;

partially validated occurrences;

unresolved occurrences;

number of unique structural signatures;

unknown fields by class;

classes that require stat mapping;

classes that require caster level;

classes that require spell rank;

classes that require target state;

classes that reference other calculations;

classes that cannot yet be evaluated.

Do not optimize coverage by weakening classification.

Checkpoint A passes if taxonomy is accurate and all observed classes are accounted for, even if some remain unsupported.

Commit checkpoint A if clean.

Suggested commit:

Catalog champion spell calculation class semantics

7. Checkpoint B - Rank/value indexing foundation

Checkpoint status: COMPLETED - explicit pinned 0..6 and 1..6 contracts; full array audit PASS.

Do not blindly assume that every values-array uses the same indexing convention.

Create a generic source-value resolver.

Suggested file:

knowledge/champion_spell_value_resolver.py

Validation files:

knowledge/champion_spell_value_resolver_synthetic_checks.py

knowledge/champion_spell_value_resolver_precision_checks.py

knowledge/champion_spell_value_resolver_full_audit.py

7.1 Audit array shapes first

Across the pinned source, inventory arrays used in:

DataValues;

calculation parts;

cooldowns;

cost arrays where exposed;

any formula fields used by executable classes.

Record:

array lengths;

leading zero patterns;

repeated values;

spell max rank;

slot;

context.

Do not universalize values[rank] until shape rules are proven.

7.2 Explicit rank statuses

Use explicit results:

VALUE_RESOLVED

INVALID_SPELL_RANK

VALUE_SHAPE_UNSUPPORTED

RANK_INDEXING_UNRESOLVED

VALUE_MISSING

NON_NUMERIC_VALUE

Zero is a valid value.

Never confuse zero with missing.

7.3 Rank contract

The resolver must distinguish:

Q/W/E typical rank range;

R rank range;

rank 0 / unlearned where relevant;

arrays with sentinel element;

arrays that do not map directly to rank.

Do not infer spell max rank solely from slot if source exposes a more exact contract.

7.4 Tests

Include deterministic fixtures for:

leading sentinel zero;

legitimate rank-1 zero;

constant arrays;

malformed arrays;

short arrays;

overlong arrays;

rank 0;

invalid high rank;

exact preservation of floating-point values.

Commit checkpoint B if clean.

Suggested commit:

Add spell rank value resolution foundation

8. Checkpoint C - DataValue registry and named-reference resolver

Checkpoint status: COMPLETED - exact case-sensitive registry and 1,829-reference audit PASS.

Create a deterministic per-spell DataValue registry.

Suggested file:

knowledge/champion_spell_data_value_resolver.py

Responsibilities:

index raw DataValues without mutating Phase 2F data;

preserve original names/casing;

preserve duplicate-name situations explicitly;

resolve exact-name references;

do not fuzzy-match names;

resolve rank-dependent value only through checkpoint B;

expose raw + resolved form;

report ambiguity.

Required statuses:

DATA_VALUE_RESOLVED

DATA_VALUE_NOT_FOUND

DATA_VALUE_AMBIGUOUS

DATA_VALUE_SHAPE_UNSUPPORTED

DATA_VALUE_NON_NUMERIC

DATA_VALUE_RANK_UNRESOLVED

Audit:

number of exact DataValue references in the 5,318 graph nodes;

resolved exact references;

unresolved references;

duplicate DataValue names;

hashed names;

case-sensitive/case-variant collisions.

Do not silently normalize names for lookup.

Commit if clean.

Suggested commit:

Resolve pinned spell DataValue references

9. Checkpoint D - Stat-reference semantics

Checkpoint status: COMPLETED - 16 raw IDs inventoried; all remain explicitly unresolved because no mapping was proven.

Some executable formula nodes may reference internal stat identifiers such as mStat.

Create:

knowledge/champion_spell_stat_reference.py

knowledge/champion_spell_stat_reference_synthetic_checks.py

knowledge/champion_spell_stat_reference_full_audit.py

9.1 Never guess numeric stat enums

For every observed numeric/string stat reference:

inventory values;

inventory classes where used;

inventory surrounding fields;

search pinned game-file data and existing project sources for explicit mapping;

search Riot official documentation where applicable;

search established community technical documentation when Riot does not publish the mapping;

record provenance for each mapping.

If a numeric enum cannot be established confidently:

STAT_REFERENCE_UNRESOLVED

Do not map it because "2 probably means AP" from one example.

9.2 Desired semantic stat vocabulary

Map only proven references into a project vocabulary such as:

ABILITY_POWER

ATTACK_DAMAGE_TOTAL

ATTACK_DAMAGE_BONUS

ATTACK_DAMAGE_BASE

HEALTH_MAX

HEALTH_BONUS

HEALTH_CURRENT

HEALTH_MISSING

ARMOR

MAGIC_RESISTANCE

ATTACK_SPEED

MOVE_SPEED

other proven stats

This list is not permission to fabricate unsupported mappings.

9.3 Context ownership

Every stat reference must specify:

caster / source;

target;

unknown owner;

source-level;

spell rank dependent if relevant.

If ownership cannot be proven:

STAT_OWNER_UNRESOLVED

9.4 Audit

Report:

distinct raw stat IDs;

mapped stat IDs;

unresolved IDs;

occurrence coverage;

classes affected;

formulas blocked only by stat mapping.

Commit if clean.

Suggested commit:

Map validated champion spell stat references

10. Checkpoint E - Generic formula evaluation result model

Checkpoint status: COMPLETED - structured typed outcomes preserve children, provenance, context, and unresolved reasons.

Create a reusable evaluation result model.

Suggested file:

knowledge/combat_formula_types.py

Use dataclasses / typed records where practical.

Every node evaluation should produce a structured object with at least:

status;

numeric value if fully resolved;

raw class;

graph path;

calculation key;

dependencies;

required context;

provenance;

warnings;

unresolved reasons;

child results.

Core statuses:

RESOLVED

RESOLVED_WITH_WARNINGS

PARTIALLY_RESOLVED

UNSUPPORTED_CLASS

UNSUPPORTED_SIGNATURE

MISSING_CONTEXT

MISSING_DATA_VALUE

AMBIGUOUS_DATA_VALUE

UNRESOLVED_STAT_REFERENCE

UNRESOLVED_STAT_OWNER

INVALID_SPELL_RANK

NON_NUMERIC_RESULT

NAMED_CALCULATION_NOT_FOUND

NAMED_CALCULATION_AMBIGUOUS

CYCLE_DETECTED

MAX_RECURSION_DEPTH

MALFORMED_NODE

SOURCE_VERSION_MISMATCH

Do not use None alone to represent why evaluation failed.

11. Checkpoint F - Safe recursive formula evaluator

Checkpoint status: COMPLETED - 1,443-calculation real audit PASS with conservative partial/unsupported statuses.

Create:

knowledge/champion_spell_formula_evaluator.py

knowledge/champion_spell_formula_evaluator_synthetic_checks.py

knowledge/champion_spell_formula_evaluator_precision_checks.py

knowledge/champion_spell_formula_evaluator_full_audit.py

The evaluator consumes frozen Phase 2F graphs plus the taxonomy/value/stat foundations.

11.1 Evaluation architecture

Use a registry/dispatcher keyed by validated calculation class and supported structural signature.

Do not create one giant if/elif block if a clean registry pattern is possible.

Each handler must declare:

class;

supported signature;

required context;

input semantics;

output semantics;

provenance;

failure modes.

11.2 Recursion

Support recursive/nested formula graphs when validated.

Must include:

deterministic traversal;

child result preservation;

cycle detection;

named-calculation recursion guard;

max depth guard;

no global mutable evaluation state.

11.3 Named calculation references

If classes can reference another calculation by exact key:

exact lookup only;

preserve key casing;

detect missing key;

detect cycles;

no fuzzy matching.

11.4 Arithmetic

Implement only arithmetic explicitly required by validated classes.

Potential primitives may include:

constant;

sum;

product;

scalar coefficient;

DataValue;

stat coefficient;

min/max/clamp;

level interpolation;

named calculation reference;

conditional forms only if exact condition semantics are available.

Do not implement a primitive just because it seems likely.

11.5 Floating point

Do not round internally for convenience.

Use tolerances only in tests.

Preserve source precision.

11.6 Partial evaluation

If a parent formula has one unresolved child:

preserve resolved children;

return PARTIALLY_RESOLVED;

do not pretend the numeric partial sum is the full result.

An optional known_partial_value may be exposed but must never be called final.

11.7 Full real audit

Evaluate structural executability across all 1,443 raw calculation records using synthetic neutral contexts where context-independent.

For context-dependent formulas, report their required inputs rather than forcing values.

Report:

total calculations;

calculations structurally supported;

fully evaluable without combat context;

evaluable with standard caster context;

target-context dependent;

unsupported by class;

unsupported by signature;

blocked by stat mapping;

blocked by DataValue;

blocked by named refs;

cycles;

malformed;

partial;

formula coverage by champion and slot;

class-level coverage.

No target coverage percentage is a pass requirement.

Correct unresolved reasons are more important than a large number.

Commit checkpoint F if clean.

Suggested commit:

Build conservative champion spell formula evaluator

12. Checkpoint G - Static combat-stat snapshot foundation

Checkpoint status: COMPLETED - 4,844 real snapshots across 173 champions and discovered SR items PASS.

Create a generic combat-state layer that combines only factual static inputs.

Suggested files:

knowledge/combat_stat_snapshot.py

knowledge/combat_stat_snapshot_synthetic_checks.py

knowledge/combat_stat_snapshot_precision_checks.py

knowledge/combat_stat_snapshot_full_audit.py

Consume frozen:

Level Stats Phase 2D v4

Item Knowledge Phase 2A

Champion Knowledge Phase 2B1 only for identity/context where needed

Do not alter those frozen modules.

12.1 Snapshot input

A snapshot should be buildable from:

champion;

level;

list/multiset of item IDs;

optional explicit current-health value;

optional extra factual stat overrides supplied by caller;

explicit patch/version context.

12.2 Static stats

Resolve only stats whose static semantics are already factual.

Candidate output vocabulary:

base/native health at level;

total max health;

bonus health;

current health when supplied;

missing health when current health supplied;

base/native AD at level;

total AD;

bonus AD;

AP;

armor;

bonus armor;

MR;

bonus MR;

attack speed;

movement speed;

ability haste;

crit chance;

life steal;

lethality;

flat armor penetration;

percent armor penetration;

flat magic penetration;

percent magic penetration;

other normalized factual Item Knowledge stats.

Only include fields that can be supported accurately.

12.3 Item policy

Static unconditional item stats may contribute.

Do NOT execute:

item passive damage;

item active damage;

conditional stat passives;

stacking item passives;

temporary buffs;

proc systems;

transformations;

on-hit effects;

shields;

healing;

executes.

If Item Knowledge has a stat value parsed from description but provenance/reliability is not adequate for exact combat arithmetic, expose an unresolved/reliability status rather than silently using it.

12.4 Base vs bonus

Do not conflate:

native/base-at-level stat;

item bonus;

total stat.

Formula evaluation may need total AD vs bonus AD.

Keep those distinct.

12.5 Attack speed

Use frozen Phase 2D Attack Speed Ratio logic.

Do not recreate it.

If item attack-speed contribution can be applied unambiguously, apply it through a dedicated tested formula.

Special champions already handled by frozen foundation must remain consistent.

12.6 Level limits

Standard factual calculations use supported levels from Phase 2D.

Do not extrapolate native growth at unresolved Top quest levels 19-20.

Propagate the frozen unresolved status.

12.7 Rune policy

Do NOT invent rune shard meanings.

Do NOT execute conditional rune effects in this checkpoint.

If no validated numeric rune contribution is available, snapshot must say runes are not applied.

12.8 Audit

Real audit should build representative snapshots for all 173 champions at selected supported levels with:

no items;

representative AD item;

representative AP item;

representative armor item;

representative MR item;

representative health item;

representative attack-speed item where applicable.

Use actual purchasable SR item IDs discovered from frozen Item Knowledge, not hardcoded assumptions without validation.

Report failures and unresolved stats.

Commit if clean.

Suggested commit:

Build static combat stat snapshot foundation

13. Checkpoint H - Formula evaluation with real combat context

Checkpoint status: COMPLETED - caller-selected adapter and 1,443-calculation runtime audit PASS.

Integrate checkpoint F evaluator with checkpoint G combat snapshots.

Create an adapter such as:

knowledge/champion_spell_formula_runtime.py

Input:

source champion;

level;

spell slot;

spell rank;

optional items;

optional current health;

optional target snapshot;

calculation key.

Output:

exact source record;

formula key;

evaluated result;

dependencies;

context used;

source provenance;

unsupported reasons;

no semantic claim that the calculation is necessarily "damage".

13.1 Caller-selected calculation

The runtime must support:

evaluate_calculation(champion, slot, calculation_key, context)

This is the safest generic API.

The caller chooses the raw calculation key.

Do not auto-label it damage at this stage.

13.2 Bulk audit

For every calculation record in the pinned catalog:

determine whether its dependencies can be satisfied by a standard static caster snapshot;

evaluate where possible;

classify unresolved cases.

Use several representative spell ranks / champion levels as appropriate.

Do not evaluate invalid rank combinations.

Report per-class and per-champion coverage.

Commit if clean.

Suggested commit:

Connect spell formulas to static combat context

14. Checkpoint I - Damage-formula evidence classifier

Checkpoint status: COMPLETED - 692-spell semantic audit PASS; candidates and mixed/contextual types remain separate.

Only after generic formula execution works, build a SEPARATE conservative semantic classifier.

Suggested files:

knowledge/champion_spell_damage_evidence.py

knowledge/champion_spell_damage_evidence_synthetic_checks.py

knowledge/champion_spell_damage_evidence_full_audit.py

This layer answers:

"Is there enough evidence to treat a particular calculation key as a damage amount, and if yes, what damage type is supported?"

It must not guess.

14.1 Evidence sources

Possible evidence can include:

exact calculation key/name;

raw pinned spell metadata;

frozen Champion Knowledge semantic tags;

Data Dragon description/tooltip context;

Riot official documentation;

community documentation with explicit provenance.

No single generic word such as Damage is sufficient if context is ambiguous.

14.2 Statuses

At minimum:

DAMAGE_CALCULATION_HIGH_CONFIDENCE

DAMAGE_CALCULATION_MULTIPLE_CANDIDATES

DAMAGE_TYPE_PHYSICAL

DAMAGE_TYPE_MAGIC

DAMAGE_TYPE_TRUE

DAMAGE_TYPE_MULTIPLE_OR_CONTEXTUAL

DAMAGE_TYPE_UNRESOLVED

NOT_IDENTIFIED_AS_DAMAGE

DAMAGE_EVIDENCE_INSUFFICIENT

Do not collapse mixed-damage spells into one type.

14.3 Multiple components

A spell may have:

initial damage;

repeated ticks;

max-health damage;

detonation damage;

empowered form;

passive component;

multi-hit;

conditional bonus;

several calculation keys.

Do not force "one spell = one damage formula".

Represent damage components separately.

14.4 No intent guessing

Do not decide which condition triggers in a real game unless the required state is explicitly supplied.

A damage component can be "known formula, unresolved activation condition".

14.5 Full catalog audit

Report:

primary spells with zero damage candidate;

one high-confidence candidate;

multiple candidates;

unresolved damage type;

physical;

magic;

true;

mixed/contextual;

formulas whose arithmetic is executable;

formulas whose semantic damage identity is known but arithmetic is unsupported;

formulas executable but not safely classified as damage.

No coverage target.

Commit if clean.

Suggested commit:

Classify champion spell damage evidence conservatively

15. Checkpoint J - Damage component resolver

Checkpoint status: COMPLETED - 849 candidates audited; only fully supported arithmetic/evidence/state emits raw damage.

Create:

knowledge/champion_spell_damage_resolver.py

knowledge/champion_spell_damage_resolver_synthetic_checks.py

knowledge/champion_spell_damage_resolver_precision_checks.py

knowledge/champion_spell_damage_resolver_full_audit.py

This is the first layer allowed to return a value explicitly labeled as spell damage.

Only do so when BOTH are true:

damage semantic evidence is sufficiently strong;

formula evaluation is fully resolved for supplied context.

Otherwise return an explicit unresolved result.

15.1 Output structure

Each damage component should contain:

champion;

slot;

spell rank;

calculation key;

component ID;

component label/evidence;

damage type;

raw/pre-mitigation amount;

activation-condition status;

formula resolution status;

source provenance;

semantic evidence provenance;

warnings.

15.2 Activation conditions

Default behavior:

do not assume empowered form;

do not assume mark present;

do not assume max stacks;

do not assume low-health condition;

do not assume target is immobilized;

do not assume champion transformed;

do not assume repeated tick count;

do not assume passive triggered.

Represent required state.

Allow explicit caller state to satisfy a condition only if the condition semantics have been validated.

15.3 Damage type

Do not send unresolved/mixed damage through a single resistance.

Physical -> armor.
Magic -> MR.
True -> resistance bypass within frozen Phase 2E contract.

Mixed components remain separate.

Commit if clean.

Suggested commit:

Resolve validated champion spell damage components

16. Checkpoint K - Integrate frozen Combat Resistance Phase 2E

Checkpoint status: COMPLETED - thin adapter and physical/magic/true synthetic regression PASS.

Create a thin adapter instead of duplicating resistance math.

Suggested file:

knowledge/spell_damage_mitigation.py

Consume frozen:

knowledge/combat_resistance_rules.py

Do not copy its formulas.

16.1 Target input

Target combat snapshot should expose:

armor;

base/bonus armor where known;

MR;

penetration/reduction context supplied by attacker or explicit effects.

16.2 Attacker penetration

Use only factual static penetration values available in the attacker snapshot.

Do not execute conditional item/rune penetration passives yet.

Current lethality remains 1:1 flat armor penetration per frozen Phase 2E.

16.3 Result

For every fully resolved damage component return:

raw damage;

damage type;

original resistance;

reduction/penetration inputs;

effective resistance;

resistance multiplier;

post-mitigation damage;

Phase 2E provenance/version.

True damage bypasses armor/MR exactly as Phase 2E defines.

16.4 No double application

Ensure penetration is not applied:

once in formula evaluator;

and again in mitigation.

Keep arithmetic layers separate.

Commit if clean.

Suggested commit:

Connect spell damage components to combat resistance

17. Checkpoint L - End-to-end supported spell combat API

Checkpoint status: COMPLETED - single-cast API preserves components and defaults totals to non-composable.

Create a single stable high-level API.

Suggested file:

knowledge/spell_combat_runtime.py

Example conceptual interface:

resolve_spell_combat(...)

Inputs should allow:

source champion;

source level;

source items;

source current health if relevant;

spell slot;

spell rank;

target champion;

target level;

target items;

target current health if relevant;

explicit combat state flags;

optional explicit calculation/component selection.

Output:

source snapshot;

target snapshot;

source spell record;

all identified damage components;

resolved raw components;

unresolved components + reasons;

post-mitigation components;

total only when summing components is semantically valid;

provenance tree;

reliability/status.

17.1 Total damage rule

Do not automatically sum components if:

they are mutually exclusive;

one is an empowered alternative;

one is repeated damage with unknown tick count;

one requires a missing condition;

one is a passive proc not guaranteed by cast;

calculation semantics do not establish additive behavior.

Possible statuses:

TOTAL_DAMAGE_RESOLVED

COMPONENTS_RESOLVED_TOTAL_NOT_COMPOSABLE

PARTIAL_DAMAGE_ONLY

DAMAGE_UNRESOLVED

This is mandatory.

17.2 No combo engine yet

This API resolves one spell/cast-state query.

Do not simulate a full combo sequence automatically in core production logic during this milestone.

18. Checkpoint M - Spell cooldown/resource factual resolver

Checkpoint status: COMPLETED - 692 spells audited; resource type remains unresolved unless supplied explicitly.

If all earlier core checkpoints are technically healthy, continue in the same Sol task.

Do not stop simply because the damage path is complete.

Create:

knowledge/champion_spell_cast_stats.py

focused tests/audit.

Resolve factual spell metadata when exposed:

cooldown by rank;

resource cost by rank;

cast range;

other stable numeric cast metadata with clear semantics.

18.1 Ability haste

If cooldown with ability haste is implemented:

use a separately documented generic formula;

preserve provenance;

do not modify source cooldown;

report base cooldown and adjusted cooldown separately.

18.2 Unsupported costs

Different champions use:

mana;

energy;

health;

fury/other systems;

no conventional cost.

Do not label every primary-resource field "mana".

Use explicit resource semantics or unresolved resource type.

18.3 No gameplay simulation

Do not infer whether a spell can actually be cast from current resource unless resource-state semantics are validated.

Commit if clean.

Suggested commit:

Resolve factual spell cast stats

19. Checkpoint N - Pinned catalog cache for development speed

Checkpoint status: COMPLETED - optional exact-key gzip cache with checksum; ignored local storage.

The real source audit currently requires many exact pinned source fetches.

Without modifying frozen Phase 2F semantics, add an optional local cache layer for its returned catalog.

Suggested file:

knowledge/pinned_spell_catalog_cache.py

Requirements:

key includes Phase 2F source version;

pinned commit;

Data Dragon version;

locale;

schema/cache version;

exact hash/checksum of stored payload if practical;

cache invalidates on any key mismatch;

no fallback from cache of a different patch;

cache is optional;

source can still be rebuilt from pinned URLs;

cache failure never changes semantics.

Store only in an ignored local directory such as:

.cache/zircon/

Update .gitignore only if required.

Never commit huge downloaded raw game files.

This checkpoint is optional only if implementation would interfere with frozen 2F. If an adapter can do it cleanly, implement it.

Commit separately if clean.

Suggested commit:

Add pinned spell catalog development cache

20. Checkpoint O - Representative precision suite

Checkpoint status: COMPLETED - 48 requested/diverse champion probes plus independent arithmetic derivation PASS.

Create a broad representative test suite across real pinned champions.

Suggested file:

knowledge/combat_formula_representative_checks.py

Select champions based on observed class/graph diversity rather than popularity alone.

Include, when useful and supported:

simple AP caster;

simple AD scaler;

hybrid scaler;

max-health damage;

missing-health scaling;

multi-component spell;

true damage;

transformed/alternate-form champion;

repeated/tick spell;

shield/heal calculation as a NON-damage semantic control;

champion with unusual attack-speed/stat semantics;

champion with named calculation recursion;

champion using rare calculation classes.

Also include key ZiRcoN Coach champion-pool examples when they provide useful structural diversity:

Shyvana

Bel'Veth

Dr. Mundo

Viego

Rammus

Do not create champion-specific production hacks to make these tests pass.

They are validation examples only.

20.1 Manual derivation records

For representative cases, tests should show:

raw source fields;

manually derived expected arithmetic from the fixture/source;

evaluator output;

tolerance;

semantic classification;

mitigation result if applicable.

Avoid circular tests that calculate expected results by calling the same production evaluator.

21. Checkpoint P - Full cross-layer audit

Checkpoint status: COMPLETED - real cross-layer audit PASS / REVIEW_REQUIRED FOR FREEZE; no technical failures.

Create a top-level audit:

knowledge/combat_formula_foundation_full_audit.py

This is the key final report of the Sol mission.

It must aggregate:

Frozen inputs

Item Knowledge version

Champion Knowledge version

Rune Knowledge version

Level Stats version

Combat Resistance version

Champion Spell Source version

pinned datamine repository/commit/patch

Source coverage

173 champions

692 slots

1,443 calculation records

graph-node baseline

class baseline

Taxonomy

classes observed

executable classes

partially supported classes

unresolved classes

occurrences by support status

Value/DataValue

value refs resolved/unresolved

DataValue refs resolved/unresolved

rank-shape unresolved cases

Stat references

raw distinct stat refs

mapped

unresolved

occurrence coverage

Formula evaluator

fully executable calculations

partial

unsupported class

unsupported signature

missing context

cycles

malformed

per-class coverage

per-champion coverage

Static snapshots

champion/level coverage

item static-stat coverage

unresolved static stats

Damage semantics

damage candidates high confidence

ambiguous/multiple

unresolved damage type

non-damage calculations

arithmetic-resolved damage components

End-to-end mitigation

raw damage components resolved

post-mitigation components resolved

totals composable

totals not safely composable

partial/unresolved

Cast stats

cooldown coverage

resource-cost coverage

unsupported resource semantics

Validation

synthetic test counts

precision test counts

representative checks

frozen guard

git diff check

Issues

blocking issues

review items

accepted limitations

Do not hide unresolved counts.

22. main.py harness for the massive milestone

Keep main.py as a development harness.

Do NOT print all old analyzer outputs.

After Phase 2F freeze, point main.py to the new Phase 2G milestone.

It should execute a reasonable ordered validation stack, for example:

compile all new Phase 2G modules;

taxonomy synthetic/audit;

value resolver tests;

DataValue tests;

stat-ref tests;

evaluator synthetic/precision;

static snapshot tests;

damage evidence tests;

damage resolver tests;

mitigation/runtime tests;

representative checks;

top-level full audit;

FROZEN guard.

If full network audits are slow, use the exact pinned optional cache, but do not weaken source validation.

Final harness status:

PASS if technically clean;

REVIEW_REQUIRED if project-review-only decisions remain;

FAIL only for real technical failure.

23. FROZEN guard expansion

After freezing Phase 2F, main.py must protect at least:

Phase 2D

knowledge/champion_attack_speed_source.py

knowledge/champion_level_stats.py

knowledge/champion_level_stats_synthetic_checks.py

knowledge/champion_level_stats_precision_checks.py

knowledge/champion_level_stats_full_audit.py

Phase 2E

knowledge/combat_resistance_rules.py

knowledge/combat_resistance_synthetic_checks.py

knowledge/combat_resistance_precision_checks.py

knowledge/combat_resistance_full_audit.py

Phase 2F

knowledge/champion_spell_source.py

knowledge/champion_spell_source_synthetic_checks.py

knowledge/champion_spell_source_precision_checks.py

knowledge/champion_spell_source_full_audit.py

And all earlier frozen production files already guarded by the project.

Do not use the guard as a substitute for inspecting git diff.

24. Autonomy protocol for Sol

This is important.

Do NOT stop for ordinary coding issues.

Autonomously fix:

syntax errors;

imports;

typing mismatches;

malformed local fixtures;

deterministic test failures;

obvious incorrect assumptions exposed by real source audit;

performance problems;

cache bugs;

Windows path/encoding issues;

exact-source download errors that can be retried safely;

localized implementation defects.

Do NOT ask the user for permission for routine fixes.

Continue to the next checkpoint when the current checkpoint has a technically valid supported subset, even if some formula classes remain explicitly unsupported.

Example:

If 18 of 25 classes are validated executable and 7 remain unresolved:

do NOT fail the whole task solely because of the 7;

preserve the 7 as unresolved;

continue building the evaluator for the 18;

report coverage honestly.

Stop/REVIEW_REQUIRED only if:

a frozen production module must be changed;

pinned source identity is inconsistent;

a calculation semantic requires an unsupported guess that materially affects architecture;

damage semantic classification cannot be made conservative enough;

a project-wide methodology decision is genuinely required.

Even in REVIEW_REQUIRED:

finish all independent checkpoints that are still safe;

document what is blocked vs what is complete.

25. No coverage gaming

Never:

lower precision to improve formula coverage;

guess stat enum meanings;

treat formula-key names as ground truth without evidence;

silently convert partial formulas to full;

count unresolved as resolved;

force damage type from champion archetype;

assume all AP ratios mean magic damage;

assume all AD ratios mean physical damage;

assume one calculation key equals one cast's total damage;

assume max stacks;

assume all ticks hit;

assume transformed state;

assume target health threshold;

assume a mark/debuff exists;

assume item/rune proc availability.

The best result may be a smaller exact executable subset.

That is acceptable.

26. No causal/gameplay overclaiming

This milestone is deterministic combat math.

Do not infer:

whether a spell will hit;

whether a player should cast it;

whether an item is optimal;

whether a target will die in a real fight unless exact requested state is fully modeled;

gameplay recommendation;

causality;

player skill.

Do not connect to Win/Loss analyzers.

27. Explicitly NOT part of this massive Sol milestone

Even though this TODO is intentionally large, these remain out of scope because they depend on additional validated mechanics:

full item passive/active proc engine;

full rune effect engine;

stat-shard hardcoding without authoritative mapping;

generic on-hit/on-attack ordering engine;

crit engine for every champion special case;

shields as a complete combat-state simulation;

healing/omnivamp simulation;

summoner spell engine;

minion/monster damage rules;

jungle Smite rules;

multi-cast combo sequencing;

cooldown rotation simulation;

full Burst/TTK engine;

team composition scoring;

automatic build recommendations;

automatic rune recommendations;

ML;

LLM-generated combat truth;

final PySide6 UI.

Do not opportunistically implement these.

However, design the new interfaces so these layers can be added later without rewriting the formula foundation.

28. Performance engineering

This milestone may process:

173 champions;

692 spells;

1,443 calculation records;

thousands of graph nodes;

many evaluation contexts.

Avoid obviously quadratic rescans of the full catalog.

Use:

indexes;

precomputed registries;

immutable/read-only catalog structures where practical;

caching of repeated exact dependency resolution;

local pinned catalog cache if implemented;

deterministic iteration for stable audits.

Do not sacrifice correctness for speed.

Record runtime of major audits.

29. Error-handling contract

Expected incomplete knowledge is not an exception.

Use structured statuses for:

unsupported classes;

missing context;

unresolved stat refs;

unsupported rank shape;

ambiguous damage semantics.

Exceptions are for programming/source-contract errors.

Top-level audits must catch and report champion/calculation identity for unexpected exceptions.

Never silently skip a failed formula.

30. Provenance contract

Every production result exposed by the new foundation should be able to identify:

project module version;

Champion Spell Source version;

pinned datamine repository;

pinned datamine commit;

Data Dragon version;

formula calculation key;

source spell path;

slot;

any community formula provenance used;

any Riot official formula provenance used.

Do not mix source tiers without recording them.

31. Versioning

Give new modules explicit version constants.

Suggested milestone naming:

champion_spell_formula_taxonomy_phase2g_v1

champion_spell_value_resolver_phase2g_v1

champion_spell_formula_evaluator_phase2g_v1

combat_stat_snapshot_phase2g_v1

champion_spell_damage_resolver_phase2g_v1

combat_formula_foundation_phase2g_v1

Exact names may be improved for consistency, but do not omit explicit versions.

32. Documentation responsibility

As checkpoints finish, keep documentation concise but current.

PROJECT_STATE.md

Track:

Phase 2F frozen baseline;

active Phase 2G milestone;

technical support coverage;

latest full audit;

known unsupported classes;

current end-to-end capabilities;

permanent limitations.

Do not paste huge class tables into PROJECT_STATE.

DECISIONS.md

Add only durable decisions, for example:

Phase 2F freeze;

class semantics source hierarchy;

unsupported-over-guessing policy;

distinction between formula executability and damage semantic identity;

static item stats only in combat snapshot;

total damage composability rule.

Do not log routine bugs.

LAST_RUN.md

Final report must include:

exact commit(s);

commands;

runtime;

test totals;

actual class support counts;

actual formula coverage counts;

actual stat-ref coverage;

actual damage semantic coverage;

actual end-to-end coverage;

suspicious findings;

methodology concerns;

remaining issues;

review request.

TODO.md

At the end:

mark completed checkpoints;

identify any blocked checkpoint;

do not invent the next major product phase after this milestone.

33. Git checkpoint strategy

Before any commit:

git status

git diff

git diff --check

ensure no secret/local files are staged

Never commit:

.env

API keys

tokens

.venv

DB files

raw private match data

local logs

.cache

large downloaded game files

Recommended checkpoint commits, when each is independently clean:

Freeze champion spell calculation source phase 2F

Catalog champion spell calculation class semantics

Add spell value and DataValue resolution foundation

Map validated champion spell stat references

Build conservative champion spell formula evaluator

Build static combat stat snapshot foundation

Connect spell formulas to static combat context

Classify champion spell damage evidence conservatively

Resolve validated champion spell damage components

Connect spell damage components to combat resistance

Add spell combat runtime and representative validation

optional Add pinned spell catalog development cache

final docs/audit commit such as:
Validate executable combat formula foundation phase 2G

Do not create empty commits just to match this list.

Push all successful commits to origin/main at the end if:

no known broken code remains;

frozen guard passes;

final full audit completes;

git diff check passes.

If later checkpoint is blocked but earlier commits are clean, pushing the clean checkpoints is acceptable as long as LAST_RUN.md clearly says Phase 2G remains REVIEW_REQUIRED/incomplete.

No force push.

34. Required synthetic tests

Across the new modules, include deterministic no-network tests for at least:

exact class dispatch;

unknown class remains unsupported;

unsupported signature remains unsupported;

classless dictionary not executed;

scalar constant zero;

negative numeric constant;

floating point coefficient;

exact DataValue resolution;

missing DataValue;

duplicate DataValue ambiguity;

rank leading sentinel;

rank legitimate zero;

invalid rank;

exact named-calculation reference;

missing named calculation;

recursive named calculation;

cycle detection;

max recursion;

stat mapping resolved;

stat mapping unresolved;

caster stat vs target stat distinction;

total AD vs bonus AD distinction;

max health vs current/missing health distinction;

item static AD/AP/HP/armor/MR contribution;

unsupported conditional item effect excluded;

unsupported rune contribution excluded;

formula fully resolved;

formula partial because one child unresolved;

damage semantics known but formula unresolved;

formula resolved but not safely classified as damage;

physical damage mitigation;

magic damage mitigation;

true damage bypass;

penetration not double-applied;

multiple damage components preserved separately;

mutually exclusive components not auto-summed;

unknown tick count not auto-summed;

empty damage candidate list;

exact provenance preserved.

Do not make tests depend on external network unless explicitly full-audit tests.

35. Precision validation requirements

Precision tests must include real-structure fixtures copied/minimized from the pinned source.

Do not make all fixtures toy examples.

For each supported formula class/signature:

include at least one real-shaped fixture;

when the class has meaningfully different signatures, test each supported signature;

manually derive expected arithmetic;

assert provenance and dependency trace;

assert unsupported variants remain unsupported.

If there are too many classes for one file, split tests cleanly.

36. Full-catalog invariant checks

Every full audit must verify:

Champion Spell Source remains version champion_spell_source_phase2f_v1;

pinned commit remains exactly 9245fd616059c6c658d1faa1029f0e18ea179154;

frozen Champion Knowledge remains champion_knowledge_phase2b1_c_v1;

Data Dragon remains 16.16.1/fr_FR;

source still resolves 173 champions;

source still maps 692 Q/W/E/R slots;

no fuzzy mapping is introduced;

Phase 2F frozen files remain unchanged;

Phase 2E frozen files remain unchanged;

Phase 2D frozen files remain unchanged.

Any baseline mismatch is REVIEW_REQUIRED.

37. Representative end-to-end queries

When enough formula semantics are supported, the final validation should attempt real end-to-end queries.

Do not hardcode expected success for every query.

Use them to expose gaps.

Examples:

simple AP spell with no target-health dependency;

simple AD spell;

health-scaling spell;

true-damage component;

multi-component spell;

unusual state-dependent spell;

Shyvana example;

Bel'Veth example;

Dr. Mundo example;

Viego example;

Rammus example.

For each report:

whether damage formula was identified;

whether arithmetic resolved;

required state;

raw damage;

target resistance;

post-mitigation damage;

any unresolved component;

whether total damage is composable.

Never modify production logic just to make a showcase champion resolve.

38. Final milestone acceptance states

The final Phase 2G report may legitimately end in one of these states.

PASS / REVIEW_REQUIRED FOR FREEZE

Use when:

architecture is coherent;

all technical tests pass;

audits complete;

unsupported semantics are explicit;

no frozen module changed;

no concrete correctness bug remains;

remaining limitations are scope limitations.

REVIEW_REQUIRED - PARTIAL MILESTONE

Use when:

some checkpoints are clean and committed;

one methodology/source blocker prevents later checkpoints;

existing completed work remains correct.

Clearly identify the exact blocked dependency.

FAIL

Use only for actual broken implementation or failing required regression that could not be fixed.

Do not call normal unsupported League mechanics a technical FAIL.

39. Final Codex response

At the end of this one Sol mission, report concisely:

checkpoint commits created;

files added/modified;

Phase 2F freeze status;

real class taxonomy counts;

executable class count;

unsupported class count;

formula evaluation coverage;

DataValue resolution coverage;

stat-reference coverage;

static combat snapshot coverage;

damage-semantic coverage;

raw-damage coverage;

post-mitigation coverage;

representative examples;

all tests run;

full audit status;

FROZEN guard status;

git diff check;

push status;

exact remaining blockers;

whether project review is required.

Do not choose the next major product direction.

That remains ChatGPT/project review.

40. Final instruction to Sol

Treat this as one coherent engineering milestone.

Do not prematurely stop after the first successful module.

Work through the checkpoints in order.

Use your reasoning to discover the real pinned source structures and adapt the implementation to them.

The objective is not maximum percentage coverage.

The objective is the largest defensible, deterministic, auditable executable combat-formula foundation that can be built from the current frozen ZiRcoN Coach data without inventing League of Legends mechanics.

When evidence ends, explicit UNKNOWN begins.
