"""Evidence-gated Phase 2I stat-owner inventory and contracts.

No production contract in v1 equates a champion spell stat reference with the
caster.  Ordinary serialized stat parts are classified as context-dependent:
reverse-engineered evaluators read the unit/champion supplied by their caller,
while the pinned graphs do not reveal that caller binding.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter, defaultdict

from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION, DATAMINE_COMMIT
from knowledge.champion_spell_stat_owner_sources import (
    OWNER_SEMANTICS_VERSION,
    PINNED_DDRAGON_VERSION,
    PINNED_GAME_PATCH,
    PINNED_LOCALE,
)
from knowledge.champion_spell_stat_semantics import (
    VALIDATED,
    build_formula_semantic_records,
    build_stat_semantic_records,
    get_validated_stat_formula_mapping,
    get_validated_stat_mapping,
    inventory_stat_semantic_occurrences,
    stat_reference_rows,
)


OWNER_VALIDATED_CASTER = "OWNER_VALIDATED_CASTER"
OWNER_VALIDATED_TARGET = "OWNER_VALIDATED_TARGET"
OWNER_VALIDATED_SOURCE_LEVEL = "OWNER_VALIDATED_SOURCE_LEVEL"
OWNER_VALIDATED_OTHER_CONTEXT = "OWNER_VALIDATED_OTHER_CONTEXT"
OWNER_CONTEXT_DEPENDENT = "OWNER_CONTEXT_DEPENDENT"
OWNER_STRONGLY_SUPPORTED_CASTER = "OWNER_STRONGLY_SUPPORTED_CASTER"
OWNER_STRONGLY_SUPPORTED_TARGET = "OWNER_STRONGLY_SUPPORTED_TARGET"
OWNER_AMBIGUOUS = "OWNER_AMBIGUOUS"
OWNER_CONTRADICTED = "OWNER_CONTRADICTED"
OWNER_UNRESOLVED = "OWNER_UNRESOLVED"

OWNER_CONTRACT_RESOLVED = "OWNER_CONTRACT_RESOLVED"
OWNER_CONTRACT_NOT_FOUND = "OWNER_CONTRACT_NOT_FOUND"
OWNER_SIGNATURE_MISMATCH = "OWNER_SIGNATURE_MISMATCH"
OWNER_CONTEXT_MISMATCH = "OWNER_CONTEXT_MISMATCH"
SOURCE_VERSION_MISMATCH = "SOURCE_VERSION_MISMATCH"

VALIDATED_OWNER_STATUSES = {
    OWNER_VALIDATED_CASTER,
    OWNER_VALIDATED_TARGET,
    OWNER_VALIDATED_SOURCE_LEVEL,
    OWNER_VALIDATED_OTHER_CONTEXT,
}
STAT_CLASSES = {
    "StatByCoefficientCalculationPart",
    "StatByNamedDataValueCalculationPart",
    "StatBySubPartCalculationPart",
}

# These are the six ordinary signatures actually observed in the pinned
# catalog.  The two variants with 0xa8cb9c14 are deliberately absent.
ORDINARY_CONTEXT_SIGNATURES = {
    ("StatByCoefficientCalculationPart", "mCoefficient|mStat|~class"),
    (
        "StatByCoefficientCalculationPart",
        "mCoefficient|mStat|mStatFormula|~class",
    ),
    ("StatByNamedDataValueCalculationPart", "mDataValue|mStat|~class"),
    (
        "StatByNamedDataValueCalculationPart",
        "mDataValue|mStat|mStatFormula|~class",
    ),
    ("StatBySubPartCalculationPart", "mStat|mSubpart|~class"),
    (
        "StatBySubPartCalculationPart",
        "mStat|mStatFormula|mSubpart|~class",
    ),
}

_OWNER_FIELD_PATTERN = re.compile(r"owner|caster|target|source.?unit|stat.?unit", re.I)


def _direct_container(graph_path):
    parts = str(graph_path or "").split("/")
    if not parts:
        return None
    if parts[-1].isdigit() and len(parts) > 1:
        return parts[-2]
    return parts[-1]


def _node_signature(node):
    payload = node.get("raw_node_payload") if isinstance(node, dict) else None
    return "|".join(sorted(payload)) if isinstance(payload, dict) else ""


def _ancestor_nodes(graph_path, node_index):
    parts = str(graph_path or "").split("/")
    ancestors = []
    for end in range(2, len(parts)):
        path = "/".join(parts[:end])
        node = node_index.get(path)
        if not isinstance(node, dict):
            continue
        payload = node.get("raw_node_payload")
        if not isinstance(payload, dict):
            continue
        scalar_fields = {
            key: copy.deepcopy(value)
            for key, value in payload.items()
            if key != "~class" and not isinstance(value, (dict, list))
        }
        ancestors.append(
            {
                "graph_path": path,
                "calculation_class": node.get("calculation_class"),
                "class_signature": _node_signature(node),
                "scalar_fields": scalar_fields,
                "potential_owner_selector_fields": {
                    key: value
                    for key, value in scalar_fields.items()
                    if _OWNER_FIELD_PATTERN.search(key)
                },
                "unresolved_hash_fields": {
                    key: value
                    for key, value in scalar_fields.items()
                    if key.startswith("0x") or (key.startswith("{") and key.endswith("}"))
                },
            }
        )
    return ancestors


def _tooltip_linkage(spell, calculation_key, frozen_linkage):
    spell_data = (spell.get("raw_spell_object") or {}).get("mSpell") or {}
    tooltip_data = (spell_data.get("mClientData") or {}).get("mTooltipData") or {}
    loc_keys = tooltip_data.get("mLocKeys") or {}
    token_patterns = (
        re.compile(rf"@{re.escape(str(calculation_key))}@", re.I),
        re.compile(rf"{{{{\s*{re.escape(str(calculation_key))}\s*}}}}", re.I),
    )
    matches = []
    for field, text in loc_keys.items():
        if not isinstance(text, str):
            continue
        if any(pattern.search(text) for pattern in token_patterns):
            matches.append({"field": field, "text": text})
    return {
        "status": "PINNED_TOOLTIP_CALCULATION_LINK_FOUND" if matches else "NO_EXACT_TOOLTIP_TOKEN_LINK",
        "calculation_key": calculation_key,
        "matches": matches,
        "frozen_phase2h_linkage": copy.deepcopy(frozen_linkage),
    }


def _context_signature(row, ancestors):
    context = {
        "direct_container": _direct_container(row.get("graph_path")),
        "root_class": (row.get("root_calculation_identity") or {}).get("calculation_class"),
        "ancestor_classes": [item.get("calculation_class") for item in ancestors],
        "ancestor_signatures": [item.get("class_signature") for item in ancestors],
    }
    encoded = json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return context, hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def inventory_owner_occurrences(catalog):
    """Enrich all 569 frozen Phase 2H stat rows with owner-relevant context."""
    base_rows = stat_reference_rows(inventory_stat_semantic_occurrences(catalog))
    stat_records = build_stat_semantic_records(
        sorted({row["raw_mStat"] for row in base_rows}), base_rows
    )
    formula_records = build_formula_semantic_records(
        sorted({row["effective_mStatFormula"] for row in base_rows}), base_rows
    )
    spell_index = {}
    for champion_id, champion in catalog.get("records", {}).items():
        for spell in champion.get("primary_spells", []):
            spell_index[(champion_id, spell.get("slot"))] = spell

    result = []
    for base in base_rows:
        row = copy.deepcopy(base)
        spell = spell_index.get((row.get("champion_id"), row.get("slot")), {})
        node_index = {
            node.get("graph_path"): node
            for node in spell.get("calculation_nodes", [])
            if isinstance(node, dict)
        }
        source_node = node_index.get(row.get("graph_path"), {})
        raw_payload = copy.deepcopy(source_node.get("raw_node_payload") or {})
        ancestors = _ancestor_nodes(row.get("graph_path"), node_index)
        structural_context, context_id = _context_signature(row, ancestors)
        stat_record = stat_records.get(row.get("raw_mStat"), {})
        formula_record = formula_records.get(row.get("effective_mStatFormula"), {})
        row.update(
            {
                "phase2i_owner_version": OWNER_SEMANTICS_VERSION,
                "exact_structural_signature": tuple(sorted(raw_payload)),
                "raw_node_payload": raw_payload,
                "structural_context": structural_context,
                "structural_context_signature": context_id,
                "ancestor_context": ancestors,
                "nearest_parent_calculation": ancestors[-1] if ancestors else None,
                "child_subpart_structure": copy.deepcopy(row.get("subpart_fields", {})),
                "tooltip_linkage": _tooltip_linkage(
                    spell,
                    row.get("calculation_key"),
                    row.get("tooltip_component_linkage"),
                ),
                "frozen_phase2h_stat_result": {
                    "raw_stat_id": row.get("raw_mStat"),
                    "semantic_stat": stat_record.get("semantic_stat"),
                    "status": stat_record.get("status"),
                    "execution_eligible": stat_record.get("execution_eligible"),
                    "provenance": copy.deepcopy(stat_record.get("provenance")),
                },
                "frozen_phase2h_formula_result": {
                    "raw_formula_id": row.get("effective_mStatFormula"),
                    "semantic_formula": formula_record.get("semantic_formula"),
                    "status": formula_record.get("status"),
                    "execution_eligible": formula_record.get("execution_eligible"),
                    "provenance": copy.deepcopy(formula_record.get("provenance")),
                },
                "source_provenance": {
                    "source_version": row.get("champion_spell_source_version"),
                    "source_commit": row.get("pinned_commit"),
                    "game_patch": PINNED_GAME_PATCH,
                    "ddragon_version": catalog.get("ddragon_version"),
                    "locale": catalog.get("locale"),
                },
            }
        )
        result.append(row)
    return result


def owner_contract_key(row):
    return (
        row.get("calculation_class"),
        row.get("class_signature"),
        row.get("structural_context_signature"),
    )


def _contract_id(key):
    encoded = json.dumps(key, ensure_ascii=False, separators=(",", ":"))
    return "owner:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def build_owner_contracts(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[owner_contract_key(row)].append(row)

    contracts = {}
    for key, matching in sorted(grouped.items(), key=lambda item: str(item[0])):
        class_name, signature, context_signature = key
        ordinary = (class_name, signature) in ORDINARY_CONTEXT_SIGNATURES
        source_match = all(
            row.get("source_provenance", {}).get("source_version")
            == CHAMPION_SPELL_SOURCE_VERSION
            and row.get("source_provenance", {}).get("source_commit") == DATAMINE_COMMIT
            for row in matching
        )
        selector_fields = [
            field
            for row in matching
            for ancestor in row.get("ancestor_context", [])
            for field in ancestor.get("potential_owner_selector_fields", {})
        ]
        if ordinary and source_match and not selector_fields:
            owner_status = OWNER_CONTEXT_DEPENDENT
            semantic_owner = "CALCULATION_INPUT_UNIT_UNBOUND"
            evidence = [
                "pinned_26_16_spell_graphs",
                "meta_classes_26_16",
                "calcrev_runtime_interface",
                "calcrev_stat_part_execution",
                "leaguebuilder_context_execution",
            ]
            limitation = (
                "The stat subject is supplied by evaluation context; the pinned serialized "
                "graph does not prove whether the 26.16 caller binds caster, target, or another unit."
            )
        else:
            owner_status = OWNER_UNRESOLVED
            semantic_owner = None
            evidence = ["pinned_26_16_spell_graphs", "meta_classes_26_16"]
            limitation = (
                "Unknown signature field, source mismatch, or potential selector prevents even "
                "a generic context-subject contract."
            )
        contracts[key] = {
            "contract_id": _contract_id(key),
            "contract_key": key,
            "calculation_class": class_name,
            "exact_signature": signature,
            "structural_context_signature": context_signature,
            "structural_context": copy.deepcopy(matching[0].get("structural_context")),
            "owner_status": owner_status,
            "semantic_owner": semantic_owner,
            "execution_eligible": owner_status in VALIDATED_OWNER_STATUSES,
            "evidence_source_ids": evidence,
            "limitations": [limitation],
            "occurrence_count": len(matching),
            "champions": sorted({row.get("champion_id") for row in matching}),
            "examples": [
                {
                    "champion": row.get("champion_id"),
                    "slot": row.get("slot"),
                    "calculation_key": row.get("calculation_key"),
                    "graph_path": row.get("graph_path"),
                }
                for row in matching[:4]
            ],
            "contradictions": [],
            "potential_owner_selector_fields": sorted(set(selector_fields)),
            "provenance": {
                "phase2i_version": OWNER_SEMANTICS_VERSION,
                "source_commit": DATAMINE_COMMIT,
                "contract_granularity": "CLASS_EXACT_SIGNATURE_STRUCTURAL_CONTEXT",
            },
        }
    return contracts


def resolve_owner_contract(row, contracts):
    provenance = row.get("source_provenance", {})
    if (
        provenance.get("source_version") != CHAMPION_SPELL_SOURCE_VERSION
        or provenance.get("source_commit") != DATAMINE_COMMIT
    ):
        return {
            "status": SOURCE_VERSION_MISMATCH,
            "owner_status": OWNER_UNRESOLVED,
            "execution_eligible": False,
        }
    key = owner_contract_key(row)
    contract = contracts.get(key)
    if contract is None:
        same_class_context = any(
            candidate[0] == key[0] and candidate[2] == key[2] for candidate in contracts
        )
        same_class_signature = any(
            candidate[0] == key[0] and candidate[1] == key[1] for candidate in contracts
        )
        status = (
            OWNER_SIGNATURE_MISMATCH
            if same_class_context
            else OWNER_CONTEXT_MISMATCH
            if same_class_signature
            else OWNER_CONTRACT_NOT_FOUND
        )
        return {
            "status": status,
            "owner_status": OWNER_UNRESOLVED,
            "execution_eligible": False,
            "contract_key": key,
        }
    return {
        "status": OWNER_CONTRACT_RESOLVED,
        "owner_status": contract["owner_status"],
        "semantic_owner": contract.get("semantic_owner"),
        "execution_eligible": contract["owner_status"] in VALIDATED_OWNER_STATUSES,
        "contract_id": contract.get("contract_id"),
        "contract_key": key,
        "provenance": copy.deepcopy(contract.get("provenance", {})),
        "evidence_source_ids": list(contract.get("evidence_source_ids", [])),
        "damage_target_role_consumed": False,
    }


def build_owner_records(rows, contracts=None):
    contracts = contracts or build_owner_contracts(rows)
    return [
        {
            "occurrence_identity": row.get("occurrence_identity"),
            "champion": row.get("champion_id"),
            "slot": row.get("slot"),
            "calculation_key": row.get("calculation_key"),
            "graph_path": row.get("graph_path"),
            "class_signature": row.get("class_signature"),
            "structural_context_signature": row.get("structural_context_signature"),
            **resolve_owner_contract(row, contracts),
        }
        for row in rows
    ]


def build_execution_gate(rows, owner_records):
    stat_records = build_stat_semantic_records(
        sorted({row["raw_mStat"] for row in rows}), rows
    )
    formula_records = build_formula_semantic_records(
        sorted({row["effective_mStatFormula"] for row in rows}), rows
    )
    stat_map = get_validated_stat_mapping(stat_records)
    formula_map = get_validated_stat_formula_mapping(formula_records)
    blockers = Counter()
    eligible = []
    for row, owner in zip(rows, owner_records):
        if row.get("raw_mStat") not in stat_map:
            blockers["STAT_ID_NOT_EXECUTION_ELIGIBLE"] += 1
        elif row.get("effective_mStatFormula") not in formula_map:
            blockers["STAT_FORMULA_NOT_EXECUTION_ELIGIBLE"] += 1
        elif not owner.get("execution_eligible"):
            blockers["STAT_OWNER_NOT_EXECUTION_ELIGIBLE"] += 1
        else:
            eligible.append(row.get("occurrence_identity"))
    return {
        "stat_rows": len(rows),
        "execution_eligible_occurrences": len(eligible),
        "eligible_occurrence_identities": eligible,
        "blockers": dict(blockers),
        "gate_passed": bool(eligible),
        "branch_b_status": "OPEN" if eligible else "NOT_STARTED_GATE_ZERO",
        "frozen_stat_map": stat_map,
        "frozen_formula_map": formula_map,
        "owner_guess_count": 0,
    }


def summarize_owner_inventory(rows, contracts, owner_records):
    return {
        "stat_rows": len(rows),
        "class_counts": dict(Counter(row.get("calculation_class") for row in rows)),
        "signature_counts": dict(Counter(row.get("class_signature") for row in rows)),
        "context_contract_count": len(contracts),
        "owner_status_counts": dict(
            Counter(record.get("owner_status") for record in owner_records)
        ),
        "execution_eligible_owner_occurrences": sum(
            bool(record.get("execution_eligible")) for record in owner_records
        ),
        "tooltip_linked_occurrences": sum(
            row.get("tooltip_linkage", {}).get("status")
            == "PINNED_TOOLTIP_CALCULATION_LINK_FOUND"
            for row in rows
        ),
        "frozen_stat_validated_occurrences": sum(
            row.get("frozen_phase2h_stat_result", {}).get("status") == VALIDATED
            for row in rows
        ),
        "frozen_formula_validated_occurrences": sum(
            row.get("frozen_phase2h_formula_result", {}).get("status") == VALIDATED
            for row in rows
        ),
    }
