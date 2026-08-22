"""Pinned real-catalog safety probes plus non-circular arithmetic checks."""
from collections import defaultdict

from knowledge.champion_spell_damage_evidence import (
    DAMAGE_EVIDENCE_INSUFFICIENT,
    KEY_NAME_ONLY,
    classify_damage_evidence,
)
from knowledge.champion_spell_damage_resolver import RAW_DAMAGE_RESOLVED, resolve_damage_components
from knowledge.champion_spell_formula_evaluator import evaluate_calculation
from knowledge.champion_spell_formula_taxonomy import SUPPORTED_SIGNATURES, structural_signature
from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION
from knowledge.combat_stat_snapshot import STATIC_STAT_PARTIAL, build_combat_snapshot
from knowledge.item_knowledge import build_item_knowledge_catalog
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog
from knowledge.spell_damage_mitigation import POST_MITIGATION_RESOLVED, mitigate_component

NO_HACK_CHAMPION = "Rammus"


def _walk_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _first_description_item(items, canonical_stat):
    for item in items["records"].values():
        if not item.get("applicability", {}).get("purchasable_on_summoners_rift"):
            continue
        for fact in item.get("normalized_stats", []):
            if fact.get("stat") == canonical_stat and fact.get("source") != "DDRAGON_STATS":
                return item, fact
    return None, None


def _real_signature_inventory(source_catalog):
    signatures = defaultdict(set)
    examples = {}
    for champion in source_catalog["records"].values():
        for spell in champion["primary_spells"]:
            for key, calculation in (spell.get("raw_m_spell_calculations") or {}).items():
                for node in _walk_dicts(calculation):
                    class_name = node.get("~class")
                    if class_name:
                        signature = structural_signature(node)
                        signatures[class_name].add(signature)
                        examples.setdefault((class_name, signature), (spell, key, node))
    return signatures, examples


def run_representative_checks(source_catalog=None, champion_catalog=None, item_catalog=None):
    source_catalog = source_catalog or get_pinned_spell_catalog()
    item_catalog = item_catalog or build_item_knowledge_catalog("16.16.1")
    semantic_records = (champion_catalog or {}).get("records", {})
    failures = []
    probes = []

    lethality_item, lethality_fact = _first_description_item(item_catalog, "lethality")
    haste_item, haste_fact = _first_description_item(item_catalog, "ability_haste")
    if not lethality_item:
        failures.append(("REAL_ITEM_LETHALITY", "DESCRIPTION_DERIVED_FACT_NOT_FOUND"))
    if not haste_item:
        failures.append(("REAL_ITEM_ABILITY_HASTE", "DESCRIPTION_DERIVED_FACT_NOT_FOUND"))
    champion = next(iter(semantic_records.values()), None)
    if champion and lethality_item and haste_item:
        equipped = [lethality_item["item_id"], haste_item["item_id"]]
        snapshot = build_combat_snapshot(champion, 11, item_catalog["records"], equipped)
        for stat, item, fact in (
            ("lethality", lethality_item, lethality_fact),
            ("ability_haste", haste_item, haste_fact),
        ):
            resolution = snapshot["stat_resolution"][stat]
            ok = snapshot["stats"][stat] is None and resolution["status"] == STATIC_STAT_PARTIAL
            if not ok:
                failures.append(("REAL_ITEM_EXCLUSION", stat, item["item_id"]))
            probes.append({"probe": f"description-derived {stat}", "item_id": item["item_id"], "item_name": item["name"], "source": fact.get("source"), "withheld": ok})

        synthetic_penetration = {
            "A": {"item_id": "A", "name": "30 percent fixture", "normalized_stats": [{"stat": "armor_penetration_percent", "value": 0.30, "source": "DDRAGON_STATS", "confidence": "STRUCTURED"}]},
            "B": {"item_id": "B", "name": "20 percent fixture", "normalized_stats": [{"stat": "armor_penetration_percent", "value": 0.20, "source": "DDRAGON_STATS", "confidence": "STRUCTURED"}]},
        }
        attacker = build_combat_snapshot(champion, 11, synthetic_penetration, ("A", "B"), overrides={"lethality": 0, "armor_penetration_flat": 0})
        target = build_combat_snapshot(champion, 11, overrides={"armor": 100, "armor_native": 100})
        component = {"status": RAW_DAMAGE_RESOLVED, "raw_damage": 100, "damage_type": "PHYSICAL"}
        mitigation = mitigate_component(component, attacker, target)
        sources = [row["value"] for row in attacker["stats"]["armor_penetration_percent_sources"]]
        penetration_ok = (
            sources == [0.30, 0.20]
            and abs(attacker["stats"]["armor_penetration_percent"] - 0.44) < 1e-12
            and mitigation["status"] == POST_MITIGATION_RESOLVED
            and abs(mitigation["penetration_inputs"]["percentage_combined"] - 0.44) < 1e-12
            and abs(mitigation["effective_resistance"] - 56.0) < 1e-12
        )
        if not penetration_ok:
            failures.append(("PERCENTAGE_PENETRATION", "EXPECTED_30_PLUS_20_EQUALS_44"))
        probes.append({"probe": "multiplicative percentage penetration", "sources": sources, "combined": mitigation.get("penetration_inputs", {}).get("percentage_combined"), "effective_armor": mitigation.get("effective_resistance"), "passed": penetration_ok})

    signatures, _ = _real_signature_inventory(source_catalog)
    multi_signature_classes = sorted(name for name, values in signatures.items() if len(values) > 1)
    if not multi_signature_classes:
        failures.append(("REAL_SIGNATURES", "NO_MULTI_SIGNATURE_CLASS"))
    probes.append({"probe": "real multi-signature class", "classes": multi_signature_classes})

    supported_example = None
    unsupported_example = None
    for source_champion in source_catalog["records"].values():
        for spell in source_champion["primary_spells"]:
            for key, node in (spell.get("raw_m_spell_calculations") or {}).items():
                class_name = node.get("~class") if isinstance(node, dict) else None
                signature = structural_signature(node) if isinstance(node, dict) else ()
                result = evaluate_calculation(spell, key, {"spell_rank": 1, "max_rank": 5})
                if supported_example is None and signature in SUPPORTED_SIGNATURES.get(class_name, {}):
                    supported_example = (class_name, signature, spell, key, result.status)
                if unsupported_example is None and class_name in SUPPORTED_SIGNATURES and signature not in SUPPORTED_SIGNATURES[class_name]:
                    unsupported_example = (class_name, signature, spell, key, result.status)
                if supported_example and unsupported_example:
                    break
            if supported_example and unsupported_example:
                break
        if supported_example and unsupported_example:
            break
    if not supported_example or not unsupported_example:
        failures.append(("REAL_SIGNATURES", "SUPPORTED_OR_UNSUPPORTED_EXAMPLE_MISSING"))
    elif supported_example[4] == "UNSUPPORTED_SIGNATURE" or unsupported_example[4] != "UNSUPPORTED_SIGNATURE":
        failures.append(("REAL_SIGNATURES", "EVALUATOR_DID_NOT_RESPECT_EXACT_REGISTRY"))
    probes.append({"probe": "supported real signature", "example": None if not supported_example else (supported_example[0], supported_example[1], supported_example[2].get("champion_id"), supported_example[2].get("slot"), supported_example[3], supported_example[4])})
    probes.append({"probe": "unsupported real signature", "example": None if not unsupported_example else (unsupported_example[0], unsupported_example[1], unsupported_example[2].get("champion_id"), unsupported_example[2].get("slot"), unsupported_example[3], unsupported_example[4])})

    key_only_probe = None
    for champion_id, source_champion in source_catalog["records"].items():
        semantic = {row.get("inferred_slot"): row for row in semantic_records.get(champion_id, {}).get("spells", [])}
        for spell in source_champion["primary_spells"]:
            evidence = classify_damage_evidence(spell, semantic.get(spell["slot"]))
            if evidence["status"] == DAMAGE_EVIDENCE_INSUFFICIENT and any(row.get("evidence_tier") == KEY_NAME_ONLY for row in evidence["components"]):
                resolved = resolve_damage_components(spell, evidence, {"spell_rank": 1, "max_rank": 5})
                key_only_probe = (champion_id, spell["slot"], [row["calculation_key"] for row in evidence["components"]])
                if any(row["status"] == RAW_DAMAGE_RESOLVED for row in resolved):
                    failures.append(("KEY_NAME_ONLY", champion_id, spell["slot"], "RAW_DAMAGE_EMITTED"))
                break
        if key_only_probe:
            break
    if not key_only_probe:
        failures.append(("KEY_NAME_ONLY", "REAL_EXAMPLE_NOT_FOUND"))
    probes.append({"probe": "damage key not automatically accepted", "example": key_only_probe})

    no_hack_source = source_catalog["records"].get(NO_HACK_CHAMPION)
    if no_hack_source is None:
        failures.append((NO_HACK_CHAMPION, "SOURCE_RECORD_MISSING"))
    else:
        semantic = {row.get("inferred_slot"): row for row in semantic_records.get(NO_HACK_CHAMPION, {}).get("spells", [])}
        no_hack_statuses = [classify_damage_evidence(spell, semantic.get(spell["slot"]))["status"] for spell in no_hack_source["primary_spells"]]
        probes.append({"probe": "named champion no-hack regression", "champion": NO_HACK_CHAMPION, "spell_statuses": no_hack_statuses})

    fixture = {
        "champion_spell_source_version": CHAMPION_SPELL_SOURCE_VERSION,
        "champion_id": "ManualPinnedShape",
        "slot": "Q",
        "raw_data_values": [{"name": "BaseDamage", "values": [0, 25, 50, 75, 100, 125, 150]}],
        "raw_m_spell_calculations": {"QDamage": {"~class": "GameCalculation", "mFormulaParts": [{"~class": "NamedDataValueCalculationPart", "mDataValue": "BaseDamage"}, {"~class": "ProductOfSubPartsCalculationPart", "mPart1": {"~class": "NumberCalculationPart", "mNumber": 2}, "mPart2": {"~class": "NumberCalculationPart", "mNumber": 3.5}}]}},
    }
    manual = evaluate_calculation(fixture, "QDamage", {"spell_rank": 2, "max_rank": 5})
    if abs((manual.value or 0) - 57.0) > 1e-12:
        failures.append(("MANUAL_DERIVATION", "EXPECTED_50_PLUS_2_TIMES_3_5"))
    return {"probes": probes, "manual_expected": 57.0, "manual_result": manual.value, "failures": failures}


def main():
    result = run_representative_checks()
    print(f"Representative probes: {len(result['probes'])}")
    for probe in result["probes"]:
        print(probe)
    print(f"Manual expected/result: {result['manual_expected']} / {result['manual_result']}")
    print(f"Failures: {result['failures']}")
    ok = not result["failures"]
    print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
