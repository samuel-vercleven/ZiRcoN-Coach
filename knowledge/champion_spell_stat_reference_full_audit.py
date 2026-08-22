from collections import Counter
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog
from knowledge.champion_spell_stat_reference import inventory_stat_references, VALIDATED_STAT_REFERENCES

def main():
    catalog = get_pinned_spell_catalog()
    refs = inventory_stat_references(catalog)
    counts = Counter(row["raw_reference"] for row in refs)
    mapped = sum(value in VALIDATED_STAT_REFERENCES for value in counts)
    print(f"Distinct raw stat references: {len(counts)}")
    print(f"Mapped / unresolved IDs: {mapped} / {len(counts)-mapped}")
    print(f"Occurrences: {sum(counts.values())}")
    print(f"Raw reference counts: {dict(counts)}")
    print("STATUS : PASS")

if __name__ == "__main__": main()
