from knowledge.combat_stat_snapshot_synthetic_checks import champion
from knowledge.combat_stat_snapshot import build_combat_snapshot


def main():
    item={"normalized_stats":[{"stat":"attack_speed_percent","value":0.25,"source":"DDRAGON_STATS"}]}
    ratio={"attack_speed_ratio":0.625}
    result=build_combat_snapshot(champion(),1,{1:item},[1],attack_speed_source_record=ratio)
    assert abs(result["stats"]["attack_speed"]-(0.65+0.625*0.25))<1e-12
    assert result["stats"]["attack_speed_native"]==0.65
    print("Combat stat snapshot precision checks: PASS (2/2)")


if __name__=="__main__": main()
