# ZiRcoN Coach - Phase 2G pre-freeze hardening

## Execution status

COMPLETED on 2026-08-22. All hardening checkpoints, the complete Phase 2G test/audit stack, `python main.py`, the FROZEN guard, and final Git checks passed. Phase 2G remains `REVIEW_REQUIRED` for the project freeze decision; no new phase was started.

## Model recommendation
Codex: Terra
Reasoning: HIGH

This is NOT a new major phase.

Phase 2G has produced a large, useful foundation and its real audits are technically clean, but project review found concrete correctness/contract problems that must be fixed before Phase 2G can be frozen.

Do not reopen frozen Phase 2D, 2E, or 2F production code.

Do not start Phase 2H.

---

# 1. Preserve the successful Phase 2G baseline

The current Phase 2G implementation and audit established:

- Phase 2F is now FROZEN.
- 173/173 champions and 692/692 Q/W/E/R primary spell mappings still resolve from the exact pinned source.
- 1,443 raw calculation records.
- 5,318 dictionary graph nodes.
- 25 calculation classes.
- 109 observed structural signatures.
- DataValue references: 1,464 resolved, 361 exact-name not found, 4 unsupported shapes.
- stat references: 885 occurrences / 16 raw IDs / 0 mapped.
- evaluator: 79 RESOLVED, 1,037 PARTIALLY_RESOLVED, 110 UNSUPPORTED_SIGNATURE, 217 UNSUPPORTED_CLASS.
- current damage execution coverage is intentionally tiny: 1 raw/post-mitigation component.
- all frozen guards and current audits pass.

Do not weaken UNKNOWN/UNSUPPORTED rules to increase those counts.

The purpose of this task is to correct unsafe "resolved" contracts and validation gaps, not to increase coverage.

---

# 2. Concrete blocker A - static item facts are silently discarded

Current `combat_stat_snapshot.py` applies only normalized stats whose source is exactly:

`DDRAGON_STATS`

That policy itself is acceptable.

The bug is that relevant static facts from other Item Knowledge provenance are silently skipped while the snapshot may still be returned as `SNAPSHOT_RESOLVED`.

Frozen Item Knowledge explicitly has description-derived static canonical facts including at least:

- `lethality`
- `ability_haste`
- and other description-only / description-derived stats.

Current Phase 2G then initializes:

- `ability_haste = 0.0`
- `lethality = 0.0`

even if an equipped item's Item Knowledge record contains an excluded description-derived value for one of those stats.

That can turn "not used because source policy excludes it" into the false factual statement "the champion has zero".

This violates the milestone rule:

> If Item Knowledge has a stat value parsed from description but provenance/reliability is not adequate for exact combat arithmetic, expose an unresolved/reliability status rather than silently using it.

## Required fix

For every equipped item:

1. inspect all normalized stat facts;
2. continue to apply only source types explicitly authorized for arithmetic;
3. BUT inventory relevant excluded static facts;
4. if an excluded fact could change a snapshot output used by combat arithmetic, mark that output unresolved/unknown rather than silently treating the contribution as zero.

Create structured evidence, for example:

- item ID;
- canonical stat;
- source;
- value;
- confidence;
- reason excluded.

Use a status such as:

- `STATIC_STAT_RESOLVED`
- `STATIC_STAT_PARTIAL`
- `STATIC_STAT_SOURCE_EXCLUDED`
- `STATIC_STAT_NOT_EXPOSED`

Do not use free-text strings as the only machine-readable contract.

For a stat with an excluded contribution:

- the final exact total must not be emitted as if complete;
- preserve any known partial amount separately if useful;
- do not feed an incomplete total into downstream exact damage math.

Examples that must be covered explicitly:

- lethality item whose lethality is only description-derived;
- ability-haste item whose AH is only description-derived;
- item with supported structured AD plus excluded description-derived AH: AD can remain exact while AH is unresolved.

If no equipped item exposes any contribution for a stat and the native baseline is genuinely zero, zero is valid.

Do not globally turn all absent optional stats into UNKNOWN.

---

# 3. Concrete blocker B - percentage penetration sources are being summed additively

Current `combat_stat_snapshot.py` accumulates normalized item stats using a numeric `Counter`.

This means multiple:

- `armor_penetration_percent`
- `magic_penetration_percent`

sources are added together.

Current `spell_damage_mitigation.py` then sends that one summed fraction to frozen Phase 2E as one percentage penetration source.

Frozen Phase 2E explicitly combines independent percentage effects multiplicatively:

`1 - product(1 - each_source)`

For example, 30% + 20% must be 44%, not 50%.

The Phase 2G snapshot must not destroy source multiplicity.

## Required fix

Preserve percentage penetration sources individually.

Suggested snapshot fields:

- `armor_penetration_percent_sources`
- `magic_penetration_percent_sources`

Each source should include at least:

- item ID/source identity;
- fraction;
- provenance.

If a combined display value is useful, compute it only by consuming frozen Phase 2E `combine_percentages`; do not duplicate the formula.

`spell_damage_mitigation.py` must pass the individual percentage fractions into:

- `resolve_armor(... percentage_penetrations=...)`
- `resolve_magic_resistance(... percentage_penetrations=...)`

Flat penetration remains additive where the frozen rules allow it.

Lethality remains additive flat armor penetration only when the snapshot lethality value is exact.

If percentage penetration is partial/unresolved, exact mitigation must not proceed as if the unknown contribution were zero.

Add a deterministic regression test:

- source A = 30%
- source B = 20%
- effective combined percentage = 44%
- never 50%.

The test must verify both the snapshot representation and final Phase 2E input/result.

---

# 4. Concrete blocker C - "executable class" is broader than validated signature

Current taxonomy contract logic effectively says:

- class is known;
- required fields are a subset of observed fields;
- therefore classify the node as executable/partially validated.

That is not strict enough for the Phase 2G contract.

The milestone explicitly required:

> A class may have several structural variants.
> Do not make one implementation support all variants unless each is validated.
> Represent supported signatures separately.

A node with extra, semantically meaningful fields must not become executable merely because it also contains the minimum required field.

The evaluator has the same problem for several classes: it dispatches by class and reads selected fields without first proving that the exact structural signature is supported.

## Required fix

Build an explicit supported-signature registry.

For every executable class:

- inventory real pinned structural signatures;
- explicitly mark which exact signatures are validated;
- store provenance/evidence for the decision;
- unsupported signature => `UNSUPPORTED_SIGNATURE`.

Do not use "required subset" as executable proof.

If harmless presentation-only fields are intentionally ignored:

- enumerate those exact fields;
- document why they do not affect arithmetic;
- test that contract.

At minimum harden:

- `NumberCalculationPart`
- `NamedDataValueCalculationPart`
- `SumOfSubPartsCalculationPart`
- `ProductOfSubPartsCalculationPart`
- supported `GameCalculation` root signatures
- any other class that currently produces a numeric `RESOLVED`.

The evaluator must consult this signature contract before arithmetic.

A newly observed/unlisted field on an executable class must fail closed to `UNSUPPORTED_SIGNATURE`.

Do not modify frozen Phase 2F source inventory to achieve this.

---

# 5. Concrete blocker D - damage identity is currently too dependent on the word "damage"

Current `champion_spell_damage_evidence.py` forms candidate calculation keys with:

`"damage" in calculation_key.casefold()`

and combines that with spell-level frozen Champion Knowledge damage-type effects.

This is not sufficient for `DAMAGE_CALCULATION_HIGH_CONFIDENCE`.

The milestone explicitly required:

> No single generic word such as `Damage` is sufficient if context is ambiguous.

A calculation key such as damage reduction, damage multiplier, incoming damage, tooltip damage helper, or another non-output quantity can contain "damage".

Also, spell-level damage-type tags are not automatically component-local proof that every key containing "damage" is that damage type.

## Required fix

Keep key text only as supporting evidence, never as sole component-identity evidence.

For `DAMAGE_CALCULATION_HIGH_CONFIDENCE`, require a stronger auditable linkage.

Inspect actual pinned spell structures and frozen Champion Knowledge context for available component-local linkage such as:

- tooltip calculation references;
- exact spell calculation keys referenced by damage tooltip fields;
- source fields that bind a displayed damage value to a calculation;
- other reproducible pinned structural evidence.

Do not invent a linkage if the source does not expose one.

If no sufficiently strong component-local linkage exists:

- downgrade to `DAMAGE_EVIDENCE_INSUFFICIENT`;
- keep candidate key names as evidence;
- do not emit raw damage.

It is acceptable if the current 1 resolved real damage component becomes 0 after this correction.

Precision is more important than retaining that one result.

Do not solve this with a fragile blacklist like `"reduction" not in key`.
A negative-word filter may be an additional guard, not primary proof.

---

# 6. Concrete blocker E - snapshot incompleteness must propagate downstream

Once blocker A is fixed, downstream layers must not ignore incomplete stats.

Harden:

- formula runtime;
- damage resolver;
- mitigation;
- cast cooldown adjustment;
- end-to-end spell combat runtime.

Examples:

- unknown lethality contribution -> physical post-mitigation result cannot be exact if lethality is needed;
- unknown percentage penetration -> mitigation cannot be exact;
- unknown ability haste -> adjusted cooldown cannot be exact;
- exact AD but unknown AH should not invalidate AD-only formula arithmetic.

Use per-stat dependency propagation rather than invalidating the entire snapshot unnecessarily.

The evaluator should care only about the exact stats it depends on.

---

# 7. Composability contract hardening

Current `spell_combat_runtime.resolve_spell_combat` accepts a plain boolean:

`explicitly_composable=True`

That is too weak to represent the milestone's "explicitly validated composability decision".

Replace or supplement it with a structured composability decision containing:

- status;
- component IDs/calculation keys covered;
- reason/evidence;
- provenance/source;
- caller supplied vs project validated.

A bare boolean must not be enough to emit `TOTAL_DAMAGE_RESOLVED`.

Suggested statuses:

- `COMPOSABILITY_NOT_ESTABLISHED`
- `COMPOSABILITY_CALLER_ASSERTED`
- `COMPOSABILITY_VALIDATED`
- `COMPONENTS_MUTUALLY_EXCLUSIVE`
- `TICK_COUNT_UNRESOLVED`
- `ACTIVATION_RELATION_UNRESOLVED`

Only `COMPOSABILITY_VALIDATED` may produce an exact total.

If there is currently no project-validated real composability rule, totals should remain unresolved/not safely composable.

---

# 8. Validation gap - precision fixtures must cover executable signatures

The Phase 2G precision suite is currently too small relative to the executable signature surface.

For every exact signature that remains executable after blocker C:

- add at least one deterministic precision fixture;
- the fixture must be copied/minimized from a real pinned 26.16 source shape, with the source champion/slot/calculation key recorded in comments or fixture metadata;
- manually derive expected arithmetic;
- do not call the production evaluator to produce the expected value;
- include provenance assertion.

If multiple signatures of one class remain supported, test every supported signature.

Also test at least one real pinned unsupported variant for each class that has both supported and unsupported signatures.

---

# 9. Audit hardening

Current audits correctly report unresolved coverage, but several PASS conditions mostly prove "no exception".

Strengthen them without creating artificial coverage targets.

## 9.1 Snapshot full audit

Report:

- fully resolved snapshots;
- partial snapshots;
- excluded static facts by canonical stat/source;
- exact item stat contributions applied;
- known partial contributions;
- unresolved totals;
- representative item IDs/names.

It must fail/review if an excluded relevant contribution is silently represented as exact zero.

Do NOT require 4,844/4,844 fully resolved if real evidence makes some snapshots partial.

## 9.2 Taxonomy/evaluator audit

Report:

- exact executable signatures;
- exact unsupported signatures;
- numeric calculations resolved through each signature;
- any node evaluated under an unregistered signature.

Any arithmetic evaluation under an unregistered signature is a blocker.

## 9.3 Damage evidence audit

Report evidence tiers, not just candidate count:

- component-local structural linkage;
- key-name-only candidates;
- spell-level-type-only evidence;
- insufficient;
- ambiguous.

`DAMAGE_CALCULATION_HIGH_CONFIDENCE` must have no key-name-only cases.

## 9.4 Mitigation audit

Report:

- exact penetration sources passed to Phase 2E;
- unresolved penetration inputs;
- physical/magic components withheld because penetration is incomplete;
- multiplicative percentage regression.

## 9.5 Top full audit

`technical_ok` must include the new safety invariants above.

Do not require a minimum formula/damage coverage.

A result of 0 exact real damage components may still PASS if all unresolved reasons are correct.

---

# 10. Real regression probes

Add real-catalog probes specifically selected to test the bugs above.

At minimum:

1. an item with description-derived lethality;
2. an item with description-derived ability haste;
3. two synthetic percentage penetration sources to prove multiplicative behavior;
4. a real calculation class with more than one observed signature;
5. a key containing "damage" that is not automatically accepted as an outgoing damage amount, if such a real example exists;
6. a supported real formula signature;
7. an unsupported real signature;
8. one of Shyvana / Bel'Veth / Mundo / Viego / Rammus as a no-hack regression probe.

Do not add champion-specific production branches.

---

# 11. Frozen boundaries

Do NOT modify:

## Phase 2D
- `knowledge/champion_attack_speed_source.py`
- `knowledge/champion_level_stats.py`
- `knowledge/champion_level_stats_synthetic_checks.py`
- `knowledge/champion_level_stats_precision_checks.py`
- `knowledge/champion_level_stats_full_audit.py`

## Phase 2E
- `knowledge/combat_resistance_rules.py`
- `knowledge/combat_resistance_synthetic_checks.py`
- `knowledge/combat_resistance_precision_checks.py`
- `knowledge/combat_resistance_full_audit.py`

## Phase 2F
- `knowledge/champion_spell_source.py`
- `knowledge/champion_spell_source_synthetic_checks.py`
- `knowledge/champion_spell_source_precision_checks.py`
- `knowledge/champion_spell_source_full_audit.py`

And all earlier frozen analyzer/knowledge modules listed in `AGENTS.md`.

If a genuine frozen change is required, stop that branch and return REVIEW_REQUIRED.

---

# 12. Files likely to change

Likely:

- `knowledge/champion_spell_formula_taxonomy.py`
- taxonomy tests/audit
- `knowledge/champion_spell_formula_evaluator.py`
- evaluator tests/audit
- `knowledge/combat_stat_snapshot.py`
- snapshot tests/audit
- `knowledge/champion_spell_damage_evidence.py`
- evidence tests/audit
- `knowledge/champion_spell_damage_resolver.py`
- damage tests/audit as needed
- `knowledge/spell_damage_mitigation.py`
- mitigation tests
- `knowledge/champion_spell_cast_stats.py`
- `knowledge/spell_combat_runtime.py`
- representative checks
- `knowledge/combat_formula_foundation_full_audit.py`
- `main.py`
- `PROJECT_STATE.md`
- `LAST_RUN.md`
- `TODO.md`
- `DECISIONS.md` only for new durable policy decisions

Do not rewrite unrelated code.

---

# 13. Required validation

Run the complete Phase 2G stack.

At minimum:

- py_compile all Phase 2G files;
- all synthetic checks;
- all precision checks;
- taxonomy real audit;
- value/DataValue audits;
- stat-reference audit;
- evaluator real audit;
- snapshot real audit;
- damage evidence real audit;
- damage resolver real audit;
- cast stats audit;
- representative checks;
- top cross-layer audit;
- `python main.py`;
- FROZEN guard;
- `git diff --check`;
- inspect `git status`;
- inspect final diff.

Do not modify audit expectations merely to make tests green.

Update `LAST_RUN.md` with the NEW real counts after the fixes.

Do not preserve old counts such as:

- 4,844/4,844 snapshot resolved;
- 1 raw damage resolved;

if the corrected safety contracts change them.

---

# 14. Git strategy

This is a pre-freeze hardening pass.

Prefer one or a few coherent commits, for example:

1. `Harden phase 2G combat stat and penetration contracts`
2. `Harden formula signatures and damage evidence`
3. `Validate phase 2G pre-freeze safety`

Push if clean.

No force push.

---

# 15. Final state

Do NOT declare Phase 2G FROZEN yourself.

Finish with:

`REVIEW_REQUIRED`

for ChatGPT/project freeze review.

Report:

- exact static stats now withheld/partial because of source policy;
- number of snapshots fully resolved vs partial;
- exact supported signatures;
- formula counts after signature hardening;
- damage evidence counts by evidence tier;
- raw/post-mitigation damage count after stronger evidence;
- percentage penetration regression result;
- tests/audits;
- frozen guard;
- git diff check;
- commits pushed;
- remaining blockers.

The goal is not to restore the old coverage numbers.

The goal is to make every remaining exact number defensible.
