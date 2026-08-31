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
```

---

# 3. Completion status

`COMPLETED / REVIEW_REQUIRED FOR FREEZE`

Phase 2H v1 is implemented and technically validated. The final stack covers compilation, 21/21 synthetic checks, 31/31 precision assertions, provenance research, the exact 885-occurrence inventory, the full real semantics audit, `python main.py`, and the FROZEN guard.

Validated execution-map semantics remain deliberately limited to:

- `mStat 1 -> ARMOR`;
- `mStat 2 -> ATTACK_DAMAGE`;
- `mStat 12 -> HEALTH`;
- `mStatFormula 0 -> TOTAL_STAT`;
- `mStatFormula 2 -> BONUS_STAT`.

Raw stat IDs 13, 14, 15, and 16, formula value 1, resource enum semantics, and all real owner identities remain non-executable or unresolved. Phase 2G v2 was not modified. Phase 2I was not started.

Project review decides whether Phase 2H v1 is ready to freeze.
