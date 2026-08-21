import json
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


ATTACK_SPEED_SOURCE_VERSION = "champion_attack_speed_source_v3"

# Exact LIVE 26.16 datamine commit.
#
# GitHub commit:
#   9245fd616059c6c658d1faa1029f0e18ea179154
# Commit title:
#   LIVE 26.16 (#17)
#
# The repository contains per-champion BaseStats.json extracted from Riot game
# files. The source is pinned to this immutable commit instead of following a
# moving "latest" endpoint.
DATAMINE_REPOSITORY = "Haru-Kay/LeagueDatamines"
DATAMINE_COMMIT = "9245fd616059c6c658d1faa1029f0e18ea179154"
TARGET_PATCH = "16.16"
TARGET_RIOT_PATCH_LABEL = "26.16"

RAW_GITHUB_BASE = (
    "https://raw.githubusercontent.com/"
    f"{DATAMINE_REPOSITORY}/{DATAMINE_COMMIT}"
)

SOURCE_EXACT_PATCH = "PINNED_LEAGUE_DATAMINE_LIVE_26_16"

# Kept as an interface-compatible symbol for champion_level_stats.py.
# v4 never emits this status.
SOURCE_VERIFIED_PREVIOUS_PATCH_CARRY_FORWARD = (
    "COMMUNITYDRAGON_VERIFIED_PREVIOUS_PATCH_CARRY_FORWARD"
)

SOURCE_PARTIAL = "PINNED_LEAGUE_DATAMINE_PARTIAL"
SOURCE_UNAVAILABLE = "PINNED_LEAGUE_DATAMINE_UNAVAILABLE"

RATIO_RESOLVED = "ATTACK_SPEED_RATIO_RESOLVED"
RATIO_MISSING = "ATTACK_SPEED_RATIO_MISSING"

DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_WORKERS = 12


def _normalize_name(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]", "", text.casefold())


def cdragon_patch_from_ddragon(ddragon_version):
    """
    Historical compatibility helper.

    Phase 2D v4 no longer depends on CommunityDragon at runtime, but the
    caller still supplies a frozen Data Dragon catalog. This helper verifies
    that the catalog belongs to the expected major.minor patch.
    """
    parts = str(ddragon_version or "").split(".")
    if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise ValueError(
            f"Cannot derive patch from Data Dragon version {ddragon_version!r}"
        )
    return f"{parts[0]}.{parts[1]}"


def _base_value(value):
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, dict):
        base = value.get("baseValue")
        if isinstance(base, (int, float)):
            return float(base)

    return None


def _character_root(payload):
    if not isinstance(payload, dict):
        return None, None

    candidates = [
        (key, value)
        for key, value in payload.items()
        if (
            isinstance(key, str)
            and key.casefold().endswith("/characterrecords/root")
            and isinstance(value, dict)
        )
    ]

    if len(candidates) == 1:
        return candidates[0]

    # Defensive recursive fallback for future export wrappers.
    found = []

    def visit(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if (
                    isinstance(key, str)
                    and key.casefold().endswith("/characterrecords/root")
                    and isinstance(value, dict)
                ):
                    found.append((key, value))
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(payload)

    if len(found) == 1:
        return found[0]

    return None, None


def extract_attack_speed_record(
    payload,
    source_url,
    source_patch=TARGET_PATCH,
):
    root_key, root = _character_root(payload)
    if root is None:
        return None

    ratio = _base_value(
        root.get("attackSpeedRatioModifiable")
    )
    if ratio is None:
        ratio = _base_value(root.get("attackSpeedRatio"))

    if ratio is None:
        return None

    base_attack_speed = _base_value(
        root.get("attackSpeedModifiable")
    )
    if base_attack_speed is None:
        base_attack_speed = _base_value(
            root.get("attackSpeed")
        )

    attack_speed_growth = _base_value(
        root.get("attackSpeedPerLevelModifiable")
    )
    if attack_speed_growth is None:
        attack_speed_growth = _base_value(
            root.get("attackSpeedPerLevel")
        )

    champion_name = root.get("mCharacterName")
    if not champion_name and isinstance(root_key, str):
        parts = root_key.replace("\\", "/").split("/")
        if len(parts) >= 2:
            champion_name = parts[1]

    return {
        "attack_speed_source_version": ATTACK_SPEED_SOURCE_VERSION,
        "champion_name_datamine": champion_name,
        "normalized_name": _normalize_name(champion_name),
        "status": RATIO_RESOLVED,
        "attack_speed_ratio": ratio,
        "attack_speed_cdragon": base_attack_speed,
        "attack_speed_growth_percent_cdragon": attack_speed_growth,
        "source": "PINNED_LEAGUE_DATAMINE_RIOT_GAME_FILE",
        "source_type": "RIOT_GAME_FILE_GITHUB_DATAMINE",
        "source_root_key": root_key,
        "source_url": source_url,
        "source_patch": source_patch,
        "source_repository": DATAMINE_REPOSITORY,
        "source_commit": DATAMINE_COMMIT,
        "source_riot_patch_label": TARGET_RIOT_PATCH_LABEL,
        "raw_character_record_subset": {
            "attackSpeedModifiable": root.get(
                "attackSpeedModifiable"
            ),
            "attackSpeedPerLevelModifiable": root.get(
                "attackSpeedPerLevelModifiable"
            ),
            "attackSpeedRatioModifiable": root.get(
                "attackSpeedRatioModifiable"
            ),
        },
    }


def extract_attack_speed_records(
    payload,
    source_url,
    source_patch=TARGET_PATCH,
):
    """
    Compatibility wrapper used by older synthetic checks.

    A per-champion BaseStats.json contains one CharacterRecords/Root, so this
    returns a map keyed by the normalized champion name.
    """
    record = extract_attack_speed_record(
        payload,
        source_url,
        source_patch=source_patch,
    )
    if record is None:
        return {}

    normalized = record.get("normalized_name")
    if not normalized:
        return {}

    return {normalized: record}


def _request_json(url, timeout):
    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": (
                "ZiRcoN-Coach/ChampionLevelStats "
                "(local factual validation)"
            )
        },
    )
    response.raise_for_status()
    return response.json()


def _candidate_slugs(champion_record):
    candidates = []

    # Data Dragon's champion_id normally matches the internal game directory
    # after lowercase normalization (e.g. MonkeyKing -> monkeyking).
    for value in (
        champion_record.get("champion_id"),
        champion_record.get("name"),
    ):
        normalized = _normalize_name(value)
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    # Path aliases only. No stat values are hardcoded here.
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


def _raw_url(slug):
    return (
        f"{RAW_GITHUB_BASE}/champions/"
        f"{slug}/BaseStats.json"
    )


def _fetch_one(champion_record, timeout):
    errors = []

    for slug in _candidate_slugs(champion_record):
        url = _raw_url(slug)

        try:
            payload = _request_json(url, timeout)
        except (
            requests.RequestException,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            errors.append(
                f"{url}: {type(exc).__name__}: {exc}"
            )
            continue

        record = extract_attack_speed_record(
            payload,
            source_url=url,
            source_patch=TARGET_PATCH,
        )

        if record is None:
            errors.append(
                f"{url}: attackSpeedRatioModifiable not found"
            )
            continue

        expected_names = {
            _normalize_name(
                champion_record.get("champion_id")
            ),
            _normalize_name(
                champion_record.get("name")
            ),
        }
        expected_names.discard("")

        actual = record.get("normalized_name")

        # Internal game names can differ from display names, so accept either
        # the source slug or an expected normalized name.
        if (
            actual
            and actual not in expected_names
            and actual != slug
        ):
            errors.append(
                f"{url}: identity mismatch "
                f"expected={sorted(expected_names)} "
                f"actual={actual}"
            )
            continue

        return record, errors

    return None, errors


def load_attack_speed_ratio_catalog(
    champion_catalog,
    timeout=DEFAULT_TIMEOUT_SECONDS,
    workers=DEFAULT_WORKERS,
):
    """
    Resolve Attack Speed Ratio from an immutable LIVE 26.16 game-file
    datamine snapshot.

    This deliberately does NOT:
      - follow a moving latest branch;
      - fall back to a previous patch;
      - infer ratio = base attack speed.

    The source commit is patch-pinned and all available base-AS / AS-growth
    fields are cross-checked downstream against frozen Data Dragon 16.16.1.
    """
    ddragon_version = champion_catalog.get(
        "resolved_ddragon_version"
    )
    target_patch = cdragon_patch_from_ddragon(
        ddragon_version
    )

    expected_records = champion_catalog.get(
        "records",
        {},
    )

    if target_patch != TARGET_PATCH:
        return {
            "attack_speed_source_version": (
                ATTACK_SPEED_SOURCE_VERSION
            ),
            "source_status": SOURCE_UNAVAILABLE,
            "ddragon_version": ddragon_version,
            "target_patch": target_patch,
            "selected_source_patch": TARGET_PATCH,
            "records": {},
            "resolved_count": 0,
            "expected_count": len(expected_records),
            "missing": [
                {
                    "champion_id": champion_id,
                    "name": record.get("name"),
                    "status": RATIO_MISSING,
                    "reason": (
                        "Pinned datamine is only validated "
                        "for patch 16.16."
                    ),
                }
                for champion_id, record
                in expected_records.items()
            ],
            "carry_forward": None,
            "attempts": [
                {
                    "source_patch": TARGET_PATCH,
                    "consolidated_url": (
                        "PINNED_GITHUB_PER_CHAMPION_FILES"
                    ),
                    "consolidated_error": (
                        f"Catalog patch {target_patch} != "
                        f"pinned source patch {TARGET_PATCH}"
                    ),
                    "resolved_count": 0,
                    "expected_count": len(
                        expected_records
                    ),
                    "missing_count": len(
                        expected_records
                    ),
                    "individual_error_champions": 0,
                }
            ],
            "no_unverified_latest_fallback": True,
            "provenance_note": (
                "Patch mismatch blocked intentionally."
            ),
            "source_repository": DATAMINE_REPOSITORY,
            "source_commit": DATAMINE_COMMIT,
            "source_riot_patch_label": (
                TARGET_RIOT_PATCH_LABEL
            ),
        }

    resolved = {}
    errors_by_champion = {}

    with ThreadPoolExecutor(
        max_workers=max(1, int(workers))
    ) as pool:
        future_map = {
            pool.submit(
                _fetch_one,
                champion_record,
                timeout,
            ): (champion_id, champion_record)
            for champion_id, champion_record
            in expected_records.items()
        }

        for future in as_completed(future_map):
            champion_id, champion_record = (
                future_map[future]
            )

            try:
                record, errors = future.result()
            except Exception as exc:
                record = None
                errors = [
                    f"{type(exc).__name__}: {exc}"
                ]

            if record is not None:
                enriched = dict(record)
                enriched.update(
                    {
                        "target_ddragon_version": (
                            ddragon_version
                        ),
                        "target_patch": target_patch,
                        "source_status": (
                            SOURCE_EXACT_PATCH
                        ),
                        "carry_forward": None,
                    }
                )
                resolved[champion_id] = enriched

            if errors:
                errors_by_champion[
                    champion_id
                ] = errors

    missing = [
        {
            "champion_id": champion_id,
            "name": champion_record.get("name"),
            "status": RATIO_MISSING,
        }
        for champion_id, champion_record
        in expected_records.items()
        if champion_id not in resolved
    ]

    if len(resolved) == len(expected_records):
        source_status = SOURCE_EXACT_PATCH
    elif resolved:
        source_status = SOURCE_PARTIAL
    else:
        source_status = SOURCE_UNAVAILABLE

    # Update each record with final catalog source status.
    for record in resolved.values():
        record["source_status"] = source_status

    return {
        "attack_speed_source_version": (
            ATTACK_SPEED_SOURCE_VERSION
        ),
        "source_status": source_status,
        "ddragon_version": ddragon_version,
        "target_patch": target_patch,
        "selected_source_patch": TARGET_PATCH,
        "records": resolved,
        "resolved_count": len(resolved),
        "expected_count": len(expected_records),
        "missing": missing,
        "carry_forward": None,
        "attempts": [
            {
                "source_patch": TARGET_PATCH,
                "consolidated_url": (
                    "PINNED_GITHUB_PER_CHAMPION_FILES"
                ),
                "consolidated_error": None,
                "resolved_count": len(resolved),
                "expected_count": len(
                    expected_records
                ),
                "missing_count": len(missing),
                "individual_error_champions": len(
                    errors_by_champion
                ),
            }
        ],
        "individual_errors": errors_by_champion,
        "no_unverified_latest_fallback": True,
        "provenance_note": (
            "Attack Speed Ratio is read from per-champion "
            "BaseStats.json files extracted from Riot game "
            "files and pinned to the immutable Git commit "
            "named LIVE 26.16 (#17)."
        ),
        "source_repository": DATAMINE_REPOSITORY,
        "source_commit": DATAMINE_COMMIT,
        "source_riot_patch_label": (
            TARGET_RIOT_PATCH_LABEL
        ),
    }
