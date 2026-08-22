"""Provenance-first stat-reference registry; unknown enums remain unresolved."""
STAT_REFERENCE_VERSION = "champion_spell_stat_reference_phase2g_v1"
STAT_REFERENCE_RESOLVED = "STAT_REFERENCE_RESOLVED"
STAT_REFERENCE_UNRESOLVED = "STAT_REFERENCE_UNRESOLVED"
STAT_OWNER_UNRESOLVED = "STAT_OWNER_UNRESOLVED"
VALIDATED_STAT_REFERENCES = {}

def resolve_stat_reference(raw_reference, owner=None, mappings=None):
    mappings = VALIDATED_STAT_REFERENCES if mappings is None else mappings
    if raw_reference not in mappings:
        return {"status": STAT_REFERENCE_UNRESOLVED, "raw_reference": raw_reference, "stat": None, "owner": owner}
    if owner not in {"CASTER", "TARGET", "SOURCE_LEVEL"}:
        return {"status": STAT_OWNER_UNRESOLVED, "raw_reference": raw_reference, "stat": mappings[raw_reference], "owner": owner}
    return {"status": STAT_REFERENCE_RESOLVED, "raw_reference": raw_reference, "stat": mappings[raw_reference], "owner": owner}

def inventory_stat_references(catalog):
    occurrences = []
    for champion in catalog.get("records", {}).values():
        for spell in champion.get("primary_spells", []):
            for node in spell.get("calculation_nodes", []):
                for ref in node.get("stat_references", []):
                    occurrences.append({"champion": spell.get("champion_id"), "slot": spell.get("slot"), "class": node.get("calculation_class"), "path": node.get("graph_path"), "raw_reference": ref.get("value")})
    return occurrences
