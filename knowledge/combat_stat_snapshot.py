"""Static, factual combat-stat snapshots from frozen level/item layers."""
from collections import Counter
from knowledge.champion_level_stats import LEVEL_STATS_VERSION, resolve_champion_stats_at_level
from knowledge.item_knowledge import ITEM_KNOWLEDGE_VERSION

SNAPSHOT_VERSION="combat_stat_snapshot_phase2g_v1"
SNAPSHOT_RESOLVED="SNAPSHOT_RESOLVED"
SNAPSHOT_PARTIAL="SNAPSHOT_PARTIAL"

STATIC_ITEM_STATS={"health","attack_damage","ability_power","armor","magic_resistance","attack_speed_percent","critical_strike_chance","life_steal","armor_penetration_flat","armor_penetration_percent","magic_penetration_flat","magic_penetration_percent","flat_move_speed"}

def build_combat_snapshot(champion_record,level,item_records=None,item_ids=(),attack_speed_source_record=None,current_health=None,overrides=None):
    native=resolve_champion_stats_at_level(champion_record,level,attack_speed_source_record)
    base={name:fact.get("value") for name,fact in native["stats"].items()}
    bonuses=Counter(); unresolved=[]
    item_records=item_records or {}
    for item_id in item_ids:
        item=item_records.get(str(item_id)) or item_records.get(item_id)
        if not item: unresolved.append(f"ITEM_NOT_FOUND:{item_id}"); continue
        for stat in item.get("normalized_stats",[]):
            if stat.get("source")!="DDRAGON_STATS" or stat.get("stat") not in STATIC_ITEM_STATS or not isinstance(stat.get("value"),(int,float)):
                continue
            bonuses[stat["stat"]]+=stat["value"]
    stats={
        "health_native":base.get("health"),"health_bonus":bonuses["health"],
        "health_max":None if base.get("health") is None else base["health"]+bonuses["health"],
        "attack_damage_native":base.get("attack_damage"),"attack_damage_bonus":bonuses["attack_damage"],
        "attack_damage_total":None if base.get("attack_damage") is None else base["attack_damage"]+bonuses["attack_damage"],
        "ability_power":bonuses["ability_power"],"armor_native":base.get("armor"),"armor_bonus":bonuses["armor"],
        "armor":None if base.get("armor") is None else base["armor"]+bonuses["armor"],
        "magic_resistance_native":base.get("magic_resistance"),"magic_resistance_bonus":bonuses["magic_resistance"],
        "magic_resistance":None if base.get("magic_resistance") is None else base["magic_resistance"]+bonuses["magic_resistance"],
        "move_speed":None if base.get("move_speed") is None else base["move_speed"]+bonuses["flat_move_speed"],
        "attack_speed_native":base.get("attack_speed"),"attack_speed":base.get("attack_speed"),
        "critical_strike_chance":bonuses["critical_strike_chance"],"life_steal":bonuses["life_steal"],
        "ability_haste":0.0,"lethality":0.0,
        "armor_penetration_flat":bonuses["armor_penetration_flat"],"armor_penetration_percent":bonuses["armor_penetration_percent"],
        "magic_penetration_flat":bonuses["magic_penetration_flat"],"magic_penetration_percent":bonuses["magic_penetration_percent"],
    }
    ratio=(attack_speed_source_record or {}).get("attack_speed_ratio")
    if stats["attack_speed"] is not None and isinstance(ratio,(int,float)):
        stats["attack_speed"] += ratio*bonuses["attack_speed_percent"]
    elif bonuses["attack_speed_percent"]: unresolved.append("ATTACK_SPEED_RATIO_REQUIRED")
    if current_health is not None:
        if stats["health_max"] is None or current_health<0 or current_health>stats["health_max"]: unresolved.append("CURRENT_HEALTH_INVALID")
        else: stats.update({"health_current":current_health,"health_missing":stats["health_max"]-current_health})
    applied_overrides={}
    for name,value in (overrides or {}).items():
        if name not in stats or not isinstance(value,(int,float)) or isinstance(value,bool):
            unresolved.append(f"FACTUAL_OVERRIDE_UNSUPPORTED:{name}")
            continue
        stats[name]=value; applied_overrides[name]=value
    return {"snapshot_version":SNAPSHOT_VERSION,"status":SNAPSHOT_PARTIAL if unresolved or native["unresolved_count"] else SNAPSHOT_RESOLVED,"champion_id":champion_record.get("champion_id"),"level":level,"item_ids":list(item_ids),"stats":stats,"unresolved":unresolved,"native_unresolved":[fact.get("stat") for fact in native.get("unresolved",[])],"runes_applied":False,"factual_overrides":applied_overrides,"provenance":{"level_stats":LEVEL_STATS_VERSION,"item_knowledge":ITEM_KNOWLEDGE_VERSION,"ddragon_version":champion_record.get("ddragon_version"),"locale":champion_record.get("locale")}}
