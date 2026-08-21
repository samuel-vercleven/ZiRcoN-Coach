"""Real pinned-source audit for Phase 2F."""

from collections import Counter

from knowledge.champion_spell_source import (
    CALCULATIONS_EXPOSED,
    CHAMPION_SPELL_SOURCE_VERSION,
    EXPECTED_CHAMPION_COUNT,
    EXPECTED_CHAMPION_KNOWLEDGE_VERSION,
    EXPECTED_DDRAGON_VERSION,
    EXPECTED_LOCALE,
    EXACT_OBJECT_PATH_MATCH,
    EXACT_PRIMARY_SPELL_PATH,
    MALFORMED_CALCULATION_GRAPH,
    PRIMARY_SLOTS,
    SOURCE_EXACT_PATCH,
    build_champion_spell_source_catalog,
)


def build_audit():
    catalog = build_champion_spell_source_catalog()
    records = catalog["records"]
    primary_spells = [spell for record in records.values() for spell in record["primary_spells"]]
    blocking, review = [], []
    if catalog["champion_knowledge_version"] != EXPECTED_CHAMPION_KNOWLEDGE_VERSION:
        review.append({"kind": "FROZEN_CHAMPION_KNOWLEDGE_VERSION_CHANGED"})
    if catalog["ddragon_version"] != EXPECTED_DDRAGON_VERSION or catalog["locale"] != EXPECTED_LOCALE:
        review.append({"kind": "FROZEN_CHAMPION_KNOWLEDGE_CONTEXT_CHANGED"})
    if catalog["expected_champion_count"] != EXPECTED_CHAMPION_COUNT:
        review.append({"kind": "CHAMPION_COUNT_NOT_FROZEN_BASELINE", "value": catalog["expected_champion_count"]})
    if catalog["source_status"] != SOURCE_EXACT_PATCH:
        review.append({"kind": "EXACT_PINNED_SOURCE_UNAVAILABLE", "failures": len(catalog["source_failures"])})
    for record in records.values():
        if record["ddragon_spell_slots"] != list(PRIMARY_SLOTS):
            review.append({"kind": "DDRAGON_PRIMARY_SLOTS_NOT_FOUR", "champion": record["champion_id"]})
    unresolved = [spell for spell in primary_spells if spell["mapping_status"] not in {EXACT_PRIMARY_SPELL_PATH, EXACT_OBJECT_PATH_MATCH}]
    if len(primary_spells) != EXPECTED_CHAMPION_COUNT * len(PRIMARY_SLOTS):
        review.append({"kind": "PRIMARY_SLOT_COUNT_INCOMPLETE", "value": len(primary_spells)})
    if unresolved:
        review.append({"kind": "PRIMARY_SLOT_MAPPING_UNRESOLVED", "count": len(unresolved)})
    malformed = [spell for spell in primary_spells if spell["calculation_status"] == MALFORMED_CALCULATION_GRAPH]
    if malformed:
        review.append({"kind": "MALFORMED_CALCULATION_GRAPHS", "count": len(malformed)})
    class_counts = Counter(node["calculation_class"] for spell in primary_spells for node in spell.get("calculation_nodes", []))
    return {
        "catalog": catalog,
        "primary_spells": primary_spells,
        "class_counts": class_counts,
        "blocking": blocking,
        "review": review,
        "exact_key_count": sum(spell["mapping_status"] == EXACT_PRIMARY_SPELL_PATH for spell in primary_spells),
        "object_path_count": sum(spell["mapping_status"] == EXACT_OBJECT_PATH_MATCH for spell in primary_spells),
        "calculation_slots": sum(spell["calculation_status"] == CALCULATIONS_EXPOSED for spell in primary_spells),
        "malformed": malformed,
    }


def render_audit(audit):
    catalog, spells = audit["catalog"], audit["primary_spells"]
    lines = [
        "=" * 76,
        "CHAMPION SPELL CALCULATION SOURCE - FULL AUDIT",
        "=" * 76,
        f"Spell source version       : {CHAMPION_SPELL_SOURCE_VERSION}",
        f"Frozen Champion Knowledge  : {catalog['champion_knowledge_version']}",
        f"Data Dragon / locale       : {catalog['ddragon_version']} / {catalog['locale']}",
        f"Datamine repository        : {catalog['source_repository']}",
        f"Pinned commit              : {catalog['source_commit']}",
        f"Target patch               : {catalog['target_patch']} / Riot {catalog['target_riot_patch_label']}",
        f"Champions expected/resolved: {catalog['expected_champion_count']} / {len(catalog['records'])}",
        f"Primary slots expected/resolved: {EXPECTED_CHAMPION_COUNT * 4} / {len(spells)}",
        f"Exact key / objectPath maps: {audit['exact_key_count']} / {audit['object_path_count']}",
        f"Slots with/without calcs   : {audit['calculation_slots']} / {len(spells) - audit['calculation_slots']}",
        f"Calculation records         : {sum(len(spell.get('raw_calculation_names', [])) for spell in spells)}",
        f"Calculation graph nodes     : {sum(len(spell.get('calculation_nodes', [])) for spell in spells)}",
        f"Unique calculation classes  : {len(audit['class_counts'])}",
        f"Uninterpreted class nodes   : {sum(audit['class_counts'].values())}",
        f"Raw DataValues              : {sum(len(spell.get('raw_data_values') or []) for spell in spells)}",
        f"Malformed graphs            : {len(audit['malformed'])}",
        f"Source failures             : {len(catalog['source_failures'])}",
        f"Blocking issues             : {len(audit['blocking'])}",
        f"Review items                : {len(audit['review'])}",
        "",
        "CALCULATION CLASSES",
        "-" * 76,
    ]
    lines.extend(f"- {name}: {count}" for name, count in sorted(audit["class_counts"].items()))
    if audit["review"]:
        lines.extend(["", "REVIEW ITEMS", "-" * 76])
        lines.extend(f"[REVIEW] {item}" for item in audit["review"])
    lines.extend(["", "SCOPE", "-" * 76, "[INFO] Raw source catalog only; no formula, stat, or damage evaluation is performed."])
    status = "FAIL" if audit["blocking"] else "REVIEW_REQUIRED" if audit["review"] else "PASS"
    lines.extend(["", f"STATUS : {status}"])
    return "\n".join(lines)


def main():
    audit = build_audit()
    print(render_audit(audit))
    return 2 if audit["blocking"] else 1 if audit["review"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
