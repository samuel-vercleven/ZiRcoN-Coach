from knowledge.champion_spell_formula_runtime import evaluate_spell_calculation
from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION


def main():
    spell={"champion_spell_source_version":CHAMPION_SPELL_SOURCE_VERSION,"champion_id":"Test","slot":"Q","source_commit":"fixture","object_path":"fixture/Q","raw_data_values":[],"raw_m_spell_calculations":{"Amount":{"~class":"NumberCalculationPart","mNumber":12.5}}}
    result=evaluate_spell_calculation(spell,"Amount",spell_rank=1,max_rank=5,source_snapshot={"stats":{}})
    assert result["result"].value==12.5 and result["calculation_key"]=="Amount"
    assert result["provenance"]["source_path"]=="fixture/Q"
    print("Spell formula runtime synthetic checks: PASS (2/2)")


if __name__=="__main__": main()
