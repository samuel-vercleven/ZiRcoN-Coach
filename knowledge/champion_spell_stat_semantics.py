"""Evidence-gated Phase 2H champion spell stat semantics.

Phase 2H inventories and labels references.  It does not execute any spell
calculation class and does not alter the frozen Phase 2G evaluator.
"""

from __future__ import annotations

import copy
from collections import Counter, defaultdict

from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION, DATAMINE_COMMIT
from knowledge.champion_spell_stat_semantics_sources import (
    PHASE2H_VERSION,
    PINNED_GLOBAL_STAT_UI_MAPPING,
    SOURCE_REGISTRY,
)


STAT_REFERENCE_BRANCH = "STAT_REFERENCE"
ABILITY_RESOURCE_BRANCH = "ABILITY_RESOURCE"
FORMULA_WITHOUT_STAT_BRANCH = "FORMULA_WITHOUT_STAT"
RESOURCE_ENUM_RESEARCH_ONLY = "RESOURCE_ENUM_RESEARCH_ONLY"

VALIDATED = "VALIDATED"
STRONGLY_SUPPORTED = "STRONGLY_SUPPORTED"
AMBIGUOUS = "AMBIGUOUS"
CONTRADICTED = "CONTRADICTED"
UNRESOLVED = "UNRESOLVED"

BASE_STAT = "BASE_STAT"
BONUS_STAT = "BONUS_STAT"
TOTAL_STAT = "TOTAL_STAT"
STAT_FORMULA_UNRESOLVED = "STAT_FORMULA_UNRESOLVED"

OWNER_VALIDATED_CASTER = "OWNER_VALIDATED_CASTER"
OWNER_VALIDATED_TARGET = "OWNER_VALIDATED_TARGET"
OWNER_VALIDATED_SOURCE_LEVEL = "OWNER_VALIDATED_SOURCE_LEVEL"
OWNER_CONTEXT_DEPENDENT = "OWNER_CONTEXT_DEPENDENT"
OWNER_UNRESOLVED = "OWNER_UNRESOLVED"

SEMANTIC_REFERENCE_RESOLVED = "SEMANTIC_REFERENCE_RESOLVED"
STAT_ID_UNRESOLVED = "STAT_ID_UNRESOLVED"
STAT_FORMULA_UNRESOLVED_STATUS = "STAT_FORMULA_UNRESOLVED"
STAT_OWNER_UNRESOLVED = "STAT_OWNER_UNRESOLVED"
SNAPSHOT_FIELD_UNAVAILABLE = "SNAPSHOT_FIELD_UNAVAILABLE"
SEMANTIC_COMBINATION_UNSUPPORTED = "SEMANTIC_COMBINATION_UNSUPPORTED"

_VALIDATED_STAT_IDS = {1, 2, 12}
_OFFICIAL_STAT_EVIDENCE = {
    1: ["riot_patch_26_2"],
    2: ["riot_patch_9_2", "riot_patch_26_1"],
    12: ["riot_patch_9_24"],
}

# Phase 2G fields are only named here; the frozen snapshot builder is not
# imported or modified.  No BASE_STAT combination is admitted because native
# at level is not proven equivalent to every internal base-stat definition.
_SNAPSHOT_FIELDS = {
    ("ATTACK_DAMAGE", BONUS_STAT): "attack_damage_bonus",
    ("ATTACK_DAMAGE", TOTAL_STAT): "attack_damage_total",
    ("ARMOR", BONUS_STAT): "armor_bonus",
    ("ARMOR", TOTAL_STAT): "armor",
    ("HEALTH", BONUS_STAT): "health_bonus",
    ("HEALTH", TOTAL_STAT): "health_max",
}


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


def finalize_candidate_status(proposed_status, evidence, contradictions):
    """Apply Phase 2H's minimum evidence and blocking-contradiction policy."""
    if any(item.get("blocking", True) for item in contradictions):
        return CONTRADICTED
    independent_tiers = {
        item.get("tier") for item in evidence if item.get("tier") and not item.get("key_name_only")
    }
    if proposed_status == VALIDATED and len(independent_tiers) < 2:
        return STRONGLY_SUPPORTED
    return proposed_status


def _stat_examples(stat_rows, raw_stat_id, limit=5):
    rows = [row for row in stat_rows if row.get("raw_mStat") == raw_stat_id]
    champions = set()
    examples = []
    for row in rows:
        champion = row.get("champion_id")
        if champion in champions and len(champions) < 2:
            continue
        champions.add(champion)
        examples.append(
            {
                "champion": champion,
                "slot": row.get("slot"),
                "calculation_key": row.get("calculation_key"),
                "graph_path": row.get("graph_path"),
                "raw_mStatFormula": row.get("raw_mStatFormula"),
                "effective_mStatFormula": row.get("effective_mStatFormula"),
                "coefficient_fields": copy.deepcopy(row.get("coefficient_fields", {})),
                "data_value_references": copy.deepcopy(row.get("data_value_references", {})),
            }
        )
        if len(examples) >= limit:
            break
    return examples


def build_stat_semantic_records(observed_ids, stat_rows=()):
    """Build structured records for exactly the IDs discovered by the caller."""
    records = {}
    stat_rows = list(stat_rows)
    for raw_stat_id in sorted(set(observed_ids)):
        semantic = PINNED_GLOBAL_STAT_UI_MAPPING.get(raw_stat_id)
        matching_rows = [row for row in stat_rows if row.get("raw_mStat") == raw_stat_id]
        evidence = []
        contradictions = []
        if semantic is not None:
            evidence.append(
                {
                    "source_id": "league_datamines_global_stats_ui",
                    "tier": SOURCE_REGISTRY["league_datamines_global_stats_ui"]["tier"],
                    "finding": f"Direct mStatUIData object {raw_stat_id} identifies {semantic}.",
                    "key_name_only": False,
                }
            )
            if matching_rows:
                evidence.append(
                    {
                        "source_id": "exact_pinned_spell_occurrences",
                        "tier": "EXACT_PINNED_26_16_OCCURRENCE_CROSS_CHECK",
                        "finding": (
                            f"{len(matching_rows)} exact spell occurrences across "
                            f"{len({row.get('champion_id') for row in matching_rows})} champions."
                        ),
                        "key_name_only": False,
                    }
                )
        for source_id in _OFFICIAL_STAT_EVIDENCE.get(raw_stat_id, []):
            evidence.append(
                {
                    "source_id": source_id,
                    "tier": SOURCE_REGISTRY[source_id]["tier"],
                    "finding": SOURCE_REGISTRY[source_id]["supports"][0],
                    "key_name_only": False,
                }
            )
        if semantic is None:
            proposed = UNRESOLVED
            semantic = None
        elif raw_stat_id in _VALIDATED_STAT_IDS and matching_rows:
            proposed = VALIDATED
        else:
            proposed = STRONGLY_SUPPORTED
        status = finalize_candidate_status(proposed, evidence, contradictions)
        execution_eligible = status == VALIDATED
        records[raw_stat_id] = {
            "raw_stat_id": raw_stat_id,
            "status": status,
            "semantic_stat": semantic,
            "execution_eligible": execution_eligible,
            "evidence": evidence,
            "contradictions": contradictions,
            "contradiction_count": len(contradictions),
            "representative_examples": _stat_examples(stat_rows, raw_stat_id),
            "occurrence_count": len(matching_rows),
            "champion_count": len({row.get("champion_id") for row in matching_rows}),
            "provenance": {
                "phase2h_version": PHASE2H_VERSION,
                "pinned_commit": DATAMINE_COMMIT,
                "primary_source_id": (
                    "league_datamines_global_stats_ui" if semantic is not None else None
                ),
            },
            "cross_patch_stability": "UNCERTAIN",
            "notes": (
                "Exact pinned stat UI identity plus official independent mechanic evidence."
                if status == VALIDATED
                else "Exact stat UI identity lacks enough independent patch-specific evidence."
                if status == STRONGLY_SUPPORTED
                else "ID absent from the exact pinned GlobalStatsUIData table; no enum position inferred."
            ),
        }
    return records


def build_formula_semantic_records(raw_formula_ids, stat_rows=()):
    """Build records only for formula values observed on actual mStat nodes."""
    stat_rows = list(stat_rows)
    records = {}
    for raw_value in sorted(set(raw_formula_ids)):
        examples = [
            {
                "champion": row.get("champion_id"),
                "slot": row.get("slot"),
                "calculation_key": row.get("calculation_key"),
                "graph_path": row.get("graph_path"),
                "raw_mStat": row.get("raw_mStat"),
                "serialized": row.get("raw_mStatFormula_present"),
            }
            for row in stat_rows
            if row.get("effective_mStatFormula") == raw_value
        ][:6]
        if raw_value == 0:
            semantic = TOTAL_STAT
            evidence = [
                {
                    "source_id": "exact_pinned_aatrox_malphite_fixtures",
                    "tier": "EXACT_PINNED_26_16_OCCURRENCE_CROSS_CHECK",
                    "finding": "Implicit-zero Aatrox total-AD and Malphite armor structures.",
                    "key_name_only": False,
                },
                {
                    "source_id": "riot_patch_9_2",
                    "tier": SOURCE_REGISTRY["riot_patch_9_2"]["tier"],
                    "finding": SOURCE_REGISTRY["riot_patch_9_2"]["supports"][0],
                    "key_name_only": False,
                },
                {
                    "source_id": "riot_patch_26_2",
                    "tier": SOURCE_REGISTRY["riot_patch_26_2"]["tier"],
                    "finding": SOURCE_REGISTRY["riot_patch_26_2"]["supports"][0],
                    "key_name_only": False,
                },
            ]
            contradictions = [
                {
                    "source_id": "hextechdocs_historical",
                    "claim": "Historical table labels zero BASE.",
                    "blocking": False,
                    "reason": "Lower-tier historical claim conflicts with two exact-pinned mechanic fixtures.",
                },
                {
                    "source_id": "leaguebuilder_current_formula",
                    "claim": "Current cross-patch table labels zero BASE.",
                    "blocking": False,
                    "reason": "Not patch-pinned and its raw StatType numbering is incompatible with 26.16.",
                },
            ]
            proposed = VALIDATED
        elif raw_value == 2:
            semantic = BONUS_STAT
            evidence = [
                {
                    "source_id": "exact_pinned_akshan_diana_fixtures",
                    "tier": "EXACT_PINNED_26_16_OCCURRENCE_CROSS_CHECK",
                    "finding": "Explicit-two Akshan bonus-AD and Diana bonus-health structures.",
                    "key_name_only": False,
                },
                {
                    "source_id": "riot_patch_26_1",
                    "tier": SOURCE_REGISTRY["riot_patch_26_1"]["tier"],
                    "finding": SOURCE_REGISTRY["riot_patch_26_1"]["supports"][0],
                    "key_name_only": False,
                },
                {
                    "source_id": "riot_patch_9_24",
                    "tier": SOURCE_REGISTRY["riot_patch_9_24"]["tier"],
                    "finding": SOURCE_REGISTRY["riot_patch_9_24"]["supports"][0],
                    "key_name_only": False,
                },
                {
                    "source_id": "leaguebuilder_current_formula",
                    "tier": SOURCE_REGISTRY["leaguebuilder_current_formula"]["tier"],
                    "finding": "Current implementation also labels two BONUS.",
                    "key_name_only": False,
                },
            ]
            contradictions = [
                {
                    "source_id": "hextechdocs_historical",
                    "claim": "Historical table labels two TOTAL.",
                    "blocking": False,
                    "reason": "Lower-tier historical claim is contradicted by exact 26.16 official fixtures.",
                }
            ]
            proposed = VALIDATED
        elif raw_value == 1:
            semantic = STAT_FORMULA_UNRESOLVED
            evidence = [
                {
                    "source_id": "exact_pinned_mordekaiser_fixture",
                    "tier": "EXACT_PINNED_26_16_SINGLE_OCCURRENCE",
                    "finding": "One health reference does not distinguish base, bonus, or total.",
                    "key_name_only": False,
                }
            ]
            contradictions = [
                {
                    "source_id": "hextechdocs_historical",
                    "claim": "one BONUS",
                    "blocking": True,
                },
                {
                    "source_id": "leaguebuilder_current_formula",
                    "claim": "one TOTAL",
                    "blocking": True,
                },
            ]
            proposed = CONTRADICTED
        else:
            semantic = STAT_FORMULA_UNRESOLVED
            evidence = []
            contradictions = []
            proposed = UNRESOLVED
        status = finalize_candidate_status(proposed, evidence, contradictions)
        records[raw_value] = {
            "raw_formula_id": raw_value,
            "semantic_formula": semantic,
            "status": status,
            "execution_eligible": status == VALIDATED,
            "evidence": evidence,
            "contradictions": contradictions,
            "contradiction_count": len(contradictions),
            "representative_examples": examples,
            "occurrence_count": sum(
                row.get("effective_mStatFormula") == raw_value for row in stat_rows
            ),
            "provenance": {
                "phase2h_version": PHASE2H_VERSION,
                "pinned_commit": DATAMINE_COMMIT,
                "implicit_default_zero": raw_value == 0,
            },
            "notes": (
                "Only exact mStat-branch occurrences contribute; AbilityResource is excluded."
            ),
        }
    return records


def get_validated_stat_mapping(records=None):
    if records is None:
        records = build_stat_semantic_records(PINNED_GLOBAL_STAT_UI_MAPPING)
    return {
        raw_id: record["semantic_stat"]
        for raw_id, record in records.items()
        if record.get("status") == VALIDATED and record.get("execution_eligible") is True
    }


def get_validated_stat_formula_mapping(records=None):
    if records is None:
        records = build_formula_semantic_records((0, 1, 2))
    return {
        raw_id: record["semantic_formula"]
        for raw_id, record in records.items()
        if record.get("status") == VALIDATED and record.get("execution_eligible") is True
    }


def build_owner_semantic_records(stat_rows):
    """Keep every real owner unresolved; available sources do not prove identity."""
    return [
        {
            "occurrence_identity": row.get("occurrence_identity"),
            "champion": row.get("champion_id"),
            "slot": row.get("slot"),
            "graph_path": row.get("graph_path"),
            "owner_status": OWNER_UNRESOLVED,
            "status": UNRESOLVED,
            "execution_eligible": False,
            "evidence": [
                {
                    "source_id": "calcrev_historical",
                    "finding": "A unitStatComponent exists, but caster/target identity is not established.",
                }
            ],
            "notes": "No owner is inferred from common spell behavior or key names.",
        }
        for row in stat_rows
    ]


def audit_stat_mapping_contradictions(stat_records, stat_rows):
    """Account for every occurrence and retain any independent mismatch.

    Most exact occurrences do not independently name their stat, so absence of
    a counterexample is not promoted into positive evidence.
    """
    independent_expectations = {
        ("Malphite", "E", "mSpellCalculations/EDamageCalc/mFormulaParts/1"): "ARMOR",
        ("Aatrox", "Q", "mSpellCalculations/QDamage/mFormulaParts/1"): "ATTACK_DAMAGE",
        ("Akshan", "Q", "mSpellCalculations/FinalDamage/mFormulaParts/1"): "ATTACK_DAMAGE",
        ("Diana", "W", "mSpellCalculations/ShieldValue/mFormulaParts/2"): "HEALTH",
    }
    result = {}
    for raw_id, record in stat_records.items():
        rows = [row for row in stat_rows if row.get("raw_mStat") == raw_id]
        contradictions = []
        independently_checked = 0
        for row in rows:
            expected = independent_expectations.get(
                (row.get("champion_id"), row.get("slot"), row.get("graph_path"))
            )
            if expected is None:
                continue
            independently_checked += 1
            if expected != record.get("semantic_stat"):
                contradictions.append(
                    {
                        "champion": row.get("champion_id"),
                        "slot": row.get("slot"),
                        "graph_path": row.get("graph_path"),
                        "expected": expected,
                        "proposed": record.get("semantic_stat"),
                    }
                )
        result[raw_id] = {
            "occurrences_searched": len(rows),
            "independently_semantic_checked": independently_checked,
            "structurally_preserved_unlabelled": len(rows) - independently_checked,
            "contradictions": contradictions,
            "contradiction_count": len(contradictions),
        }
    return result


def compose_snapshot_reference(
    raw_stat_id,
    raw_formula_id,
    owner_status,
    stat_records,
    formula_records,
    caster_snapshot=None,
    target_snapshot=None,
):
    """Compose a Phase 2G field only after stat, formula, and owner validation."""
    if type(raw_stat_id) is not int or raw_stat_id not in get_validated_stat_mapping(stat_records):
        return {"status": STAT_ID_UNRESOLVED, "raw_stat_id": raw_stat_id}
    if type(raw_formula_id) is not int or raw_formula_id not in get_validated_stat_formula_mapping(formula_records):
        return {"status": STAT_FORMULA_UNRESOLVED_STATUS, "raw_formula_id": raw_formula_id}
    if owner_status not in {OWNER_VALIDATED_CASTER, OWNER_VALIDATED_TARGET}:
        return {"status": STAT_OWNER_UNRESOLVED, "owner_status": owner_status}
    semantic_stat = get_validated_stat_mapping(stat_records)[raw_stat_id]
    semantic_formula = get_validated_stat_formula_mapping(formula_records)[raw_formula_id]
    snapshot_field = _SNAPSHOT_FIELDS.get((semantic_stat, semantic_formula))
    if snapshot_field is None:
        return {
            "status": SEMANTIC_COMBINATION_UNSUPPORTED,
            "semantic_stat": semantic_stat,
            "semantic_formula": semantic_formula,
        }
    owner_key = "caster" if owner_status == OWNER_VALIDATED_CASTER else "target"
    snapshot = caster_snapshot if owner_key == "caster" else target_snapshot
    if not isinstance(snapshot, dict):
        return {
            "status": SNAPSHOT_FIELD_UNAVAILABLE,
            "snapshot_owner": owner_key,
            "snapshot_field": snapshot_field,
            "reason": "SNAPSHOT_NOT_PROVIDED",
        }
    stats = snapshot.get("stats", {})
    resolution = snapshot.get("stat_resolution", {})
    fact = resolution.get(snapshot_field, {})
    if snapshot_field not in stats or stats.get(snapshot_field) is None or fact.get("status") != "STATIC_STAT_RESOLVED":
        return {
            "status": SNAPSHOT_FIELD_UNAVAILABLE,
            "snapshot_owner": owner_key,
            "snapshot_field": snapshot_field,
            "reason": "PHASE2G_FIELD_NOT_FULLY_RESOLVED",
        }
    return {
        "status": SEMANTIC_REFERENCE_RESOLVED,
        "raw_stat_id": raw_stat_id,
        "raw_formula_id": raw_formula_id,
        "semantic_stat": semantic_stat,
        "semantic_formula": semantic_formula,
        "snapshot_owner": owner_key,
        "snapshot_field": snapshot_field,
        "value": stats[snapshot_field],
        "execution_performed": False,
    }
