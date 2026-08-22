from knowledge.combat_stat_snapshot import STATIC_STAT_RESOLVED, build_combat_snapshot
from knowledge.combat_stat_snapshot_synthetic_checks import champion


def main():
    items = {
        1: {"item_id": 1, "name": "AS", "normalized_stats": [{"stat": "attack_speed_percent", "value": 0.25, "source": "DDRAGON_STATS"}]},
        2: {"item_id": 2, "name": "Pen A", "normalized_stats": [{"stat": "armor_penetration_percent", "value": 0.30, "source": "DDRAGON_STATS"}]},
        3: {"item_id": 3, "name": "Pen B", "normalized_stats": [{"stat": "armor_penetration_percent", "value": 0.20, "source": "DDRAGON_STATS"}]},
    }
    result = build_combat_snapshot(champion(), 1, items, [1, 2, 3], attack_speed_source_record={"attack_speed_ratio": 0.625})
    assert abs(result["stats"]["attack_speed"] - (0.65 + 0.625 * 0.25)) < 1e-12
    assert result["stats"]["attack_speed_native"] == 0.65
    assert [row["value"] for row in result["stats"]["armor_penetration_percent_sources"]] == [0.30, 0.20]
    assert abs(result["stats"]["armor_penetration_percent"] - 0.44) < 1e-12
    assert result["stat_resolution"]["armor_penetration_percent"]["status"] == STATIC_STAT_RESOLVED
    print("Combat stat snapshot precision checks: PASS (5/5)")


if __name__ == "__main__":
    main()
