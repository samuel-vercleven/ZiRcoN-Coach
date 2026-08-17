import html
import re
import unicodedata
from collections import Counter

import requests

from riot.data_dragon import (
    DDRAGON_BASE_URL,
    get_ddragon_versions,
    get_items,
)


ITEM_KNOWLEDGE_VERSION = "item_knowledge_phase2a_v1"
DEFAULT_LOCALE = "fr_FR"
UNKNOWN = "UNKNOWN"
NOT_EXPOSED = "NOT_EXPOSED"
UNPARSED_EFFECT_TEXT = "UNPARSED_EFFECT_TEXT"
SUMMONERS_RIFT_MAP_ID = "11"

STAT_FIELD_MAP = {
    "FlatPhysicalDamageMod": ("attack_damage", "flat"),
    "FlatMagicDamageMod": ("ability_power", "flat"),
    "PercentAttackSpeedMod": ("attack_speed_percent", "fraction"),
    "FlatCritChanceMod": ("critical_strike_chance", "fraction"),
    "FlatArmorPenetrationMod": ("armor_penetration_flat", "flat"),
    "PercentArmorPenetrationMod": (
        "armor_penetration_percent",
        "fraction",
    ),
    "FlatMagicPenetrationMod": ("magic_penetration_flat", "flat"),
    "PercentMagicPenetrationMod": (
        "magic_penetration_percent",
        "fraction",
    ),
    "FlatHPPoolMod": ("health", "flat"),
    "FlatHPRegenMod": ("health_regen", "flat"),
    "FlatArmorMod": ("armor", "flat"),
    "FlatSpellBlockMod": ("magic_resistance", "flat"),
    "FlatMPPoolMod": ("mana", "flat"),
    "FlatMPRegenMod": ("mana_regen", "flat"),
    "PercentLifeStealMod": ("life_steal", "fraction"),
    "PercentSpellVampMod": ("spell_vamp", "fraction"),
    "FlatMovementSpeedMod": ("flat_move_speed", "flat"),
    "PercentMovementSpeedMod": ("percent_move_speed", "fraction"),
}

DESCRIPTION_STAT_PATTERNS = [
    ("attack_damage", "flat", ("degats d'attaque",)),
    ("ability_power", "flat", ("puissance",)),
    ("attack_speed_percent", "percent", ("vitesse d'attaque",)),
    (
        "critical_strike_chance",
        "percent",
        ("chances de coup critique", "chance de coup critique"),
    ),
    ("lethality", "flat", ("letalite",)),
    (
        "armor_penetration_percent",
        "percent",
        ("penetration d'armure",),
    ),
    (
        "magic_penetration_percent",
        "percent",
        ("penetration magique",),
    ),
    ("ability_haste", "flat", ("acceleration de competence",)),
    ("health_regen", "percent", ("regen. de base des pv",)),
    ("health_regen", "percent", ("regeneration de base des pv",)),
    ("health", "flat", (" pv", "points de vie")),
    ("armor", "flat", ("armure",)),
    ("magic_resistance", "flat", ("resistance magique",)),
    ("tenacity", "percent", ("tenacite",)),
    ("slow_resistance", "percent", ("resistance aux ralentissements",)),
    ("mana_regen", "percent", ("regen. de base du mana",)),
    ("mana_regen", "percent", ("regeneration de base du mana",)),
    ("mana", "flat", (" mana",)),
    ("life_steal", "percent", ("vol de vie",)),
    ("omnivamp", "percent", ("omnivampirisme",)),
    ("flat_move_speed", "flat", ("vitesse de deplacement",)),
    ("percent_move_speed", "percent", ("vitesse de deplacement",)),
]

TAG_EFFECT_MAP = {
    "OnHit": "ON_HIT_DAMAGE",
    "Slow": "SLOW",
    "Tenacity": "TENACITY",
    "LifeSteal": "LIFE_STEAL_EFFECT",
    "SpellVamp": "OMNIVAMP_EFFECT",
}

EFFECT_RULES = [
    ("SPELLBLADE", ("lame enchantee",)),
    ("CRITICAL_STRIKE_EFFECT", ("coup critique",)),
    ("LIFELINE_SHIELD", ("lien vital",)),
    ("SPELL_SHIELD", ("bouclier antisorts", "bouclier anti-sorts")),
    ("ACTIVE_SHIELD", ("bouclier",)),
    ("ACTIVE_DAMAGE", ("degats",)),
    ("ACTIVE_MOVEMENT", ("vitesse de deplacement",)),
    ("DASH", ("ruée", "ruee", "dash", "bondissez")),
    (
        "MOVEMENT_SPEED_TRIGGER",
        ("vitesse de deplacement", "vitesse de deplacement bonus"),
    ),
    ("SLOW", ("ralentit", "ralentissement", "ralentisse")),
    (
        "HARD_CC",
        (
            "etourdit",
            "immobilise",
            "projette",
            "silence",
            "provocation",
            "suppression",
        ),
    ),
    ("HEAL", ("soigne", "soignez", "recuperez des pv")),
    ("LIFE_STEAL_EFFECT", ("vol de vie",)),
    ("OMNIVAMP_EFFECT", ("omnivampirisme",)),
    ("DAMAGE_REDUCTION", ("degats sont reduits", "reduction des degats")),
    ("STASIS", ("stase",)),
    ("REVIVE", ("ressuscite", "ressuscitez", "ranimation")),
    ("CLEANSE", ("dissipez", "dissipe")),
    ("TENACITY", ("tenacite",)),
    ("GRIEVOUS_WOUNDS", ("hemorragie",)),
    ("SHIELD_REDUCTION", ("reduit les boucliers", "reduction des boucliers")),
    (
        "PERCENT_CURRENT_HEALTH_DAMAGE",
        ("pourcentage des pv actuels", "pv actuels"),
    ),
    ("PERCENT_MAX_HEALTH_DAMAGE", ("pv max", "pv maximum")),
    ("MISSING_HEALTH_SCALING", ("pv manquants",)),
    ("EXECUTE", ("execute", "execution", "acheve")),
    (
        "ARMOR_REDUCTION",
        ("armure reduite", "reduit son armure", "reduction d'armure"),
    ),
    (
        "MAGIC_RESIST_REDUCTION",
        (
            "resistance magique reduite",
            "reduit sa resistance magique",
            "reduction de resistance magique",
        ),
    ),
    ("ARMOR_PENETRATION", ("penetration d'armure",)),
    ("MAGIC_PENETRATION", ("penetration magique",)),
    ("TRUE_DAMAGE", ("degats bruts",)),
    ("ON_HIT_DAMAGE", ("a l'impact", "à l'impact")),
    ("STACKING_EFFECT", ("cumul", "charges")),
    ("TRANSFORMATION", ("transforme", "transformation", "ameliore")),
    ("QUEST_OR_SPECIAL_MECHANIC", ("quete", "compagnon de la jungle")),
]

REPRESENTATIVE_REQUIREMENTS = [
    "pure_ad_item",
    "pure_ap_item",
    "armor_item",
    "mr_item",
    "attack_speed_item",
    "crit_item",
    "boots",
    "tank_item",
    "lifeline_or_shield_item",
    "grievous_wounds_item",
    "penetration_item",
    "on_hit_item",
    "percent_health_mechanic",
    "active_item",
    "consumable",
    "jungle_starter",
    "trinket",
    "non_purchasable_or_transformed_item",
]


def _normalize_text(value):
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFKD", str(value))
    normalized = "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )
    return normalized.lower()


def _collapse_spaces(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def clean_description(raw_description):
    text = str(raw_description or "")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(stats|mainText|passive|active|rules)>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\xa0", " ")
    lines = [_collapse_spaces(line) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _clean_fragment(raw_fragment):
    return clean_description(raw_fragment)


def parse_description_sections(raw_description):
    raw_description = str(raw_description or "")
    sections = {
        "stats_text": "",
        "sections": [],
        "clean_text": clean_description(raw_description),
    }

    stats_match = re.search(
        r"<stats>(.*?)</stats>",
        raw_description,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if stats_match:
        sections["stats_text"] = _clean_fragment(stats_match.group(1))

    marker_pattern = re.compile(
        r"<(?P<tag>passive|active|rules)>(?P<title>.*?)</(?P=tag)>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    matches = list(marker_pattern.finditer(raw_description))

    for index, match in enumerate(matches):
        next_start = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(raw_description)
        )
        body = raw_description[match.end():next_start]
        tag = match.group("tag").upper()
        title = _clean_fragment(match.group("title"))
        text = _clean_fragment(body)
        if title or text:
            sections["sections"].append(
                {
                    "section_type": tag,
                    "name": title or UNKNOWN,
                    "text": text,
                    "raw": match.group(0) + body,
                }
            )

    return sections


def _parse_numeric_prefix(text):
    match = re.search(r"([+-]?\d+(?:[.,]\d+)?)\s*%?", text)
    if not match:
        return None, False

    raw_number = match.group(1).replace(",", ".")
    value = float(raw_number)
    if value.is_integer():
        value = int(value)
    is_percent = "%" in text[max(0, match.start()):match.end() + 3]
    return value, is_percent


def _description_stat_mapping(line):
    normalized = _normalize_text(line)
    value, has_percent = _parse_numeric_prefix(line)
    if value is None:
        return None

    for canonical, unit_type, phrases in DESCRIPTION_STAT_PATTERNS:
        if not any(phrase in normalized for phrase in phrases):
            continue
        if canonical == "flat_move_speed" and has_percent:
            continue
        if canonical == "percent_move_speed" and not has_percent:
            continue
        if canonical == "armor_penetration_percent" and not has_percent:
            canonical = "armor_penetration_flat"
            unit_type = "flat"
        if canonical == "magic_penetration_percent" and not has_percent:
            canonical = "magic_penetration_flat"
            unit_type = "flat"
        if unit_type == "percent":
            value = value / 100
            unit = "fraction"
        else:
            unit = "flat"
        return canonical, value, unit

    return None


def normalize_item_stats(raw_stats, stats_text, ddragon_version):
    normalized = []
    seen_canonical = set()
    raw_stats = raw_stats or {}

    for source_field, value in sorted(raw_stats.items()):
        mapping = STAT_FIELD_MAP.get(source_field)
        if mapping:
            stat, unit = mapping
            seen_canonical.add(stat)
        else:
            stat, unit = "UNKNOWN", UNKNOWN
        normalized.append(
            {
                "stat": stat,
                "value": value,
                "unit": unit,
                "source": "DDRAGON_STATS",
                "source_field": source_field,
                "confidence": "STRUCTURED",
                "ddragon_version": ddragon_version,
            }
        )

    for line in (stats_text or "").splitlines():
        parsed = _description_stat_mapping(line)
        if not parsed:
            continue
        stat, value, unit = parsed
        if stat in seen_canonical:
            continue
        seen_canonical.add(stat)
        normalized.append(
            {
                "stat": stat,
                "value": value,
                "unit": unit,
                "source": "DDRAGON_DESCRIPTION_STATS",
                "source_field": "description.stats",
                "confidence": "DESCRIPTION_EXPLICIT",
                "evidence_text": line,
                "ddragon_version": ddragon_version,
            }
        )

    return normalized


def _effect_key(effect):
    return (
        effect["effect_type"],
        effect.get("source"),
        effect.get("evidence_text"),
    )


def _add_effect(effects, effect):
    key = _effect_key(effect)
    if key in {_effect_key(existing) for existing in effects}:
        return
    effects.append(effect)


def extract_item_effects(raw_item, description_sections, ddragon_version):
    effects = []
    tags = raw_item.get("tags") or []

    for tag in tags:
        effect_type = TAG_EFFECT_MAP.get(tag)
        if not effect_type:
            continue
        _add_effect(
            effects,
            {
                "effect_type": effect_type,
                "confidence": "STRUCTURED",
                "source": "DDRAGON_TAGS",
                "evidence_text": tag,
                "source_field": "tags",
                "ddragon_version": ddragon_version,
            },
        )

    unparsed = []
    for section in description_sections.get("sections", []):
        section_text = " ".join(
            value
            for value in (section.get("name"), section.get("text"))
            if value
        )
        normalized = _normalize_text(section_text)
        matched = False

        for effect_type, phrases in EFFECT_RULES:
            phrase_matches = [
                phrase
                for phrase in phrases
                if _normalize_text(phrase) in normalized
            ]
            if not phrase_matches:
                continue

            if (
                effect_type.startswith("ACTIVE_")
                and section.get("section_type") != "ACTIVE"
            ):
                continue

            matched = True
            _add_effect(
                effects,
                {
                    "effect_type": effect_type,
                    "confidence": "DESCRIPTION_EXPLICIT",
                    "source": "DDRAGON_DESCRIPTION",
                    "source_field": section.get("section_type"),
                    "section_name": section.get("name"),
                    "evidence_text": section_text,
                    "matched_text": phrase_matches[0],
                    "ddragon_version": ddragon_version,
                },
            )

        if section.get("text") and not matched:
            unparsed.append(
                {
                    "kind": UNPARSED_EFFECT_TEXT,
                    "section_type": section.get("section_type", UNKNOWN),
                    "section_name": section.get("name", UNKNOWN),
                    "text": section.get("text"),
                    "source": "DDRAGON_DESCRIPTION",
                    "ddragon_version": ddragon_version,
                }
            )

    return effects, unparsed


def _int_list(values):
    result = []
    for value in values or []:
        try:
            result.append(int(value))
        except (TypeError, ValueError):
            continue
    return result


def _field_or_not_exposed(raw_item, key):
    if key in raw_item:
        return raw_item.get(key)
    return NOT_EXPOSED


def classify_applicability(raw_item, item_id):
    tags = set(raw_item.get("tags") or [])
    maps = raw_item.get("maps") or {}
    gold = raw_item.get("gold") or {}
    purchasable = gold.get("purchasable")
    map11 = maps.get(SUMMONERS_RIFT_MAP_ID)
    required_champion = raw_item.get("requiredChampion")
    in_store = raw_item.get("inStore", True)

    classes = []
    if map11 is True and purchasable is True:
        classes.append("SUMMONERS_RIFT_PURCHASABLE")
    if "Boots" in tags:
        classes.append("BOOTS")
    if "Trinket" in tags:
        classes.append("TRINKET")
    if "Consumable" in tags or raw_item.get("consumed"):
        classes.append("CONSUMABLE")
    if "Jungle" in tags and item_id in {1101, 1102, 1103}:
        classes.append("JUNGLE_STARTER")
    if (
        purchasable is True
        and map11 is True
        and gold.get("total") is not None
        and gold.get("total") <= 500
        and not {"Trinket", "Consumable", "Jungle"} & tags
    ):
        classes.append("STARTER_OR_BASIC_COMPONENT")
    if map11 is not True:
        classes.append("MODE_SPECIFIC_OR_NOT_SR")
    if required_champion:
        classes.append("CHAMPION_SPECIFIC")
    if purchasable is False:
        classes.append("NON_PURCHASABLE")
    if raw_item.get("hideFromAll") or in_store is False:
        classes.append("SPECIAL_OR_GENERATED")
    if raw_item.get("specialRecipe") is not None:
        classes.append("SPECIAL_RECIPE")
    if not classes:
        classes.append(UNKNOWN)

    return {
        "classes": sorted(set(classes)),
        "summoners_rift_available": map11
        if map11 is not None
        else NOT_EXPOSED,
        "purchasable_on_summoners_rift": (
            map11 is True and purchasable is True
        ),
        "map_availability": maps if maps else NOT_EXPOSED,
        "required_champion": required_champion or NOT_EXPOSED,
        "in_store": in_store,
    }


def _resolve_version(requested_game_version=None, versions=None):
    versions = list(versions or get_ddragon_versions())
    requested = requested_game_version or "LATEST"

    if not versions:
        return {
            "requested_game_version": requested,
            "resolved_ddragon_version": UNKNOWN,
            "resolution_status": "NO_VERSIONS_AVAILABLE",
            "fallback_used": True,
        }

    if requested_game_version is None:
        return {
            "requested_game_version": requested,
            "resolved_ddragon_version": versions[0],
            "resolution_status": "LATEST",
            "fallback_used": False,
        }

    if requested_game_version in versions:
        return {
            "requested_game_version": requested_game_version,
            "resolved_ddragon_version": requested_game_version,
            "resolution_status": "EXACT_VERSION",
            "fallback_used": False,
        }

    parts = str(requested_game_version).split(".")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        patch = f"{parts[0]}.{parts[1]}"
        for version in versions:
            if version.startswith(patch + "."):
                return {
                    "requested_game_version": requested_game_version,
                    "resolved_ddragon_version": version,
                    "resolution_status": "EXACT_PATCH",
                    "fallback_used": False,
                }

    return {
        "requested_game_version": requested_game_version,
        "resolved_ddragon_version": versions[0],
        "resolution_status": "FALLBACK_LATEST",
        "fallback_used": True,
    }


def _load_raw_items(ddragon_version, locale):
    if locale == "fr_FR":
        return get_items(ddragon_version)

    url = (
        f"{DDRAGON_BASE_URL}/cdn/"
        f"{ddragon_version}/data/{locale}/item.json"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()["data"]


def _build_initial_record(
    item_id,
    raw_item,
    version_info,
    locale,
):
    ddragon_version = version_info["resolved_ddragon_version"]
    gold = raw_item.get("gold") or {}
    description = raw_item.get("description")
    sections = parse_description_sections(description)
    normalized_stats = normalize_item_stats(
        raw_item.get("stats") or {},
        sections.get("stats_text"),
        ddragon_version,
    )
    effects, unparsed = extract_item_effects(
        raw_item,
        sections,
        ddragon_version,
    )
    metadata_warnings = []

    for required_key in ("name", "gold", "tags", "maps", "stats"):
        if required_key not in raw_item:
            metadata_warnings.append(f"{required_key}:NOT_EXPOSED")

    return {
        "item_id": item_id,
        "name": raw_item.get("name") or f"ITEM_{item_id}",
        "item_knowledge_version": ITEM_KNOWLEDGE_VERSION,
        "requested_game_version": version_info["requested_game_version"],
        "ddragon_version": ddragon_version,
        "version_resolution_status": version_info["resolution_status"],
        "version_fallback_used": version_info["fallback_used"],
        "locale": locale,
        "purchasable": gold.get("purchasable")
        if "purchasable" in gold
        else UNKNOWN,
        "gold": {
            "total": gold.get("total"),
            "base": gold.get("base"),
            "sell": gold.get("sell"),
            "purchasable": gold.get("purchasable")
            if "purchasable" in gold
            else UNKNOWN,
            "raw": gold,
        },
        "tags": list(raw_item.get("tags") or []),
        "from_item_ids": _int_list(raw_item.get("from") or []),
        "into_item_ids": _int_list(raw_item.get("into") or []),
        "raw_stats": dict(raw_item.get("stats") or {}),
        "normalized_stats": normalized_stats,
        "raw_effect_fields": dict(raw_item.get("effect") or {}),
        "effects": effects,
        "unparsed_effect_text": unparsed,
        "raw_description": description if description is not None else "",
        "clean_description": sections["clean_text"],
        "description_sections": sections,
        "plaintext": raw_item.get("plaintext", ""),
        "maps": raw_item.get("maps") or NOT_EXPOSED,
        "consumed": _field_or_not_exposed(raw_item, "consumed"),
        "consume_on_full": _field_or_not_exposed(raw_item, "consumeOnFull"),
        "raw_metadata": {
            "colloq": raw_item.get("colloq", ""),
            "image": raw_item.get("image", NOT_EXPOSED),
            "depth": raw_item.get("depth", NOT_EXPOSED),
            "stacks": raw_item.get("stacks", NOT_EXPOSED),
            "inStore": raw_item.get("inStore", NOT_EXPOSED),
            "hideFromAll": raw_item.get("hideFromAll", NOT_EXPOSED),
            "requiredChampion": raw_item.get(
                "requiredChampion",
                NOT_EXPOSED,
            ),
            "specialRecipe": raw_item.get("specialRecipe", NOT_EXPOSED),
        },
        "raw_data": raw_item,
        "metadata_warnings": metadata_warnings,
        "applicability": classify_applicability(raw_item, item_id),
        "item_graph": {},
    }


def _component_tree(item_id, records, visiting=None):
    visiting = set(visiting or ())
    if item_id in visiting:
        return [], [{"kind": "CYCLE", "item_id": item_id}]
    visiting.add(item_id)

    record = records.get(item_id)
    if not record:
        return [], [{"kind": "MISSING_ITEM", "item_id": item_id}]

    tree = []
    issues = []
    for component_id in record["from_item_ids"]:
        if component_id not in records:
            issues.append(
                {
                    "kind": "MISSING_COMPONENT",
                    "item_id": item_id,
                    "component_id": component_id,
                }
            )
            continue
        tree.append(component_id)
        nested_tree, nested_issues = _component_tree(
            component_id,
            records,
            visiting.copy(),
        )
        tree.extend(nested_tree)
        issues.extend(nested_issues)

    return tree, issues


def _upgrade_descendants(item_id, records, visiting=None):
    visiting = set(visiting or ())
    if item_id in visiting:
        return [], [{"kind": "CYCLE", "item_id": item_id}]
    visiting.add(item_id)

    record = records.get(item_id)
    if not record:
        return [], [{"kind": "MISSING_ITEM", "item_id": item_id}]

    descendants = []
    issues = []
    for upgrade_id in record["into_item_ids"]:
        if upgrade_id not in records:
            issues.append(
                {
                    "kind": "MISSING_UPGRADE",
                    "item_id": item_id,
                    "upgrade_id": upgrade_id,
                }
            )
            continue
        descendants.append(upgrade_id)
        nested_descendants, nested_issues = _upgrade_descendants(
            upgrade_id,
            records,
            visiting.copy(),
        )
        descendants.extend(nested_descendants)
        issues.extend(nested_issues)

    return descendants, issues


def _item_depth(item_id, records, visiting=None):
    visiting = set(visiting or ())
    if item_id in visiting:
        return UNKNOWN
    visiting.add(item_id)
    record = records.get(item_id)
    if not record:
        return UNKNOWN
    if not record["from_item_ids"]:
        return 0
    depths = [
        _item_depth(component_id, records, visiting.copy())
        for component_id in record["from_item_ids"]
    ]
    numeric_depths = [depth for depth in depths if isinstance(depth, int)]
    if not numeric_depths:
        return UNKNOWN
    return 1 + max(numeric_depths)


def _sum_component_gold(component_ids, records):
    total = 0
    missing = []
    for component_id in component_ids:
        record = records.get(component_id)
        if not record:
            missing.append(component_id)
            continue
        component_total = record.get("gold", {}).get("total")
        if component_total is None:
            missing.append(component_id)
            continue
        total += component_total
    return total, missing


def attach_item_graph(records):
    graph_issues = []
    for item_id, record in records.items():
        direct_components = list(record["from_item_ids"])
        component_tree, component_issues = _component_tree(item_id, records)
        descendants, descendant_issues = _upgrade_descendants(
            item_id,
            records,
        )
        component_gold, missing_component_gold = _sum_component_gold(
            direct_components,
            records,
        )
        total_gold = record["gold"].get("total")
        combine_cost = None
        combine_cost_status = "NOT_DERIVED"
        if total_gold is not None and not missing_component_gold:
            combine_cost = total_gold - component_gold
            combine_cost_status = "DERIVED_FROM_DIRECT_COMPONENTS"

        issues = component_issues + descendant_issues
        for component_id in direct_components:
            if component_id not in records:
                issues.append(
                    {
                        "kind": "MISSING_DIRECT_COMPONENT",
                        "item_id": item_id,
                        "component_id": component_id,
                    }
                )
        for upgrade_id in record["into_item_ids"]:
            if upgrade_id not in records:
                issues.append(
                    {
                        "kind": "MISSING_DIRECT_UPGRADE",
                        "item_id": item_id,
                        "upgrade_id": upgrade_id,
                    }
                )

        record["item_graph"] = {
            "direct_components": direct_components,
            "recursive_component_tree": sorted(set(component_tree)),
            "direct_upgrades": list(record["into_item_ids"]),
            "final_upgrade_descendants": sorted(set(descendants)),
            "item_depth": _item_depth(item_id, records),
            "component_cost_contribution": component_gold,
            "combine_cost": combine_cost,
            "combine_cost_status": combine_cost_status,
            "missing_component_gold": missing_component_gold,
            "issues": issues,
        }
        graph_issues.extend(issues)

    return graph_issues


def build_item_knowledge_catalog(
    requested_game_version=None,
    locale=DEFAULT_LOCALE,
    raw_items=None,
    versions=None,
):
    version_info = _resolve_version(requested_game_version, versions=versions)
    if raw_items is None:
        raw_items = _load_raw_items(
            version_info["resolved_ddragon_version"],
            locale,
        )

    records = {}
    invalid_item_keys = []
    for raw_key, raw_item in sorted(
        raw_items.items(),
        key=lambda item: int(item[0]) if str(item[0]).isdigit() else 10**9,
    ):
        try:
            item_id = int(raw_key)
        except (TypeError, ValueError):
            invalid_item_keys.append(raw_key)
            continue
        records[item_id] = _build_initial_record(
            item_id,
            raw_item or {},
            version_info,
            locale,
        )

    graph_issues = attach_item_graph(records)
    summary = summarize_item_knowledge(records, graph_issues, invalid_item_keys)

    return {
        "item_knowledge_version": ITEM_KNOWLEDGE_VERSION,
        "requested_game_version": version_info["requested_game_version"],
        "resolved_ddragon_version": version_info["resolved_ddragon_version"],
        "version_resolution_status": version_info["resolution_status"],
        "version_fallback_used": version_info["fallback_used"],
        "locale": locale,
        "records": records,
        "summary": summary,
    }


def summarize_item_knowledge(records, graph_issues, invalid_item_keys=None):
    invalid_item_keys = invalid_item_keys or []
    name_counts = Counter(record["name"] for record in records.values())
    duplicate_names = {
        name: count
        for name, count in name_counts.items()
        if count > 1
    }
    stat_counts = Counter()
    source_field_counts = Counter()
    effect_counts = Counter()
    effect_confidence_counts = Counter()
    class_counts = Counter()
    unknown_metadata_count = 0
    items_with_stats = 0
    items_with_effects = 0
    items_with_description_effects = 0
    items_with_unparsed = 0
    items_with_unknown_stats = 0

    for record in records.values():
        normalized_stats = record["normalized_stats"]
        if normalized_stats:
            items_with_stats += 1
        if record["effects"]:
            items_with_effects += 1
        if any(
            effect["source"] == "DDRAGON_DESCRIPTION"
            for effect in record["effects"]
        ):
            items_with_description_effects += 1
        if record["unparsed_effect_text"]:
            items_with_unparsed += 1
        if record["metadata_warnings"]:
            unknown_metadata_count += 1
        if any(stat["stat"] == "UNKNOWN" for stat in normalized_stats):
            items_with_unknown_stats += 1

        for stat in normalized_stats:
            stat_counts[stat["stat"]] += 1
            source_field_counts[stat["source_field"]] += 1
        for effect in record["effects"]:
            effect_counts[effect["effect_type"]] += 1
            effect_confidence_counts[effect["confidence"]] += 1
        class_counts.update(record["applicability"]["classes"])

    return {
        "total_item_records": len(records),
        "invalid_item_keys": invalid_item_keys,
        "purchasable_summoners_rift_items": class_counts[
            "SUMMONERS_RIFT_PURCHASABLE"
        ],
        "items_with_normalized_stats": items_with_stats,
        "items_with_effects_extracted": items_with_effects,
        "items_with_description_only_effects": (
            items_with_description_effects
        ),
        "items_with_unparsed_effect_text": items_with_unparsed,
        "items_with_unknown_metadata": unknown_metadata_count,
        "items_with_unknown_stats": items_with_unknown_stats,
        "graph_inconsistencies": len(graph_issues),
        "graph_issue_kinds": Counter(issue["kind"] for issue in graph_issues),
        "duplicate_ids": 0,
        "duplicate_names": duplicate_names,
        "mode_specific_items": class_counts["MODE_SPECIFIC_OR_NOT_SR"],
        "champion_specific_items": class_counts["CHAMPION_SPECIFIC"],
        "non_purchasable_items": class_counts["NON_PURCHASABLE"],
        "applicability_class_counts": class_counts,
        "canonical_stat_coverage": stat_counts,
        "source_field_coverage": source_field_counts,
        "effect_type_coverage": effect_counts,
        "effect_confidence_counts": effect_confidence_counts,
        "graph_issue_samples": graph_issues[:12],
    }


def _format_counts(counter, limit=None):
    if not counter:
        return "none"
    items = counter.items() if hasattr(counter, "items") else counter
    sorted_items = sorted(items, key=lambda item: (-item[1], str(item[0])))
    if limit:
        sorted_items = sorted_items[:limit]
    return ", ".join(f"{key}: {value}" for key, value in sorted_items)


def _record_has_stat(record, stat_name):
    return any(stat["stat"] == stat_name for stat in record["normalized_stats"])


def _record_has_effect(record, effect_type):
    return any(effect["effect_type"] == effect_type for effect in record["effects"])


def select_representative_items(catalog):
    records = catalog["records"]
    selected = {}

    def pick(requirement, predicate):
        if requirement in selected:
            return
        all_records = list(records.values())
        preferred_records = [
            record
            for record in all_records
            if "SUMMONERS_RIFT_PURCHASABLE"
            in record["applicability"]["classes"]
        ]
        for candidate_records in (preferred_records, all_records):
            for record in candidate_records:
                if predicate(record):
                    selected[requirement] = record["item_id"]
                    return

    pick(
        "pure_ad_item",
        lambda r: _record_has_stat(r, "attack_damage")
        and not _record_has_stat(r, "ability_power")
        and not r["from_item_ids"],
    )
    pick(
        "pure_ap_item",
        lambda r: _record_has_stat(r, "ability_power")
        and not _record_has_stat(r, "attack_damage")
        and not r["from_item_ids"],
    )
    pick("armor_item", lambda r: _record_has_stat(r, "armor"))
    pick("mr_item", lambda r: _record_has_stat(r, "magic_resistance"))
    pick(
        "attack_speed_item",
        lambda r: _record_has_stat(r, "attack_speed_percent"),
    )
    pick(
        "crit_item",
        lambda r: _record_has_stat(r, "critical_strike_chance"),
    )
    pick("boots", lambda r: "BOOTS" in r["applicability"]["classes"])
    pick(
        "tank_item",
        lambda r: _record_has_stat(r, "health")
        and (
            _record_has_stat(r, "armor")
            or _record_has_stat(r, "magic_resistance")
        ),
    )
    pick(
        "lifeline_or_shield_item",
        lambda r: _record_has_effect(r, "LIFELINE_SHIELD")
        or _record_has_effect(r, "ACTIVE_SHIELD")
        or _record_has_effect(r, "SPELL_SHIELD"),
    )
    pick(
        "grievous_wounds_item",
        lambda r: _record_has_effect(r, "GRIEVOUS_WOUNDS"),
    )
    pick(
        "penetration_item",
        lambda r: _record_has_stat(r, "armor_penetration_flat")
        or _record_has_stat(r, "armor_penetration_percent")
        or _record_has_stat(r, "magic_penetration_flat")
        or _record_has_stat(r, "magic_penetration_percent")
        or _record_has_effect(r, "ARMOR_PENETRATION")
        or _record_has_effect(r, "MAGIC_PENETRATION"),
    )
    pick("on_hit_item", lambda r: _record_has_effect(r, "ON_HIT_DAMAGE"))
    pick(
        "percent_health_mechanic",
        lambda r: _record_has_effect(r, "PERCENT_CURRENT_HEALTH_DAMAGE")
        or _record_has_effect(r, "PERCENT_MAX_HEALTH_DAMAGE"),
    )
    pick(
        "active_item",
        lambda r: "Active" in r["tags"]
        or any(
            effect["effect_type"].startswith("ACTIVE_")
            for effect in r["effects"]
        ),
    )
    pick("consumable", lambda r: "CONSUMABLE" in r["applicability"]["classes"])
    pick(
        "jungle_starter",
        lambda r: "JUNGLE_STARTER" in r["applicability"]["classes"],
    )
    pick("trinket", lambda r: "TRINKET" in r["applicability"]["classes"])
    pick(
        "non_purchasable_or_transformed_item",
        lambda r: "NON_PURCHASABLE" in r["applicability"]["classes"]
        or _record_has_effect(r, "TRANSFORMATION"),
    )

    return selected


def render_item_record_diagnostic(record):
    graph = record["item_graph"]
    lines = [
        (
            f"{record['name']} ({record['item_id']}) | "
            f"version={record['ddragon_version']} | "
            f"locale={record['locale']}"
        ),
        (
            "raw facts: "
            f"purchasable={record['purchasable']} | "
            f"gold={record['gold']} | tags={record['tags']} | "
            f"maps={record['maps']}"
        ),
        f"raw stats: {record['raw_stats'] or 'none'}",
        f"raw effect fields: {record['raw_effect_fields'] or 'none'}",
        f"plaintext: {record['plaintext'] or 'none'}",
        f"clean description: {record['clean_description'] or 'none'}",
        "normalized stats:",
    ]

    if record["normalized_stats"]:
        for stat in record["normalized_stats"]:
            lines.append(f"  - {stat}")
    else:
        lines.append("  - none")

    lines.append("mechanics:")
    if record["effects"]:
        for effect in record["effects"]:
            lines.append(f"  - {effect}")
    else:
        lines.append("  - none")

    lines.extend(
        [
            "item graph:",
            f"  direct_components={graph['direct_components']}",
            f"  recursive_component_tree={graph['recursive_component_tree']}",
            f"  direct_upgrades={graph['direct_upgrades']}",
            f"  final_upgrade_descendants={graph['final_upgrade_descendants']}",
            f"  item_depth={graph['item_depth']}",
            (
                "  component_cost_contribution="
                f"{graph['component_cost_contribution']} | "
                f"combine_cost={graph['combine_cost']} "
                f"({graph['combine_cost_status']})"
            ),
            f"  issues={graph['issues'] or 'none'}",
            f"applicability: {record['applicability']}",
            (
                "unknown/unparsed: "
                f"metadata={record['metadata_warnings'] or 'none'} | "
                f"unparsed={record['unparsed_effect_text'] or 'none'}"
            ),
        ]
    )
    return "\n".join(lines)


def render_item_knowledge_audit(catalog):
    summary = catalog["summary"]
    lines = [
        "ITEM KNOWLEDGE BASE PHASE 2A AUDIT",
        "",
        "Scope: factual, patch-aware Data Dragon item knowledge only.",
        "No champion analysis, composition analysis, item recommendation,",
        "GOOD/BAD labels, win-rate learning, or ML is computed here.",
        "",
        f"Item knowledge version: {catalog['item_knowledge_version']}",
        f"Requested game version: {catalog['requested_game_version']}",
        f"Resolved Data Dragon version: {catalog['resolved_ddragon_version']}",
        f"Version resolution: {catalog['version_resolution_status']}",
        f"Fallback used: {catalog['version_fallback_used']}",
        f"Locale: {catalog['locale']}",
        "",
        f"Total item records: {summary['total_item_records']}",
        (
            "Purchasable Summoner's Rift items: "
            f"{summary['purchasable_summoners_rift_items']}"
        ),
        (
            "Items with normalized stats: "
            f"{summary['items_with_normalized_stats']}"
        ),
        (
            "Items with extracted effects: "
            f"{summary['items_with_effects_extracted']}"
        ),
        (
            "Items with description effects: "
            f"{summary['items_with_description_only_effects']}"
        ),
        (
            "Items with unparsed effect text: "
            f"{summary['items_with_unparsed_effect_text']}"
        ),
        (
            "Items with UNKNOWN metadata: "
            f"{summary['items_with_unknown_metadata']}"
        ),
        (
            "Items with unknown raw stats preserved: "
            f"{summary['items_with_unknown_stats']}"
        ),
        f"Graph inconsistencies: {summary['graph_inconsistencies']}",
        f"Graph issue kinds: {_format_counts(summary['graph_issue_kinds'])}",
        f"Duplicate IDs: {summary['duplicate_ids']}",
        f"Duplicate names: {summary['duplicate_names'] or 'none'}",
        f"Mode-specific / non-SR items: {summary['mode_specific_items']}",
        f"Champion-specific items: {summary['champion_specific_items']}",
        f"Non-purchasable items: {summary['non_purchasable_items']}",
        "",
        (
            "Applicability classes: "
            f"{_format_counts(summary['applicability_class_counts'])}"
        ),
        (
            "Canonical stat coverage: "
            f"{_format_counts(summary['canonical_stat_coverage'])}"
        ),
        (
            "Data Dragon stat field coverage: "
            f"{_format_counts(summary['source_field_coverage'])}"
        ),
        (
            "Effect type coverage: "
            f"{_format_counts(summary['effect_type_coverage'])}"
        ),
        (
            "Effect confidence coverage: "
            f"{_format_counts(summary['effect_confidence_counts'])}"
        ),
    ]

    if summary["graph_issue_samples"]:
        lines.extend(["", "Graph issue samples:"])
        for issue in summary["graph_issue_samples"]:
            lines.append(f"- {issue}")

    return "\n".join(lines)


def render_representative_item_diagnostics(catalog):
    selected = select_representative_items(catalog)
    lines = [
        "REPRESENTATIVE ITEM KNOWLEDGE DIAGNOSTICS",
        "",
    ]
    missing = [
        requirement
        for requirement in REPRESENTATIVE_REQUIREMENTS
        if requirement not in selected
    ]
    lines.append(f"Coverage requirements satisfied: {len(selected)}/{len(REPRESENTATIVE_REQUIREMENTS)}")
    lines.append(f"Missing diagnostic requirements: {missing or 'none'}")

    printed_item_ids = set()
    for requirement in REPRESENTATIVE_REQUIREMENTS:
        item_id = selected.get(requirement)
        if item_id is None:
            continue
        record = catalog["records"][item_id]
        lines.extend(
            [
                "",
                f"## {requirement}",
                render_item_record_diagnostic(record),
            ]
        )
        printed_item_ids.add(item_id)

    return "\n".join(lines)


def main():
    catalog = build_item_knowledge_catalog()
    print(render_item_knowledge_audit(catalog))
    print()
    print(render_representative_item_diagnostics(catalog))


if __name__ == "__main__":
    main()
