import math
import unicodedata
from collections import Counter

from knowledge.champion_attack_speed_source import (
    RATIO_RESOLVED,
    SOURCE_EXACT_PATCH,
    SOURCE_VERIFIED_PREVIOUS_PATCH_CARRY_FORWARD,
    load_attack_speed_ratio_catalog,
)


LEVEL_STATS_VERSION = "champion_level_stats_phase2d_v4"

STANDARD_SUMMONERS_RIFT_MAX_LEVEL = 18
TOP_QUEST_MAX_LEVEL = 20

GROWTH_BASE_COEFFICIENT = 0.7025
GROWTH_ACCELERATION_COEFFICIENT = 0.0175

FORMULA_PROVENANCE = "VALIDATED_COMMUNITY_FORMULA_WITH_RIOT_ANCHORS"

FORMULA_EXPRESSION = (
    "base + growth * (level - 1) * "
    "(0.7025 + 0.0175 * (level - 1))"
)

RESOLVED_STANDARD_GROWTH = "RESOLVED_STANDARD_GROWTH"
RESOLVED_FLAT = "RESOLVED_FLAT"

RESOLVED_LEVEL1_ATTACK_SPEED = "RESOLVED_LEVEL1_ATTACK_SPEED"
RESOLVED_ZERO_GROWTH_ATTACK_SPEED = "RESOLVED_ZERO_GROWTH_ATTACK_SPEED"
RESOLVED_ATTACK_SPEED_WITH_RATIO = "RESOLVED_ATTACK_SPEED_WITH_RATIO"
RESOLVED_JHIN_ATTACK_SPEED_SPECIAL_CASE = (
    "RESOLVED_JHIN_ATTACK_SPEED_SPECIAL_CASE"
)

ATTACK_SPEED_RATIO_UNAVAILABLE = "ATTACK_SPEED_RATIO_UNAVAILABLE"
MISSING_SOURCE_STAT = "MISSING_SOURCE_STAT"

UNRESOLVED_TOP_QUEST_LEVEL_FORMULA = "UNRESOLVED_TOP_QUEST_LEVEL_FORMULA"

ACCEPTED_ATTACK_SPEED_SOURCE_STATUSES = {
    SOURCE_EXACT_PATCH,
    SOURCE_VERIFIED_PREVIOUS_PATCH_CARRY_FORWARD,
}


STANDARD_GROWTH_PAIRS = (
    ("health", "health_base", "health_growth", "points"),
    (
        "health_regen",
        "health_regen_base",
        "health_regen_growth",
        "per_5_seconds",
    ),
    ("resource", "resource_base", "resource_growth", "resource_points"),
    (
        "resource_regen",
        "resource_regen_base",
        "resource_regen_growth",
        "per_5_seconds",
    ),
    (
        "attack_damage",
        "attack_damage_base",
        "attack_damage_growth",
        "points",
    ),
    ("armor", "armor_base", "armor_growth", "points"),
    (
        "magic_resistance",
        "magic_resistance_base",
        "magic_resistance_growth",
        "points",
    ),
    (
        "critical_strike_chance",
        "crit_base",
        "crit_growth",
        "percent",
    ),
)

FLAT_STATS = (
    ("move_speed", "move_speed", "units"),
    ("attack_range", "attack_range", "units"),
)


def _normalize_name(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    return "".join(
        char for char in text.casefold()
        if char.isalnum()
    )


def _is_jhin(champion_record):
    return (
        _normalize_name(champion_record.get("champion_id")) == "jhin"
        or _normalize_name(champion_record.get("name")) == "jhin"
    )


def _validate_level(level):
    if isinstance(level, bool) or not isinstance(level, int):
        raise TypeError("level must be an integer")
    if level < 1 or level > TOP_QUEST_MAX_LEVEL:
        raise ValueError("level must be between 1 and 20")


def stat_growth_multiplier(level):
    _validate_level(level)
    level_index = level - 1
    return level_index * (
        GROWTH_BASE_COEFFICIENT
        + GROWTH_ACCELERATION_COEFFICIENT * level_index
    )


def resolve_growth_value(base_value, growth_value, level):
    if level > STANDARD_SUMMONERS_RIFT_MAX_LEVEL:
        raise ValueError(
            "Levels 19-20 are intentionally unresolved in Phase 2D v3."
        )
    return (
        float(base_value)
        + float(growth_value) * stat_growth_multiplier(level)
    )


def _stat_index(champion_record):
    return {
        row.get("stat"): row
        for row in champion_record.get("normalized_stats", [])
        if row.get("stat")
    }


def _source_fact(index, name):
    row = index.get(name)
    if not row:
        return None
    if not isinstance(row.get("value"), (int, float)):
        return None
    return row


def _extended_unresolved_fact(output_name, unit, level):
    return {
        "stat": output_name,
        "status": UNRESOLVED_TOP_QUEST_LEVEL_FORMULA,
        "value": None,
        "unit": unit,
        "level": level,
        "reason": (
            "Riot 26.1 confirms the top-role level cap can reach 20, but "
            "Phase 2D does not freeze the native-stat coefficient contract "
            "above level 18. No extrapolated native-growth value is emitted."
        ),
    }


def _growth_fact(
    champion_record,
    index,
    output_name,
    base_name,
    growth_name,
    unit,
    level,
):
    if level > STANDARD_SUMMONERS_RIFT_MAX_LEVEL:
        return _extended_unresolved_fact(
            output_name,
            unit,
            level,
        )

    base = _source_fact(index, base_name)
    growth = _source_fact(index, growth_name)

    if not base or not growth:
        return {
            "stat": output_name,
            "status": MISSING_SOURCE_STAT,
            "value": None,
            "unit": unit,
            "level": level,
            "base_stat": base_name,
            "growth_stat": growth_name,
        }

    multiplier = stat_growth_multiplier(level)

    return {
        "stat": output_name,
        "status": RESOLVED_STANDARD_GROWTH,
        "value": (
            float(base["value"])
            + float(growth["value"]) * multiplier
        ),
        "unit": unit,
        "level": level,
        "base_value": float(base["value"]),
        "growth_value": float(growth["value"]),
        "growth_multiplier": multiplier,
        "formula": FORMULA_EXPRESSION,
        "formula_provenance": FORMULA_PROVENANCE,
        "source": "FROZEN_CHAMPION_KNOWLEDGE_NORMALIZED_STATS",
        "source_fields": [
            base.get("source_field"),
            growth.get("source_field"),
        ],
        "source_ddragon_version": champion_record.get(
            "ddragon_version"
        ),
    }


def _flat_fact(
    champion_record,
    index,
    output_name,
    source_name,
    unit,
    level,
):
    source = _source_fact(index, source_name)

    if not source:
        return {
            "stat": output_name,
            "status": MISSING_SOURCE_STAT,
            "value": None,
            "unit": unit,
            "level": level,
        }

    return {
        "stat": output_name,
        "status": RESOLVED_FLAT,
        "value": float(source["value"]),
        "unit": unit,
        "level": level,
        "source": "FROZEN_CHAMPION_KNOWLEDGE_NORMALIZED_STATS",
        "source_fields": [source.get("source_field")],
        "source_ddragon_version": champion_record.get(
            "ddragon_version"
        ),
    }


def _attack_speed_fact(
    champion_record,
    index,
    level,
    attack_speed_source_record,
):
    if level > STANDARD_SUMMONERS_RIFT_MAX_LEVEL:
        return _extended_unresolved_fact(
            "attack_speed",
            "attacks_per_second",
            level,
        )

    base = _source_fact(index, "attack_speed_base")
    growth = _source_fact(index, "attack_speed_growth")

    if not base or not growth:
        return {
            "stat": "attack_speed",
            "status": MISSING_SOURCE_STAT,
            "value": None,
            "unit": "attacks_per_second",
            "level": level,
        }

    base_attack_speed = float(base["value"])
    growth_percent = float(growth["value"])
    multiplier = stat_growth_multiplier(level)
    growth_bonus_percent = growth_percent * multiplier

    common = {
        "stat": "attack_speed",
        "unit": "attacks_per_second",
        "level": level,
        "base_attack_speed": base_attack_speed,
        "attack_speed_growth_percent": growth_percent,
        "growth_multiplier": multiplier,
        "level_growth_bonus_percent": growth_bonus_percent,
        "formula_provenance": FORMULA_PROVENANCE,
        "source_ddragon_version": champion_record.get(
            "ddragon_version"
        ),
    }

    if level == 1:
        return {
            **common,
            "status": RESOLVED_LEVEL1_ATTACK_SPEED,
            "value": base_attack_speed,
        }

    if math.isclose(growth_percent, 0.0, abs_tol=1e-12):
        return {
            **common,
            "status": RESOLVED_ZERO_GROWTH_ATTACK_SPEED,
            "value": base_attack_speed,
        }

    if (
        not attack_speed_source_record
        or attack_speed_source_record.get("status")
        != RATIO_RESOLVED
        or not isinstance(
            attack_speed_source_record.get(
                "attack_speed_ratio"
            ),
            (int, float),
        )
    ):
        return {
            **common,
            "status": ATTACK_SPEED_RATIO_UNAVAILABLE,
            "value": None,
            "reason": (
                "Exact non-level-1 attack speed requires a separate "
                "Attack Speed Ratio with accepted provenance."
            ),
        }

    ratio = float(
        attack_speed_source_record["attack_speed_ratio"]
    )

    if _is_jhin(champion_record):
        value = base_attack_speed + (
            base_attack_speed
            * (growth_bonus_percent / 100.0)
        )
        status = RESOLVED_JHIN_ATTACK_SPEED_SPECIAL_CASE
        ratio_used = base_attack_speed
        formula = (
            "base_attack_speed + base_attack_speed * "
            "(growth_percent * growth_multiplier / 100)"
        )
    else:
        value = base_attack_speed + (
            ratio * (growth_bonus_percent / 100.0)
        )
        status = RESOLVED_ATTACK_SPEED_WITH_RATIO
        ratio_used = ratio
        formula = (
            "base_attack_speed + attack_speed_ratio * "
            "(growth_percent * growth_multiplier / 100)"
        )

    return {
        **common,
        "status": status,
        "value": value,
        "attack_speed_ratio": ratio,
        "ratio_used_for_growth": ratio_used,
        "formula": formula,
        "attack_speed_source": attack_speed_source_record.get(
            "source"
        ),
        "attack_speed_source_type": (
            attack_speed_source_record.get("source_type")
        ),
        "attack_speed_source_url": (
            attack_speed_source_record.get("source_url")
        ),
        "attack_speed_target_patch": (
            attack_speed_source_record.get("target_patch")
        ),
        "attack_speed_source_patch": (
            attack_speed_source_record.get("source_patch")
        ),
        "attack_speed_source_status": (
            attack_speed_source_record.get("source_status")
        ),
        "attack_speed_carry_forward": (
            attack_speed_source_record.get("carry_forward")
        ),
    }


def resolve_champion_stats_at_level(
    champion_record,
    level,
    attack_speed_source_record=None,
):
    _validate_level(level)
    index = _stat_index(champion_record)

    stats = {}

    for (
        output_name,
        base_name,
        growth_name,
        unit,
    ) in STANDARD_GROWTH_PAIRS:
        stats[output_name] = _growth_fact(
            champion_record,
            index,
            output_name,
            base_name,
            growth_name,
            unit,
            level,
        )

    for output_name, source_name, unit in FLAT_STATS:
        stats[output_name] = _flat_fact(
            champion_record,
            index,
            output_name,
            source_name,
            unit,
            level,
        )

    stats["attack_speed"] = _attack_speed_fact(
        champion_record,
        index,
        level,
        attack_speed_source_record,
    )

    unresolved = [
        fact
        for fact in stats.values()
        if fact.get("value") is None
    ]

    return {
        "level_stats_version": LEVEL_STATS_VERSION,
        "champion_knowledge_version": (
            champion_record.get(
                "champion_knowledge_version"
            )
        ),
        "champion_id": champion_record.get("champion_id"),
        "champion_key": champion_record.get("champion_key"),
        "name": champion_record.get("name"),
        "partype": champion_record.get("partype"),
        "level": level,
        "level_context": (
            "TOP_QUEST_EXTENDED_LEVEL_UNRESOLVED"
            if level > STANDARD_SUMMONERS_RIFT_MAX_LEVEL
            else "STANDARD_SUMMONERS_RIFT_LEVEL"
        ),
        "formula_provenance": FORMULA_PROVENANCE,
        "ddragon_version": champion_record.get(
            "ddragon_version"
        ),
        "locale": champion_record.get("locale"),
        "stats": stats,
        "resolved_value_count": sum(
            1
            for fact in stats.values()
            if fact.get("value") is not None
        ),
        "unresolved_count": len(unresolved),
        "unresolved": unresolved,
    }


def _cross_source_checks(
    champion_record,
    attack_record,
):
    checks = []
    index = _stat_index(champion_record)

    ddragon_as = _source_fact(
        index,
        "attack_speed_base",
    )
    ddragon_growth = _source_fact(
        index,
        "attack_speed_growth",
    )

    cdragon_as = attack_record.get(
        "attack_speed_cdragon"
    )
    cdragon_growth = attack_record.get(
        "attack_speed_growth_percent_cdragon"
    )

    if ddragon_as and isinstance(
        cdragon_as,
        (int, float),
    ):
        delta = abs(
            float(ddragon_as["value"])
            - float(cdragon_as)
        )
        checks.append(
            {
                "field": "attack_speed_base",
                "delta": delta,
                "status": (
                    "MATCH"
                    if delta <= 0.0025
                    else "MISMATCH"
                ),
                "ddragon": float(
                    ddragon_as["value"]
                ),
                "cdragon": float(cdragon_as),
            }
        )

    if ddragon_growth and isinstance(
        cdragon_growth,
        (int, float),
    ):
        delta = abs(
            float(ddragon_growth["value"])
            - float(cdragon_growth)
        )
        checks.append(
            {
                "field": "attack_speed_growth",
                "delta": delta,
                "status": (
                    "MATCH"
                    if delta <= 0.02
                    else "MISMATCH"
                ),
                "ddragon": float(
                    ddragon_growth["value"]
                ),
                "cdragon": float(cdragon_growth),
            }
        )

    return checks


def build_level_stats_catalog_audit(
    champion_catalog=None,
    attack_speed_catalog=None,
):
    if champion_catalog is None:
        from knowledge.champion_knowledge import (
            build_champion_knowledge_catalog,
        )
        champion_catalog = (
            build_champion_knowledge_catalog()
        )

    if attack_speed_catalog is None:
        attack_speed_catalog = (
            load_attack_speed_ratio_catalog(
                champion_catalog
            )
        )

    records = champion_catalog.get(
        "records",
        {},
    )
    attack_records = attack_speed_catalog.get(
        "records",
        {},
    )

    blocking = []
    review = []
    info = []

    standard_status_counts = Counter()
    attack_speed_status_counts = Counter()

    cross_source_mismatches = []
    standard_rows = 0
    extended_rows = 0

    if (
        champion_catalog.get(
            "champion_knowledge_version"
        )
        != "champion_knowledge_phase2b1_c_v1"
    ):
        review.append(
            {
                "kind": (
                    "FROZEN_CHAMPION_KNOWLEDGE_"
                    "VERSION_CHANGED"
                ),
                "message": (
                    "Champion Knowledge is not the "
                    "expected frozen Phase 2B1-C baseline."
                ),
            }
        )

    if (
        attack_speed_catalog.get("source_status")
        not in ACCEPTED_ATTACK_SPEED_SOURCE_STATUSES
    ):
        review.append(
            {
                "kind": (
                    "ATTACK_SPEED_SOURCE_"
                    "PROVENANCE_NOT_ACCEPTED"
                ),
                "message": (
                    f"Source status is "
                    f"{attack_speed_catalog.get('source_status')}; "
                    f"resolved "
                    f"{attack_speed_catalog.get('resolved_count')}/"
                    f"{attack_speed_catalog.get('expected_count')}."
                ),
            }
        )

    for champion_id, champion_record in records.items():
        attack_record = attack_records.get(
            champion_id
        )

        if attack_record:
            for check in _cross_source_checks(
                champion_record,
                attack_record,
            ):
                if check["status"] == "MISMATCH":
                    cross_source_mismatches.append(
                        {
                            "champion_id": champion_id,
                            **check,
                        }
                    )

        for level in range(
            1,
            STANDARD_SUMMONERS_RIFT_MAX_LEVEL + 1,
        ):
            result = resolve_champion_stats_at_level(
                champion_record,
                level,
                attack_speed_source_record=(
                    attack_record
                ),
            )
            standard_rows += 1

            for stat_name, fact in (
                result["stats"].items()
            ):
                status = fact.get("status")

                if stat_name == "attack_speed":
                    attack_speed_status_counts[
                        status
                    ] += 1
                else:
                    standard_status_counts[
                        status
                    ] += 1

                value = fact.get("value")
                if (
                    value is not None
                    and not math.isfinite(float(value))
                ):
                    blocking.append(
                        {
                            "champion_id": champion_id,
                            "level": level,
                            "stat": stat_name,
                            "message": (
                                "Resolved value is not finite."
                            ),
                        }
                    )

            if level == 1:
                for output_name, *_ in (
                    STANDARD_GROWTH_PAIRS
                ):
                    fact = result["stats"][
                        output_name
                    ]
                    if (
                        fact.get("status")
                        == RESOLVED_STANDARD_GROWTH
                        and not math.isclose(
                            fact["value"],
                            fact["base_value"],
                            rel_tol=0.0,
                            abs_tol=1e-9,
                        )
                    ):
                        blocking.append(
                            {
                                "champion_id": (
                                    champion_id
                                ),
                                "level": 1,
                                "stat": output_name,
                                "message": (
                                    "Level-1 value differs "
                                    "from base."
                                ),
                            }
                        )

            if level == 18:
                for output_name, *_ in (
                    STANDARD_GROWTH_PAIRS
                ):
                    fact = result["stats"][
                        output_name
                    ]
                    if (
                        fact.get("status")
                        != RESOLVED_STANDARD_GROWTH
                    ):
                        continue

                    expected = (
                        fact["base_value"]
                        + 17.0
                        * fact["growth_value"]
                    )

                    if not math.isclose(
                        fact["value"],
                        expected,
                        rel_tol=0.0,
                        abs_tol=1e-8,
                    ):
                        blocking.append(
                            {
                                "champion_id": (
                                    champion_id
                                ),
                                "level": 18,
                                "stat": output_name,
                                "message": (
                                    "Level-18 invariant "
                                    "base + 17*growth failed."
                                ),
                            }
                        )

        for level in (19, 20):
            result = resolve_champion_stats_at_level(
                champion_record,
                level,
                attack_speed_source_record=(
                    attack_record
                ),
            )
            extended_rows += 1

            for fact in result["stats"].values():
                if (
                    fact.get("status")
                    not in {
                        RESOLVED_FLAT,
                        UNRESOLVED_TOP_QUEST_LEVEL_FORMULA,
                    }
                ):
                    blocking.append(
                        {
                            "champion_id": champion_id,
                            "level": level,
                            "stat": fact.get("stat"),
                            "message": (
                                "Extended native-growth stat "
                                "must remain unresolved."
                            ),
                        }
                    )

    missing_standard = standard_status_counts.get(
        MISSING_SOURCE_STAT,
        0,
    )

    if missing_standard:
        blocking.append(
            {
                "kind": (
                    "MISSING_STANDARD_CHAMPION_STATS"
                ),
                "message": (
                    f"{missing_standard} standard rows "
                    "lack frozen Champion Knowledge facts."
                ),
            }
        )

    ratio_unavailable = (
        attack_speed_status_counts.get(
            ATTACK_SPEED_RATIO_UNAVAILABLE,
            0,
        )
    )

    if ratio_unavailable:
        review.append(
            {
                "kind": (
                    "ATTACK_SPEED_RATIO_UNAVAILABLE"
                ),
                "message": (
                    f"{ratio_unavailable} standard "
                    "attack-speed rows remain unresolved."
                ),
            }
        )

    if cross_source_mismatches:
        review.append(
            {
                "kind": (
                    "DDRAGON_CDRAGON_ATTACK_SPEED_"
                    "MISMATCH"
                ),
                "message": (
                    f"{len(cross_source_mismatches)} "
                    "base/growth cross-source checks "
                    "exceed tolerance."
                ),
            }
        )

    if (
        attack_speed_catalog.get("source_status")
        == SOURCE_VERIFIED_PREVIOUS_PATCH_CARRY_FORWARD
    ):
        info.append(
            {
                "kind": (
                    "ATTACK_SPEED_RATIO_PATCH_"
                    "CARRY_FORWARD_ACCEPTED"
                ),
                "message": (
                    f"Target patch "
                    f"{attack_speed_catalog.get('target_patch')} "
                    f"uses ratio data from verified source "
                    f"{attack_speed_catalog.get('selected_source_patch')} "
                    f"because exact CDragon was unavailable. "
                    f"Official patch notes transition is "
                    f"documented in provenance."
                ),
            }
        )

    info.append(
        {
            "kind": (
                "TOP_QUEST_LEVELS_19_20_"
                "DEFERRED_BY_SCOPE"
            ),
            "message": (
                f"{extended_rows} champion-level rows "
                "for levels 19-20 were checked for "
                "explicit non-extrapolation."
            ),
        }
    )

    info.append(
        {
            "kind": "FORMULA_PROVENANCE_ACCEPTED",
            "message": (
                "0.7025 / 0.0175 is treated as a "
                "community-documented formula with "
                "Riot terminology/numeric anchors, not "
                "as a Riot Developer Portal publication."
            ),
        }
    )

    return {
        "level_stats_version": LEVEL_STATS_VERSION,
        "champion_knowledge_version": (
            champion_catalog.get(
                "champion_knowledge_version"
            )
        ),
        "ddragon_version": (
            champion_catalog.get(
                "resolved_ddragon_version"
            )
        ),
        "locale": champion_catalog.get("locale"),
        "champion_count": len(records),
        "standard_level_rows": standard_rows,
        "extended_level_rows": extended_rows,
        "standard_status_counts": dict(
            standard_status_counts
        ),
        "attack_speed_status_counts": dict(
            attack_speed_status_counts
        ),
        "attack_speed_source": attack_speed_catalog,
        "cross_source_mismatches": (
            cross_source_mismatches
        ),
        "blocking": blocking,
        "review": review,
        "info": info,
    }


def render_level_stats_catalog_audit(audit):
    source = audit["attack_speed_source"]

    lines = [
        "=" * 76,
        (
            "CHAMPION LEVEL-RESOLVED STATS - "
            "FULL CATALOG AUDIT V4"
        ),
        "=" * 76,
        (
            f"Level stats version       : "
            f"{audit['level_stats_version']}"
        ),
        (
            f"Champion knowledge       : "
            f"{audit['champion_knowledge_version']}"
        ),
        (
            f"Data Dragon              : "
            f"{audit['ddragon_version']}"
        ),
        (
            f"Locale                   : "
            f"{audit['locale']}"
        ),
        (
            f"Champions                : "
            f"{audit['champion_count']}"
        ),
        (
            f"Standard rows 1-18       : "
            f"{audit['standard_level_rows']}"
        ),
        (
            f"Extended rows 19-20      : "
            f"{audit['extended_level_rows']}"
        ),
        (
            f"Attack ratio source      : "
            f"{source.get('source_status')}"
        ),
        (
            f"Attack ratio target      : "
            f"{source.get('target_patch')}"
        ),
        (
            f"Attack ratio data patch  : "
            f"{source.get('selected_source_patch')}"
        ),
        (
            f"Attack ratios resolved   : "
            f"{source.get('resolved_count')}/"
            f"{source.get('expected_count')}"
        ),
        (
            f"Cross-source mismatches  : "
            f"{len(audit['cross_source_mismatches'])}"
        ),
        (
            f"Blocking issues          : "
            f"{len(audit['blocking'])}"
        ),
        (
            f"Review items             : "
            f"{len(audit['review'])}"
        ),
        "",
        "SOURCE ATTEMPTS",
        "-" * 76,
    ]

    for attempt in source.get("attempts", []):
        lines.append(
            f"- patch {attempt['source_patch']}: "
            f"{attempt['resolved_count']}/"
            f"{attempt['expected_count']} resolved"
        )
        if attempt.get("consolidated_error"):
            lines.append(
                f"  consolidated_error: "
                f"{attempt['consolidated_error']}"
            )

    if source.get("carry_forward"):
        carry = source["carry_forward"]
        lines.extend(
            [
                "",
                "CARRY-FORWARD PROVENANCE",
                "-" * 76,
                (
                    f"- verification: "
                    f"{carry['verification_status']}"
                ),
                (
                    f"- official patch notes: "
                    f"{carry['official_patch_notes_url']}"
                ),
                (
                    f"- notes: "
                    f"{carry['verification_notes']}"
                ),
            ]
        )

    lines.extend(
        [
            "",
            "Standard stat status counts:",
        ]
    )

    for key, value in sorted(
        audit["standard_status_counts"].items()
    ):
        lines.append(f"- {key}: {value}")

    lines.extend(
        [
            "",
            "Attack-speed status counts:",
        ]
    )

    for key, value in sorted(
        audit["attack_speed_status_counts"].items()
    ):
        lines.append(f"- {key}: {value}")

    if audit["cross_source_mismatches"]:
        lines.extend(
            [
                "",
                "CROSS-SOURCE MISMATCHES",
                "-" * 76,
            ]
        )
        for row in (
            audit["cross_source_mismatches"][:30]
        ):
            lines.append(f"[REVIEW] {row}")

    if audit["blocking"]:
        lines.extend(
            [
                "",
                "BLOCKING ISSUES",
                "-" * 76,
            ]
        )
        for issue in audit["blocking"][:30]:
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
            lines.append(
                f"[REVIEW] {issue['kind']}: "
                f"{issue['message']}"
            )

    if audit["info"]:
        lines.extend(
            [
                "",
                "ACCEPTED SCOPE / INFORMATION",
                "-" * 76,
            ]
        )
        for issue in audit["info"]:
            lines.append(
                f"[INFO] {issue['kind']}: "
                f"{issue['message']}"
            )

    status = (
        "FAIL"
        if audit["blocking"]
        else (
            "REVIEW_REQUIRED"
            if audit["review"]
            else "PASS"
        )
    )

    lines.extend(
        [
            "",
            f"STATUS : {status}",
        ]
    )

    return "\n".join(lines)


def main():
    audit = build_level_stats_catalog_audit()
    print(render_level_stats_catalog_audit(audit))

    if audit["blocking"]:
        return 2
    if audit["review"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
