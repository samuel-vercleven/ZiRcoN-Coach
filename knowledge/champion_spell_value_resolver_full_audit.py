from collections import Counter

from knowledge.champion_spell_value_resolver import PINNED_RANK_0_TO_6, VALUE_RESOLVED, resolve_rank_value
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog


def build_audit():
    catalog = get_pinned_spell_catalog()
    lengths = Counter()
    statuses = Counter()
    total = 0
    for champion in catalog["records"].values():
        for spell in champion["primary_spells"]:
            for entry in spell.get("raw_data_values") or []:
                values = entry.get("values")
                lengths[len(values) if isinstance(values, list) else None] += 1
                total += 1
                statuses[resolve_rank_value(values, 1, 5, PINNED_RANK_0_TO_6)["status"]] += 1
    return {"catalog": catalog, "total": total, "lengths": lengths, "statuses": statuses}


def main():
    audit = build_audit()
    print(f"DataValue arrays: {audit['total']}")
    print(f"Array lengths: {dict(audit['lengths'])}")
    print(f"Rank-1 statuses: {dict(audit['statuses'])}")
    ok = audit["total"] == 5063 and audit["statuses"][VALUE_RESOLVED] == 4975
    print(f"STATUS : {'PASS' if ok else 'REVIEW_REQUIRED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
