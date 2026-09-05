from __future__ import annotations

from services.analysis_contracts import ANALYZER_CACHE_VERSIONS, ANALYZER_VERSIONS
from services.post_game_analysis import PostGameAnalysisService


def _metric_keys(payload: dict) -> set[str]:
    return {metric["raw_key"] for event in payload["events"] for metric in event.get("metrics", [])}


def main() -> None:
    service = PostGameAnalysisService(None, None)
    tempo = service._tempo_payload({"EARLY_CLEAR": {
        "minutes": 7.0, "farmable_minutes": 3.0, "mirrored_minutes": 2.0, "strict_minutes": 2.0,
        "player_xp_per_min": 360.2, "player_jungle_cs_per_min": 6.14,
        "relative_gold_per_min": 1.57, "relative_xp_per_min": -62.3,
        "relative_jungle_cs_per_min": -1.57, "farmable_xp_per_min": 311.2,
        "farmable_jungle_cs_per_min": 5.33, "mirrored_relative_gold_per_min": -137.5,
        "mirrored_relative_xp_per_min": -237.9, "mirrored_relative_jungle_cs_per_min": -6.0,
        "tempo_score": 42.7, "pathing_score": 35.3, "sustained_pathing_holes": 2,
        "single_minute_watches": 1,
    }})
    assert "SUPPORTED CONTEXT" not in str(tempo)
    assert {"minutes", "tempo_score", "pathing_score", "player_xp_per_min", "player_jungle_cs_per_min", "relative_gold_per_min", "relative_xp_per_min", "relative_jungle_cs_per_min"} <= _metric_keys(tempo)
    assert tempo["events"][0]["technical"] and len(tempo["findings"]) == 2

    objective = service._objective_payload([{
        "timestamp": 520239, "objective_kind": "GRUBS", "objective_family": "GRUBS",
        "monster_type": "HORDE", "secured_side": "ENEMY", "player_proximity_pre": "MID",
        "opponent_proximity_pre": "NEAR", "entry_state": "BEHIND", "entry_gold_diff": -240,
        "entry_xp_diff": -110, "entry_jungle_cs_diff": -4, "entry_level_diff": -1,
        "contest_evidence": "MEDIUM", "trade_evidence": "ALLY_COUNTER_OBJECTIVE",
        "prior_trade_context": "NONE", "preparation_score": 5.3, "preparation_label": "LOW",
        "preparation_reference_size": 61, "preparation_reference_scope": "CHAMPION_FAMILY_TIME",
        "conversion_score": 46.8, "conversion_label": "BELOW_BASELINE",
        "conversion_reference_size": 61, "conversion_reference_scope": "CHAMPION_FAMILY_TIME",
        "sequence_classification": "LOST_WITH_COMPENSATION", "short_pre_objective_death": True,
        "ally_counter_objectives": ["DRAGON"], "enemy_counter_objectives": [],
        "resource_compensation_gold_change": 150, "frozen_tempo_score_change": -4.0,
    }])
    assert "context available" not in str(objective)
    assert {"secured_side", "sequence_classification", "player_proximity_pre/opponent_proximity_pre", "entry_state", "entry_*_diff", "contest_evidence", "trade_evidence", "preparation_score/label", "conversion_score/label"} <= _metric_keys(objective)
    assert "preparation_reference=CHAMPION_FAMILY_TIME N=61" in objective["events"][0]["technical"]

    reset = service._reset_payload([{
        "start_timestamp": 233644, "phase": "EARLY_CLEAR", "reset_origin": "VOLUNTARY_RESET_PROXY",
        "sequence_classification": "VOLUNTARY_NEUTRAL", "purchase_count": 2, "sale_count": 0,
        "undo_count": 0, "purchased_item_ids": [3057, 1036], "current_gold_before_frame": 904,
        "current_gold_drop_proxy": 604, "entry_gold_diff": 0, "entry_xp_diff": 0,
        "entry_jungle_cs_diff": 0, "reentry_gold_diff": 460, "reentry_xp_diff": 111,
        "reentry_jungle_cs_diff": 0, "reentry_score": 18.2, "reentry_label": "LOW",
        "reentry_reference_size": 76, "reentry_reference_scope": "CHAMPION_PHASE_ORIGIN_TIME",
        "post_reset_death_120": False, "high_unspent_gold_context": False,
    }])
    rendered = str(reset)
    assert "Production après reset vs historique" in rendered
    assert "mauvais reset" not in rendered.lower() and "excellent recall" not in rendered.lower()
    assert reset["findings"] and "ne qualifie pas causalement" in reset["findings"][0]["detail"]

    build = service._build_payload({
        "final_validation": {"status": "EXACT", "riot_final_counter": {6672: 1, 3111: 1},
                             "riot_trinket": 3340, "reconstructed_final_counter": {6672: 1, 3111: 1},
                             "effective_reconstructed_final_counter": {6672: 1, 3111: 1}},
        "milestones": {"first_meaningful_purchase": {"timestamp": 1000, "time": "00:01", "item_id": 1036, "item_name": "Épée longue"}, "boots_purchase": None, "boots_upgrade": None,
                       "completed_major_items": [{"timestamp": 500000, "time": "08:20", "item_id": 6672, "item_name": "Tueur de krakens"}]},
        "transactions": [{"time": "00:01", "event_type": "ITEM_PURCHASED", "item_name": "Épée longue", "shop_visit_id": 1, "reconstruction_status": "OK"}],
    })
    assert build["events"][0]["item_ids"] == [6672, 3111, 3340]
    assert len(build["events"]) == 3 and build["technical_details"]
    assert not build["findings"] and "optimal" in build["summary"]

    assert len(set(ANALYZER_CACHE_VERSIONS.values())) == len(ANALYZER_VERSIONS)
    for name in ANALYZER_VERSIONS:
        assert ANALYZER_CACHE_VERSIONS[name] != ANALYZER_VERSIONS[name]
    print("ZiRcoN Coach remaining adapters check: PASS")


if __name__ == "__main__": main()
