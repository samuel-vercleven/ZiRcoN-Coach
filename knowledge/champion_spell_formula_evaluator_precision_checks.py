from knowledge.champion_spell_formula_evaluator import evaluate_calculation
from knowledge.combat_formula_types import RESOLVED, UNSUPPORTED_SIGNATURE
from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION

def main():
    record={"champion_spell_source_version":CHAMPION_SPELL_SOURCE_VERSION,"raw_data_values":[{"name":"Base","values":[0,10,20]}],"raw_m_spell_calculations":{"Damage":{"~class":"GameCalculation","mFormulaParts":[{"~class":"NamedDataValueCalculationPart","mDataValue":"Base"},{"~class":"NumberCalculationPart","mNumber":0.125}]}}}
    result=evaluate_calculation(record,"Damage",{"spell_rank":2,"max_rank":2,"data_value_indexing_contract":None})
    assert result.status==RESOLVED and abs(result.value-20.125)<1e-12 and len(result.child_results)==2
    assert evaluate_calculation({**record,"raw_m_spell_calculations":{"x":{"~class":"NumberCalculationPart"}}},"x").status==UNSUPPORTED_SIGNATURE
    print("Spell formula evaluator precision checks: PASS (2/2)")
if __name__ == "__main__": main()
