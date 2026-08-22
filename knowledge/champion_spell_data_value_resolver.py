"""Case-sensitive per-spell DataValue registry and rank resolver."""
from collections import defaultdict
from knowledge.champion_spell_value_resolver import PINNED_RANK_0_TO_6, VALUE_RESOLVED, resolve_rank_value

DATA_VALUE_RESOLVED = "DATA_VALUE_RESOLVED"
DATA_VALUE_NOT_FOUND = "DATA_VALUE_NOT_FOUND"
DATA_VALUE_AMBIGUOUS = "DATA_VALUE_AMBIGUOUS"
DATA_VALUE_SHAPE_UNSUPPORTED = "DATA_VALUE_SHAPE_UNSUPPORTED"
DATA_VALUE_NON_NUMERIC = "DATA_VALUE_NON_NUMERIC"
DATA_VALUE_RANK_UNRESOLVED = "DATA_VALUE_RANK_UNRESOLVED"

def build_registry(raw_data_values):
    registry = defaultdict(list)
    for entry in raw_data_values or []:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str):
            registry[entry["name"]].append(entry)
    return dict(registry)

def resolve_data_value(registry, name, rank, max_rank, indexing_contract=PINNED_RANK_0_TO_6):
    matches = registry.get(name, [])
    if not matches: return {"status": DATA_VALUE_NOT_FOUND, "value": None, "name": name}
    if len(matches) != 1: return {"status": DATA_VALUE_AMBIGUOUS, "value": None, "name": name, "matches": matches}
    entry = matches[0]
    result = resolve_rank_value(entry.get("values"), rank, max_rank, indexing_contract)
    if result["status"] != VALUE_RESOLVED:
        if result["status"] == "NON_NUMERIC_VALUE":
            status = DATA_VALUE_NON_NUMERIC
        elif result["status"] == "INVALID_SPELL_RANK":
            status = DATA_VALUE_RANK_UNRESOLVED
        else:
            status = DATA_VALUE_SHAPE_UNSUPPORTED
        return {"status": status, "value": None, "name": name, "rank_result": result, "raw": entry}
    return {"status": DATA_VALUE_RESOLVED, "value": result["value"], "name": name, "raw": entry, "rank_result": result}
