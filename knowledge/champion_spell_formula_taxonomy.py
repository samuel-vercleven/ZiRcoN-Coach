"""Dynamic, conservative taxonomy of frozen Phase 2F calculation classes."""
from __future__ import annotations

from collections import Counter, defaultdict

TAXONOMY_VERSION = "champion_spell_formula_taxonomy_phase2g_v1"
SEMANTICS_VALIDATED_EXECUTABLE = "SEMANTICS_VALIDATED_EXECUTABLE"
SEMANTICS_PARTIALLY_VALIDATED = "SEMANTICS_PARTIALLY_VALIDATED"
CONTEXT_DEPENDENT_NOT_EXECUTABLE = "CONTEXT_DEPENDENT_NOT_EXECUTABLE"
STRUCTURAL_CONTAINER_ONLY = "STRUCTURAL_CONTAINER_ONLY"
UNRESOLVED_CLASS_SEMANTICS = "UNRESOLVED_CLASS_SEMANTICS"
NON_NUMERIC_OR_NOT_RELEVANT = "NON_NUMERIC_OR_NOT_RELEVANT"

# Only exact source field contracts used by the evaluator are accepted here.
# This is deliberately smaller than the observed class set.
CLASS_CONTRACTS = {
    "NumberCalculationPart": (SEMANTICS_VALIDATED_EXECUTABLE, ("mNumber",)),
    "NamedDataValueCalculationPart": (SEMANTICS_VALIDATED_EXECUTABLE, ("mDataValue",)),
    "SumOfSubPartsCalculationPart": (SEMANTICS_VALIDATED_EXECUTABLE, ("mSubparts",)),
    "ProductOfSubPartsCalculationPart": (SEMANTICS_VALIDATED_EXECUTABLE, ("mPart1", "mPart2")),
    "GameCalculation": (STRUCTURAL_CONTAINER_ONLY, ("mFormulaParts",)),
    "StatByCoefficientCalculationPart": (SEMANTICS_PARTIALLY_VALIDATED, ("mStat", "mCoefficient")),
    "StatByNamedDataValueCalculationPart": (SEMANTICS_PARTIALLY_VALIDATED, ("mStat", "mDataValue")),
    "NamedGameCalculationCalculationPart": (SEMANTICS_PARTIALLY_VALIDATED, ("mSpellCalculationKey",)),
}


def structural_signature(node):
    return tuple(sorted(node.get("field_names") or ()))


def classify_node(node):
    class_name = node.get("calculation_class")
    if class_name is None:
        return STRUCTURAL_CONTAINER_ONLY
    contract = CLASS_CONTRACTS.get(class_name)
    if contract is None:
        return UNRESOLVED_CLASS_SEMANTICS
    status, required = contract
    fields = set(node.get("field_names") or ())
    return status if set(required).issubset(fields) else UNRESOLVED_CLASS_SEMANTICS


def build_taxonomy(catalog):
    rows = defaultdict(lambda: {"count": 0, "champions": set(), "slots": set(), "calculation_keys": set(), "depths": Counter(), "fields": Counter(), "signatures": Counter(), "statuses": Counter(), "examples": []})
    for champion in catalog.get("records", {}).values():
        for spell in champion.get("primary_spells", []):
            for node in spell.get("calculation_nodes", []):
                class_name = node.get("calculation_class")
                if class_name is None:
                    continue
                row = rows[class_name]
                row["count"] += 1
                row["champions"].add(spell.get("champion_id"))
                row["slots"].add(spell.get("slot"))
                path = node.get("graph_path", "")
                parts = path.split("/")
                if len(parts) > 1:
                    row["calculation_keys"].add(parts[1])
                row["depths"][path.count("/")] += 1
                row["fields"].update(node.get("field_names") or ())
                row["signatures"][structural_signature(node)] += 1
                row["statuses"][classify_node(node)] += 1
                if len(row["examples"]) < 2:
                    row["examples"].append(node.get("raw_node_payload"))
    return {
        "version": TAXONOMY_VERSION,
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
