import math

from knowledge.champion_attack_speed_source import (
    DATAMINE_COMMIT,
    SOURCE_EXACT_PATCH,
    TARGET_PATCH,
    extract_attack_speed_records,
)
from knowledge.champion_level_stats import (
    RESOLVED_ATTACK_SPEED_WITH_RATIO,
    RESOLVED_JHIN_ATTACK_SPEED_SPECIAL_CASE,
    UNRESOLVED_TOP_QUEST_LEVEL_FORMULA,
    resolve_champion_stats_at_level,
    stat_growth_multiplier,
)


def _stat(stat, value, source_field):
    return {
        "stat": stat,
        "value": value,
        "unit": "flat",
        "source_field": source_field,
        "ddragon_version": "16.16.1",
    }


def _champion(champion_id="Synthetic"):
    values = {
        "health_base": (600, "hp"),
        "health_growth": (100, "hpperlevel"),
        "health_regen_base": (5, "hpregen"),
        "health_regen_growth": (0.5, "hpregenperlevel"),
        "resource_base": (300, "mp"),
        "resource_growth": (40, "mpperlevel"),
        "resource_regen_base": (8, "mpregen"),
        "resource_regen_growth": (0.8, "mpregenperlevel"),
        "attack_damage_base": (60, "attackdamage"),
        "attack_damage_growth": (3.5, "attackdamageperlevel"),
        "attack_speed_base": (0.65, "attackspeed"),
        "attack_speed_growth": (3.0, "attackspeedperlevel"),
        "armor_base": (30, "armor"),
        "armor_growth": (4, "armorperlevel"),
        "magic_resistance_base": (32, "spellblock"),
        "magic_resistance_growth": (2.05, "spellblockperlevel"),
        "move_speed": (340, "movespeed"),
        "attack_range": (125, "attackrange"),
        "crit_base": (0, "crit"),
        "crit_growth": (0, "critperlevel"),
    }

    return {
        "champion_knowledge_version": "champion_knowledge_phase2b1_c_v1",
        "champion_id": champion_id,
        "champion_key": "999",
        "name": champion_id,
        "partype": "Mana",
        "ddragon_version": "16.16.1",
        "locale": "fr_FR",
        "normalized_stats": [
            _stat(name, value, field)
            for name, (value, field) in values.items()
        ],
    }


def _ratio(value=0.625):
    return {
        "status": "ATTACK_SPEED_RATIO_RESOLVED",
        "attack_speed_ratio": value,
        "source": "PINNED_LEAGUE_DATAMINE_RIOT_GAME_FILE",
        "source_type": "RIOT_GAME_FILE_GITHUB_DATAMINE",
        "source_url": "fixture",
        "source_patch": TARGET_PATCH,
        "target_patch": TARGET_PATCH,
        "source_status": SOURCE_EXACT_PATCH,
        "carry_forward": None,
    }


def test_multiplier_reference_points():
    assert math.isclose(
        stat_growth_multiplier(1),
        0,
    )
    assert math.isclose(
        stat_growth_multiplier(2),
        0.72,
    )
    assert math.isclose(
        stat_growth_multiplier(18),
        17,
    )


def test_attack_speed_uses_ratio():
    result = resolve_champion_stats_at_level(
        _champion(),
        18,
        _ratio(0.5),
    )
    attack = result["stats"]["attack_speed"]

    assert attack["status"] == (
        RESOLVED_ATTACK_SPEED_WITH_RATIO
    )

    expected = (
        0.65
        + 0.5 * ((3.0 * 17.0) / 100.0)
    )
    assert math.isclose(
        attack["value"],
        expected,
    )


def test_jhin_special_case():
    result = resolve_champion_stats_at_level(
        _champion("Jhin"),
        18,
        _ratio(0.0),
    )
    attack = result["stats"]["attack_speed"]

    assert attack["status"] == (
        RESOLVED_JHIN_ATTACK_SPEED_SPECIAL_CASE
    )

    expected = (
        0.65
        + 0.65 * ((3.0 * 17.0) / 100.0)
    )
    assert math.isclose(
        attack["value"],
        expected,
    )


def test_level_20_native_growth_remains_unresolved():
    result = resolve_champion_stats_at_level(
        _champion(),
        20,
        _ratio(),
    )

    assert result["stats"]["health"]["status"] == (
        UNRESOLVED_TOP_QUEST_LEVEL_FORMULA
    )
    assert (
        result["stats"]["health"]["value"]
        is None
    )


def test_pinned_live_26_16_commit():
    assert TARGET_PATCH == "16.16"
    assert DATAMINE_COMMIT == (
        "9245fd616059c6c658d1faa1029f0e18ea179154"
    )


def test_modifiable_float_parser():
    payload = {
        "Characters/Synthetic/CharacterRecords/Root": {
            "mCharacterName": "Synthetic",
            "attackSpeedModifiable": {
                "baseValue": 0.65,
                "~class": "ModifiableFloat",
            },
            "attackSpeedPerLevelModifiable": {
                "baseValue": 3.0,
                "~class": "ModifiableFloat",
            },
            "attackSpeedRatioModifiable": {
                "baseValue": 0.625,
                "~class": "ModifiableFloat",
            },
        }
    }

    records = extract_attack_speed_records(
        payload,
        "fixture",
        TARGET_PATCH,
    )

    record = records["synthetic"]
    assert record["attack_speed_ratio"] == 0.625
    assert record["attack_speed_cdragon"] == 0.65
    assert (
        record[
            "attack_speed_growth_percent_cdragon"
        ]
        == 3.0
    )


def test_jhin_zero_ratio_is_not_missing():
    payload = {
        "Characters/Jhin/CharacterRecords/Root": {
            "mCharacterName": "Jhin",
            "attackSpeedModifiable": {
                "baseValue": 0.625,
            },
            "attackSpeedRatioModifiable": {
                "baseValue": 0.0,
            },
        }
    }

    records = extract_attack_speed_records(
        payload,
        "fixture",
        TARGET_PATCH,
    )

    assert "jhin" in records
    assert (
        records["jhin"]["attack_speed_ratio"]
        == 0.0
    )


def main():
    tests = sorted(
        (name, fn)
        for name, fn in globals().items()
        if name.startswith("test_")
        and callable(fn)
    )

    for _name, fn in tests:
        fn()

    print(
        "Champion Level Stats synthetic checks: "
        f"PASS ({len(tests)}/{len(tests)})"
    )


if __name__ == "__main__":
    main()
