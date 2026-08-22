from collections import Counter

from knowledge.champion_spell_formula_evaluator import evaluate_calculation
from knowledge.champion_spell_formula_taxonomy import SUPPORTED_SIGNATURES
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog
from knowledge.combat_formula_types import RESOLVED


def _walk_results(result):
    yield result
    for child in result.child_results:
        yield from _walk_results(child)


def build_audit(catalog=None):
    catalog = catalog or get_pinned_spell_catalog()
    counts = Counter()
    resolved_node_signatures = Counter()
    evaluated_node_signatures = Counter()
    for class_name, signatures in SUPPORTED_SIGNATURES.items():
        for signature in signatures:
            resolved_node_signatures[(class_name, signature)] = 0
            evaluated_node_signatures[(class_name, signature)] = 0
    unregistered_arithmetic = []
    failures = []
    total = 0
    for champion in catalog["records"].values():
        for spell in champion["primary_spells"]:
            for key in spell.get("raw_calculation_names", []):
                total += 1
                try:
                    result = evaluate_calculation(spell, key, {"spell_rank": 1, "max_rank": 5})
                except Exception as exc:
                    counts["UNEXPECTED_EXCEPTION"] += 1
                    failures.append((spell.get("champion_id"), spell.get("slot"), key, type(exc).__name__))
                    continue
                counts[result.status] += 1
                for node_result in _walk_results(result):
                    signature = (
                        node_result.raw_class,
                        tuple(node_result.provenance.get("structural_signature", ())),
                    )
                    evaluated_node_signatures[signature] += 1
                    if node_result.status == RESOLVED:
                        resolved_node_signatures[signature] += 1
                        if not node_result.provenance.get("signature_registered"):
                            unregistered_arithmetic.append(
                                (spell.get("champion_id"), spell.get("slot"), key, node_result.graph_path, signature)
                            )
    return {
        "total": total,
        "counts": counts,
        "examples": failures,
        "catalog": catalog,
        "evaluated_node_signatures": evaluated_node_signatures,
        "resolved_node_signatures": resolved_node_signatures,
        "unregistered_arithmetic": unregistered_arithmetic,
    }


def main():
    audit = build_audit()
    print(f"Total calculations: {audit['total']}")
    print(f"Statuses: {dict(audit['counts'])}")
    print(f"Resolved numeric node signatures: {dict(audit['resolved_node_signatures'])}")
    print(f"Arithmetic under unregistered signature: {audit['unregistered_arithmetic'][:10]}")
    print(f"Unexpected examples: {audit['examples'][:5]}")
    ok = audit["total"] == 1443 and not audit["examples"] and not audit["unregistered_arithmetic"]
    print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
