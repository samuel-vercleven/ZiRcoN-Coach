"""Component-local damage evidence classifier; arithmetic is not evaluated."""
from __future__ import annotations

import re
from collections import defaultdict

DAMAGE_EVIDENCE_VERSION = "champion_spell_damage_evidence_phase2g_v2"
DAMAGE_CALCULATION_HIGH_CONFIDENCE = "DAMAGE_CALCULATION_HIGH_CONFIDENCE"
DAMAGE_CALCULATION_MULTIPLE_CANDIDATES = "DAMAGE_CALCULATION_MULTIPLE_CANDIDATES"
DAMAGE_TYPE_PHYSICAL = "PHYSICAL"
DAMAGE_TYPE_MAGIC = "MAGIC"
DAMAGE_TYPE_TRUE = "TRUE"
DAMAGE_TYPE_MULTIPLE_OR_CONTEXTUAL = "DAMAGE_TYPE_MULTIPLE_OR_CONTEXTUAL"
DAMAGE_TYPE_UNRESOLVED = "DAMAGE_TYPE_UNRESOLVED"
NOT_IDENTIFIED_AS_DAMAGE = "NOT_IDENTIFIED_AS_DAMAGE"
DAMAGE_EVIDENCE_INSUFFICIENT = "DAMAGE_EVIDENCE_INSUFFICIENT"

COMPONENT_LOCAL_STRUCTURAL_LINKAGE = "COMPONENT_LOCAL_STRUCTURAL_LINKAGE"
KEY_NAME_ONLY = "KEY_NAME_ONLY"
SPELL_LEVEL_TYPE_ONLY = "SPELL_LEVEL_TYPE_ONLY"

TYPE_TAGS = {
    "PHYSICAL_DAMAGE": DAMAGE_TYPE_PHYSICAL,
    "MAGIC_DAMAGE": DAMAGE_TYPE_MAGIC,
    "TRUE_DAMAGE": DAMAGE_TYPE_TRUE,
}
TOOLTIP_TAG_TYPES = {
    "physicaldamage": DAMAGE_TYPE_PHYSICAL,
    "magicdamage": DAMAGE_TYPE_MAGIC,
    "truedamage": DAMAGE_TYPE_TRUE,
}
CONDITIONAL_CLASSES = {
    "GameCalculationConditional",
    "BuffCounterByCoefficientCalculationPart",
    "BuffCounterByNamedDataValueCalculationPart",
    "PercentageOfBuffNameElapsed",
    "HasBuffCastRequirement",
}
TAG_PATTERN = re.compile(
    r"<(?P<tag>physicalDamage|magicDamage|trueDamage)\b[^>]*>(?P<body>.*?)</(?P=tag)>",
    re.IGNORECASE | re.DOTALL,
)
PLACEHOLDER_PATTERN = re.compile(r"{{\s*([^{}]+?)\s*}}")


def _activation(source_spell, key):
    prefix = f"mSpellCalculations/{key}"
    conditional = sorted(
        {
            node.get("calculation_class")
            for node in source_spell.get("calculation_nodes", [])
            if node.get("graph_path", "").startswith(prefix)
            and node.get("calculation_class") in CONDITIONAL_CLASSES
        }
    )
    return {
        "activation_condition_status": "UNRESOLVED_UNLESS_EXPLICIT" if conditional else "NOT_REQUIRED",
        "required_state": conditional,
    }


def _component_local_links(source_spell, semantic_spell):
    keys = list(source_spell.get("raw_calculation_names", []))
    folded = defaultdict(list)
    for key in keys:
        folded[key.casefold()].append(key)
    links = []
    tooltip = (semantic_spell or {}).get("raw_tooltip") or ""
    for tag_match in TAG_PATTERN.finditer(tooltip):
        damage_type = TOOLTIP_TAG_TYPES[tag_match.group("tag").casefold()]
        for placeholder in PLACEHOLDER_PATTERN.findall(tag_match.group("body")):
            matches = folded.get(placeholder.strip().casefold(), [])
            if len(matches) != 1:
                continue
            key = matches[0]
            links.append(
                {
                    "calculation_key": key,
                    "damage_type": damage_type,
                    "tooltip_placeholder": placeholder.strip(),
                    "tooltip_tag": tag_match.group("tag"),
                    "source_field": "raw_tooltip",
                }
            )
    unique = {}
    for link in links:
        unique[(link["calculation_key"], link["damage_type"], link["tooltip_placeholder"])] = link
    return list(unique.values())


def classify_damage_evidence(source_spell, champion_knowledge_spell):
    effects = {row.get("effect_type") for row in (champion_knowledge_spell or {}).get("effects", [])}
    spell_types = sorted({TYPE_TAGS[tag] for tag in effects if tag in TYPE_TAGS})
    keys = list(source_spell.get("raw_calculation_names", []))
    key_name_candidates = [key for key in keys if "damage" in key.casefold()]
    structural_links = _component_local_links(source_spell, champion_knowledge_spell)

    if structural_links:
        components = []
        for index, link in enumerate(structural_links):
            key = link["calculation_key"]
            components.append(
                {
                    "component_id": f"{key}:{link['damage_type']}:{index}",
                    "calculation_key": key,
                    "damage_type": link["damage_type"],
                    "evidence_tier": COMPONENT_LOCAL_STRUCTURAL_LINKAGE,
                    "component_evidence": link,
                    **_activation(source_spell, key),
                }
            )
        status = DAMAGE_CALCULATION_HIGH_CONFIDENCE if len(components) == 1 else DAMAGE_CALCULATION_MULTIPLE_CANDIDATES
    elif key_name_candidates:
        inferred_type = spell_types[0] if len(spell_types) == 1 else (
            DAMAGE_TYPE_MULTIPLE_OR_CONTEXTUAL if spell_types else DAMAGE_TYPE_UNRESOLVED
        )
        components = [
            {
                "component_id": key,
                "calculation_key": key,
                "damage_type": inferred_type,
                "evidence_tier": KEY_NAME_ONLY,
                "component_evidence": {"key_name": key},
                **_activation(source_spell, key),
            }
            for key in key_name_candidates
        ]
        status = DAMAGE_EVIDENCE_INSUFFICIENT
    elif spell_types:
        components = []
        status = DAMAGE_EVIDENCE_INSUFFICIENT
    else:
        components = []
        status = NOT_IDENTIFIED_AS_DAMAGE

    return {
        "status": status,
        "components": components,
        "evidence": {
            "version": DAMAGE_EVIDENCE_VERSION,
            "component_local_structural_links": structural_links,
            "key_name_evidence": key_name_candidates,
            "spell_level_semantic_effects": sorted(effects),
            "spell_level_damage_types": spell_types,
            "spell_level_evidence_tier": SPELL_LEVEL_TYPE_ONLY if spell_types else None,
            "source": "FROZEN_CHAMPION_KNOWLEDGE_RAW_TOOLTIP_PLUS_PINNED_CALCULATION_KEYS",
        },
    }
