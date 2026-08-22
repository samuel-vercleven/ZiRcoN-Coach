"""Static combat snapshots with per-stat completeness and source evidence."""
from __future__ import annotations

from collections import Counter, defaultdict

from knowledge.champion_level_stats import LEVEL_STATS_VERSION, resolve_champion_stats_at_level
from knowledge.combat_resistance_rules import combine_percentages
from knowledge.item_knowledge import ITEM_KNOWLEDGE_VERSION

SNAPSHOT_VERSION = "combat_stat_snapshot_phase2g_v2"
SNAPSHOT_RESOLVED = "SNAPSHOT_RESOLVED"
SNAPSHOT_PARTIAL = "SNAPSHOT_PARTIAL"

STATIC_STAT_RESOLVED = "STATIC_STAT_RESOLVED"
STATIC_STAT_PARTIAL = "STATIC_STAT_PARTIAL"
STATIC_STAT_SOURCE_EXCLUDED = "STATIC_STAT_SOURCE_EXCLUDED"
STATIC_STAT_NOT_EXPOSED = "STATIC_STAT_NOT_EXPOSED"

AUTHORIZED_STATIC_SOURCES = {"DDRAGON_STATS"}
RELEVANT_ITEM_STATS = {
    "health",
    "attack_damage",
    "ability_power",
    "armor",
    "magic_resistance",
    "attack_speed_percent",
    "ability_haste",
    "critical_strike_chance",
    "life_steal",
    "lethality",
    "armor_penetration_flat",
    "armor_penetration_percent",
    "magic_penetration_flat",
    "magic_penetration_percent",
    "flat_move_speed",
}
PERCENT_SOURCE_STATS = {"armor_penetration_percent", "magic_penetration_percent"}


def _item_fact(item_id, item, fact, reason=None):
    return {
        "item_id": item_id,
        "item_name": item.get("name"),
        "stat": fact.get("stat"),
        "value": fact.get("value"),
        "source": fact.get("source"),
        "source_field": fact.get("source_field"),
        "confidence": fact.get("confidence"),
        "ddragon_version": fact.get("ddragon_version"),
        "status": STATIC_STAT_SOURCE_EXCLUDED if reason else STATIC_STAT_RESOLVED,
        "reason_excluded": reason,
    }


def _item_contributions(item_records, item_ids):
    additive = Counter()
    percentage_sources = defaultdict(list)
    applied = defaultdict(list)
    excluded = defaultdict(list)
    missing_items = []
    for requested_id in item_ids:
        item = item_records.get(str(requested_id)) or item_records.get(requested_id)
        if not item:
            missing_items.append({"item_id": requested_id, "status": STATIC_STAT_NOT_EXPOSED, "reason": "ITEM_NOT_FOUND"})
            continue
        item_id = item.get("item_id", requested_id)
        for fact in item.get("normalized_stats", []):
            stat = fact.get("stat")
            if stat not in RELEVANT_ITEM_STATS:
                continue
            value = fact.get("value")
            if fact.get("source") not in AUTHORIZED_STATIC_SOURCES:
                excluded[stat].append(_item_fact(item_id, item, fact, "SOURCE_NOT_AUTHORIZED_FOR_EXACT_ARITHMETIC"))
                continue
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                excluded[stat].append(_item_fact(item_id, item, fact, "NON_NUMERIC_STATIC_VALUE"))
                continue
            evidence = _item_fact(item_id, item, fact)
            applied[stat].append(evidence)
            if stat in PERCENT_SOURCE_STATS:
                percentage_sources[stat].append(evidence)
            else:
                additive[stat] += value
    return additive, percentage_sources, applied, excluded, missing_items


def _contribution_resolution(stat, additive, percentage_sources, applied, excluded, missing_items):
    if stat in PERCENT_SOURCE_STATS:
        known_partial = combine_percentages(row["value"] for row in percentage_sources[stat])
    else:
        known_partial = additive[stat]
    incomplete = bool(excluded[stat] or missing_items)
    return {
        "status": STATIC_STAT_PARTIAL if incomplete else STATIC_STAT_RESOLVED,
        "exact_value": None if incomplete else known_partial,
        "known_partial_value": known_partial,
        "applied_facts": list(applied[stat]),
        "excluded_facts": list(excluded[stat]),
        "missing_items": list(missing_items),
    }


def _resolved_fact(value, known_partial=None, dependencies=(), applied=(), excluded=(), reasons=()):
    complete = value is not None and not excluded and not reasons
    return {
        "status": STATIC_STAT_RESOLVED if complete else STATIC_STAT_PARTIAL,
        "exact_value": value if complete else None,
        "known_partial_value": value if complete else known_partial,
        "dependencies": list(dependencies),
        "applied_facts": list(applied),
        "excluded_facts": list(excluded),
        "unresolved_reasons": list(reasons),
    }


def build_combat_snapshot(
    champion_record,
    level,
    item_records=None,
    item_ids=(),
    attack_speed_source_record=None,
    current_health=None,
    overrides=None,
):
    native = resolve_champion_stats_at_level(champion_record, level, attack_speed_source_record)
    base = {name: fact.get("value") for name, fact in native["stats"].items()}
    item_records = item_records or {}
    additive, percentage_sources, applied, excluded, missing_items = _item_contributions(item_records, item_ids)
    contributions = {
        stat: _contribution_resolution(stat, additive, percentage_sources, applied, excluded, missing_items)
        for stat in RELEVANT_ITEM_STATS
    }

    stats = {}
    stat_resolution = {}

    def native_stat(output, source):
        value = base.get(source)
        stats[output] = value
        stat_resolution[output] = _resolved_fact(
            value,
            dependencies=(f"native:{source}",),
            reasons=() if value is not None else ("NATIVE_STAT_UNRESOLVED",),
        )

    def item_only(output, stat):
        fact = contributions[stat]
        stats[output] = fact["exact_value"]
        stat_resolution[output] = {
            **fact,
            "dependencies": [f"items:{stat}"],
        }

    def native_plus_item(output, native_name, item_stat):
        native_value = base.get(native_name)
        item_fact = contributions[item_stat]
        known = None if native_value is None else native_value + item_fact["known_partial_value"]
        reasons = [] if native_value is not None else ["NATIVE_STAT_UNRESOLVED"]
        complete = native_value is not None and item_fact["status"] == STATIC_STAT_RESOLVED
        value = known if complete else None
        stats[output] = value
        stat_resolution[output] = _resolved_fact(
            value,
            known_partial=known,
            dependencies=(f"native:{native_name}", f"items:{item_stat}"),
            applied=item_fact["applied_facts"],
            excluded=item_fact["excluded_facts"],
            reasons=reasons + (["ITEM_STATIC_CONTRIBUTION_INCOMPLETE"] if item_fact["status"] != STATIC_STAT_RESOLVED else []),
        )

    native_stat("health_native", "health")
    item_only("health_bonus", "health")
    native_plus_item("health_max", "health", "health")
    native_stat("attack_damage_native", "attack_damage")
    item_only("attack_damage_bonus", "attack_damage")
    native_plus_item("attack_damage_total", "attack_damage", "attack_damage")
    item_only("ability_power", "ability_power")
    native_stat("armor_native", "armor")
    item_only("armor_bonus", "armor")
    native_plus_item("armor", "armor", "armor")
    native_stat("magic_resistance_native", "magic_resistance")
    item_only("magic_resistance_bonus", "magic_resistance")
    native_plus_item("magic_resistance", "magic_resistance", "magic_resistance")
    native_plus_item("move_speed", "move_speed", "flat_move_speed")
    native_stat("attack_speed_native", "attack_speed")

    attack_speed_fact = contributions["attack_speed_percent"]
    ratio = (attack_speed_source_record or {}).get("attack_speed_ratio")
    attack_speed_known = base.get("attack_speed")
    attack_speed_reasons = []
    if attack_speed_fact["known_partial_value"]:
        if isinstance(ratio, (int, float)) and not isinstance(ratio, bool) and attack_speed_known is not None:
            attack_speed_known += ratio * attack_speed_fact["known_partial_value"]
        else:
            attack_speed_reasons.append("ATTACK_SPEED_RATIO_REQUIRED")
    attack_speed_complete = attack_speed_fact["status"] == STATIC_STAT_RESOLVED and not attack_speed_reasons and attack_speed_known is not None
    stats["attack_speed"] = attack_speed_known if attack_speed_complete else None
    stat_resolution["attack_speed"] = _resolved_fact(
        stats["attack_speed"],
        known_partial=attack_speed_known,
        dependencies=("native:attack_speed", "items:attack_speed_percent", "attack_speed_ratio"),
        applied=attack_speed_fact["applied_facts"],
        excluded=attack_speed_fact["excluded_facts"],
        reasons=attack_speed_reasons + (["ITEM_STATIC_CONTRIBUTION_INCOMPLETE"] if attack_speed_fact["status"] != STATIC_STAT_RESOLVED else []),
    )
    item_only("attack_speed_percent", "attack_speed_percent")

    for output, stat in (
        ("critical_strike_chance", "critical_strike_chance"),
        ("life_steal", "life_steal"),
        ("ability_haste", "ability_haste"),
        ("lethality", "lethality"),
        ("armor_penetration_flat", "armor_penetration_flat"),
        ("armor_penetration_percent", "armor_penetration_percent"),
        ("magic_penetration_flat", "magic_penetration_flat"),
        ("magic_penetration_percent", "magic_penetration_percent"),
    ):
        item_only(output, stat)

    stats["armor_penetration_percent_sources"] = list(percentage_sources["armor_penetration_percent"])
    stats["magic_penetration_percent_sources"] = list(percentage_sources["magic_penetration_percent"])

    unresolved = []
    if missing_items:
        unresolved.append({"status": STATIC_STAT_NOT_EXPOSED, "missing_items": missing_items})
    if native["unresolved_count"]:
        unresolved.append({"status": STATIC_STAT_NOT_EXPOSED, "native_stats": [fact.get("stat") for fact in native.get("unresolved", [])]})

    if current_health is not None:
        stats["health_current"] = current_health if isinstance(current_health, (int, float)) and current_health >= 0 else None
        stat_resolution["health_current"] = _resolved_fact(
            stats["health_current"],
            dependencies=("caller:current_health",),
            reasons=() if stats["health_current"] is not None else ("CURRENT_HEALTH_INVALID",),
        )
        max_health = stats["health_max"]
        valid = max_health is not None and stats["health_current"] is not None and stats["health_current"] <= max_health
        stats["health_missing"] = max_health - stats["health_current"] if valid else None
        stat_resolution["health_missing"] = _resolved_fact(
            stats["health_missing"],
            dependencies=("health_max", "health_current"),
            reasons=() if valid else ("HEALTH_MAX_OR_CURRENT_INCOMPLETE",),
        )

    applied_overrides = {}
    for name, value in (overrides or {}).items():
        if name not in stats or name.endswith("_sources") or not isinstance(value, (int, float)) or isinstance(value, bool):
            unresolved.append({"status": STATIC_STAT_NOT_EXPOSED, "reason": "FACTUAL_OVERRIDE_UNSUPPORTED", "stat": name})
            continue
        stats[name] = value
        applied_overrides[name] = value
        stat_resolution[name] = _resolved_fact(value, dependencies=("caller:factual_override",))

    excluded_static_facts = [fact for stat_facts in excluded.values() for fact in stat_facts]
    partial_outputs = sorted(name for name, fact in stat_resolution.items() if fact["status"] != STATIC_STAT_RESOLVED)
    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "status": SNAPSHOT_PARTIAL if unresolved or partial_outputs else SNAPSHOT_RESOLVED,
        "champion_id": champion_record.get("champion_id"),
        "level": level,
        "item_ids": list(item_ids),
        "stats": stats,
        "stat_resolution": stat_resolution,
        "partial_outputs": partial_outputs,
        "excluded_static_facts": excluded_static_facts,
        "unresolved": unresolved,
        "native_unresolved": [fact.get("stat") for fact in native.get("unresolved", [])],
        "runes_applied": False,
        "factual_overrides": applied_overrides,
        "provenance": {
            "level_stats": LEVEL_STATS_VERSION,
            "item_knowledge": ITEM_KNOWLEDGE_VERSION,
            "ddragon_version": champion_record.get("ddragon_version"),
            "locale": champion_record.get("locale"),
            "authorized_static_sources": sorted(AUTHORIZED_STATIC_SOURCES),
        },
    }
