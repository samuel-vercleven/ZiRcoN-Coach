"""Conservative recursive evaluator gated by exact structural signatures."""
from __future__ import annotations

from math import isfinite

from knowledge.champion_spell_data_value_resolver import (
    DATA_VALUE_AMBIGUOUS,
    DATA_VALUE_NOT_FOUND,
    DATA_VALUE_RESOLVED,
    build_registry,
    resolve_data_value,
)
from knowledge.champion_spell_formula_taxonomy import (
    SUPPORTED_SIGNATURES,
    signature_contract,
    structural_signature,
)
from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION, DATAMINE_COMMIT
from knowledge.champion_spell_value_resolver import PINNED_RANK_0_TO_6
from knowledge.combat_formula_types import *

EVALUATOR_VERSION = "champion_spell_formula_evaluator_phase2g_v2"


def _result(status, node, path, key, **kwargs):
    signature = structural_signature(node) if isinstance(node, dict) else ()
    class_name = node.get("~class") if isinstance(node, dict) else None
    contract = signature_contract(class_name, signature)
    provenance = {
        "evaluator_version": EVALUATOR_VERSION,
        "source_version": CHAMPION_SPELL_SOURCE_VERSION,
        "source_commit": DATAMINE_COMMIT,
        "structural_signature": signature,
        "signature_registered": contract is not None,
        "signature_evidence": contract.get("evidence") if contract else None,
    }
    return EvaluationResult(
        status=status,
        raw_class=class_name,
        graph_path=path,
        calculation_key=key,
        provenance=provenance,
        **kwargs,
    )


def _children(node, field, calculations, context, path, key, stack, depth, max_depth):
    values = node.get(field)
    if not isinstance(values, list):
        return None
    return [
        _evaluate(item, calculations, context, f"{path}/{field}/{index}", key, stack, depth + 1, max_depth)
        for index, item in enumerate(values)
    ]


def _combine(children, node, path, key, product=False):
    resolved = [child.value for child in children if child.status == RESOLVED and child.value is not None]
    if len(resolved) != len(children):
        partial = None
        if resolved:
            partial = 1.0 if product else 0.0
            for value in resolved:
                partial = partial * value if product else partial + value
        return _result(
            PARTIALLY_RESOLVED,
            node,
            path,
            key,
            child_results=children,
            known_partial_value=partial,
            unresolved_reasons=[child.status for child in children if child.status != RESOLVED],
        )
    value = 1.0 if product else 0.0
    for item in resolved:
        value = value * item if product else value + item
    if not isfinite(value):
        return _result(NON_NUMERIC_RESULT, node, path, key, child_results=children)
    return _result(RESOLVED, node, path, key, value=value, child_results=children)


def _evaluate(node, calculations, context, path, key, stack, depth, max_depth):
    if depth > max_depth:
        return _result(MAX_RECURSION_DEPTH, node if isinstance(node, dict) else {}, path, key)
    if not isinstance(node, dict):
        return _result(MALFORMED_NODE, {}, path, key)
    class_name = node.get("~class")
    if class_name is None:
        return _result(UNSUPPORTED_CLASS, node, path, key, unresolved_reasons=["NO_CALCULATION_CLASS_EXPOSED"])

    if class_name in SUPPORTED_SIGNATURES and signature_contract(class_name, structural_signature(node)) is None:
        return _result(
            UNSUPPORTED_SIGNATURE,
            node,
            path,
            key,
            unresolved_reasons=["EXACT_SIGNATURE_NOT_REGISTERED"],
        )

    if class_name == "NumberCalculationPart":
        value = node["mNumber"]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value):
            return _result(NON_NUMERIC_RESULT, node, path, key)
        return _result(RESOLVED, node, path, key, value=float(value))

    if class_name == "NamedDataValueCalculationPart":
        name = node["mDataValue"]
        if not isinstance(name, str):
            return _result(UNSUPPORTED_SIGNATURE, node, path, key)
        resolved = resolve_data_value(
            context.get("data_values", {}),
            name,
            context.get("spell_rank"),
            context.get("max_rank"),
            context.get("data_value_indexing_contract", PINNED_RANK_0_TO_6),
        )
        statuses = {
            DATA_VALUE_NOT_FOUND: MISSING_DATA_VALUE,
            DATA_VALUE_AMBIGUOUS: AMBIGUOUS_DATA_VALUE,
        }
        if resolved["status"] == DATA_VALUE_RESOLVED:
            return _result(RESOLVED, node, path, key, value=float(resolved["value"]), dependencies=[name])
        return _result(
            statuses.get(resolved["status"], INVALID_SPELL_RANK),
            node,
            path,
            key,
            dependencies=[name],
            unresolved_reasons=[resolved["status"]],
        )

    if class_name == "SumOfSubPartsCalculationPart":
        children = _children(node, "mSubparts", calculations, context, path, key, stack, depth, max_depth)
        return _result(UNSUPPORTED_SIGNATURE, node, path, key) if children is None else _combine(children, node, path, key)

    if class_name == "ProductOfSubPartsCalculationPart":
        children = [
            _evaluate(node[field], calculations, context, f"{path}/{field}", key, stack, depth + 1, max_depth)
            for field in ("mPart1", "mPart2")
        ]
        return _combine(children, node, path, key, product=True)

    if class_name == "GameCalculation":
        children = _children(node, "mFormulaParts", calculations, context, path, key, stack, depth, max_depth)
        return _result(UNSUPPORTED_SIGNATURE, node, path, key) if children is None else _combine(children, node, path, key)

    if class_name == "NamedGameCalculationCalculationPart":
        reference = node["mSpellCalculationKey"]
        if not isinstance(reference, str):
            return _result(UNSUPPORTED_SIGNATURE, node, path, key)
        if reference not in calculations:
            return _result(NAMED_CALCULATION_NOT_FOUND, node, path, key, dependencies=[reference])
        if reference in stack:
            return _result(CYCLE_DETECTED, node, path, key, dependencies=[reference])
        child = _evaluate(
            calculations[reference],
            calculations,
            context,
            f"mSpellCalculations/{reference}",
            reference,
            stack + (reference,),
            depth + 1,
            max_depth,
        )
        if child.status == RESOLVED:
            return _result(
                RESOLVED,
                node,
                path,
                key,
                value=child.value,
                dependencies=[reference, *child.dependencies],
                child_results=[child],
            )
        return _result(
            child.status,
            node,
            path,
            key,
            dependencies=[reference, *child.dependencies],
            required_context=child.required_context,
            unresolved_reasons=child.unresolved_reasons or [child.status],
            child_results=[child],
            known_partial_value=child.known_partial_value,
        )

    if class_name in {
        "StatByCoefficientCalculationPart",
        "StatByNamedDataValueCalculationPart",
        "StatBySubPartCalculationPart",
    }:
        return _result(
            UNRESOLVED_STAT_REFERENCE,
            node,
            path,
            key,
            required_context=["validated_stat_mapping_and_owner"],
        )
    return _result(UNSUPPORTED_CLASS, node, path, key)


def evaluate_calculation(spell_record, calculation_key, context=None, max_depth=32):
    context = dict(context or {})
    if spell_record.get("champion_spell_source_version") != CHAMPION_SPELL_SOURCE_VERSION:
        return EvaluationResult(status=SOURCE_VERSION_MISMATCH, calculation_key=calculation_key)
    calculations = spell_record.get("raw_m_spell_calculations")
    if not isinstance(calculations, dict):
        return EvaluationResult(status=MALFORMED_NODE, calculation_key=calculation_key)
    if calculation_key not in calculations:
        return EvaluationResult(status=NAMED_CALCULATION_NOT_FOUND, calculation_key=calculation_key)
    context.setdefault("data_values", build_registry(spell_record.get("raw_data_values")))
    return _evaluate(
        calculations[calculation_key],
        calculations,
        context,
        f"mSpellCalculations/{calculation_key}",
        calculation_key,
        (calculation_key,),
        0,
        max_depth,
    )
