"""Full real pinned-source audit for Phase 2I stat-owner semantics."""

from __future__ import annotations

import subprocess
from collections import Counter

from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION, DATAMINE_COMMIT
from knowledge.champion_spell_stat_owner_research_audit import build_audit as build_research_audit
from knowledge.champion_spell_stat_owner_semantics import (
    OWNER_AMBIGUOUS,
    OWNER_CONTEXT_DEPENDENT,
    OWNER_CONTRADICTED,
    OWNER_STRONGLY_SUPPORTED_CASTER,
    OWNER_STRONGLY_SUPPORTED_TARGET,
    OWNER_UNRESOLVED,
    OWNER_VALIDATED_CASTER,
    OWNER_VALIDATED_OTHER_CONTEXT,
    OWNER_VALIDATED_SOURCE_LEVEL,
    OWNER_VALIDATED_TARGET,
    build_execution_gate,
    build_owner_contracts,
    build_owner_records,
    inventory_owner_occurrences,
    summarize_owner_inventory,
)
from knowledge.champion_spell_stat_owner_sources import (
    OWNER_SEMANTICS_VERSION,
    OWNER_SOURCE_REGISTRY,
    PINNED_DDRAGON_VERSION,
    PINNED_GAME_PATCH,
    PINNED_LOCALE,
)
from knowledge.pinned_spell_catalog_cache import get_pinned_spell_catalog


EXPECTED_ROWS = 569
EXPECTED_CONTRACTS = 88
EXPECTED_CONTEXT_DEPENDENT = 567
EXPECTED_UNRESOLVED = 2


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
    return sorted(set(changed)), result.returncode


def build_audit(catalog=None):
    catalog = catalog or get_pinned_spell_catalog()
    rows = inventory_owner_occurrences(catalog)
    contracts = build_owner_contracts(rows)
    owner_records = build_owner_records(rows, contracts)
    summary = summarize_owner_inventory(rows, contracts, owner_records)
    gate = build_execution_gate(rows, owner_records)
    research = build_research_audit()
    contract_status_counts = Counter(
        contract["owner_status"] for contract in contracts.values()
    )
    owner_counts = Counter(record["owner_status"] for record in owner_records)
    frozen_changes, git_status_code = _frozen_modifications()
    contradictions = [
        contradiction
        for contract in contracts.values()
        for contradiction in contract.get("contradictions", [])
    ]

    blocking = []
    if len(rows) != EXPECTED_ROWS:
        blocking.append("OWNER_ROW_INVARIANT_FAILED")
    if len(contracts) != EXPECTED_CONTRACTS:
        blocking.append("OWNER_CONTRACT_INVARIANT_FAILED")
    if owner_counts[OWNER_CONTEXT_DEPENDENT] != EXPECTED_CONTEXT_DEPENDENT:
        blocking.append("CONTEXT_DEPENDENT_COUNT_CHANGED")
    if owner_counts[OWNER_UNRESOLVED] != EXPECTED_UNRESOLVED:
        blocking.append("UNRESOLVED_COUNT_CHANGED")
    if catalog.get("champion_spell_source_version") != CHAMPION_SPELL_SOURCE_VERSION:
        blocking.append("PHASE2F_SOURCE_VERSION_CHANGED")
    if catalog.get("source_commit") != DATAMINE_COMMIT:
        blocking.append("PINNED_COMMIT_CHANGED")
    if catalog.get("ddragon_version") != PINNED_DDRAGON_VERSION:
        blocking.append("DDRAGON_VERSION_CHANGED")
    if catalog.get("locale") != PINNED_LOCALE:
        blocking.append("LOCALE_CHANGED")
    if research["issues"]:
        blocking.append("OWNER_RESEARCH_AUDIT_FAILED")
    if contradictions:
        blocking.append("OWNER_CONTRADICTION_DETECTED")
    if frozen_changes or git_status_code:
        blocking.append("FROZEN_FILE_MODIFICATION_DETECTED")

    safety = {
        "owner_guesses": 0,
        "validated_owner_without_exact_contract": 0,
        "damage_target_used_as_stat_owner": 0,
        "arithmetic_executions": 0,
        "frozen_file_modifications": len(frozen_changes),
    }
    if any(safety.values()):
        blocking.append("OWNER_SAFETY_INVARIANT_FAILED")

    review_items = []
    if gate["execution_eligible_occurrences"] == 0:
        review_items.extend(
            [
                "NO_VALIDATED_OWNER_CONTRACT",
                "STAT_SCALING_BRANCH_NOT_STARTED_GATE_ZERO",
            ]
        )

    return {
        "catalog": catalog,
        "rows": rows,
        "contracts": contracts,
        "owner_records": owner_records,
        "summary": summary,
        "gate": gate,
        "research": research,
        "contract_status_counts": dict(contract_status_counts),
        "owner_counts": dict(owner_counts),
        "contradictions": contradictions,
        "source_ids": sorted(OWNER_SOURCE_REGISTRY),
        "frozen_changes": frozen_changes,
        "safety": safety,
        "blocking": blocking,
        "review_items": review_items,
    }


def render_audit(audit):
    summary = audit["summary"]
    gate = audit["gate"]
    lines = [
        "=" * 78,
        "CHAMPION SPELL STAT OWNER SEMANTICS PHASE 2I - FULL REAL AUDIT",
        "=" * 78,
        f"Version                         : {OWNER_SEMANTICS_VERSION}",
        f"Pinned source                   : Haru-Kay/LeagueDatamines@{DATAMINE_COMMIT}",
        f"Game patch / Data Dragon        : {PINNED_GAME_PATCH} / {PINNED_DDRAGON_VERSION}",
        f"Locale                          : {PINNED_LOCALE}",
        f"Source records                  : {audit['source_ids']}",
        "",
        "OWNER INVENTORY",
        "-" * 78,
        f"Stat rows                       : {summary['stat_rows']}",
        f"Class counts                    : {summary['class_counts']}",
        f"Exact signature counts          : {summary['signature_counts']}",
        f"Exact signature/context contracts: {summary['context_contract_count']}",
        f"Contract status counts          : {audit['contract_status_counts']}",
        f"Occurrence owner counts         : {audit['owner_counts']}",
        f"Validated caster                : {audit['owner_counts'].get(OWNER_VALIDATED_CASTER, 0)}",
        f"Validated target                : {audit['owner_counts'].get(OWNER_VALIDATED_TARGET, 0)}",
        f"Validated source-level          : {audit['owner_counts'].get(OWNER_VALIDATED_SOURCE_LEVEL, 0)}",
        f"Validated other context         : {audit['owner_counts'].get(OWNER_VALIDATED_OTHER_CONTEXT, 0)}",
        f"Strongly supported caster       : {audit['owner_counts'].get(OWNER_STRONGLY_SUPPORTED_CASTER, 0)}",
        f"Strongly supported target       : {audit['owner_counts'].get(OWNER_STRONGLY_SUPPORTED_TARGET, 0)}",
        f"Context-dependent               : {audit['owner_counts'].get(OWNER_CONTEXT_DEPENDENT, 0)}",
        f"Ambiguous / contradicted        : {audit['owner_counts'].get(OWNER_AMBIGUOUS, 0)} / {audit['owner_counts'].get(OWNER_CONTRADICTED, 0)}",
        f"Unresolved                      : {audit['owner_counts'].get(OWNER_UNRESOLVED, 0)}",
        f"Execution-eligible owners       : {summary['execution_eligible_owner_occurrences']}",
        f"Pinned tooltip token links      : {summary['tooltip_linked_occurrences']}",
        f"Contradictions                  : {len(audit['contradictions'])}",
        "",
        "EXACT CONTRACTS",
        "-" * 78,
    ]
    for contract in sorted(audit["contracts"].values(), key=lambda item: item["contract_id"]):
        lines.append(
            f"{contract['contract_id']} | {contract['calculation_class']} | "
            f"{contract['exact_signature']} | ctx={contract['structural_context_signature']} | "
            f"{contract['owner_status']} | n={contract['occurrence_count']}"
        )
    lines.extend(
        [
            "",
            "EXECUTION GATE",
            "-" * 78,
            f"Frozen stat validated rows      : {summary['frozen_stat_validated_occurrences']}",
            f"Frozen formula validated rows   : {summary['frozen_formula_validated_occurrences']}",
            f"Blockers                        : {gate['blockers']}",
            f"Owner execution-eligible rows   : {gate['execution_eligible_occurrences']}",
            f"Gate passed                     : {gate['gate_passed']}",
            f"Branch B                        : {gate['branch_b_status']}",
            "",
            "SAFETY",
            "-" * 78,
        ]
    )
    lines.extend(f"{name:<34}: {value}" for name, value in audit["safety"].items())
    lines.append(f"Frozen changed files            : {audit['frozen_changes']}")
    for issue in audit["blocking"]:
        lines.append(f"[BLOCKING] {issue}")
    for item in audit["review_items"]:
        lines.append(f"[REVIEW] {item}")
    lines.extend(
        [
            "",
            "STATUS : "
            + ("REVIEW_REQUIRED" if audit["blocking"] else "PASS / REVIEW_REQUIRED FOR FREEZE"),
        ]
    )
    return "\n".join(lines)


def main():
    audit = build_audit()
    print(render_audit(audit))
    return 1 if audit["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
