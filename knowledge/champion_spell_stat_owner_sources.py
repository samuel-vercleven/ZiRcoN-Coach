"""Public provenance for Phase 2I stat-owner research.

The recorded implementations prove that stat parts read a unit/champion from
their evaluation context.  They do not prove that every 26.16 client call site
binds that context to the spell caster.
"""

from __future__ import annotations

import hashlib
import json


OWNER_SEMANTICS_VERSION = "champion_spell_stat_owner_semantics_phase2i_v1"
PINNED_DATAMINE_COMMIT = "9245fd616059c6c658d1faa1029f0e18ea179154"
PINNED_GAME_PATCH = "26.16"
PINNED_DDRAGON_VERSION = "16.16.1"
PINNED_LOCALE = "fr_FR"
META_CLASSES_COMMIT = "6222976776a9ca18fc63945930f22b8b03b30144"
CALCREV_COMMIT = "40f21c06e5cfc10750bb44b39d1f2d4e3567a6dc"
LEAGUEBUILDER_COMMIT = "1ae51c26bdde36e178174b98f7c65a52d55f10fa"


OWNER_SOURCE_REGISTRY = {
    "pinned_26_16_spell_graphs": {
        "url": (
            "https://github.com/Haru-Kay/LeagueDatamines/tree/"
            f"{PINNED_DATAMINE_COMMIT}/champions"
        ),
        "repository": "Haru-Kay/LeagueDatamines",
        "commit": PINNED_DATAMINE_COMMIT,
        "patch": PINNED_GAME_PATCH,
        "tier": "EXACT_PINNED_26_16_GAME_FILE_STRUCTURES",
        "supports": [
            "EXHAUSTIVE_SERIALIZED_STAT_CONTEXT_INVENTORY",
            "NO_NAMED_OWNER_SELECTOR_IN_ORDINARY_STAT_SIGNATURES",
        ],
        "limitations": [
            "Serialized structures do not expose runtime call-site bindings.",
            "Absence of a field cannot prove CASTER or TARGET identity.",
        ],
    },
    "meta_classes_26_16": {
        "url": (
            "https://github.com/LeagueToolkit/lol-meta-classes/blob/"
            f"{META_CLASSES_COMMIT}/db/database.py"
        ),
        "repository": "LeagueToolkit/lol-meta-classes",
        "commit": META_CLASSES_COMMIT,
        "patch": "16.16",
        "tier": "PATCH_MATCHED_META_STRUCTURE",
        "supports": [
            "STAT_PARTS_SHARE_MSTAT_AND_MSTATFORMULA",
            "COEFFICIENT_DATA_VALUE_AND_SUBPART_FIELDS_ARE_CLASS_SPECIFIC",
        ],
        "limitations": [
            "Meta field layout does not encode the runtime stat owner.",
            "Inheritance and UInt8 types are structural evidence only.",
        ],
    },
    "calcrev_runtime_interface": {
        "url": (
            "https://github.com/moonshadow565/calcrev/blob/"
            f"{CALCREV_COMMIT}/calc_ida.h"
        ),
        "repository": "moonshadow565/calcrev",
        "commit": CALCREV_COMMIT,
        "patch": "HISTORICAL_UNMATCHED",
        "tier": "HISTORICAL_EXECUTABLE_REVERSE_ENGINEERING",
        "supports": [
            "RESULTNUM_ACCEPTS_UNIT_STAT_COMPONENT",
            "GENERATION_CONTEXT_CARRIES_UNIT_STAT_COMPONENT",
        ],
        "limitations": [
            "Historical and not patch-matched to 26.16.",
            "The header does not identify every caller-provided unit as caster or target.",
        ],
    },
    "calcrev_stat_part_execution": {
        "url": (
            "https://github.com/moonshadow565/calcrev/blob/"
            f"{CALCREV_COMMIT}/calc.py"
        ),
        "repository": "moonshadow565/calcrev",
        "commit": CALCREV_COMMIT,
        "patch": "HISTORICAL_UNMATCHED",
        "tier": "HISTORICAL_EXECUTABLE_REVERSE_ENGINEERING",
        "supports": [
            "STAT_PARTS_DELEGATE_TO_CONTEXT_GET_STAT_TOTAL",
            "COEFFICIENT_SOURCE_DIFFERS_BY_STAT_CLASS",
        ],
        "limitations": [
            "get_stat_total is unimplemented in the public tool.",
            "The evaluation context has no proven CASTER/TARGET binding.",
        ],
    },
    "leaguebuilder_context_execution": {
        "url": (
            "https://github.com/OsOmE1/leaguebuilder/blob/"
            f"{LEAGUEBUILDER_COMMIT}/LeagueBuilder/ChampionInstance.cs"
        ),
        "repository": "OsOmE1/leaguebuilder",
        "commit": LEAGUEBUILDER_COMMIT,
        "patch": "CURRENT_CROSS_PATCH_NOT_26_16_PINNED",
        "tier": "INDEPENDENT_EXECUTABLE_REVERSE_ENGINEERING",
        "supports": [
            "CALCULATION_CONTEXT_CARRIES_CALLER_CHAMPION_INSTANCE",
            "STAT_PARTS_READ_CONTEXT_CHAMPION_STATS",
        ],
        "limitations": [
            "Community implementation, not the game client's call graph.",
            "A caller-supplied Champion does not prove universal caster identity.",
        ],
    },
}


def source_registry_digest():
    payload = json.dumps(
        OWNER_SOURCE_REGISTRY,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_owner_source(source_id):
    record = OWNER_SOURCE_REGISTRY.get(source_id)
    return None if record is None else json.loads(json.dumps(record))
