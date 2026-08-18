# ZiRcoN Coach — TODO

## Current task
COMPLETED — Phase 2B1 — Patch-aware Champion Knowledge Base.

## Status

Completed by Codex on 2026-08-18.

Result: REVIEW_REQUIRED.

Champion Knowledge Base Phase 2B1 is implemented and tested, but not FROZEN.

No next major task is defined here; project review should decide whether Phase 2B1 is freeze-ready and define any next step.

## Goal

Build a generic, patch-aware factual knowledge layer for every League of
Legends champion.

The goal is to know:

- champion identity;
- base stats;
- stat growth fields;
- passive;
- abilities;
- cooldown/cost/range data when exposed;
- raw tooltips;
- raw spell variables/effects;
- factual kit mechanics with evidence;
- semantic completeness / uncertainty.

This phase does NOT calculate combat damage yet.

It must create a trustworthy champion-data foundation for future:

- rune knowledge;
- spell formula resolution;
- damage simulation;
- Burst / TTK;
- composition analysis;
- contextual item reasoning.

---

# Architecture

Preferred files:

knowledge/
├── champion_knowledge.py
├── champion_knowledge_synthetic_checks.py
└── champion_knowledge_precision_checks.py

Keep this layer UI-agnostic.

Do NOT modify frozen analyzers.

Adding new backward-compatible Data Dragon champion helper functions to
riot/data_dragon.py is allowed only if necessary.

If riot/data_dragon.py is modified:

- do not alter existing item functions;
- rerun existing Item Knowledge tests;
- Phase 2A behavior must remain unchanged.

---

# Part A — Patch-aware Champion Data Dragon source

Use Data Dragon champion data.

Load:

1. champion.json
2. individual champion JSON for every champion

Every record must preserve:

- requested game version
- resolved Data Dragon version
- version resolution status
- fallback status
- locale
- raw champion JSON

Do not silently use latest data when an older patch was requested.

Reuse the same version-resolution philosophy as frozen Item Knowledge.

---

# Part B — Champion identity

For every champion preserve factual identity fields where exposed:

- numeric champion key
- internal ID
- display name
- title
- tags
- partype/resource type
- info fields
- image metadata
- lore/blurb if desired for raw completeness

Do not derive gameplay recommendations from Riot tags.

Example:

"Tank"
!= automatically durable in every game state

"Assassin"
!= automatically high burst at every level

Tags are factual source metadata only.

---

# Part C — Base stats

Build a canonical champion stat record.

Preserve raw Data Dragon stat fields and provenance.

At minimum include where exposed:

- HP base
- HP per level
- HP regeneration
- HP regeneration per level
- mana/resource base
- mana/resource per level
- resource regeneration
- resource regeneration per level
- attack damage
- attack damage per level
- attack speed
- attack speed per level
- armor
- armor per level
- magic resistance
- magic resistance per level
- movement speed
- attack range
- crit
- crit per level

Every normalized field must store:

- canonical stat
- raw source field
- value
- source
- confidence
- Data Dragon version

Preserve unmapped stat fields instead of discarding them.

---

# Important — Do NOT calculate level stats yet unless formally justified

This phase stores base stats + growth fields.

Do NOT assume:

base + growth × (level - 1)

unless Riot-supported or otherwise project-reviewed exact level-growth
semantics have been established.

Future Damage / Combat Engine requires exact level-resolved stats, so false
precision here would be worse than deferring the calculation.

For Phase 2B1:

store the factual growth fields.

Level-resolved stat formulas belong to a later validated formula layer.

---

# Part D — Passive knowledge

For every champion preserve:

- passive name
- raw description
- cleaned description
- image
- source/version
- semantic parser status
- extracted factual mechanics
- unparsed / partially parsed text

Do NOT assume the passive description exposes every internal numeric rule.

---

# Part E — Ability records

Build an auditable record for every Data Dragon spell.

Preserve all available fields such as:

- array/index position
- spell ID
- spell name
- raw description
- raw tooltip
- cleaned description
- cleaned tooltip
- max rank
- cooldown
- cooldownBurn
- cost
- costBurn
- costType
- resource
- range
- rangeBurn
- effect
- effectBurn
- vars
- image
- any other raw fields

Never discard fields simply because the current code does not understand them.

---

# Part F — Q / W / E / R assignment

Do not blindly pretend Data Dragon contains an explicit keyboard key if it
does not.

Preserve:

- spell array index
- inferred slot from Data Dragon order when applicable
- slot provenance

Suggested:

slot = Q / W / E / R
slot_source = DDRAGON_ARRAY_ORDER

Audit all champions.

Report:

- champions with exactly 4 spells
- champions with unusual spell counts
- records where slot assignment cannot safely be made

If a champion cannot be represented by normal four-spell ordering:

do not fabricate a normal kit.

Mark explicit complexity / uncertainty.

---

# Part G — Tooltip placeholder resolution

Implement factual resolution support for Riot Data Dragon placeholders where
the data is actually available.

Examples conceptually:

{{ eN }}
→ effectBurn[N]

{{ aN }}
{{ fN }}
→ corresponding vars entry when resolvable

Preserve BOTH:

- original tooltip
- resolved/annotated representation

Do not destroy the original placeholders.

For every placeholder record:

- placeholder
- resolved value if known
- source field
- resolution status

Example statuses:

RESOLVED_EFFECT_BURN
RESOLVED_VAR
UNRESOLVED_VAR
UNKNOWN_PLACEHOLDER

Do not infer missing coefficients.

---

# Part H — Formula fragments

This is NOT the Damage Engine.

However, preserve structured formula fragments when Data Dragon explicitly
provides them.

Examples:

- rank-value array
- AP ratio
- AD ratio
- bonus AD ratio
- target HP scaling if explicitly represented
- self HP scaling if explicitly represented

Every formula fragment must preserve provenance.

Do NOT attempt to evaluate final spell damage.

Do NOT combine all fragments into a final combat formula yet.

If Data Dragon information is incomplete:

mark FORMULA_INCOMPLETE.

This distinction is critical for the future Combat Engine.

---

# Part I — Champion/ability semantic taxonomy

Build a conservative factual semantic layer.

Possible mechanic families include:

Damage:
- PHYSICAL_DAMAGE
- MAGIC_DAMAGE
- TRUE_DAMAGE
- DAMAGE_TYPE_UNRESOLVED
- PERCENT_MAX_HEALTH_DAMAGE
- PERCENT_CURRENT_HEALTH_DAMAGE
- MISSING_HEALTH_DAMAGE
- EXECUTE

Sustain / defense:
- HEAL
- SHIELD
- DAMAGE_REDUCTION
- INVULNERABLE
- UNTARGETABLE

Mobility:
- DASH
- BLINK
- MOVE_SPEED
- DISPLACEMENT_SELF

Crowd control:
- SLOW
- STUN
- ROOT
- KNOCKUP
- KNOCKBACK
- FEAR
- CHARM
- TAUNT
- SILENCE
- SUPPRESSION
- SLEEP
- GROUND

Visibility / targeting:
- STEALTH
- CAMOUFLAGE
- REVEAL

Combat mechanics:
- ATTACK_RESET
- ON_HIT
- STACKING
- TRANSFORMATION
- MARK
- EMPOWERED_ATTACK
- RESET_OR_REFRESH
- SPECIAL_RESOURCE

This taxonomy is descriptive only.

Do NOT create:

- BURST_CHAMPION
- GOOD_VS_TANK
- BAD_VS_SQUISHY
- STRONG_EARLY
- STRONG_LATE
- DUELIST_SCORE
- THREAT_SCORE

Those are future reasoning outputs.

---

# Part J — Semantic evidence rules

Use the same conservative methodology accepted for Item Knowledge.

Every semantic effect requires:

- effect_type
- source
- evidence_text
- confidence
- Data Dragon version

Confidence concept:

- STRUCTURED
- DESCRIPTION_EXPLICIT
- HEURISTIC
- UNKNOWN

Prefer DESCRIPTION_EXPLICIT / UNKNOWN over aggressive heuristics.

Raw tooltip/description must always remain available.

---

# Part K — Full / partial / unparsed semantics

Champion spell/passive descriptions can contain many mechanics in one sentence.

Reuse the frozen Item Knowledge philosophy:

- FULLY_PARSED
- PARTIALLY_PARSED
- COMPLETELY_UNPARSED
- UNSUPPORTED_LOCALE

A recognized word must never make an entire complex ability appear fully understood.

Preserve unresolved clauses.

No silent source-text loss.

Parser locale contract:

fr_FR supported for semantic text parsing.

Other locales:
raw structured data remains available,
but semantic text parsing must report UNSUPPORTED_LOCALE unless explicitly
implemented and validated later.

---

# Part L — Champion complexity audit

Champion kits can contain transformations, alternate forms, copied abilities,
weapon systems, or other structures that a simple four-spell record may not
fully represent.

Do NOT solve every exceptional champion with champion-specific hacks.

Create generic factual complexity flags.

Examples:

- STANDARD_KIT
- ALTERNATE_FORM_POSSIBLE
- MULTI_FORM_KIT
- EXTRA_ABILITY_STRUCTURE
- COPIED_OR_DYNAMIC_ABILITY
- DATA_DRAGON_KIT_INCOMPLETE
- COMPLEX_KIT_UNDERMODELED

Use only when evidence supports them.

Audit unusual champions rather than forcing them into normal assumptions.

The general Champion Knowledge architecture must remain champion-agnostic.

---

# Part M — Full catalog audit

Run against every champion in the current resolved Data Dragon version.

Report:

- resolved Data Dragon version
- total champions
- individual champion files successfully loaded
- missing champion detail files
- champions with normalized base stats
- passive records
- total spells
- spell-count distribution
- champions not represented as normal 4-spell kits
- placeholders total
- resolved eN placeholders
- resolved aN/fN placeholders
- unresolved placeholders
- complete/incomplete formula fragments
- semantic effects by type
- FULLY_PARSED sections
- PARTIALLY_PARSED sections
- COMPLETELY_UNPARSED sections
- unsupported-locale sections
- complexity flags
- metadata warnings

Do not optimize counts.

Transparency is the objective.

---

# Part N — Representative champion diagnostics

Mandatory diagnostics:

Primary practical champions:
- Shyvana
- Bel'Veth
- Dr. Mundo
- Rammus
- Viego

Also include complex-kit examples where available in current Data Dragon:

- at least one transformation / alternate-form champion
- at least one unusually complex ability-structure champion
- at least one champion with significant shields/healing
- at least one champion with true damage
- at least one champion with hard CC
- at least one champion with mixed damage

For every diagnostic print:

- identity
- base stats
- raw growth fields
- passive
- Q/W/E/R or available spell structure
- raw tooltip
- placeholder resolution
- formula fragments
- semantic mechanics
- parse completeness
- unresolved information
- complexity flags

Do not judge champion strength.

---

# Part O — Synthetic tests

Add deterministic no-network tests for:

- champion identity
- base stat normalization
- unknown raw stat preservation
- passive parsing
- 4-spell normal kit
- unusual spell count
- QWER provenance
- eN placeholder resolution
- aN/fN variable resolution
- unresolved placeholder preservation
- cooldown/cost/range preservation
- physical damage semantic extraction
- magic damage semantic extraction
- true damage semantic extraction
- heal
- shield
- hard CC
- mobility
- percent-HP mechanic
- same-sentence partial parsing
- completely unparsed text
- unsupported locale
- complex-kit flag
- malformed/missing fields

No network dependency for synthetic tests.

---

# Part P — Frozen boundaries

Do NOT modify:

- Death Analyzer v11
- Jungle Tempo / Pathing v17
- Objective Analyzer v20
- Recall / Reset Analyzer v21
- Build / Itemization Analyzer v22 Phase 1
- Item Knowledge Base Phase 2A

If a real correctness issue is discovered in a frozen layer:

do not silently modify it.

Return REVIEW_REQUIRED.

---

# Do NOT implement yet

Do NOT implement:

- champion recommendations
- champion pick scoring
- composition scoring
- rune knowledge
- exact level-resolved champion stats
- executable spell damage formulas
- damage simulation
- combo simulation
- Burst / TTK
- time-to-kill graphs
- enemy threat score
- contextual build recommendations
- item-vs-champion recommendation logic
- ML

---

# Future Combat Engine requirement

Phase 2B1 must preserve enough factual information for a later engine to ask:

"Given champion X at level Y with these stats/items/runes,
what formulas are needed to compute damage?"

But Phase 2B1 must NOT answer the damage question itself.

Preserve data now.
Evaluate formulas later.

---

# Testing

Run:

- py_compile
- Champion Knowledge synthetic checks
- Champion Knowledge precision checks
- full real Data Dragon champion catalog audit
- representative champion diagnostics

If riot/data_dragon.py changes:
also rerun existing frozen Item Knowledge synthetic/precision tests to prove
backward compatibility.

No main.py run unless dev-harness integration is deliberately added.

---

# Reporting

Update:

- PROJECT_STATE.md
- TODO.md → COMPLETED
- LAST_RUN.md

Do NOT mark Phase 2B FROZEN yourself.

Finish with:

REVIEW_REQUIRED

LAST_RUN must report:

- files changed
- tests
- version resolution
- champion count
- detail-file coverage
- stat coverage
- spell-count distribution
- placeholder resolution
- formula completeness
- semantic coverage
- parsing completeness
- complexity findings
- representative diagnostics
- limitations
- whether Phase 2B1 appears freeze-ready

---

# Git

Commit and push tested work.

Suggested commit:

Build patch-aware champion knowledge base
