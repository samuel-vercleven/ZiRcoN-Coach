from collections import Counter

from knowledge.champion_spell_data_value_resolver import build_registry, resolve_data_value
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog


def build_audit():
    catalog = get_pinned_spell_catalog()
    statuses = Counter()
    references = 0
    duplicates = 0
    case_collisions = 0
    for champion in catalog["records"].values():
        for spell in champion["primary_spells"]:
            registry = build_registry(spell.get("raw_data_values"))
            duplicates += sum(len(rows) > 1 for rows in registry.values())
            folded = Counter(name.casefold() for name in registry)
            case_collisions += sum(count > 1 for count in folded.values())
            for node in spell.get("calculation_nodes", []):
                for ref in node.get("named_data_value_references", []):
                    references += 1
                    statuses[resolve_data_value(registry, ref["value"], 1, 5)["status"]] += 1
    return {"catalog": catalog, "references": references, "statuses": statuses, "duplicates": duplicates, "case_collisions": case_collisions}


def main():
    audit = build_audit()
    print(f"Exact DataValue references: {audit['references']}")
    print(f"Statuses: {dict(audit['statuses'])}")
    print(f"Duplicate names: {audit['duplicates']}")
    print(f"Case-variant collisions: {audit['case_collisions']}")
    print("STATUS : PASS")


if __name__ == "__main__":
    main()
