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


RUNE_KNOWLEDGE_VERSION = "rune_knowledge_phase2c1_b_v3"
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
RUNE_ROLE_SOURCE = "DDRAGON_RUNESREFORGED_SLOT_INDEX"
PAGE_CONTEXT_SOURCE = "RIOT_PERKS_STYLE_DESCRIPTION"

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
    ("COOLDOWN", ("delai de recuperation", "recuperation")),
    ("SLOW", ("ralentit", "ralentissement", "ralentisse")),
    ("STACKING", ("cumul", "cumuls", "charge", "charges")),
    ("OMNIVAMP", ("omnivampirisme",)),
    ("LIFE_STEAL", ("vol de vie",)),
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

def _has_health_reference(normalized_text):
    return (
        re.search(
            r"(^|[^a-z])pv([^a-z]|$)",
            normalized_text,
        )
        is not None
        or "points de vie" in normalized_text
    )


def _health_effect_types(normalized_text):
    """
    Classe les relations aux PV de façon conservative.

    Une mention de PV ne signifie jamais automatiquement
    qu'une rune donne des PV au champion.

    Relations possibles :
    - HEALTH_STAT_GAIN
    - HEALTH_THRESHOLD_REFERENCE
    - HEALTH_SCALING_REFERENCE
    - HEALTH_REFERENCE
    """

    if not _has_health_reference(normalized_text):
        return []

    effects = []

    # ========================================================
    # 1. VRAI GAIN DE PV / PV MAX DU JOUEUR
    # ========================================================

    health_gain_patterns = (
        r"\bvous gagnez\s+\d+(?:[,.]\d+)?%\s+de pv max supplementaires\b",
        r"\baugmente(?:nt)? definitivement vos pv(?: max)?\b",
        r"\bvos pv max augmentent definitivement\b",
        r"\baugmente vos pv max\b",

        # Gain explicite en valeur fixe ou en pourcentage.
        r"\bvous gagnez\b[^.;]{0,80}\bpv max\b",
        r"\bvous obtenez\b[^.;]{0,80}\bpv max\b",
        r"\bvous recevez\b[^.;]{0,80}\bpv max\b",

        r"\bconfere\b[^.;]{0,80}\bpv max\b",
        r"\boctroie\b[^.;]{0,80}\bpv max\b",
    )

    has_stat_gain = any(
        re.search(pattern, normalized_text)
        for pattern in health_gain_patterns
    )

    if has_stat_gain:
        effects.append("HEALTH_STAT_GAIN")

    # ========================================================
    # 2. SEUIL / CONDITION BASÉE SUR LES PV
    # ========================================================

    threshold_patterns = (
        r"\bmoins de \d+(?:[,.]\d+)?%\s+(?:de|des)\s+[^.;]{0,30}\bpv\b",
        r"\bplus de \d+(?:[,.]\d+)?%\s+(?:de|des)\s+[^.;]{0,30}\bpv\b",
        r"\ben dessous de \d+(?:[,.]\d+)?%\s+(?:de|des)\s+[^.;]{0,30}\bpv\b",
        r"\bau-dessus de \d+(?:[,.]\d+)?%\s+(?:de|des)\s+[^.;]{0,30}\bpv\b",
        r"\ba \d+(?:[,.]\d+)?%\s+(?:de|des)\s+[^.;]{0,30}\bpv\b",
        r"\binfliger \d+(?:[,.]\d+)?%\s+des pv max d'un champion\b",
    )

    has_threshold = any(
        re.search(pattern, normalized_text)
        for pattern in threshold_patterns
    )

    if has_threshold:
        effects.append("HEALTH_THRESHOLD_REFERENCE")

    # ========================================================
    # 3. SCALING / FORMULE BASÉE SUR LES PV
    # ========================================================
    #
    # On retire d'abord les passages correspondant clairement
    # à des seuils. Cela évite :
    #
    # "moins de 40% de leurs PV"
    #
    # => THRESHOLD + SCALING
    #
    # alors qu'il s'agit uniquement d'un seuil.
    # ========================================================

    scaling_text = normalized_text

    for pattern in threshold_patterns:
        scaling_text = re.sub(
            pattern,
            " ",
            scaling_text,
        )

    # Une augmentation explicite des PV max exprimée en %
    # reste un gain de stat, pas une simple référence de scaling.
    pure_percentage_stat_gain_patterns = (
        r"\bvous gagnez\b[^.;]{0,40}"
        r"\d+(?:[,.]\d+)?%\s+de pv max supplementaires\b",
    )

    for pattern in pure_percentage_stat_gain_patterns:
        scaling_text = re.sub(
            pattern,
            " ",
            scaling_text,
        )

    scaling_patterns = (
        r"\d+(?:[,.]\d+)?%\s+(?:de|des)\s+[^.;]{0,30}\bpv\b",
        r"\ben fonction de[^.;]{0,50}\bpv\b",
        r"\bbase sur[^.;]{0,50}\bpv\b",
        r"\bequivalent(?:e|s)? a[^.;]{0,50}\bpv\b",
    )

    has_scaling = any(
        re.search(pattern, scaling_text)
        for pattern in scaling_patterns
    )

    if has_scaling:
        effects.append("HEALTH_SCALING_REFERENCE")

    # ========================================================
    # 4. SIMPLE RÉFÉRENCE
    # ========================================================

    if not effects:
        effects.append("HEALTH_REFERENCE")

    return effects



def _split_sentences_preserve_coordination(text):
    """
    Découpe uniquement aux frontières de phrase / ligne.

    Contrairement à _split_fragments(), cette vue conserve les coordinations
    comme "armure et résistance magique" afin de ne pas perdre un prédicat
    commun placé après les deux stats.
    """
    text = str(text or "")
    return [
        _collapse_spaces(sentence)
        for sentence in re.split(r"(?:\n+|(?<=[.!?])\s+)", text)
        if _collapse_spaces(sentence)
    ]


def _defense_stat_relation(normalized_text, stat_name):
    """Retourne une relation conservative pour ARMOR ou MAGIC_RESISTANCE."""
    if stat_name == "ARMOR":
        phrase = "armure"
        self_gain_patterns = (
            r"\bvous\s+(?:gagnez|obtenez|recevez)\b[^.;]{0,120}\barmure\b",
            r"\bvous\s+augmentez\b[^.;]{0,80}\b(?:votre|vos)\s+armure\b",
            r"\b(?:votre|vos)\s+armure\b[^.;]{0,100}\baugmente(?:nt)?\b",
        )
        target_reduction_patterns = (
            r"\b(?:reduisez|reduit|reduire|diminuez|diminue|retirez|retire)\b"
            r"[^.;]{0,80}\bl['’ ]?armure\b[^.;]{0,60}\b(?:cible|ennemi|ennemis)\b",
            r"\b(?:cible|ennemi|ennemis)\b[^.;]{0,60}\b(?:perd|perdent)\b"
            r"[^.;]{0,40}\barmure\b",
        )
        scaling_patterns = (
            r"\d+(?:[,.]\d+)?%\s+(?:de|des)\s+(?:votre|vos)\s+armure\b",
            r"\ben fonction de\b[^.;]{0,60}\b(?:votre|vos)\s+armure\b",
            r"\bselon\b[^.;]{0,60}\b(?:votre|vos)\s+armure\b",
        )
    elif stat_name == "MAGIC_RESISTANCE":
        phrase = "resistance magique"
        self_gain_patterns = (
            r"\bvous\s+(?:gagnez|obtenez|recevez)\b[^.;]{0,140}\bresistance magique\b",
            r"\bvous\s+augmentez\b[^.;]{0,100}\b(?:votre|vos)\s+resistance magique\b",
            r"\b(?:votre|vos)\s+resistance magique\b[^.;]{0,100}\baugmente(?:nt)?\b",
        )
        target_reduction_patterns = (
            r"\b(?:reduisez|reduit|reduire|diminuez|diminue|retirez|retire)\b"
            r"[^.;]{0,100}\bla resistance magique\b[^.;]{0,60}\b(?:cible|ennemi|ennemis)\b",
            r"\b(?:cible|ennemi|ennemis)\b[^.;]{0,60}\b(?:perd|perdent)\b"
            r"[^.;]{0,60}\bresistance magique\b",
        )
        scaling_patterns = (
            r"\d+(?:[,.]\d+)?%\s+(?:de|des)\s+(?:votre|vos)\s+resistance magique\b",
            r"\ben fonction de\b[^.;]{0,80}\b(?:votre|vos)\s+resistance magique\b",
            r"\bselon\b[^.;]{0,80}\b(?:votre|vos)\s+resistance magique\b",
        )
    else:
        return None

    if phrase not in normalized_text:
        return None

    if any(re.search(pattern, normalized_text) for pattern in target_reduction_patterns):
        return f"{stat_name}_REDUCTION_TARGET"

    if any(re.search(pattern, normalized_text) for pattern in self_gain_patterns):
        return f"{stat_name}_STAT_GAIN"

    if any(re.search(pattern, normalized_text) for pattern in scaling_patterns):
        return f"{stat_name}_SCALING_REFERENCE"

    return f"{stat_name}_REFERENCE"


def _defense_stat_sentence_effects(text, source_field, ddragon_version):
    """
    Analyse armure / résistance magique au niveau phrase entière.

    Cette passe existe spécialement pour conserver les prédicats coordonnés,
    par ex. "votre armure et votre résistance magique augmentent".
    Une simple mention ne devient jamais automatiquement un gain de stat.
    """
    effects = []
    seen = set()

    for sentence in _split_sentences_preserve_coordination(text):
        normalized = _normalize_text(sentence)
        for stat_name in ("ARMOR", "MAGIC_RESISTANCE"):
            effect_type = _defense_stat_relation(normalized, stat_name)
            if not effect_type:
                continue
            key = (effect_type, sentence)
            if key in seen:
                continue
            seen.add(key)
            effects.append(
                {
                    "effect_type": effect_type,
                    "source": "DDRAGON_RUNE_DESCRIPTION",
                    "source_field": source_field,
                    "confidence": "DESCRIPTION_EXPLICIT_STAT_RELATION",
                    "evidence_text": sentence,
                    "relation_scope": "SENTENCE_PRESERVED_COORDINATION",
                    "ddragon_version": ddragon_version,
                }
            )

    return effects


def _refined_stat_relations(normalized_text, stat_name):
    """
    Classe de façon conservative les autres statistiques de rune auditées.

    Le but est de distinguer un vrai gain de stat d'une simple référence,
    d'un scaling ou d'un effet d'amplification. Les familles non validées
    (par ex. ENERGY / TENACITY sur le patch courant) restent non structurées
    plutôt que d'être devinées.
    """

    if stat_name == "MOVE_SPEED":
        phrase = "vitesse de deplacement"
        if phrase not in normalized_text:
            return []

        relations = []

        amplification_patterns = (
            r"\bbonus\b.{0,100}\bvitesse de deplacement\b"
            r".{0,100}\bplus efficace",
            r"\bvitesse de deplacement\b.{0,100}\bplus efficace",
        )

        gain_patterns = (
            r"\bvous\s+gagnez\b.{0,140}\bvitesse de deplacement\b",
            r"\bvous\s+obtenez\b.{0,140}\bvitesse de deplacement\b",
            r"\bvous\s+recevez\b.{0,140}\bvitesse de deplacement\b",
            r"\b(?:vous\s+)?octroie(?:nt)?\b.{0,160}\bvitesse de deplacement\b",
            r"\b(?:vous\s+)?confere(?:nt)?\b.{0,160}\bvitesse de deplacement\b",
            r"\baugmente(?:nt)?\b.{0,100}\b(?:votre|vos)\s+vitesse de deplacement\b",
            r"\b(?:votre|vos)\s+vitesse de deplacement\b.{0,120}\baugmente(?:e|ent|es)?\b",
            r"\bbonus\s*:\s*\+?\d+(?:[,.]\d+)?%?.{0,80}\bvitesse de deplacement\b",
        )

        bonus_gain_patterns = (
            r"\b(?:vous\s+)?gagnez\s+un\s+bonus\s+en\s+vitesse de deplacement\b",
            r"\bbonus\s+en\s+vitesse de deplacement\b",
        )

        has_amplification = any(
            re.search(pattern, normalized_text)
            for pattern in amplification_patterns
        )

        if has_amplification:
            relations.append("MOVE_SPEED_BONUS_AMPLIFICATION")

        # Une phrase d'amplification comme Célérité peut aussi contenir un
        # gain direct distinct (ex. +1% de vitesse de déplacement). Le simple
        # syntagme "bonus en vitesse" n'est toutefois pas suffisant quand la
        # phrase dit uniquement que ces bonus deviennent plus efficaces.
        has_direct_gain = any(
            re.search(pattern, normalized_text)
            for pattern in gain_patterns
        )
        if not has_direct_gain and not has_amplification:
            has_direct_gain = any(
                re.search(pattern, normalized_text)
                for pattern in bonus_gain_patterns
            )

        if has_direct_gain:
            relations.append("MOVE_SPEED_STAT_GAIN")

        if not relations:
            relations.append("MOVE_SPEED_REFERENCE")

        return relations

    if stat_name == "ATTACK_SPEED":
        phrase = "vitesse d'attaque"
        if phrase not in normalized_text:
            return []

        relations = []

        scaling_patterns = (
            r"\bdegats\b.{0,120}\baugmentent?\b.{0,120}"
            r"\bvitesse d'attaque bonus\b",
            r"\ben fonction de\b.{0,80}\bvitesse d'attaque\b",
            r"\bselon\b.{0,80}\bvitesse d'attaque\b",
        )

        gain_patterns = (
            r"\bvous\s+gagnez\b.{0,140}\bvitesse d'attaque\b",
            r"\bvous\s+obtenez\b.{0,140}\bvitesse d'attaque\b",
            r"\b(?:vous\s+)?octroie(?:nt)?\b.{0,160}\bvitesse d'attaque\b",
            r"\baugmente(?:nt)?\s+definitivement\b.{0,120}\b(?:votre|vos)\s+vitesse d'attaque\b",
            r"\b(?:votre|vos)\s+vitesse d'attaque\b.{0,120}\baugmente(?:e|ent|es)?\b",
        )

        if any(re.search(pattern, normalized_text) for pattern in scaling_patterns):
            relations.append("ATTACK_SPEED_SCALING_REFERENCE")

        if any(re.search(pattern, normalized_text) for pattern in gain_patterns):
            relations.append("ATTACK_SPEED_STAT_GAIN")

        if not relations:
            relations.append("ATTACK_SPEED_REFERENCE")

        return relations

    if stat_name == "ABILITY_HASTE":
        phrase = "acceleration de competence"
        if phrase not in normalized_text:
            return []

        gain_patterns = (
            r"\b(?:vous|votre ultime)\s+gagne(?:z)?\b.{0,160}\bacceleration de competence\b",
            r"\b(?:vous\s+)?octroie(?:nt)?\b.{0,160}\bacceleration de competence\b",
            r"\baugmente(?:nt)?\s+definitivement\b.{0,140}\b(?:votre|vos)\s+acceleration de competence\b",
            r"\b(?:votre|vos)\s+acceleration de competence\b.{0,120}\baugmente(?:e|ent|es)?\b",
        )

        if any(re.search(pattern, normalized_text) for pattern in gain_patterns):
            return ["ABILITY_HASTE_STAT_GAIN"]

        return ["ABILITY_HASTE_REFERENCE"]

    if stat_name == "ADAPTIVE_FORCE":
        phrase = "force adaptative"
        if phrase not in normalized_text:
            return []

        gain_patterns = (
            r"\b(?:vous\s+)?(?:fait\s+)?gagne(?:r|z)?\b.{0,160}\bforce adaptative\b",
            r"\b(?:vous\s+)?octroie(?:nt)?\b.{0,160}\bforce adaptative\b",
            r"\bforce adaptative bonus\b.{0,120}\b(?:gagne|cumul|octroie)\b",
        )

        if any(re.search(pattern, normalized_text) for pattern in gain_patterns):
            return ["ADAPTIVE_FORCE_STAT_GAIN"]

        # Si la phrase complète contient un verbe de gain plus tôt, une
        # coordination coupée en fragments ne doit pas transformer la suite
        # en simple référence.
        if (
            "force adaptative bonus" in normalized_text
            and re.search(r"\bvous\s+gagnez\b", normalized_text)
        ):
            return ["ADAPTIVE_FORCE_STAT_GAIN"]

        return ["ADAPTIVE_FORCE_REFERENCE"]

    if stat_name == "MANA":
        if re.search(r"\bmana\b", normalized_text) is None:
            return []

        relations = []

        max_gain_patterns = (
            r"\baugmente(?:nt)?\s+definitivement\b.{0,120}\b(?:votre|vos)\s+mana max\b",
            r"\b(?:votre|vos)\s+mana max\b.{0,100}\baugmente(?:e|ent|es)?\b",
            r"\bvous\s+(?:gagnez|obtenez|recevez)\b.{0,140}\bmana max\b",
        )

        restore_patterns = (
            r"\brecupere(?:z|nt)?\b.{0,140}\bmana\b",
            r"\brend(?:ez|ent)?\b.{0,120}\bmana\b",
            r"\brestaure(?:z|nt)?\b.{0,120}\bmana\b",
        )

        if any(re.search(pattern, normalized_text) for pattern in max_gain_patterns):
            relations.append("MANA_MAX_STAT_GAIN")

        if any(re.search(pattern, normalized_text) for pattern in restore_patterns):
            relations.append("MANA_RESTORE")

        if not relations:
            relations.append("MANA_REFERENCE")

        return relations

    return []


def _refined_stat_sentence_effects(text, source_field, ddragon_version):
    """
    Analyse au niveau de la phrase entière les familles de stats qui ont été
    auditées sur les 62 runes du catalogue 16.16.1.
    """
    effects = []
    seen = set()

    for sentence in _split_sentences_preserve_coordination(text):
        normalized = _normalize_text(sentence)
        for stat_name in (
            "MOVE_SPEED",
            "ATTACK_SPEED",
            "ABILITY_HASTE",
            "ADAPTIVE_FORCE",
            "MANA",
        ):
            for effect_type in _refined_stat_relations(normalized, stat_name):
                key = (effect_type, sentence)
                if key in seen:
                    continue
                seen.add(key)
                effects.append(
                    {
                        "effect_type": effect_type,
                        "source": "DDRAGON_RUNE_DESCRIPTION",
                        "source_field": source_field,
                        "confidence": "DESCRIPTION_EXPLICIT_STAT_RELATION",
                        "evidence_text": sentence,
                        "relation_scope": "SENTENCE_PRESERVED_COORDINATION",
                        "ddragon_version": ddragon_version,
                    }
                )

    return effects


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
    for health_effect_type in _health_effect_types(normalized):
        effects.append(
            {
                "effect_type": health_effect_type,
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

    effects = _defense_stat_sentence_effects(
        text,
        source_field,
        ddragon_version,
    )
    effects.extend(
        _refined_stat_sentence_effects(
            text,
            source_field,
            ddragon_version,
        )
    )
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
    if unparsed_fragments and effects:
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
    elif unparsed_fragments:
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


def resolve_match_ddragon_version(game_version, versions=None):
    versions = list(versions if versions is not None else get_ddragon_versions())
    if not versions:
        return {
            "requested_game_version": game_version,
            "resolved_ddragon_version": None,
            "resolution_status": "NO_VERSIONS_AVAILABLE",
            "fallback_used": False,
            "catalog_required": True,
        }

    if not game_version:
        return {
            "requested_game_version": game_version,
            "resolved_ddragon_version": None,
            "resolution_status": "MATCH_GAME_VERSION_MISSING",
            "fallback_used": False,
            "catalog_required": True,
        }

    requested = str(game_version)
    if requested in versions:
        return {
            "requested_game_version": requested,
            "resolved_ddragon_version": requested,
            "resolution_status": "EXACT_VERSION",
            "fallback_used": False,
            "catalog_required": True,
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
                    "catalog_required": True,
                }

    return {
        "requested_game_version": requested,
        "resolved_ddragon_version": None,
        "resolution_status": "PATCH_CATALOG_UNAVAILABLE",
        "fallback_used": False,
        "catalog_required": True,
    }

def _major_minor_patch_from_game_version(game_version):
    if game_version in (None, "", UNKNOWN):
        return None

    match = re.match(
        r"^\s*(\d+)\.(\d+)(?:\.|$)",
        str(game_version),
    )

    if not match:
        return None

    major = int(match.group(1))
    minor = int(match.group(2))

    return f"{major}.{minor}"

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
    for record in fields:
        has_evidence = (
            bool(record["effects"])
            or bool(record["conditions"])
            or bool(record["numeric_fragments"])
        )
        any_evidence = any_evidence or has_evidence

    if any_evidence:
        return "PARTIALLY_STRUCTURED"
    return "COMPLETELY_UNPARSED"


def _semantic_parse_summary(short_record, long_record):
    counts = Counter()
    for record in (short_record, long_record):
        if not record["clean_text"]:
            counts["EMPTY"] += 1
            continue
        has_evidence = (
            bool(record["effects"])
            or bool(record["conditions"])
            or bool(record["numeric_fragments"])
        )
        if has_evidence:
            counts["PARTIALLY_STRUCTURED"] += 1
        else:
            counts["COMPLETELY_UNPARSED"] += 1
    return dict(counts)


def _build_rune_record(style, slot_index, rune, version_info, locale):
    ddragon_version = version_info["resolved_ddragon_version"]
    rune_role = "KEYSTONE" if slot_index == 0 else "MINOR"
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
        "rune_role": rune_role,
        "rune_role_provenance": {
            "source": RUNE_ROLE_SOURCE,
            "rule": "slot_index 0 => KEYSTONE; other slots => MINOR",
            "slot_index": slot_index,
            "style_id": int(style["id"]),
        },
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
        "semantic_parse_summary": _semantic_parse_summary(short_record, long_record),
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
                "slot_role": "KEYSTONE" if slot_index == 0 else "MINOR",
                "slot_role_provenance": {
                    "source": RUNE_ROLE_SOURCE,
                    "rule": "slot_index 0 => KEYSTONE; other slots => MINOR",
                },
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
    semantic_field_counts = Counter()
    unparsed_kind_counts = Counter()
    runes_by_style = Counter()
    runes_by_slot = Counter()
    rune_role_counts = Counter()

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
        semantic_field_counts.update(record.get("semantic_parse_summary", {}))
        rune_role_counts[record["rune_role"]] += 1
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
        "rune_role_counts": dict(rune_role_counts),
        "semantic_effect_counts": dict(effect_counts),
        "condition_trigger_counts": dict(condition_trigger_counts),
        "numeric_fragment_counts": dict(numeric_fragment_counts),
        "formula_status_counts": dict(formula_status_counts),
        "semantic_parser_status_counts": dict(parser_status_counts),
        "structure_completeness_counts": dict(structure_counts),
        "semantic_field_parse_counts": dict(semantic_field_counts),
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


def _page_context_from_description(description):
    if description == "primaryStyle":
        return "PRIMARY"
    if description == "subStyle":
        return "SECONDARY"
    return UNKNOWN


def _style_index(catalog):
    if not catalog:
        return {}
    return {style["style_id"]: style for style in catalog.get("styles", [])}


def resolve_observed_rune_page(perks, catalog=None, match_context=None):
    match_context = dict(match_context or {})
    records = catalog.get("records", {}) if catalog else {}
    style_index = _style_index(catalog)
    if not perks:
        return {
            "resolution_status": "NO_PERKS_PAYLOAD",
            "catalog_status": (
                "PATCH_CATALOG_AVAILABLE" if catalog else "PATCH_CATALOG_UNAVAILABLE"
            ),
            "match_context": match_context,
            "styles": [],
            "stat_perks": {},
            "counts": {},
        }

    styles = []
    stat_perks = {}
    counts = Counter()
    page_context_counts = Counter()
    rune_role_counts = Counter()
    has_unknown_link = False

    for style in perks.get("styles", []) or []:
        observed_style_id = style.get("style")
        page_context = _page_context_from_description(style.get("description"))
        page_context_counts[page_context] += 1
        if catalog is None:
            style_link_status = "PATCH_CATALOG_UNAVAILABLE"
            static_style = None
            has_unknown_link = True
        else:
            static_style = style_index.get(observed_style_id)
            if static_style:
                style_link_status = "LINKED_RUNE_STYLE"
            else:
                style_link_status = "UNKNOWN_RUNE_STYLE_ID"
                has_unknown_link = True

        resolved_style = {
            "observed_style_id": observed_style_id,
            "observed_description": style.get("description"),
            "page_context": page_context,
            "page_context_provenance": {
                "source": PAGE_CONTEXT_SOURCE,
                "raw_description": style.get("description"),
                "note": "PRIMARY/SECONDARY is page context only, not rune role.",
            },
            "style_link_status": style_link_status,
            "static_style_key": static_style.get("key") if static_style else UNKNOWN,
            "static_style_name": static_style.get("name") if static_style else UNKNOWN,
            "selections": [],
        }

        for selection in style.get("selections", []) or []:
            perk_id = selection.get("perk")
            if catalog is None:
                record = None
                link_status = "PATCH_CATALOG_UNAVAILABLE"
                has_unknown_link = True
            else:
                record = records.get(perk_id)
                if record:
                    link_status = "LINKED_RUNE_CATALOG"
                else:
                    link_status = "UNKNOWN_PERK_ID"
                    has_unknown_link = True

            if record:
                rune_role = record["rune_role"]
                rune_role_provenance = dict(record["rune_role_provenance"])
                style_consistency = (
                    "MATCHES_OBSERVED_STYLE"
                    if record["style_id"] == observed_style_id
                    else "STATIC_STYLE_MISMATCH"
                )
                if style_consistency != "MATCHES_OBSERVED_STYLE":
                    has_unknown_link = True
            else:
                rune_role = UNKNOWN
                rune_role_provenance = {
                    "source": RUNE_ROLE_SOURCE,
                    "status": "UNAVAILABLE_WITHOUT_STATIC_RUNE_RECORD",
                }
                style_consistency = "UNKNOWN"

            rune_role_counts[rune_role] += 1
            counts[link_status] += 1
            resolved_style["selections"].append(
                {
                    "perk_id": perk_id,
                    "link_status": link_status,
                    "rune_id": record["rune_id"] if record else perk_id,
                    "rune_key": record["key"] if record else UNKNOWN,
                    "rune_name": record["name"] if record else UNKNOWN,
                    "rune_role": rune_role,
                    "rune_role_provenance": rune_role_provenance,
                    "static_style_id": record["style_id"] if record else None,
                    "static_style_key": record["style_key"] if record else UNKNOWN,
                    "static_slot_index": record["slot_index"] if record else None,
                    "observed_style_id": observed_style_id,
                    "style_consistency": style_consistency,
                    "page_context": page_context,
                    "page_context_provenance": {
                        "source": PAGE_CONTEXT_SOURCE,
                        "raw_description": style.get("description"),
                        "note": (
                            "PRIMARY/SECONDARY is page context only and does "
                            "not determine KEYSTONE/MINOR."
                        ),
                    },
                    "var1": selection.get("var1"),
                    "var2": selection.get("var2"),
                    "var3": selection.get("var3"),
                    "var_meaning_status": "RIOT_OBSERVED_UNINTERPRETED",
                }
            )

        styles.append(resolved_style)

    for slot in STAT_PERK_SLOTS:
        stat_perk_id = (perks.get("statPerks") or {}).get(slot)
        if stat_perk_id is None:
            status = "MISSING"
        elif catalog is None:
            status = "PATCH_CATALOG_UNAVAILABLE"
        elif stat_perk_id in records:
            status = "LINKED_STATIC_RUNE_UNEXPECTED"
        else:
            status = "STAT_PERK_NOT_EXPOSED_BY_DDRAGON_RUNE_CATALOG"
        stat_perks[slot] = {
            "slot": slot,
            "stat_perk_id": stat_perk_id,
            "status": status,
            "meaning_status": NOT_EXPOSED,
            "value_status": NOT_EXPOSED,
            "source": "RIOT_MATCH_PERKS_STATPERKS",
        }

    if catalog is None:
        resolution_status = "PATCH_CATALOG_UNAVAILABLE"
    elif has_unknown_link:
        resolution_status = "PARTIALLY_RESOLVED"
    else:
        resolution_status = "RESOLVED"

    return {
        "resolution_status": resolution_status,
        "catalog_status": (
            "PATCH_CATALOG_AVAILABLE" if catalog else "PATCH_CATALOG_UNAVAILABLE"
        ),
        "ddragon_version": catalog.get("resolved_ddragon_version") if catalog else None,
        "locale": catalog.get("locale") if catalog else None,
        "match_context": match_context,
        "styles": styles,
        "stat_perks": stat_perks,
        "counts": dict(counts),
        "page_context_counts": dict(page_context_counts),
        "rune_role_counts": dict(rune_role_counts),
    }


def _catalog_for_resolved_version(
    ddragon_version,
    locale,
    versions,
    cache,
    raw_runes_by_version=None,
):
    if not ddragon_version:
        return None, "PATCH_CATALOG_UNAVAILABLE"
    if ddragon_version in cache:
        return cache[ddragon_version], "PATCH_CATALOG_AVAILABLE"

    raw_runes = None
    if raw_runes_by_version:
        raw_runes = raw_runes_by_version.get(ddragon_version)
    try:
        catalog = build_rune_knowledge_catalog(
            requested_game_version=ddragon_version,
            locale=locale,
            raw_runes=raw_runes,
            versions=[ddragon_version] if versions is None else versions,
        )
    except requests.RequestException:
        return None, "PATCH_CATALOG_LOAD_FAILED"

    cache[ddragon_version] = catalog
    return catalog, "PATCH_CATALOG_AVAILABLE"


def _rune_name_from_catalog_cache(perk_id, catalog_cache):
    for catalog in catalog_cache.values():
        record = catalog.get("records", {}).get(perk_id)
        if record:
            return record["name"]
    return UNKNOWN


def build_observed_rune_audit(
    catalog=None,
    match_rows=None,
    db_path=DB_PATH,
    locale=DEFAULT_LOCALE,
    versions=None,
    catalog_by_version=None,
    raw_runes_by_version=None,
):
    match_rows = match_rows if match_rows is not None else _load_match_rows(db_path)
    versions = list(versions if versions is not None else get_ddragon_versions())
    catalog_cache = dict(catalog_by_version or {})
    if catalog:
        catalog_cache[catalog["resolved_ddragon_version"]] = catalog

    rune_counts = Counter()
    style_counts = Counter()
    link_status_counts = Counter()
    style_link_status_counts = Counter()
    linked_rune_name_counts = Counter()
    unresolved_perk_counts = Counter()
    match_version_resolution_counts = Counter()
    catalog_status_counts = Counter()
    catalog_versions_used = Counter()
    page_resolution_counts = Counter()
    page_context_counts = Counter()
    rune_role_counts = Counter()
    style_consistency_counts = Counter()
    stat_perk_counts_by_slot = {slot: Counter() for slot in STAT_PERK_SLOTS}
    stat_perk_status_counts = Counter()
    stat_perk_examples = defaultdict(list)
    unknown_perk_examples = []
    unknown_style_examples = []
    unavailable_catalog_examples = []
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
        version_info = resolve_match_ddragon_version(game_version, versions=versions)
        match_version_resolution_counts[version_info["resolution_status"]] += 1
        patch_catalog = None
        patch_catalog_status = "PATCH_CATALOG_UNAVAILABLE"
        if version_info["resolved_ddragon_version"]:
            patch_catalog, patch_catalog_status = _catalog_for_resolved_version(
                version_info["resolved_ddragon_version"],
                locale,
                versions,
                catalog_cache,
                raw_runes_by_version=raw_runes_by_version,
            )
        catalog_status_counts[patch_catalog_status] += 1
        if patch_catalog:
            catalog_versions_used[patch_catalog["resolved_ddragon_version"]] += 1
        else:
            _example(
                unavailable_catalog_examples,
                {
                    "match_id": match_row.get("match_id"),
                    "game_version": game_version,
                    "version_resolution_status": version_info["resolution_status"],
                    "catalog_status": patch_catalog_status,
                },
            )

        for participant in participants:
            participant_count += 1
            champion = participant.get("championName") or UNKNOWN
            champion_counts[champion] += 1
            perks = participant.get("perks") or {}
            if not perks:
                continue
            participants_with_perks += 1
            matches_with_perks.add(match_row.get("match_id"))

            resolved_page = resolve_observed_rune_page(
                perks,
                patch_catalog,
                match_context={
                    "match_id": match_row.get("match_id"),
                    "game_version": game_version,
                    "resolved_ddragon_version": version_info["resolved_ddragon_version"],
                    "version_resolution_status": version_info["resolution_status"],
                    "catalog_status": patch_catalog_status,
                    "participant_id": participant.get("participantId"),
                    "champion": champion,
                },
            )
            page_resolution_counts[resolved_page["resolution_status"]] += 1
            page_context_counts.update(resolved_page.get("page_context_counts", {}))
            rune_role_counts.update(resolved_page.get("rune_role_counts", {}))

            for resolved_style in resolved_page["styles"]:
                style_id = resolved_style["observed_style_id"]
                style_counts[style_id] += 1
                style_link_status_counts[resolved_style["style_link_status"]] += 1
                if resolved_style["style_link_status"] != "LINKED_RUNE_STYLE":
                    _example(
                        unknown_style_examples,
                        {
                            "match_id": match_row.get("match_id"),
                            "participant_id": participant.get("participantId"),
                            "champion": champion,
                            "style_id": style_id,
                            "style_link_status": resolved_style["style_link_status"],
                            "game_version": game_version,
                            "resolved_ddragon_version": version_info[
                                "resolved_ddragon_version"
                            ],
                        },
                    )

                for selection in resolved_style["selections"]:
                    perk_id = selection["perk_id"]
                    rune_selection_count += 1
                    rune_counts[perk_id] += 1
                    link_status_counts[selection["link_status"]] += 1
                    style_consistency_counts[selection["style_consistency"]] += 1
                    if selection["link_status"] == "LINKED_RUNE_CATALOG":
                        linked_rune_name_counts[selection["rune_name"]] += 1
                    else:
                        unresolved_perk_counts[perk_id] += 1
                        _example(
                            unknown_perk_examples,
                            {
                                "match_id": match_row.get("match_id"),
                                "participant_id": participant.get("participantId"),
                                "champion": champion,
                                "perk_id": perk_id,
                                "style_id": style_id,
                                "link_status": selection["link_status"],
                                "game_version": game_version,
                                "resolved_ddragon_version": version_info[
                                    "resolved_ddragon_version"
                                ],
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
                                    "var1": selection["var1"],
                                    "var2": selection["var2"],
                                    "var3": selection["var3"],
                                    "meaning_status": "RIOT_OBSERVED_UNINTERPRETED",
                                    "link_status": selection["link_status"],
                                    "rune_role": selection["rune_role"],
                                    "page_context": selection["page_context"],
                                    "resolved_ddragon_version": version_info[
                                        "resolved_ddragon_version"
                                    ],
                                },
                            },
                        )

            for slot, stat_perk in resolved_page["stat_perks"].items():
                stat_perk_id = stat_perk["stat_perk_id"]
                if stat_perk_id is None:
                    stat_perk_status_counts[f"{slot}:MISSING"] += 1
                    continue
                stat_perk_counts_by_slot[slot][stat_perk_id] += 1
                status = stat_perk["status"]
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
                        "status": status,
                        "game_version": game_version,
                        "resolved_ddragon_version": version_info[
                            "resolved_ddragon_version"
                        ],
                    },
                )

    return {
        "observed_match_count": len(match_rows),
        "participant_count": participant_count,
        "participants_with_perks": participants_with_perks,
        "matches_with_perks": len(matches_with_perks),
        "rune_selection_count": rune_selection_count,
        "patch_aware_catalog_resolution": True,
        "match_version_resolution_counts": dict(match_version_resolution_counts),
        "catalog_status_counts": dict(catalog_status_counts),
        "catalog_versions_used": dict(catalog_versions_used),
        "page_resolution_counts": dict(page_resolution_counts),
        "page_context_counts": dict(page_context_counts),
        "rune_role_counts": dict(rune_role_counts),
        "style_consistency_counts": dict(style_consistency_counts),
        "link_status_counts": dict(link_status_counts),
        "style_link_status_counts": dict(style_link_status_counts),
        "observed_rune_id_counts": dict(rune_counts),
        "known_rune_name_counts": dict(linked_rune_name_counts.most_common()),
        "unknown_perk_id_counts": dict(unresolved_perk_counts),
        "unknown_perk_examples": unknown_perk_examples,
        "observed_style_counts": dict(style_counts),
        "unknown_style_examples": unknown_style_examples,
        "unavailable_catalog_examples": unavailable_catalog_examples,
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
        (
            "rune role: "
            f"{record['rune_role']} "
            f"({record['rune_role_provenance']['source']})"
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
        f"Rune roles: {_format_counts(Counter(summary['rune_role_counts']))}",
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
            "Description-field semantic completeness: "
            f"{_format_counts(Counter(summary['semantic_field_parse_counts']))}"
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
                    "Patch-aware catalog resolution: "
                    f"{observed_audit['patch_aware_catalog_resolution']}"
                ),
                (
                    "Match version resolution: "
                    f"{_format_counts(Counter(observed_audit['match_version_resolution_counts']))}"
                ),
                (
                    "Patch catalog status: "
                    f"{_format_counts(Counter(observed_audit['catalog_status_counts']))}"
                ),
                (
                    "Catalog versions used: "
                    f"{_format_counts(Counter(observed_audit['catalog_versions_used']))}"
                ),
                (
                    "Rune page resolution: "
                    f"{_format_counts(Counter(observed_audit['page_resolution_counts']))}"
                ),
                (
                    "Rune page context counts: "
                    f"{_format_counts(Counter(observed_audit['page_context_counts']))}"
                ),
                (
                    "Observed rune roles: "
                    f"{_format_counts(Counter(observed_audit['rune_role_counts']))}"
                ),
                (
                    "Observed rune/static style consistency: "
                    f"{_format_counts(Counter(observed_audit['style_consistency_counts']))}"
                ),
                (
                    "Rune catalog link statuses: "
                    f"{_format_counts(Counter(observed_audit['link_status_counts']))}"
                ),
                (
                    "Rune style link statuses: "
                    f"{_format_counts(Counter(observed_audit['style_link_status_counts']))}"
                ),
                (
                    "Unresolved observed perk IDs: "
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
                    "Unavailable patch catalog samples: "
                    f"{observed_audit['unavailable_catalog_examples'] or 'none'}"
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
