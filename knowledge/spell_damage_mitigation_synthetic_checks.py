from knowledge.spell_damage_mitigation import MITIGATION_INPUT_UNRESOLVED, mitigate_component


def main():
    attacker = {
        "stats": {
            "armor_penetration_percent": 0.0,
            "armor_penetration_percent_sources": [],
            "armor_penetration_flat": 0.0,
            "lethality": 0.0,
            "magic_penetration_percent": 0.0,
            "magic_penetration_percent_sources": [],
            "magic_penetration_flat": 0.0,
        }
    }
    target = {"stats": {"armor": 100.0, "armor_native": 100.0, "magic_resistance": 25.0}}
    base = {"status": "RAW_DAMAGE_RESOLVED", "raw_damage": 100.0}
    assert mitigate_component({**base, "damage_type": "PHYSICAL"}, attacker, target)["post_mitigation_damage"] == 50.0
    assert mitigate_component({**base, "damage_type": "MAGIC"}, attacker, target)["post_mitigation_damage"] == 80.0
    assert mitigate_component({**base, "damage_type": "TRUE"}, attacker, target)["post_mitigation_damage"] == 100.0

    attacker["stats"]["armor_penetration_percent"] = 0.44
    attacker["stats"]["armor_penetration_percent_sources"] = [
        {"item_id": "A", "value": 0.30, "source": "DDRAGON_STATS"},
        {"item_id": "B", "value": 0.20, "source": "DDRAGON_STATS"},
    ]
    result = mitigate_component({**base, "damage_type": "PHYSICAL"}, attacker, target)
    assert abs(result["penetration_inputs"]["percentage_combined"] - 0.44) < 1e-12
    assert abs(result["effective_resistance"] - 56.0) < 1e-12

    attacker["stats"]["lethality"] = None
    attacker["stat_resolution"] = {"lethality": {"status": "STATIC_STAT_PARTIAL"}}
    assert mitigate_component({**base, "damage_type": "PHYSICAL"}, attacker, target)["status"] == MITIGATION_INPUT_UNRESOLVED
    print("Spell damage mitigation synthetic checks: PASS (6/6)")


if __name__ == "__main__":
    main()
