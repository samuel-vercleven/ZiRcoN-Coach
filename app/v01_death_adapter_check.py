from __future__ import annotations

from services.post_game_analysis import PostGameAnalysisService


def main() -> None:
    service = PostGameAnalysisService(None, None)  # _death_payload is a pure adapter.
    raw_v11_row = {
        "timestamp": 670_143,
        "killer_champion": "Kayn",
        "killer_position": "JUNGLE",
        "killed_by_enemy_jungler": True,
        "advantage_state_before_death": "EN_RETARD",
        "death_zone_approx": "RIVER_OR_MID_APPROX",
        "current_gold_before_death": 693,
        "resource_cost_score": 82.0255,
        "resource_cost_label": "TRÈS ÉLEVÉ",
        "score_reference_size": 200,
        "impact_interval_seconds": 60.013,
        "gold_cost_60": 602,
        "cs_cost_60": 12,
        "xp_cost_60": 652,
        "enemy_objectives_after": 1,
        "ally_objectives_after": 0,
        "enemy_towers_after": 1,
        "trade": True,
        "enemy_jungle_trade": True,
        "death_chain": True,
        "death_chain_size": 4,
        "death_spiral": True,
        "death_spiral_score": 77.9294,
    }

    payload = service._death_payload([raw_v11_row])
    rendered = "\n".join(payload["evidence"])
    assert "UNKNOWN" not in rendered
    assert "pre-death state EN RETARD" in rendered
    assert "historical severity 82.0/100 (TRÈS ÉLEVÉ)" in rendered
    assert "killed by Kayn (JUNGLE)" in rendered
    assert "zone RIVER OR MID APPROX" in rendered
    assert "60s bracket" in rendered
    assert "relative costs Gold 602, CS 12.0, XP 652" in rendered
    assert "enemy jungler was the killer" in rendered
    assert "trade observed (enemy jungler killed)" in rendered
    assert "90s context: enemy objectives 1, ally objectives 0, allied towers lost 1" in rendered
    assert "death chain size 4" in rendered
    assert "severe death spiral 77.9/100" in rendered
    assert payload["summary"].endswith("état avant la mort disponible pour 1/1.")
    assert payload["source_version"] == "death_analyzer_v11"

    warmup = service._death_payload([{
        "timestamp": 60_000,
        "advantage_state_before_death": "EQUILIBRE",
        "resource_cost_score": None,
        "resource_cost_label": "WARMUP",
        "score_reference_size": 12,
    }])
    assert "historical severity WARMUP • 12 prior-death reference(s)" in warmup["evidence"][0]
    assert "UNKNOWN" not in warmup["evidence"][0]

    genuinely_missing = service._death_payload([{"timestamp": 60_000}])
    assert "pre-death state UNKNOWN" in genuinely_missing["evidence"][0]
    assert genuinely_missing["summary"].endswith("état avant la mort disponible pour 0/1.")

    print("ZiRcoN Coach Death v11 adapter check: PASS")


if __name__ == "__main__":
    main()
