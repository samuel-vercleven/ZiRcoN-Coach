from knowledge.item_knowledge import (
    build_item_knowledge_catalog,
    clean_description,
    render_item_knowledge_audit,
    render_representative_item_diagnostics,
)


RAW_ITEMS = {
    "1001": {
        "name": "Synthetic Boots",
        "description": (
            "<mainText><stats><attention>+25</attention> "
            "vitesse de déplacement</stats></mainText>"
        ),
        "plaintext": "Movement speed.",
        "gold": {"base": 300, "purchasable": True, "total": 300, "sell": 210},
        "tags": ["Boots"],
        "maps": {"11": True, "12": False},
        "stats": {"FlatMovementSpeedMod": 25},
        "into": ["3000"],
    },
    "1036": {
        "name": "Synthetic Sword",
        "description": (
            "<mainText><stats><attention>+10</attention> "
            "dégâts d'attaque</stats></mainText>"
        ),
        "plaintext": "Attack damage.",
        "gold": {"base": 350, "purchasable": True, "total": 350, "sell": 245},
        "tags": ["Damage"],
        "maps": {"11": True},
        "stats": {
            "FlatPhysicalDamageMod": 10,
            "SyntheticUnknownStatMod": 7,
        },
        "into": ["3000"],
    },
    "1052": {
        "name": "Synthetic Wand",
        "description": (
            "<mainText><stats><attention>+20</attention> "
            "puissance</stats></mainText>"
        ),
        "plaintext": "Ability power.",
        "gold": {"base": 400, "purchasable": True, "total": 400, "sell": 280},
        "tags": ["SpellDamage"],
        "maps": {"11": True},
        "stats": {"FlatMagicDamageMod": 20},
        "into": ["4000"],
    },
    "1101": {
        "name": "Synthetic Jungle Pet",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<passive>Compagnon de la jungle</passive><br>"
            "Votre compagnon achève une quête de jungle.</mainText>"
        ),
        "plaintext": "Jungle pet.",
        "gold": {"base": 450, "purchasable": True, "total": 450, "sell": 0},
        "tags": ["Jungle"],
        "maps": {"11": True, "12": False},
        "stats": {},
    },
    "2003": {
        "name": "Synthetic Potion",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<active>Consommation</active><br>Vous soigne.</mainText>"
        ),
        "plaintext": "Heals.",
        "gold": {"base": 50, "purchasable": True, "total": 50, "sell": 20},
        "tags": ["Consumable"],
        "maps": {"11": True},
        "stats": {},
        "consumed": True,
        "consumeOnFull": True,
        "stacks": 5,
    },
    "2422": {
        "name": "Synthetic Granted Boots",
        "description": (
            "<mainText><stats><attention>+10</attention> "
            "vitesse de déplacement</stats><br><br>"
            "<rules>Octroyé par une rune.</rules></mainText>"
        ),
        "plaintext": "Granted.",
        "gold": {"base": 0, "purchasable": False, "total": 300, "sell": 210},
        "tags": ["Boots"],
        "maps": {"11": True},
        "stats": {"FlatMovementSpeedMod": 10},
        "into": ["3000"],
    },
    "3000": {
        "name": "Synthetic On-hit Major",
        "description": (
            "<mainText><stats><attention>+30</attention> "
            "dégâts d'attaque<br><attention>+15</attention> "
            "accélération de compétence</stats><br><br>"
            "<passive>Fil de brume</passive><br>Vos attaques infligent "
            "des dégâts physiques bonus <OnHit>à l'impact</OnHit> "
            "équivalents à un pourcentage des PV actuels de l'ennemi."
            "<br><br><passive>Mystère</passive><br>Texte inconnu conservé."
            "</mainText>"
        ),
        "plaintext": "On-hit effect.",
        "gold": {"base": 850, "purchasable": True, "total": 1500, "sell": 1050},
        "tags": ["Damage", "OnHit"],
        "maps": {"11": True},
        "stats": {"FlatPhysicalDamageMod": 30},
        "from": ["1036", "1001"],
    },
    "3020": {
        "name": "Synthetic Magic Boots",
        "description": (
            "<mainText><stats><attention>+45</attention> "
            "vitesse de déplacement<br><attention>+15</attention> "
            "pénétration magique</stats></mainText>"
        ),
        "plaintext": "Magic penetration boots.",
        "gold": {"base": 800, "purchasable": True, "total": 1100, "sell": 770},
        "tags": ["Boots"],
        "maps": {"11": True},
        "stats": {"FlatMovementSpeedMod": 45},
        "from": ["1001"],
    },
    "3340": {
        "name": "Synthetic Trinket",
        "description": (
            "<mainText><stats></stats><br><br>"
            "<active>Propriété active</active><br>Pose une balise.</mainText>"
        ),
        "plaintext": "Vision.",
        "gold": {"base": 0, "purchasable": True, "total": 0, "sell": 0},
        "tags": ["Active", "Trinket", "Vision"],
        "maps": {"11": True},
        "stats": {},
        "effect": {"Effect1Amount": "90"},
    },
    "4000": {
        "name": "Synthetic Active Stasis",
        "description": (
            "<mainText><stats><attention>+20</attention> puissance"
            "</stats><br><br><active>Pause temporelle</active><br>"
            "Vous entrez en stase pendant 2.5 sec.</mainText>"
        ),
        "plaintext": "Stasis active.",
        "gold": {"base": 700, "purchasable": True, "total": 1100, "sell": 770},
        "tags": ["SpellDamage", "Active"],
        "maps": {"11": True},
        "stats": {"FlatMagicDamageMod": 20},
        "from": ["1052"],
    },
    "5000": {
        "name": "Malformed Mystery",
        "description": "<mainText><passive>Inconnu</passive>Texte opaque.</mainText>",
        "stats": {},
        "tags": [],
    },
}


def _catalog():
    return build_item_knowledge_catalog(
        requested_game_version="16.1.9999",
        raw_items=RAW_ITEMS,
        versions=["16.1.2", "15.24.1"],
    )


def test_version_metadata():
    catalog = _catalog()
    assert catalog["resolved_ddragon_version"] == "16.1.2"
    assert catalog["version_resolution_status"] == "EXACT_PATCH"
    assert catalog["version_fallback_used"] is False


def test_raw_stat_normalization_and_unknown_preservation():
    record = _catalog()["records"][1036]
    stats = record["normalized_stats"]
    assert any(
        stat["stat"] == "attack_damage"
        and stat["source_field"] == "FlatPhysicalDamageMod"
        for stat in stats
    )
    assert any(
        stat["stat"] == "UNKNOWN"
        and stat["source_field"] == "SyntheticUnknownStatMod"
        for stat in stats
    )


def test_description_stat_supplement():
    record = _catalog()["records"][3000]
    assert any(
        stat["stat"] == "ability_haste"
        and stat["source"] == "DDRAGON_DESCRIPTION_STATS"
        for stat in record["normalized_stats"]
    )

    boots = _catalog()["records"][3020]
    assert any(
        stat["stat"] == "magic_penetration_flat"
        and stat["value"] == 15
        and stat["unit"] == "flat"
        for stat in boots["normalized_stats"]
    )


def test_description_cleanup():
    text = clean_description("<mainText>A<br><attention>B</attention></mainText>")
    assert text == "A\nB"


def test_explicit_effect_extraction_and_unparsed_preservation():
    record = _catalog()["records"][3000]
    effects = {effect["effect_type"] for effect in record["effects"]}
    assert "ON_HIT_DAMAGE" in effects
    assert "PERCENT_CURRENT_HEALTH_DAMAGE" in effects
    assert record["unparsed_effect_text"]
    assert (
        record["unparsed_effect_text"][0]["kind"]
        == "UNPARSED_EFFECT_TEXT"
    )


def test_active_and_special_effects():
    records = _catalog()["records"]
    assert any(
        effect["effect_type"] == "STASIS"
        for effect in records[4000]["effects"]
    )
    assert any(
        effect["effect_type"] == "QUEST_OR_SPECIAL_MECHANIC"
        for effect in records[1101]["effects"]
    )


def test_item_graph_traversal_and_costs():
    records = _catalog()["records"]
    major_graph = records[3000]["item_graph"]
    sword_graph = records[1036]["item_graph"]
    assert set(major_graph["direct_components"]) == {1036, 1001}
    assert set(major_graph["recursive_component_tree"]) == {1036, 1001}
    assert 3000 in sword_graph["final_upgrade_descendants"]
    assert major_graph["combine_cost"] == 850


def test_applicability_classification():
    records = _catalog()["records"]
    assert "BOOTS" in records[1001]["applicability"]["classes"]
    assert "CONSUMABLE" in records[2003]["applicability"]["classes"]
    assert "JUNGLE_STARTER" in records[1101]["applicability"]["classes"]
    assert "TRINKET" in records[3340]["applicability"]["classes"]
    assert "NON_PURCHASABLE" in records[2422]["applicability"]["classes"]


def test_malformed_missing_fields_are_preserved_as_unknown():
    record = _catalog()["records"][5000]
    assert record["purchasable"] == "UNKNOWN"
    assert record["maps"] == "NOT_EXPOSED"
    assert record["metadata_warnings"]
    assert record["unparsed_effect_text"]


def test_renderers_execute():
    catalog = _catalog()
    audit = render_item_knowledge_audit(catalog)
    diagnostics = render_representative_item_diagnostics(catalog)
    assert "ITEM KNOWLEDGE BASE PHASE 2A AUDIT" in audit
    assert "REPRESENTATIVE ITEM KNOWLEDGE DIAGNOSTICS" in diagnostics


def main():
    test_version_metadata()
    test_raw_stat_normalization_and_unknown_preservation()
    test_description_stat_supplement()
    test_description_cleanup()
    test_explicit_effect_extraction_and_unparsed_preservation()
    test_active_and_special_effects()
    test_item_graph_traversal_and_costs()
    test_applicability_classification()
    test_malformed_missing_fields_are_preserved_as_unknown()
    test_renderers_execute()
    print("Synthetic item knowledge checks passed.")


if __name__ == "__main__":
    main()
