from knowledge.combat_stat_snapshot import *


def champion():
    names = {"health_base": 600, "health_growth": 100, "attack_damage_base": 60, "attack_damage_growth": 3, "armor_base": 30, "armor_growth": 4, "magic_resistance_base": 32, "magic_resistance_growth": 1, "move_speed": 340, "attack_range": 125, "crit_base": 0, "crit_growth": 0, "resource_base": 0, "resource_growth": 0, "health_regen_base": 0, "health_regen_growth": 0, "resource_regen_base": 0, "resource_regen_growth": 0, "attack_speed_base": 0.65, "attack_speed_growth": 0}
    return {"champion_id": "Test", "name": "Test", "champion_knowledge_version": "champion_knowledge_phase2b1_c_v1", "ddragon_version": "16.16.1", "locale": "fr_FR", "normalized_stats": [{"stat": key, "value": value} for key, value in names.items()]}


def main():
    items = {
        1: {
            "item_id": 1,
            "name": "Mixed item",
            "normalized_stats": [
                {"stat": "attack_damage", "value": 20, "source": "DDRAGON_STATS", "confidence": "STRUCTURED"},
                {"stat": "health", "value": 200, "source": "DDRAGON_STATS", "confidence": "STRUCTURED"},
                {"stat": "ability_haste", "value": 15, "source": "DDRAGON_DESCRIPTION_STATS", "confidence": "DESCRIPTION_EXPLICIT"},
                {"stat": "lethality", "value": 10, "source": "DDRAGON_DESCRIPTION_STATS", "confidence": "DESCRIPTION_EXPLICIT"},
            ],
        }
    }
    snapshot = build_combat_snapshot(champion(), 1, items, [1], current_health=700)
    assert snapshot["stats"]["attack_damage_total"] == 80 and snapshot["stat_resolution"]["attack_damage_total"]["status"] == STATIC_STAT_RESOLVED
    assert snapshot["stats"]["health_max"] == 800 and snapshot["stats"]["health_missing"] == 100
    assert snapshot["stats"]["ability_haste"] is None and snapshot["stat_resolution"]["ability_haste"]["known_partial_value"] == 0
    assert snapshot["stats"]["lethality"] is None and len(snapshot["excluded_static_facts"]) == 2
    assert snapshot["status"] == SNAPSHOT_PARTIAL and snapshot["runes_applied"] is False
    assert build_combat_snapshot(champion(), 1)["stats"]["ability_haste"] == 0
    assert build_combat_snapshot(champion(), 19)["status"] == SNAPSHOT_PARTIAL
    print("Combat stat snapshot synthetic checks: PASS (7/7)")


if __name__ == "__main__":
    main()
