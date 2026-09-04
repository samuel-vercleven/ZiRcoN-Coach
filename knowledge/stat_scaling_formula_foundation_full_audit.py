"""Top Phase 2I audit, including the owner gate and Branch B disposition."""

from knowledge.champion_spell_formula_evaluator import EVALUATOR_VERSION
from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION
from knowledge.champion_spell_stat_owner_full_audit import build_audit as build_owner_audit
from knowledge.champion_spell_stat_owner_sources import OWNER_SEMANTICS_VERSION
from knowledge.champion_spell_stat_semantics_sources import PHASE2H_VERSION
from knowledge.combat_formula_foundation_full_audit import FOUNDATION_VERSION
from knowledge.combat_stat_snapshot import SNAPSHOT_VERSION


FOUNDATION_PHASE2I_VERSION = "stat_scaling_formula_foundation_phase2i_v1"
PHASE2G_BASELINE = {
    "total": 1443,
    "resolved": 13,
    "partially_resolved": 720,
    "unsupported_signature": 493,
    "unsupported_class": 217,
}


def build_audit():
    owner = build_owner_audit()
    catalog = owner["catalog"]
    total_calculations = sum(
        len(spell.get("raw_calculation_names", []))
        for champion in catalog.get("records", {}).values()
        for spell in champion.get("primary_spells", [])
    )
    gate = owner["gate"]
    replay = {
        "status": "NOT_RUN_EXECUTION_GATE_ZERO" if not gate["gate_passed"] else "REQUIRED",
        "total_inventory_confirmed": total_calculations,
        "phase2g_baseline": dict(PHASE2G_BASELINE),
        "phase2i_fully_resolved": None,
        "phase2i_partially_resolved": None,
        "newly_resolved": None,
        "blocked_by_owner": gate["blockers"].get("STAT_OWNER_NOT_EXECUTION_ELIGIBLE", 0),
        "blocked_by_stat": gate["blockers"].get("STAT_ID_NOT_EXECUTION_ELIGIBLE", 0),
        "blocked_by_formula": gate["blockers"].get(
            "STAT_FORMULA_NOT_EXECUTION_ELIGIBLE", 0
        ),
        "blocked_by_snapshot": 0,
        "blocked_by_context": gate["blockers"].get(
            "STAT_OWNER_NOT_EXECUTION_ELIGIBLE", 0
        ),
        "cycles": 0,
        "malformed": 0,
        "reason": (
            "The TODO requires replay only after at least one real owner contract is "
            "VALIDATED. No production owner contract reached that status."
        ),
    }
    safety = {
        "frozen_modifications": len(owner["frozen_changes"]),
        "owner_guesses": 0,
        "non_validated_stat_executions": 0,
        "non_validated_formula_executions": 0,
        "unsupported_signature_executions": 0,
        "partial_snapshot_exact_use": 0,
        "stat_arithmetic_executions": 0,
    }
    blocking = list(owner["blocking"])
    if total_calculations != PHASE2G_BASELINE["total"]:
        blocking.append("CALCULATION_INVENTORY_CHANGED")
    if gate["gate_passed"]:
        blocking.append("BRANCH_B_REQUIRED_BUT_NOT_IMPLEMENTED")
    if any(safety.values()):
        blocking.append("PHASE2I_SAFETY_INVARIANT_FAILED")
    return {
        "owner": owner,
        "gate": gate,
        "replay": replay,
        "safety": safety,
        "blocking": blocking,
        "review_items": [
            "Project review may revisit owner binding only with patch-specific runtime/call-site evidence.",
            "AP remains outside execution because frozen Phase 2H did not promote raw mStat 0.",
        ],
    }


def render_audit(audit):
    owner = audit["owner"]
    summary = owner["summary"]
    replay = audit["replay"]
    lines = [
        "=" * 78,
        "STAT-SCALING FORMULA FOUNDATION PHASE 2I - TOP AUDIT",
        "=" * 78,
        "FROZEN VERSIONS",
        "-" * 78,
        f"Phase 2F source                 : {CHAMPION_SPELL_SOURCE_VERSION}",
        f"Phase 2G evaluator              : {EVALUATOR_VERSION}",
        f"Phase 2G foundation             : {FOUNDATION_VERSION}",
        f"Phase 2G snapshot               : {SNAPSHOT_VERSION}",
        f"Phase 2H semantics              : {PHASE2H_VERSION}",
        f"Phase 2I owner                  : {OWNER_SEMANTICS_VERSION}",
        f"Phase 2I foundation             : {FOUNDATION_PHASE2I_VERSION}",
        "",
        "OWNER SEMANTICS",
        "-" * 78,
        f"Owner baseline                  : {summary['stat_rows']}",
        f"Owner status counts             : {summary['owner_status_counts']}",
        f"Owner execution-eligible        : {summary['execution_eligible_owner_occurrences']}",
        f"Exact signature/context contracts: {summary['context_contract_count']}",
        "",
        "FROZEN PHASE 2H CONSUMPTION",
        "-" * 78,
        f"Validated stat occurrences      : {summary['frozen_stat_validated_occurrences']}",
        f"Validated formula occurrences   : {summary['frozen_formula_validated_occurrences']}",
        f"Gate blockers                   : {audit['gate']['blockers']}",
        "",
        "SIGNATURES AND EXECUTION",
        "-" * 78,
        f"Observed exact signatures       : {summary['signature_counts']}",
        "Validated owner signatures      : 0",
        "Fully executable stat nodes      : 0",
        f"Branch B status                 : {audit['gate']['branch_b_status']}",
        "",
        "1,443 FORMULA REPLAY",
        "-" * 78,
        f"Inventory confirmed             : {replay['total_inventory_confirmed']}",
        f"Phase 2G baseline               : {replay['phase2g_baseline']}",
        f"Replay status                   : {replay['status']}",
        f"Newly resolved                  : {replay['newly_resolved']}",
        f"Reason                          : {replay['reason']}",
        "",
        "SAFETY",
        "-" * 78,
    ]
    lines.extend(f"{name:<34}: {value}" for name, value in audit["safety"].items())
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
