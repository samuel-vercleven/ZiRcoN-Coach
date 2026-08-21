from __future__ import annotations

import math

from knowledge.combat_resistance_rules import (
    STATUS_BONUS_ARMOR_COMPONENT_REQUIRED,
    STATUS_RESOLVED,
    STATUS_TRUE_DAMAGE_BYPASS,
    apply_resistance_to_damage,
    combine_percentages,
    resistance_damage_multiplier,
    resolve_armor,
    resolve_magic_resistance,
)


def test_percentage_stacking_is_multiplicative():
    assert math.isclose(
        combine_percentages((0.30, 0.20)),
        0.44,
        abs_tol=1e-12,
    )


def test_positive_resistance_multiplier():
    assert math.isclose(
        resistance_damage_multiplier(100),
        0.5,
        abs_tol=1e-12,
    )


def test_negative_resistance_multiplier():
    assert math.isclose(
        resistance_damage_multiplier(-100),
        1.5,
        abs_tol=1e-12,
    )


def test_flat_penetration_cannot_create_negative_armor():
    result = resolve_armor(
        30,
        flat_penetration=40,
    )
    assert result.status == STATUS_RESOLVED
    assert result.effective_resistance == 0


def test_flat_reduction_can_create_negative_armor():
    result = resolve_armor(
        10,
        flat_reduction=25,
        percentage_penetrations=(0.50,),
        flat_penetration=100,
    )
    assert result.effective_resistance == -15
    assert result.stopped_after_negative_reduction is True


def test_lethality_is_one_to_one_flat_penetration():
    result = resolve_armor(
        100,
        lethality=18,
    )
    assert result.effective_resistance == 82


def test_bonus_armor_pen_requires_component_split():
    result = resolve_armor(
        100,
        percentage_bonus_armor_penetrations=(0.30,),
    )
    assert result.status == STATUS_BONUS_ARMOR_COMPONENT_REQUIRED
    assert result.effective_resistance is None


def test_bonus_armor_pen_affects_only_bonus_component():
    result = resolve_armor(
        100,
        base_armor=40,
        percentage_bonus_armor_penetrations=(0.50,),
    )
    assert math.isclose(
        result.effective_resistance,
        70,
        abs_tol=1e-12,
    )


def test_magic_pen_order():
    result = resolve_magic_resistance(
        100,
        flat_reduction=20,
        percentage_reductions=(0.25,),
        percentage_penetrations=(0.40,),
        flat_penetration=18,
    )
    assert math.isclose(
        result.effective_resistance,
        18,
        abs_tol=1e-12,
    )


def test_true_damage_bypasses_resistance():
    result = apply_resistance_to_damage(
        500,
        "TRUE",
    )
    assert result.status == STATUS_TRUE_DAMAGE_BYPASS
    assert result.post_mitigation_damage == 500


def test_physical_damage_uses_final_armor():
    result = apply_resistance_to_damage(
        1000,
        "PHYSICAL",
        effective_resistance=100,
    )
    assert math.isclose(
        result.post_mitigation_damage,
        500,
        abs_tol=1e-12,
    )


def test_magic_damage_uses_final_mr():
    result = apply_resistance_to_damage(
        1000,
        "MAGIC",
        effective_resistance=25,
    )
    assert math.isclose(
        result.post_mitigation_damage,
        800,
        abs_tol=1e-12,
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
        "Combat Resistance synthetic checks: "
        f"PASS ({len(tests)}/{len(tests)})"
    )


if __name__ == "__main__":
    main()
