# ZiRcoN Coach — Phase 2I
## Stat Owner Semantics & Stat-Scaling Formula Execution Foundation

### Model recommendation
Codex: GPT-5.6 Sol
Reasoning: HIGH

This is a large, research-heavy milestone with two gated branches:

A. prove stat-owner / calculation-context semantics;
B. only where owner + stat + formula + signature + snapshot value are all validated, execute stat-scaling formulas in a NEW layer.

Never replace missing evidence with “probably caster”.

---

# 0. Starting baseline

Repository: `samuel-vercleven/ZiRcoN-Coach`
Expected HEAD: `29682a4a9419b234537bcf73cc9352f723860153`
Commit: `Freeze champion spell stat semantics phase 2H`

Frozen layers include Phase 2A through Phase 2H.
Do not modify any frozen production or validation behavior.

Phase 2H frozen facts:

- 885 semantic-field occurrences
- 569 `mStat` occurrences
- 316 explicit `mStatFormula` occurrences
- 16 raw `mStat` IDs: `[1,2,4,6,7,8,9,10,12,13,14,15,16,18,29,31]`
- execution-eligible stats:
  - `1 -> ARMOR`
  - `2 -> ATTACK_DAMAGE`
  - `12 -> HEALTH`
- validated stat coverage: `468/569 = 82.25%`
- strongly supported but non-executable: `4,6,7,8,9,10,18,29,31`
- unresolved: `13,14,15,16`
- `mStatFormula 0 -> TOTAL_STAT` VALIDATED
- `mStatFormula 2 -> BONUS_STAT` VALIDATED
- `mStatFormula 1` CONTRADICTED / non-executable
- formula coverage: `568/569 = 99.82%`
- owner baseline: `569/569 OWNER_UNRESOLVED`
- fully composed real references: `0`

Phase 2G frozen formula baseline:

- 173 champions
- 692 Q/W/E/R
- 1,443 calculations
- 5,318 graph nodes
- 25 classes
- 109 signatures
- 13 RESOLVED
- 720 PARTIALLY_RESOLVED
- 493 UNSUPPORTED_SIGNATURE
- 217 UNSUPPORTED_CLASS

Frozen exact executable signatures:

- NumberCalculationPart
- NamedDataValueCalculationPart
- SumOfSubPartsCalculationPart
- ProductOfSubPartsCalculationPart
- core GameCalculation
- NamedGameCalculationCalculationPart

Stat classes intentionally left partial:

- `StatByCoefficientCalculationPart`
- `StatByNamedDataValueCalculationPart`
- `StatBySubPartCalculationPart`

---

# 1. Mandatory startup

Read completely:

1. `AGENTS.md`
2. `PROJECT_STATE.md`
3. `TODO.md`
4. `DECISIONS.md`
5. `LAST_RUN.md`
6. `main.py`

Inspect read-only:

- `knowledge/champion_spell_source.py`
- `knowledge/champion_spell_formula_taxonomy.py`
- `knowledge/champion_spell_formula_evaluator.py`
- `knowledge/champion_spell_formula_runtime.py`
- `knowledge/combat_formula_types.py`
- `knowledge/combat_stat_snapshot.py`
- `knowledge/champion_spell_stat_semantics.py`
- `knowledge/champion_spell_stat_semantics_sources.py`
- `knowledge/champion_spell_stat_semantics_full_audit.py`

Before coding run:

```text
git status
git diff
git log --oneline --decorate -15
git rev-parse HEAD
git rev-parse origin/main
```

If HEAD differs from the expected freeze commit, inspect why first.

Search the repo for:

- `StatByCoefficientCalculationPart`
- `StatByNamedDataValueCalculationPart`
- `StatBySubPartCalculationPart`
- `mStat`
- `mStatFormula`
- `unitStatComponent`
- `CASTER`
- `TARGET`
- `SOURCE_LEVEL`
- `compose_snapshot_reference`
- `PARTIALLY_RESOLVED`

---

# 2. Frozen boundary

Do NOT modify Phase 2G or Phase 2H files.

Especially do not modify:

- `knowledge/champion_spell_formula_taxonomy.py`
- `knowledge/champion_spell_formula_evaluator.py`
- `knowledge/champion_spell_formula_runtime.py`
- `knowledge/combat_formula_types.py`
- `knowledge/combat_stat_snapshot.py`
- any Phase 2H file

Use new adapters/new modules.

If a frozen interface truly blocks a safe implementation, stop that branch and return `REVIEW_REQUIRED` instead of editing frozen code.

---

# 3. New Phase 2I modules

Suggested production:

- `knowledge/champion_spell_stat_owner_semantics.py`
- `knowledge/champion_spell_stat_owner_sources.py`
- `knowledge/champion_spell_stat_scaling_evaluator.py`
- `knowledge/champion_spell_stat_scaling_runtime.py`

Suggested validation:

- `knowledge/champion_spell_stat_owner_synthetic_checks.py`
- `knowledge/champion_spell_stat_owner_precision_checks.py`
- `knowledge/champion_spell_stat_owner_full_audit.py`
- `knowledge/champion_spell_stat_scaling_synthetic_checks.py`
- `knowledge/champion_spell_stat_scaling_precision_checks.py`
- `knowledge/champion_spell_stat_scaling_full_audit.py`
- `knowledge/champion_spell_stat_scaling_representative_checks.py`
- `knowledge/stat_scaling_formula_foundation_full_audit.py`

Optional:

- `knowledge/champion_spell_stat_owner_research_audit.py`

Suggested versions:

- `champion_spell_stat_owner_semantics_phase2i_v1`
- `champion_spell_stat_scaling_phase2i_v1`
- `stat_scaling_formula_foundation_phase2i_v1`

Do not freeze Phase 2I yourself.

---

# 4. Branch A — Stat owner/context semantics

## 4.1 Source hierarchy

Use evidence in this order:

1. exact pinned 26.16 game-file structures: `Haru-Kay/LeagueDatamines@9245fd616059c6c658d1faa1029f0e18ea179154`
2. patch-matched reverse-engineered meta structures
3. executable reverse-engineering implementations such as `moonshadow565/calcrev`, LeagueBuilder, CommunityDragon tooling
4. independent exact champion/mechanic evidence
5. unresolved

A field type or memory layout does not prove owner identity.

Do not equate `unitStatComponent` with caster unless the actual source-unit semantics are proven.

## 4.2 Exhaustive owner inventory

For all 569 `mStat` occurrences preserve:

- champion
- slot
- spell path
- calculation key
- graph path
- class
- exact structural signature
- raw `mStat`
- effective `mStatFormula`
- frozen 2H semantic stat result
- frozen 2H semantic formula result
- parent/root calculation
- sibling fields
- ancestor fields potentially relevant to source/target selection
- child/subpart structure
- tooltip linkage
- source/version/provenance

Group by class + exact signature + structural context.

## 4.3 Owner taxonomy

Possible statuses:

- `OWNER_VALIDATED_CASTER`
- `OWNER_VALIDATED_TARGET`
- `OWNER_VALIDATED_SOURCE_LEVEL`
- `OWNER_VALIDATED_OTHER_CONTEXT`
- `OWNER_CONTEXT_DEPENDENT`
- `OWNER_STRONGLY_SUPPORTED_CASTER`
- `OWNER_STRONGLY_SUPPORTED_TARGET`
- `OWNER_AMBIGUOUS`
- `OWNER_CONTRADICTED`
- `OWNER_UNRESOLVED`

Only exact `OWNER_VALIDATED_*` statuses can be execution-eligible.

## 4.4 Contract granularity

Prefer the narrowest defensible contract:

`class + exact signature + structural context`

rather than a global rule such as:

`all StatByCoefficient = CASTER`.

A broad rule is acceptable only if all real matching contexts are proven equivalent.

## 4.5 Contradiction audit

For every candidate owner contract search all real matching occurrences for counterexamples.

Do not confuse:

- spell/damage target
- stat owner
- tooltip subject
- calculation source unit

A spell may damage TARGET while scaling from CASTER.

Damage target != stat owner.

## 4.6 Source registry

Create owner-specific source records with:

- source ID
- URL
- immutable commit where possible
- patch/version
- evidence tier
- supported claim
- limitations

---

# 5. Owner precision requirements

For every VALIDATED owner contract include real pinned precision fixtures with:

- champion
- slot
- calculation key
- graph path
- class/signature
- stat/formula
- expected owner
- independent evidence
- provenance

Do not derive expected owner from production code.

Broad contracts need multiple unrelated champions.

---

# 6. Execution gate

After owner research, produce a gate report.

Proceed to stat arithmetic only if at least one real stat reference has ALL of:

- exact supported stat-class signature
- frozen 2H `mStat` status VALIDATED
- frozen 2H `mStatFormula` status VALIDATED
- Phase 2I owner status VALIDATED
- compatible frozen Phase 2G snapshot field
- required coefficient/DataValue/subpart semantics proven

If zero real occurrences satisfy this:

- do not invent owner semantics
- finish Branch A
- run audits
- commit/push
- return `PASS / REVIEW_REQUIRED`
- do not create fake numeric coverage

This is a valid result.

---

# 7. Branch B — exact stat-class signatures

Inventory every exact pinned structural signature for:

- `StatByCoefficientCalculationPart`
- `StatByNamedDataValueCalculationPart`
- `StatBySubPartCalculationPart`

Build a NEW Phase 2I signature registry.

For every signature record:

- exact fields
- required fields
- unsupported fields
- stat behavior
- coefficient/DataValue/subpart behavior
- owner contract
- provenance
- execution eligibility

Unknown extra field => fail closed.

Do not inherit executable status merely from class name.

---

# 8. StatByCoefficientCalculationPart

Only implement arithmetic after exact semantics are proven.

Do not assume `stat * coefficient` from name alone.

Validate:

- coefficient field
- numeric semantics
- total/bonus handling
- owner
- signature
- any modifier fields

Unsupported variant => `STAT_SIGNATURE_UNSUPPORTED`.

---

# 9. StatByNamedDataValueCalculationPart

Only implement if exact semantics are proven.

Reuse frozen Phase 2G DataValue/rank resolvers where possible.

Require:

- exact DataValue name
- valid spell-rank resolution
- validated stat ID
- validated formula ID
- validated owner
- exact signature

Do not assume multiplication from class naming alone.

---

# 10. StatBySubPartCalculationPart

Treat conservatively.

Determine exact relation between:

- stat value
- nested subpart
- any coefficient/modifier

Do not infer.

Use cycle-safe recursion.

An unresolved required child prevents a fully resolved parent.

---

# 11. Snapshot dependency contract

A snapshot stat is usable only if its frozen Phase 2G `stat_resolution` status is exactly:

`STATIC_STAT_RESOLVED`

If partial:

- preserve known partial for diagnostics if useful
- do NOT use it as exact arithmetic

Examples of frozen fields potentially usable after semantic composition:

- `attack_damage_total`
- `attack_damage_bonus`
- `armor`
- `armor_bonus`
- `health_max`
- `health_bonus`

Do not invent a BASE_STAT mapping to native-at-level fields.

---

# 12. Frozen 2H consumption

Do not hardcode 2H mappings into Phase 2I.

Consume frozen Phase 2H records/APIs.

If stat status is not exactly VALIDATED:
return unresolved.

If formula status is not exactly VALIDATED:
return unresolved.

In particular:

- `mStatFormula=1` must never execute
- IDs `4,6,7,8,9,10,18,29,31` must not execute
- IDs `13,14,15,16` must not execute

Phase 2I cannot upgrade frozen 2H semantics.

---

# 13. AP boundary

The pinned UI table contains `0 -> ABILITY_POWER`, but raw `mStat=0` was not an execution-eligible Phase 2H mapping.

Phase 2I must NOT independently promote AP.

If this blocks AP formula coverage, report it as a future project-review item.

Do not patch Phase 2H.

---

# 14. AbilityResource boundary

Phase 2H isolated AbilityResource as research-only.

Do not turn Phase 2I into a resource enum engine.

Leave resource semantics unsupported unless an already-frozen fact directly resolves them.

---

# 15. New stat-scaling evaluator

Create a new evaluator above frozen Phase 2G.

Preferred architecture:

- reuse/delegate frozen primitive semantics where possible
- intercept newly validated stat-class signatures
- recursively evaluate mixed graphs
- preserve child traces and provenance

Do NOT modify the frozen Phase 2G evaluator.

If callback/delegation architecture is insufficient, create a new orchestration evaluator that reuses frozen contracts without editing them.

---

# 16. New result statuses

At minimum:

- `STAT_SCALING_RESOLVED`
- `STAT_SCALING_PARTIALLY_RESOLVED`
- `STAT_ID_NOT_EXECUTION_ELIGIBLE`
- `STAT_FORMULA_NOT_EXECUTION_ELIGIBLE`
- `STAT_OWNER_NOT_EXECUTION_ELIGIBLE`
- `STAT_SNAPSHOT_FIELD_UNAVAILABLE`
- `STAT_SNAPSHOT_VALUE_PARTIAL`
- `STAT_SIGNATURE_UNSUPPORTED`
- `STAT_COEFFICIENT_UNRESOLVED`
- `STAT_DATA_VALUE_UNRESOLVED`
- `STAT_SUBPART_UNRESOLVED`
- `STAT_CONTEXT_UNSUPPORTED`
- `STAT_CYCLE_DETECTED`
- `SOURCE_VERSION_MISMATCH`

Do not represent failure only with `None`.

---

# 17. Mixed graph rule

A root may contain:

- Number
- DataValue
- stat part
- Sum/Product
- named calculation
- unsupported child

Resolve the root only when every required traversed child is validated and resolved.

One unresolved required child => parent is not fully resolved.

Preserve partial children.

---

# 18. Formula replay audit

Replay all 1,443 pinned calculations through the new Phase 2I layer.

Compare against frozen Phase 2G baseline without modifying it.

Report:

- total 1,443
- Phase 2G baseline: 13 resolved / 720 partial / 493 unsupported signature / 217 unsupported class
- Phase 2I fully resolved
- Phase 2I partially resolved
- unsupported signature
- unsupported class
- blocked by stat ID
- blocked by formula ID
- blocked by owner
- blocked by snapshot field
- blocked by partial snapshot
- blocked by DataValue
- blocked by context
- cycles
- malformed

No target coverage percentage.

---

# 19. Resolution attribution

For every formula whose status improves, record exactly why.

Example:

```text
PARTIALLY_RESOLVED -> RESOLVED
because:
validated stat signature
+ mStat 2 ATTACK_DAMAGE
+ mStatFormula 0 TOTAL_STAT
+ owner CASTER
+ attack_damage_total STATIC_STAT_RESOLVED
```

For formulas still partial, preserve exact blocker such as:

`OWNER_UNRESOLVED`.

---

# 20. Representative validation

Use actual structural diversity.

Include where relevant:

- Aatrox
- Akshan
- Diana
- Malphite

Also inspect, without champion-specific production hacks:

- Shyvana
- Bel'Veth
- Dr. Mundo
- Viego
- Rammus

Only use them where they actually exercise useful source structures.

---

# 21. Manual arithmetic precision tests

For every executable real stat signature:

- use minimized real pinned structure
- manually state snapshot value
- manually state coefficient/DataValue/subpart
- manually derive expected result
- compare with evaluator

Do not compute expected values with production evaluator.

Test negative/zero/decimal values where supported by real semantics.

---

# 22. Required synthetic owner tests

At minimum:

1. unresolved owner stays unresolved
2. strongly supported owner is non-executable
3. ambiguous owner is non-executable
4. contradicted owner is non-executable
5. validated caster path
6. validated target code path if a real production contract exists; otherwise synthetic contract only
7. damage target != scaling-stat owner
8. exact signature mismatch fails closed
9. context mismatch fails closed
10. provenance preserved

Do not fabricate a real target-owner production mapping for test coverage.

---

# 23. Required stat-scaling tests

At minimum exercise code paths for:

- total AD
- bonus AD
- total armor
- bonus armor
- total HP
- bonus HP
- formula 1 rejected
- strongly-supported mStat rejected
- unresolved mStat rejected
- unresolved owner rejected
- partial snapshot rejected
- missing snapshot field
- unresolved DataValue
- unresolved subpart
- mixed graph partial propagation
- cycle detection
- source mismatch
- zero coefficient valid
- raw enum zero not treated as missing
- full provenance trace

Only production-resolve combinations actually allowed by frozen 2H + validated owner contracts.

---

# 24. Owner full audit

Report:

- 569 stat rows
- owner contract count
- exact owner-signature/context contracts
- validated caster occurrences
- validated target occurrences
- validated other occurrences
- strongly supported
- ambiguous
- contradicted
- unresolved
- execution-eligible owner occurrence count
- contradictions
- source provenance
- frozen changes
- blockers

No owner coverage target.

---

# 25. Stat-scaling full audit

Report:

- stat class counts
- exact signatures observed
- exact signatures validated
- owner eligible nodes
- stat eligible nodes
- formula eligible nodes
- snapshot eligible nodes
- fully executable stat nodes
- unresolved by reason
- numeric results by class
- arithmetic under unvalidated signature = 0
- arithmetic under unvalidated owner = 0
- arithmetic under non-validated stat/formula = 0
- partial snapshot used as exact = 0

---

# 26. Top Phase 2I audit

Create:
`knowledge/stat_scaling_formula_foundation_full_audit.py`

Include:

## Frozen versions
- Phase 2F
- Phase 2G
- Phase 2H
- snapshot/version dependencies

## Owner semantics
- 569 baseline
- validated owner coverage
- unresolved/ambiguous/contradicted

## Frozen 2H consumption
- validated stat occurrences
- validated formula occurrences
- blocked IDs/formulas

## Signatures
- observed
- validated
- unsupported

## 1,443 formula replay
- Phase 2G baseline
- Phase 2I result
- delta newly resolved
- attribution

## Safety
- frozen modifications = 0
- owner guesses = 0
- non-validated stat executions = 0
- non-validated formula executions = 0
- unsupported signature executions = 0
- partial snapshot exact-use = 0

## Result
- blockers
- review items
- status

---

# 27. Success criteria

All of these are valid technical outcomes:

A. broad owner proof + many newly resolved formulas
B. narrow owner proof + small exact executable subset
C. no defensible owner proof + zero new numeric execution

PASS depends on correctness and auditability, not coverage.

Do not lower standards to improve numbers.

---

# 28. Damage boundary

Phase 2I is formula arithmetic, not damage semantics.

Do not modify frozen damage evidence/resolver/mitigation layers.

Do not automatically call a numeric formula result “damage”.

Do not integrate into Burst/TTK.

---

# 29. main.py development harness

Make Phase 2I the active development harness while preserving every frozen guard.

Suggested order:

1. compile Phase 2I modules
2. owner synthetic checks
3. owner precision checks
4. owner research/full audit
5. execution gate
6. if gate passes:
   - stat scaling synthetic checks
   - stat scaling precision checks
   - stat scaling full audit
   - representative checks
   - 1,443 formula replay
7. top Phase 2I audit
8. FROZEN guard

Do not print all historical analyzers.

---

# 30. Documentation

Update:

- `PROJECT_STATE.md`
- `TODO.md`
- `LAST_RUN.md`

Update `DECISIONS.md` only for durable Phase 2I methodology/source decisions.

Do NOT declare Phase 2I FROZEN.

Final status:

`PASS / REVIEW_REQUIRED FOR FREEZE`

or `REVIEW_REQUIRED` if a real methodology blocker remains.

---

# 31. LAST_RUN must include

- Phase 2I versions
- source commits/URLs
- runtime
- 569 owner baseline
- owner status counts
- owner execution-eligible count
- exact stat signatures
- executable stat node count
- 1,443 formula replay
- Phase 2G baseline comparison
- newly resolved count
- still-partial count
- blocked-by-owner/stat/formula/snapshot/context counts
- tests/audits
- FROZEN guard
- `git diff --check`
- remaining limitations

---

# 32. Git strategy

Before commits:

```text
git status
git diff
git diff --check
```

Never stage:

- `.env`
- API keys/tokens
- `.venv`
- DB
- logs
- `.cache`
- downloaded archives
- credentials

Suggested commits:

1. `Research champion spell stat owner semantics phase 2I`
2. `Validate champion spell stat owner contracts phase 2I`
3. `Build stat scaling formula execution phase 2I`
4. `Audit stat scaling formula foundation phase 2I`

Use fewer commits if cleaner.

Push clean commits to `origin/main`.
No force push.

At end verify:

```text
git rev-parse HEAD
git rev-parse origin/main
git status --short
```

HEAD and origin/main must match.

---

# 33. Autonomy protocol

Fix routine issues autonomously:

- syntax
- imports
- fixtures
- typing
- cache
- exact-source parsing
- deterministic audit bugs
- performance

If one owner contract fails, continue others.

If arithmetic branch cannot safely proceed, finish owner branch and audits.

Stop only for:

- required frozen change
- source identity mismatch
- architecture-level methodology contradiction

---

# 34. Explicitly out of scope

Do NOT implement:

- Phase 2H remapping
- AP enum promotion outside frozen 2H
- full resource enum engine
- item passive/active engine
- rune execution
- stat shards
- generic buff engine
- transformations
- ticks
- crit special cases
- on-hit ordering
- combo sequencing
- Burst/TTK
- build recommendations
- ML
- UI

Do not start a successor phase automatically.

---

# 35. Final Codex response

Report concisely:

- commits
- files
- owner research conclusion
- owner counts
- validated owner contracts
- unresolved/ambiguous/contradicted owner contracts
- exact stat signatures validated
- whether execution gate passed
- stat nodes executed
- 1,443 formula replay
- delta from Phase 2G baseline 13 RESOLVED / 720 PARTIAL
- representative cases
- tests/audits
- FROZEN guard
- git diff check
- push status
- HEAD/origin SHA
- remaining blockers

Do NOT declare Phase 2I FROZEN.
Do NOT start the next phase.

---

# Final principle

Phase 2H answered:

WHAT STAT?
WHAT STAT FORMULA SHAPE?

Phase 2I must answer:

WHOSE STAT?

Only when that is proven may it calculate:

STAT VALUE × SCALING.

Never replace an unknown owner with “probably caster”.
The largest defensible executable subset wins.

---

# 36. Completion status

`COMPLETED / FROZEN`

Phase 2I v1 was accepted and FROZEN by project review on 2026-09-04.

- 569/569 stat occurrences were inventoried with exact owner-relevant context.
- 88 exact class/signature/context owner contracts were audited.
- 567 occurrences are `OWNER_CONTEXT_DEPENDENT`.
- The two signatures carrying unknown `0xa8cb9c14` remain `OWNER_UNRESOLVED`.
- No caster, target, source-level, or other-context owner contract reached `VALIDATED`.
- Owner execution eligibility is 0/569; the stat-scaling execution gate did not pass.
- Branch B, numeric stat arithmetic, and the 1,443-calculation numeric replay were therefore not started, exactly as required by the zero-gate outcome.
- The frozen Phase 2G baseline remains 13 `RESOLVED`, 720 `PARTIALLY_RESOLVED`, 493 `UNSUPPORTED_SIGNATURE`, and 217 `UNSUPPORTED_CLASS`, without modifying Phase 2G or Phase 2H.
- The full owner validation stack, top Phase 2I audit, `python main.py`, and FROZEN guard pass.

Accepted FROZEN baseline: version `champion_spell_stat_owner_semantics_phase2i_v1`; top foundation `stat_scaling_formula_foundation_phase2i_v1`; 567 `OWNER_CONTEXT_DEPENDENT`, 2 `OWNER_UNRESOLVED`, 0 execution-eligible owner occurrences; gate blockers 467 owner, 101 frozen stat ID, and 1 frozen formula ID.

Phase 2I is FROZEN. Branch B remains not started; no stat-scaling evaluator, stat arithmetic, or numeric 1,443-calculation replay exists. No successor backend phase has been started.
