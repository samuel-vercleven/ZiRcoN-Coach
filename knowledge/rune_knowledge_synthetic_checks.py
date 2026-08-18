import json

from knowledge.rune_knowledge import (
    MAGICAL_FOOTWEAR_PERK_ID,
    NOT_EXPOSED,
    RUNE_FORMULA_INCOMPLETE,
    build_observed_rune_audit,
    build_rune_knowledge_catalog,
    clean_description,
    resolve_match_ddragon_version,
    resolve_observed_rune_page,
    render_rune_knowledge_audit,
    render_representative_rune_diagnostics,
    _major_minor_patch_from_game_version,
)


RAW_RUNES = [
    {
        "id": 8100,
        "key": "Domination",
        "icon": "perk-images/Styles/7200_Domination.png",
        "name": "Domination",
        "slots": [
            {
                "runes": [
                    {
                        "id": 8112,
                        "key": "Electrocute",
                        "icon": "electrocute.png",
                        "name": "Synthetic Electrocute",
                        "shortDesc": (
                            "Toucher un champion avec 3 attaques inflige "
                            "des degats adaptatifs."
                        ),
                        "longDesc": (
                            "Toucher un champion ennemi avec 3 attaques "
                            "differentes inflige des degats adaptatifs bonus."
                            "<br>Degats : 70 - 240 (+0.1 degats d'attaque "
                            "bonus, +0.05 puissance) pts de degats."
                            "<br>Delai de recuperation : 20 sec."
                        ),
                    }
                ]
            },
            {
                "runes": [
                    {
                        "id": 8126,
                        "key": "CheapShot",
                        "icon": "cheap-shot.png",
                        "name": "Synthetic Cheap Shot",
                        "shortDesc": "Apres avoir ralenti un champion, inflige des degats bruts.",
                        "longDesc": (
                            "Apres avoir ralenti un champion ennemi, votre "
                            "prochaine attaque inflige 10 - 45 degats bruts."
                        ),
                    }
                ]
            },
        ],
    },
    {
        "id": 8300,
        "key": "Inspiration",
        "icon": "perk-images/Styles/7203_Whimsy.png",
        "name": "Inspiration",
        "slots": [
            {
                "runes": [
                    {
                        "id": 8360,
                        "key": "UnsealedSpellbook",
                        "icon": "spellbook.png",
                        "name": "Synthetic Spellbook",
                        "shortDesc": "Vous obtenez une option tactique inconnue.",
                        "longDesc": "Vous obtenez une option tactique inconnue.",
                    }
                ]
            },
            {
                "runes": [
                    {
                        "id": MAGICAL_FOOTWEAR_PERK_ID,
                        "key": "MagicalFootwear",
                        "icon": "magical-footwear.png",
                        "name": "Synthetic Magical Footwear",
                        "shortDesc": "Vous obtenez des bottes gratuites a 12 min.",
                        "longDesc": (
                            "Vous obtenez des Bottes legerement magiques a "
                            "12 min, mais vous ne pouvez pas acheter de "
                            "bottes avant."
                        ),
                    }
                ]
            },
        ],
    },
]

RAW_RUNES_1615 = [
    {
        "id": 8100,
        "key": "Domination",
        "icon": "domination-old.png",
        "name": "Domination",
        "slots": [
            {
                "runes": [
                    {
                        "id": 8112,
                        "key": "Electrocute",
                        "icon": "electrocute-old.png",
                        "name": "Old Synthetic Electrocute",
                        "shortDesc": "Ancien texte qui inflige des degats adaptatifs.",
                        "longDesc": "Ancien texte qui inflige des degats adaptatifs.",
                    }
                ]
            }
        ],
    }
]


def _catalog(locale="fr_FR"):
    return build_rune_knowledge_catalog(
        requested_game_version="16.16.804.9184",
        locale=locale,
        raw_runes=RAW_RUNES,
        versions=["16.16.1", "16.15.1"],
    )


def _match_rows():
    return [
        {
            "match_id": "MATCH_1",
            "game_creation": 1,
            "game_version": "16.16.804.9184",
            "raw_json": json.dumps(
                {
                    "info": {
                        "gameVersion": "16.16.804.9184",
                        "participants": [
                            {
                                "participantId": 1,
                                "championName": "SyntheticHero",
                                "perks": {
                                    "statPerks": {
                                        "offense": 5008,
                                        "flex": 5008,
                                        "defense": 5001,
                                    },
                                    "styles": [
                                        {
                                            "description": "primaryStyle",
                                            "style": 8100,
                                            "selections": [
                                                {
                                                    "perk": 8112,
                                                    "var1": 123,
                                                    "var2": 0,
                                                    "var3": 7,
                                                },
                                                {
                                                    "perk": 999999,
                                                    "var1": 0,
                                                    "var2": 0,
                                                    "var3": 0,
                                                },
                                            ],
                                        },
                                        {
                                            "description": "subStyle",
                                            "style": 8300,
                                            "selections": [
                                                {
                                                    "perk": MAGICAL_FOOTWEAR_PERK_ID,
                                                    "var1": 1,
                                                    "var2": 2,
                                                    "var3": 3,
                                                }
                                            ],
                                        },
                                    ],
                                },
                            }
                        ],
                    }
                },
                ensure_ascii=False,
            ),
        }
    ]

def test_game_version_extracts_major_minor_patch():
    assert _major_minor_patch_from_game_version(
        "16.16.804.9184"
    ) == "16.16"

    assert _major_minor_patch_from_game_version(
        "15.24.123.456"
    ) == "15.24"

    assert _major_minor_patch_from_game_version(
        "16.16"
    ) == "16.16"

    assert _major_minor_patch_from_game_version(None) is None
    assert _major_minor_patch_from_game_version("") is None
    assert _major_minor_patch_from_game_version("UNKNOWN") is None
    assert _major_minor_patch_from_game_version("version-bizarre") is None
    
def test_catalog_preserves_tree_slots_and_raw_descriptions():
    catalog = _catalog()

    assert catalog["version_resolution_status"] == "EXACT_PATCH"
    assert catalog["summary"]["total_styles"] == 2
    assert catalog["summary"]["total_slots"] == 4
    assert catalog["summary"]["total_runes"] == 4
    assert catalog["summary"]["rune_role_counts"] == {"KEYSTONE": 2, "MINOR": 2}

    record = catalog["records"][8112]
    assert record["style_id"] == 8100
    assert record["slot_index"] == 0
    assert record["rune_role"] == "KEYSTONE"
    assert "shortDesc" in record["raw_rune_json"]
    assert "longDesc" in record["raw_rune_json"]
    assert "70 - 240" in record["clean_longDesc"]


def test_formula_numeric_condition_and_semantic_evidence_are_structured():
    catalog = _catalog()
    electrocute = catalog["records"][8112]
    cheap_shot = catalog["records"][8126]

    assert electrocute["formula"]["status"] == RUNE_FORMULA_INCOMPLETE
    assert any(
        fragment["fragment_type"] == "NUMERIC_RANGE"
        and fragment["values"] == [70, 240]
        for fragment in electrocute["numeric_fragments"]
    )
    assert any(
        fragment["raw_fragment"].strip() == "20 sec"
        and fragment["unit"] == "seconds"
        for fragment in electrocute["numeric_fragments"]
    )
    assert any(
        effect["effect_type"] == "ADAPTIVE_DAMAGE"
        for effect in electrocute["effects"]
    )
    assert any(
        condition["execution_status"] == "NOT_EXECUTED"
        for condition in cheap_shot["conditions"]
    )


def test_magical_footwear_static_catalog_fact_is_exposed():
    catalog = _catalog()
    magical = catalog["summary"]["magical_footwear_static_record"]

    assert magical["catalog_status"] == "FOUND_IN_DDRAGON_RUNE_CATALOG"
    assert magical["rune_id"] == MAGICAL_FOOTWEAR_PERK_ID
    assert magical["style_key"] == "Inspiration"
    assert magical["slot_index"] == 1
    assert catalog["records"][MAGICAL_FOOTWEAR_PERK_ID]["rune_role"] == "MINOR"


def test_observed_perks_link_to_catalog_and_preserve_unknowns():
    catalog = _catalog()
    audit = build_observed_rune_audit(
        catalog,
        match_rows=_match_rows(),
        versions=["16.16.1"],
    )

    assert audit["observed_match_count"] == 1
    assert audit["participant_count"] == 1
    assert audit["rune_selection_count"] == 3
    assert audit["link_status_counts"]["LINKED_RUNE_CATALOG"] == 2
    assert audit["link_status_counts"]["UNKNOWN_PERK_ID"] == 1
    assert audit["unknown_perk_id_counts"][999999] == 1
    assert audit["match_version_resolution_counts"] == {"EXACT_PATCH": 1}
    assert audit["catalog_versions_used"] == {"16.16.1": 1}


def test_stat_perks_are_audited_by_slot_without_invented_meaning():
    catalog = _catalog()
    audit = build_observed_rune_audit(
        catalog,
        match_rows=_match_rows(),
        versions=["16.16.1"],
    )

    assert audit["stat_perk_counts_by_slot"]["offense"][5008] == 1
    assert audit["stat_perk_counts_by_slot"]["flex"][5008] == 1
    assert audit["stat_perk_counts_by_slot"]["defense"][5001] == 1
    assert (
        audit["stat_perk_status_counts"][
            "offense:STAT_PERK_NOT_EXPOSED_BY_DDRAGON_RUNE_CATALOG"
        ]
        == 1
    )
    example = audit["stat_perk_examples"]["offense:5008"][0]
    assert example["meaning_status"] == NOT_EXPOSED
    assert "name" not in example
    assert "value" not in example


def test_observed_vars_are_kept_as_uninterpreted_riot_values():
    catalog = _catalog()
    audit = build_observed_rune_audit(
        catalog,
        match_rows=_match_rows(),
        versions=["16.16.1"],
    )

    assert audit["var_observation_counts"] == {"var1": 3, "var2": 3, "var3": 3}
    assert audit["nonzero_var_observation_counts"] == {
        "var1": 2,
        "var2": 1,
        "var3": 2,
    }
    example = audit["var_value_examples"]["8112:var1"][0]
    assert example["var1"] == 123
    assert example["meaning_status"] == "RIOT_OBSERVED_UNINTERPRETED"


def test_renderers_emit_audit_text():
    catalog = _catalog()
    audit = build_observed_rune_audit(
        catalog,
        match_rows=_match_rows(),
        versions=["16.16.1"],
    )

    rendered = render_rune_knowledge_audit(catalog, audit)
    diagnostics = render_representative_rune_diagnostics(catalog, audit)

    assert "RUNE KNOWLEDGE BASE PHASE 2C1 AUDIT" in rendered
    assert "Observed historical rune audit" in rendered
    assert "Magical Footwear" in diagnostics


def test_clean_description_removes_html_and_preserves_text():
    assert clean_description("<b>Inflige</b><br>20 sec.") == "Inflige\n20 sec."


def test_match_version_resolver_never_falls_back_to_latest_for_history():
    resolved = resolve_match_ddragon_version(
        "16.15.999.1",
        versions=["16.16.1"],
    )

    assert resolved["resolution_status"] == "PATCH_CATALOG_UNAVAILABLE"
    assert resolved["resolved_ddragon_version"] is None
    assert resolved["fallback_used"] is False


def test_observed_rune_page_resolver_separates_role_from_page_context():
    catalog = _catalog()
    perks = json.loads(_match_rows()[0]["raw_json"])["info"]["participants"][0]["perks"]
    page = resolve_observed_rune_page(perks, catalog)

    primary = page["styles"][0]["selections"][0]
    secondary = page["styles"][1]["selections"][0]

    assert primary["page_context"] == "PRIMARY"
    assert primary["rune_role"] == "KEYSTONE"
    assert primary["rune_role_provenance"]["source"] == "DDRAGON_RUNESREFORGED_SLOT_INDEX"
    assert secondary["page_context"] == "SECONDARY"
    assert secondary["rune_role"] == "MINOR"
    assert "PRIMARY/SECONDARY is page context only" in secondary["page_context_provenance"]["note"]


def test_historical_audit_uses_catalog_for_each_match_patch():
    old_rows = [
        {
            "match_id": "OLD_MATCH",
            "game_creation": 1,
            "game_version": "16.15.700.1",
            "raw_json": json.dumps(
                {
                    "info": {
                        "gameVersion": "16.15.700.1",
                        "participants": [
                            {
                                "participantId": 1,
                                "championName": "OldHero",
                                "perks": {
                                    "statPerks": {
                                        "offense": 5008,
                                        "flex": 5008,
                                        "defense": 5001,
                                    },
                                    "styles": [
                                        {
                                            "description": "primaryStyle",
                                            "style": 8100,
                                            "selections": [
                                                {
                                                    "perk": 8112,
                                                    "var1": 0,
                                                    "var2": 0,
                                                    "var3": 0,
                                                }
                                            ],
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                },
                ensure_ascii=False,
            ),
        }
    ]

    audit = build_observed_rune_audit(
        match_rows=old_rows,
        versions=["16.16.1", "16.15.1"],
        raw_runes_by_version={"16.15.1": RAW_RUNES_1615},
    )

    assert audit["match_version_resolution_counts"] == {"EXACT_PATCH": 1}
    assert audit["catalog_versions_used"] == {"16.15.1": 1}
    assert audit["known_rune_name_counts"] == {"Old Synthetic Electrocute": 1}


def test_unavailable_match_patch_is_explicit_not_latest():
    catalog = _catalog()
    old_rows = _match_rows()
    old_rows[0]["game_version"] = "16.15.700.1"

    audit = build_observed_rune_audit(
        catalog,
        match_rows=old_rows,
        versions=["16.16.1"],
    )

    assert audit["match_version_resolution_counts"] == {
        "PATCH_CATALOG_UNAVAILABLE": 1
    }
    assert audit["catalog_status_counts"] == {"PATCH_CATALOG_UNAVAILABLE": 1}
    assert audit["link_status_counts"] == {"PATCH_CATALOG_UNAVAILABLE": 3}
    assert audit["catalog_versions_used"] == {}
    assert audit["unavailable_catalog_examples"][0]["game_version"] == "16.15.700.1"

# ============================================================
# TEST RUNNER
# ============================================================

def main():
    tests = sorted(
        (
            value
            for name, value in globals().items()
            if name.startswith("test_") and callable(value)
        ),
        key=lambda test: test.__name__,
    )

    passed = 0
    for test in tests:
        test()
        passed += 1

    print(
        "Rune Knowledge synthetic checks: "
        f"PASS ({passed}/{len(tests)})"
    )


if __name__ == "__main__":
    main()
