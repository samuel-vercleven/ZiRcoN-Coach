"""Offline provenance audit for Phase 2I owner research."""

from urllib.parse import urlparse

from knowledge.champion_spell_stat_owner_sources import (
    OWNER_SEMANTICS_VERSION,
    OWNER_SOURCE_REGISTRY,
    PINNED_DATAMINE_COMMIT,
    source_registry_digest,
)


def build_audit():
    issues = []
    exact_patch = 0
    executable_research = 0
    owner_binding_overclaims = []
    for source_id, source in OWNER_SOURCE_REGISTRY.items():
        url = source.get("url", "")
        if urlparse(url).scheme != "https":
            issues.append(f"NON_HTTPS_SOURCE:{source_id}")
        commit = source.get("commit")
        if commit and commit not in url:
            issues.append(f"COMMIT_NOT_IN_URL:{source_id}")
        exact_patch += source.get("tier", "").startswith("EXACT_PINNED") or source.get(
            "tier"
        ) == "PATCH_MATCHED_META_STRUCTURE"
        executable_research += "EXECUTABLE_REVERSE_ENGINEERING" in source.get("tier", "")
        claims = " ".join(source.get("supports", []))
        if "OWNER_IS_CASTER" in claims or "OWNER_IS_TARGET" in claims:
            owner_binding_overclaims.append(source_id)
        if not source.get("limitations"):
            issues.append(f"MISSING_LIMITATIONS:{source_id}")
    if OWNER_SOURCE_REGISTRY["pinned_26_16_spell_graphs"].get("commit") != PINNED_DATAMINE_COMMIT:
        issues.append("PINNED_COMMIT_MISMATCH")
    if owner_binding_overclaims:
        issues.append(f"UNPROVEN_OWNER_BINDING_CLAIM:{owner_binding_overclaims}")
    if exact_patch < 2:
        issues.append("INSUFFICIENT_EXACT_PATCH_STRUCTURAL_SOURCES")
    if executable_research < 3:
        issues.append("INSUFFICIENT_EXECUTABLE_RESEARCH_CROSS_CHECKS")
    return {
        "issues": issues,
        "source_count": len(OWNER_SOURCE_REGISTRY),
        "exact_patch_source_count": exact_patch,
        "executable_research_source_count": executable_research,
        "validated_caster_or_target_claims": 0,
        "digest": source_registry_digest(),
        "conclusion": (
            "The stat subject is evaluation-context supplied; no source proves a universal "
            "26.16 caster or target binding."
        ),
    }


def main():
    audit = build_audit()
    print("=" * 76)
    print("CHAMPION SPELL STAT OWNER SEMANTICS - RESEARCH AUDIT")
    print("=" * 76)
    print(f"Phase 2I version                : {OWNER_SEMANTICS_VERSION}")
    print(f"Recorded sources                : {audit['source_count']}")
    print(f"Exact/patch-matched structures  : {audit['exact_patch_source_count']}")
    print(f"Executable RE cross-checks      : {audit['executable_research_source_count']}")
    print(f"Validated caster/target claims  : {audit['validated_caster_or_target_claims']}")
    print(f"Registry SHA-256                : {audit['digest']}")
    print(f"Conclusion                      : {audit['conclusion']}")
    print(f"Issues                          : {len(audit['issues'])}")
    for issue in audit["issues"]:
        print(f"[BLOCKING] {issue}")
    print("STATUS : " + ("FAIL" if audit["issues"] else "PASS"))
    return 1 if audit["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
