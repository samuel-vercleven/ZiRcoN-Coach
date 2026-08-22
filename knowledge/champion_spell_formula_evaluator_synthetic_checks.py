from knowledge.champion_spell_formula_evaluator import *
from knowledge.combat_formula_types import *
from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION

def spell(calcs, values=None): return {"champion_spell_source_version":CHAMPION_SPELL_SOURCE_VERSION,"raw_m_spell_calculations":calcs,"raw_data_values":values or []}
def main():
    assert evaluate_calculation(spell({"x":{"~class":"NumberCalculationPart","mNumber":0}}),"x").value == 0
    assert evaluate_calculation(spell({"x":{"~class":"NumberCalculationPart","mNumber":-2.5}}),"x").value == -2.5
    assert evaluate_calculation(spell({"x":{"~class":"Future"}}),"x").status == UNSUPPORTED_CLASS
    assert evaluate_calculation(spell({"x":{"mNumber":1}}),"x").status == UNSUPPORTED_CLASS
    s=spell({"x":{"~class":"GameCalculation","mFormulaParts":[{"~class":"NumberCalculationPart","mNumber":2},{"~class":"NamedDataValueCalculationPart","mDataValue":"A"}]}},[{"name":"A","values":[0,3]}])
    assert evaluate_calculation(s,"x",{"spell_rank":1,"max_rank":1,"data_value_indexing_contract":None}).value == 5
    partial=spell({"x":{"~class":"GameCalculation","mFormulaParts":[{"~class":"NumberCalculationPart","mNumber":2},{"~class":"Future"}]}})
    assert evaluate_calculation(partial,"x").status == PARTIALLY_RESOLVED
    assert evaluate_calculation(spell({"x":{"~class":"NamedGameCalculationCalculationPart","mSpellCalculationKey":"x"}}),"x").status == CYCLE_DETECTED
    assert evaluate_calculation(spell({"x":{"~class":"StatByCoefficientCalculationPart","mStat":2,"mCoefficient":1}}),"x").status == UNRESOLVED_STAT_REFERENCE
    print("Spell formula evaluator synthetic checks: PASS (8/8)")
if __name__ == "__main__": main()
