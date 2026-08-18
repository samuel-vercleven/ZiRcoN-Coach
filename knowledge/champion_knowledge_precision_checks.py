from knowledge.champion_knowledge import (
    PARTIALLY_PARSED_EFFECT_TEXT,
    SEMANTIC_PARSER_UNSUPPORTED_LOCALE,
    UNPARSED_EFFECT_TEXT,
)
from knowledge.champion_knowledge_synthetic_checks import _catalog


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
    test_no_source_text_loss_for_incomplete_semantics()
    print("Champion knowledge precision checks passed.")


if __name__ == "__main__":
    main()
