import html
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import requests

from database.database import DB_PATH
from riot.data_dragon import DDRAGON_BASE_URL, get_ddragon_versions


RUNE_KNOWLEDGE_VERSION = "rune_knowledge_phase2c1_v1"
DEFAULT_LOCALE = "fr_FR"
UNKNOWN = "UNKNOWN"
NOT_EXPOSED = "NOT_EXPOSED"
RUNE_FORMULA_INCOMPLETE = "RUNE_FORMULA_INCOMPLETE"
UNPARSED_RUNE_TEXT = "UNPARSED_RUNE_TEXT"
PARTIALLY_STRUCTURED_RUNE_TEXT = "PARTIALLY_STRUCTURED_RUNE_TEXT"
SEMANTIC_PARSER_SUPPORTED = "SUPPORTED"
SEMANTIC_PARSER_UNSUPPORTED_LOCALE = "UNSUPPORTED_LOCALE"
SUPPORTED_SEMANTIC_LOCALES = {"fr_FR"}

MAGICAL_FOOTWEAR_PERK_ID = 8304
SLIGHTLY_MAGICAL_BOOTS_ITEM_ID = 2422
STAT_PERK_SLOTS = ("offense", "flex", "defense")

OUTGOING_DAMAGE_ACTION_PHRASES = (
    "inflige",
    "infligent",
    "infligez",
    "infliger",
    "blesse",
    "blessent",
    "fait perdre",
    "font perdre",
)

DEFENSIVE_DAMAGE_CONTEXT_PHRASES = (
    "degats subis",
    "degats qu'il subit",
    "degats qu'elle subit",
    "degats qu'ils subissent",
    "degats qu'elles subissent",
    "reduit les degats",
    "reduisent les degats",
    "reduction des degats",
    "subit moins de degats",
    "subissent moins de degats",
    "absorbe les degats",
    "absorbe des degats",
)

SHIELD_GRANT_OR_USE_PHRASES = (
    "gagne un bouclier",
    "gagnez un bouclier",
    "obtient un bouclier",
    "obtenez un bouclier",
    "octroie un bouclier",
    "confere un bouclier",
    "cree un bouclier",
    "applique un bouclier",
    "bouclier qui absorbe",
    "bouclier absorbe",
    "bouclier protege",
)

CONDITION_TRIGGERS = (
    "si ",
    "quand ",
    "lorsque ",
    "apres ",
    "apres avoir",
    "pendant ",
    "tant que ",
    "chaque fois",
    "a chaque",
    "au bout de",
    "en combat",
    "hors combat",
    "contre ",
    "en dessous de",
    "au-dessus de",
    "apres un",
    "apres une",
)

SEMANTIC_RULES = (
    ("HEAL", ("soigne", "soignez", "rend des pv", "recuperez des pv")),
    ("MOVE_SPEED", ("vitesse de deplacement",)),
    ("ATTACK_SPEED", ("vitesse d'attaque",)),
    ("ABILITY_HASTE", ("acceleration de competence",)),
    ("COOLDOWN", ("delai de recuperation", "recuperation")),
    ("SLOW", ("ralentit", "ralentissement", "ralentisse")),
    ("STACKING", ("cumul", "cumuls", "charge", "charges")),
    ("ADAPTIVE_FORCE", ("force adaptative",)),
    ("ARMOR", ("armure",)),
    ("MAGIC_RESISTANCE", ("resistance magique",)),
    ("HEALTH", ("points de vie", " pv")),
    ("MANA", (" mana",)),
    ("ENERGY", ("energie",)),
    ("OMNIVAMP", ("omnivampirisme",)),
    ("LIFE_STEAL", ("vol de vie",)),
    ("TENACITY", ("tenacite",)),
)

REPRESENTATIVE_RUNE_IDS = (
    MAGICAL_FOOTWEAR_PERK_ID,
    8112,
    8128,
    8005,
    8437,
    8369,
    8214,
    8230,
)


def _normalize_text(value):
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFKD", str(value))
    normalized = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return normalized.lower()


def _collapse_spaces(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _format_counts(counts, limit=None):
    if not counts:
        return "none"
    items = list(counts.items())
    if not isinstance(counts, Counter):
        items = sorted(items, key=lambda item: (-item[1], str(item[0])))
    if limit is not None:
        items = items[:limit]
    return ", ".join(f"{key}={value}" for key, value in items)


def clean_description(raw_description):
    text = str(raw_description or "")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\xa0", " ")
    lines = [_collapse_spaces(line) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _semantic_parser_status(locale):
    if locale in SUPPORTED_SEMANTIC_LOCALES:
        return SEMANTIC_PARSER_SUPPORTED
    return SEMANTIC_PARSER_UNSUPPORTED_LOCALE


def _contains_any(normalized_text, phrases):
    return any(phrase in normalized_text for phrase in phrases)


def _numeric_value(raw_number):
    value = float(str(raw_number).replace(",", "."))
    if value.is_integer():
        return int(value)
    return value


def _unit_from_text(raw_unit):
    normalized = _normalize_text(raw_unit).strip()
    if not normalized:
        return UNKNOWN
    if "%" in normalized:
        return "percent"
    if normalized in {"sec", "secs", "seconde", "secondes", "s"}:
        return "seconds"
    if normalized in {"min", "mins", "minute", "minutes"}:
        return "minutes"
    if normalized.startswith("pt"):
        return "points"
    if normalized in {"po", "gold"}:
        return "gold"
    return UNKNOWN


def _context(text, start, end, size=50):
    return _collapse_spaces(text[max(0, start - size):end + size])


def extract_numeric_fragments(text, source_field, ddragon_version):
    fragments = []
    occupied_spans = []
    text = str(text or "")

    placeholder_pattern = re.compile(r"\{\{\s*(?P<key>[^{}]+?)\s*\}\}")
    for match in placeholder_pattern.finditer(text):
        occupied_spans.append(match.span())
        fragments.append(
            {
                "source": "DDRAGON_RUNE_DESCRIPTION",
                "source_field": source_field,
                "fragment_type": "DDRAGON_PLACEHOLDER",
                "raw_fragment": match.group(0),
                "placeholder_key": match.group("key").strip(),
                "value": None,
                "unit": UNKNOWN,
                "formula_status": RUNE_FORMULA_INCOMPLETE,
                "evidence_text": _context(text, match.start(), match.end()),
                "ddragon_version": ddragon_version,
            }
        )

    range_pattern = re.compile(
        r"(?P<start>[+-]?\d+(?:[,.]\d+)?)\s*[-–]\s*"
        r"(?P<end>[+-]?\d+(?:[,.]\d+)?)"
        r"(?P<unit>\s*(?:%|sec(?:onde)?s?|min(?:ute)?s?|pts?|po))?",
        flags=re.IGNORECASE,
    )
    for match in range_pattern.finditer(text):
        if _span_overlaps(match.span(), occupied_spans):
            continue
        occupied_spans.append(match.span())
        fragments.append(
            {
                "source": "DDRAGON_RUNE_DESCRIPTION",
                "source_field": source_field,
                "fragment_type": "NUMERIC_RANGE",
                "raw_fragment": match.group(0),
                "values": [
                    _numeric_value(match.group("start")),
                    _numeric_value(match.group("end")),
                ],
                "unit": _unit_from_text(match.group("unit") or ""),
                "formula_status": RUNE_FORMULA_INCOMPLETE,
                "evidence_text": _context(text, match.start(), match.end()),
                "ddragon_version": ddragon_version,
            }
        )

    number_pattern = re.compile(
        r"(?<![\w{])(?P<number>[+-]?\d+(?:[,.]\d+)?)"
        r"(?P<unit>\s*(?:%|sec(?:onde)?s?|min(?:ute)?s?|pts?|po))?",
        flags=re.IGNORECASE,
    )
    for match in number_pattern.finditer(text):
        if _span_overlaps(match.span(), occupied_spans):
            continue
        occupied_spans.append(match.span())
        fragments.append(
            {
                "source": "DDRAGON_RUNE_DESCRIPTION",
                "source_field": source_field,
                "fragment_type": "NUMERIC_LITERAL",
                "raw_fragment": match.group(0),
                "value": _numeric_value(match.group("number")),
                "unit": _unit_from_text(match.group("unit") or ""),
                "formula_status": RUNE_FORMULA_INCOMPLETE,
                "evidence_text": _context(text, match.start(), match.end()),
                "ddragon_version": ddragon_version,
            }
        )

    return fragments


def _span_overlaps(span, occupied_spans):
    start, end = span
    return any(start < other_end and end > other_start for other_start, other_end in occupied_spans)


def _split_fragments(text):
    text = str(text or "")
    pieces = re.split(r"(?:\n+|;|(?<=[.!?])\s+)", text)
    fragments = []
    for piece in pieces:
        for clause in re.split(
            r"\s+(?:et|puis|mais|ainsi que|tout en)\s+",
            piece,
            flags=re.IGNORECASE,
        ):
            cleaned = _collapse_spaces(clause)
            if cleaned:
                fragments.append(cleaned)
    return fragments


def _is_outgoing_damage(normalized_text):
    return (
        _contains_any(normalized_text, OUTGOING_DAMAGE_ACTION_PHRASES)
        and "degat" in normalized_text
        and not _contains_any(normalized_text, DEFENSIVE_DAMAGE_CONTEXT_PHRASES)
    )


def _has_gold_context(normalized_text):
    return (
        "piece d'or" in normalized_text
        or "pieces d'or" in normalized_text
        or re.search(r"(^|[^a-z0-9])po($|[^a-z0-9])", normalized_text) is not None
        or re.search(r"(^|[^a-z0-9])gold($|[^a-z0-9])", normalized_text) is not None
    )


def _condition_records(text, source_field, ddragon_version):
    records = []
    for fragment in _split_fragments(text):
        normalized = _normalize_text(fragment)
        matched = [
            trigger for trigger in CONDITION_TRIGGERS if trigger in normalized
        ]
        if not matched:
            continue
        records.append(
            {
                "source": "DDRAGON_RUNE_DESCRIPTION",
                "source_field": source_field,
                "condition_text": fragment,
                "matched_triggers": matched,
                "condition_status": "CONDITION_TEXT_STRUCTURED",
                "execution_status": "NOT_EXECUTED",
                "ddragon_version": ddragon_version,
            }
        )
    return records


def _semantic_effects_for_fragment(fragment, source_field, ddragon_version):
    effects = []
    normalized = _normalize_text(fragment)

    if _is_outgoing_damage(normalized):
        if "degats adaptatifs" in normalized:
            effect_type = "ADAPTIVE_DAMAGE"
        elif "degats bruts" in normalized:
            effect_type = "TRUE_DAMAGE"
        elif "degats physiques" in normalized:
            effect_type = "PHYSICAL_DAMAGE"
        elif "degats magiques" in normalized:
            effect_type = "MAGIC_DAMAGE"
        else:
            effect_type = "DAMAGE_TYPE_UNRESOLVED"
        effects.append(
            {
                "effect_type": effect_type,
                "source": "DDRAGON_RUNE_DESCRIPTION",
                "source_field": source_field,
                "confidence": "DESCRIPTION_EXPLICIT",
                "evidence_text": fragment,
                "ddragon_version": ddragon_version,
            }
        )

    if _contains_any(normalized, DEFENSIVE_DAMAGE_CONTEXT_PHRASES):
        effects.append(
            {
                "effect_type": "DAMAGE_REDUCTION",
                "source": "DDRAGON_RUNE_DESCRIPTION",
                "source_field": source_field,
                "confidence": "DESCRIPTION_EXPLICIT",
                "evidence_text": fragment,
                "ddragon_version": ddragon_version,
            }
        )

    if _contains_any(normalized, SHIELD_GRANT_OR_USE_PHRASES):
        effects.append(
            {
                "effect_type": "SHIELD",
                "source": "DDRAGON_RUNE_DESCRIPTION",
                "source_field": source_field,
                "confidence": "DESCRIPTION_EXPLICIT",
                "evidence_text": fragment,
                "ddragon_version": ddragon_version,
            }
        )

    if "revele" in normalized or "revelez" in normalized:
        effects.append(
            {
                "effect_type": "REVEAL",
                "source": "DDRAGON_RUNE_DESCRIPTION",
                "source_field": source_field,
                "confidence": "DESCRIPTION_EXPLICIT",
                "evidence_text": fragment,
                "ddragon_version": ddragon_version,
            }
        )

    if _has_gold_context(normalized):
        effects.append(
            {
                "effect_type": "GOLD",
                "source": "DDRAGON_RUNE_DESCRIPTION",
                "source_field": source_field,
                "confidence": "DESCRIPTION_EXPLICIT",
                "evidence_text": fragment,
                "ddragon_version": ddragon_version,
            }
        )

    for effect_type, phrases in SEMANTIC_RULES:
        if _contains_any(normalized, phrases):
            effects.append(
                {
                    "effect_type": effect_type,
                    "source": "DDRAGON_RUNE_DESCRIPTION",
                    "source_field": source_field,
                    "confidence": "DESCRIPTION_EXPLICIT",
                    "evidence_text": fragment,
                    "ddragon_version": ddragon_version,
                }
            )

    deduped = []
    seen = set()
    for effect in effects:
        key = (effect["effect_type"], effect["evidence_text"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(effect)
    return deduped


def extract_semantic_effects(text, source_field, ddragon_version, locale=DEFAULT_LOCALE):
    if _semantic_parser_status(locale) != SEMANTIC_PARSER_SUPPORTED:
        return [], [
            {
                "kind": UNPARSED_RUNE_TEXT,
                "source_field": source_field,
                "text": text,
                "unparsed_fragments": _split_fragments(text),
                "reason": "SEMANTIC_PARSER_UNSUPPORTED_LOCALE",
                "ddragon_version": ddragon_version,
            }
        ]

    effects = []
    unparsed_fragments = []
    for fragment in _split_fragments(text):
        fragment_effects = _semantic_effects_for_fragment(
            fragment,
            source_field,
            ddragon_version,
        )
        if fragment_effects:
            effects.extend(fragment_effects)
        else:
            unparsed_fragments.append(fragment)

    unparsed_records = []
    if unparsed_fragments and len(unparsed_fragments) < len(_split_fragments(text)):
        unparsed_records.append(
            {
                "kind": PARTIALLY_STRUCTURED_RUNE_TEXT,
                "source_field": source_field,
                "text": text,
                "unparsed_fragments": unparsed_fragments,
                "matched_effects": [effect["effect_type"] for effect in effects],
                "ddragon_version": ddragon_version,
            }
        )
    elif unparsed_fragments and not effects:
        unparsed_records.append(
            {
                "kind": UNPARSED_RUNE_TEXT,
                "source_field": source_field,
                "text": text,
                "unparsed_fragments": unparsed_fragments,
                "ddragon_version": ddragon_version,
            }
        )

    return effects, unparsed_records


def _resolve_version(requested_game_version=None, versions=None):
    versions = list(versions if versions is not None else get_ddragon_versions())
    if not versions:
        return {
            "requested_game_version": requested_game_version,
            "resolved_ddragon_version": None,
            "resolution_status": "NO_VERSIONS_AVAILABLE",
            "fallback_used": True,
        }

    latest = versions[0]
    if not requested_game_version:
        return {
            "requested_game_version": None,
            "resolved_ddragon_version": latest,
            "resolution_status": "LATEST",
            "fallback_used": False,
        }

    requested = str(requested_game_version)
    if requested in versions:
        return {
            "requested_game_version": requested,
            "resolved_ddragon_version": requested,
            "resolution_status": "EXACT_VERSION",
            "fallback_used": False,
        }

    parts = requested.split(".")
    if len(parts) >= 2:
        patch_prefix = f"{parts[0]}.{parts[1]}."
        for version in versions:
            if version.startswith(patch_prefix):
                return {
                    "requested_game_version": requested,
                    "resolved_ddragon_version": version,
                    "resolution_status": "EXACT_PATCH",
                    "fallback_used": False,
                }

    return {
        "requested_game_version": requested,
        "resolved_ddragon_version": latest,
        "resolution_status": "FALLBACK_LATEST",
        "fallback_used": True,
    }


def _load_raw_runes(ddragon_version, locale):
    url = (
        f"{DDRAGON_BASE_URL}/cdn/{ddragon_version}/data/"
        f"{locale}/runesReforged.json"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def _schema_summary(raw_runes):
    style_keys = Counter()
    slot_keys = Counter()
    rune_keys = Counter()
    for style in raw_runes or []:
        style_keys.update(style.keys())
        for slot in style.get("slots", []) or []:
            slot_keys.update(slot.keys())
            for rune in slot.get("runes", []) or []:
                rune_keys.update(rune.keys())
    return {
        "top_level_type": type(raw_runes).__name__,
        "style_keys": sorted(style_keys),
        "slot_keys": sorted(slot_keys),
        "rune_keys": sorted(rune_keys),
    }


def _description_record(raw_value, source_field, ddragon_version, locale):
    clean_text = clean_description(raw_value)
    numeric_fragments = extract_numeric_fragments(
        clean_text,
        source_field,
        ddragon_version,
    )
    conditions = _condition_records(clean_text, source_field, ddragon_version)
    effects, unparsed = extract_semantic_effects(
        clean_text,
        source_field,
        ddragon_version,
        locale,
    )
    return {
        "source_field": source_field,
        "raw_text": raw_value or "",
        "clean_text": clean_text,
        "numeric_fragments": numeric_fragments,
        "conditions": conditions,
        "effects": effects,
        "unparsed_text": unparsed,
    }


def _parse_completeness(short_record, long_record):
    fields = [record for record in (short_record, long_record) if record["clean_text"]]
    if not fields:
        return "COMPLETELY_UNPARSED"

    any_evidence = False
    any_unparsed = False
    for record in fields:
        has_evidence = (
            bool(record["effects"])
            or bool(record["conditions"])
            or bool(record["numeric_fragments"])
        )
        any_evidence = any_evidence or has_evidence
        any_unparsed = any_unparsed or bool(record["unparsed_text"])

    if any_evidence and not any_unparsed:
        return "FULLY_STRUCTURED"
    if any_evidence:
        return "PARTIALLY_STRUCTURED"
    return "COMPLETELY_UNPARSED"


def _build_rune_record(style, slot_index, rune, version_info, locale):
    ddragon_version = version_info["resolved_ddragon_version"]
    short_record = _description_record(
        rune.get("shortDesc"),
        "shortDesc",
        ddragon_version,
        locale,
    )
    long_record = _description_record(
        rune.get("longDesc"),
        "longDesc",
        ddragon_version,
        locale,
    )
    all_numeric = short_record["numeric_fragments"] + long_record["numeric_fragments"]
    all_conditions = short_record["conditions"] + long_record["conditions"]
    all_effects = short_record["effects"] + long_record["effects"]
    all_unparsed = short_record["unparsed_text"] + long_record["unparsed_text"]

    return {
        "rune_knowledge_version": RUNE_KNOWLEDGE_VERSION,
        "rune_id": int(rune["id"]),
        "key": rune.get("key") or UNKNOWN,
        "name": rune.get("name") or UNKNOWN,
        "icon": rune.get("icon") or "",
        "style_id": int(style["id"]),
        "style_key": style.get("key") or UNKNOWN,
        "style_name": style.get("name") or UNKNOWN,
        "slot_index": slot_index,
        "locale": locale,
        "ddragon_version": ddragon_version,
        "raw_shortDesc": rune.get("shortDesc") or "",
        "raw_longDesc": rune.get("longDesc") or "",
        "clean_shortDesc": short_record["clean_text"],
        "clean_longDesc": long_record["clean_text"],
        "numeric_fragments": all_numeric,
        "conditions": all_conditions,
        "effects": all_effects,
        "unparsed_rune_text": all_unparsed,
        "formula": {
            "status": RUNE_FORMULA_INCOMPLETE,
            "reason": (
                "Data Dragon rune descriptions are factual text, not a complete "
                "executable formula contract."
            ),
            "numeric_fragments": all_numeric,
            "ddragon_version": ddragon_version,
        },
        "semantic_parser": {
            "status": _semantic_parser_status(locale),
            "supported_locales": sorted(SUPPORTED_SEMANTIC_LOCALES),
            "locale": locale,
        },
        "structure_completeness": _parse_completeness(short_record, long_record),
        "raw_rune_json": dict(rune),
    }


def build_rune_knowledge_catalog(
    requested_game_version=None,
    locale=DEFAULT_LOCALE,
    raw_runes=None,
    versions=None,
):
    version_info = _resolve_version(requested_game_version, versions=versions)
    ddragon_version = version_info["resolved_ddragon_version"]
    if raw_runes is None:
        raw_runes = _load_raw_runes(ddragon_version, locale)

    records = {}
    styles = []
    duplicate_rune_ids = []
    invalid_rune_records = []

    for style in raw_runes or []:
        style_id = style.get("id")
        style_record = {
            "style_id": style_id,
            "key": style.get("key") or UNKNOWN,
            "name": style.get("name") or UNKNOWN,
            "icon": style.get("icon") or "",
            "slots": [],
            "raw_style_json": dict(style),
        }
        for slot_index, slot in enumerate(style.get("slots", []) or []):
            slot_record = {
                "slot_index": slot_index,
                "rune_ids": [],
                "raw_slot_json": dict(slot),
            }
            for rune in slot.get("runes", []) or []:
                try:
                    rune_id = int(rune["id"])
                    record = _build_rune_record(
                        style,
                        slot_index,
                        rune,
                        version_info,
                        locale,
                    )
                except (KeyError, TypeError, ValueError):
                    invalid_rune_records.append(
                        {
                            "style_id": style_id,
                            "slot_index": slot_index,
                            "raw_rune_json": dict(rune or {}),
                        }
                    )
                    continue
                if rune_id in records:
                    duplicate_rune_ids.append(rune_id)
                records[rune_id] = record
                slot_record["rune_ids"].append(rune_id)
            style_record["slots"].append(slot_record)
        styles.append(style_record)

    summary = summarize_rune_knowledge(
        raw_runes,
        records,
        styles,
        duplicate_rune_ids,
        invalid_rune_records,
    )
    return {
        "rune_knowledge_version": RUNE_KNOWLEDGE_VERSION,
        "requested_game_version": version_info["requested_game_version"],
        "resolved_ddragon_version": ddragon_version,
        "version_resolution_status": version_info["resolution_status"],
        "version_fallback_used": version_info["fallback_used"],
        "locale": locale,
        "schema_summary": _schema_summary(raw_runes),
        "styles": styles,
        "records": records,
        "summary": summary,
    }


def summarize_rune_knowledge(
    raw_runes,
    records,
    styles,
    duplicate_rune_ids,
    invalid_rune_records,
):
    effect_counts = Counter()
    condition_trigger_counts = Counter()
    numeric_fragment_counts = Counter()
    formula_status_counts = Counter()
    parser_status_counts = Counter()
    structure_counts = Counter()
    unparsed_kind_counts = Counter()
    runes_by_style = Counter()
    runes_by_slot = Counter()

    for style in styles:
        style_key = style["key"]
        for slot in style["slots"]:
            count = len(slot["rune_ids"])
            runes_by_style[style_key] += count
            runes_by_slot[f"{style_key}:{slot['slot_index']}"] += count

    for record in records.values():
        effect_counts.update(effect["effect_type"] for effect in record["effects"])
        formula_status_counts[record["formula"]["status"]] += 1
        parser_status_counts[record["semantic_parser"]["status"]] += 1
        structure_counts[record["structure_completeness"]] += 1
        numeric_fragment_counts.update(
            fragment["fragment_type"] for fragment in record["numeric_fragments"]
        )
        for condition in record["conditions"]:
            condition_trigger_counts.update(condition["matched_triggers"])
        unparsed_kind_counts.update(
            record["kind"] for record in record["unparsed_rune_text"]
        )

    return {
        "raw_style_records": len(raw_runes or []),
        "total_styles": len(styles),
        "total_slots": sum(len(style["slots"]) for style in styles),
        "total_runes": len(records),
        "duplicate_rune_ids": sorted(set(duplicate_rune_ids)),
        "invalid_rune_records": invalid_rune_records,
        "runes_by_style": dict(runes_by_style),
        "runes_by_slot": dict(runes_by_slot),
        "semantic_effect_counts": dict(effect_counts),
        "condition_trigger_counts": dict(condition_trigger_counts),
        "numeric_fragment_counts": dict(numeric_fragment_counts),
        "formula_status_counts": dict(formula_status_counts),
        "semantic_parser_status_counts": dict(parser_status_counts),
        "structure_completeness_counts": dict(structure_counts),
        "unparsed_kind_counts": dict(unparsed_kind_counts),
        "magical_footwear_static_record": _magical_footwear_static_summary(records),
        "stat_perks_in_static_catalog": [
            rune_id for rune_id in (5001, 5002, 5003, 5005, 5007, 5008, 5010, 5011, 5013)
            if rune_id in records
        ],
    }


def _magical_footwear_static_summary(records):
    record = records.get(MAGICAL_FOOTWEAR_PERK_ID)
    if not record:
        return {
            "catalog_status": "MISSING_FROM_DDRAGON_RUNE_CATALOG",
            "rune_id": MAGICAL_FOOTWEAR_PERK_ID,
        }
    return {
        "catalog_status": "FOUND_IN_DDRAGON_RUNE_CATALOG",
        "rune_id": record["rune_id"],
        "key": record["key"],
        "name": record["name"],
        "style_id": record["style_id"],
        "style_key": record["style_key"],
        "slot_index": record["slot_index"],
    }


def _load_match_rows(db_path=DB_PATH):
    db_path = Path(db_path)
    if not db_path.exists():
        return []

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT match_id, game_creation, game_version, raw_json
        FROM matches
        WHERE raw_json IS NOT NULL
        ORDER BY game_creation, match_id
        """
    )
    rows = cursor.fetchall()
    connection.close()
    return [
        {
            "match_id": row[0],
            "game_creation": row[1],
            "game_version": row[2],
            "raw_json": row[3],
        }
        for row in rows
    ]


def _example(examples, value, limit=5):
    if len(examples) < limit:
        examples.append(value)


def _parse_raw_json(raw_json):
    if isinstance(raw_json, dict):
        return raw_json
    try:
        return json.loads(raw_json)
    except (TypeError, json.JSONDecodeError):
        return {}


def build_observed_rune_audit(catalog, match_rows=None, db_path=DB_PATH):
    match_rows = match_rows if match_rows is not None else _load_match_rows(db_path)
    records = catalog["records"]
    style_ids = {style["style_id"] for style in catalog["styles"]}

    rune_counts = Counter()
    style_counts = Counter()
    link_status_counts = Counter()
    style_link_status_counts = Counter()
    stat_perk_counts_by_slot = {slot: Counter() for slot in STAT_PERK_SLOTS}
    stat_perk_status_counts = Counter()
    stat_perk_examples = defaultdict(list)
    unknown_perk_examples = []
    unknown_style_examples = []
    var_observations = Counter()
    nonzero_var_observations = Counter()
    var_value_examples = defaultdict(list)
    magical_examples = []
    champion_counts = Counter()
    game_version_counts = Counter()
    malformed_matches = []

    participant_count = 0
    participants_with_perks = 0
    rune_selection_count = 0
    matches_with_perks = set()
    matches_with_magical_footwear = set()

    for match_row in match_rows:
        raw_match = _parse_raw_json(match_row.get("raw_json"))
        info = raw_match.get("info", {})
        participants = info.get("participants") or []
        if not participants:
            _example(
                malformed_matches,
                {
                    "match_id": match_row.get("match_id"),
                    "reason": "NO_PARTICIPANTS_OR_INVALID_RAW_JSON",
                },
            )
            continue
        game_version = match_row.get("game_version") or info.get("gameVersion")
        game_version_counts[game_version or UNKNOWN] += 1

        for participant in participants:
            participant_count += 1
            champion = participant.get("championName") or UNKNOWN
            champion_counts[champion] += 1
            perks = participant.get("perks") or {}
            if not perks:
                continue
            participants_with_perks += 1
            matches_with_perks.add(match_row.get("match_id"))

            for style in perks.get("styles", []) or []:
                style_id = style.get("style")
                style_counts[style_id] += 1
                if style_id in style_ids:
                    style_link_status_counts["LINKED_RUNE_STYLE"] += 1
                else:
                    style_link_status_counts["UNKNOWN_RUNE_STYLE_ID"] += 1
                    _example(
                        unknown_style_examples,
                        {
                            "match_id": match_row.get("match_id"),
                            "participant_id": participant.get("participantId"),
                            "champion": champion,
                            "style_id": style_id,
                        },
                    )

                for selection in style.get("selections", []) or []:
                    perk_id = selection.get("perk")
                    rune_selection_count += 1
                    rune_counts[perk_id] += 1
                    if perk_id in records:
                        link_status_counts["LINKED_RUNE_CATALOG"] += 1
                    else:
                        link_status_counts["UNKNOWN_PERK_ID"] += 1
                        _example(
                            unknown_perk_examples,
                            {
                                "match_id": match_row.get("match_id"),
                                "participant_id": participant.get("participantId"),
                                "champion": champion,
                                "perk_id": perk_id,
                                "style_id": style_id,
                            },
                        )

                    for var_key in ("var1", "var2", "var3"):
                        value = selection.get(var_key)
                        var_observations[var_key] += 1
                        if value not in (None, 0):
                            nonzero_var_observations[var_key] += 1
                            _example(
                                var_value_examples[(perk_id, var_key)],
                                {
                                    "match_id": match_row.get("match_id"),
                                    "participant_id": participant.get("participantId"),
                                    "champion": champion,
                                    "perk_id": perk_id,
                                    var_key: value,
                                    "meaning_status": "RIOT_OBSERVED_UNINTERPRETED",
                                },
                            )

                    if perk_id == MAGICAL_FOOTWEAR_PERK_ID:
                        matches_with_magical_footwear.add(match_row.get("match_id"))
                        _example(
                            magical_examples,
                            {
                                "match_id": match_row.get("match_id"),
                                "game_version": game_version,
                                "participant_id": participant.get("participantId"),
                                "champion": champion,
                                "perk_selection": {
                                    "perk": perk_id,
                                    "var1": selection.get("var1"),
                                    "var2": selection.get("var2"),
                                    "var3": selection.get("var3"),
                                    "meaning_status": "RIOT_OBSERVED_UNINTERPRETED",
                                },
                            },
                        )

            stat_perks = perks.get("statPerks") or {}
            for slot in STAT_PERK_SLOTS:
                stat_perk_id = stat_perks.get(slot)
                if stat_perk_id is None:
                    stat_perk_status_counts[f"{slot}:MISSING"] += 1
                    continue
                stat_perk_counts_by_slot[slot][stat_perk_id] += 1
                if stat_perk_id in records:
                    status = "LINKED_STATIC_RUNE_UNEXPECTED"
                else:
                    status = "STAT_PERK_NOT_EXPOSED_BY_DDRAGON_RUNE_CATALOG"
                stat_perk_status_counts[f"{slot}:{status}"] += 1
                _example(
                    stat_perk_examples[(slot, stat_perk_id)],
                    {
                        "match_id": match_row.get("match_id"),
                        "participant_id": participant.get("participantId"),
                        "champion": champion,
                        "slot": slot,
                        "stat_perk_id": stat_perk_id,
                        "meaning_status": NOT_EXPOSED,
                        "value_status": NOT_EXPOSED,
                    },
                )

    known_rune_counts = Counter(
        {
            records[perk_id]["name"]: count
            for perk_id, count in rune_counts.items()
            if perk_id in records
        }
    )
    unknown_rune_counts = Counter(
        {
            perk_id: count
            for perk_id, count in rune_counts.items()
            if perk_id not in records
        }
    )

    return {
        "observed_match_count": len(match_rows),
        "participant_count": participant_count,
        "participants_with_perks": participants_with_perks,
        "matches_with_perks": len(matches_with_perks),
        "rune_selection_count": rune_selection_count,
        "link_status_counts": dict(link_status_counts),
        "style_link_status_counts": dict(style_link_status_counts),
        "observed_rune_id_counts": dict(rune_counts),
        "known_rune_name_counts": dict(known_rune_counts.most_common()),
        "unknown_perk_id_counts": dict(unknown_rune_counts),
        "unknown_perk_examples": unknown_perk_examples,
        "observed_style_counts": dict(style_counts),
        "unknown_style_examples": unknown_style_examples,
        "stat_perk_counts_by_slot": {
            slot: dict(counts)
            for slot, counts in stat_perk_counts_by_slot.items()
        },
        "stat_perk_status_counts": dict(stat_perk_status_counts),
        "stat_perk_examples": {
            f"{slot}:{stat_perk_id}": examples
            for (slot, stat_perk_id), examples in stat_perk_examples.items()
        },
        "var_observation_counts": dict(var_observations),
        "nonzero_var_observation_counts": dict(nonzero_var_observations),
        "var_value_examples": {
            f"{perk_id}:{var_key}": examples
            for (perk_id, var_key), examples in var_value_examples.items()
        },
        "var_meaning_status": "RIOT_OBSERVED_UNINTERPRETED",
        "game_version_counts": dict(game_version_counts),
        "champion_counts": dict(champion_counts.most_common()),
        "malformed_matches": malformed_matches,
        "magical_footwear": {
            "perk_id": MAGICAL_FOOTWEAR_PERK_ID,
            "participants": rune_counts.get(MAGICAL_FOOTWEAR_PERK_ID, 0),
            "matches": len(matches_with_magical_footwear),
            "catalog_status": catalog["summary"]["magical_footwear_static_record"][
                "catalog_status"
            ],
            "examples": magical_examples,
        },
        "magical_footwear_itemization_contract": (
            verify_magical_footwear_itemization_contract()
        ),
    }


def verify_magical_footwear_itemization_contract(itemization_path=None):
    if itemization_path is None:
        itemization_path = (
            Path(__file__).resolve().parents[1]
            / "analysis"
            / "itemization_analyzer.py"
        )
    itemization_path = Path(itemization_path)
    if not itemization_path.exists():
        return {
            "status": "MISSING_ITEMIZATION_ANALYZER_SOURCE",
            "itemization_path": str(itemization_path),
        }

    text = itemization_path.read_text(encoding="utf-8")
    checks = {
        "magical_footwear_perk_id_8304": (
            "MAGICAL_FOOTWEAR_PERK_ID = 8304" in text
        ),
        "slightly_magical_boots_item_id_2422": (
            "SLIGHTLY_MAGICAL_BOOTS_ITEM_ID = 2422" in text
        ),
        "rune_grant_source": '"source": "RUNE_GRANT"' in text,
        "derived_inferred_timing": "DERIVED_INFERRED" in text,
    }
    return {
        "status": "PASS" if all(checks.values()) else "REVIEW_REQUIRED",
        "itemization_path": str(itemization_path),
        "checks": checks,
        "rule": (
            "Magical Footwear is compatible when rune 8304 is present and "
            "item 2422 is treated as RUNE_GRANT with DERIVED_INFERRED timing, "
            "not as an observed Riot purchase."
        ),
    }


def render_rune_record_diagnostic(record):
    effect_counts = Counter(effect["effect_type"] for effect in record["effects"])
    condition_count = len(record["conditions"])
    numeric_counts = Counter(
        fragment["fragment_type"] for fragment in record["numeric_fragments"]
    )
    lines = [
        f"Rune {record['rune_id']} - {record['name']} ({record['key']})",
        (
            "style/slot: "
            f"{record['style_name']} ({record['style_id']}), slot {record['slot_index']}"
        ),
        f"formula: {record['formula']['status']}",
        f"structure completeness: {record['structure_completeness']}",
        f"effects: {_format_counts(effect_counts)}",
        f"conditions: {condition_count}",
        f"numeric fragments: {_format_counts(numeric_counts)}",
    ]
    if record["conditions"]:
        lines.append(
            "condition sample: "
            f"{record['conditions'][0]['condition_text'][:180]}"
        )
    if record["numeric_fragments"]:
        lines.append(
            "numeric sample: "
            f"{record['numeric_fragments'][0]['raw_fragment']} "
            f"from {record['numeric_fragments'][0]['source_field']}"
        )
    if record["unparsed_rune_text"]:
        sample = record["unparsed_rune_text"][0]
        fragments = sample.get("unparsed_fragments") or []
        lines.append(
            "unparsed sample: "
            f"{fragments[0][:180] if fragments else sample.get('text', '')[:180]}"
        )
    return "\n".join(lines)


def render_representative_rune_diagnostics(catalog, observed_audit=None):
    lines = [
        "REPRESENTATIVE RUNE DIAGNOSTICS",
        "",
        "These examples are factual parser diagnostics, not rune advice.",
        "",
    ]
    for rune_id in REPRESENTATIVE_RUNE_IDS:
        record = catalog["records"].get(rune_id)
        if not record:
            continue
        lines.append(render_rune_record_diagnostic(record))
        lines.append("")

    if observed_audit:
        lines.extend(
            [
                "Observed statPerks diagnostics:",
                (
                    "stat shard IDs are audited by offense/flex/defense slot "
                    "and are not assigned names or values from memory."
                ),
            ]
        )
        for slot in STAT_PERK_SLOTS:
            counts = Counter(observed_audit["stat_perk_counts_by_slot"].get(slot, {}))
            lines.append(f"- {slot}: {_format_counts(counts)}")
        lines.append("")
        lines.append("Magical Footwear compatibility:")
        contract = observed_audit["magical_footwear_itemization_contract"]
        lines.append(f"- itemization contract status: {contract.get('status')}")
        lines.append(
            "- observed participants with 8304: "
            f"{observed_audit['magical_footwear']['participants']}"
        )
        lines.append(
            "- observed matches with 8304: "
            f"{observed_audit['magical_footwear']['matches']}"
        )
    return "\n".join(lines).rstrip()


def render_rune_knowledge_audit(catalog, observed_audit=None):
    summary = catalog["summary"]
    schema = catalog["schema_summary"]
    lines = [
        "RUNE KNOWLEDGE BASE PHASE 2C1 AUDIT",
        "",
        "Scope: factual, patch-aware Data Dragon rune knowledge plus observed",
        "Riot perk linkage. No executable formulas, damage engine, Burst/TTK,",
        "composition analysis, recommendations, rune scoring, or ML are computed.",
        "",
        f"Rune knowledge version: {catalog['rune_knowledge_version']}",
        f"Requested game version: {catalog['requested_game_version']}",
        f"Resolved Data Dragon version: {catalog['resolved_ddragon_version']}",
        f"Version resolution: {catalog['version_resolution_status']}",
        f"Fallback used: {catalog['version_fallback_used']}",
        f"Locale: {catalog['locale']}",
        "",
        "Observed Data Dragon schema:",
        f"- top-level type: {schema['top_level_type']}",
        f"- style keys: {', '.join(schema['style_keys'])}",
        f"- slot keys: {', '.join(schema['slot_keys'])}",
        f"- rune keys: {', '.join(schema['rune_keys'])}",
        "",
        f"Total rune trees/styles: {summary['total_styles']}",
        f"Total slots: {summary['total_slots']}",
        f"Total rune records: {summary['total_runes']}",
        f"Runes by style: {_format_counts(Counter(summary['runes_by_style']))}",
        f"Runes by slot: {_format_counts(Counter(summary['runes_by_slot']), limit=12)}",
        f"Duplicate rune IDs: {summary['duplicate_rune_ids'] or 'none'}",
        f"Invalid rune records: {len(summary['invalid_rune_records'])}",
        (
            "Formula status counts: "
            f"{_format_counts(Counter(summary['formula_status_counts']))}"
        ),
        (
            "Semantic parser statuses: "
            f"{_format_counts(Counter(summary['semantic_parser_status_counts']))}"
        ),
        (
            "Structure completeness: "
            f"{_format_counts(Counter(summary['structure_completeness_counts']))}"
        ),
        (
            "Semantic effect counts: "
            f"{_format_counts(Counter(summary['semantic_effect_counts']))}"
        ),
        (
            "Condition trigger counts: "
            f"{_format_counts(Counter(summary['condition_trigger_counts']))}"
        ),
        (
            "Numeric fragment counts: "
            f"{_format_counts(Counter(summary['numeric_fragment_counts']))}"
        ),
        (
            "Unparsed/partial text counts: "
            f"{_format_counts(Counter(summary['unparsed_kind_counts']))}"
        ),
        (
            "Static statPerks present in runesReforged: "
            f"{summary['stat_perks_in_static_catalog'] or 'none'}"
        ),
        (
            "Magical Footwear static record: "
            f"{summary['magical_footwear_static_record']}"
        ),
    ]

    if observed_audit:
        lines.extend(
            [
                "",
                "Observed historical rune audit:",
                f"Matches with raw JSON audited: {observed_audit['observed_match_count']}",
                f"Participants audited: {observed_audit['participant_count']}",
                (
                    "Participants with perks payload: "
                    f"{observed_audit['participants_with_perks']}"
                ),
                f"Matches with perks payload: {observed_audit['matches_with_perks']}",
                f"Rune selections observed: {observed_audit['rune_selection_count']}",
                (
                    "Rune catalog link statuses: "
                    f"{_format_counts(Counter(observed_audit['link_status_counts']))}"
                ),
                (
                    "Rune style link statuses: "
                    f"{_format_counts(Counter(observed_audit['style_link_status_counts']))}"
                ),
                (
                    "Unknown observed perk IDs: "
                    f"{_format_counts(Counter(observed_audit['unknown_perk_id_counts']))}"
                ),
                (
                    "Top observed runes: "
                    f"{_format_counts(Counter(observed_audit['known_rune_name_counts']), limit=12)}"
                ),
                (
                    "Observed game versions: "
                    f"{_format_counts(Counter(observed_audit['game_version_counts']), limit=8)}"
                ),
                (
                    "var1/var2/var3 observation counts: "
                    f"{_format_counts(Counter(observed_audit['var_observation_counts']))}"
                ),
                (
                    "non-zero var1/var2/var3 counts: "
                    f"{_format_counts(Counter(observed_audit['nonzero_var_observation_counts']))}"
                ),
                (
                    "var meaning status: "
                    f"{observed_audit['var_meaning_status']}"
                ),
                (
                    "statPerks status counts: "
                    f"{_format_counts(Counter(observed_audit['stat_perk_status_counts']))}"
                ),
            ]
        )
        for slot in STAT_PERK_SLOTS:
            lines.append(
                f"statPerks.{slot}: "
                f"{_format_counts(Counter(observed_audit['stat_perk_counts_by_slot'].get(slot, {})))}"
            )
        lines.extend(
            [
                (
                    "Magical Footwear observed participants: "
                    f"{observed_audit['magical_footwear']['participants']}"
                ),
                (
                    "Magical Footwear observed matches: "
                    f"{observed_audit['magical_footwear']['matches']}"
                ),
                (
                    "Magical Footwear itemization compatibility: "
                    f"{observed_audit['magical_footwear_itemization_contract']['status']}"
                ),
                (
                    "Malformed match samples: "
                    f"{observed_audit['malformed_matches'] or 'none'}"
                ),
            ]
        )

    lines.extend(
        [
            "",
            "Permanent methodology notes for review:",
            "- Data Dragon runesReforged does not expose stat shard meanings here;",
            "  observed statPerks IDs are preserved by slot without invented values.",
            "- Riot var1/var2/var3 are observed match telemetry and are kept",
            "  uninterpreted until a later validated formula layer exists.",
            "- Rune descriptions are parsed only as conservative fr_FR evidence.",
            "- Every rune formula remains RUNE_FORMULA_INCOMPLETE.",
            "- Conditions are structured as text and never executed.",
            "- Magical Footwear 8304 is compatible with frozen itemization v22",
            "  as a RUNE_GRANT for item 2422 with derived/inferred timing only.",
        ]
    )
    return "\n".join(lines)


def main():
    catalog = build_rune_knowledge_catalog()
    observed_audit = build_observed_rune_audit(catalog)
    print(render_rune_knowledge_audit(catalog, observed_audit))
    print()
    print(render_representative_rune_diagnostics(catalog, observed_audit))


if __name__ == "__main__":
    main()
