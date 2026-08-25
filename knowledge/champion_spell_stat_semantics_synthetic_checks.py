"""Synthetic safety checks for Phase 2H."""

from knowledge.champion_spell_stat_semantics import (
    AMBIGUOUS,
    BONUS_STAT,
    CONTRADICTED,
    OWNER_UNRESOLVED,
    OWNER_VALIDATED_CASTER,
    SEMANTIC_REFERENCE_RESOLVED,
    SNAPSHOT_FIELD_UNAVAILABLE,
    STAT_FORMULA_UNRESOLVED_STATUS,
    STAT_ID_UNRESOLVED,
    STAT_OWNER_UNRESOLVED,
    STRONGLY_SUPPORTED,
    TOTAL_STAT,
    VALIDATED,
    build_formula_semantic_records,
    build_stat_semantic_records,
    compose_snapshot_reference,
    finalize_candidate_status,
    get_validated_stat_formula_mapping,
    get_validated_stat_mapping,
    inventory_ability_resource_calculations,
)


def _snapshot(**values):
    return {
        "stats": values,
        "stat_resolution": {
            name: {"status": "STATIC_STAT_RESOLVED"} for name in values
        },
    }


def main():
    checks = 0
    synthetic_stat_rows = [
        {"raw_mStat": raw_id, "champion_id": f"Fixture{raw_id}", "slot": "Q"}
        for raw_id in (1, 2, 12)
    ]
    stat_records = build_stat_semantic_records([0, 1, 2, 12, 13], synthetic_stat_rows)
    formula_records = build_formula_semantic_records([0, 1, 2, 99])

    assert get_validated_stat_mapping(stat_records)[2] == "ATTACK_DAMAGE"; checks += 1
    assert 13 not in get_validated_stat_mapping(stat_records); checks += 1
    assert get_validated_stat_formula_mapping(formula_records)[2] == BONUS_STAT; checks += 1
    assert 99 not in get_validated_stat_formula_mapping(formula_records); checks += 1

    unresolved_owner = compose_snapshot_reference(
        2, 2, OWNER_UNRESOLVED, stat_records, formula_records,
        caster_snapshot=_snapshot(attack_damage_bonus=50.0),
    )
    assert unresolved_owner["status"] == STAT_OWNER_UNRESOLVED; checks += 1
    assert set(get_validated_stat_formula_mapping(formula_records).values()) == {TOTAL_STAT, BONUS_STAT}; checks += 1

    assert 0 in stat_records and stat_records[0]["semantic_stat"] == "ABILITY_POWER"; checks += 1
    assert get_validated_stat_formula_mapping(formula_records)[0] == TOTAL_STAT; checks += 1

    no_fuzzy = compose_snapshot_reference(
        "2", 2, OWNER_VALIDATED_CASTER, stat_records, formula_records,
        caster_snapshot=_snapshot(attack_damage_bonus=50.0),
    )
    assert no_fuzzy["status"] == STAT_ID_UNRESOLVED; checks += 1

    excluded_records = {
        40: {"semantic_stat": "MANA", "status": AMBIGUOUS, "execution_eligible": False},
        41: {"semantic_stat": "MANA", "status": CONTRADICTED, "execution_eligible": False},
    }
    assert get_validated_stat_mapping(excluded_records) == {}; checks += 1
    assert 41 not in get_validated_stat_mapping(excluded_records); checks += 1

    resolved = compose_snapshot_reference(
        2, 2, OWNER_VALIDATED_CASTER, stat_records, formula_records,
        caster_snapshot=_snapshot(attack_damage_bonus=50.0),
    )
    assert resolved["status"] == SEMANTIC_REFERENCE_RESOLVED and resolved["value"] == 50.0; checks += 1

    unavailable = compose_snapshot_reference(
        2, 2, OWNER_VALIDATED_CASTER, stat_records, formula_records,
        caster_snapshot=_snapshot(attack_damage_total=100.0),
    )
    assert unavailable["status"] == SNAPSHOT_FIELD_UNAVAILABLE; checks += 1

    assert stat_records[2]["provenance"]["pinned_commit"] and stat_records[2]["evidence"]; checks += 1
    weak = finalize_candidate_status(
        VALIDATED,
        [{"tier": "ONE_WEAK_SOURCE", "key_name_only": False}],
        [],
    )
    assert weak == STRONGLY_SUPPORTED; checks += 1
    assert finalize_candidate_status(VALIDATED, [{"tier": "A"}, {"tier": "B"}], [{"blocking": True}]) == CONTRADICTED; checks += 1

    unknown_formula = compose_snapshot_reference(
        2, 99, OWNER_VALIDATED_CASTER, stat_records, formula_records,
        caster_snapshot=_snapshot(attack_damage_bonus=50.0),
    )
    assert unknown_formula["status"] == STAT_FORMULA_UNRESOLVED_STATUS; checks += 1
    assert formula_records[1]["status"] == CONTRADICTED and not formula_records[1]["execution_eligible"]; checks += 1

    # A zero enum is present, not false/missing, while lack of exact occurrences
    # keeps it below execution eligibility.
    assert stat_records[0]["status"] == STRONGLY_SUPPORTED and 0 not in get_validated_stat_mapping(stat_records); checks += 1

    synthetic_resource_catalog = {
        "records": {
            "X": {
                "primary_spells": [{
                    "champion_name": "X",
                    "slot": "Q",
                    "internal_spell_path": "Characters/X/Q",
                    "source_commit": "pinned",
                    "calculation_nodes": [{
                        "graph_path": "mSpellCalculations/X/mFormulaParts/0",
                        "raw_node_payload": {
                            "~class": "AbilityResourceByCoefficientCalculationPart",
                            "mAbilityResource": 0,
                            "mCoefficient": 0.1,
                        },
                    }],
                }],
            }
        }
    }
    resource_rows = inventory_ability_resource_calculations(synthetic_resource_catalog)
    assert resource_rows[0]["raw_mAbilityResource_present"] and resource_rows[0]["raw_mAbilityResource"] == 0; checks += 1

    print(f"Champion spell stat semantics synthetic checks: PASS ({checks}/{checks})")


if __name__ == "__main__":
    main()
