"""Offline provenance audit for Phase 2H public research records."""

from urllib.parse import urlparse

from knowledge.champion_spell_stat_semantics_sources import (
    PHASE2H_VERSION,
    PINNED_DATAMINE_COMMIT,
    SOURCE_REGISTRY,
    source_registry_digest,
)


def build_audit():
    issues = []
    immutable = 0
    exact_stat_sources = 0
    semantic_overclaims = []
    for source_id, source in SOURCE_REGISTRY.items():
        url = source.get("url", "")
        if urlparse(url).scheme != "https":
            issues.append(f"NON_HTTPS_SOURCE:{source_id}")
        commit = source.get("commit")
        if commit and commit not in url:
            issues.append(f"COMMIT_NOT_IN_URL:{source_id}")
        immutable += source.get("hash_policy") == "IMMUTABLE_GIT_COMMIT_URL"
        exact_stat_sources += "DIRECT_RAW_STAT_ID_TO_UI_STAT_IDENTITY" in source.get("supports", [])
        if "U8" in " ".join(source.get("supports", [])) and any(
            "ENUM_MEANING" in claim for claim in source.get("supports", [])
        ):
            semantic_overclaims.append(source_id)
    if SOURCE_REGISTRY["league_datamines_global_stats_ui"].get("commit") != PINNED_DATAMINE_COMMIT:
        issues.append("PRIMARY_SOURCE_COMMIT_MISMATCH")
    if exact_stat_sources != 1:
        issues.append(f"PRIMARY_DIRECT_STAT_SOURCE_COUNT:{exact_stat_sources}")
    if semantic_overclaims:
        issues.append(f"STRUCTURAL_SOURCE_SEMANTIC_OVERCLAIM:{semantic_overclaims}")
    return {
        "issues": issues,
        "source_count": len(SOURCE_REGISTRY),
        "immutable_source_count": immutable,
        "digest": source_registry_digest(),
    }


def main():
    audit = build_audit()
    print("=" * 76)
    print("CHAMPION SPELL STAT SEMANTICS - RESEARCH AUDIT")
    print("=" * 76)
    print(f"Phase 2H version       : {PHASE2H_VERSION}")
    print(f"Recorded sources       : {audit['source_count']}")
    print(f"Immutable commit URLs  : {audit['immutable_source_count']}")
    print(f"Registry SHA-256       : {audit['digest']}")
    print(f"Issues                 : {len(audit['issues'])}")
    for issue in audit["issues"]:
        print(f"[BLOCKING] {issue}")
    print("STATUS : " + ("FAIL" if audit["issues"] else "PASS"))
    return 1 if audit["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

