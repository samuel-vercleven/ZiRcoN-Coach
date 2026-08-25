"""Exact pinned inventory audit for Phase 2H."""

from knowledge.champion_spell_stat_semantics import (
    class_specific_inventory,
    inventory_ability_resource_calculations,
    inventory_stat_semantic_occurrences,
    stat_reference_rows,
    summarize_inventory,
)
from knowledge.champion_spell_stat_semantics_sources import PHASE2H_VERSION
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog


EXPECTED_TOTAL_FIELD_OCCURRENCES = 885
EXPECTED_DISTINCT_MSTAT_IDS = 16


def build_audit(catalog=None):
    catalog = catalog or get_pinned_spell_catalog()
    occurrences = inventory_stat_semantic_occurrences(catalog)
    summary = summarize_inventory(occurrences)
    resource_rows = inventory_ability_resource_calculations(catalog)
    issues = []
    if summary["total_occurrences"] != EXPECTED_TOTAL_FIELD_OCCURRENCES:
        issues.append(
            f"TOTAL_OCCURRENCES:{summary['total_occurrences']}!={EXPECTED_TOTAL_FIELD_OCCURRENCES}"
        )
    if len(summary["distinct_mStat_ids"]) != EXPECTED_DISTINCT_MSTAT_IDS:
        issues.append(
            f"DISTINCT_MSTAT_IDS:{len(summary['distinct_mStat_ids'])}!={EXPECTED_DISTINCT_MSTAT_IDS}"
        )
    if summary["mStat_occurrences"] + summary["mStatFormula_occurrences"] != summary["total_occurrences"]:
        issues.append("FIELD_OCCURRENCE_PARTITION_MISMATCH")
    if any(row["raw_mStat"] is None for row in stat_reference_rows(occurrences)):
        issues.append("MSTAT_ZERO_OR_VALUE_LOST_AS_MISSING")
    return {
        "catalog": catalog,
        "occurrences": occurrences,
        "summary": summary,
        "classes": class_specific_inventory(stat_reference_rows(occurrences)),
        "resource_rows": resource_rows,
        "issues": issues,
    }


def main():
    audit = build_audit()
    summary = audit["summary"]
    print("=" * 76)
    print("CHAMPION SPELL STAT SEMANTICS - PINNED INVENTORY AUDIT")
    print("=" * 76)
    print(f"Phase 2H version             : {PHASE2H_VERSION}")
    print(f"Field occurrences            : {summary['total_occurrences']}")
    print(f"mStat / mStatFormula fields  : {summary['mStat_occurrences']} / {summary['mStatFormula_occurrences']}")
    print(f"Distinct mStat IDs           : {len(summary['distinct_mStat_ids'])}")
    print(f"Actual mStat IDs             : {summary['distinct_mStat_ids']}")
    print(f"Explicit mStatFormula values : {summary['explicit_mStatFormula_values']}")
    print(f"Effective formula values     : {summary['effective_stat_formula_values']}")
    print(f"mStat counts                 : {summary['groups']['raw_mStat']}")
    print(f"Formula counts on stat rows  : {summary['groups']['raw_mStatFormula']}")
    print(f"Pair matrix                  : {summary['groups']['mStat_formula_pair']}")
    print(f"AbilityResource field occurrences: {summary['ability_resource_occurrences']}")
    print(f"AbilityResource class nodes  : {len(audit['resource_rows'])}")
    print(f"AbilityResource raw records  : {audit['resource_rows']}")
    print("CLASS-SPECIFIC INVENTORY")
    for name, detail in audit["classes"].items():
        print(f"- {name}: {detail}")
    for issue in audit["issues"]:
        print(f"[BLOCKING] {issue}")
    print("STATUS : " + ("FAIL" if audit["issues"] else "PASS"))
    return 1 if audit["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
