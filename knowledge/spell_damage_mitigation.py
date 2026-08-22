"""Thin completeness-aware adapter over frozen Phase 2E resistance math."""
from knowledge.combat_resistance_rules import (
    COMBAT_RESISTANCE_VERSION,
    apply_resistance_to_damage,
    resolve_armor,
    resolve_magic_resistance,
)
from knowledge.combat_stat_snapshot import STATIC_STAT_RESOLVED

MITIGATION_VERSION = "spell_damage_mitigation_phase2g_v2"
POST_MITIGATION_RESOLVED = "POST_MITIGATION_RESOLVED"
MITIGATION_INPUT_UNRESOLVED = "MITIGATION_INPUT_UNRESOLVED"


def _exact_stat(snapshot, name):
    value = snapshot.get("stats", {}).get(name)
    resolution = snapshot.get("stat_resolution", {}).get(name)
    if resolution is not None and resolution.get("status") != STATIC_STAT_RESOLVED:
        return None, {"stat": name, "status": resolution.get("status"), "resolution": resolution}
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None, {"stat": name, "status": "VALUE_NOT_EXACT_NUMERIC", "value": value}
    return value, None


def _percentage_sources(snapshot, stat_name, sources_name):
    aggregate, issue = _exact_stat(snapshot, stat_name)
    if issue:
        return None, issue
    raw_sources = snapshot.get("stats", {}).get(sources_name)
    if raw_sources is None:
        return (aggregate,), None
    values = []
    for source in raw_sources:
        value = source.get("value") if isinstance(source, dict) else source
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return None, {"stat": stat_name, "status": "PERCENTAGE_SOURCE_NON_NUMERIC", "source": source}
        values.append(value)
    return tuple(values), None


def mitigate_component(component, attacker_snapshot, target_snapshot):
    if component.get("status") != "RAW_DAMAGE_RESOLVED":
        return {"status": "DAMAGE_UNRESOLVED", "component": component}
    raw = component["raw_damage"]
    kind = component["damage_type"]
    if kind == "TRUE":
        resolution = apply_resistance_to_damage(raw, "TRUE")
        resistance = None
        penetration_inputs = {}
    elif kind == "PHYSICAL":
        armor, armor_issue = _exact_stat(target_snapshot, "armor")
        base_armor, base_issue = _exact_stat(target_snapshot, "armor_native")
        flat, flat_issue = _exact_stat(attacker_snapshot, "armor_penetration_flat")
        lethality, lethality_issue = _exact_stat(attacker_snapshot, "lethality")
        percentages, percent_issue = _percentage_sources(
            attacker_snapshot, "armor_penetration_percent", "armor_penetration_percent_sources"
        )
        issues = [issue for issue in (armor_issue, base_issue, flat_issue, lethality_issue, percent_issue) if issue]
        if issues:
            return {"status": MITIGATION_INPUT_UNRESOLVED, "component": component, "unresolved_inputs": issues}
        resistance = resolve_armor(
            armor,
            base_armor=base_armor,
            percentage_penetrations=percentages,
            flat_penetration=flat,
            lethality=lethality,
        )
        resolution = apply_resistance_to_damage(raw, "PHYSICAL", effective_resistance=resistance.effective_resistance)
        penetration_inputs = {
            "percentage_sources": percentages,
            "percentage_combined": resistance.percentage_penetration_combined,
            "flat": flat,
            "lethality": lethality,
        }
    elif kind == "MAGIC":
        magic_resistance, resistance_issue = _exact_stat(target_snapshot, "magic_resistance")
        flat, flat_issue = _exact_stat(attacker_snapshot, "magic_penetration_flat")
        percentages, percent_issue = _percentage_sources(
            attacker_snapshot, "magic_penetration_percent", "magic_penetration_percent_sources"
        )
        issues = [issue for issue in (resistance_issue, flat_issue, percent_issue) if issue]
        if issues:
            return {"status": MITIGATION_INPUT_UNRESOLVED, "component": component, "unresolved_inputs": issues}
        resistance = resolve_magic_resistance(
            magic_resistance,
            percentage_penetrations=percentages,
            flat_penetration=flat,
        )
        resolution = apply_resistance_to_damage(raw, "MAGIC", effective_resistance=resistance.effective_resistance)
        penetration_inputs = {
            "percentage_sources": percentages,
            "percentage_combined": resistance.percentage_penetration_combined,
            "flat": flat,
        }
    else:
        return {"status": "DAMAGE_TYPE_UNRESOLVED", "component": component}
    return {
        "status": POST_MITIGATION_RESOLVED,
        "component": component,
        "raw_damage": raw,
        "damage_type": kind,
        "original_resistance": None if resistance is None else resistance.original_resistance,
        "effective_resistance": resolution.effective_resistance,
        "penetration_inputs": penetration_inputs,
        "post_mitigation_damage": resolution.post_mitigation_damage,
        "resistance_multiplier": resolution.resistance_multiplier,
        "phase2e_version": COMBAT_RESISTANCE_VERSION,
        "mitigation_version": MITIGATION_VERSION,
    }
