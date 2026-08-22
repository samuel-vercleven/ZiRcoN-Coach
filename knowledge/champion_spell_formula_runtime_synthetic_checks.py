from knowledge.champion_spell_formula_runtime import evaluate_spell_calculation
from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION
from knowledge.combat_stat_snapshot import STATIC_STAT_PARTIAL


def main():
    spell={"champion_spell_source_version":CHAMPION_SPELL_SOURCE_VERSION,"champion_id":"Test","slot":"Q","source_commit":"fixture","object_path":"fixture/Q","raw_data_values":[],"raw_m_spell_calculations":{"Amount":{"~class":"NumberCalculationPart","mNumber":12.5}}}
    result=evaluate_spell_calculation(spell,"Amount",spell_rank=1,max_rank=5,source_snapshot={"stats":{}})
    assert result["result"].value==12.5 and result["calculation_key"]=="Amount"
    assert result["provenance"]["source_path"]=="fixture/Q"
    partial_snapshot={"status":"SNAPSHOT_PARTIAL","stats":{"attack_damage_total":100,"ability_haste":None},"stat_resolution":{"ability_haste":{"status":STATIC_STAT_PARTIAL}}}
    independent=evaluate_spell_calculation(spell,"Amount",spell_rank=1,max_rank=5,source_snapshot=partial_snapshot)
    assert independent["result"].value==12.5
    print("Spell formula runtime synthetic checks: PASS (3/3)")


if __name__=="__main__": main()
