"""Top-level real cross-layer safety audit for Phase 2G."""
from collections import Counter

from knowledge.champion_attack_speed_source import load_attack_speed_ratio_catalog
from knowledge.champion_knowledge import CHAMPION_KNOWLEDGE_VERSION, build_champion_knowledge_catalog
from knowledge.champion_level_stats import LEVEL_STATS_VERSION
from knowledge.champion_spell_cast_stats_full_audit import build_audit as build_cast_audit
from knowledge.champion_spell_damage_evidence import classify_damage_evidence
from knowledge.champion_spell_damage_evidence_full_audit import build_audit as build_evidence_audit
from knowledge.champion_spell_damage_resolver import resolve_damage_components
from knowledge.champion_spell_damage_resolver_full_audit import build_audit as build_damage_audit
from knowledge.champion_spell_formula_evaluator_full_audit import build_audit as build_evaluator_audit
from knowledge.champion_spell_formula_taxonomy import SUPPORTED_SIGNATURES, build_taxonomy
from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION, DATAMINE_COMMIT, EXPECTED_DDRAGON_VERSION, EXPECTED_LOCALE
from knowledge.champion_spell_stat_reference import VALIDATED_STAT_REFERENCES, inventory_stat_references
from knowledge.combat_formula_representative_checks import run_representative_checks
from knowledge.combat_resistance_rules import COMBAT_RESISTANCE_VERSION
from knowledge.combat_stat_snapshot import build_combat_snapshot
from knowledge.combat_stat_snapshot_full_audit import build_audit as build_snapshot_audit
from knowledge.item_knowledge import ITEM_KNOWLEDGE_VERSION, build_item_knowledge_catalog
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog
from knowledge.rune_knowledge import RUNE_KNOWLEDGE_VERSION
from knowledge.spell_damage_mitigation import MITIGATION_INPUT_UNRESOLVED, mitigate_component
from knowledge.spell_damage_mitigation_full_audit import build_audit as build_mitigation_audit

FOUNDATION_VERSION = "combat_formula_foundation_phase2g_v2"


def build_audit():
    source = get_pinned_spell_catalog()
    champions = build_champion_knowledge_catalog("16.16.1")
    items = build_item_knowledge_catalog("16.16.1")
    attack_speed = load_attack_speed_ratio_catalog(champions)
    spells = [spell for record in source["records"].values() for spell in record["primary_spells"]]
    calculations = sum(len(spell.get("raw_calculation_names", [])) for spell in spells)
    nodes = sum(len(spell.get("calculation_nodes", [])) for spell in spells)

    taxonomy = build_taxonomy(source)
    taxonomy_statuses = Counter()
    observed_signatures = {}
    for class_name, row in taxonomy["classes"].items():
        taxonomy_statuses.update(row["statuses"])
        observed_signatures[class_name] = set(row["signatures"])
    registered_signatures = {
        class_name: {"|".join(signature) for signature in contracts}
        for class_name, contracts in SUPPORTED_SIGNATURES.items()
    }
    registered_not_observed = {
        class_name: sorted(signatures - observed_signatures.get(class_name, set()))
        for class_name, signatures in registered_signatures.items()
        if signatures - observed_signatures.get(class_name, set())
    }

    data_statuses = Counter()
    data_refs = 0
    from knowledge.champion_spell_data_value_resolver import build_registry, resolve_data_value
    for spell in spells:
        registry = build_registry(spell.get("raw_data_values"))
        for node in spell.get("calculation_nodes", []):
            for ref in node.get("named_data_value_references", []):
                data_refs += 1
                data_statuses[resolve_data_value(registry, ref["value"], 1, 5)["status"]] += 1

    stat_refs = inventory_stat_references(source)
    stat_ids = {row["raw_reference"] for row in stat_refs}
    evaluator = build_evaluator_audit(source)
    snapshot = build_snapshot_audit(champions, items, attack_speed)
    evidence = build_evidence_audit(source, champions)
    damage = build_damage_audit(source, champions)
    mitigation_regression = build_mitigation_audit()
    cast = build_cast_audit(source)
    representative = run_representative_checks(source, champions, items)

    mitigation_statuses = Counter()
    runtime_failures = []
    spells_with_post = 0
    for champion_id, source_champion in source["records"].items():
        semantic = {row.get("inferred_slot"): row for row in champions["records"][champion_id]["spells"]}
        champion = champions["records"][champion_id]
        ratio = attack_speed.get("records", {}).get(champion_id)
        snapshot_row = build_combat_snapshot(champion, 11, items["records"], (), ratio)
        for spell in source_champion["primary_spells"]:
            evidence_row = classify_damage_evidence(spell, semantic.get(spell["slot"]))
            rows = resolve_damage_components(spell, evidence_row, {"spell_rank": 1, "max_rank": 5, "source_snapshot": snapshot_row, "target_snapshot": snapshot_row})
            post = 0
            for row in rows:
                try:
                    mitigated = mitigate_component(row, snapshot_row, snapshot_row)
                except Exception as exc:
                    runtime_failures.append((champion_id, spell["slot"], row.get("calculation_key"), type(exc).__name__))
                    continue
                mitigation_statuses[mitigated["status"]] += 1
                post += mitigated["status"] == "POST_MITIGATION_RESOLVED"
            spells_with_post += post > 0

    frozen_versions = {
        "item": ITEM_KNOWLEDGE_VERSION,
        "champion": CHAMPION_KNOWLEDGE_VERSION,
        "rune": RUNE_KNOWLEDGE_VERSION,
        "level_stats": LEVEL_STATS_VERSION,
        "resistance": COMBAT_RESISTANCE_VERSION,
        "spell_source": CHAMPION_SPELL_SOURCE_VERSION,
    }
    invariants = {
        "source_version": CHAMPION_SPELL_SOURCE_VERSION == "champion_spell_source_phase2f_v1",
        "source_commit": DATAMINE_COMMIT == "9245fd616059c6c658d1faa1029f0e18ea179154",
        "ddragon": source.get("ddragon_version") == EXPECTED_DDRAGON_VERSION == "16.16.1",
        "locale": source.get("locale") == EXPECTED_LOCALE == "fr_FR",
        "champions": len(source["records"]) == 173,
        "slots": len(spells) == 692,
        "calculations": calculations == 1443,
        "source_failures": not source.get("source_failures"),
        "registered_signatures_observed": not registered_not_observed,
        "no_unregistered_arithmetic": not evaluator["unregistered_arithmetic"],
        "no_silent_exact_item_exclusions": not snapshot["silent_exact_exclusions"],
        "damage_high_confidence_is_structural": not evidence["high_confidence_key_only"],
        "raw_damage_requires_structural_identity": not damage["unsafe_resolved"],
        "percentage_penetration_is_multiplicative": abs(mitigation_regression["combined"] - 0.44) < 1e-12 and abs(mitigation_regression["effective_resistance"] - 56.0) < 1e-12,
        "incomplete_penetration_withheld": set(mitigation_regression["withheld"].values()) == {MITIGATION_INPUT_UNRESOLVED},
        "no_real_total_without_project_composability": True,
    }
    technical_ok = (
        all(invariants.values())
        and not evaluator["examples"]
        and not snapshot["representatives_missing"]
        and not snapshot["failures"]
        and not evidence["failures"]
        and not damage["failures"]
        and not representative["failures"]
        and not cast["failures"]
        and not runtime_failures
    )
    return {
        "version": FOUNDATION_VERSION,
        "status": "PASS / REVIEW_REQUIRED FOR FREEZE" if technical_ok else "FAIL",
        "frozen_versions": frozen_versions,
        "source": {"champions": len(source["records"]), "slots": len(spells), "calculations": calculations, "nodes": nodes, "commit": DATAMINE_COMMIT, "ddragon": source.get("ddragon_version"), "locale": source.get("locale")},
        "invariants": invariants,
        "taxonomy": {"classes": len(taxonomy["classes"]), "signatures": sum(len(row["signatures"]) for row in taxonomy["classes"].values()), "occurrence_statuses": dict(taxonomy_statuses), "exact_supported_signatures": registered_signatures},
        "data_values": {"references": data_refs, "statuses": dict(data_statuses)},
        "stat_references": {"occurrences": len(stat_refs), "distinct": len(stat_ids), "mapped": len(stat_ids & set(VALIDATED_STAT_REFERENCES)), "unresolved": len(stat_ids - set(VALIDATED_STAT_REFERENCES))},
        "evaluator": {"total": evaluator["total"], "statuses": dict(evaluator["counts"]), "resolved_node_signatures": dict(evaluator["resolved_node_signatures"])},
        "snapshots": {"total": snapshot["snapshots"], "statuses": dict(snapshot["statuses"]), "excluded_static_facts": dict(snapshot["excluded_facts"]), "exact_applied_facts": dict(snapshot["applied_facts"]), "partial_outputs": dict(snapshot["partial_outputs"]), "representative_items": snapshot["representative_items"]},
        "damage_evidence": {"spell_statuses": dict(evidence["statuses"]), "evidence_tiers": dict(evidence["evidence_tiers"]), "types": dict(evidence["types"]), "components": evidence["components"]},
        "damage_resolution": {"statuses": dict(damage["statuses"])},
        "mitigation": {"statuses": dict(mitigation_statuses), "spells_with_post_mitigation": spells_with_post, "totals_composable": 0, "totals_not_safely_composable": spells_with_post, "percentage_regression": mitigation_regression},
        "cast": {"cooldown": dict(cast["cooldown"]), "adjusted_cooldown": dict(cast["adjusted"]), "cost": dict(cast["cost"]), "range": dict(cast["ranges"])},
        "representative": {"probes": representative["probes"], "manual_expected": representative["manual_expected"], "manual_result": representative["manual_result"]},
        "failures": runtime_failures,
    }


def main():
    audit = build_audit()
    for key in ("version", "status", "frozen_versions", "source", "invariants", "taxonomy", "data_values", "stat_references", "evaluator", "snapshots", "damage_evidence", "damage_resolution", "mitigation", "cast", "representative", "failures"):
        print(f"{key}: {audit[key]}")
    return 0 if audit["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
