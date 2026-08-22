"""Conservative single-cast orchestration across Phase 2G layers."""
from knowledge.champion_spell_damage_evidence import classify_damage_evidence
from knowledge.champion_spell_damage_resolver import resolve_damage_components
from knowledge.combat_stat_snapshot import build_combat_snapshot
from knowledge.spell_damage_mitigation import mitigate_component

SPELL_COMBAT_RUNTIME_VERSION = "spell_combat_runtime_phase2g_v2"
TOTAL_DAMAGE_RESOLVED = "TOTAL_DAMAGE_RESOLVED"
COMPONENTS_RESOLVED_TOTAL_NOT_COMPOSABLE = "COMPONENTS_RESOLVED_TOTAL_NOT_COMPOSABLE"
PARTIAL_DAMAGE_ONLY = "PARTIAL_DAMAGE_ONLY"
DAMAGE_UNRESOLVED = "DAMAGE_UNRESOLVED"

COMPOSABILITY_NOT_ESTABLISHED = "COMPOSABILITY_NOT_ESTABLISHED"
COMPOSABILITY_CALLER_ASSERTED = "COMPOSABILITY_CALLER_ASSERTED"
COMPOSABILITY_VALIDATED = "COMPOSABILITY_VALIDATED"
COMPONENTS_MUTUALLY_EXCLUSIVE = "COMPONENTS_MUTUALLY_EXCLUSIVE"
TICK_COUNT_UNRESOLVED = "TICK_COUNT_UNRESOLVED"
ACTIVATION_RELATION_UNRESOLVED = "ACTIVATION_RELATION_UNRESOLVED"
PROJECT_VALIDATED = "PROJECT_VALIDATED"
CALLER_SUPPLIED = "CALLER_SUPPLIED"

COMPOSABILITY_STATUSES = {
    COMPOSABILITY_NOT_ESTABLISHED,
    COMPOSABILITY_CALLER_ASSERTED,
    COMPOSABILITY_VALIDATED,
    COMPONENTS_MUTUALLY_EXCLUSIVE,
    TICK_COUNT_UNRESOLVED,
    ACTIVATION_RELATION_UNRESOLVED,
}


def _component_id(row):
    component = row.get("component", row)
    return component.get("component_id") or component.get("calculation_key")


def _normalize_composability(decision, explicitly_composable):
    if decision is None:
        if explicitly_composable:
            return {
                "status": COMPOSABILITY_CALLER_ASSERTED,
                "covered_component_ids": [],
                "reason": "LEGACY_BARE_BOOLEAN_IS_NOT_VALIDATION",
                "evidence": [],
                "provenance": {"origin": CALLER_SUPPLIED, "source": "explicitly_composable"},
            }
        return {
            "status": COMPOSABILITY_NOT_ESTABLISHED,
            "covered_component_ids": [],
            "reason": "NO_COMPOSABILITY_DECISION",
            "evidence": [],
            "provenance": {"origin": CALLER_SUPPLIED, "source": "default"},
        }
    if not isinstance(decision, dict):
        return {
            "status": COMPOSABILITY_NOT_ESTABLISHED,
            "covered_component_ids": [],
            "reason": "MALFORMED_COMPOSABILITY_DECISION",
            "evidence": [],
            "provenance": {"origin": CALLER_SUPPLIED, "source": "invalid"},
        }
    status = decision.get("status")
    covered = decision.get("covered_component_ids")
    provenance = decision.get("provenance")
    evidence = decision.get("evidence")
    well_formed = (
        status in COMPOSABILITY_STATUSES
        and isinstance(covered, (list, tuple))
        and all(isinstance(value, str) and value for value in covered)
        and isinstance(decision.get("reason"), str)
        and bool(decision.get("reason"))
        and isinstance(evidence, (list, tuple))
        and isinstance(provenance, dict)
        and provenance.get("origin") in {CALLER_SUPPLIED, PROJECT_VALIDATED}
        and isinstance(provenance.get("source"), str)
        and bool(provenance.get("source"))
    )
    if not well_formed:
        return {
            "status": COMPOSABILITY_NOT_ESTABLISHED,
            "covered_component_ids": [],
            "reason": "MALFORMED_COMPOSABILITY_DECISION",
            "evidence": [],
            "provenance": {"origin": CALLER_SUPPLIED, "source": "invalid"},
        }
    return {
        **decision,
        "covered_component_ids": list(covered),
        "evidence": list(evidence),
        "provenance": dict(provenance),
    }


def _validated_for_all_components(decision, components):
    component_ids = [_component_id(row) for row in components]
    return (
        decision["status"] == COMPOSABILITY_VALIDATED
        and decision["provenance"].get("origin") == PROJECT_VALIDATED
        and bool(decision["evidence"])
        and None not in component_ids
        and len(component_ids) == len(set(component_ids))
        and set(decision["covered_component_ids"]) == set(component_ids)
        and len(decision["covered_component_ids"]) == len(component_ids)
    )


def resolve_spell_combat(
    source_champion,
    target_champion,
    source_spell,
    semantic_spell,
    *,
    source_level,
    target_level,
    spell_rank,
    max_rank,
    item_records=None,
    source_item_ids=(),
    target_item_ids=(),
    attack_speed_records=None,
    source_current_health=None,
    target_current_health=None,
    calculation_keys=None,
    explicitly_composable=False,
    composability_decision=None,
    formula_context=None,
):
    ratios = attack_speed_records or {}
    source_snapshot = build_combat_snapshot(
        source_champion,
        source_level,
        item_records,
        source_item_ids,
        ratios.get(source_champion.get("champion_id")),
        source_current_health,
    )
    target_snapshot = build_combat_snapshot(
        target_champion,
        target_level,
        item_records,
        target_item_ids,
        ratios.get(target_champion.get("champion_id")),
        target_current_health,
    )
    evidence = classify_damage_evidence(source_spell, semantic_spell)
    if calculation_keys is not None:
        selected = set(calculation_keys)
        evidence = {
            **evidence,
            "components": [row for row in evidence.get("components", []) if row["calculation_key"] in selected],
        }
    context = {
        "spell_rank": spell_rank,
        "max_rank": max_rank,
        "source_snapshot": source_snapshot,
        "target_snapshot": target_snapshot,
        **(formula_context or {}),
    }
    raw = resolve_damage_components(source_spell, evidence, context)
    mitigated = [mitigate_component(row, source_snapshot, target_snapshot) for row in raw]
    resolved = [row for row in mitigated if row["status"] == "POST_MITIGATION_RESOLVED"]
    decision = _normalize_composability(composability_decision, explicitly_composable)
    composability_valid = _validated_for_all_components(decision, mitigated)
    if not resolved:
        status = DAMAGE_UNRESOLVED
        total = None
    elif len(resolved) != len(mitigated):
        status = PARTIAL_DAMAGE_ONLY
        total = None
    elif composability_valid:
        status = TOTAL_DAMAGE_RESOLVED
        total = sum(row["post_mitigation_damage"] for row in resolved)
    else:
        status = COMPONENTS_RESOLVED_TOTAL_NOT_COMPOSABLE
        total = None
    return {
        "runtime_version": SPELL_COMBAT_RUNTIME_VERSION,
        "status": status,
        "source_snapshot": source_snapshot,
        "target_snapshot": target_snapshot,
        "source_spell": source_spell,
        "damage_evidence": evidence,
        "raw_components": raw,
        "post_mitigation_components": mitigated,
        "total_damage": total,
        "composability_decision": decision,
        "composability_valid_for_all_components": composability_valid,
        "explicitly_composable": explicitly_composable,
    }
