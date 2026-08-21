from __future__ import annotations

import math

from knowledge.combat_resistance_rules import (
    COMBAT_RESISTANCE_VERSION,
    PROVENANCE,
    SCOPE_LIMITATIONS,
    STATUS_BONUS_ARMOR_COMPONENT_REQUIRED,
    apply_resistance_to_damage,
    combine_percentages,
    resistance_damage_multiplier,
    resolve_armor,
    resolve_magic_resistance,
)


def build_audit():
    blocking = []
    review = []
    info = []

    multiplier_cases = 0
    previous_multiplier = None

    # Higher resistance must never increase the standard damage multiplier.
    for resistance in range(-200, 501, 5):
        multiplier = resistance_damage_multiplier(
            resistance
        )
        multiplier_cases += 1

        if not math.isfinite(multiplier):
            blocking.append(
                {
                    "kind": "NON_FINITE_MULTIPLIER",
                    "resistance": resistance,
                }
            )

        if multiplier <= 0 or multiplier >= 2:
            blocking.append(
                {
                    "kind": "MULTIPLIER_OUT_OF_RANGE",
                    "resistance": resistance,
                    "multiplier": multiplier,
                }
            )

        if (
            previous_multiplier is not None
            and multiplier > previous_multiplier + 1e-12
        ):
            blocking.append(
                {
                    "kind": "MULTIPLIER_NOT_MONOTONIC",
                    "resistance": resistance,
                    "multiplier": multiplier,
                    "previous_multiplier": previous_multiplier,
                }
            )

        previous_multiplier = multiplier

    armor_matrix_cases = 0

    for armor in (0, 10, 30, 60, 100, 200, 300):
        for flat_reduction in (0, 15):
            for pct_reduction in (0.0, 0.20):
                for pct_pen in (0.0, 0.30):
                    for lethality in (0, 18):
                        result = resolve_armor(
                            armor,
                            flat_reduction=flat_reduction,
                            percentage_reductions=(pct_reduction,),
                            percentage_penetrations=(pct_pen,),
                            lethality=lethality,
                        )
                        armor_matrix_cases += 1

                        if result.effective_resistance is None:
                            blocking.append(
                                {
                                    "kind": "UNEXPECTED_ARMOR_UNRESOLVED",
                                    "inputs": {
                                        "armor": armor,
                                        "flat_reduction": flat_reduction,
                                        "pct_reduction": pct_reduction,
                                        "pct_pen": pct_pen,
                                        "lethality": lethality,
                                    },
                                }
                            )
                            continue

                        damage = apply_resistance_to_damage(
                            1000,
                            "PHYSICAL",
                            effective_resistance=(
                                result.effective_resistance
                            ),
                        )

                        if not math.isfinite(
                            damage.post_mitigation_damage
                        ):
                            blocking.append(
                                {
                                    "kind": "NON_FINITE_PHYSICAL_DAMAGE",
                                    "inputs": {
                                        "armor": armor,
                                        "flat_reduction": flat_reduction,
                                        "pct_reduction": pct_reduction,
                                        "pct_pen": pct_pen,
                                        "lethality": lethality,
                                    },
                                }
                            )

    magic_matrix_cases = 0

    for mr in (0, 10, 30, 60, 100, 200, 300):
        for flat_reduction in (0, 15):
            for pct_reduction in (0.0, 0.20):
                for pct_pen in (0.0, 0.30):
                    for flat_pen in (0, 18):
                        result = resolve_magic_resistance(
                            mr,
                            flat_reduction=flat_reduction,
                            percentage_reductions=(pct_reduction,),
                            percentage_penetrations=(pct_pen,),
                            flat_penetration=flat_pen,
                        )
                        magic_matrix_cases += 1

                        if result.effective_resistance is None:
                            blocking.append(
                                {
                                    "kind": "UNEXPECTED_MR_UNRESOLVED",
                                }
                            )
                            continue

                        damage = apply_resistance_to_damage(
                            1000,
                            "MAGIC",
                            effective_resistance=(
                                result.effective_resistance
                            ),
                        )

                        if not math.isfinite(
                            damage.post_mitigation_damage
                        ):
                            blocking.append(
                                {
                                    "kind": "NON_FINITE_MAGIC_DAMAGE",
                                }
                            )

    # Bonus armor penetration must never be silently guessed without a base /
    # bonus split.
    unresolved = resolve_armor(
        120,
        percentage_bonus_armor_penetrations=(0.30,),
    )
    if (
        unresolved.status
        != STATUS_BONUS_ARMOR_COMPONENT_REQUIRED
        or unresolved.effective_resistance is not None
    ):
        blocking.append(
            {
                "kind": "BONUS_ARMOR_COMPONENT_GUARD_FAILED",
            }
        )

    # Lethality is current flat armor penetration, not old level-scaled
    # lethality. There is deliberately no attacker-level argument in the API.
    lethality_case = resolve_armor(
        100,
        lethality=20,
    )
    if lethality_case.effective_resistance != 80:
        blocking.append(
            {
                "kind": "LETHALITY_NOT_ONE_TO_ONE",
                "value": lethality_case.effective_resistance,
            }
        )

    # Precision anchors.
    wiki_example = resolve_armor(
        300,
        base_armor=100,
        flat_reduction=30,
        percentage_reductions=(0.30,),
        percentage_bonus_armor_penetrations=(0.45,),
        flat_penetration=10,
    )
    if not math.isclose(
        wiki_example.effective_resistance,
        122.3,
        abs_tol=1e-9,
    ):
        blocking.append(
            {
                "kind": "WIKI_ARMOR_ORDER_ANCHOR_FAILED",
                "value": wiki_example.effective_resistance,
            }
        )

    negative_example = resolve_armor(
        18,
        flat_reduction=30,
        percentage_reductions=(0.30,),
        percentage_penetrations=(0.45,),
        flat_penetration=10,
    )
    if negative_example.effective_resistance != -12:
        blocking.append(
            {
                "kind": "NEGATIVE_REDUCTION_ANCHOR_FAILED",
                "value": negative_example.effective_resistance,
            }
        )

    stacked = combine_percentages((0.40, 0.35))
    if not math.isclose(stacked, 0.61, abs_tol=1e-12):
        blocking.append(
            {
                "kind": "MULTIPLICATIVE_PERCENT_STACKING_FAILED",
                "value": stacked,
            }
        )

    true_case = apply_resistance_to_damage(
        777,
        "TRUE",
    )
    if true_case.post_mitigation_damage != 777:
        blocking.append(
            {
                "kind": "TRUE_DAMAGE_RESISTANCE_BYPASS_FAILED",
            }
        )

    info.extend(
        [
            {
                "kind": "LETHALITY_CURRENT_RULE",
                "message": (
                    "1 lethality = 1 flat armor penetration; old "
                    "level-scaling is intentionally not implemented."
                ),
            },
            {
                "kind": "BONUS_ARMOR_PROVENANCE_GUARD",
                "message": (
                    "Bonus armor penetration requires a known base/bonus "
                    "armor split and otherwise returns an explicit unresolved "
                    "status."
                ),
            },
            {
                "kind": "OUT_OF_SCOPE",
                "message": SCOPE_LIMITATIONS,
            },
        ]
    )

    return {
        "version": COMBAT_RESISTANCE_VERSION,
        "multiplier_cases": multiplier_cases,
        "armor_matrix_cases": armor_matrix_cases,
        "magic_matrix_cases": magic_matrix_cases,
        "blocking": blocking,
        "review": review,
        "info": info,
        "provenance": PROVENANCE,
    }


def render_audit(audit):
    lines = [
        "=" * 76,
        "COMBAT RESISTANCE / PENETRATION RULES - FULL AUDIT",
        "=" * 76,
        f"Version                  : {audit['version']}",
        f"Resistance multiplier   : {audit['multiplier_cases']} cases",
        f"Armor matrix            : {audit['armor_matrix_cases']} cases",
        f"Magic resistance matrix : {audit['magic_matrix_cases']} cases",
        f"Blocking issues         : {len(audit['blocking'])}",
        f"Review items            : {len(audit['review'])}",
        "",
        "PROVENANCE",
        "-" * 76,
        (
            "- Resistance formula     : "
            f"{audit['provenance']['resistance_damage_formula']['status']}"
        ),
        (
            "- Penetration order      : "
            f"{audit['provenance']['penetration_order']['status']}"
        ),
        (
            "- Lethality 1:1          : "
            f"{audit['provenance']['lethality']['status']}"
        ),
    ]

    if audit["blocking"]:
        lines.extend(
            [
                "",
                "BLOCKING ISSUES",
                "-" * 76,
            ]
        )
        for issue in audit["blocking"][:50]:
            lines.append(f"[FAIL] {issue}")

    if audit["review"]:
        lines.extend(
            [
                "",
                "REVIEW ITEMS",
                "-" * 76,
            ]
        )
        for issue in audit["review"]:
            lines.append(f"[REVIEW] {issue}")

    lines.extend(
        [
            "",
            "ACCEPTED SCOPE / INFORMATION",
            "-" * 76,
        ]
    )
    for issue in audit["info"]:
        lines.append(
            f"[INFO] {issue['kind']}: {issue['message']}"
        )

    status = (
        "FAIL"
        if audit["blocking"]
        else "REVIEW_REQUIRED"
        if audit["review"]
        else "PASS"
    )
    lines.extend(["", f"STATUS : {status}"])

    return "\n".join(lines)


def main():
    audit = build_audit()
    print(render_audit(audit))

    if audit["blocking"]:
        return 2
    if audit["review"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
