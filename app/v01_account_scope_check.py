from __future__ import annotations

import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from services.analysis_contracts import ANALYZER_CACHE_VERSIONS
from services.cache_repository import CacheRepository
from services.local_data import LocalDataService
from services.post_game_analysis import PostGameAnalysisService
from services.runtime_settings import RuntimeSettingsService


def _database(path: Path) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE matches(match_id TEXT PRIMARY KEY, game_creation INTEGER, game_duration INTEGER, game_version TEXT, queue_id INTEGER, raw_json TEXT)")
        connection.execute("""CREATE TABLE participants(id INTEGER PRIMARY KEY, match_id TEXT, puuid TEXT, riot_name TEXT, riot_tag TEXT, team_id INTEGER, position TEXT, champion_id INTEGER, champion_name TEXT, kills INTEGER, deaths INTEGER, assists INTEGER, cs INTEGER, gold INTEGER, damage_to_champions INTEGER, vision_score INTEGER, win INTEGER, item0 INTEGER, item1 INTEGER, item2 INTEGER, item3 INTEGER, item4 INTEGER, item5 INTEGER, item6 INTEGER)""")
        connection.execute("CREATE TABLE timelines(match_id TEXT PRIMARY KEY, raw_json TEXT NOT NULL)")
        rows = [
            ("A1", 1000, 420, "a", "Old", "ONE", "JUNGLE"), ("A2", 2000, 420, "a", "Old", "ONE", "JUNGLE"), ("A3", 3000, 420, "a", "Old", "ONE", "JUNGLE"),
            ("B_JG", 5000, 420, "b", "Active", "EUW", "JUNGLE"), ("B_MID", 4000, 420, "b", "Active", "EUW", "MIDDLE"),
            ("B_ARENA", 6000, 450, "b", "Active", "EUW", "MIDDLE"),
        ]
        for index, (match_id, creation, queue, puuid, name, tag, role) in enumerate(rows, 1):
            connection.execute("INSERT INTO matches VALUES (?, ?, 1800, '16.16.1', ?, '{}')", (match_id, creation, queue))
            connection.execute("INSERT INTO participants VALUES (?, ?, ?, ?, ?, 100, ?, 1, 'Annie', 1, 2, 3, 100, 5000, 10000, 10, 1, 1001, 2003, 0, 0, 0, 0, 3340)", (index, match_id, puuid, name, tag, role))
        connection.execute("INSERT INTO timelines VALUES ('A1', '{}')"); connection.execute("INSERT INTO timelines VALUES ('B_JG', '{}')"); connection.commit()


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory); db = root / "scope.db"; _database(db)
        settings = RuntimeSettingsService(root / ".env", root / "settings.json"); settings.save_identity("Active#EUW", 20)
        cache = CacheRepository(db); cache.initialize(); local = LocalDataService(db, cache, settings)
        assert local.player().puuid == "b"
        assert [match.match_id for match in local.matches()] == ["B_JG", "B_MID"]
        assert all(match.queue == "Ranked Solo/Duo" for match in local.matches())
        assert local.status().match_count == 2 and local.status().timeline_count == 1

        cache.save_profile("b", {"riot_id": "Active#EUW", "tier": "GOLD", "rank": "II"})
        assert local.player().profile_status == "CACHED"
        settings.mark_profile_current("b"); assert local.player().profile_status == "CURRENT"

        cache.save_report("B_JG", "tempo", "stale", "AVAILABLE", {})
        assert local.matches()[0].analysis_status == "UNAVAILABLE"
        cache.save_report("B_JG", "death", ANALYZER_CACHE_VERSIONS["death"], "AVAILABLE", {})
        assert local.matches()[0].analysis_status == "PARTIAL"
        for name, version in ANALYZER_CACHE_VERSIONS.items():
            cache.save_report("B_JG", name, version, "AVAILABLE", {})
        assert local.matches()[0].analysis_status == "AVAILABLE"
        assert local.status().analyzed_match_count == 1

        analysis = PostGameAnalysisService(local, cache)
        with patch("services.post_game_analysis.build_death_cost_dataset", return_value=[]) as death, \
             patch("services.post_game_analysis.build_itemization_history", return_value={"matches": []}) as build, \
             patch("services.post_game_analysis.load_tempo_bundles", return_value=[]) as bundles, \
             patch("services.post_game_analysis.build_tempo_intervals", return_value=[]), \
             patch("services.post_game_analysis.build_objective_dataset", return_value=[]), \
             patch("services.post_game_analysis.build_reset_dataset", return_value=[]):
            result = analysis.generate_for_matches(["B_JG", "B_MID"])
        assert result["generated"] == 10
        assert [call.kwargs["position"] for call in death.call_args_list] == ["JUNGLE", "MIDDLE"]
        assert [call.kwargs["position"] for call in build.call_args_list] == ["JUNGLE", "MIDDLE"]
        bundles.assert_called_once_with("b", position="JUNGLE")
        middle = analysis.get_match_insights("B_MID")
        assert all(value.status == "UNAVAILABLE" for value in middle.insights if value.source_module in ("tempo", "objectives", "resets"))
        assert all("MIDDLE" in value.summary for value in middle.insights if value.source_module in ("tempo", "objectives", "resets"))
    print("ZiRcoN Coach account/data scope check: PASS")


if __name__ == "__main__": main()
