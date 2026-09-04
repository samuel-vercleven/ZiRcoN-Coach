"""Synthetic fail-closed checks for Phase 2I owner contracts."""

from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION, DATAMINE_COMMIT
from knowledge.champion_spell_stat_owner_semantics import (
    OWNER_AMBIGUOUS,
    OWNER_CONTEXT_MISMATCH,
    OWNER_CONTRADICTED,
    OWNER_SIGNATURE_MISMATCH,
    OWNER_STRONGLY_SUPPORTED_CASTER,
    OWNER_UNRESOLVED,
    OWNER_VALIDATED_CASTER,
    OWNER_VALIDATED_TARGET,
    owner_contract_key,
    resolve_owner_contract,
)


def _row(signature="mCoefficient|mStat|~class", context="ctx-a", commit=DATAMINE_COMMIT):
    return {
        "calculation_class": "StatByCoefficientCalculationPart",
        "class_signature": signature,
        "structural_context_signature": context,
        "source_provenance": {
            "source_version": CHAMPION_SPELL_SOURCE_VERSION,
            "source_commit": commit,
        },
    }


def _contract(row, owner_status, semantic_owner):
    return {
        "owner_status": owner_status,
        "semantic_owner": semantic_owner,
        "contract_id": f"synthetic:{owner_status}",
        "evidence_source_ids": ["SYNTHETIC_EXPLICIT_TEST_CONTRACT"],
        "provenance": {"fixture": "SYNTHETIC_ONLY"},
    }


def main():
    checks = 0
    base = _row()

    unresolved = resolve_owner_contract(base, {})
    assert unresolved["owner_status"] == OWNER_UNRESOLVED
    assert unresolved["execution_eligible"] is False
    checks += 1

    for status in (
        OWNER_STRONGLY_SUPPORTED_CASTER,
        OWNER_AMBIGUOUS,
        OWNER_CONTRADICTED,
    ):
        resolved = resolve_owner_contract(
            base, {owner_contract_key(base): _contract(base, status, "CASTER")}
        )
        assert resolved["execution_eligible"] is False
        checks += 1

    caster = resolve_owner_contract(
        base,
        {owner_contract_key(base): _contract(base, OWNER_VALIDATED_CASTER, "CASTER")},
    )
    assert caster["execution_eligible"] is True
    assert caster["semantic_owner"] == "CASTER"
    checks += 1

    target = resolve_owner_contract(
        base,
        {owner_contract_key(base): _contract(base, OWNER_VALIDATED_TARGET, "TARGET")},
    )
    assert target["execution_eligible"] is True
    assert target["semantic_owner"] == "TARGET"
    checks += 1

    # A damage target is deliberately absent from owner resolution inputs.
    assert caster["semantic_owner"] == "CASTER"
    assert caster["damage_target_role_consumed"] is False
    checks += 1

    signature_variant = _row(signature="mCoefficient|mStat|mUnknown|~class")
    mismatch = resolve_owner_contract(
        signature_variant,
        {owner_contract_key(base): _contract(base, OWNER_VALIDATED_CASTER, "CASTER")},
    )
    assert mismatch["status"] == OWNER_SIGNATURE_MISMATCH
    checks += 1

    context_variant = _row(context="ctx-b")
    mismatch = resolve_owner_contract(
        context_variant,
        {owner_contract_key(base): _contract(base, OWNER_VALIDATED_CASTER, "CASTER")},
    )
    assert mismatch["status"] == OWNER_CONTEXT_MISMATCH
    checks += 1

    assert caster["provenance"] == {"fixture": "SYNTHETIC_ONLY"}
    assert caster["evidence_source_ids"] == ["SYNTHETIC_EXPLICIT_TEST_CONTRACT"]
    checks += 1

    print(f"Champion spell stat owner synthetic checks: PASS ({checks}/{checks})")


if __name__ == "__main__":
    main()
