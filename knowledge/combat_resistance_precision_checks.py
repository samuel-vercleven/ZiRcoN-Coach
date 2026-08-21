from __future__ import annotations

import math

from knowledge.combat_resistance_rules import (
    COMBAT_RESISTANCE_VERSION,
    PROVENANCE,
    apply_resistance_to_damage,
    combine_percentages,
    resolve_armor,
    resolve_magic_resistance,
)


def _stage(result, name):
    for stage in result.stages:
        if stage.name == name:
            return stage
    raise AssertionError(f"Missing stage {name}")


def test_wiki_armor_penetration_example_300_to_122_3():
    # Community-documented example:
    # 300 armor = 100 base + 200 bonus
    # 30 flat reduction -> 90 + 180
    # 30% reduction -> 63 + 126
    # 45% bonus armor penetration -> 63 + 69.3
    # 10 flat penetration -> 122.3
    result = resolve_armor(
        300,
        base_armor=100,
        flat_reduction=30,
        percentage_reductions=(0.30,),
        percentage_bonus_armor_penetrations=(0.45,),
        flat_penetration=10,
    )

    assert math.isclose(
        result.effective_resistance,
        122.3,
        abs_tol=1e-9,
    )


def test_wiki_negative_armor_example_stops_after_reduction():
    # 18 armor - 30 flat reduction = -12. Further penetration is ignored.
    result = resolve_armor(
        18,
        flat_reduction=30,
        percentage_reductions=(0.30,),
        percentage_penetrations=(0.45,),
        flat_penetration=10,
    )

    assert math.isclose(
        result.effective_resistance,
        -12,
        abs_tol=1e-12,
    )
    assert result.stopped_after_negative_reduction


def test_lethality_current_rule_has_no_level_parameter():
    # Riot Patch 14.1: 1 lethality = 1 flat armor penetration.
    result = resolve_armor(
        80,
        lethality=18,
    )
    assert result.effective_resistance == 62


def test_total_and_bonus_percent_penetration_compose():
    result = resolve_armor(
        60,
        base_armor=20,
        percentage_bonus_armor_penetrations=(0.30,),
        percentage_penetrations=(0.10,),
    )

    # 20 * .9 + 40 * .7 * .9 = 43.2
    assert math.isclose(
        result.effective_resistance,
        43.2,
        abs_tol=1e-12,
    )


def test_multiple_percent_penetrations_stack_multiplicatively():
    assert math.isclose(
        combine_percentages((0.40, 0.35)),
        0.61,
        abs_tol=1e-12,
    )


def test_flat_reduction_split_preserves_armor_components():
    result = resolve_armor(
        300,
        base_armor=100,
        flat_reduction=30,
    )
    stage = _stage(
        result,
        "AFTER_FLAT_REDUCTION",
    )

    assert math.isclose(stage.base_component, 90)
    assert math.isclose(stage.bonus_component, 180)


def test_magic_and_armor_use_same_positive_resistance_multiplier():
    physical = apply_resistance_to_damage(
        1000,
        "PHYSICAL",
        effective_resistance=60,
    )
    magic = apply_resistance_to_damage(
        1000,
        "MAGIC",
        effective_resistance=60,
    )

    assert math.isclose(
        physical.post_mitigation_damage,
        magic.post_mitigation_damage,
        abs_tol=1e-12,
    )


def test_negative_reduction_can_amplify_damage():
    armor = resolve_armor(
        10,
        flat_reduction=25,
    )
    damage = apply_resistance_to_damage(
        100,
        "PHYSICAL",
        effective_resistance=armor.effective_resistance,
    )

    assert damage.post_mitigation_damage > 100


def test_flat_magic_penetration_clamps_at_zero():
    result = resolve_magic_resistance(
        12,
        flat_penetration=20,
    )
    assert result.effective_resistance == 0


def test_provenance_contract_is_explicit():
    assert COMBAT_RESISTANCE_VERSION == "combat_resistance_phase2e_v1"
    assert PROVENANCE["lethality"]["status"] == "RIOT_OFFICIAL"
    assert (
        PROVENANCE["resistance_damage_formula"]["status"]
        == "COMMUNITY_DOCUMENTED"
    )


def main():
    tests = sorted(
        (name, fn)
        for name, fn in globals().items()
        if name.startswith("test_") and callable(fn)
    )

    for _name, fn in tests:
        fn()

    print(
        "Combat Resistance precision checks: "
        f"PASS ({len(tests)}/{len(tests)})"
    )


if __name__ == "__main__":
    main()
