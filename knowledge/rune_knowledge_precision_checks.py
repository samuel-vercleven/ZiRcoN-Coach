from knowledge.rune_knowledge import (
    PARTIALLY_STRUCTURED_RUNE_TEXT,
    SEMANTIC_PARSER_UNSUPPORTED_LOCALE,
    UNPARSED_RUNE_TEXT,
    build_rune_knowledge_catalog,
    extract_semantic_effects,
)

from knowledge.rune_knowledge_synthetic_checks import RAW_RUNES


# ============================================================
# HELPERS
# ============================================================

def _effects_for_text(
    text,
    locale="fr_FR",
):
    effects, unparsed = extract_semantic_effects(
        text,
        "TEST_FIELD",
        "TEST_VERSION",
        locale=locale,
    )

    effect_types = {
        effect["effect_type"]
        for effect in effects
    }

    return (
        effect_types,
        effects,
        unparsed,
    )


# ============================================================
# DAMAGE
# ============================================================

def test_damage_requires_outgoing_damage_action():

    positive, _, _ = _effects_for_text(
        "Inflige 100 degats a la cible."
    )

    assert (
        "DAMAGE_TYPE_UNRESOLVED"
        in positive
    )

    reduction, _, _ = _effects_for_text(
        "Reduit les degats subis de 30%."
    )

    assert (
        "DAMAGE_REDUCTION"
        in reduction
    )

    assert (
        "DAMAGE_TYPE_UNRESOLVED"
        not in reduction
    )

    health_gain, _, _ = _effects_for_text(
        "Vous gagnez 10% de PV max."
    )

    assert (
        "DAMAGE_TYPE_UNRESOLVED"
        not in health_gain
    )

    assert (
        "HEALTH_STAT_GAIN"
        in health_gain
    )

    assert (
        "HEALTH_REFERENCE"
        not in health_gain
    )

    target_has_health, _, _ = _effects_for_text(
        "La cible a plus de PV."
    )

    assert (
        "HEALTH_STAT_GAIN"
        not in target_has_health
    )

    assert (
        "DAMAGE_TYPE_UNRESOLVED"
        not in target_has_health
    )


# ============================================================
# HEALTH SEMANTICS
# ============================================================

def test_health_semantics_distinguish_gain_threshold_and_scaling():

    # --------------------------------------------------------
    # Gain fixe de PV max
    # --------------------------------------------------------

    gain, _, _ = _effects_for_text(
        "Vos PV max augmentent definitivement de 30."
    )

    assert (
        "HEALTH_STAT_GAIN"
        in gain
    )

    # --------------------------------------------------------
    # Seuil de PV de la cible
    # --------------------------------------------------------

    threshold, _, _ = _effects_for_text(
        "Vous infligez davantage de degats aux champions "
        "qui ont moins de 40% de leurs PV."
    )

    assert (
        "HEALTH_THRESHOLD_REFERENCE"
        in threshold
    )

    assert (
        "HEALTH_SCALING_REFERENCE"
        not in threshold
    )

    assert (
        "HEALTH_STAT_GAIN"
        not in threshold
    )

    # --------------------------------------------------------
    # Scaling basé sur les PV
    # --------------------------------------------------------

    scaling, _, _ = _effects_for_text(
        "Le bouclier est augmente de 6% de vos PV bonus."
    )

    assert (
        "HEALTH_SCALING_REFERENCE"
        in scaling
    )

    assert (
        "HEALTH_STAT_GAIN"
        not in scaling
    )

    # --------------------------------------------------------
    # Phase Rush :
    # 25% des PV max de la cible = seuil,
    # pas gain de PV du joueur.
    # --------------------------------------------------------

    phase_rush_like, _, _ = _effects_for_text(
        "Infliger 25% des PV max d'un champion "
        "octroie de la vitesse de deplacement."
    )

    assert (
        "HEALTH_THRESHOLD_REFERENCE"
        in phase_rush_like
    )

    assert (
        "HEALTH_SCALING_REFERENCE"
        not in phase_rush_like
    )

    assert (
        "HEALTH_STAT_GAIN"
        not in phase_rush_like
    )

    # --------------------------------------------------------
    # Surcroissance :
    # gain relatif de PV max = vrai gain de stat.
    # --------------------------------------------------------

    relative_stat_gain, _, _ = _effects_for_text(
        "Vous gagnez 3.5% de PV max supplementaires."
    )

    assert (
        "HEALTH_STAT_GAIN"
        in relative_stat_gain
    )

    assert (
        "HEALTH_SCALING_REFERENCE"
        not in relative_stat_gain
    )

    # --------------------------------------------------------
    # PV d'un autre objet :
    # une balise qui gagne des PV ne signifie pas que
    # le champion gagne de la vie.
    # --------------------------------------------------------

    ward, _, _ = _effects_for_text(
        "Les balises gagnent +1 PV bonus."
    )

    assert (
        "HEALTH_STAT_GAIN"
        not in ward
    )


# ============================================================
# SHIELD
# ============================================================

def test_shield_requires_grant_or_use_context():

    positive, _, _ = _effects_for_text(
        "Vous gagnez un bouclier "
        "qui absorbe 80 degats."
    )

    assert (
        "SHIELD"
        in positive
    )

    generic, _, _ = _effects_for_text(
        "Les boucliers ennemis sont plus faibles."
    )

    assert (
        "SHIELD"
        not in generic
    )


# ============================================================
# REVEAL / VISION
# ============================================================

def test_reveal_requires_explicit_reveal_not_generic_vision():

    generic_vision, _, _ = _effects_for_text(
        "Octroie de la vision autour de vous."
    )

    assert (
        "REVEAL"
        not in generic_vision
    )

    explicit_reveal, _, _ = _effects_for_text(
        "Revele les champions ennemis proches."
    )

    assert (
        "REVEAL"
        in explicit_reveal
    )


# ============================================================
# GOLD
# ============================================================

def test_gold_requires_explicit_gold_or_po_not_pouvoir_text():

    cannot_buy, _, _ = _effects_for_text(
        "Vous ne pouvez pas acheter "
        "de bottes avant 12 min."
    )

    assert (
        "GOLD"
        not in cannot_buy
    )

    gold_gain, _, _ = _effects_for_text(
        "Vous gagnez 25 PO."
    )

    assert (
        "GOLD"
        in gold_gain
    )


# ============================================================
# PARTIAL SEMANTIC PARSING
# ============================================================

def test_same_sentence_multiple_mechanics_preserve_unparsed_fragment():

    effects, _, unparsed = _effects_for_text(
        "Inflige 100 degats et "
        "vous confere un effet solaire inconnu."
    )

    assert (
        "DAMAGE_TYPE_UNRESOLVED"
        in effects
    )

    assert any(
        row["kind"]
        == PARTIALLY_STRUCTURED_RUNE_TEXT
        for row in unparsed
    )

    assert any(
        "effet solaire inconnu"
        in fragment
        for row in unparsed
        for fragment in row["unparsed_fragments"]
    )


# ============================================================
# UNSUPPORTED LOCALE
# ============================================================

def test_unsupported_locale_has_no_semantic_effects_but_preserves_text():

    effects, _, unparsed = _effects_for_text(
        "Inflige 100 degats et revele la cible.",
        locale="en_US",
    )

    assert not effects

    assert (
        unparsed[0]["kind"]
        == UNPARSED_RUNE_TEXT
    )

    assert (
        unparsed[0]["reason"]
        == "SEMANTIC_PARSER_UNSUPPORTED_LOCALE"
    )


def test_unsupported_locale_catalog_contract_is_explicit():

    catalog = build_rune_knowledge_catalog(
        locale="en_US",
        raw_runes=RAW_RUNES,
        versions=["16.16.1"],
    )

    record = catalog["records"][8112]

    assert (
        record["semantic_parser"]["status"]
        == SEMANTIC_PARSER_UNSUPPORTED_LOCALE
    )

    assert record["raw_longDesc"]

    assert not record["effects"]


# ============================================================
# TEST RUNNER
# ============================================================

def main():
    """
    Exécute automatiquement toutes les fonctions test_* de ce
    module.

    Cela évite d'oublier d'ajouter manuellement un nouveau test
    au runner.
    """

    tests = sorted(
        (
            value
            for name, value in globals().items()
            if name.startswith("test_")
            and callable(value)
        ),
        key=lambda test: test.__name__,
    )

    passed = 0

    for test in tests:
        test()
        passed += 1

    print(
        "Rune Knowledge precision checks: "
        f"PASS ({passed}/{len(tests)})"
    )


if __name__ == "__main__":
    main()