"""Pinned, non-executable champion-spell calculation source catalog.

Phase 2F intentionally preserves Riot game-file datamine structures.  It does
not evaluate a spell formula or label a formula as damage.
"""

from __future__ import annotations

import copy
import json
import re
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


CHAMPION_SPELL_SOURCE_VERSION = "champion_spell_source_phase2f_v1"
EXPECTED_CHAMPION_KNOWLEDGE_VERSION = "champion_knowledge_phase2b1_c_v1"
EXPECTED_DDRAGON_VERSION = "16.16.1"
EXPECTED_LOCALE = "fr_FR"
EXPECTED_CHAMPION_COUNT = 173
PRIMARY_SLOTS = ("Q", "W", "E", "R")

DATAMINE_REPOSITORY = "Haru-Kay/LeagueDatamines"
DATAMINE_COMMIT = "9245fd616059c6c658d1faa1029f0e18ea179154"
DATAMINE_COMMIT_LABEL = "LIVE 26.16 (#17)"
TARGET_PATCH = "16.16"
TARGET_RIOT_PATCH_LABEL = "26.16"
RAW_GITHUB_BASE = (
    "https://raw.githubusercontent.com/"
    f"{DATAMINE_REPOSITORY}/{DATAMINE_COMMIT}"
)

SOURCE_EXACT_PATCH = "PINNED_LEAGUE_DATAMINE_LIVE_26_16"
SOURCE_UNAVAILABLE = "PINNED_LEAGUE_DATAMINE_SOURCE_UNAVAILABLE"
CALCULATIONS_EXPOSED = "CALCULATIONS_EXPOSED"
NO_CALCULATIONS_EXPOSED = "NO_CALCULATIONS_EXPOSED"
MALFORMED_CALCULATION_GRAPH = "MALFORMED_CALCULATION_GRAPH"
UNINTERPRETED_CALCULATION_CLASS = "UNINTERPRETED_CALCULATION_CLASS"
EXACT_PRIMARY_SPELL_PATH = "EXACT_PRIMARY_SPELL_PATH"
EXACT_OBJECT_PATH_MATCH = "EXACT_OBJECT_PATH_MATCH"
PRIMARY_SPELL_OBJECT_NOT_FOUND = "PRIMARY_SPELL_OBJECT_NOT_FOUND"
PRIMARY_SPELL_PATH_AMBIGUOUS = "PRIMARY_SPELL_PATH_AMBIGUOUS"

DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_WORKERS = 8


def _normalize_name(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", text.casefold())


def _candidate_slugs(champion_record):
    candidates = []
    for value in (champion_record.get("champion_id"), champion_record.get("name")):
        normalized = _normalize_name(value)
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    # These are directory aliases in the pinned export, not spell mapping
    # guesses and never affect Q/W/E/R identity.
    aliases = {
        "wukong": "monkeyking",
        "nunuwillump": "nunu",
        "renataglasc": "renata",
    }
    for candidate in list(candidates):
        alias = aliases.get(candidate)
        if alias and alias not in candidates:
            candidates.append(alias)
    return candidates


def _urls_for_slug(slug):
    prefix = f"{RAW_GITHUB_BASE}/champions/{slug}"
    return {
        "base_stats": f"{prefix}/BaseStats.json",
        "spells": f"{prefix}/Spells.json",
    }


def _request_json(url, timeout):
    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": "ZiRcoN-Coach/ChampionSpellSource (local factual audit)"
        },
    )
    response.raise_for_status()
    return response.json()


def _character_root(payload):
    if not isinstance(payload, dict):
        return None, None
    matches = [
        (key, value)
        for key, value in payload.items()
        if isinstance(key, str)
        and key.casefold().endswith("/characterrecords/root")
        and isinstance(value, dict)
    ]
    return matches[0] if len(matches) == 1 else (None, None)


def extract_primary_spell_paths(base_stats_payload):
    """Read only the primary ordered Q/W/E/R paths from CharacterRecords/Root."""
    root_key, root = _character_root(base_stats_payload)
    if root is None:
        return {
            "status": SOURCE_UNAVAILABLE,
            "reason": "CHARACTER_RECORD_ROOT_NOT_FOUND_OR_AMBIGUOUS",
            "root_key": root_key,
            "spell_paths": [],
            "spell_names": [],
        }

    spell_paths = root.get("spells")
    spell_names = root.get("spellNames")
    if not isinstance(spell_paths, list) or len(spell_paths) != 4:
        return {
            "status": SOURCE_UNAVAILABLE,
            "reason": "PRIMARY_SPELL_PATH_LIST_NOT_EXACTLY_FOUR",
            "root_key": root_key,
            "spell_paths": list(spell_paths) if isinstance(spell_paths, list) else [],
            "spell_names": list(spell_names) if isinstance(spell_names, list) else [],
        }

    return {
        "status": SOURCE_EXACT_PATCH,
        "reason": None,
        "root_key": root_key,
        "spell_paths": list(spell_paths),
        "spell_names": list(spell_names) if isinstance(spell_names, list) else [],
        "character_name_datamine": root.get("mCharacterName"),
    }


def _match_spell_object(spells_payload, expected_path):
    if not isinstance(spells_payload, dict):
        return PRIMARY_SPELL_OBJECT_NOT_FOUND, None, []
    direct = spells_payload.get(expected_path)
    if isinstance(direct, dict):
        return EXACT_PRIMARY_SPELL_PATH, direct, [expected_path]

    matches = [
        (key, value)
        for key, value in spells_payload.items()
        if isinstance(value, dict) and value.get("objectPath") == expected_path
    ]
    if len(matches) == 1:
        return EXACT_OBJECT_PATH_MATCH, matches[0][1], [matches[0][0]]
    if len(matches) > 1:
        return PRIMARY_SPELL_PATH_AMBIGUOUS, None, [key for key, _ in matches]
    return PRIMARY_SPELL_OBJECT_NOT_FOUND, None, []


def _walk_calculation_nodes(value, path, nodes):
    if isinstance(value, dict):
        class_name = value.get("~class")
        if class_name is not None:
            named_refs = [
                {"field": key, "value": item}
                for key, item in value.items()
                if "datavalue" in key.casefold() and isinstance(item, str)
            ]
            stat_refs = [
                {"field": key, "value": item}
                for key, item in value.items()
                if key.casefold() in {"mstat", "mstatformula"}
            ]
            coefficient_fields = [
                {"field": key, "value": item}
                for key, item in value.items()
                if any(token in key.casefold() for token in ("coefficient", "ratio", "multiplier"))
            ]
            nodes.append(
                {
                    "graph_path": path,
                    "calculation_class": class_name,
                    "field_names": sorted(value),
                    "named_data_value_references": named_refs,
                    "stat_references": stat_refs,
                    "coefficient_fields": coefficient_fields,
                    "raw_node_payload": copy.deepcopy(value),
                    "interpretation_status": UNINTERPRETED_CALCULATION_CLASS,
                }
            )
        for key, item in value.items():
            _walk_calculation_nodes(item, f"{path}/{key}", nodes)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_calculation_nodes(item, f"{path}/{index}", nodes)


def inventory_calculation_graph(raw_calculations):
    if raw_calculations is None:
        return {
            "status": NO_CALCULATIONS_EXPOSED,
            "calculation_keys": [],
            "nodes": [],
            "classes": [],
            "raw_calculations": None,
        }
    if not isinstance(raw_calculations, dict):
        return {
            "status": MALFORMED_CALCULATION_GRAPH,
            "calculation_keys": [],
            "nodes": [],
            "classes": [],
            "raw_calculations": copy.deepcopy(raw_calculations),
        }

    nodes = []
    _walk_calculation_nodes(raw_calculations, "mSpellCalculations", nodes)
    return {
        "status": CALCULATIONS_EXPOSED,
        "calculation_keys": list(raw_calculations),
        "nodes": nodes,
        "classes": sorted(
            {
                node["calculation_class"]
                for node in nodes
                if isinstance(node["calculation_class"], str)
            }
        ),
        "raw_calculations": copy.deepcopy(raw_calculations),
    }


def _data_values(spell_object):
    spell_data = spell_object.get("mSpell") if isinstance(spell_object, dict) else None
    if not isinstance(spell_data, dict):
        return None
    return copy.deepcopy(spell_data.get("DataValues"))


def build_primary_spell_record(champion_record, slot, expected_path, spell_name, spells_payload):
    mapping_status, spell_object, match_keys = _match_spell_object(spells_payload, expected_path)
    base = {
        "champion_spell_source_version": CHAMPION_SPELL_SOURCE_VERSION,
        "champion_id": champion_record.get("champion_id"),
        "champion_name": champion_record.get("name"),
        "slot": slot,
        "internal_spell_path": expected_path,
        "base_stats_spell_name": spell_name,
        "mapping_status": mapping_status,
        "mapping_match_keys": match_keys,
        "calculation_status": NO_CALCULATIONS_EXPOSED,
        "source_status": SOURCE_EXACT_PATCH,
        "source_repository": DATAMINE_REPOSITORY,
        "source_commit": DATAMINE_COMMIT,
        "source_commit_label": DATAMINE_COMMIT_LABEL,
        "target_patch": TARGET_PATCH,
        "target_ddragon_version": champion_record.get("ddragon_version"),
        "source_type": "COMMUNITY_DATAMINE_EXPORT_OF_RIOT_GAME_FILES",
        "formula_execution": "NOT_EXECUTED",
    }
    if spell_object is None:
        return base

    spell_data = spell_object.get("mSpell")
    if not isinstance(spell_data, dict):
        graph = inventory_calculation_graph("MISSING_mSpell_OBJECT")
    else:
        graph = inventory_calculation_graph(spell_data.get("mSpellCalculations"))
    base.update(
        {
            "object_name": spell_object.get("ObjectName"),
            "m_script_name": spell_object.get("mScriptName"),
            "object_path": spell_object.get("objectPath"),
            "raw_spell_object": copy.deepcopy(spell_object),
            "raw_data_values": _data_values(spell_object),
            "raw_calculation_names": graph["calculation_keys"],
            "raw_m_spell_calculations": graph["raw_calculations"],
            "calculation_nodes": graph["nodes"],
            "calculation_classes": graph["classes"],
            "calculation_status": graph["status"],
        }
    )
    return base


def build_champion_spell_source_record(champion_record, base_stats_payload, spells_payload, urls):
    primary = extract_primary_spell_paths(base_stats_payload)
    result = {
        "champion_spell_source_version": CHAMPION_SPELL_SOURCE_VERSION,
        "champion_id": champion_record.get("champion_id"),
        "champion_name": champion_record.get("name"),
        "ddragon_spell_slots": [
            spell.get("inferred_slot") for spell in champion_record.get("spells", [])
        ],
        "base_stats_url": urls.get("base_stats"),
        "spells_url": urls.get("spells"),
        "source_status": primary["status"],
        "source_error": primary["reason"],
        "character_record_root_key": primary["root_key"],
        "primary_spell_paths": primary["spell_paths"],
        "spell_names": primary["spell_names"],
        "primary_spells": [],
    }
    if primary["status"] != SOURCE_EXACT_PATCH:
        return result

    duplicate_paths = {path for path, count in Counter(primary["spell_paths"]).items() if count > 1}
    for index, slot in enumerate(PRIMARY_SLOTS):
        path = primary["spell_paths"][index]
        record = build_primary_spell_record(
            champion_record,
            slot,
            path,
            primary["spell_names"][index] if index < len(primary["spell_names"]) else None,
            spells_payload,
        )
        if path in duplicate_paths:
            record["mapping_status"] = PRIMARY_SPELL_PATH_AMBIGUOUS
            record["mapping_match_keys"] = [path]
        result["primary_spells"].append(record)
    return result


def _fetch_champion_source(champion_record, timeout):
    errors = []
    expected_names = {
        _normalize_name(champion_record.get("champion_id")),
        _normalize_name(champion_record.get("name")),
    }
    expected_names.discard("")
    for slug in _candidate_slugs(champion_record):
        urls = _urls_for_slug(slug)
        try:
            base_stats = _request_json(urls["base_stats"], timeout)
            spells = _request_json(urls["spells"], timeout)
        except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{slug}: {type(exc).__name__}: {exc}")
            continue
        primary = extract_primary_spell_paths(base_stats)
        actual_name = _normalize_name(primary.get("character_name_datamine"))
        if actual_name and actual_name not in expected_names and actual_name != slug:
            errors.append(f"{slug}: identity mismatch actual={actual_name}")
            continue
        return base_stats, spells, urls, errors
    return None, None, None, errors


def build_champion_spell_source_catalog(champion_catalog=None, timeout=DEFAULT_TIMEOUT_SECONDS, workers=DEFAULT_WORKERS):
    if champion_catalog is None:
        from knowledge.champion_knowledge import build_champion_knowledge_catalog

        champion_catalog = build_champion_knowledge_catalog(
            requested_game_version=EXPECTED_DDRAGON_VERSION,
            locale=EXPECTED_LOCALE,
        )

    champions = champion_catalog.get("records", {})
    ddragon_version = champion_catalog.get("resolved_ddragon_version")
    source_compatible = ddragon_version == EXPECTED_DDRAGON_VERSION
    records, source_failures = {}, {}
    if source_compatible:
        with ThreadPoolExecutor(max_workers=max(1, int(workers))) as pool:
            futures = {
                pool.submit(_fetch_champion_source, record, timeout): (champion_id, record)
                for champion_id, record in champions.items()
            }
            for future in as_completed(futures):
                champion_id, champion_record = futures[future]
                try:
                    base_stats, spells, urls, errors = future.result()
                except Exception as exc:  # Audit must report, never silently drop.
                    base_stats, spells, urls, errors = None, None, None, [f"{type(exc).__name__}: {exc}"]
                if base_stats is None:
                    source_failures[champion_id] = errors
                    continue
                records[champion_id] = build_champion_spell_source_record(
                    champion_record, base_stats, spells, urls
                )
                if errors:
                    source_failures[champion_id] = errors
    else:
        source_failures = {
            champion_id: [
                f"Exact source is only valid for {EXPECTED_DDRAGON_VERSION}; got {ddragon_version}."
            ]
            for champion_id in champions
        }

    source_status = SOURCE_EXACT_PATCH if len(records) == len(champions) and source_compatible else SOURCE_UNAVAILABLE
    return {
        "champion_spell_source_version": CHAMPION_SPELL_SOURCE_VERSION,
        "champion_knowledge_version": champion_catalog.get("champion_knowledge_version"),
        "ddragon_version": ddragon_version,
        "locale": champion_catalog.get("locale"),
        "source_status": source_status,
        "source_repository": DATAMINE_REPOSITORY,
        "source_commit": DATAMINE_COMMIT,
        "source_commit_label": DATAMINE_COMMIT_LABEL,
        "target_patch": TARGET_PATCH,
        "target_riot_patch_label": TARGET_RIOT_PATCH_LABEL,
        "source_type": "COMMUNITY_DATAMINE_EXPORT_OF_RIOT_GAME_FILES",
        "no_latest_or_previous_patch_fallback": True,
        "expected_champion_count": len(champions),
        "records": records,
        "source_failures": source_failures,
    }
