from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Literal


COMBAT_RESISTANCE_VERSION = "combat_resistance_phase2e_v1"

DamageType = Literal["PHYSICAL", "MAGIC", "TRUE"]

STATUS_RESOLVED = "RESOLVED"
STATUS_TRUE_DAMAGE_BYPASS = "TRUE_DAMAGE_BYPASS"
STATUS_BONUS_ARMOR_COMPONENT_REQUIRED = "BONUS_ARMOR_COMPONENT_REQUIRED"

PROVENANCE = {
    "resistance_damage_formula": {
        "status": "COMMUNITY_DOCUMENTED",
        "source": "League of Legends Wiki - Armor / Magic resistance",
        "armor_url": "https://leagueoflegends.fandom.com/wiki/Armor",
        "magic_resistance_url": (
            "https://leagueoflegends.fandom.com/wiki/Magic_resistance"
        ),
        "contract": (
            "For non-negative resistance, multiplier = 100/(100+R). "
            "For negative resistance, multiplier = 2 - 100/(100-R)."
        ),
    },
    "penetration_order": {
        "status": "COMMUNITY_DOCUMENTED",
        "source": (
            "League of Legends Wiki - Armor penetration / Magic penetration"
        ),
        "armor_url": (
            "https://leagueoflegends.fandom.com/wiki/Armor_penetration"
        ),
        "magic_penetration_url": (
            "https://leagueoflegends.fandom.com/wiki/Magic_penetration"
        ),
        "contract": (
            "Flat resistance reduction -> percentage resistance reduction -> "
            "percentage penetration -> flat penetration. Bonus armor "
            "penetration is tracked separately against the bonus-armor "
            "component before total percent armor penetration."
        ),
    },
    "lethality": {
        "status": "RIOT_OFFICIAL",
        "source": "Riot Games Patch 14.1 Notes",
        "url": (
            "https://www.leagueoflegends.com/en-us/news/game-updates/"
            "patch-14-1-notes/"
        ),
        "contract": (
            "Since patch 14.1, 1 lethality grants 1 flat armor penetration "
            "at every level."
        ),
    },
}

SCOPE_LIMITATIONS = (
    "This module resolves resistance/reduction/penetration math only. "
    "It does not execute champion spell formulas, item/rune effects, "
    "damage amplification/reduction modifiers, shields, critical strikes, "
    "on-hit effects, executes, healing, or Burst/TTK."
)


@dataclass(frozen=True)
class ResistanceStage:
    name: str
    value: float
    base_component: float | None = None
    bonus_component: float | None = None


@dataclass(frozen=True)
class ResistanceResolution:
    status: str
    resistance_type: str
    original_resistance: float
    effective_resistance: float | None
    stages: tuple[ResistanceStage, ...]
    stopped_after_negative_reduction: bool
    percentage_reduction_combined: float
    percentage_penetration_combined: float
    percentage_bonus_armor_penetration_combined: float
    flat_reduction: float
    flat_penetration: float
    lethality: float
    provenance_version: str = COMBAT_RESISTANCE_VERSION


@dataclass(frozen=True)
class DamageResolution:
    status: str
    damage_type: DamageType
    raw_damage: float
    effective_resistance: float | None
    resistance_multiplier: float
    post_mitigation_damage: float
    provenance_version: str = COMBAT_RESISTANCE_VERSION


def _finite_number(value: float, name: str) -> float:
    numeric = float(value)
    if not isfinite(numeric):
        raise ValueError(f"{name} must be finite")
    return numeric


def _non_negative(value: float, name: str) -> float:
    numeric = _finite_number(value, name)
    if numeric < 0:
        raise ValueError(f"{name} must be >= 0")
    return numeric


def _fractions(values: Iterable[float], name: str) -> tuple[float, ...]:
    result = []
    for index, value in enumerate(values):
        numeric = _finite_number(value, f"{name}[{index}]")
        if numeric < 0 or numeric > 1:
            raise ValueError(
                f"{name}[{index}] must be a fraction between 0 and 1"
            )
        result.append(numeric)
    return tuple(result)


def combine_percentages(values: Iterable[float]) -> float:
    """
    Combine independent percentage reductions/penetrations multiplicatively.

    Example:
        30% and 20% -> 1 - (0.70 * 0.80) = 44%.
    """
    fractions = _fractions(values, "values")
    remaining = 1.0
    for value in fractions:
        remaining *= 1.0 - value
    return 1.0 - remaining


def resistance_damage_multiplier(resistance: float) -> float:
    """
    Convert final effective armor/MR to the standard LoL damage multiplier.

    Penetration normally cannot create negative effective resistance.
    Negative values remain possible when a resistance-reduction effect itself
    reduces a target below zero, so the negative branch is intentionally kept.
    """
    resistance = _finite_number(resistance, "resistance")

    if resistance >= 0:
        return 100.0 / (100.0 + resistance)

    return 2.0 - (100.0 / (100.0 - resistance))


def _proportional_flat_reduction(
    base_component: float,
    bonus_component: float,
    flat_reduction: float,
) -> tuple[float, float]:
    total = base_component + bonus_component
    if flat_reduction == 0:
        return base_component, bonus_component

    if total <= 0:
        # Once total resistance is already non-positive, later percent and
        # penetration layers are not applied. The precise component split no
        # longer changes damage math, so keep the full additional reduction on
        # the aggregate by assigning it to the base component.
        return base_component - flat_reduction, bonus_component

    scale = (total - flat_reduction) / total
    return base_component * scale, bonus_component * scale


def resolve_armor(
    total_armor: float,
    *,
    base_armor: float | None = None,
    flat_reduction: float = 0.0,
    percentage_reductions: Iterable[float] = (),
    percentage_bonus_armor_penetrations: Iterable[float] = (),
    percentage_penetrations: Iterable[float] = (),
    flat_penetration: float = 0.0,
    lethality: float = 0.0,
) -> ResistanceResolution:
    total_armor = _finite_number(total_armor, "total_armor")
    flat_reduction = _non_negative(flat_reduction, "flat_reduction")
    flat_penetration = _non_negative(flat_penetration, "flat_penetration")
    lethality = _non_negative(lethality, "lethality")

    reductions = _fractions(
        percentage_reductions,
        "percentage_reductions",
    )
    bonus_penetrations = _fractions(
        percentage_bonus_armor_penetrations,
        "percentage_bonus_armor_penetrations",
    )
    penetrations = _fractions(
        percentage_penetrations,
        "percentage_penetrations",
    )

    reduction_combined = combine_percentages(reductions)
    bonus_pen_combined = combine_percentages(bonus_penetrations)
    pen_combined = combine_percentages(penetrations)

    if base_armor is None:
        if bonus_pen_combined > 0:
            return ResistanceResolution(
                status=STATUS_BONUS_ARMOR_COMPONENT_REQUIRED,
                resistance_type="ARMOR",
                original_resistance=total_armor,
                effective_resistance=None,
                stages=(
                    ResistanceStage(
                        "ORIGINAL",
                        total_armor,
                    ),
                ),
                stopped_after_negative_reduction=False,
                percentage_reduction_combined=reduction_combined,
                percentage_penetration_combined=pen_combined,
                percentage_bonus_armor_penetration_combined=(
                    bonus_pen_combined
                ),
                flat_reduction=flat_reduction,
                flat_penetration=flat_penetration,
                lethality=lethality,
            )

        base_component = None
        bonus_component = None
    else:
        base_armor = _finite_number(base_armor, "base_armor")
        if base_armor < 0:
            raise ValueError("base_armor must be >= 0")
        if total_armor >= 0 and base_armor > total_armor + 1e-9:
            raise ValueError(
                "base_armor cannot exceed non-negative total_armor "
                "before reductions"
            )

        base_component = base_armor
        bonus_component = total_armor - base_armor

    stages: list[ResistanceStage] = [
        ResistanceStage(
            "ORIGINAL",
            total_armor,
            base_component,
            bonus_component,
        )
    ]

    # 1. Flat resistance reduction.
    if base_component is None:
        current = total_armor - flat_reduction
    else:
        base_component, bonus_component = _proportional_flat_reduction(
            base_component,
            bonus_component,
            flat_reduction,
        )
        current = base_component + bonus_component

    stages.append(
        ResistanceStage(
            "AFTER_FLAT_REDUCTION",
            current,
            base_component,
            bonus_component,
        )
    )

    # A flat reduction is the layer that can drive resistance below zero.
    # Once non-positive, percentage reductions and penetration do not create
    # an additional benefit and are intentionally skipped.
    if current <= 0:
        return ResistanceResolution(
            status=STATUS_RESOLVED,
            resistance_type="ARMOR",
            original_resistance=total_armor,
            effective_resistance=current,
            stages=tuple(stages),
            stopped_after_negative_reduction=True,
            percentage_reduction_combined=reduction_combined,
            percentage_penetration_combined=pen_combined,
            percentage_bonus_armor_penetration_combined=bonus_pen_combined,
            flat_reduction=flat_reduction,
            flat_penetration=flat_penetration,
            lethality=lethality,
        )

    # 2. Percentage resistance reduction.
    remaining_after_reduction = 1.0 - reduction_combined
    if base_component is None:
        current *= remaining_after_reduction
    else:
        base_component *= remaining_after_reduction
        bonus_component *= remaining_after_reduction
        current = base_component + bonus_component

    stages.append(
        ResistanceStage(
            "AFTER_PERCENT_REDUCTION",
            current,
            base_component,
            bonus_component,
        )
    )

    # Bonus armor penetration requires a known base/bonus split. When known,
    # it affects only the bonus component.
    if bonus_pen_combined > 0:
        assert base_component is not None
        assert bonus_component is not None
        bonus_component *= 1.0 - bonus_pen_combined
        current = base_component + bonus_component

    stages.append(
        ResistanceStage(
            "AFTER_BONUS_ARMOR_PENETRATION",
            current,
            base_component,
            bonus_component,
        )
    )

    # 3. Percentage total armor penetration.
    remaining_after_pen = 1.0 - pen_combined
    if base_component is None:
        current *= remaining_after_pen
    else:
        base_component *= remaining_after_pen
        bonus_component *= remaining_after_pen
        current = base_component + bonus_component

    stages.append(
        ResistanceStage(
            "AFTER_PERCENT_PENETRATION",
            current,
            base_component,
            bonus_component,
        )
    )

    # 4. Flat armor penetration. Lethality is 1:1 flat armor penetration
    # since Riot patch 14.1. Penetration cannot create negative resistance.
    total_flat_pen = flat_penetration + lethality
    current = max(0.0, current - total_flat_pen)

    stages.append(
        ResistanceStage(
            "AFTER_FLAT_PENETRATION",
            current,
        )
    )

    return ResistanceResolution(
        status=STATUS_RESOLVED,
        resistance_type="ARMOR",
        original_resistance=total_armor,
        effective_resistance=current,
        stages=tuple(stages),
        stopped_after_negative_reduction=False,
        percentage_reduction_combined=reduction_combined,
        percentage_penetration_combined=pen_combined,
        percentage_bonus_armor_penetration_combined=bonus_pen_combined,
        flat_reduction=flat_reduction,
        flat_penetration=flat_penetration,
        lethality=lethality,
    )


def resolve_magic_resistance(
    magic_resistance: float,
    *,
    flat_reduction: float = 0.0,
    percentage_reductions: Iterable[float] = (),
    percentage_penetrations: Iterable[float] = (),
    flat_penetration: float = 0.0,
) -> ResistanceResolution:
    magic_resistance = _finite_number(
        magic_resistance,
        "magic_resistance",
    )
    flat_reduction = _non_negative(flat_reduction, "flat_reduction")
    flat_penetration = _non_negative(flat_penetration, "flat_penetration")

    reductions = _fractions(
        percentage_reductions,
        "percentage_reductions",
    )
    penetrations = _fractions(
        percentage_penetrations,
        "percentage_penetrations",
    )

    reduction_combined = combine_percentages(reductions)
    pen_combined = combine_percentages(penetrations)

    stages: list[ResistanceStage] = [
        ResistanceStage("ORIGINAL", magic_resistance)
    ]

    # 1. Flat MR reduction.
    current = magic_resistance - flat_reduction
    stages.append(
        ResistanceStage(
            "AFTER_FLAT_REDUCTION",
            current,
        )
    )

    if current <= 0:
        return ResistanceResolution(
            status=STATUS_RESOLVED,
            resistance_type="MAGIC_RESISTANCE",
            original_resistance=magic_resistance,
            effective_resistance=current,
            stages=tuple(stages),
            stopped_after_negative_reduction=True,
            percentage_reduction_combined=reduction_combined,
            percentage_penetration_combined=pen_combined,
            percentage_bonus_armor_penetration_combined=0.0,
            flat_reduction=flat_reduction,
            flat_penetration=flat_penetration,
            lethality=0.0,
        )

    # 2. Percentage MR reduction.
    current *= 1.0 - reduction_combined
    stages.append(
        ResistanceStage(
            "AFTER_PERCENT_REDUCTION",
            current,
        )
    )

    # 3. Percentage magic penetration.
    current *= 1.0 - pen_combined
    stages.append(
        ResistanceStage(
            "AFTER_PERCENT_PENETRATION",
            current,
        )
    )

    # 4. Flat magic penetration, clamped at zero.
    current = max(0.0, current - flat_penetration)
    stages.append(
        ResistanceStage(
            "AFTER_FLAT_PENETRATION",
            current,
        )
    )

    return ResistanceResolution(
        status=STATUS_RESOLVED,
        resistance_type="MAGIC_RESISTANCE",
        original_resistance=magic_resistance,
        effective_resistance=current,
        stages=tuple(stages),
        stopped_after_negative_reduction=False,
        percentage_reduction_combined=reduction_combined,
        percentage_penetration_combined=pen_combined,
        percentage_bonus_armor_penetration_combined=0.0,
        flat_reduction=flat_reduction,
        flat_penetration=flat_penetration,
        lethality=0.0,
    )


def apply_resistance_to_damage(
    raw_damage: float,
    damage_type: DamageType,
    *,
    effective_resistance: float | None = None,
) -> DamageResolution:
    raw_damage = _non_negative(raw_damage, "raw_damage")

    if damage_type == "TRUE":
        return DamageResolution(
            status=STATUS_TRUE_DAMAGE_BYPASS,
            damage_type=damage_type,
            raw_damage=raw_damage,
            effective_resistance=None,
            resistance_multiplier=1.0,
            post_mitigation_damage=raw_damage,
        )

    if damage_type not in {"PHYSICAL", "MAGIC"}:
        raise ValueError(
            "damage_type must be PHYSICAL, MAGIC, or TRUE"
        )

    if effective_resistance is None:
        raise ValueError(
            "effective_resistance is required for physical/magic damage"
        )

    effective_resistance = _finite_number(
        effective_resistance,
        "effective_resistance",
    )
    multiplier = resistance_damage_multiplier(
        effective_resistance
    )

    return DamageResolution(
        status=STATUS_RESOLVED,
        damage_type=damage_type,
        raw_damage=raw_damage,
        effective_resistance=effective_resistance,
        resistance_multiplier=multiplier,
        post_mitigation_damage=raw_damage * multiplier,
    )
