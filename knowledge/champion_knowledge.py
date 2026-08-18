import html
import re
import unicodedata
from collections import Counter

import requests

from riot.data_dragon import DDRAGON_BASE_URL, get_ddragon_versions


CHAMPION_KNOWLEDGE_VERSION = "champion_knowledge_phase2b1_c_v1"
DEFAULT_LOCALE = "fr_FR"
UNKNOWN = "UNKNOWN"
NOT_EXPOSED = "NOT_EXPOSED"
UNPARSED_EFFECT_TEXT = "UNPARSED_EFFECT_TEXT"
PARTIALLY_PARSED_EFFECT_TEXT = "PARTIALLY_PARSED_EFFECT_TEXT"
FORMULA_INCOMPLETE = "FORMULA_INCOMPLETE"
SEMANTIC_PARSER_SUPPORTED = "SUPPORTED"
SEMANTIC_PARSER_UNSUPPORTED_LOCALE = "UNSUPPORTED_LOCALE"
SUPPORTED_SEMANTIC_LOCALES = {"fr_FR"}

SLOT_BY_INDEX = {0: "Q", 1: "W", 2: "E", 3: "R"}

STAT_FIELD_MAP = {
    "hp": ("health_base", "flat"),
    "hpperlevel": ("health_growth", "per_level_field"),
    "hpregen": ("health_regen_base", "flat"),
    "hpregenperlevel": ("health_regen_growth", "per_level_field"),
    "mp": ("resource_base", "flat"),
    "mpperlevel": ("resource_growth", "per_level_field"),
    "mpregen": ("resource_regen_base", "flat"),
    "mpregenperlevel": ("resource_regen_growth", "per_level_field"),
    "attackdamage": ("attack_damage_base", "flat"),
    "attackdamageperlevel": ("attack_damage_growth", "per_level_field"),
    "attackspeed": ("attack_speed_base", "flat"),
    "attackspeedperlevel": ("attack_speed_growth", "per_level_field"),
    "armor": ("armor_base", "flat"),
    "armorperlevel": ("armor_growth", "per_level_field"),
    "spellblock": ("magic_resistance_base", "flat"),
    "spellblockperlevel": ("magic_resistance_growth", "per_level_field"),
    "movespeed": ("move_speed", "flat"),
    "attackrange": ("attack_range", "flat"),
    "crit": ("crit_base", "flat"),
    "critperlevel": ("crit_growth", "per_level_field"),
}

SEMANTIC_RULES = [
    ("PERCENT_MAX_HEALTH_DAMAGE", ("pv max", "points de vie max")),
    ("PERCENT_CURRENT_HEALTH_DAMAGE", ("pv actuels", "pv actuel")),
    ("MISSING_HEALTH_DAMAGE", ("pv manquants", "points de vie manquants")),
    ("TRUE_DAMAGE", ("degats bruts",)),
    ("PHYSICAL_DAMAGE", ("degats physiques",)),
    ("MAGIC_DAMAGE", ("degats magiques",)),
    ("EXECUTE", ("execute", "execution", "acheve")),
    ("HEAL", ("soigne", "soignez", "recupere des pv", "recuperez des pv", "rend des pv")),
    ("SHIELD", ("bouclier",)),
    ("DAMAGE_REDUCTION", ("reduit les degats", "degats subis", "reduction des degats")),
    ("INVULNERABLE", ("invulnerable", "invulnerabilite")),
    ("UNTARGETABLE", ("inciblable", "impossible a cibler", "ne peut pas etre cible")),
    ("BLINK", ("teleporte", "se teleporte")),
    ("DASH", ("ruee", "se rue", "fonce", "bondit", "bondissez")),
    ("MOVE_SPEED", ("vitesse de deplacement",)),
    ("DISPLACEMENT_SELF", ("bondit", "saute", "se rue", "fonce")),
    ("SLOW", ("ralentit", "ralentissement", "ralentisse")),
    ("STUN", ("etourdit", "etourdissement")),
    ("ROOT", ("immobilise", "immobilisation", "entrave")),
    ("KNOCKUP", ("projette dans les airs", "projette en l'air")),
    ("KNOCKBACK", ("repousse", "repousses")),
    ("FEAR", ("effraie", "fuite")),
    ("CHARM", ("charme",)),
    ("TAUNT", ("provoque", "provocation")),
    ("SILENCE", ("silence", "reduit au silence")),
    ("SUPPRESSION", ("suppression",)),
    ("SLEEP", ("endort", "sommeil")),
    ("GROUND", ("cloue au sol", "ancre au sol")),
    ("CAMOUFLAGE", ("camouflage", "camoufle")),
    ("STEALTH", ("furtivite", "invisible", "invisibilite")),
    ("REVEAL", ("revele", "revelation")),
    ("ATTACK_RESET", ("reinitialise son attaque", "reinitialise l'attaque")),
    ("ON_HIT", ("a l'impact", "effets a l'impact")),
    ("STACKING", ("cumul", "cumuls", "charge", "charges")),
    (
        "TRANSFORMATION",
        (
            "transforme",
            "change de forme",
            "forme de dragon",
            "forme humaine",
            "forme arachneenne",
            "forme de cougar",
        ),
    ),
    ("MARK", ("marque", "marquee", "marquer")),
    ("EMPOWERED_ATTACK", ("prochaine attaque", "attaque renforcee")),
    ("RESET_OR_REFRESH", ("reinitialise", "rafraichit")),
    ("SPECIAL_RESOURCE", ("fureur", "energie", "flux", "ferveur")),
    ("DAMAGE_TYPE_UNRESOLVED", ("degats",)),
]

HARD_CC_TYPES = {
    "STUN",
    "ROOT",
    "KNOCKUP",
    "KNOCKBACK",
    "FEAR",
    "CHARM",
    "TAUNT",
    "SILENCE",
    "SUPPRESSION",
    "SLEEP",
}

CLAUSE_LOCAL_EFFECT_TYPES = {
    "PERCENT_MAX_HEALTH_DAMAGE",
    "PERCENT_CURRENT_HEALTH_DAMAGE",
    "MISSING_HEALTH_DAMAGE",
    "TRUE_DAMAGE",
    "PHYSICAL_DAMAGE",
    "MAGIC_DAMAGE",
    "DAMAGE_TYPE_UNRESOLVED",
    "EXECUTE",
    "HEAL",
    "SHIELD",
    "DAMAGE_REDUCTION",
    "REVEAL",
}

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
    "immunise aux degats",
    "insensible aux degats",
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

SHIELD_NEGATIVE_CONTEXT_PHRASES = (
    "detruit les boucliers",
    "detruire les boucliers",
    "reduit les boucliers",
    "ignore les boucliers",
    "contre les boucliers",
    "aux boucliers",
    "boucliers ennemis",
    "cible deja protegee par un bouclier",
)

TRANSFORMATION_EVIDENCE_PHRASES = (
    "transforme",
    "se transforme",
    "change de forme",
    "changer de forme",
    "forme de dragon",
    "forme dragon",
    "forme humaine",
    "forme arachneenne",
    "forme de cougar",
    "forme de couguar",
    "forme couguar",
    "posture",
)

ALTERNATE_FORM_SELF_PHRASES = (
    "se transforme",
    "change de forme",
    "changer de forme",
    "alterne entre",
    "passe en forme",
    "passe sous forme",
    "activer sa forme",
    "active sa forme",
    "sa forme veritable",
    "forme veritable",
    "veritable forme",
    "le transforme en",
    "la transforme en",
)

ALTERNATE_FORM_NAMED_FORM_PHRASES = (
    "forme de dragon",
    "forme dragon",
    "forme humaine",
    "forme arachneenne",
    "forme de cougar",
    "forme de couguar",
    "forme couguar",
)

ALTERNATE_FORM_STANCE_PHRASES = (
    "change de posture",
    "changer de posture",
    "adopte une posture",
    "prend une posture",
    "posture",
)

GENERIC_TRANSFORMATION_OBJECT_PHRASES = (
    "transforme les degats",
    "transforme des degats",
    "transforme ses degats",
    "transforme l'attaque",
    "transforme son attaque",
    "transforme sa prochaine attaque",
    "transforme le prochain lancement",
    "transforme la prochaine",
    "transforme son kit",
    "transforme ses competences",
    "transforme sa competence",
    "transforme cette competence",
    "transforme la competence",
    "transforme la cible",
    "transforme un ennemi",
    "transforme l'ennemi",
    "ennemi est transforme",
    "ennemis sont transformes",
    "cible est transformee",
    "transforme la marque",
    "transforme les marques",
    "transforme la ressource",
    "transforme la fureur",
    "transforme l'effet",
    "transforme les effets",
    "transforme le terrain",
    "transforme les sbires",
    "transforme les arbrisseaux",
    "transforme les graines",
    "transforme les goules",
    "transforme les plantes",
    "transforme murmure",
)

NON_SELF_TRANSFORMATION_SUBJECT_PHRASES = (
    "cette graine se transforme",
    "une graine se transforme",
    "la graine se transforme",
    "l'ennemi se transforme",
    "un ennemi se transforme",
    "un champion ennemi se transforme",
    "le champion ennemi se transforme",
    "il se transforme en serviteur",
    "elle se transforme en serviteur",
    "la cible se transforme",
    "il le transforme",
    "elle le transforme",
    "il la transforme",
    "elle la transforme",
    "les ennemis se transforment",
    "les sbires se transforment",
    "les arbrisseaux se transforment",
    "les graines se transforment",
    "les goules se transforment",
    "les plantes se transforment",
    "se transforme en laser",
)

PLACEHOLDER_FORMULA_HINTS = (
    "damage",
    "degat",
    "heal",
    "shield",
    "speed",
    "slow",
    "duration",
    "range",
    "radius",
    "ratio",
    "amount",
    "value",
    "bonus",
    "cost",
    "cooldown",
    "stack",
    "percent",
    "hp",
    "mana",
)

PLACEHOLDER_DISPLAY_HINTS = (
    "keyword",
    "icon",
    "color",
    "display",
    "name",
    "text",
    "description",
    "append",
    "modifier",
    "resource",
)

REPRESENTATIVE_REQUIREMENTS = [
    "Shyvana",
    "Bel'Veth",
    "Dr. Mundo",
    "Rammus",
    "Viego",
    "alternate_or_transformation",
    "complex_ability_structure",
    "shield",
    "healing",
    "copied_or_dynamic",
    "true_damage",
    "percent_health_damage",
    "hard_cc",
    "stealth_or_reveal",
    "mixed_damage",
]


def _collapse_spaces(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _normalize_text(text):
    text = html.unescape(str(text or "")).lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("’", "'")
    return _collapse_spaces(text)


def clean_description(raw_text):
    if raw_text is None:
        return ""
    text = html.unescape(str(raw_text))
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(?:p|div|li|maintext|stats|passive|active|rules)>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    lines = [_collapse_spaces(line) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def semantic_parser_status(locale):
    if locale in SUPPORTED_SEMANTIC_LOCALES:
        return SEMANTIC_PARSER_SUPPORTED
    return SEMANTIC_PARSER_UNSUPPORTED_LOCALE


def _contains_any(normalized_text, phrases):
    return any(_normalize_text(phrase) in normalized_text for phrase in phrases)


def _has_damage_action(normalized_text):
    return _contains_any(normalized_text, OUTGOING_DAMAGE_ACTION_PHRASES)


def _has_defensive_damage_context(normalized_text):
    return _contains_any(normalized_text, DEFENSIVE_DAMAGE_CONTEXT_PHRASES)


def _is_damage_type_present(normalized_text):
    return _contains_any(
        normalized_text,
        ("degats physiques", "degats magiques", "degats bruts"),
    )


def _effect_rule_applies(effect_type, normalized_text):
    if effect_type in {
        "PHYSICAL_DAMAGE",
        "MAGIC_DAMAGE",
        "TRUE_DAMAGE",
        "PERCENT_MAX_HEALTH_DAMAGE",
        "PERCENT_CURRENT_HEALTH_DAMAGE",
        "MISSING_HEALTH_DAMAGE",
    }:
        return (
            _has_damage_action(normalized_text)
            and not _has_defensive_damage_context(normalized_text)
        )

    if effect_type == "DAMAGE_TYPE_UNRESOLVED":
        return (
            _has_damage_action(normalized_text)
            and not _is_damage_type_present(normalized_text)
            and not _has_defensive_damage_context(normalized_text)
        )

    if effect_type == "EXECUTE":
        return _contains_any(
            normalized_text,
            ("ennemi", "ennemis", "champion", "champions", "cible", "monstre"),
        )

    if effect_type == "SHIELD":
        return (
            "bouclier" in normalized_text
            and _contains_any(normalized_text, SHIELD_GRANT_OR_USE_PHRASES)
            and not _contains_any(normalized_text, SHIELD_NEGATIVE_CONTEXT_PHRASES)
        )

    if effect_type == "HEAL":
        return _contains_any(
            normalized_text,
            ("soigne", "soignez", "recupere", "recuperez", "rend des pv"),
        )

    if effect_type == "TRANSFORMATION":
        return _contains_any(normalized_text, TRANSFORMATION_EVIDENCE_PHRASES)

    if effect_type == "REVEAL":
        return _contains_any(
            normalized_text,
            ("ennemi", "ennemis", "champion", "champions", "cible", "zone"),
        )

    return True


def _effect_key(effect):
    return (
        effect.get("effect_type"),
        effect.get("source_field"),
        effect.get("evidence_text"),
    )


def _add_effect(effects, effect):
    key = _effect_key(effect)
    if key in {_effect_key(existing) for existing in effects}:
        return
    effects.append(effect)


def _split_semantic_fragments(text):
    fragments = re.split(r"[\n.;!?]+", text or "")
    return [_collapse_spaces(fragment) for fragment in fragments if _collapse_spaces(fragment)]


def _split_semantic_clauses(fragment):
    clauses = re.split(
        r"\s+(?:et|puis|ainsi\s+que|mais|tout\s+en)\s+|,\s*",
        fragment or "",
        flags=re.IGNORECASE,
    )
    return [_collapse_spaces(clause) for clause in clauses if _collapse_spaces(clause)]


def _candidate_semantic_units(text, clause_local):
    if not clause_local:
        return [text]

    units = []
    for fragment in _split_semantic_fragments(text):
        clauses = _split_semantic_clauses(fragment)
        units.extend(clauses or [fragment])
    return units or [text]


def _contains_matched_semantic_text(text, normalized_matched_texts):
    normalized_text = _normalize_text(text)
    return any(
        matched_text in normalized_text for matched_text in normalized_matched_texts
    )


def _unresolved_semantic_clauses(fragment, normalized_matched_texts):
    if not _contains_matched_semantic_text(fragment, normalized_matched_texts):
        return [fragment]

    clauses = _split_semantic_clauses(fragment)
    if len(clauses) <= 1:
        return []

    return [
        clause
        for clause in clauses
        if not _contains_matched_semantic_text(clause, normalized_matched_texts)
    ]


def _section_partial_parse_record(
    section,
    section_effects,
    ddragon_version,
    rejected_matched_texts=None,
):
    text = section.get("text")
    if not text:
        return None, "NO_EFFECT_TEXT"

    rejected_matched_texts = list(rejected_matched_texts or [])
    matched_texts = [
        effect.get("matched_text")
        for effect in section_effects
        if effect.get("matched_text")
    ]
    normalized_matched_texts = [
        _normalize_text(text) for text in matched_texts if _normalize_text(text)
    ]
    normalized_rejected_texts = [
        _normalize_text(text)
        for text in rejected_matched_texts
        if _normalize_text(text)
    ]

    if not section_effects:
        return (
            {
                "kind": UNPARSED_EFFECT_TEXT,
                "section_type": section.get("section_type", UNKNOWN),
                "section_name": section.get("section_name", UNKNOWN),
                "text": text,
                "unparsed_fragments": [text],
                "rejected_matched_texts": rejected_matched_texts,
                "source": "DDRAGON_CHAMPION_TEXT",
                "ddragon_version": ddragon_version,
            },
            "COMPLETELY_UNPARSED",
        )

    unmatched_fragments = []
    partial_fragment_details = []
    for fragment in _split_semantic_fragments(text):
        matched_in_fragment = _contains_matched_semantic_text(
            fragment,
            normalized_matched_texts,
        )
        unresolved_clauses = _unresolved_semantic_clauses(
            fragment,
            normalized_matched_texts,
        )
        for clause in _split_semantic_clauses(fragment):
            if (
                _contains_matched_semantic_text(clause, normalized_rejected_texts)
                and clause not in unresolved_clauses
            ):
                unresolved_clauses.append(clause)
        if unresolved_clauses:
            unmatched_fragments.extend(unresolved_clauses)
            partial_fragment_details.append(
                {
                    "fragment": fragment,
                    "matched_in_fragment": matched_in_fragment,
                    "unresolved_clauses": unresolved_clauses,
                }
            )

    if unmatched_fragments:
        return (
            {
                "kind": PARTIALLY_PARSED_EFFECT_TEXT,
                "section_type": section.get("section_type", UNKNOWN),
                "section_name": section.get("section_name", UNKNOWN),
                "text": text,
                "unparsed_fragments": unmatched_fragments,
                "partial_fragment_details": partial_fragment_details,
                "matched_effect_types": [
                    effect["effect_type"] for effect in section_effects
                ],
                "matched_texts": matched_texts,
                "rejected_matched_texts": rejected_matched_texts,
                "source": "DDRAGON_CHAMPION_TEXT",
                "ddragon_version": ddragon_version,
            },
            "PARTIALLY_PARSED",
        )

    return None, "FULLY_PARSED"


def extract_semantic_effects(sections, ddragon_version, locale=DEFAULT_LOCALE):
    parser_status = semantic_parser_status(locale)
    effects = []
    unparsed = []
    section_parse_counts = Counter()
    section_parse_details = []

    if parser_status != SEMANTIC_PARSER_SUPPORTED:
        for section in sections:
            if not section.get("text"):
                continue
            section_parse_counts["unsupported_locale_sections"] += 1
            unparsed.append(
                {
                    "kind": UNPARSED_EFFECT_TEXT,
                    "reason": SEMANTIC_PARSER_UNSUPPORTED_LOCALE,
                    "section_type": section.get("section_type", UNKNOWN),
                    "section_name": section.get("section_name", UNKNOWN),
                    "text": section.get("text"),
                    "unparsed_fragments": [section.get("text")],
                    "source": "DDRAGON_CHAMPION_TEXT",
                    "ddragon_version": ddragon_version,
                }
            )
        return effects, unparsed, {
            "status": parser_status,
            "section_counts": dict(section_parse_counts),
            "section_parse_details": section_parse_details,
        }

    for section in sections:
        text = section.get("text")
        if not text:
            continue
        section_effects = []
        rejected_matched_texts = []

        for effect_type, phrases in SEMANTIC_RULES:
            clause_local = effect_type in CLAUSE_LOCAL_EFFECT_TYPES
            for unit_text in _candidate_semantic_units(text, clause_local):
                normalized_unit = _normalize_text(unit_text)
                phrase_matches = [
                    phrase
                    for phrase in phrases
                    if _normalize_text(phrase) in normalized_unit
                ]
                if not phrase_matches:
                    continue
                if not _effect_rule_applies(effect_type, normalized_unit):
                    if effect_type != "DAMAGE_TYPE_UNRESOLVED":
                        rejected_matched_texts.extend(phrase_matches)
                    continue
                effect = {
                    "effect_type": effect_type,
                    "source": "DDRAGON_CHAMPION_TEXT",
                    "source_field": section.get("section_type", UNKNOWN),
                    "section_name": section.get("section_name", UNKNOWN),
                    "evidence_text": unit_text,
                    "matched_text": phrase_matches[0],
                    "confidence": "DESCRIPTION_EXPLICIT",
                    "ddragon_version": ddragon_version,
                }
                before_count = len(effects)
                _add_effect(effects, effect)
                if len(effects) > before_count:
                    section_effects.append(effect)

        parse_record, parse_status = _section_partial_parse_record(
            section,
            section_effects,
            ddragon_version,
            rejected_matched_texts,
        )
        section_parse_counts[parse_status.lower() + "_sections"] += 1
        section_parse_details.append(
            {
                "section_type": section.get("section_type", UNKNOWN),
                "section_name": section.get("section_name", UNKNOWN),
                "text": text,
                "parse_status": parse_status,
                "matched_effect_types": [
                    effect["effect_type"] for effect in section_effects
                ],
                "rejected_matched_texts": rejected_matched_texts,
                "unresolved_text": parse_record.get("unparsed_fragments", [])
                if parse_record
                else [],
            }
        )
        if parse_record:
            unparsed.append(parse_record)

    return effects, unparsed, {
        "status": parser_status,
        "section_counts": dict(section_parse_counts),
        "section_parse_details": section_parse_details,
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


def _load_champion_summary(ddragon_version, locale):
    url = f"{DDRAGON_BASE_URL}/cdn/{ddragon_version}/data/{locale}/champion.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json().get("data", {})


def _load_champion_detail(ddragon_version, locale, champion_id):
    url = (
        f"{DDRAGON_BASE_URL}/cdn/{ddragon_version}/data/"
        f"{locale}/champion/{champion_id}.json"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json().get("data", {})
    return data.get(champion_id) or next(iter(data.values()), {})


def normalize_champion_stats(raw_stats, ddragon_version):
    normalized = []
    for source_field, value in (raw_stats or {}).items():
        canonical, unit = STAT_FIELD_MAP.get(source_field, (UNKNOWN, UNKNOWN))
        normalized.append(
            {
                "stat": canonical,
                "value": value,
                "unit": unit,
                "source": "DDRAGON_CHAMPION_STATS",
                "source_field": source_field,
                "confidence": "STRUCTURED"
                if canonical != UNKNOWN
                else "UNKNOWN",
                "ddragon_version": ddragon_version,
            }
        )
    return normalized


def _field_or_not_exposed(raw, key):
    if isinstance(raw, dict) and key in raw:
        return raw.get(key)
    return NOT_EXPOSED


def _parse_champion_key(raw_key):
    try:
        return int(raw_key)
    except (TypeError, ValueError):
        return UNKNOWN


def _placeholder_records_for_field(spell, field_name, text):
    if not text:
        return [], text or ""

    effect_burn = spell.get("effectBurn") or []
    vars_entries = spell.get("vars") or []
    vars_by_key = {
        str(entry.get("key")): entry for entry in vars_entries if entry.get("key")
    }

    records = []

    def annotate(match):
        placeholder = match.group(0)
        key = _collapse_spaces(match.group(1)).replace(" ", "")
        normalized_key = key.lower()
        record = {
            "field": field_name,
            "placeholder": placeholder,
            "key": key,
            "resolved_value": None,
            "source_field": None,
            "resolution_status": "UNKNOWN_PLACEHOLDER",
        }

        effect_match = re.fullmatch(r"e(\d+)", normalized_key)
        var_match = re.fullmatch(r"[af](\d+)", normalized_key)

        if effect_match:
            index = int(effect_match.group(1))
            if index < len(effect_burn) and effect_burn[index] not in (None, ""):
                record.update(
                    {
                        "resolved_value": effect_burn[index],
                        "source_field": f"effectBurn[{index}]",
                        "resolution_status": "RESOLVED_EFFECT_BURN",
                    }
                )
            else:
                record.update(
                    {
                        "source_field": f"effectBurn[{index}]",
                        "resolution_status": "UNRESOLVED_EFFECT_BURN",
                    }
                )
        elif var_match:
            entry = vars_by_key.get(normalized_key)
            if entry is not None:
                record.update(
                    {
                        "resolved_value": dict(entry),
                        "source_field": f"vars[{normalized_key}]",
                        "resolution_status": "RESOLVED_VAR",
                    }
                )
            else:
                record.update(
                    {
                        "source_field": f"vars[{normalized_key}]",
                        "resolution_status": "UNRESOLVED_VAR",
                    }
                )

        records.append(record)
        if record["resolution_status"] == "RESOLVED_EFFECT_BURN":
            return f"{placeholder}[{record['source_field']}={record['resolved_value']}]"
        if record["resolution_status"] == "RESOLVED_VAR":
            return f"{placeholder}[{record['source_field']}={record['resolved_value']}]"
        return f"{placeholder}[{record['resolution_status']}]"

    annotated = re.sub(r"\{\{\s*([^{}]+?)\s*\}\}", annotate, text)
    return records, annotated


def resolve_spell_placeholders(raw_spell):
    records = []
    annotated_fields = {}
    for field_name in ("description", "tooltip", "resource"):
        field_records, annotated = _placeholder_records_for_field(
            raw_spell,
            field_name,
            raw_spell.get(field_name),
        )
        records.extend(field_records)
        annotated_fields[f"annotated_{field_name}"] = annotated
    return records, annotated_fields


def extract_formula_fragments(raw_spell, placeholder_records, ddragon_version):
    fragments = []
    effect = raw_spell.get("effect") or []
    effect_burn = raw_spell.get("effectBurn") or []

    for index, values in enumerate(effect):
        if index == 0 or values in (None, "", []):
            continue
        fragments.append(
            {
                "fragment_type": "RANK_VALUE_ARRAY",
                "values": values,
                "source_field": f"effect[{index}]",
                "effect_burn": effect_burn[index]
                if index < len(effect_burn)
                else NOT_EXPOSED,
                "status": "FORMULA_FRAGMENT_STRUCTURED",
                "ddragon_version": ddragon_version,
            }
        )

    for var in raw_spell.get("vars") or []:
        fragments.append(
            {
                "fragment_type": "VAR_COEFFICIENT",
                "key": var.get("key", UNKNOWN),
                "link": var.get("link", UNKNOWN),
                "coeff": var.get("coeff", UNKNOWN),
                "raw": dict(var),
                "source_field": "vars",
                "status": "FORMULA_FRAGMENT_STRUCTURED",
                "ddragon_version": ddragon_version,
            }
        )

    unresolved_placeholders = [
        record
        for record in placeholder_records
        if not record["resolution_status"].startswith("RESOLVED_")
    ]
    for record in unresolved_placeholders:
        fragments.append(
            {
                "fragment_type": "UNRESOLVED_PLACEHOLDER",
                "placeholder": record["placeholder"],
                "source_field": record["field"],
                "status": FORMULA_INCOMPLETE,
                "ddragon_version": ddragon_version,
            }
        )

    if unresolved_placeholders:
        formula_status = FORMULA_INCOMPLETE
    elif fragments:
        formula_status = "FORMULA_FRAGMENTS_AVAILABLE"
    else:
        formula_status = "FORMULA_NOT_EXPOSED"

    return {
        "status": formula_status,
        "fragments": fragments,
    }


def _spell_sections(raw_spell):
    sections = []
    description = clean_description(raw_spell.get("description"))
    tooltip = clean_description(raw_spell.get("tooltip"))
    if description:
        sections.append(
            {
                "section_type": "SPELL_DESCRIPTION",
                "section_name": raw_spell.get("name", UNKNOWN),
                "text": description,
            }
        )
    if tooltip and tooltip != description:
        sections.append(
            {
                "section_type": "SPELL_TOOLTIP",
                "section_name": raw_spell.get("name", UNKNOWN),
                "text": tooltip,
            }
        )
    return sections


def build_passive_record(raw_passive, ddragon_version, locale):
    raw_passive = raw_passive or {}
    clean = clean_description(raw_passive.get("description"))
    sections = []
    if clean:
        sections.append(
            {
                "section_type": "PASSIVE_DESCRIPTION",
                "section_name": raw_passive.get("name", UNKNOWN),
                "text": clean,
            }
        )
    effects, unparsed, semantic_parse = extract_semantic_effects(
        sections,
        ddragon_version,
        locale,
    )
    return {
        "name": raw_passive.get("name", UNKNOWN),
        "raw_description": raw_passive.get("description", ""),
        "clean_description": clean,
        "image": raw_passive.get("image", NOT_EXPOSED),
        "source": "DDRAGON_CHAMPION_PASSIVE",
        "ddragon_version": ddragon_version,
        "semantic_parser": {
            "status": semantic_parse["status"],
            "supported_locales": sorted(SUPPORTED_SEMANTIC_LOCALES),
        },
        "effects": effects,
        "unparsed_effect_text": unparsed,
        "semantic_parse_summary": semantic_parse["section_counts"],
        "semantic_parse_details": semantic_parse["section_parse_details"],
        "raw": dict(raw_passive),
    }


def build_spell_records(raw_spells, ddragon_version, locale):
    raw_spells = list(raw_spells or [])
    spell_count = len(raw_spells)
    records = []

    for index, raw_spell in enumerate(raw_spells):
        raw_spell = raw_spell or {}
        slot = SLOT_BY_INDEX.get(index) if spell_count == 4 else UNKNOWN
        slot_source = (
            "DDRAGON_ARRAY_ORDER"
            if spell_count == 4 and index in SLOT_BY_INDEX
            else "UNSAFE_UNUSUAL_SPELL_COUNT"
        )
        placeholder_records, annotated_fields = resolve_spell_placeholders(raw_spell)
        formula = extract_formula_fragments(
            raw_spell,
            placeholder_records,
            ddragon_version,
        )
        sections = _spell_sections(raw_spell)
        effects, unparsed, semantic_parse = extract_semantic_effects(
            sections,
            ddragon_version,
            locale,
        )

        known_fields = {
            "id",
            "name",
            "description",
            "tooltip",
            "maxrank",
            "cooldown",
            "cooldownBurn",
            "cost",
            "costBurn",
            "costType",
            "resource",
            "range",
            "rangeBurn",
            "effect",
            "effectBurn",
            "vars",
            "image",
        }
        extra_fields = {
            key: value for key, value in raw_spell.items() if key not in known_fields
        }

        records.append(
            {
                "spell_array_index": index,
                "inferred_slot": slot,
                "slot_source": slot_source,
                "spell_id": raw_spell.get("id", UNKNOWN),
                "name": raw_spell.get("name", UNKNOWN),
                "raw_description": raw_spell.get("description", ""),
                "clean_description": clean_description(raw_spell.get("description")),
                "raw_tooltip": raw_spell.get("tooltip", ""),
                "clean_tooltip": clean_description(raw_spell.get("tooltip")),
                "max_rank": _field_or_not_exposed(raw_spell, "maxrank"),
                "cooldown": _field_or_not_exposed(raw_spell, "cooldown"),
                "cooldown_burn": _field_or_not_exposed(raw_spell, "cooldownBurn"),
                "cost": _field_or_not_exposed(raw_spell, "cost"),
                "cost_burn": _field_or_not_exposed(raw_spell, "costBurn"),
                "cost_type": _field_or_not_exposed(raw_spell, "costType"),
                "resource": _field_or_not_exposed(raw_spell, "resource"),
                "range": _field_or_not_exposed(raw_spell, "range"),
                "range_burn": _field_or_not_exposed(raw_spell, "rangeBurn"),
                "effect": _field_or_not_exposed(raw_spell, "effect"),
                "effect_burn": _field_or_not_exposed(raw_spell, "effectBurn"),
                "vars": _field_or_not_exposed(raw_spell, "vars"),
                "image": _field_or_not_exposed(raw_spell, "image"),
                "extra_fields": extra_fields,
                "placeholder_resolution": placeholder_records,
                "annotated_description": annotated_fields["annotated_description"],
                "annotated_tooltip": annotated_fields["annotated_tooltip"],
                "annotated_resource": annotated_fields["annotated_resource"],
                "formula": formula,
                "semantic_parser": {
                    "status": semantic_parse["status"],
                    "supported_locales": sorted(SUPPORTED_SEMANTIC_LOCALES),
                },
                "effects": effects,
                "unparsed_effect_text": unparsed,
                "semantic_parse_summary": semantic_parse["section_counts"],
                "semantic_parse_details": semantic_parse["section_parse_details"],
                "raw_spell": dict(raw_spell),
                "source": "DDRAGON_CHAMPION_SPELL",
                "ddragon_version": ddragon_version,
            }
        )
    return records


def _combined_text_for_complexity(record):
    texts = [record["passive"].get("clean_description", "")]
    for spell in record["spells"]:
        texts.append(spell.get("clean_description", ""))
        texts.append(spell.get("clean_tooltip", ""))
    return _normalize_text("\n".join(texts))


COPIED_OR_DYNAMIC_ABILITY_RULES = [
    ("copie", "CONFIRMED_COMPLEX_MECHANIC", "copy wording in ability text"),
    ("copier", "CONFIRMED_COMPLEX_MECHANIC", "copy wording in ability text"),
    (
        "possession",
        "CONFIRMED_COMPLEX_MECHANIC",
        "possession wording in ability text",
    ),
    (
        "prend possession",
        "CONFIRMED_COMPLEX_MECHANIC",
        "possession wording in ability text",
    ),
    (
        "vole une competence",
        "CONFIRMED_COMPLEX_MECHANIC",
        "stolen-ability wording in ability text",
    ),
]

PHASE2B1_B_COMPLEXITY_PHRASE_RULES = {
    "ALTERNATE_FORM_POSSIBLE": [
        (
            "change de forme",
            "CONFIRMED_COMPLEX_MECHANIC",
            "Phase 2B1-B explicit form-change evidence",
        ),
        (
            "changer de forme",
            "CONFIRMED_COMPLEX_MECHANIC",
            "Phase 2B1-B explicit form-change evidence",
        ),
        (
            "transforme",
            "UNRESOLVED",
            "Phase 2B1-B keyword evidence; Phase 2B1-C audits transformed entity",
        ),
        (
            "se transforme",
            "CONFIRMED_COMPLEX_MECHANIC",
            "Phase 2B1-B self-transformation evidence",
        ),
        (
            "forme de dragon",
            "PLAUSIBLE_BUT_UNDERMODELED",
            "Phase 2B1-B named form evidence",
        ),
        (
            "forme dragon",
            "PLAUSIBLE_BUT_UNDERMODELED",
            "Phase 2B1-B named form evidence",
        ),
        (
            "forme humaine",
            "PLAUSIBLE_BUT_UNDERMODELED",
            "Phase 2B1-B named form evidence",
        ),
        (
            "forme arachneenne",
            "PLAUSIBLE_BUT_UNDERMODELED",
            "Phase 2B1-B named form evidence",
        ),
        (
            "forme de cougar",
            "PLAUSIBLE_BUT_UNDERMODELED",
            "Phase 2B1-B named form evidence",
        ),
        (
            "posture",
            "PLAUSIBLE_BUT_UNDERMODELED",
            "Phase 2B1-B posture evidence",
        ),
    ],
    "COPIED_OR_DYNAMIC_ABILITY": COPIED_OR_DYNAMIC_ABILITY_RULES,
}


def _iter_complexity_text_sources(record):
    passive = record.get("passive") or {}
    if passive.get("clean_description"):
        yield {
            "source_field": "PASSIVE_DESCRIPTION",
            "section_name": passive.get("name", UNKNOWN),
            "evidence_text": passive.get("clean_description", ""),
        }
    for spell in record.get("spells", []):
        if spell.get("clean_description"):
            yield {
                "source_field": "SPELL_DESCRIPTION",
                "section_name": spell.get("name", UNKNOWN),
                "spell_id": spell.get("spell_id", UNKNOWN),
                "slot": spell.get("inferred_slot", UNKNOWN),
                "evidence_text": spell.get("clean_description", ""),
            }
        if spell.get("clean_tooltip"):
            yield {
                "source_field": "SPELL_TOOLTIP",
                "section_name": spell.get("name", UNKNOWN),
                "spell_id": spell.get("spell_id", UNKNOWN),
                "slot": spell.get("inferred_slot", UNKNOWN),
                "evidence_text": spell.get("clean_tooltip", ""),
            }


def _complexity_units(source):
    text = source["evidence_text"]
    for fragment in _split_semantic_fragments(text):
        clauses = _split_semantic_clauses(fragment)
        for clause in clauses or [fragment]:
            unit = dict(source)
            unit["evidence_text"] = clause
            unit["context_text"] = text
            yield unit
    context_unit = dict(source)
    context_unit["context_text"] = text
    yield context_unit


def _record_identity_terms(record):
    terms = []
    if record:
        for candidate in (record.get("name"), record.get("champion_id")):
            normalized = _normalize_text(candidate)
            if len(normalized) >= 3 and normalized not in terms:
                terms.append(normalized)
    return terms


def _has_record_identity(normalized_text, record):
    return any(term in normalized_text for term in _record_identity_terms(record))


def _has_explicit_champion_self_subject(normalized_text, context_normalized, record):
    if _contains_any(normalized_text, ("le champion", "la championne")):
        return True
    if _has_record_identity(normalized_text, record):
        return True
    if _has_record_identity(context_normalized, record) and _contains_any(
        normalized_text,
        (
            "sa prochaine competence le transforme",
            "sa prochaine competence la transforme",
            "elle prend alors sa veritable forme",
            "il prend alors sa veritable forme",
        ),
    ):
        return True
    return False


def _described_transformed_entity(normalized_text, context_normalized="", record=None):
    for phrase in NON_SELF_TRANSFORMATION_SUBJECT_PHRASES:
        if _normalize_text(phrase) in normalized_text:
            return (
                "non_champion_target_or_summoned_entity",
                "FALSE_POSITIVE",
                phrase,
                "self-transformation grammar belongs to a target or summoned entity, not the champion",
            )

    for phrase in GENERIC_TRANSFORMATION_OBJECT_PHRASES:
        if _normalize_text(phrase) in normalized_text:
            return (
                "generic_transformed_mechanic_or_object",
                "FALSE_POSITIVE",
                phrase,
                "transformed entity is not the champion's own form or kit state",
            )

    if _contains_any(normalized_text, ("change de forme", "changer de forme")):
        if not _has_explicit_champion_self_subject(
            normalized_text, context_normalized, record
        ):
            return (
                "generic_transformation_unknown_entity",
                "UNRESOLVED",
                "change de forme",
                "form-change wording lacks local champion ownership evidence",
            )
        return (
            "champion_self_form_or_kit_state",
            "CONFIRMED_COMPLEX_MECHANIC",
            "change de forme",
            "explicit champion form-change wording",
        )

    if _contains_any(normalized_text, ("se transforme",)):
        if not _has_explicit_champion_self_subject(
            normalized_text, context_normalized, record
        ):
            return (
                "generic_transformation_unknown_entity",
                "UNRESOLVED",
                "se transforme",
                "self-transformation wording lacks local champion ownership evidence",
            )
        return (
            "champion_self_form_or_state",
            "CONFIRMED_COMPLEX_MECHANIC",
            "se transforme",
            "self-transformation wording identifies the champion as the subject",
        )

    if _contains_any(normalized_text, ("le transforme en", "la transforme en")):
        if not _contains_any(
            normalized_text,
            (
                "sa prochaine competence le transforme",
                "sa prochaine competence la transforme",
            ),
        ):
            return (
                "generic_transformation_unknown_entity",
                "UNRESOLVED",
                "le/la transforme en",
                "pronoun transformation wording does not establish champion self-form ownership",
            )
        return (
            "champion_self_form_or_state",
            "CONFIRMED_COMPLEX_MECHANIC",
            "le/la transforme en",
            "ability text indicates the champion is transformed into another form",
        )

    if _contains_any(
        normalized_text,
        (
            "passe en forme",
            "passe sous forme",
            "activer sa forme",
            "active sa forme",
        ),
    ):
        if not _has_explicit_champion_self_subject(
            normalized_text, context_normalized, record
        ):
            return (
                "generic_transformation_unknown_entity",
                "UNRESOLVED",
                "owned named form",
                "owned-form wording lacks local champion ownership evidence",
            )
        return (
            "champion_owned_named_form",
            "CONFIRMED_COMPLEX_MECHANIC",
            "owned named form",
            "wording indicates the champion enters or activates their own named form",
        )

    if _contains_any(normalized_text, ("forme veritable", "veritable forme")):
        true_form_entry_phrases = (
            "prend sa veritable forme",
            "prend alors sa veritable forme",
            "active sa forme veritable",
            "activer sa forme veritable",
            "active sa veritable forme",
            "activer sa veritable forme",
        )
        if not (
            _has_explicit_champion_self_subject(
                normalized_text, context_normalized, record
            )
            and _contains_any(normalized_text, true_form_entry_phrases)
        ):
            return (
                "generic_transformation_unknown_entity",
                "UNRESOLVED",
                "true form",
                "true-form wording does not show the champion entering that form",
            )
        return (
            "champion_owned_named_form",
            "CONFIRMED_COMPLEX_MECHANIC",
            "owned named form",
            "wording indicates the champion enters or activates their own named form",
        )

    named_forms = [
        phrase
        for phrase in ALTERNATE_FORM_NAMED_FORM_PHRASES
        if _normalize_text(phrase) in normalized_text
    ]
    context_named_forms = [
        phrase
        for phrase in ALTERNATE_FORM_NAMED_FORM_PHRASES
        if _normalize_text(phrase) in context_normalized
    ]
    if (
        len(set(named_forms + context_named_forms)) >= 2
        or (
            "forme de dragon" in named_forms
            and _has_explicit_champion_self_subject(
                normalized_text, context_normalized, record
            )
        )
        or (
            "forme de cougar" in named_forms
            and _has_explicit_champion_self_subject(
                normalized_text, context_normalized, record
            )
        )
        or (
            "forme de couguar" in named_forms
            and _has_explicit_champion_self_subject(
                normalized_text, context_normalized, record
            )
        )
        or (
            "forme couguar" in named_forms
            and _has_explicit_champion_self_subject(
                normalized_text, context_normalized, record
            )
        )
    ):
        return (
            "champion_named_form_set",
            "PLAUSIBLE_BUT_UNDERMODELED",
            ", ".join(sorted(set(named_forms + context_named_forms))),
            "named champion form wording suggests an alternate form kit/state",
        )

    if _contains_any(normalized_text, ALTERNATE_FORM_STANCE_PHRASES):
        if not _has_explicit_champion_self_subject(
            normalized_text, context_normalized, record
        ):
            return (
                "generic_transformation_unknown_entity",
                "UNRESOLVED",
                "posture",
                "stance/posture wording lacks local champion ownership evidence",
            )
        return (
            "champion_combat_stance_or_state",
            "PLAUSIBLE_BUT_UNDERMODELED",
            "posture",
            "stance/posture wording may describe the champion's combat state",
        )

    if "transforme" in normalized_text:
        return (
            "generic_transformation_unknown_entity",
            "UNRESOLVED",
            "transforme",
            "generic transformation wording does not establish champion self-form ownership",
        )

    return (
        UNKNOWN,
        "UNRESOLVED",
        UNKNOWN,
        "no transformation entity could be identified",
    )


def _scan_alternate_form_evidence(record):
    evidence = []
    seen = set()
    for source in _iter_complexity_text_sources(record):
        for unit in _complexity_units(source):
            normalized = _normalize_text(unit["evidence_text"])
            context_normalized = _normalize_text(unit.get("context_text", ""))
            if not (
                _contains_any(normalized, ALTERNATE_FORM_SELF_PHRASES)
                or _contains_any(normalized, ALTERNATE_FORM_NAMED_FORM_PHRASES)
                or _contains_any(normalized, ALTERNATE_FORM_STANCE_PHRASES)
                or _contains_any(context_normalized, ALTERNATE_FORM_NAMED_FORM_PHRASES)
            ):
                continue
            entity, classification, matched_text, why = _described_transformed_entity(
                normalized,
                context_normalized,
                record,
            )
            if classification == "FALSE_POSITIVE":
                continue
            if classification == "UNRESOLVED":
                continue
            if entity == "generic_transformation_unknown_entity":
                continue
            key = (
                "ALTERNATE_FORM_POSSIBLE",
                unit["source_field"],
                unit.get("spell_id"),
                unit["section_name"],
                matched_text,
                unit["evidence_text"],
            )
            if key in seen:
                continue
            seen.add(key)
            evidence.append(
                {
                    "flag": "ALTERNATE_FORM_POSSIBLE",
                    "evidence_classification": classification,
                    "source_field": unit["source_field"],
                    "section_name": unit["section_name"],
                    "spell_id": unit.get("spell_id", NOT_EXPOSED),
                    "slot": unit.get("slot", NOT_EXPOSED),
                    "matched_text": matched_text,
                    "evidence_text": unit["evidence_text"],
                    "entity_or_state": entity,
                    "why": why,
                    "ddragon_version": record["ddragon_version"],
                }
            )
    return evidence


def _scan_complexity_phrase_evidence(record, phrase_rules):
    evidence = []
    seen = set()
    for flag, rules in phrase_rules.items():
        for source in _iter_complexity_text_sources(record):
            normalized = _normalize_text(source["evidence_text"])
            for phrase, classification, why in rules:
                normalized_phrase = _normalize_text(phrase)
                if normalized_phrase not in normalized:
                    continue
                key = (
                    flag,
                    source["source_field"],
                    source.get("spell_id"),
                    source["section_name"],
                    normalized_phrase,
                    source["evidence_text"],
                )
                if key in seen:
                    continue
                seen.add(key)
                entity_or_state = "copied_or_dynamic_ability"
                classification_to_use = classification
                why_to_use = why
                if flag == "ALTERNATE_FORM_POSSIBLE":
                    (
                        entity_or_state,
                        classification_to_use,
                        _matched_entity_text,
                        why_to_use,
                    ) = _described_transformed_entity(
                        normalized,
                        normalized,
                        record,
                    )
                evidence.append(
                    {
                        "flag": flag,
                        "evidence_classification": classification_to_use,
                        "source_field": source["source_field"],
                        "section_name": source["section_name"],
                        "spell_id": source.get("spell_id", NOT_EXPOSED),
                        "slot": source.get("slot", NOT_EXPOSED),
                        "matched_text": phrase,
                        "evidence_text": source["evidence_text"],
                        "entity_or_state": entity_or_state,
                        "why": why_to_use,
                        "ddragon_version": record["ddragon_version"],
                    }
                )
    return evidence


def _complexity_review_classification(evidence):
    classifications = {item["evidence_classification"] for item in evidence}
    if "FALSE_POSITIVE" in classifications and len(classifications) == 1:
        return "FALSE_POSITIVE"
    if "CONFIRMED_COMPLEX_MECHANIC" in classifications:
        return "CONFIRMED_COMPLEX_MECHANIC"
    if "PLAUSIBLE_BUT_UNDERMODELED" in classifications:
        return "PLAUSIBLE_BUT_UNDERMODELED"
    if "FALSE_POSITIVE" in classifications:
        return "FALSE_POSITIVE"
    return "UNRESOLVED"


def audit_complexity(record):
    flags = []
    spell_count = len(record["spells"])
    evidence = []

    if spell_count != 4:
        flags.append("EXTRA_ABILITY_STRUCTURE")
        evidence.append(
            {
                "flag": "EXTRA_ABILITY_STRUCTURE",
                "evidence_classification": "CONFIRMED_COMPLEX_MECHANIC",
                "source_field": "DDRAGON_SPELL_ARRAY",
                "section_name": "spell_count",
                "spell_id": NOT_EXPOSED,
                "slot": NOT_EXPOSED,
                "matched_text": f"{spell_count} spells",
                "evidence_text": f"Data Dragon exposes {spell_count} spells",
                "entity_or_state": "spell_array_structure",
                "why": "non-4-spell structure makes Q/W/E/R inference unsafe",
                "ddragon_version": record["ddragon_version"],
            }
        )

    alternate_form_evidence = _scan_alternate_form_evidence(record)
    evidence.extend(alternate_form_evidence)
    flags.extend(item["flag"] for item in alternate_form_evidence)

    copied_dynamic_evidence = _scan_complexity_phrase_evidence(
        record,
        {"COPIED_OR_DYNAMIC_ABILITY": COPIED_OR_DYNAMIC_ABILITY_RULES},
    )
    evidence.extend(copied_dynamic_evidence)
    flags.extend(item["flag"] for item in copied_dynamic_evidence)

    if record["metadata_warnings"]:
        flags.append("DATA_DRAGON_KIT_INCOMPLETE")
        evidence.append(
            {
                "flag": "DATA_DRAGON_KIT_INCOMPLETE",
                "evidence_classification": "UNRESOLVED",
                "source_field": "DDRAGON_CHAMPION_DETAIL",
                "section_name": "metadata_warnings",
                "spell_id": NOT_EXPOSED,
                "slot": NOT_EXPOSED,
                "matched_text": ", ".join(record["metadata_warnings"]),
                "evidence_text": f"metadata_warnings={record['metadata_warnings']}",
                "entity_or_state": "missing_ddragon_detail",
                "why": "missing Data Dragon fields make the kit incomplete",
                "ddragon_version": record["ddragon_version"],
            }
        )
    if any(flag != "STANDARD_KIT" for flag in flags):
        flags.append("COMPLEX_KIT_UNDERMODELED")
        evidence.append(
            {
                "flag": "COMPLEX_KIT_UNDERMODELED",
                "evidence_classification": _complexity_review_classification(
                    evidence
                ),
                "source_field": "DERIVED_COMPLEXITY_AUDIT",
                "section_name": "non_standard_flags",
                "spell_id": NOT_EXPOSED,
                "slot": NOT_EXPOSED,
                "matched_text": ", ".join(sorted(set(flags))),
                "evidence_text": "Generic factual flags indicate under-modeled kit semantics.",
                "entity_or_state": "aggregate_non_standard_complexity",
                "why": "aggregate marker for consumers; not champion-specific logic",
                "ddragon_version": record["ddragon_version"],
            }
        )
    if not flags:
        flags.append("STANDARD_KIT")
    return {
        "flags": sorted(set(flags)),
        "evidence": evidence,
    }


def classify_complexity(record):
    return audit_complexity(record)["flags"]


def _phase2b1_b_complexity_flags(record):
    flags = []
    spell_count = len(record["spells"])
    text = _combined_text_for_complexity(record)

    if spell_count != 4:
        flags.append("EXTRA_ABILITY_STRUCTURE")
    if _contains_any(
        text,
        (
            "change de forme",
            "changer de forme",
            "transforme",
            "se transforme",
            "forme de dragon",
            "forme dragon",
            "forme humaine",
            "forme arachneenne",
            "forme de cougar",
            "posture",
        ),
    ):
        flags.append("ALTERNATE_FORM_POSSIBLE")
    if _contains_any(
        text,
        (
            "copie",
            "copier",
            "possession",
            "prend possession",
            "vole une competence",
        ),
    ):
        flags.append("COPIED_OR_DYNAMIC_ABILITY")
    if record["metadata_warnings"]:
        flags.append("DATA_DRAGON_KIT_INCOMPLETE")
    if any(flag != "STANDARD_KIT" for flag in flags):
        flags.append("COMPLEX_KIT_UNDERMODELED")
    if not flags:
        flags.append("STANDARD_KIT")
    return sorted(set(flags))


def _phase2b1_b_complexity_evidence(record):
    evidence = []
    spell_count = len(record["spells"])
    if spell_count != 4:
        evidence.append(
            {
                "flag": "EXTRA_ABILITY_STRUCTURE",
                "evidence_classification": "CONFIRMED_COMPLEX_MECHANIC",
                "source_field": "DDRAGON_SPELL_ARRAY",
                "section_name": "spell_count",
                "spell_id": NOT_EXPOSED,
                "slot": NOT_EXPOSED,
                "matched_text": f"{spell_count} spells",
                "evidence_text": f"Data Dragon exposes {spell_count} spells",
                "entity_or_state": "spell_array_structure",
                "why": "Phase 2B1-B non-4-spell structure evidence",
                "ddragon_version": record["ddragon_version"],
            }
        )
    evidence.extend(
        _scan_complexity_phrase_evidence(record, PHASE2B1_B_COMPLEXITY_PHRASE_RULES)
    )
    if record["metadata_warnings"]:
        evidence.append(
            {
                "flag": "DATA_DRAGON_KIT_INCOMPLETE",
                "evidence_classification": "UNRESOLVED",
                "source_field": "DDRAGON_CHAMPION_DETAIL",
                "section_name": "metadata_warnings",
                "spell_id": NOT_EXPOSED,
                "slot": NOT_EXPOSED,
                "matched_text": ", ".join(record["metadata_warnings"]),
                "evidence_text": f"metadata_warnings={record['metadata_warnings']}",
                "entity_or_state": "missing_ddragon_detail",
                "why": "Phase 2B1-B missing Data Dragon fields evidence",
                "ddragon_version": record["ddragon_version"],
            }
        )
    return evidence


def _metadata_warnings(summary_champion, detail_champion):
    warnings = []
    if not detail_champion:
        warnings.append("MISSING_CHAMPION_DETAIL")
    if not (detail_champion or {}).get("passive"):
        warnings.append("MISSING_PASSIVE")
    if "spells" not in (detail_champion or {}):
        warnings.append("MISSING_SPELLS")
    if "stats" not in (detail_champion or summary_champion or {}):
        warnings.append("MISSING_STATS")
    return warnings


def build_champion_record(
    champion_id,
    summary_champion,
    detail_champion,
    version_info,
    locale,
):
    detail_champion = detail_champion or {}
    source_champion = {**(summary_champion or {}), **detail_champion}
    ddragon_version = version_info["resolved_ddragon_version"]
    raw_stats = source_champion.get("stats") or {}
    normalized_stats = normalize_champion_stats(raw_stats, ddragon_version)
    metadata_warnings = _metadata_warnings(summary_champion, detail_champion)
    spells = build_spell_records(source_champion.get("spells") or [], ddragon_version, locale)

    record = {
        "champion_knowledge_version": CHAMPION_KNOWLEDGE_VERSION,
        "requested_game_version": version_info["requested_game_version"],
        "ddragon_version": ddragon_version,
        "version_resolution_status": version_info["resolution_status"],
        "version_fallback_used": version_info["fallback_used"],
        "locale": locale,
        "champion_id": source_champion.get("id", champion_id),
        "champion_key": source_champion.get("key", UNKNOWN),
        "champion_key_int": _parse_champion_key(source_champion.get("key")),
        "name": source_champion.get("name", champion_id),
        "title": source_champion.get("title", ""),
        "tags": source_champion.get("tags", []),
        "partype": source_champion.get("partype", NOT_EXPOSED),
        "info": source_champion.get("info", NOT_EXPOSED),
        "image": source_champion.get("image", NOT_EXPOSED),
        "lore": source_champion.get("lore", NOT_EXPOSED),
        "blurb": source_champion.get("blurb", NOT_EXPOSED),
        "allytips": source_champion.get("allytips", NOT_EXPOSED),
        "enemytips": source_champion.get("enemytips", NOT_EXPOSED),
        "raw_stats": raw_stats,
        "normalized_stats": normalized_stats,
        "passive": build_passive_record(
            source_champion.get("passive") or {},
            ddragon_version,
            locale,
        ),
        "spells": spells,
        "metadata_warnings": metadata_warnings,
        "raw_summary_champion": dict(summary_champion or {}),
        "raw_champion_json": dict(detail_champion or {}),
    }
    complexity_audit = audit_complexity(record)
    record["complexity_flags"] = complexity_audit["flags"]
    record["complexity_evidence"] = complexity_audit["evidence"]
    return record


def build_champion_knowledge_catalog(
    requested_game_version=None,
    locale=DEFAULT_LOCALE,
    raw_champions=None,
    raw_champion_details=None,
    versions=None,
):
    version_info = _resolve_version(requested_game_version, versions=versions)
    ddragon_version = version_info["resolved_ddragon_version"]
    raw_champions = (
        raw_champions
        if raw_champions is not None
        else _load_champion_summary(ddragon_version, locale)
    )
    raw_champion_details = dict(raw_champion_details or {})

    records = {}
    missing_detail_files = []

    for champion_id, summary_champion in sorted(raw_champions.items()):
        detail_champion = raw_champion_details.get(champion_id)
        if detail_champion is None and raw_champion_details:
            missing_detail_files.append(champion_id)
        if detail_champion is None and raw_champion_details == {}:
            try:
                detail_champion = _load_champion_detail(
                    ddragon_version,
                    locale,
                    champion_id,
                )
            except requests.RequestException:
                detail_champion = {}
                missing_detail_files.append(champion_id)
        record = build_champion_record(
            champion_id,
            summary_champion,
            detail_champion,
            version_info,
            locale,
        )
        records[record["champion_id"]] = record

    summary = summarize_champion_knowledge(records, missing_detail_files)
    return {
        "champion_knowledge_version": CHAMPION_KNOWLEDGE_VERSION,
        "requested_game_version": version_info["requested_game_version"],
        "resolved_ddragon_version": ddragon_version,
        "version_resolution_status": version_info["resolution_status"],
        "version_fallback_used": version_info["fallback_used"],
        "locale": locale,
        "records": records,
        "summary": summary,
    }


def _record_has_effect(record, effect_type):
    if any(effect["effect_type"] == effect_type for effect in record["passive"]["effects"]):
        return True
    return any(
        effect["effect_type"] == effect_type
        for spell in record["spells"]
        for effect in spell["effects"]
    )


def _placeholder_family(key):
    normalized = _normalize_text(key)
    if re.fullmatch(r"e\d+", normalized):
        return "effectBurn_index_not_exposed"
    if re.fullmatch(r"[af]\d+", normalized):
        return "var_key_not_exposed"
    if _contains_any(normalized, PLACEHOLDER_DISPLAY_HINTS):
        return "formatting_or_display_placeholder"
    if _contains_any(normalized, PLACEHOLDER_FORMULA_HINTS):
        return "likely_formula_related_but_unresolved"
    if "_" in str(key) or re.search(r"[A-Z]", str(key or "")):
        return "calculated_or_custom_ddragon_placeholder"
    return "unknown"


def _placeholder_example(record, spell, placeholder):
    return {
        "champion_id": record["champion_id"],
        "champion_name": record["name"],
        "spell_id": spell["spell_id"],
        "spell_name": spell["name"],
        "slot": spell["inferred_slot"],
        "field": placeholder["field"],
        "placeholder": placeholder["placeholder"],
        "key": placeholder["key"],
    }


def _complexity_baseline_audit_row(record):
    previous_flags = _phase2b1_b_complexity_flags(record)
    current_flags = record["complexity_flags"]
    current_evidence = list(record.get("complexity_evidence", []))
    baseline_evidence = _phase2b1_b_complexity_evidence(record)
    current_non_standard = [
        flag
        for flag in current_flags
        if flag not in {"STANDARD_KIT", "COMPLEX_KIT_UNDERMODELED"}
    ]

    if current_non_standard:
        review_status = _complexity_review_classification(current_evidence)
    else:
        review_status = "FALSE_POSITIVE"

    return {
        "champion_id": record["champion_id"],
        "champion_name": record["name"],
        "previous_flags": previous_flags,
        "current_flags": current_flags,
        "review_status": review_status,
        "current_evidence": current_evidence,
        "baseline_evidence": baseline_evidence,
    }


def _complexity_flag_audit_row(record, flag):
    evidence = [
        item
        for item in record.get("complexity_evidence", [])
        if item.get("flag") == flag
    ]
    return {
        "champion_id": record["champion_id"],
        "champion_name": record["name"],
        "flag": flag,
        "current_flags": record["complexity_flags"],
        "evidence": evidence,
    }


def summarize_champion_knowledge(records, missing_detail_files=None):
    missing_detail_files = list(missing_detail_files or [])
    stat_counts = Counter()
    unknown_stat_fields = Counter()
    spell_count_distribution = Counter()
    placeholder_status_counts = Counter()
    unknown_placeholder_family_counts = Counter()
    formula_status_counts = Counter()
    formula_fragment_status_counts = Counter()
    semantic_effect_counts = Counter()
    section_parse_counts = Counter()
    complexity_flag_counts = Counter()
    complexity_audit_classification_counts = Counter()
    metadata_warning_counts = Counter()
    unknown_placeholder_keys = {}
    baseline_complexity_audit = []
    current_alternate_form_audit = []
    current_copied_dynamic_audit = []

    champions_with_normalized_stats = 0
    passive_records = 0
    total_spells = 0
    champions_not_normal_4_spell = []
    slot_assignment_uncertain = []

    for record in records.values():
        if record["normalized_stats"]:
            champions_with_normalized_stats += 1
        for stat in record["normalized_stats"]:
            stat_counts[stat["stat"]] += 1
            if stat["stat"] == UNKNOWN:
                unknown_stat_fields[stat["source_field"]] += 1

        if record["passive"]:
            passive_records += 1
            section_parse_counts.update(record["passive"]["semantic_parse_summary"])
            for effect in record["passive"]["effects"]:
                semantic_effect_counts[effect["effect_type"]] += 1

        spell_count = len(record["spells"])
        total_spells += spell_count
        spell_count_distribution[spell_count] += 1
        if spell_count != 4:
            champions_not_normal_4_spell.append(record["champion_id"])

        for warning in record["metadata_warnings"]:
            metadata_warning_counts[warning] += 1
        complexity_flag_counts.update(record["complexity_flags"])
        if "ALTERNATE_FORM_POSSIBLE" in record["complexity_flags"]:
            current_alternate_form_audit.append(
                _complexity_flag_audit_row(record, "ALTERNATE_FORM_POSSIBLE")
            )
        if "COPIED_OR_DYNAMIC_ABILITY" in record["complexity_flags"]:
            current_copied_dynamic_audit.append(
                _complexity_flag_audit_row(record, "COPIED_OR_DYNAMIC_ABILITY")
            )

        for spell in record["spells"]:
            if spell["slot_source"] != "DDRAGON_ARRAY_ORDER":
                slot_assignment_uncertain.append(
                    {
                        "champion_id": record["champion_id"],
                        "spell_id": spell["spell_id"],
                        "spell_array_index": spell["spell_array_index"],
                        "slot_source": spell["slot_source"],
                    }
                )
            for placeholder in spell["placeholder_resolution"]:
                placeholder_status_counts[placeholder["resolution_status"]] += 1
                if placeholder["resolution_status"] == "UNKNOWN_PLACEHOLDER":
                    key = placeholder["key"]
                    family = _placeholder_family(key)
                    unknown_placeholder_family_counts[family] += 1
                    entry = unknown_placeholder_keys.setdefault(
                        key,
                        {
                            "key": key,
                            "count": 0,
                            "champion_ids": set(),
                            "spell_ids": set(),
                            "fields": Counter(),
                            "families": Counter(),
                            "examples": [],
                        },
                    )
                    entry["count"] += 1
                    entry["champion_ids"].add(record["champion_id"])
                    entry["spell_ids"].add(spell["spell_id"])
                    entry["fields"][placeholder["field"]] += 1
                    entry["families"][family] += 1
                    if len(entry["examples"]) < 3:
                        entry["examples"].append(
                            _placeholder_example(record, spell, placeholder)
                        )
            formula_status_counts[spell["formula"]["status"]] += 1
            for fragment in spell["formula"]["fragments"]:
                formula_fragment_status_counts[fragment["status"]] += 1
            section_parse_counts.update(spell["semantic_parse_summary"])
            for effect in spell["effects"]:
                semantic_effect_counts[effect["effect_type"]] += 1

        previous_flags = _phase2b1_b_complexity_flags(record)
        if "COMPLEX_KIT_UNDERMODELED" in previous_flags:
            row = _complexity_baseline_audit_row(record)
            baseline_complexity_audit.append(row)
            complexity_audit_classification_counts[row["review_status"]] += 1

    normal_4_spell_count = spell_count_distribution[4]
    unknown_placeholder_key_audit = []
    for entry in unknown_placeholder_keys.values():
        unknown_placeholder_key_audit.append(
            {
                "key": entry["key"],
                "count": entry["count"],
                "champion_count": len(entry["champion_ids"]),
                "spell_count": len(entry["spell_ids"]),
                "fields": dict(entry["fields"]),
                "families": dict(entry["families"]),
                "primary_family": entry["families"].most_common(1)[0][0],
                "examples": entry["examples"],
            }
        )
    unknown_placeholder_key_audit.sort(
        key=lambda item: (-item["count"], item["key"])
    )
    baseline_complexity_audit.sort(key=lambda item: item["champion_id"])
    current_alternate_form_audit.sort(key=lambda item: item["champion_id"])
    current_copied_dynamic_audit.sort(key=lambda item: item["champion_id"])

    return {
        "total_champions": len(records),
        "detail_files_loaded": len(records) - len(set(missing_detail_files)),
        "missing_detail_files": sorted(set(missing_detail_files)),
        "champions_with_normalized_stats": champions_with_normalized_stats,
        "passive_records": passive_records,
        "total_spells": total_spells,
        "spell_count_distribution": spell_count_distribution,
        "champions_with_exactly_4_spells": normal_4_spell_count,
        "champions_not_normal_4_spell": champions_not_normal_4_spell,
        "slot_assignment_uncertain": slot_assignment_uncertain,
        "canonical_stat_coverage": stat_counts,
        "unknown_stat_fields": unknown_stat_fields,
        "placeholder_status_counts": placeholder_status_counts,
        "unknown_placeholder_family_counts": unknown_placeholder_family_counts,
        "unknown_placeholder_key_audit": unknown_placeholder_key_audit,
        "formula_status_counts": formula_status_counts,
        "formula_fragment_status_counts": formula_fragment_status_counts,
        "semantic_effect_counts": semantic_effect_counts,
        "section_parse_counts": section_parse_counts,
        "complexity_flag_counts": complexity_flag_counts,
        "baseline_complexity_audit": baseline_complexity_audit,
        "complexity_audit_classification_counts": complexity_audit_classification_counts,
        "current_alternate_form_audit": current_alternate_form_audit,
        "current_copied_dynamic_audit": current_copied_dynamic_audit,
        "removed_complex_false_positives": [
            row
            for row in baseline_complexity_audit
            if row["review_status"] == "FALSE_POSITIVE"
        ],
        "metadata_warning_counts": metadata_warning_counts,
    }


def _format_counts(counter, limit=None):
    if not counter:
        return "none"
    items = counter.items() if hasattr(counter, "items") else counter
    sorted_items = sorted(items, key=lambda item: (-item[1], str(item[0])))
    if limit:
        sorted_items = sorted_items[:limit]
    return ", ".join(f"{key}: {value}" for key, value in sorted_items)


def _format_mapping(mapping):
    if not mapping:
        return "none"
    return ", ".join(f"{key}: {value}" for key, value in sorted(mapping.items()))


def _format_unknown_placeholder_key_audit(entries, limit=30):
    lines = []
    for entry in entries[:limit]:
        examples = []
        for example in entry["examples"]:
            examples.append(
                (
                    f"{example['champion_name']} {example['slot']} "
                    f"{example['spell_name']} {example['field']} "
                    f"{example['placeholder']}"
                )
            )
        lines.append(
            (
                f"- {entry['key']}: count={entry['count']} | "
                f"champions={entry['champion_count']} | spells={entry['spell_count']} | "
                f"family={entry['primary_family']} | fields={_format_mapping(entry['fields'])} | "
                f"examples={examples or 'none'}"
            )
        )
    if len(entries) > limit:
        lines.append(f"- ... {len(entries) - limit} additional UNKNOWN keys omitted")
    return lines or ["- none"]


def _first_evidence_per_flag(evidence):
    selected = []
    seen = set()
    for item in evidence:
        flag = item.get("flag")
        if flag in seen:
            continue
        seen.add(flag)
        selected.append(item)
    return selected


def _format_complexity_evidence(item, prefix):
    return (
        f"  * {prefix} {item['flag']} [{item['evidence_classification']}] "
        f"{item['source_field']} {item['section_name']} "
        f"entity={item.get('entity_or_state', UNKNOWN)} "
        f"matched={item['matched_text']!r} evidence={item['evidence_text']!r} "
        f"why={item['why']}"
    )


def _format_complexity_baseline_audit(rows):
    lines = []
    for row in rows:
        lines.append(
            (
                f"- {row['champion_name']} ({row['champion_id']}): "
                f"review={row['review_status']} | "
                f"previous={row['previous_flags']} | current={row['current_flags']}"
            )
        )
        current = _first_evidence_per_flag(row["current_evidence"])
        baseline = _first_evidence_per_flag(row["baseline_evidence"])
        if current:
            for item in current:
                lines.append(_format_complexity_evidence(item, "current"))
        else:
            for item in baseline:
                lines.append(_format_complexity_evidence(item, "baseline-only"))
    return lines or ["- none"]


def _format_current_complexity_flag_audit(rows):
    lines = []
    for row in rows:
        lines.append(
            (
                f"- {row['champion_name']} ({row['champion_id']}): "
                f"flag={row['flag']} | current={row['current_flags']}"
            )
        )
        for item in _first_evidence_per_flag(row["evidence"]):
            lines.append(_format_complexity_evidence(item, "current"))
    return lines or ["- none"]


def _format_removed_complexity_false_positives(rows):
    lines = []
    for row in rows:
        lines.append(
            (
                f"- {row['champion_name']} ({row['champion_id']}): "
                f"previous={row['previous_flags']} | current={row['current_flags']}"
            )
        )
        for item in _first_evidence_per_flag(row["baseline_evidence"]):
            lines.append(_format_complexity_evidence(item, "removed-baseline"))
    return lines or ["- none"]


def select_representative_champions(catalog):
    records = catalog["records"]
    selected = {}

    def pick(requirement, predicate):
        if requirement in selected:
            return
        for record in records.values():
            if predicate(record):
                selected[requirement] = record["champion_id"]
                return

    wanted_names = {
        "Shyvana": "Shyvana",
        "Bel'Veth": "Bel'Veth",
        "Dr. Mundo": "Dr. Mundo",
        "Rammus": "Rammus",
        "Viego": "Viego",
    }
    for requirement, display_name in wanted_names.items():
        pick(requirement, lambda record, name=display_name: record["name"] == name)

    pick(
        "alternate_or_transformation",
        lambda record: any(
            flag in record["complexity_flags"]
            for flag in ("ALTERNATE_FORM_POSSIBLE", "MULTI_FORM_KIT")
        ),
    )
    pick(
        "complex_ability_structure",
        lambda record: any(
            flag in record["complexity_flags"]
            for flag in (
                "EXTRA_ABILITY_STRUCTURE",
                "COPIED_OR_DYNAMIC_ABILITY",
                "COMPLEX_KIT_UNDERMODELED",
            )
        ),
    )
    pick("shield", lambda record: _record_has_effect(record, "SHIELD"))
    pick("healing", lambda record: _record_has_effect(record, "HEAL"))
    pick(
        "copied_or_dynamic",
        lambda record: "COPIED_OR_DYNAMIC_ABILITY" in record["complexity_flags"],
    )
    pick("true_damage", lambda record: _record_has_effect(record, "TRUE_DAMAGE"))
    pick(
        "percent_health_damage",
        lambda record: any(
            _record_has_effect(record, effect)
            for effect in (
                "PERCENT_MAX_HEALTH_DAMAGE",
                "PERCENT_CURRENT_HEALTH_DAMAGE",
                "MISSING_HEALTH_DAMAGE",
            )
        ),
    )
    pick(
        "hard_cc",
        lambda record: any(_record_has_effect(record, effect) for effect in HARD_CC_TYPES),
    )
    pick(
        "stealth_or_reveal",
        lambda record: _record_has_effect(record, "STEALTH")
        or _record_has_effect(record, "CAMOUFLAGE")
        or _record_has_effect(record, "REVEAL"),
    )
    pick(
        "mixed_damage",
        lambda record: _record_has_effect(record, "PHYSICAL_DAMAGE")
        and _record_has_effect(record, "MAGIC_DAMAGE"),
    )
    return selected


def _brief_spell(spell):
    return {
        "slot": spell["inferred_slot"],
        "slot_source": spell["slot_source"],
        "id": spell["spell_id"],
        "name": spell["name"],
        "cooldown": spell["cooldown"],
        "cost": spell["cost"],
        "range": spell["range"],
        "raw_tooltip": spell["raw_tooltip"],
        "placeholder_resolution": spell["placeholder_resolution"],
        "formula": spell["formula"],
        "effects": spell["effects"],
        "parse_summary": spell["semantic_parse_summary"],
        "unparsed": spell["unparsed_effect_text"],
    }


def render_champion_record_diagnostic(record):
    lines = [
        (
            f"{record['name']} ({record['champion_id']}) | "
            f"key={record['champion_key']} | version={record['ddragon_version']} | "
            f"locale={record['locale']}"
        ),
        (
            "identity: "
            f"title={record['title']} | tags={record['tags']} | "
            f"partype={record['partype']} | info={record['info']}"
        ),
        f"complexity flags: {record['complexity_flags']}",
        f"complexity evidence: {record.get('complexity_evidence') or 'none'}",
        f"metadata warnings: {record['metadata_warnings'] or 'none'}",
        f"raw stats: {record['raw_stats'] or 'none'}",
        "normalized stats:",
    ]
    if record["normalized_stats"]:
        for stat in record["normalized_stats"]:
            lines.append(f"  - {stat}")
    else:
        lines.append("  - none")

    passive = record["passive"]
    lines.extend(
        [
            "passive:",
            f"  name={passive['name']}",
            f"  raw_description={passive['raw_description']}",
            f"  clean_description={passive['clean_description']}",
            f"  effects={passive['effects'] or 'none'}",
            f"  parse={passive['semantic_parse_summary'] or 'none'}",
            f"  unparsed={passive['unparsed_effect_text'] or 'none'}",
            "spells:",
        ]
    )
    for spell in record["spells"]:
        lines.append(f"  - {_brief_spell(spell)}")
    return "\n".join(lines)


def render_champion_knowledge_audit(catalog):
    summary = catalog["summary"]
    lines = [
        "CHAMPION KNOWLEDGE BASE PHASE 2B1-C AUDIT",
        "",
        "Scope: factual, patch-aware Data Dragon champion knowledge only.",
        "No runes, damage simulation, combos, Burst/TTK, composition analysis,",
        "item recommendations, champion scoring, or ML are computed here.",
        "",
        f"Champion knowledge version: {catalog['champion_knowledge_version']}",
        f"Requested game version: {catalog['requested_game_version']}",
        f"Resolved Data Dragon version: {catalog['resolved_ddragon_version']}",
        f"Version resolution: {catalog['version_resolution_status']}",
        f"Fallback used: {catalog['version_fallback_used']}",
        f"Locale: {catalog['locale']}",
        "",
        f"Total champions: {summary['total_champions']}",
        f"Individual champion files loaded: {summary['detail_files_loaded']}",
        f"Missing champion detail files: {summary['missing_detail_files'] or 'none'}",
        (
            "Champions with normalized base/growth stats: "
            f"{summary['champions_with_normalized_stats']}"
        ),
        f"Passive records: {summary['passive_records']}",
        f"Total spells: {summary['total_spells']}",
        (
            "Spell-count distribution: "
            f"{_format_counts(summary['spell_count_distribution'])}"
        ),
        (
            "Champions with exactly 4 spells: "
            f"{summary['champions_with_exactly_4_spells']}"
        ),
        (
            "Champions not represented as normal 4-spell kits: "
            f"{summary['champions_not_normal_4_spell'] or 'none'}"
        ),
        (
            "Slot assignment uncertain records: "
            f"{len(summary['slot_assignment_uncertain'])}"
        ),
        (
            "Canonical stat coverage: "
            f"{_format_counts(summary['canonical_stat_coverage'])}"
        ),
        f"Unknown stat fields: {_format_counts(summary['unknown_stat_fields'])}",
        (
            "Placeholder resolution: "
            f"{_format_counts(summary['placeholder_status_counts'])}"
        ),
        (
            "UNKNOWN placeholder families: "
            f"{_format_counts(summary['unknown_placeholder_family_counts'])}"
        ),
        (
            "Formula status counts: "
            f"{_format_counts(summary['formula_status_counts'])}"
        ),
        (
            "Formula fragment status counts: "
            f"{_format_counts(summary['formula_fragment_status_counts'])}"
        ),
        (
            "Semantic effect coverage: "
            f"{_format_counts(summary['semantic_effect_counts'])}"
        ),
        (
            "Semantic parse completeness: "
            f"{_format_counts(summary['section_parse_counts'])}"
        ),
        (
            "Complexity flags: "
            f"{_format_counts(summary['complexity_flag_counts'])}"
        ),
        (
            "Complexity baseline audit status: "
            f"{_format_counts(summary['complexity_audit_classification_counts'])}"
        ),
        (
            "Metadata warnings: "
            f"{_format_counts(summary['metadata_warning_counts'])}"
        ),
        "",
        "Top UNKNOWN_PLACEHOLDER keys:",
        *_format_unknown_placeholder_key_audit(
            summary["unknown_placeholder_key_audit"],
            limit=30,
        ),
        "",
        "Phase 2B1-B baseline complex champion audit:",
        f"Previous complex-kit cases audited: {len(summary['baseline_complexity_audit'])}",
        *_format_complexity_baseline_audit(summary["baseline_complexity_audit"]),
        "",
        "Remaining ALTERNATE_FORM_POSSIBLE champions:",
        *_format_current_complexity_flag_audit(summary["current_alternate_form_audit"]),
        "",
        "Remaining COPIED_OR_DYNAMIC_ABILITY champions:",
        *_format_current_complexity_flag_audit(summary["current_copied_dynamic_audit"]),
        "",
        "Removed Phase 2B1-B complex false positives:",
        *_format_removed_complexity_false_positives(
            summary["removed_complex_false_positives"]
        ),
    ]
    return "\n".join(lines)


def render_representative_champion_diagnostics(catalog):
    selected = select_representative_champions(catalog)
    missing = [
        requirement
        for requirement in REPRESENTATIVE_REQUIREMENTS
        if requirement not in selected
    ]
    lines = [
        "REPRESENTATIVE CHAMPION KNOWLEDGE DIAGNOSTICS",
        "",
        f"Coverage requirements satisfied: {len(selected)}/{len(REPRESENTATIVE_REQUIREMENTS)}",
        f"Missing diagnostic requirements: {missing or 'none'}",
    ]
    printed = set()
    for requirement in REPRESENTATIVE_REQUIREMENTS:
        champion_id = selected.get(requirement)
        if champion_id is None or champion_id in printed:
            continue
        printed.add(champion_id)
        lines.extend(
            [
                "",
                f"## {requirement}",
                render_champion_record_diagnostic(catalog["records"][champion_id]),
            ]
        )
    return "\n".join(lines)


def main():
    catalog = build_champion_knowledge_catalog()
    print(render_champion_knowledge_audit(catalog))
    print()
    print(render_representative_champion_diagnostics(catalog))


if __name__ == "__main__":
    main()
