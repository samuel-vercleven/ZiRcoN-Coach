from knowledge.combat_stat_snapshot import *

def champion():
    names={"health_base":600,"health_growth":100,"attack_damage_base":60,"attack_damage_growth":3,"armor_base":30,"armor_growth":4,"magic_resistance_base":32,"magic_resistance_growth":1,"move_speed":340,"attack_range":125,"crit_base":0,"crit_growth":0,"resource_base":0,"resource_growth":0,"health_regen_base":0,"health_regen_growth":0,"resource_regen_base":0,"resource_regen_growth":0,"attack_speed_base":0.65,"attack_speed_growth":0}
    return {"champion_id":"Test","name":"Test","champion_knowledge_version":"champion_knowledge_phase2b1_c_v1","ddragon_version":"16.16.1","locale":"fr_FR","normalized_stats":[{"stat":k,"value":v} for k,v in names.items()]}
def main():
    items={"1":{"normalized_stats":[{"stat":"attack_damage","value":20,"source":"DDRAGON_STATS"},{"stat":"health","value":200,"source":"DDRAGON_STATS"},{"stat":"ability_power","value":50,"source":"DDRAGON_STATS"},{"stat":"UNKNOWN","value":999,"source":"DDRAGON_DESCRIPTION_STATS"}]}}
    snap=build_combat_snapshot(champion(),1,items,[1],current_health=700)
    assert snap["stats"]["attack_damage_total"]==80 and snap["stats"]["attack_damage_bonus"]==20
    assert snap["stats"]["health_max"]==800 and snap["stats"]["health_missing"]==100 and snap["stats"]["ability_power"]==50
    assert snap["runes_applied"] is False and snap["stats"]["ability_haste"]==0
    assert build_combat_snapshot(champion(),19)["status"]==SNAPSHOT_PARTIAL
    print("Combat stat snapshot synthetic checks: PASS (4/4)")
if __name__=="__main__": main()
