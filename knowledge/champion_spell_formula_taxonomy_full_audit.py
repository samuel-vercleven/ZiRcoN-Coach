from collections import Counter
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog
from knowledge.champion_spell_formula_taxonomy import build_taxonomy

def build_audit():
    catalog = get_pinned_spell_catalog()
    taxonomy = build_taxonomy(catalog)
    statuses = Counter()
    signatures = 0
    for row in taxonomy["classes"].values():
        statuses.update(row["statuses"])
        signatures += len(row["signatures"])
    return {"catalog": catalog, "taxonomy": taxonomy, "statuses": statuses, "signatures": signatures}

def main():
    audit = build_audit()
    print(f"Taxonomy version: {audit['taxonomy']['version']}")
    print(f"Observed classes: {len(audit['taxonomy']['classes'])}")
    print(f"Structural signatures: {audit['signatures']}")
    print(f"Occurrence statuses: {dict(audit['statuses'])}")
    print(f"Source failures: {len(audit['catalog'].get('source_failures', {}))}")
    ok = len(audit['taxonomy']['classes']) == 25 and not audit['catalog'].get('source_failures')
    print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}")
    return 0 if ok else 1

if __name__ == "__main__": raise SystemExit(main())
