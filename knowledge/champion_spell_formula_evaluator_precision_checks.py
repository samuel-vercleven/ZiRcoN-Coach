"""Non-circular precision fixtures minimized from pinned LIVE 26.16 shapes."""
from knowledge.champion_spell_formula_evaluator import evaluate_calculation
from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION
from knowledge.combat_formula_types import RESOLVED, UNSUPPORTED_SIGNATURE


def _spell(calculations, values=None):
    return {
        "champion_spell_source_version": CHAMPION_SPELL_SOURCE_VERSION,
        "raw_data_values": values or [],
        "raw_m_spell_calculations": calculations,
    }


def main():
    # Number: Aatrox/Q/QEdgeDamage/mMultiplier/mSubparts/0.
    number = _spell({"x": {"mNumber": 1.25, "~class": "NumberCalculationPart"}})
    result = evaluate_calculation(number, "x")
    assert result.status == RESOLVED and result.value == 1.25
    assert result.provenance["signature_registered"] is True

    # Named DataValue: Ahri/Q/TotalDamage/mFormulaParts/0.
    named = _spell(
        {"x": {"mDataValue": "baseDamage", "~class": "NamedDataValueCalculationPart"}},
        [{"name": "baseDamage", "values": [0, 10.25, 20.5, 30.75, 41, 51.25, 61.5]}],
    )
    result = evaluate_calculation(named, "x", {"spell_rank": 2, "max_rank": 5})
    assert result.status == RESOLVED and result.value == 20.5

    # Sum: Aatrox/Q/QEdgeDamage/mMultiplier, minimized to numeric children.
    summed = _spell({"x": {"mSubparts": [{"mNumber": 1.0, "~class": "NumberCalculationPart"}, {"mNumber": 2.5, "~class": "NumberCalculationPart"}], "~class": "SumOfSubPartsCalculationPart"}})
    assert evaluate_calculation(summed, "x").value == 3.5

    # Product: Akshan/E/CriticalCalc/mMultiplier/mSubparts/1, minimized.
    product = _spell({"x": {"mPart1": {"mNumber": 2.0, "~class": "NumberCalculationPart"}, "mPart2": {"mNumber": 3.5, "~class": "NumberCalculationPart"}, "~class": "ProductOfSubPartsCalculationPart"}})
    assert evaluate_calculation(product, "x").value == 7.0

    # GameCalculation: Ahri/R/RCalculatedDamage exact root signature, minimized.
    game = _spell({"x": {"mFormulaParts": [{"mNumber": 2.0, "~class": "NumberCalculationPart"}, {"mNumber": 0.125, "~class": "NumberCalculationPart"}], "~class": "GameCalculation"}})
    result = evaluate_calculation(game, "x")
    assert result.status == RESOLVED and abs(result.value - 2.125) < 1e-12

    # Named calculation: Ambessa/Q/0x1442dbe0/mMultiplier, minimized.
    reference = _spell({"x": {"mSpellCalculationKey": "base", "~class": "NamedGameCalculationCalculationPart"}, "base": {"mNumber": 4.0, "~class": "NumberCalculationPart"}})
    result = evaluate_calculation(reference, "x")
    assert result.value == 4.0 and result.provenance["structural_signature"] == ("mSpellCalculationKey", "~class")

    # Real GameCalculation variant: Ahri/Q/TotalDamage adds a presentation field.
    unsupported = _spell({"x": {"mFormulaParts": [], "mSimpleTooltipCalculationDisplay": 1, "~class": "GameCalculation"}})
    result = evaluate_calculation(unsupported, "x")
    assert result.status == UNSUPPORTED_SIGNATURE
    assert result.provenance["signature_registered"] is False

    # Real Number variant without mNumber: Karma/Q/0x87bc3ca/mFormulaParts/0.
    unsupported_number = _spell({"x": {"~class": "NumberCalculationPart"}})
    assert evaluate_calculation(unsupported_number, "x").status == UNSUPPORTED_SIGNATURE

    # Newly observed fields always fail closed, even on an otherwise valid class.
    extra = _spell({"x": {"mNumber": 1.0, "newField": 7, "~class": "NumberCalculationPart"}})
    assert evaluate_calculation(extra, "x").status == UNSUPPORTED_SIGNATURE
    print("Spell formula evaluator precision checks: PASS (10/10)")


if __name__ == "__main__":
    main()
