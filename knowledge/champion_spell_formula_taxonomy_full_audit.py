from collections import Counter
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog
from knowledge.champion_spell_formula_taxonomy import SUPPORTED_SIGNATURES, build_taxonomy

def build_audit():
    catalog = get_pinned_spell_catalog()
    taxonomy = build_taxonomy(catalog)
    statuses = Counter()
    signatures = 0
    for row in taxonomy["classes"].values():
        statuses.update(row["statuses"])
        signatures += len(row["signatures"])
    observed = {name: set(row["signatures"]) for name, row in taxonomy["classes"].items()}
    supported = {name: {"|".join(signature) for signature in contracts} for name, contracts in SUPPORTED_SIGNATURES.items()}
    missing = {name: sorted(signatures - observed.get(name, set())) for name, signatures in supported.items() if signatures - observed.get(name, set())}
    unsupported = {name: sorted(signatures - supported.get(name, set())) for name, signatures in observed.items() if signatures - supported.get(name, set())}
    return {"catalog": catalog, "taxonomy": taxonomy, "statuses": statuses, "signatures": signatures, "supported": supported, "unsupported": unsupported, "registered_not_observed": missing}

def main():
    audit = build_audit()
    print(f"Taxonomy version: {audit['taxonomy']['version']}")
    print(f"Observed classes: {len(audit['taxonomy']['classes'])}")
    print(f"Structural signatures: {audit['signatures']}")
    print(f"Occurrence statuses: {dict(audit['statuses'])}")
    print(f"Exact executable signatures: {audit['supported']}")
    print(f"Exact unsupported signatures: {audit['unsupported']}")
    print(f"Registered signatures not observed: {audit['registered_not_observed']}")
    print(f"Source failures: {len(audit['catalog'].get('source_failures', {}))}")
    ok = len(audit['taxonomy']['classes']) == 25 and not audit['catalog'].get('source_failures') and not audit['registered_not_observed']
    print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}")
    return 0 if ok else 1

if __name__ == "__main__": raise SystemExit(main())
