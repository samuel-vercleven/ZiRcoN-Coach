"""Evidence-gated Phase 2H champion spell stat semantics.

Phase 2H inventories and labels references.  It does not execute any spell
calculation class and does not alter the frozen Phase 2G evaluator.
"""

from __future__ import annotations

import copy
from collections import Counter, defaultdict

from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION, DATAMINE_COMMIT
from knowledge.champion_spell_stat_semantics_sources import PHASE2H_VERSION


STAT_REFERENCE_BRANCH = "STAT_REFERENCE"
ABILITY_RESOURCE_BRANCH = "ABILITY_RESOURCE"
FORMULA_WITHOUT_STAT_BRANCH = "FORMULA_WITHOUT_STAT"
RESOURCE_ENUM_RESEARCH_ONLY = "RESOURCE_ENUM_RESEARCH_ONLY"


def _tooltip_index(champion_catalog):
    index = {}
    if not isinstance(champion_catalog, dict):
        return index
    for champion_id, champion in champion_catalog.get("records", {}).items():
        for spell in champion.get("spells", []):
            slot = spell.get("inferred_slot")
            if slot is None:
                continue
            index[(str(champion_id), slot)] = {
                "ddragon_spell_id": spell.get("id"),
                "ddragon_spell_name": spell.get("name"),
                "clean_description": spell.get("clean_description"),
                "clean_tooltip": spell.get("clean_tooltip"),
                "component_count": len(spell.get("components", [])),
                "linkage_status": "DDRAGON_SLOT_LINK_AVAILABLE",
            }
    return index


def _calculation_key(graph_path):
    parts = str(graph_path or "").split("/")
    return parts[1] if len(parts) > 1 and parts[0] == "mSpellCalculations" else None


def _parent_path(graph_path):
    return str(graph_path).rsplit("/", 1)[0] if "/" in str(graph_path) else None


def _primitive_coefficient_fields(node_payload):
    return {
        key: copy.deepcopy(value)
        for key, value in node_payload.items()
        if any(token in key.casefold() for token in ("coefficient", "ratio", "multiplier"))
    }


def _named_data_value_fields(node_payload):
    return {
        key: value
        for key, value in node_payload.items()
        if "datavalue" in key.casefold() and isinstance(value, str)
    }


def _subpart_fields(node_payload):
    return {
        key: copy.deepcopy(value)
        for key, value in node_payload.items()
        if "part" in key.casefold() and key != "~class"
    }


def _branch_for_node(node_payload):
    if node_payload.get("~class") == "AbilityResourceByCoefficientCalculationPart":
        return ABILITY_RESOURCE_BRANCH
    if "mStat" in node_payload:
        return STAT_REFERENCE_BRANCH
    if "mAbilityResource" in node_payload:
        return ABILITY_RESOURCE_BRANCH
    return FORMULA_WITHOUT_STAT_BRANCH


def inventory_stat_semantic_occurrences(catalog, champion_catalog=None):
    """Preserve every mStat and mStatFormula field occurrence independently."""
    tooltip_index = _tooltip_index(champion_catalog)
    occurrences = []
    for champion_id, champion in catalog.get("records", {}).items():
        for spell in champion.get("primary_spells", []):
            node_index = {
                node.get("graph_path"): node
                for node in spell.get("calculation_nodes", [])
                if isinstance(node, dict)
            }
            link = tooltip_index.get(
                (str(champion_id), spell.get("slot")),
                {"linkage_status": "DDRAGON_SLOT_LINK_NOT_PROVIDED"},
            )
            for node in spell.get("calculation_nodes", []):
                payload = node.get("raw_node_payload")
                if not isinstance(payload, dict):
                    continue
                fields = [field for field in ("mStat", "mStatFormula") if field in payload]
                if not fields:
                    continue
                graph_path = node.get("graph_path")
                parent = node_index.get(_parent_path(graph_path), {})
                calc_key = _calculation_key(graph_path)
                root = node_index.get(f"mSpellCalculations/{calc_key}", {})
                sibling_fields = {
                    key: copy.deepcopy(value)
                    for key, value in payload.items()
                    if key not in {"mStat", "mStatFormula"}
                }
                common = {
                    "phase2h_version": PHASE2H_VERSION,
                    "champion_spell_source_version": spell.get(
                        "champion_spell_source_version", CHAMPION_SPELL_SOURCE_VERSION
                    ),
                    "pinned_commit": spell.get("source_commit", DATAMINE_COMMIT),
                    "champion_id": champion_id,
                    "champion_name": spell.get("champion_name") or champion.get("champion_name"),
                    "slot": spell.get("slot"),
                    "spell_source_path": spell.get("internal_spell_path"),
                    "object_path": spell.get("object_path"),
                    "calculation_key": calc_key,
                    "graph_path": graph_path,
                    "calculation_class": node.get("calculation_class"),
                    "class_signature": "|".join(sorted(payload)),
                    "raw_mStat": payload.get("mStat") if "mStat" in payload else None,
                    "raw_mStat_present": "mStat" in payload,
                    "raw_mStatFormula": (
                        payload.get("mStatFormula") if "mStatFormula" in payload else None
                    ),
                    "raw_mStatFormula_present": "mStatFormula" in payload,
                    "effective_mStatFormula": (
                        payload.get("mStatFormula") if "mStatFormula" in payload else 0
                    ),
                    "formula_default_provenance": (
                        "EXPLICIT_SERIALIZED_FIELD"
                        if "mStatFormula" in payload
                        else "IMPLICIT_SERIALIZED_U8_DEFAULT_ZERO"
                    ),
                    "branch": _branch_for_node(payload),
                    "raw_mAbilityResource": payload.get("mAbilityResource"),
                    "sibling_fields": sibling_fields,
                    "coefficient_fields": _primitive_coefficient_fields(payload),
                    "data_value_references": _named_data_value_fields(payload),
                    "subpart_fields": _subpart_fields(payload),
                    "parent_calculation_identity": {
                        "graph_path": parent.get("graph_path"),
                        "calculation_class": parent.get("calculation_class"),
                    },
                    "root_calculation_identity": {
                        "calculation_key": calc_key,
                        "graph_path": root.get("graph_path"),
                        "calculation_class": root.get("calculation_class"),
                    },
                    "tooltip_component_linkage": copy.deepcopy(link),
                    "raw_hash_fields": {
                        key: copy.deepcopy(value)
                        for key, value in payload.items()
                        if key.startswith("{") and key.endswith("}")
                    },
                    "hash_resolution_status": (
                        "RAW_HASH_PRESERVED_UNRESOLVED"
                        if any(key.startswith("{") and key.endswith("}") for key in payload)
                        else "NO_HASH_FIELD"
                    ),
                }
                for field in fields:
                    occurrence = copy.deepcopy(common)
                    occurrence.update(
                        {
                            "occurrence_field": field,
                            "raw_occurrence_value": copy.deepcopy(payload[field]),
                            "occurrence_identity": (
                                f"{champion_id}:{spell.get('slot')}:{graph_path}:{field}"
                            ),
                        }
                    )
                    occurrences.append(occurrence)
    return occurrences


def stat_reference_rows(occurrences):
    return [row for row in occurrences if row["occurrence_field"] == "mStat"]


def formula_reference_rows(occurrences):
    return [row for row in occurrences if row["occurrence_field"] == "mStatFormula"]


def ability_resource_rows(occurrences):
    return [row for row in occurrences if row["branch"] == ABILITY_RESOURCE_BRANCH]


def inventory_ability_resource_calculations(catalog):
    """Inventory the resource class even when all enum fields serialize as defaults."""
    rows = []
    for champion_id, champion in catalog.get("records", {}).items():
        for spell in champion.get("primary_spells", []):
            for node in spell.get("calculation_nodes", []):
                payload = node.get("raw_node_payload")
                if not isinstance(payload, dict) or payload.get("~class") != "AbilityResourceByCoefficientCalculationPart":
                    continue
                rows.append(
                    {
                        "champion_id": champion_id,
                        "champion_name": spell.get("champion_name"),
                        "slot": spell.get("slot"),
                        "spell_source_path": spell.get("internal_spell_path"),
                        "calculation_key": _calculation_key(node.get("graph_path")),
                        "graph_path": node.get("graph_path"),
                        "calculation_class": payload.get("~class"),
                        "raw_mAbilityResource": (
                            payload.get("mAbilityResource") if "mAbilityResource" in payload else None
                        ),
                        "raw_mAbilityResource_present": "mAbilityResource" in payload,
                        "raw_mStatFormula": (
                            payload.get("mStatFormula") if "mStatFormula" in payload else None
                        ),
                        "raw_mStatFormula_present": "mStatFormula" in payload,
                        "coefficient": payload.get("mCoefficient"),
                        "raw_node_payload": copy.deepcopy(payload),
                        "status": RESOURCE_ENUM_RESEARCH_ONLY,
                        "execution_eligible": False,
                        "pinned_commit": spell.get("source_commit", DATAMINE_COMMIT),
                    }
                )
    return rows


def summarize_inventory(occurrences):
    stat_rows = stat_reference_rows(occurrences)
    formula_rows = formula_reference_rows(occurrences)
    grouped = defaultdict(Counter)
    for row in stat_rows:
        formula = row["effective_mStatFormula"]
        grouped["raw_mStat"][row["raw_mStat"]] += 1
        grouped["raw_mStatFormula"][formula] += 1
        grouped["mStat_formula_pair"][(row["raw_mStat"], formula)] += 1
        grouped["calculation_class"][row["calculation_class"]] += 1
        grouped["champion"][row["champion_id"]] += 1
        grouped["slot"][row["slot"]] += 1
        grouped["class_signature"][row["class_signature"]] += 1
    return {
        "total_occurrences": len(occurrences),
        "mStat_occurrences": len(stat_rows),
        "mStatFormula_occurrences": len(formula_rows),
        "distinct_mStat_ids": sorted(grouped["raw_mStat"]),
        "explicit_mStatFormula_values": sorted(
            {row["raw_mStatFormula"] for row in formula_rows}
        ),
        "effective_stat_formula_values": sorted(grouped["raw_mStatFormula"]),
        "ability_resource_occurrences": len(ability_resource_rows(occurrences)),
        "groups": {name: dict(counts) for name, counts in grouped.items()},
    }


def class_specific_inventory(stat_rows):
    focus_classes = {
        "StatByCoefficientCalculationPart",
        "StatByNamedDataValueCalculationPart",
        "StatBySubPartCalculationPart",
    }
    result = {}
    for class_name in sorted(focus_classes):
        rows = [row for row in stat_rows if row["calculation_class"] == class_name]
        result[class_name] = {
            "occurrence_count": len(rows),
            "signatures": dict(Counter(row["class_signature"] for row in rows)),
            "mStat_ids": sorted({row["raw_mStat"] for row in rows}),
            "mStatFormula_ids": sorted({row["effective_mStatFormula"] for row in rows}),
            "coefficient_fields": sorted(
                {key for row in rows for key in row["coefficient_fields"]}
            ),
            "data_value_fields": sorted(
                {key for row in rows for key in row["data_value_references"]}
            ),
            "subpart_fields": sorted({key for row in rows for key in row["subpart_fields"]}),
            "ownership_evidence": "OWNER_UNRESOLVED",
            "examples": [
                {
                    "champion": row["champion_id"],
                    "slot": row["slot"],
                    "path": row["graph_path"],
                    "mStat": row["raw_mStat"],
                    "mStatFormula": row["effective_mStatFormula"],
                }
                for row in rows[:3]
            ],
        }
    return result
