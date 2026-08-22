from collections import Counter

from knowledge.champion_knowledge import build_champion_knowledge_catalog
from knowledge.champion_spell_damage_evidence import (
    COMPONENT_LOCAL_STRUCTURAL_LINKAGE,
    DAMAGE_CALCULATION_HIGH_CONFIDENCE,
    KEY_NAME_ONLY,
    classify_damage_evidence,
)
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog


def build_audit(source_catalog=None, champion_catalog=None):
    source_catalog = source_catalog or get_pinned_spell_catalog()
    champion_catalog = champion_catalog or build_champion_knowledge_catalog("16.16.1")
    statuses = Counter()
    types = Counter()
    evidence_tiers = Counter()
    components = 0
    high_confidence_key_only = []
    failures = []
    examples = {}
    for champion_id, source_champion in source_catalog["records"].items():
        semantic = {
            spell.get("inferred_slot"): spell
            for spell in champion_catalog["records"].get(champion_id, {}).get("spells", [])
        }
        for source_spell in source_champion["primary_spells"]:
            try:
                result = classify_damage_evidence(source_spell, semantic.get(source_spell["slot"]))
            except Exception as exc:
                failures.append((champion_id, source_spell["slot"], type(exc).__name__))
                continue
            statuses[result["status"]] += 1
            components += len(result["components"])
            for component in result["components"]:
                types[component["damage_type"]] += 1
                evidence_tiers[component["evidence_tier"]] += 1
                examples.setdefault(component["evidence_tier"], (champion_id, source_spell["slot"], component["calculation_key"]))
                if result["status"] == DAMAGE_CALCULATION_HIGH_CONFIDENCE and component["evidence_tier"] != COMPONENT_LOCAL_STRUCTURAL_LINKAGE:
                    high_confidence_key_only.append((champion_id, source_spell["slot"], component["calculation_key"]))
            if not result["components"] and result["evidence"].get("spell_level_damage_types"):
                evidence_tiers["SPELL_LEVEL_TYPE_ONLY"] += 1
    return {
        "source_catalog": source_catalog,
        "champion_catalog": champion_catalog,
        "statuses": statuses,
        "types": types,
        "evidence_tiers": evidence_tiers,
        "components": components,
        "high_confidence_key_only": high_confidence_key_only,
        "examples": examples,
        "failures": failures,
    }


def main():
    audit = build_audit()
    print(f"Primary spells: {sum(audit['statuses'].values())}")
    print(f"Evidence statuses: {dict(audit['statuses'])}")
    print(f"Evidence tiers: {dict(audit['evidence_tiers'])}")
    print(f"Damage types: {dict(audit['types'])}")
    print(f"Candidate components: {audit['components']}")
    print(f"Tier examples: {audit['examples']}")
    print(f"High-confidence key-name-only cases: {audit['high_confidence_key_only'][:10]}")
    print(f"Failures: {audit['failures'][:10]}")
    ok = sum(audit["statuses"].values()) == 692 and not audit["failures"] and not audit["high_confidence_key_only"]
    print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
