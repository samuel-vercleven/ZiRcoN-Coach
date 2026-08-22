"""Optional exact-key cache around the frozen Phase 2F catalog builder."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

from knowledge.champion_spell_source import (
    CHAMPION_SPELL_SOURCE_VERSION,
    DATAMINE_COMMIT,
    EXPECTED_DDRAGON_VERSION,
    EXPECTED_LOCALE,
    build_champion_spell_source_catalog,
)

CACHE_VERSION = "pinned_spell_catalog_cache_v1"
CACHE_PATH = Path(".cache/zircon/champion_spell_source.json.gz")


def cache_key():
    return {
        "cache_version": CACHE_VERSION,
        "source_version": CHAMPION_SPELL_SOURCE_VERSION,
        "source_commit": DATAMINE_COMMIT,
        "ddragon_version": EXPECTED_DDRAGON_VERSION,
        "locale": EXPECTED_LOCALE,
    }


def load_cached_catalog(path=CACHE_PATH):
    path = Path(path)
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    return payload.get("catalog") if payload.get("key") == cache_key() else None


def save_cached_catalog(catalog, path=CACHE_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as handle:
        json.dump({"key": cache_key(), "catalog": catalog}, handle, ensure_ascii=False)


def get_pinned_spell_catalog(use_cache=True):
    if use_cache:
        cached = load_cached_catalog()
        if cached is not None:
            return cached
    catalog = build_champion_spell_source_catalog()
    if use_cache and catalog.get("source_status", "").startswith("PINNED_"):
        save_cached_catalog(catalog)
    return catalog
