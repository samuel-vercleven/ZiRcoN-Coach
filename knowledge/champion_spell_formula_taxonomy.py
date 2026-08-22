"""Exact-signature taxonomy for frozen Phase 2F calculation graphs."""
from __future__ import annotations

from collections import Counter, defaultdict

TAXONOMY_VERSION = "champion_spell_formula_taxonomy_phase2g_v2"
SEMANTICS_VALIDATED_EXECUTABLE = "SEMANTICS_VALIDATED_EXECUTABLE"
SEMANTICS_PARTIALLY_VALIDATED = "SEMANTICS_PARTIALLY_VALIDATED"
CONTEXT_DEPENDENT_NOT_EXECUTABLE = "CONTEXT_DEPENDENT_NOT_EXECUTABLE"
STRUCTURAL_CONTAINER_ONLY = "STRUCTURAL_CONTAINER_ONLY"
UNRESOLVED_CLASS_SEMANTICS = "UNRESOLVED_CLASS_SEMANTICS"
NON_NUMERIC_OR_NOT_RELEVANT = "NON_NUMERIC_OR_NOT_RELEVANT"


def _signature(*fields):
    return tuple(sorted(fields))


# Every entry is an exact pinned 26.16 signature. No subset matching is used.
# The examples identify the real source shape minimized in precision checks.
SUPPORTED_SIGNATURES = {
    "NumberCalculationPart": {
        _signature("mNumber", "~class"): {
            "status": SEMANTICS_VALIDATED_EXECUTABLE,
            "contract": "Return the finite numeric mNumber value.",
            "evidence": "Aatrox/Q/QEdgeDamage/mMultiplier/mSubparts/0",
        },
    },
    "NamedDataValueCalculationPart": {
        _signature("mDataValue", "~class"): {
            "status": SEMANTICS_VALIDATED_EXECUTABLE,
            "contract": "Resolve the exact per-spell DataValue name at spell rank.",
            "evidence": "Ahri/Q/TotalDamage/mFormulaParts/0",
        },
    },
    "SumOfSubPartsCalculationPart": {
        _signature("mSubparts", "~class"): {
            "status": SEMANTICS_VALIDATED_EXECUTABLE,
            "contract": "Add every resolved mSubparts child.",
            "evidence": "Aatrox/Q/QEdgeDamage/mMultiplier",
        },
    },
    "ProductOfSubPartsCalculationPart": {
        _signature("mPart1", "mPart2", "~class"): {
            "status": SEMANTICS_VALIDATED_EXECUTABLE,
            "contract": "Multiply the resolved mPart1 and mPart2 children.",
            "evidence": "Akshan/E/CriticalCalc/mMultiplier/mSubparts/1",
        },
    },
    "GameCalculation": {
        _signature("mFormulaParts", "~class"): {
            "status": SEMANTICS_VALIDATED_EXECUTABLE,
            "contract": "Add every resolved mFormulaParts child; no modifier/display fields accepted.",
            "evidence": "Ahri/R/RCalculatedDamage",
        },
    },
    "NamedGameCalculationCalculationPart": {
        _signature("mSpellCalculationKey", "~class"): {
            "status": SEMANTICS_VALIDATED_EXECUTABLE,
            "contract": "Resolve an exact named calculation key with cycle protection.",
            "evidence": "Ambessa/Q/0x1442dbe0/mMultiplier",
        },
    },
}

PARTIALLY_VALIDATED_CLASSES = {
    "StatByCoefficientCalculationPart",
    "StatByNamedDataValueCalculationPart",
    "StatBySubPartCalculationPart",
}


def structural_signature(node):
    if "field_names" in node:
        fields = node.get("field_names") or ()
    else:
        fields = node.keys() if isinstance(node, dict) else ()
    return tuple(sorted(fields))


def signature_contract(class_name, signature):
    return SUPPORTED_SIGNATURES.get(class_name, {}).get(tuple(signature))


def classify_node(node):
    class_name = node.get("calculation_class") or node.get("~class")
    if class_name is None:
        return STRUCTURAL_CONTAINER_ONLY
    contract = signature_contract(class_name, structural_signature(node))
    if contract is not None:
        return contract["status"]
    if class_name in PARTIALLY_VALIDATED_CLASSES:
        return SEMANTICS_PARTIALLY_VALIDATED
    return UNRESOLVED_CLASS_SEMANTICS


def build_taxonomy(catalog):
    rows = defaultdict(
        lambda: {
            "count": 0,
            "champions": set(),
            "slots": set(),
            "calculation_keys": set(),
            "depths": Counter(),
            "fields": Counter(),
            "signatures": Counter(),
            "statuses": Counter(),
            "examples": [],
        }
    )
    for champion in catalog.get("records", {}).values():
        for spell in champion.get("primary_spells", []):
            for node in spell.get("calculation_nodes", []):
                class_name = node.get("calculation_class")
                if class_name is None:
                    continue
                row = rows[class_name]
                signature = structural_signature(node)
                row["count"] += 1
                row["champions"].add(spell.get("champion_id"))
                row["slots"].add(spell.get("slot"))
                path = node.get("graph_path", "")
                parts = path.split("/")
                if len(parts) > 1:
                    row["calculation_keys"].add(parts[1])
                row["depths"][path.count("/")] += 1
                row["fields"].update(node.get("field_names") or ())
                row["signatures"][signature] += 1
                row["statuses"][classify_node(node)] += 1
                if len(row["examples"]) < 2:
                    row["examples"].append(node.get("raw_node_payload"))
    return {
        "version": TAXONOMY_VERSION,
        "supported_signatures": {
            name: {"|".join(signature): contract for signature, contract in signatures.items()}
            for name, signatures in SUPPORTED_SIGNATURES.items()
        },
        "classes": {
            name: {
                **row,
                "champions": sorted(row["champions"]),
                "slots": sorted(row["slots"]),
                "calculation_keys": sorted(row["calculation_keys"]),
                "depths": dict(row["depths"]),
                "fields": dict(row["fields"]),
                "signatures": {"|".join(sig): count for sig, count in row["signatures"].items()},
                "statuses": dict(row["statuses"]),
            }
            for name, row in sorted(rows.items())
        },
    }
