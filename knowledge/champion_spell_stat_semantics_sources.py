"""Pinned public provenance for Phase 2H stat semantics.

This module is deliberately declarative.  A structural type, a field name, or
an enum position is never promoted to semantic evidence by itself.
"""

from __future__ import annotations

import hashlib
import json


PHASE2H_VERSION = "champion_spell_stat_semantics_phase2h_v1"
PINNED_DATAMINE_REPOSITORY = "Haru-Kay/LeagueDatamines"
PINNED_DATAMINE_COMMIT = "9245fd616059c6c658d1faa1029f0e18ea179154"
PINNED_GAME_PATCH = "26.16"
PINNED_DDRAGON_VERSION = "16.16.1"
PINNED_LOCALE = "fr_FR"

LEAGUE_META_CLASSES_COMMIT = "6222976776a9ca18fc63945930f22b8b03b30144"
CALCREV_COMMIT = "40f21c06e5cfc10750bb44b39d1f2d4e3567a6dc"
CDTB_COMMIT = "b52d04fa986a1620f31bd3ca8f9dbbea169b1641"
LEAGUEBUILDER_CURRENT_COMMIT = "1ae51c26bdde36e178174b98f7c65a52d55f10fa"

SOURCE_REGISTRY = {
    "league_datamines_global_stats_ui": {
        "tier": "EXACT_PINNED_26_16_GAME_FILE_EXPORT",
        "repository": PINNED_DATAMINE_REPOSITORY,
        "commit": PINNED_DATAMINE_COMMIT,
        "url": (
            "https://raw.githubusercontent.com/Haru-Kay/LeagueDatamines/"
            f"{PINNED_DATAMINE_COMMIT}/aram/data/GlobalStatsUIData.json"
        ),
        "supports": ["DIRECT_RAW_STAT_ID_TO_UI_STAT_IDENTITY"],
        "limitations": [
            "Community datamine export rather than Riot-authored enum documentation.",
            "The file path is under the ARAM export; spell occurrences are cross-checked in the exact pinned champion export.",
            "It does not define stat ownership or mStatFormula semantics.",
        ],
        "hash_policy": "IMMUTABLE_GIT_COMMIT_URL",
    },
    "league_meta_classes_16_16": {
        "tier": "EXACT_PATCH_STRUCTURAL_REVERSE_ENGINEERING",
        "repository": "LeagueToolkit/lol-meta-classes",
        "commit": LEAGUE_META_CLASSES_COMMIT,
        "url": (
            "https://github.com/LeagueToolkit/lol-meta-classes/blob/"
            f"{LEAGUE_META_CLASSES_COMMIT}/db/database.py"
        ),
        "supports": [
            "MSTAT_AND_MSTATFORMULA_ARE_U8_FIELDS",
            "THREE_STAT_CALCULATION_CLASSES_SHARE_THE_FIELDS",
        ],
        "limitations": [
            "UInt8 structure does not prove an enum meaning.",
            "The schema does not prove caster/target ownership.",
        ],
        "hash_policy": "IMMUTABLE_GIT_COMMIT_URL",
    },
    "calcrev_historical": {
        "tier": "HISTORICAL_TECHNICAL_REVERSE_ENGINEERING",
        "repository": "moonshadow565/calcrev",
        "commit": CALCREV_COMMIT,
        "url": (
            "https://github.com/moonshadow565/calcrev/blob/"
            f"{CALCREV_COMMIT}/calc.py"
        ),
        "supports": [
            "STAT_CLASSES_FORWARD_MSTAT_MSTATFORMULA_AND_A_COEFFICIENT",
            "COEFFICIENT_SOURCE_DIFFERS_BY_CALCULATION_CLASS",
        ],
        "limitations": [
            "Historical source, not patch 26.16.",
            "get_stat_total is explicitly unimplemented and returns zero.",
            "It cannot validate enum values, formula meanings, or owner identity.",
        ],
        "hash_policy": "IMMUTABLE_GIT_COMMIT_URL",
    },
    "calcrev_structures_historical": {
        "tier": "HISTORICAL_TECHNICAL_REVERSE_ENGINEERING",
        "repository": "moonshadow565/calcrev",
        "commit": CALCREV_COMMIT,
        "url": (
            "https://github.com/moonshadow565/calcrev/blob/"
            f"{CALCREV_COMMIT}/calc_ida.h"
        ),
        "supports": ["MSTAT_AND_MSTATFORMULA_BYTE_LAYOUT"],
        "limitations": ["Memory layout is not semantic enum documentation."],
        "hash_policy": "IMMUTABLE_GIT_COMMIT_URL",
    },
    "cdtb_tooling": {
        "tier": "TECHNICAL_EXTRACTION_TOOLING",
        "repository": "CommunityDragon/CDTB",
        "commit": CDTB_COMMIT,
        "url": f"https://github.com/CommunityDragon/CDTB/tree/{CDTB_COMMIT}",
        "supports": ["GAME_FILE_EXTRACTION_AND_HASH_RESOLUTION_CONTEXT"],
        "limitations": ["No direct mStat or mStatFormula semantic table was found."],
        "hash_policy": "IMMUTABLE_GIT_COMMIT_URL",
    },
    "hextechdocs_historical": {
        "tier": "HISTORICAL_COMMUNITY_DOCUMENTATION",
        "publication_date": "2022-01-25",
        "url": "https://hextechdocs.dev/resolving-variables-in-spell-textsa/",
        "supports": ["HISTORICAL_CLAIM_THAT_MSTATFORMULA_HAS_BASE_BONUS_TOTAL_VARIANTS"],
        "limitations": [
            "Its numeric formula table conflicts with exact 26.16 fixtures.",
            "Its linked historical leaguebuilder commit is no longer available at the published URL.",
            "Historical claims are never substituted for exact patch evidence.",
        ],
        "hash_policy": "PUBLICATION_DATE_AND_URL_RECORDED_CONTENT_NOT_HASHED",
    },
    "leaguebuilder_current_formula": {
        "tier": "CURRENT_COMMUNITY_IMPLEMENTATION_CROSS_PATCH_ONLY",
        "repository": "OsOmE1/leaguebuilder",
        "commit": LEAGUEBUILDER_CURRENT_COMMIT,
        "url": (
            "https://github.com/OsOmE1/leaguebuilder/blob/"
            f"{LEAGUEBUILDER_CURRENT_COMMIT}/LeagueBuilder/Data/Models/StatFormulaType.cs"
        ),
        "supports": ["CURRENT_COMMUNITY_FORMULA_ENUM_CLAIM"],
        "limitations": [
            "Not pinned to patch 26.16.",
            "Its current StatType numbering conflicts with the exact pinned GlobalStatsUIData table.",
            "It is supporting/contradiction evidence only, never the primary raw-stat mapping source.",
        ],
        "hash_policy": "IMMUTABLE_GIT_COMMIT_URL",
    },
    "riot_patch_26_1": {
        "tier": "OFFICIAL_RIOT_PATCH_DOCUMENTATION",
        "publication_patch": "26.1",
        "url": "https://www.leagueoflegends.com/en-us/news/game-updates/patch-26-1-notes/",
        "supports": ["AKSHAN_Q_CHANGED_FROM_TOTAL_AD_TO_BONUS_AD"],
        "limitations": ["Human-readable mechanic documentation, not an internal enum table."],
        "hash_policy": "OFFICIAL_URL_AND_PATCH_RECORDED_CONTENT_NOT_HASHED",
    },
    "riot_patch_9_24": {
        "tier": "OFFICIAL_RIOT_PATCH_DOCUMENTATION",
        "publication_patch": "9.24",
        "url": "https://www.leagueoflegends.com/en-us/news/game-updates/patch-9-24-notes/",
        "supports": ["DIANA_W_SHIELD_BONUS_HEALTH_RATIO"],
        "limitations": ["Historical mechanic documentation; exact 26.16 structure is independently pinned."],
        "hash_policy": "OFFICIAL_URL_AND_PATCH_RECORDED_CONTENT_NOT_HASHED",
    },
    "riot_patch_9_2": {
        "tier": "OFFICIAL_RIOT_PATCH_DOCUMENTATION",
        "publication_patch": "9.2",
        "url": "https://www.leagueoflegends.com/en-gb/news/game-updates/patch-9-2-notes/",
        "supports": ["AATROX_Q_TOTAL_ATTACK_DAMAGE_RATIO"],
        "limitations": ["Historical mechanic documentation; exact 26.16 structure is independently pinned."],
        "hash_policy": "OFFICIAL_URL_AND_PATCH_RECORDED_CONTENT_NOT_HASHED",
    },
    "riot_patch_26_2": {
        "tier": "OFFICIAL_RIOT_PATCH_DOCUMENTATION",
        "publication_patch": "26.2",
        "url": "https://www.leagueoflegends.com/en-us/news/game-updates/patch-26-2-notes/",
        "supports": ["MALPHITE_E_ARMOR_RATIO"],
        "limitations": ["Human-readable mechanic documentation, not an internal enum table."],
        "hash_policy": "OFFICIAL_URL_AND_PATCH_RECORDED_CONTENT_NOT_HASHED",
    },
}


# Direct object keys in exact pinned GlobalStatsUIData.json.  IDs absent from
# this table remain unresolved even if a neighbouring integer looks plausible.
PINNED_GLOBAL_STAT_UI_MAPPING = {
    0: "ABILITY_POWER",
    1: "ARMOR",
    2: "ATTACK_DAMAGE",
    4: "ATTACK_SPEED",
    6: "MAGIC_RESISTANCE",
    7: "MOVE_SPEED",
    8: "CRITICAL_STRIKE_CHANCE",
    9: "CRITICAL_STRIKE_DAMAGE_MULTIPLIER",
    10: "COOLDOWN_REDUCTION",
    11: "ABILITY_HASTE",
    12: "HEALTH",
    17: "DODGE_CHANCE",
    18: "LIFE_STEAL",
    19: "SPELL_VAMP",
    20: "OMNIVAMP",
    22: "MAGIC_PENETRATION_FLAT",
    23: "MAGIC_PENETRATION_PERCENT",
    24: "MAGIC_PENETRATION_BONUS_PERCENT",
    25: "MAGIC_LETHALITY",
    26: "ARMOR_PENETRATION_FLAT",
    27: "ARMOR_PENETRATION_PERCENT",
    28: "ARMOR_PENETRATION_BONUS_PERCENT",
    29: "PHYSICAL_LETHALITY",
    30: "TENACITY",
    31: "ATTACK_RANGE",
    32: "HEALTH_REGENERATION",
    33: "RESOURCE_REGENERATION",
    34: "HEAL_SHIELD_POWER",
}


def source_registry_digest():
    """Return a deterministic local digest of the recorded provenance metadata."""
    payload = json.dumps(SOURCE_REGISTRY, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_source_record(source_id):
    record = SOURCE_REGISTRY.get(source_id)
    return None if record is None else json.loads(json.dumps(record))
