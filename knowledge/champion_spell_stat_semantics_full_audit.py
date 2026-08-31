"""Full real pinned-source audit for Phase 2H."""

from __future__ import annotations

import subprocess
from collections import Counter

from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION
from knowledge.champion_spell_stat_semantics import (
    AMBIGUOUS,
    CONTRADICTED,
    OWNER_CONTEXT_DEPENDENT,
    OWNER_UNRESOLVED,
    OWNER_VALIDATED_CASTER,
    OWNER_VALIDATED_SOURCE_LEVEL,
    OWNER_VALIDATED_TARGET,
    SEMANTIC_REFERENCE_RESOLVED,
    STRONGLY_SUPPORTED,
    UNRESOLVED,
    VALIDATED,
    audit_stat_mapping_contradictions,
    build_formula_semantic_records,
    build_owner_semantic_records,
    build_stat_semantic_records,
    class_specific_inventory,
    compose_snapshot_reference,
    get_validated_stat_formula_mapping,
    get_validated_stat_mapping,
    inventory_ability_resource_calculations,
    inventory_stat_semantic_occurrences,
    stat_reference_rows,
    summarize_inventory,
)
from knowledge.champion_spell_stat_semantics_sources import (
    PHASE2H_VERSION,
    PINNED_DATAMINE_COMMIT,
    PINNED_DATAMINE_REPOSITORY,
    PINNED_DDRAGON_VERSION,
    PINNED_LOCALE,
)
from knowledge.combat_formula_foundation_full_audit import FOUNDATION_VERSION
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog


EXPECTED_TOTAL_OCCURRENCES = 885
EXPECTED_DISTINCT_MSTAT_IDS = 16


def _frozen_modifications():
    from main import FROZEN_FILES

    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        text=True,
        capture_output=True,
        check=False,
    )
    changed = []
    for line in result.stdout.splitlines():
        path = line[3:].replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path in FROZEN_FILES:
            changed.append(path)
    return sorted(changed), result.returncode


def _status_ids(records):
    return {
        status: sorted(raw_id for raw_id, record in records.items() if record["status"] == status)
        for status in (VALIDATED, STRONGLY_SUPPORTED, AMBIGUOUS, CONTRADICTED, UNRESOLVED)
    }


def build_audit(catalog=None):
    catalog = catalog or get_pinned_spell_catalog()
    occurrences = inventory_stat_semantic_occurrences(catalog)
    summary = summarize_inventory(occurrences)
    stat_rows = stat_reference_rows(occurrences)
    observed_stat_ids = summary["distinct_mStat_ids"]
    observed_formula_ids = summary["effective_stat_formula_values"]
    stat_records = build_stat_semantic_records(observed_stat_ids, stat_rows)
    formula_records = build_formula_semantic_records(observed_formula_ids, stat_rows)
    stat_map = get_validated_stat_mapping(stat_records)
    formula_map = get_validated_stat_formula_mapping(formula_records)
    owner_records = build_owner_semantic_records(stat_rows)
    contradiction_audit = audit_stat_mapping_contradictions(stat_records, stat_rows)
    resources = inventory_ability_resource_calculations(catalog)

    owner_counts = Counter(record["owner_status"] for record in owner_records)
    actual_composition = Counter()
    for row, owner in zip(stat_rows, owner_records):
        result = compose_snapshot_reference(
            row["raw_mStat"],
            row["effective_mStatFormula"],
            owner["owner_status"],
            stat_records,
            formula_records,
        )
        actual_composition[result["status"]] += 1

    resolved_fields = set()
    synthetic_snapshot_fields = {
        "attack_damage_bonus": 1.0,
        "attack_damage_total": 1.0,
        "armor_bonus": 1.0,
        "armor": 1.0,
        "health_bonus": 1.0,
        "health_max": 1.0,
    }
    synthetic_snapshot = {
        "stats": synthetic_snapshot_fields,
        "stat_resolution": {
            name: {"status": "STATIC_STAT_RESOLVED"}
            for name in synthetic_snapshot_fields
        },
    }
    hypothetical_composition = Counter()
    for raw_stat in stat_map:
        for raw_formula in formula_map:
            result = compose_snapshot_reference(
                raw_stat,
                raw_formula,
                OWNER_VALIDATED_CASTER,
                stat_records,
                formula_records,
                caster_snapshot=synthetic_snapshot,
            )
            hypothetical_composition[result["status"]] += 1
            if result["status"] == SEMANTIC_REFERENCE_RESOLVED:
                resolved_fields.add(result["snapshot_field"])

    validated_occurrences = sum(row["raw_mStat"] in stat_map for row in stat_rows)
    validated_formula_occurrences = sum(
        row["effective_mStatFormula"] in formula_map for row in stat_rows
    )
    frozen_changes, git_status_code = _frozen_modifications()
    blocking = []
    if summary["total_occurrences"] != EXPECTED_TOTAL_OCCURRENCES:
        blocking.append("TOTAL_OCCURRENCE_INVARIANT_FAILED")
    if len(observed_stat_ids) != EXPECTED_DISTINCT_MSTAT_IDS:
        blocking.append("DISTINCT_MSTAT_ID_INVARIANT_FAILED")
    if catalog.get("champion_spell_source_version") != CHAMPION_SPELL_SOURCE_VERSION:
        blocking.append("PHASE2F_SOURCE_VERSION_CHANGED")
    if catalog.get("source_commit") != PINNED_DATAMINE_COMMIT:
        blocking.append("PINNED_COMMIT_CHANGED")
    if any(detail["contradiction_count"] for detail in contradiction_audit.values()):
        blocking.append("CREDIBLE_PINNED_STAT_CONTRADICTION")
    if frozen_changes or git_status_code:
        blocking.append("FROZEN_FILE_MODIFICATION_DETECTED")

    key_name_only_admitted = sum(
        item.get("key_name_only") is True
        for record in stat_records.values()
        if record["execution_eligible"]
        for item in record["evidence"]
    )
    ambiguous_in_map = sum(raw_id in stat_map for raw_id, record in stat_records.items() if record["status"] == AMBIGUOUS)
    contradicted_in_map = sum(raw_id in stat_map for raw_id, record in stat_records.items() if record["status"] == CONTRADICTED)
    contradicted_in_formula_map = sum(raw_id in formula_map for raw_id, record in formula_records.items() if record["status"] == CONTRADICTED)
    unproven_owner_assumptions = sum(record["owner_status"] != OWNER_UNRESOLVED for record in owner_records)
    safety = {
        "key_name_only_mappings_admitted": key_name_only_admitted,
        "ambiguous_mappings_in_execution_map": ambiguous_in_map,
        "contradicted_mappings_in_execution_map": contradicted_in_map,
        "contradicted_formulas_in_execution_map": contradicted_in_formula_map,
        "unproven_owner_assumptions": unproven_owner_assumptions,
        "frozen_file_modifications": len(frozen_changes),
    }
    if any(safety.values()):
        blocking.append("SAFETY_INVARIANT_FAILED")

    return {
        "catalog": catalog,
        "summary": summary,
        "stat_rows": stat_rows,
        "stat_records": stat_records,
        "formula_records": formula_records,
        "stat_status_ids": _status_ids(stat_records),
        "formula_status_ids": _status_ids(formula_records),
        "stat_map": stat_map,
        "formula_map": formula_map,
        "validated_occurrences": validated_occurrences,
        "validated_formula_occurrences": validated_formula_occurrences,
        "owner_counts": owner_counts,
        "actual_composition": actual_composition,
        "hypothetical_composition": hypothetical_composition,
        "resolved_fields": sorted(resolved_fields),
        "contradiction_audit": contradiction_audit,
        "class_inventory": class_specific_inventory(stat_rows),
        "resources": resources,
        "safety": safety,
        "frozen_changes": frozen_changes,
        "blocking": blocking,
    }


def render_audit(audit):
    summary = audit["summary"]
    catalog = audit["catalog"]
    lines = [
        "=" * 76,
        "CHAMPION SPELL STAT REFERENCE SEMANTICS - FULL REAL AUDIT",
        "=" * 76,
        "SOURCE",
        "-" * 76,
        f"Phase 2H version           : {PHASE2H_VERSION}",
        f"Phase 2F source version    : {catalog.get('champion_spell_source_version')}",
        f"Phase 2G frozen version    : {FOUNDATION_VERSION}",
        f"LeagueDatamines            : {PINNED_DATAMINE_REPOSITORY}@{PINNED_DATAMINE_COMMIT}",
        f"Data Dragon / locale       : {catalog.get('ddragon_version')} / {catalog.get('locale')}",
        "",
        "INVENTORY",
        "-" * 76,
        f"Field occurrences          : {summary['total_occurrences']}",
        f"mStat / mStatFormula       : {summary['mStat_occurrences']} / {summary['mStatFormula_occurrences']}",
        f"Distinct mStat IDs         : {len(summary['distinct_mStat_ids'])}",
        f"Actual raw mStat IDs       : {summary['distinct_mStat_ids']}",
        f"mStat counts               : {summary['groups']['raw_mStat']}",
        f"Explicit formula values    : {summary['explicit_mStatFormula_values']}",
        f"Effective formula values   : {summary['effective_stat_formula_values']}",
        f"Formula counts             : {summary['groups']['raw_mStatFormula']}",
        f"(mStat, formula) matrix    : {summary['groups']['mStat_formula_pair']}",
        "",
        "STAT SEMANTICS",
        "-" * 76,
    ]
    for status, ids in audit["stat_status_ids"].items():
        lines.append(f"{status:<24}: {ids}")
    lines.extend(
        [
            f"Execution map              : {audit['stat_map']}",
            f"Validated occurrence cover : {audit['validated_occurrences']}/{summary['mStat_occurrences']} ({audit['validated_occurrences']/summary['mStat_occurrences']:.2%})",
            f"Contradiction searches     : {audit['contradiction_audit']}",
            "",
            "FORMULA SEMANTICS",
            "-" * 76,
        ]
    )
    for status, ids in audit["formula_status_ids"].items():
        lines.append(f"{status:<24}: {ids}")
    lines.extend(
        [
            f"Execution formula map      : {audit['formula_map']}",
            f"Validated formula cover    : {audit['validated_formula_occurrences']}/{summary['mStat_occurrences']} ({audit['validated_formula_occurrences']/summary['mStat_occurrences']:.2%})",
            "",
            "OWNERSHIP",
            "-" * 76,
            f"Caster validated           : {audit['owner_counts'][OWNER_VALIDATED_CASTER]}",
            f"Target validated           : {audit['owner_counts'][OWNER_VALIDATED_TARGET]}",
            f"Source-level validated     : {audit['owner_counts'][OWNER_VALIDATED_SOURCE_LEVEL]}",
            f"Context-dependent          : {audit['owner_counts'][OWNER_CONTEXT_DEPENDENT]}",
            f"Unresolved                 : {audit['owner_counts'][OWNER_UNRESOLVED]}",
            "",
            "COMPOSITION",
            "-" * 76,
            f"Actual occurrence statuses : {dict(audit['actual_composition'])}",
            f"Real fully resolved refs   : {audit['actual_composition'][SEMANTIC_REFERENCE_RESOLVED]}",
            f"Fields possible after owner proof: {audit['resolved_fields']}",
            f"Hypothetical status audit  : {dict(audit['hypothetical_composition'])}",
            "",
            "CLASS-SPECIFIC AUDIT",
            "-" * 76,
        ]
    )
    lines.extend(f"- {name}: {detail}" for name, detail in audit["class_inventory"].items())
    lines.extend(
        [
            "",
            "ABILITY RESOURCE BRANCH",
            "-" * 76,
            f"Class nodes                : {len(audit['resources'])}",
            f"Explicit mAbilityResource  : {[row['raw_mAbilityResource'] for row in audit['resources'] if row['raw_mAbilityResource_present']]}",
            "Status                     : RESOURCE_ENUM_RESEARCH_ONLY",
            "",
            "SAFETY INVARIANTS",
            "-" * 76,
        ]
    )
    lines.extend(f"{name:<36}: {value}" for name, value in audit["safety"].items())
    lines.append(f"Frozen changed files       : {audit['frozen_changes']}")
    for issue in audit["blocking"]:
        lines.append(f"[BLOCKING] {issue}")
    lines.extend(
        [
            "",
            "STATUS : " + ("FAIL" if audit["blocking"] else "PASS / REVIEW_REQUIRED FOR FREEZE"),
            "[INFO] No stat calculation class was executed; Phase 2I was not started.",
        ]
    )
    return "\n".join(lines)


def main():
    audit = build_audit()
    print(render_audit(audit))
    return 1 if audit["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
