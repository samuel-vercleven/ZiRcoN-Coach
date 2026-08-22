"""Explicit rank/value indexing contracts for pinned spell source arrays."""
from __future__ import annotations

VALUE_RESOLVER_VERSION = "champion_spell_value_resolver_phase2g_v1"
VALUE_RESOLVED = "VALUE_RESOLVED"
INVALID_SPELL_RANK = "INVALID_SPELL_RANK"
VALUE_SHAPE_UNSUPPORTED = "VALUE_SHAPE_UNSUPPORTED"
RANK_INDEXING_UNRESOLVED = "RANK_INDEXING_UNRESOLVED"
VALUE_MISSING = "VALUE_MISSING"
NON_NUMERIC_VALUE = "NON_NUMERIC_VALUE"
PINNED_RANK_0_TO_6 = "PINNED_RANK_0_TO_6"

def resolve_rank_value(values, rank, max_rank, indexing_contract=None):
    if (isinstance(rank, bool) or not isinstance(rank, int) or rank < 0
            or isinstance(max_rank, bool) or not isinstance(max_rank, int)
            or max_rank < 1 or rank > max_rank):
        return {"status": INVALID_SPELL_RANK, "value": None, "rank": rank}
    if not isinstance(values, (list, tuple)) or not values:
        return {"status": VALUE_MISSING, "value": None, "rank": rank}
    if indexing_contract == PINNED_RANK_0_TO_6:
        if len(values) != 7 or max_rank > 6:
            return {"status": VALUE_SHAPE_UNSUPPORTED, "value": None, "rank": rank, "length": len(values), "indexing_contract": indexing_contract}
        index = rank
    elif len(values) == 1:
        index = 0
    elif len(values) == max_rank + 1:
        index = rank
    elif len(values) == max_rank and rank >= 1:
        index = rank - 1
    else:
        return {"status": VALUE_SHAPE_UNSUPPORTED, "value": None, "rank": rank, "length": len(values)}
    value = values[index]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return {"status": NON_NUMERIC_VALUE, "value": None, "rank": rank, "index": index}
    return {"status": VALUE_RESOLVED, "value": value, "rank": rank, "index": index, "raw_values": list(values), "indexing_contract": indexing_contract}
