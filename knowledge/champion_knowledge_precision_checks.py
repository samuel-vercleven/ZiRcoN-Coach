from knowledge.champion_knowledge import (
    PARTIALLY_PARSED_EFFECT_TEXT,
    SEMANTIC_PARSER_UNSUPPORTED_LOCALE,
    UNPARSED_EFFECT_TEXT,
    extract_semantic_effects,
)
from knowledge.champion_knowledge_synthetic_checks import _catalog


def _effects_for_text(text):
    effects, unparsed, semantic_parse = extract_semantic_effects(
        [
            {
                "section_type": "TEST_SECTION",
                "section_name": "synthetic",
                "text": text,
            }
        ],
        "TEST_VERSION",
    )
    return {effect["effect_type"] for effect in effects}, effects, unparsed, semantic_parse


def _all_effects(record):
    effects = {effect["effect_type"] for effect in record["passive"]["effects"]}
    for spell in record["spells"]:
        effects.update(effect["effect_type"] for effect in spell["effects"])
    return effects


def test_damage_semantics_are_explicit():
    record = _catalog()["records"]["TestHero"]
    effects = _all_effects(record)
    assert "PHYSICAL_DAMAGE" in effects
    assert "MAGIC_DAMAGE" in effects
    assert "TRUE_DAMAGE" in effects
    assert "PERCENT_MAX_HEALTH_DAMAGE" in effects


def test_sustain_defense_mobility_and_hard_cc_semantics():
    record = _catalog()["records"]["TestHero"]
    effects = _all_effects(record)
    assert "HEAL" in effects
    assert "SHIELD" in effects
    assert "DASH" in effects
    assert "STUN" in effects


def test_damage_type_unresolved_is_conservative():
    record = _catalog()["records"]["WeirdHero"]
    effects = _all_effects(record)
    assert "DAMAGE_TYPE_UNRESOLVED" in effects
    assert "PHYSICAL_DAMAGE" not in effects
    assert "MAGIC_DAMAGE" not in effects
    assert "TRUE_DAMAGE" not in effects


def test_same_sentence_partial_parsing_preserves_unknown_clause():
    spell = _catalog()["records"]["TestHero"]["spells"][1]
    assert any(effect["effect_type"] == "MAGIC_DAMAGE" for effect in spell["effects"])
    assert spell["semantic_parse_summary"]["partially_parsed_sections"] >= 1
    assert any(
        unparsed["kind"] == PARTIALLY_PARSED_EFFECT_TEXT
        and any("armure" in fragment for fragment in unparsed["unparsed_fragments"])
        and "Inflige des dégâts magiques" in unparsed["text"]
        for unparsed in spell["unparsed_effect_text"]
    )


def test_completely_unparsed_text_is_preserved():
    passive = _catalog()["records"]["WeirdHero"]["passive"]
    assert not passive["effects"]
    assert passive["semantic_parse_summary"]["completely_unparsed_sections"] == 1
    assert any(
        unparsed["kind"] == UNPARSED_EFFECT_TEXT
        and unparsed["text"] == "Texte totalement opaque."
        and unparsed["unparsed_fragments"] == ["Texte totalement opaque."]
        for unparsed in passive["unparsed_effect_text"]
    )


def test_unsupported_locale_has_no_description_semantics():
    record = _catalog(locale="en_US")["records"]["TestHero"]
    assert record["passive"]["semantic_parser"]["status"] == SEMANTIC_PARSER_UNSUPPORTED_LOCALE
    assert not _all_effects(record)
    assert record["passive"]["unparsed_effect_text"]


def test_complex_kit_flags_are_generic():
    record = _catalog()["records"]["ComplexHero"]
    flags = set(record["complexity_flags"])
    assert "ALTERNATE_FORM_POSSIBLE" in flags
    assert "COPIED_OR_DYNAMIC_ABILITY" in flags
    assert "COMPLEX_KIT_UNDERMODELED" in flags
    assert record["complexity_evidence"]


def test_shield_requires_actual_grant_or_use_context():
    positive, _, _, _ = _effects_for_text("Vous gagnez un bouclier qui absorbe 80 degats.")
    assert "SHIELD" in positive

    destroys, _, _, _ = _effects_for_text("Detruit les boucliers ennemis.")
    assert "SHIELD" not in destroys

    already_protected, _, _, _ = _effects_for_text(
        "La cible deja protegee par un bouclier gagne 30 armure."
    )
    assert "SHIELD" not in already_protected


def test_damage_type_unresolved_requires_outgoing_damage_action():
    positive, _, _, _ = _effects_for_text("Inflige 100 degats a la cible.")
    assert "DAMAGE_TYPE_UNRESOLVED" in positive

    reduction, _, _, _ = _effects_for_text("Reduit les degats subis de 30%.")
    assert "DAMAGE_REDUCTION" in reduction
    assert "DAMAGE_TYPE_UNRESOLVED" not in reduction

    ally_amp, _, _, _ = _effects_for_text("Augmente les degats d'un allie.")
    assert "DAMAGE_TYPE_UNRESOLVED" not in ally_amp


def test_percent_health_damage_requires_clause_local_damage_evidence():
    split, split_effects, split_unparsed, _ = _effects_for_text(
        "Inflige 100 degats puis gagne un bouclier egal a 10% de ses PV max."
    )
    assert "DAMAGE_TYPE_UNRESOLVED" in split
    assert "SHIELD" in split
    assert "PERCENT_MAX_HEALTH_DAMAGE" not in split
    assert any(
        "PV max" in fragment
        for record in split_unparsed
        for fragment in record.get("unparsed_fragments", [])
    )
    assert not any(
        effect["effect_type"] == "PERCENT_MAX_HEALTH_DAMAGE"
        and "bouclier" in effect["evidence_text"]
        for effect in split_effects
    )

    max_hp, _, _, _ = _effects_for_text(
        "Inflige des degats equivalents a 10% des PV max de la cible."
    )
    current_hp, _, _, _ = _effects_for_text(
        "Inflige des degats equivalents a 10% des PV actuels de la cible."
    )
    missing_hp, _, _, _ = _effects_for_text(
        "Inflige des degats equivalents a 10% des PV manquants de la cible."
    )
    assert "PERCENT_MAX_HEALTH_DAMAGE" in max_hp
    assert "PERCENT_CURRENT_HEALTH_DAMAGE" in current_hp
    assert "MISSING_HEALTH_DAMAGE" in missing_hp


def test_reveal_requires_explicit_reveal_not_generic_vision():
    generic_vision, _, _, _ = _effects_for_text("Octroie de la vision autour de vous.")
    assert "REVEAL" not in generic_vision

    explicit_reveal, _, _, _ = _effects_for_text("Revele les ennemis dans la zone.")
    assert "REVEAL" in explicit_reveal


def test_generic_form_wording_does_not_imply_transformation_or_complexity():
    effects, _, _, _ = _effects_for_text("Prend une forme de cristal.")
    assert "TRANSFORMATION" not in effects

    record = _catalog()["records"]["PrecisionHero"]
    precision_effects = _all_effects(record)
    assert "TRANSFORMATION" not in precision_effects
    assert "ALTERNATE_FORM_POSSIBLE" not in record["complexity_flags"]


def test_transformation_semantic_is_not_alternate_form_complexity():
    record = _catalog()["records"]["GenericTransformHero"]
    effects = _all_effects(record)
    assert "TRANSFORMATION" in effects
    assert "ALTERNATE_FORM_POSSIBLE" not in record["complexity_flags"]
    assert "COMPLEX_KIT_UNDERMODELED" not in record["complexity_flags"]


def test_non_self_transformations_do_not_create_alternate_form_complexity():
    record = _catalog()["records"]["NonSelfTransformHero"]
    effects = _all_effects(record)
    assert "TRANSFORMATION" in effects
    assert "ALTERNATE_FORM_POSSIBLE" not in record["complexity_flags"]
    assert "COMPLEX_KIT_UNDERMODELED" not in record["complexity_flags"]


def test_self_form_evidence_produces_alternate_form_complexity():
    record = _catalog()["records"]["SelfFormHero"]
    flags = set(record["complexity_flags"])
    assert "TRANSFORMATION" in _all_effects(record)
    assert "ALTERNATE_FORM_POSSIBLE" in flags
    assert "COMPLEX_KIT_UNDERMODELED" in flags
    assert any(
        evidence["flag"] == "ALTERNATE_FORM_POSSIBLE"
        and evidence["entity_or_state"] in {
            "champion_self_form_or_state",
            "champion_self_form_or_kit_state",
        }
        for evidence in record["complexity_evidence"]
    )

    gnar_like, _, _, _ = _effects_for_text(
        "Sa prochaine competence le transforme en Mega Forme."
    )
    assert "TRANSFORMATION" in gnar_like


def test_copied_ability_complexity_is_preserved():
    record = _catalog()["records"]["CopyHero"]
    flags = set(record["complexity_flags"])
    assert "COPIED_OR_DYNAMIC_ABILITY" in flags
    assert "COMPLEX_KIT_UNDERMODELED" in flags
    assert any(
        evidence["flag"] == "COPIED_OR_DYNAMIC_ABILITY"
        and evidence["entity_or_state"] == "copied_or_dynamic_ability"
        for evidence in record["complexity_evidence"]
    )


def test_no_source_text_loss_for_incomplete_semantics():
    catalog = _catalog()
    for record in catalog["records"].values():
        sections = [record["passive"], *record["spells"]]
        for section_holder in sections:
            for unparsed in section_holder["unparsed_effect_text"]:
                assert unparsed["text"]
                if unparsed["kind"] in {
                    PARTIALLY_PARSED_EFFECT_TEXT,
                    UNPARSED_EFFECT_TEXT,
                }:
                    assert unparsed["unparsed_fragments"]
            for detail in section_holder["semantic_parse_details"]:
                assert "text" in detail
                assert "unresolved_text" in detail


def main():
    test_damage_semantics_are_explicit()
    test_sustain_defense_mobility_and_hard_cc_semantics()
    test_damage_type_unresolved_is_conservative()
    test_same_sentence_partial_parsing_preserves_unknown_clause()
    test_completely_unparsed_text_is_preserved()
    test_unsupported_locale_has_no_description_semantics()
    test_complex_kit_flags_are_generic()
    test_shield_requires_actual_grant_or_use_context()
    test_damage_type_unresolved_requires_outgoing_damage_action()
    test_percent_health_damage_requires_clause_local_damage_evidence()
    test_reveal_requires_explicit_reveal_not_generic_vision()
    test_generic_form_wording_does_not_imply_transformation_or_complexity()
    test_transformation_semantic_is_not_alternate_form_complexity()
    test_non_self_transformations_do_not_create_alternate_form_complexity()
    test_self_form_evidence_produces_alternate_form_complexity()
    test_copied_ability_complexity_is_preserved()
    test_no_source_text_loss_for_incomplete_semantics()
    print("Champion knowledge precision checks passed.")


if __name__ == "__main__":
    main()
