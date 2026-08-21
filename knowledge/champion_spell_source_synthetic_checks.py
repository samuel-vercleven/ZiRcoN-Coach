"""Deterministic, no-network checks for Phase 2F source preservation."""

from knowledge.champion_spell_source import (
    CALCULATIONS_EXPOSED,
    EXACT_OBJECT_PATH_MATCH,
    EXACT_PRIMARY_SPELL_PATH,
    NO_CALCULATIONS_EXPOSED,
    NO_CALCULATION_CLASS_EXPOSED,
    PRIMARY_SPELL_OBJECT_NOT_FOUND,
    PRIMARY_SPELL_PATH_AMBIGUOUS,
    UNINTERPRETED_CALCULATION_CLASS,
    SOURCE_UNAVAILABLE,
    build_champion_spell_source_catalog,
    build_champion_spell_source_record,
    inventory_calculation_graph,
)


def _champion():
    return {"champion_id": "Test", "name": "Test", "ddragon_version": "16.16.1", "spells": [{"inferred_slot": slot} for slot in ("Q", "W", "E", "R")]}


def _base(paths=None):
    return {"Characters/Test/CharacterRecords/Root": {"mCharacterName": "Test", "spells": paths or ["QPath", "WPath", "EPath", "RPath"], "spellNames": ["Q", "W", "E", "R"]}}


def _spell(path, calculations=None):
    data = {"mSpellCalculations": calculations} if calculations is not None else {}
    return {"ObjectName": path, "mScriptName": path, "objectPath": path, "mSpell": data}


def test_exact_primary_paths_and_key_mapping():
    record = build_champion_spell_source_record(_champion(), _base(), {path: _spell(path) for path in ("QPath", "WPath", "EPath", "RPath")}, {})
    assert [spell["slot"] for spell in record["primary_spells"]] == ["Q", "W", "E", "R"]
    assert all(spell["mapping_status"] == EXACT_PRIMARY_SPELL_PATH for spell in record["primary_spells"])


def test_exact_object_path_fallback():
    record = build_champion_spell_source_record(_champion(), _base(), {"hashed": _spell("QPath")}, {})
    assert record["primary_spells"][0]["mapping_status"] == EXACT_OBJECT_PATH_MATCH


def test_missing_object_remains_unresolved():
    record = build_champion_spell_source_record(_champion(), _base(), {}, {})
    assert record["primary_spells"][0]["mapping_status"] == PRIMARY_SPELL_OBJECT_NOT_FOUND


def test_ambiguous_object_path_remains_explicit():
    record = build_champion_spell_source_record(_champion(), _base(), {"a": _spell("QPath"), "b": _spell("QPath")}, {})
    assert record["primary_spells"][0]["mapping_status"] == PRIMARY_SPELL_PATH_AMBIGUOUS


def test_data_values_and_multiple_calculations_are_preserved():
    calculations = {"One": {"~class": "GameCalculation"}, "Two": {"~class": "GameCalculationModified"}}
    object_ = _spell("QPath", calculations)
    object_["mSpell"]["DataValues"] = [{"mName": "Zero", "mValues": [0]}]
    record = build_champion_spell_source_record(_champion(), _base(), {"QPath": object_}, {})["primary_spells"][0]
    assert record["raw_data_values"][0]["mValues"] == [0]
    assert record["raw_calculation_names"] == ["One", "Two"]


def test_recursive_nodes_unknown_classes_and_unknown_fields_are_preserved():
    graph = inventory_calculation_graph({"Root": {"unknownHash": 7, "child": {"~class": "FutureThing", "mDataValue": "X"}, "~class": "GameCalculation"}})
    assert graph["status"] == CALCULATIONS_EXPOSED
    assert {node["calculation_class"] for node in graph["nodes"]} == {None, "GameCalculation", "FutureThing"}
    assert any(node["interpretation_status"] == NO_CALCULATION_CLASS_EXPOSED for node in graph["nodes"])
    assert all(
        node["interpretation_status"] == UNINTERPRETED_CALCULATION_CLASS
        for node in graph["nodes"]
        if node["calculation_class"] is not None
    )
    assert any("unknownHash" in node["field_names"] for node in graph["nodes"])


def test_calculation_free_spell_and_no_fallback_contract():
    record = build_champion_spell_source_record(_champion(), _base(), {"QPath": _spell("QPath")}, {})["primary_spells"][0]
    assert record["calculation_status"] == NO_CALCULATIONS_EXPOSED


def test_classless_nodes_and_nested_raw_fields_are_inventoried():
    graph = inventory_calculation_graph(
        {"Formula": {"unclassified": {"unknownHash": 7}}}
    )
    assert len(graph["nodes"]) == 3
    nested = next(
        node for node in graph["nodes"]
        if node["graph_path"] == "mSpellCalculations/Formula/unclassified"
    )
    assert nested["calculation_class"] is None
    assert nested["raw_node_payload"] == {"unknownHash": 7}
    assert nested["interpretation_status"] == NO_CALCULATION_CLASS_EXPOSED


def test_empty_calculation_mapping_is_not_exposed():
    graph = inventory_calculation_graph({})
    assert graph["status"] == NO_CALCULATIONS_EXPOSED
    assert graph["nodes"] == []


def test_non_exact_patch_has_no_latest_or_previous_source_fallback():
    catalog = build_champion_spell_source_catalog(
        {
            "champion_knowledge_version": "champion_knowledge_phase2b1_c_v1",
            "resolved_ddragon_version": "16.15.1",
            "locale": "fr_FR",
            "records": {"Test": _champion()},
        }
    )
    assert catalog["source_status"] == SOURCE_UNAVAILABLE
    assert catalog["records"] == {}
    assert catalog["no_latest_or_previous_patch_fallback"] is True


def main():
    tests = sorted((name, fn) for name, fn in globals().items() if name.startswith("test_") and callable(fn))
    for _name, fn in tests:
        fn()
    print(f"Champion Spell Source synthetic checks: PASS ({len(tests)}/{len(tests)})")


if __name__ == "__main__":
    main()
