from knowledge.champion_spell_formula_taxonomy import *

def main():
    assert classify_node({"calculation_class": "NumberCalculationPart", "field_names": ["mNumber", "~class"]}) == SEMANTICS_VALIDATED_EXECUTABLE
    assert classify_node({"calculation_class": "NumberCalculationPart", "field_names": ["~class"]}) == UNRESOLVED_CLASS_SEMANTICS
    assert classify_node({"calculation_class": "NumberCalculationPart", "field_names": ["mNumber", "newField", "~class"]}) == UNRESOLVED_CLASS_SEMANTICS
    assert classify_node({"calculation_class": "FutureClass", "field_names": []}) == UNRESOLVED_CLASS_SEMANTICS
    assert classify_node({"calculation_class": None, "field_names": []}) == STRUCTURAL_CONTAINER_ONLY
    assert len(SUPPORTED_SIGNATURES) == 6
    print("Spell formula taxonomy synthetic checks: PASS (6/6)")

if __name__ == "__main__": main()
