from knowledge.champion_knowledge import (
    CHAMPION_KNOWLEDGE_VERSION,
    FORMULA_INCOMPLETE,
    SEMANTIC_PARSER_UNSUPPORTED_LOCALE,
    UNKNOWN,
    build_champion_knowledge_catalog,
    render_champion_knowledge_audit,
    render_representative_champion_diagnostics,
)


RAW_CHAMPIONS = {
    "TestHero": {
        "id": "TestHero",
        "key": "999",
        "name": "Test Hero",
        "title": "the fixture",
        "tags": ["Fighter"],
        "partype": "Mana",
        "info": {"attack": 5, "defense": 4, "magic": 3, "difficulty": 2},
        "image": {"full": "TestHero.png"},
        "blurb": "Synthetic champion.",
        "stats": {"hp": 600, "attackdamage": 60},
    },
    "WeirdHero": {
        "id": "WeirdHero",
        "key": "1000",
        "name": "Weird Hero",
        "title": "the incomplete",
        "tags": ["Mage"],
        "partype": "Mana",
        "stats": {"hp": 500, "attackdamage": 50},
    },
    "ComplexHero": {
        "id": "ComplexHero",
        "key": "1001",
        "name": "Complex Hero",
        "title": "the changer",
        "tags": ["Assassin"],
        "partype": "Energy",
        "stats": {"hp": 590, "attackdamage": 62},
    },
    "PrecisionHero": {
        "id": "PrecisionHero",
        "key": "1003",
        "name": "Precision Hero",
        "title": "the conservative",
        "tags": ["Support"],
        "partype": "Mana",
        "stats": {"hp": 560, "attackdamage": 54},
    },
    "SelfFormHero": {
        "id": "SelfFormHero",
        "key": "1004",
        "name": "Self Form Hero",
        "title": "the shifter",
        "tags": ["Fighter"],
        "partype": "Mana",
        "stats": {"hp": 610, "attackdamage": 61},
    },
    "GenericTransformHero": {
        "id": "GenericTransformHero",
        "key": "1005",
        "name": "Generic Transform Hero",
        "title": "the converter",
        "tags": ["Mage"],
        "partype": "Mana",
        "stats": {"hp": 540, "attackdamage": 51},
    },
    "NonSelfTransformHero": {
        "id": "NonSelfTransformHero",
        "key": "1007",
        "name": "Non Self Transform Hero",
        "title": "the careful parser",
        "tags": ["Mage"],
        "partype": "Mana",
        "stats": {"hp": 540, "attackdamage": 51},
    },
    "CopyHero": {
        "id": "CopyHero",
        "key": "1006",
        "name": "Copy Hero",
        "title": "the borrower",
        "tags": ["Mage"],
        "partype": "Mana",
        "stats": {"hp": 540, "attackdamage": 51},
    },
    "MissingDetailHero": {
        "id": "MissingDetailHero",
        "key": "1002",
        "name": "Missing Detail Hero",
        "title": "the absent",
        "tags": [],
        "partype": "None",
        "stats": {"hp": 1},
    },
}


def _spell(spell_id, name, description, tooltip, **overrides):
    spell = {
        "id": spell_id,
        "name": name,
        "description": description,
        "tooltip": tooltip,
        "maxrank": 5,
        "cooldown": [10, 9, 8, 7, 6],
        "cooldownBurn": "10/9/8/7/6",
        "cost": [50, 55, 60, 65, 70],
        "costBurn": "50/55/60/65/70",
        "costType": "Mana",
        "resource": "{{ cost }} mana",
        "range": [600],
        "rangeBurn": "600",
        "effect": [None, [10, 20, 30, 40, 50]],
        "effectBurn": [None, "10/20/30/40/50"],
        "vars": [{"key": "a1", "link": "attackdamage", "coeff": [0.5]}],
        "image": {"full": f"{spell_id}.png"},
    }
    spell.update(overrides)
    return spell


RAW_CHAMPION_DETAILS = {
    "TestHero": {
        **RAW_CHAMPIONS["TestHero"],
        "lore": "Synthetic lore.",
        "allytips": ["Use fixtures."],
        "enemytips": ["Test carefully."],
        "stats": {
            "hp": 600,
            "hpperlevel": 100,
            "hpregen": 7,
            "hpregenperlevel": 0.7,
            "mp": 300,
            "mpperlevel": 40,
            "mpregen": 8,
            "mpregenperlevel": 0.8,
            "attackdamage": 60,
            "attackdamageperlevel": 3,
            "attackspeed": 0.65,
            "attackspeedperlevel": 2.5,
            "armor": 30,
            "armorperlevel": 4,
            "spellblock": 32,
            "spellblockperlevel": 2.05,
            "movespeed": 345,
            "attackrange": 175,
            "crit": 0,
            "critperlevel": 0,
            "customstat": 123,
        },
        "passive": {
            "name": "Synthetic Endurance",
            "description": "Récupère des PV et gagne un bouclier.",
            "image": {"full": "TestHero_P.png"},
        },
        "spells": [
            _spell(
                "TestHeroQ",
                "Physical Strike",
                "Inflige des dégâts physiques à la cible.",
                "Inflige {{ e1 }} dégâts physiques (+{{ a1 }} dégâts d'attaque) à la cible.",
            ),
            _spell(
                "TestHeroW",
                "Mixed Sentence",
                "Inflige des dégâts magiques et vous gagnez 30 armure.",
                "Inflige {{ e1 }} dégâts magiques et vous gagnez 30 armure.",
            ),
            _spell(
                "TestHeroE",
                "Shield Dash",
                "Vous foncez vers l'ennemi, l'étourdit et gagnez un bouclier.",
                "Vous foncez vers l'ennemi, l'étourdit et gagnez un bouclier.",
            ),
            _spell(
                "TestHeroR",
                "True Missing Formula",
                "Inflige des dégâts bruts équivalents à 10% des PV max de la cible.",
                "Inflige {{ e1 }} dégâts bruts et {{ f1 }} puissance. {{ q9 }}",
                vars=[{"key": "f1", "link": "spelldamage", "coeff": [0.7]}],
            ),
        ],
    },
    "WeirdHero": {
        **RAW_CHAMPIONS["WeirdHero"],
        "passive": {
            "name": "Opaque",
            "description": "Texte totalement opaque.",
            "image": {"full": "WeirdHero_P.png"},
        },
        "spells": [
            _spell("WeirdHeroA", "One", "Inflige des dégâts.", "Inflige des dégâts."),
            _spell("WeirdHeroB", "Two", "Soigne un allié.", "Soigne un allié."),
            _spell("WeirdHeroC", "Three", "Ralentit la cible.", "Ralentit la cible."),
        ],
    },
    "ComplexHero": {
        **RAW_CHAMPIONS["ComplexHero"],
        "passive": {
            "name": "Forms",
            "description": "Le champion change de forme et copie une compétence ennemie.",
            "image": {"full": "ComplexHero_P.png"},
        },
        "spells": [
            _spell("ComplexHeroQ", "Q", "Inflige des dégâts magiques.", "Inflige des dégâts magiques."),
            _spell("ComplexHeroW", "W", "Révèle les ennemis.", "Révèle les ennemis."),
            _spell("ComplexHeroE", "E", "Se téléporte.", "Se téléporte."),
            _spell("ComplexHeroR", "R", "Transforme son kit.", "Transforme son kit."),
        ],
    },
    "PrecisionHero": {
        **RAW_CHAMPIONS["PrecisionHero"],
        "passive": {
            "name": "Strict Words",
            "description": "La cible deja protegee par un bouclier gagne 30 armure.",
            "image": {"full": "PrecisionHero_P.png"},
        },
        "spells": [
            _spell(
                "PrecisionHeroQ",
                "Reduction",
                "Reduit les degats subis de 30%.",
                "Reduit les degats subis de 30%.",
            ),
            _spell(
                "PrecisionHeroW",
                "Split Percent",
                "Inflige 100 degats puis gagne un bouclier egal a 10% de ses PV max.",
                "Inflige 100 degats puis gagne un bouclier egal a 10% de ses PV max.",
            ),
            _spell(
                "PrecisionHeroE",
                "Vision",
                "Octroie de la vision autour de vous.",
                "Octroie de la vision autour de vous.",
            ),
            _spell(
                "PrecisionHeroR",
                "Generic Form",
                "Prend une forme de cristal.",
                "Prend une forme de cristal.",
            ),
        ],
    },
    "SelfFormHero": {
        **RAW_CHAMPIONS["SelfFormHero"],
        "passive": {
            "name": "Own Form",
            "description": "Le champion se transforme en dragon et change ses competences.",
            "image": {"full": "SelfFormHero_P.png"},
        },
        "spells": [
            _spell("SelfFormHeroQ", "Q", "Inflige des degats.", "Inflige des degats."),
            _spell("SelfFormHeroW", "W", "Ralentit la cible.", "Ralentit la cible."),
            _spell("SelfFormHeroE", "E", "Se rue.", "Se rue."),
            _spell(
                "SelfFormHeroR",
                "R",
                "Sa prochaine competence le transforme en Mega Forme.",
                "Sa prochaine competence le transforme en Mega Forme.",
            ),
        ],
    },
    "GenericTransformHero": {
        **RAW_CHAMPIONS["GenericTransformHero"],
        "passive": {
            "name": "Converted Damage",
            "description": "Transforme 20% des degats en degats magiques.",
            "image": {"full": "GenericTransformHero_P.png"},
        },
        "spells": [
            _spell(
                "GenericTransformHeroQ",
                "Target",
                "Transforme l'ennemi en creature inoffensive.",
                "Transforme l'ennemi en creature inoffensive.",
            ),
            _spell(
                "GenericTransformHeroW",
                "Resource",
                "Transforme la Fureur en bouclier.",
                "Transforme la Fureur en bouclier.",
            ),
            _spell(
                "GenericTransformHeroE",
                "Mark",
                "Transforme la marque en ralentissement.",
                "Transforme la marque en ralentissement.",
            ),
            _spell(
                "GenericTransformHeroR",
                "Effect",
                "Transforme l'effet en bonus temporaire.",
                "Transforme l'effet en bonus temporaire.",
            ),
        ],
    },
    "NonSelfTransformHero": {
        **RAW_CHAMPIONS["NonSelfTransformHero"],
        "passive": {
            "name": "Seed Form",
            "description": "Cette graine se transforme en plante.",
            "image": {"full": "NonSelfTransformHero_P.png"},
        },
        "spells": [
            _spell(
                "NonSelfTransformHeroQ",
                "Polymorph",
                "Il le transforme en une petite bete inoffensive.",
                "Il le transforme en une petite bete inoffensive.",
            ),
            _spell(
                "NonSelfTransformHeroW",
                "Laser",
                "Elle se transforme en laser a longue portee.",
                "Elle se transforme en laser a longue portee.",
            ),
            _spell(
                "NonSelfTransformHeroE",
                "True Form Display",
                "Revele sa forme veritable pendant 2 sec.",
                "Revele sa forme veritable pendant 2 sec.",
            ),
            _spell(
                "NonSelfTransformHeroR",
                "Target",
                "La cible se transforme en statue.",
                "La cible se transforme en statue.",
            ),
        ],
    },
    "CopyHero": {
        **RAW_CHAMPIONS["CopyHero"],
        "passive": {
            "name": "Borrowed Spell",
            "description": "Copie une competence ennemie.",
            "image": {"full": "CopyHero_P.png"},
        },
        "spells": [
            _spell("CopyHeroQ", "Q", "Inflige des degats.", "Inflige des degats."),
            _spell("CopyHeroW", "W", "Soigne un allie.", "Soigne un allie."),
            _spell("CopyHeroE", "E", "Ralentit la cible.", "Ralentit la cible."),
            _spell("CopyHeroR", "R", "Copier le dernier sort ennemi.", "Copier le dernier sort ennemi."),
        ],
    },
}


def _catalog(locale="fr_FR"):
    return build_champion_knowledge_catalog(
        requested_game_version="16.1.9999",
        locale=locale,
        raw_champions=RAW_CHAMPIONS,
        raw_champion_details=RAW_CHAMPION_DETAILS,
        versions=["16.1.2", "15.24.1"],
    )


def test_version_and_identity():
    catalog = _catalog()
    assert catalog["champion_knowledge_version"] == CHAMPION_KNOWLEDGE_VERSION
    assert catalog["resolved_ddragon_version"] == "16.1.2"
    assert catalog["version_resolution_status"] == "EXACT_PATCH"
    record = catalog["records"]["TestHero"]
    assert record["champion_key_int"] == 999
    assert record["name"] == "Test Hero"
    assert record["tags"] == ["Fighter"]
    assert record["partype"] == "Mana"


def test_base_stat_normalization_and_unknown_preservation():
    record = _catalog()["records"]["TestHero"]
    stats = record["normalized_stats"]
    assert any(
        stat["stat"] == "health_base"
        and stat["source_field"] == "hp"
        and stat["value"] == 600
        for stat in stats
    )
    assert any(
        stat["stat"] == "health_growth"
        and stat["source_field"] == "hpperlevel"
        and stat["unit"] == "per_level_field"
        for stat in stats
    )
    assert any(
        stat["stat"] == UNKNOWN and stat["source_field"] == "customstat"
        for stat in stats
    )


def test_passive_and_normal_kit_structure():
    record = _catalog()["records"]["TestHero"]
    assert record["passive"]["name"] == "Synthetic Endurance"
    assert record["passive"]["raw_description"]
    assert len(record["spells"]) == 4
    assert [spell["inferred_slot"] for spell in record["spells"]] == [
        "Q",
        "W",
        "E",
        "R",
    ]
    assert all(spell["slot_source"] == "DDRAGON_ARRAY_ORDER" for spell in record["spells"])


def test_unusual_spell_count_and_complexity():
    record = _catalog()["records"]["WeirdHero"]
    assert len(record["spells"]) == 3
    assert all(spell["inferred_slot"] == UNKNOWN for spell in record["spells"])
    assert "EXTRA_ABILITY_STRUCTURE" in record["complexity_flags"]
    assert "COMPLEX_KIT_UNDERMODELED" in record["complexity_flags"]


def test_placeholder_resolution_and_formula_fragments():
    q_spell = _catalog()["records"]["TestHero"]["spells"][0]
    statuses = {
        record["resolution_status"] for record in q_spell["placeholder_resolution"]
    }
    assert "RESOLVED_EFFECT_BURN" in statuses
    assert "RESOLVED_VAR" in statuses
    assert q_spell["cooldown"] == [10, 9, 8, 7, 6]
    assert q_spell["cost"] == [50, 55, 60, 65, 70]
    assert q_spell["range"] == [600]
    assert q_spell["formula"]["fragments"]

    r_spell = _catalog()["records"]["TestHero"]["spells"][3]
    assert any(
        record["resolution_status"] == "UNKNOWN_PLACEHOLDER"
        and record["placeholder"] == "{{ q9 }}"
        for record in r_spell["placeholder_resolution"]
    )
    assert r_spell["formula"]["status"] == FORMULA_INCOMPLETE


def test_missing_fields_are_preserved_as_warnings():
    record = _catalog()["records"]["MissingDetailHero"]
    assert "MISSING_CHAMPION_DETAIL" in record["metadata_warnings"]
    assert "DATA_DRAGON_KIT_INCOMPLETE" in record["complexity_flags"]


def test_unsupported_locale_keeps_raw_but_skips_semantic_text():
    record = _catalog(locale="en_US")["records"]["TestHero"]
    assert record["passive"]["semantic_parser"]["status"] == SEMANTIC_PARSER_UNSUPPORTED_LOCALE
    assert record["passive"]["unparsed_effect_text"]
    assert not record["passive"]["effects"]
    assert not record["spells"][0]["effects"]


def test_renderers_execute():
    catalog = _catalog()
    audit = render_champion_knowledge_audit(catalog)
    diagnostics = render_representative_champion_diagnostics(catalog)
    assert "CHAMPION KNOWLEDGE BASE PHASE 2B1-C AUDIT" in audit
    assert "REPRESENTATIVE CHAMPION KNOWLEDGE DIAGNOSTICS" in diagnostics


def main():
    test_version_and_identity()
    test_base_stat_normalization_and_unknown_preservation()
    test_passive_and_normal_kit_structure()
    test_unusual_spell_count_and_complexity()
    test_placeholder_resolution_and_formula_fragments()
    test_missing_fields_are_preserved_as_warnings()
    test_unsupported_locale_keeps_raw_but_skips_semantic_text()
    test_renderers_execute()
    print("Champion knowledge synthetic checks passed.")


if __name__ == "__main__":
    main()
