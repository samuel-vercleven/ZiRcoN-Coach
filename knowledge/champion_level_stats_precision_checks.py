import math

from knowledge.champion_level_stats import (
    FORMULA_PROVENANCE,
    RESOLVED_ATTACK_SPEED_WITH_RATIO,
    UNRESOLVED_TOP_QUEST_LEVEL_FORMULA,
    resolve_champion_stats_at_level,
    resolve_growth_value,
    stat_growth_multiplier,
)


def _stat(stat, value, field):
    return {
        "stat": stat,
        "value": value,
        "source_field": field,
        "ddragon_version": "16.16.1",
    }


def _record(champion_id="Fixture"):
    values = {
        "health_base": 500,
        "health_growth": 90,
        "health_regen_base": 5,
        "health_regen_growth": 0.5,
        "resource_base": 0,
        "resource_growth": 0,
        "resource_regen_base": 0,
        "resource_regen_growth": 0,
        "attack_damage_base": 60,
        "attack_damage_growth": 3,
        "attack_speed_base": 0.65,
        "attack_speed_growth": 3,
        "armor_base": 22,
        "armor_growth": 3,
        "magic_resistance_base": 30,
        "magic_resistance_growth": 1.3,
        "move_speed": 330,
        "attack_range": 550,
        "crit_base": 0,
        "crit_growth": 0,
    }

    fields = {
        "health_base": "hp",
        "health_growth": "hpperlevel",
        "health_regen_base": "hpregen",
        "health_regen_growth": "hpregenperlevel",
        "resource_base": "mp",
        "resource_growth": "mpperlevel",
        "resource_regen_base": "mpregen",
        "resource_regen_growth": "mpregenperlevel",
        "attack_damage_base": "attackdamage",
        "attack_damage_growth": "attackdamageperlevel",
        "attack_speed_base": "attackspeed",
        "attack_speed_growth": "attackspeedperlevel",
        "armor_base": "armor",
        "armor_growth": "armorperlevel",
        "magic_resistance_base": "spellblock",
        "magic_resistance_growth": "spellblockperlevel",
        "move_speed": "movespeed",
        "attack_range": "attackrange",
        "crit_base": "crit",
        "crit_growth": "critperlevel",
    }

    return {
        "champion_knowledge_version": "champion_knowledge_phase2b1_c_v1",
        "champion_id": champion_id,
        "name": champion_id,
        "champion_key": "1",
        "partype": "None",
        "ddragon_version": "16.16.1",
        "locale": "fr_FR",
        "normalized_stats": [
            _stat(name, value, fields[name])
            for name, value in values.items()
        ],
    }


def _ratio(value):
    return {
        "status": "ATTACK_SPEED_RATIO_RESOLVED",
        "attack_speed_ratio": value,
        "source": "PINNED_LEAGUE_DATAMINE_RIOT_GAME_FILE",
        "source_type": "RIOT_GAME_FILE_GITHUB_DATAMINE",
        "source_url": "fixture",
        "source_patch": "16.16",
        "target_patch": "16.16",
        "source_status": (
            "PINNED_LEAGUE_DATAMINE_LIVE_26_16"
        ),
        "carry_forward": {
            "verification_status": "OFFICIAL_PATCH_NOTES_REVIEWED",
        },
    }


def test_zeri_old_level_18_anchor():
    assert math.isclose(
        resolve_growth_value(23, 3.5, 18),
        82.5,
    )


def test_zeri_new_level_18_anchor():
    assert math.isclose(
        resolve_growth_value(22, 3, 18),
        73.0,
    )


def test_veigar_level_18_anchor():
    assert math.isclose(
        resolve_growth_value(21, 4, 18),
        89.0,
    )


def test_level_2_is_non_linear():
    assert math.isclose(
        stat_growth_multiplier(2),
        0.72,
    )
    assert not math.isclose(
        stat_growth_multiplier(2),
        1.0,
    )


def test_formula_provenance_not_called_riot_official():
    assert FORMULA_PROVENANCE == (
        "VALIDATED_COMMUNITY_FORMULA_WITH_RIOT_ANCHORS"
    )


def test_attack_speed_ratio_affects_result():
    record = _record()

    a = resolve_champion_stats_at_level(
        record,
        18,
        _ratio(0.5),
    )
    b = resolve_champion_stats_at_level(
        record,
        18,
        _ratio(0.7),
    )

    assert a["stats"]["attack_speed"]["status"] == (
        RESOLVED_ATTACK_SPEED_WITH_RATIO
    )
    assert not math.isclose(
        a["stats"]["attack_speed"]["value"],
        b["stats"]["attack_speed"]["value"],
    )


def test_level_19_not_extrapolated():
    result = resolve_champion_stats_at_level(
        _record(),
        19,
        _ratio(0.625),
    )

    assert result["stats"]["attack_damage"]["status"] == (
        UNRESOLVED_TOP_QUEST_LEVEL_FORMULA
    )
    assert result["stats"]["attack_damage"]["value"] is None


def test_zero_resource_not_missing():
    result = resolve_champion_stats_at_level(
        _record(),
        18,
        _ratio(0.625),
    )
    assert result["stats"]["resource"]["value"] == 0
    assert result["stats"]["resource_regen"]["value"] == 0


def main():
    tests = sorted(
        (name, fn)
        for name, fn in globals().items()
        if name.startswith("test_") and callable(fn)
    )
    for _name, fn in tests:
        fn()

    print(
        "Champion Level Stats precision checks: "
        f"PASS ({len(tests)}/{len(tests)})"
    )


if __name__ == "__main__":
    main()
