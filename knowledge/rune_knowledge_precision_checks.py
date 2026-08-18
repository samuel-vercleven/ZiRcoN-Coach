from knowledge.rune_knowledge import (
    PARTIALLY_STRUCTURED_RUNE_TEXT,
    SEMANTIC_PARSER_UNSUPPORTED_LOCALE,
    UNPARSED_RUNE_TEXT,
    extract_semantic_effects,
    build_rune_knowledge_catalog,
)
from knowledge.rune_knowledge_synthetic_checks import RAW_RUNES


def _effects_for_text(text, locale="fr_FR"):
    effects, unparsed = extract_semantic_effects(
        text,
        "TEST_FIELD",
        "TEST_VERSION",
        locale=locale,
    )
    return {effect["effect_type"] for effect in effects}, effects, unparsed


def test_damage_requires_outgoing_damage_action():
    positive, _, _ = _effects_for_text("Inflige 100 degats a la cible.")
    assert "DAMAGE_TYPE_UNRESOLVED" in positive

    reduction, _, _ = _effects_for_text("Reduit les degats subis de 30%.")
    assert "DAMAGE_REDUCTION" in reduction
    assert "DAMAGE_TYPE_UNRESOLVED" not in reduction

    health_reference, _, _ = _effects_for_text("Gagne 10% de PV max.")
    assert "DAMAGE_TYPE_UNRESOLVED" not in health_reference
    assert "HEALTH" in health_reference


def test_shield_requires_grant_or_use_context():
    positive, _, _ = _effects_for_text("Vous gagnez un bouclier qui absorbe 80 degats.")
    assert "SHIELD" in positive

    generic, _, _ = _effects_for_text("Les boucliers ennemis sont plus faibles.")
    assert "SHIELD" not in generic


def test_reveal_requires_explicit_reveal_not_generic_vision():
    generic_vision, _, _ = _effects_for_text("Octroie de la vision autour de vous.")
    assert "REVEAL" not in generic_vision

    explicit_reveal, _, _ = _effects_for_text("Revele les champions ennemis proches.")
    assert "REVEAL" in explicit_reveal


def test_gold_requires_explicit_gold_or_po_not_pouvoir_text():
    cannot_buy, _, _ = _effects_for_text(
        "Vous ne pouvez pas acheter de bottes avant 12 min."
    )
    assert "GOLD" not in cannot_buy

    gold_gain, _, _ = _effects_for_text("Vous gagnez 25 PO.")
    assert "GOLD" in gold_gain


def test_same_sentence_multiple_mechanics_preserve_unparsed_fragment():
    effects, _, unparsed = _effects_for_text(
        "Inflige 100 degats et vous confere un effet solaire inconnu."
    )

    assert "DAMAGE_TYPE_UNRESOLVED" in effects
    assert any(row["kind"] == PARTIALLY_STRUCTURED_RUNE_TEXT for row in unparsed)
    assert any(
        "effet solaire inconnu" in fragment
        for row in unparsed
        for fragment in row["unparsed_fragments"]
    )


def test_unsupported_locale_has_no_semantic_effects_but_preserves_text():
    effects, _, unparsed = _effects_for_text(
        "Inflige 100 degats et revele la cible.",
        locale="en_US",
    )

    assert not effects
    assert unparsed[0]["kind"] == UNPARSED_RUNE_TEXT
    assert unparsed[0]["reason"] == "SEMANTIC_PARSER_UNSUPPORTED_LOCALE"


def test_unsupported_locale_catalog_contract_is_explicit():
    catalog = build_rune_knowledge_catalog(
        locale="en_US",
        raw_runes=RAW_RUNES,
        versions=["16.16.1"],
    )

    assert catalog["records"][8112]["semantic_parser"]["status"] == (
        SEMANTIC_PARSER_UNSUPPORTED_LOCALE
    )
    assert catalog["records"][8112]["raw_longDesc"]
    assert not catalog["records"][8112]["effects"]
