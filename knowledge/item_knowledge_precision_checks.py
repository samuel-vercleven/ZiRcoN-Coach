from knowledge.item_knowledge import (
    PARTIALLY_PARSED_EFFECT_TEXT,
    SEMANTIC_PARSER_UNSUPPORTED_LOCALE,
    UNPARSED_EFFECT_TEXT,
    build_item_knowledge_catalog,
)


RAW_ITEMS = {
    "1001": {
        "name": "Boots",
        "description": "<mainText><stats>+25 vitesse de déplacement</stats></mainText>",
        "gold": {"base": 300, "purchasable": True, "total": 300, "sell": 210},
        "tags": ["Boots"],
        "maps": {"11": True},
        "stats": {"FlatMovementSpeedMod": 25},
    },
    "1036": {
        "name": "Long Sword",
        "description": "<mainText><stats>+10 dégâts d'attaque</stats></mainText>",
        "gold": {"base": 350, "purchasable": True, "total": 350, "sell": 245},
        "tags": ["Damage"],
        "maps": {"11": True},
        "stats": {"FlatPhysicalDamageMod": 10},
    },
    "1042": {
        "name": "Dagger",
        "description": "<mainText><stats>+10% vitesse d'attaque</stats></mainText>",
        "gold": {"base": 250, "purchasable": True, "total": 250, "sell": 175},
        "tags": ["AttackSpeed"],
        "maps": {"11": True},
        "stats": {"PercentAttackSpeedMod": 0.1},
    },
    "6000": {
        "name": "True Execute",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<passive>Exécution</passive><br>"
            "Vos dégâts exécutent les champions ennemis avec peu de PV."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": [],
        "maps": {"11": True},
        "stats": {},
    },
    "6001": {
        "name": "Quest Finish",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<passive>Quête</passive><br>"
            "Votre compagnon achève une quête et se transforme ensuite."
            "</mainText>"
        ),
        "gold": {"base": 450, "purchasable": True, "total": 450, "sell": 0},
        "tags": ["Jungle"],
        "maps": {"11": True},
        "stats": {},
    },
    "6002": {
        "name": "Max HP Damage",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<passive>Brûlure</passive><br>"
            "Inflige des dégâts magiques équivalents à 5% des PV max de la cible."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": [],
        "maps": {"11": True},
        "stats": {},
    },
    "6003": {
        "name": "Max HP Shield",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<active>Protection</active><br>"
            "Vous gagnez un bouclier équivalent à 5% de vos PV max."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": ["Active"],
        "maps": {"11": True},
        "stats": {},
    },
    "6004": {
        "name": "Current HP Damage",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<passive>Entaille</passive><br>"
            "Vos attaques infligent des dégâts physiques selon les PV actuels de la cible."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": [],
        "maps": {"11": True},
        "stats": {},
    },
    "6005": {
        "name": "Current HP Text",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<passive>Observation</passive><br>"
            "Affiche les PV actuels de la cible dans l'interface."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": [],
        "maps": {"11": True},
        "stats": {},
    },
    "6006": {
        "name": "Active Damage",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<active>Explosion</active><br>"
            "Inflige 100 dégâts magiques à la cible."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": ["Active"],
        "maps": {"11": True},
        "stats": {},
    },
    "6007": {
        "name": "Active Damage Reduction",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<active>Garde</active><br>"
            "Les dégâts subis sont réduits pendant 3 sec."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": ["Active"],
        "maps": {"11": True},
        "stats": {},
    },
    "6008": {
        "name": "Active Shield",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<active>Égide</active><br>"
            "Vous gagnez un bouclier qui absorbe 200 dégâts."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": ["Active"],
        "maps": {"11": True},
        "stats": {},
    },
    "6009": {
        "name": "Shield Break",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<active>Rupture</active><br>"
            "Réduit les boucliers ennemis pendant 3 sec."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": ["Active"],
        "maps": {"11": True},
        "stats": {},
    },
    "6010": {
        "name": "Cleanse",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<active>Purification</active><br>"
            "Dissipez tous les effets de contrôle et ralentissements."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": ["Active"],
        "maps": {"11": True},
        "stats": {},
    },
    "6011": {
        "name": "Dissipate Fog",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<active>Clarté</active><br>"
            "Dissipe le brouillard autour de vous."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": ["Active"],
        "maps": {"11": True},
        "stats": {},
    },
    "6012": {
        "name": "Transform",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<passive>Mue</passive><br>"
            "Cet objet se transforme après la quête."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": [],
        "maps": {"11": True},
        "stats": {},
    },
    "6013": {
        "name": "Improve",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<passive>Renfort</passive><br>"
            "Améliore légèrement votre prochaine attaque."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": [],
        "maps": {"11": True},
        "stats": {},
    },
    "6014": {
        "name": "On-hit Damage",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<passive>Impact</passive><br>"
            "Vos attaques infligent 20 dégâts magiques à l'impact."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": ["OnHit"],
        "maps": {"11": True},
        "stats": {},
    },
    "6015": {
        "name": "On-hit Utility",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<passive>Marque</passive><br>"
            "Vos attaques appliquent une marque à l'impact."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": ["OnHit"],
        "maps": {"11": True},
        "stats": {},
    },
    "6016": {
        "name": "Partial Section",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<active>Mélange</active><br>"
            "Inflige 50 dégâts magiques. Texte opaque conservé."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": [],
        "maps": {"11": True},
        "stats": {},
    },
    "6017": {
        "name": "Same Sentence Damage And Attack Speed",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<active>Explosion accélérée</active><br>"
            "Inflige 100 dégâts magiques et vous confère 30% de vitesse d'attaque."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": ["Active"],
        "maps": {"11": True},
        "stats": {},
    },
    "6018": {
        "name": "Same Sentence Shield And Slow",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<passive>Mélange</passive><br>"
            "Vous gagnez un bouclier et votre prochaine attaque ralentit la cible."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": [],
        "maps": {"11": True},
        "stats": {},
    },
    "6019": {
        "name": "Completely Unknown Mechanic",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<passive>Inconnu</passive><br>"
            "Texte mécanique totalement opaque."
            "</mainText>"
        ),
        "gold": {"base": 1000, "purchasable": True, "total": 1000, "sell": 700},
        "tags": [],
        "maps": {"11": True},
        "stats": {},
    },
    "7000": {
        "name": "Repeated Recipe",
        "description": "<mainText><stats>+20 dégâts d'attaque</stats></mainText>",
        "gold": {"base": 50, "purchasable": True, "total": 1000, "sell": 700},
        "tags": ["Damage"],
        "maps": {"11": True},
        "stats": {"FlatPhysicalDamageMod": 20},
        "from": ["1036", "1036", "1042"],
    },
}


def _catalog(locale="fr_FR"):
    return build_item_knowledge_catalog(
        requested_game_version="16.1.1",
        locale=locale,
        raw_items=RAW_ITEMS,
        versions=["16.1.1"],
    )


def _effects(item_id, locale="fr_FR"):
    record = _catalog(locale=locale)["records"][item_id]
    return {effect["effect_type"] for effect in record["effects"]}


def test_execute_positive_and_negative():
    assert "EXECUTE" in _effects(6000)
    assert "EXECUTE" not in _effects(6001)
    assert "QUEST_OR_SPECIAL_MECHANIC" in _effects(6001)


def test_percent_health_damage_requires_damage_clause():
    assert "PERCENT_MAX_HEALTH_DAMAGE" in _effects(6002)
    assert "PERCENT_MAX_HEALTH_DAMAGE" not in _effects(6003)
    assert "PERCENT_CURRENT_HEALTH_DAMAGE" in _effects(6004)
    assert "PERCENT_CURRENT_HEALTH_DAMAGE" not in _effects(6005)


def test_active_damage_and_shield_precision():
    assert "ACTIVE_DAMAGE" in _effects(6006)
    assert "ACTIVE_DAMAGE" not in _effects(6007)
    assert "DAMAGE_REDUCTION" in _effects(6007)
    assert "ACTIVE_SHIELD" in _effects(6008)
    assert "ACTIVE_SHIELD" not in _effects(6009)
    assert "SHIELD_REDUCTION" in _effects(6009)


def test_cleanse_precision():
    assert "CLEANSE" in _effects(6010)
    assert "CLEANSE" not in _effects(6011)


def test_transformation_precision():
    assert "TRANSFORMATION" in _effects(6012)
    assert "TRANSFORMATION" not in _effects(6013)


def test_on_hit_damage_requires_damage():
    assert "ON_HIT_DAMAGE" in _effects(6014)
    assert "ON_HIT_DAMAGE" not in _effects(6015)


def test_partial_parsing_is_preserved():
    record = _catalog()["records"][6016]
    assert any(
        effect["effect_type"] == "ACTIVE_DAMAGE"
        for effect in record["effects"]
    )
    assert any(
        unparsed["kind"] == PARTIALLY_PARSED_EFFECT_TEXT
        and "Texte opaque conservé" in unparsed["unparsed_fragments"]
        for unparsed in record["unparsed_effect_text"]
    )
    assert record["semantic_parse_summary"]["partially_parsed_sections"] == 1


def test_same_sentence_unknown_mechanic_makes_section_partial():
    record = _catalog()["records"][6017]
    assert any(
        effect["effect_type"] == "ACTIVE_DAMAGE"
        for effect in record["effects"]
    )
    assert record["semantic_parse_summary"].get("fully_parsed_sections", 0) == 0
    assert record["semantic_parse_summary"]["partially_parsed_sections"] == 1
    assert any(
        unparsed["kind"] == PARTIALLY_PARSED_EFFECT_TEXT
        and any(
            "vitesse d'attaque" in fragment
            for fragment in unparsed["unparsed_fragments"]
        )
        and "Inflige 100 dégâts magiques" in unparsed["text"]
        for unparsed in record["unparsed_effect_text"]
    )


def test_same_sentence_recognized_effect_does_not_swallow_unknown_clause():
    record = _catalog()["records"][6018]
    effects = {effect["effect_type"] for effect in record["effects"]}
    assert "SLOW" in effects
    assert "ACTIVE_SHIELD" not in effects
    assert record["semantic_parse_summary"]["partially_parsed_sections"] == 1
    assert any(
        unparsed["kind"] == PARTIALLY_PARSED_EFFECT_TEXT
        and any("bouclier" in fragment for fragment in unparsed["unparsed_fragments"])
        for unparsed in record["unparsed_effect_text"]
    )


def test_simple_single_mechanic_can_remain_fully_parsed():
    record = _catalog()["records"][6006]
    assert any(
        effect["effect_type"] == "ACTIVE_DAMAGE"
        for effect in record["effects"]
    )
    assert record["semantic_parse_summary"]["fully_parsed_sections"] == 1
    assert not record["unparsed_effect_text"]


def test_completely_unknown_sentence_preserves_source_text():
    record = _catalog()["records"][6019]
    assert not record["effects"]
    assert record["semantic_parse_summary"]["completely_unparsed_sections"] == 1
    assert any(
        unparsed["kind"] == UNPARSED_EFFECT_TEXT
        and unparsed["text"] == "Texte mécanique totalement opaque."
        and unparsed["unparsed_fragments"] == ["Texte mécanique totalement opaque."]
        for unparsed in record["unparsed_effect_text"]
    )


def test_no_source_text_loss_for_incomplete_semantic_sections():
    catalog = _catalog()
    for record in catalog["records"].values():
        for unparsed in record["unparsed_effect_text"]:
            assert unparsed["text"]
            if unparsed["kind"] in {
                PARTIALLY_PARSED_EFFECT_TEXT,
                UNPARSED_EFFECT_TEXT,
            }:
                assert unparsed["unparsed_fragments"]
        for detail in record["semantic_parse_details"]:
            assert "text" in detail
            assert "unresolved_text" in detail


def test_recursive_component_multiplicity():
    graph = _catalog()["records"][7000]["item_graph"]
    assert graph["direct_components"] == [1036, 1036, 1042]
    assert graph["recursive_component_tree"] == [1036, 1036, 1042]
    assert graph["recursive_component_counts"] == {1036: 2, 1042: 1}
    assert graph["component_cost_contribution"] == 950
    assert graph["combine_cost"] == 50


def test_unsupported_locale_keeps_raw_data_but_skips_description_semantics():
    record = _catalog(locale="en_US")["records"][6000]
    assert record["semantic_parser"]["status"] == SEMANTIC_PARSER_UNSUPPORTED_LOCALE
    assert record["raw_description"]
    assert not any(
        effect["source"] == "DDRAGON_DESCRIPTION"
        for effect in record["effects"]
    )
    assert record["unparsed_effect_text"]


def main():
    test_execute_positive_and_negative()
    test_percent_health_damage_requires_damage_clause()
    test_active_damage_and_shield_precision()
    test_cleanse_precision()
    test_transformation_precision()
    test_on_hit_damage_requires_damage()
    test_partial_parsing_is_preserved()
    test_same_sentence_unknown_mechanic_makes_section_partial()
    test_same_sentence_recognized_effect_does_not_swallow_unknown_clause()
    test_simple_single_mechanic_can_remain_fully_parsed()
    test_completely_unknown_sentence_preserves_source_text()
    test_no_source_text_loss_for_incomplete_semantic_sections()
    test_recursive_component_multiplicity()
    test_unsupported_locale_keeps_raw_data_but_skips_description_semantics()
    print("Item knowledge precision checks passed.")


if __name__ == "__main__":
    main()
