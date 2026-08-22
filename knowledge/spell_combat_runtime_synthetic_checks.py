from knowledge.champion_spell_source import CHAMPION_SPELL_SOURCE_VERSION
from knowledge.combat_stat_snapshot_synthetic_checks import champion
from knowledge.spell_combat_runtime import COMPONENTS_RESOLVED_TOTAL_NOT_COMPOSABLE, TOTAL_DAMAGE_RESOLVED, resolve_spell_combat


def main():
    source=champion(); target=champion()
    spell={"champion_spell_source_version":CHAMPION_SPELL_SOURCE_VERSION,"champion_id":"Test","slot":"Q","raw_data_values":[],"raw_calculation_names":["QDamage"],"raw_m_spell_calculations":{"QDamage":{"~class":"NumberCalculationPart","mNumber":100}},"calculation_nodes":[]}
    semantic={"effects":[{"effect_type":"MAGIC_DAMAGE"}]}
    result=resolve_spell_combat(source,target,spell,semantic,source_level=1,target_level=1,spell_rank=1,max_rank=5)
    assert result["status"]==COMPONENTS_RESOLVED_TOTAL_NOT_COMPOSABLE and result["total_damage"] is None
    summed=resolve_spell_combat(source,target,spell,semantic,source_level=1,target_level=1,spell_rank=1,max_rank=5,explicitly_composable=True)
    assert summed["status"]==TOTAL_DAMAGE_RESOLVED and summed["total_damage"]==10000/132
    print("Spell combat runtime synthetic checks: PASS (2/2)")


if __name__=="__main__": main()
