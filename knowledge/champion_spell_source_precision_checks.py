"""Focused structural precision checks for observed Riot game-file shapes."""

from knowledge.champion_spell_source import (
    CALCULATIONS_EXPOSED,
    EXACT_PRIMARY_SPELL_PATH,
    UNINTERPRETED_CALCULATION_CLASS,
    build_champion_spell_source_record,
)


def _record():
    champion = {"champion_id": "Aatrox", "name": "Aatrox", "ddragon_version": "16.16.1", "spells": [{"inferred_slot": slot} for slot in ("Q", "W", "E", "R")]}
    base = {"Characters/Aatrox/CharacterRecords/Root": {"mCharacterName": "Aatrox", "spells": ["Q", "W", "E", "R"], "spellNames": ["First", "Second", "Third", "Fourth"]}}
    q = {"ObjectName": "AatroxQ", "mScriptName": "AatroxQ", "objectPath": "Q", "mSpell": {"DataValues": [{"mName": "QBase", "mValues": [0, 1]}], "mSpellCalculations": {"QDamage": {"mFormulaParts": [{"mDataValue": "QBase", "mStat": 2, "mCoefficient": 0, "~class": "StatByNamedDataValueCalculationPart"}], "~class": "GameCalculation"}}}}
    return build_champion_spell_source_record(champion, base, {"Q": q}, {})["primary_spells"][0]


def _named_data_value_record():
    champion = {"champion_id": "Aatrox", "name": "Aatrox", "ddragon_version": "16.16.1", "spells": [{"inferred_slot": slot} for slot in ("Q", "W", "E", "R")]}
    base = {"Characters/Aatrox/CharacterRecords/Root": {"mCharacterName": "Aatrox", "spells": ["Q", "W", "E", "R"], "spellNames": ["First", "Second", "Third", "Fourth"]}}
    q = {"ObjectName": "AatroxQ", "mScriptName": "AatroxQ", "objectPath": "Q", "mSpell": {"mSpellCalculations": {"QDamage": {"mFormulaParts": [{"mDataValue": "QBaseDamage", "~class": "NamedDataValueCalculationPart"}], "~class": "GameCalculation"}}}}
    return build_champion_spell_source_record(champion, base, {"Q": q}, {})["primary_spells"][0]


def test_named_data_value_and_stat_evidence_remain_raw():
    node = next(
        node for node in _record()["calculation_nodes"]
        if node["calculation_class"] == "StatByNamedDataValueCalculationPart"
    )
    assert node["raw_node_payload"]["mDataValue"] == "QBase"
    assert node["stat_references"] == [{"field": "mStat", "value": 2}]


def test_nested_children_and_zero_are_preserved():
    record = _record()
    assert len(record["calculation_nodes"]) == 3
    assert record["raw_data_values"][0]["mValues"][0] == 0


def test_names_slots_provenance_and_non_execution_are_exact():
    record = _record()
    assert record["mapping_status"] == EXACT_PRIMARY_SPELL_PATH
    assert record["slot"] == "Q"
    assert record["raw_calculation_names"] == ["QDamage"]
    assert record["source_commit"] == "9245fd616059c6c658d1faa1029f0e18ea179154"
    assert record["formula_execution"] == "NOT_EXECUTED"
    assert record["calculation_status"] == CALCULATIONS_EXPOSED
    assert all(
        node["interpretation_status"] == UNINTERPRETED_CALCULATION_CLASS
        for node in record["calculation_nodes"]
        if node["calculation_class"] is not None
    )


def test_named_data_value_fixture_preserves_exact_class_path_and_non_execution():
    record = _named_data_value_record()
    node = next(
        node for node in record["calculation_nodes"]
        if node["calculation_class"] == "NamedDataValueCalculationPart"
    )
    # This dedicated source fixture ensures the nested named-data-value part
    # retains its exact Riot graph structure without evaluation.
    assert node["calculation_class"] == "NamedDataValueCalculationPart"
    assert node["raw_node_payload"]["mDataValue"] == "QBaseDamage"
    assert node["graph_path"] == "mSpellCalculations/QDamage/mFormulaParts/0"
    assert node["interpretation_status"] == UNINTERPRETED_CALCULATION_CLASS


def main():
    tests = sorted((name, fn) for name, fn in globals().items() if name.startswith("test_") and callable(fn))
    for _name, fn in tests:
        fn()
    print(f"Champion Spell Source precision checks: PASS ({len(tests)}/{len(tests)})")


if __name__ == "__main__":
    main()
