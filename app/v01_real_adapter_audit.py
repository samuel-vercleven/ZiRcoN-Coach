from __future__ import annotations

from analysis.death_cost_analyzer import build_death_cost_dataset
from analysis.itemization_analyzer import build_itemization_history
from analysis.jungle_tempo_analyzer import build_tempo_intervals, summarize_match_phases
from analysis.objective_analyzer import build_objective_dataset, get_match_objectives
from analysis.reset_analyzer import build_reset_dataset, get_match_resets
from app.bootstrap import build_app_context
from database.tempo_reader import load_tempo_bundles
from services.analysis_contracts import ANALYZER_CACHE_VERSIONS


TEMPO_FIELDS = {
    "minutes", "farmable_minutes", "mirrored_minutes", "strict_minutes", "player_xp_per_min",
    "player_jungle_cs_per_min", "relative_gold_per_min", "relative_xp_per_min",
    "relative_jungle_cs_per_min", "farmable_xp_per_min", "farmable_jungle_cs_per_min",
    "mirrored_relative_gold_per_min", "mirrored_relative_xp_per_min",
    "mirrored_relative_jungle_cs_per_min", "tempo_score", "pathing_score",
    "sustained_pathing_holes", "single_minute_watches",
}
OBJECTIVE_FIELDS = {
    "objective_kind", "objective_family", "secured_side", "player_proximity_pre",
    "opponent_proximity_pre", "entry_state", "entry_gold_diff", "entry_xp_diff",
    "entry_jungle_cs_diff", "entry_level_diff", "contest_evidence", "trade_evidence",
    "prior_trade_context", "preparation_score", "preparation_label", "preparation_reference_size",
    "preparation_reference_scope", "conversion_score", "conversion_label", "conversion_reference_size",
    "conversion_reference_scope", "sequence_classification", "short_pre_objective_death",
    "pre_objective_death", "ally_counter_objectives", "enemy_counter_objectives",
    "resource_compensation_gold_change", "resource_compensation_xp_change",
    "resource_compensation_jungle_cs_change", "frozen_tempo_score_change",
}
RESET_FIELDS = {
    "start_timestamp", "phase", "reset_origin", "sequence_classification", "purchased_item_ids",
    "purchase_count", "sale_count", "undo_count", "current_gold_before_frame",
    "current_gold_drop_proxy", "objective_timing", "previous_objective_seconds",
    "previous_objective_kind", "next_objective_seconds", "next_objective_kind", "entry_gold_diff",
    "entry_xp_diff", "entry_jungle_cs_diff", "reentry_gold_diff", "reentry_xp_diff",
    "reentry_jungle_cs_diff", "post_player_xp_per_min", "post_player_jungle_cs_per_min",
    "post_relative_gold_per_min", "post_relative_xp_per_min", "post_relative_jungle_cs_per_min",
    "reentry_score", "reentry_label", "reentry_reference_size", "reentry_reference_scope",
    "post_reset_death_120", "high_unspent_gold_context", "frozen_tempo_score_change",
}


def _available(rows, fields):
    return sum(value is not None for row in rows for key, value in row.items() if key in fields)


def main() -> None:
    context = build_app_context(); player = context.local_data.player()
    targets = [match for match in context.local_data.matches() if match.position.upper() == "JUNGLE"][:5]
    assert len(targets) >= 3, "real audit requires at least three local Jungle SoloQ matches"
    bundles = load_tempo_bundles(player.puuid, position="JUNGLE")
    deaths = build_death_cost_dataset(player.puuid, position="JUNGLE")
    tempo = build_tempo_intervals(bundles)
    objectives = build_objective_dataset(bundles, deaths, tempo)
    resets = build_reset_dataset(bundles, deaths, tempo, objectives)
    build_history = build_itemization_history(player.puuid, position="JUNGLE")
    build_by_match = {row["match_id"]: row for row in build_history.get("matches", [])}
    totals = {"tempo_events": 0, "objective_events": 0, "reset_events": 0, "build_matches": 0,
              "tempo_available": 0, "objective_available": 0, "reset_available": 0}
    for match in targets:
        match_id = match.match_id
        raw_tempo = summarize_match_phases(tempo, match_id); raw_objectives = get_match_objectives(objectives, match_id); raw_resets = get_match_resets(resets, match_id); raw_build = build_by_match.get(match_id)
        fresh = {"tempo": context.analysis._tempo_payload(raw_tempo), "objectives": context.analysis._objective_payload(raw_objectives), "resets": context.analysis._reset_payload(raw_resets), "build": context.analysis._build_payload(raw_build)}
        cached = {row["analyzer"]: row for row in context.cache.reports(match_id) if ANALYZER_CACHE_VERSIONS.get(row["analyzer"]) == row["version"]}
        assert set(fresh) <= set(cached), f"missing current cache for {match_id}"
        for name, payload in fresh.items():
            assert cached[name]["payload"].get("events") == payload.get("events"), f"stale/mismapped {name} payload for {match_id}"
            assert cached[name]["payload"].get("source_version") == payload.get("source_version")
        phase_rows = list(raw_tempo.values())
        totals["tempo_events"] += len(phase_rows); totals["objective_events"] += len(raw_objectives); totals["reset_events"] += len(raw_resets); totals["build_matches"] += raw_build is not None
        totals["tempo_available"] += _available(phase_rows, TEMPO_FIELDS)
        totals["objective_available"] += _available(raw_objectives, OBJECTIVE_FIELDS)
        totals["reset_available"] += _available(raw_resets, RESET_FIELDS)
    print("ZiRcoN Coach real adapter audit: PASS")
    print(f"- matches cross-checked: {len(targets)}")
    print(f"- raw/presentation events: tempo {totals['tempo_events']}, objectives {totals['objective_events']}, resets {totals['reset_events']}, build matches {totals['build_matches']}")
    print(f"- non-null required field occurrences mapped: tempo {totals['tempo_available']}/{totals['tempo_available']}, objectives {totals['objective_available']}/{totals['objective_available']}, resets {totals['reset_available']}/{totals['reset_available']}")
    print("- intentionally omitted from primary cards: unrelated raw diagnostics; retained source enums/scopes and v22 transactions in technical details")


if __name__ == "__main__": main()
