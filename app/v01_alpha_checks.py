from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from services.cache_repository import CacheRepository
from services.local_data import LocalDataService
from services.post_game_analysis import (
    ANALYZER_CACHE_VERSIONS,
    PostGameAnalysisService,
)
from services.riot_client import DynamicRiotClient, RiotResult, RiotStatus
from services.riot_sync import RiotSyncService
from services.runtime_settings import RuntimeSettingsService


def _database(path: Path) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE matches(match_id TEXT PRIMARY KEY, game_creation INTEGER, game_duration INTEGER, game_version TEXT, queue_id INTEGER, raw_json TEXT)")
        connection.execute("""CREATE TABLE participants(id INTEGER PRIMARY KEY, match_id TEXT, puuid TEXT, riot_name TEXT, riot_tag TEXT,
            team_id INTEGER, position TEXT, champion_id INTEGER, champion_name TEXT, kills INTEGER, deaths INTEGER, assists INTEGER,
            cs INTEGER, gold INTEGER, damage_to_champions INTEGER, vision_score INTEGER, win INTEGER,
            item0 INTEGER, item1 INTEGER, item2 INTEGER, item3 INTEGER, item4 INTEGER, item5 INTEGER, item6 INTEGER)""")
        connection.execute("INSERT INTO matches VALUES ('EUW1_TEST', 1700000000000, 1800, '16.16.1', 420, '{}')")
        connection.execute("INSERT INTO participants VALUES (1,'EUW1_TEST','p','Player','EUW',100,'JUNGLE',1,'Annie',5,2,7,180,10000,20000,15,1,1001,0,0,0,0,0,0)")
        connection.commit()


class _Response:
    def __init__(self, status, data=None, headers=None): self.status_code, self._data, self.headers = status, data, headers or {}; self.text = ""
    def json(self): return self._data


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory); db = root / "test.db"; env = root / ".env"; settings_file = root / "settings.json"
        _database(db); env.write_text("OTHER_VALUE=preserved\n", encoding="utf-8")
        missing = RuntimeSettingsService(root / "missing.env", root / "missing.json")
        assert missing.api_status() == "NOT_CONFIGURED"
        settings = RuntimeSettingsService(env, settings_file); settings.save_api_key("FAKE_TEST_KEY"); settings.save_identity("Player#EUW", 20)
        assert "OTHER_VALUE=preserved" in env.read_text(encoding="utf-8")
        assert settings.api_key() == "FAKE_TEST_KEY" and "FAKE_TEST_KEY" not in settings.masked_key()

        cache = CacheRepository(db); cache.initialize(); local = LocalDataService(db, cache, settings)
        matches = local.matches(); assert len(matches) == 1 and matches[0].champion == "Annie"
        assert local.progress().win_rate == 100.0 and local.match_detail("EUW1_TEST") is not None
        analysis = PostGameAnalysisService(local, cache)
        cache.save_report("EUW1_TEST", "death", ANALYZER_CACHE_VERSIONS["death"], "PARTIAL", {"title": "Deaths", "summary": "Supported evidence", "evidence": ["fixture"], "source_version": "death_analyzer_v11"})
        cache.save_report("EUW1_TEST", "tempo", "stale_version", "AVAILABLE", {"title": "Stale", "summary": "Must not render", "evidence": []})
        report = analysis.get_match_insights("EUW1_TEST")
        assert len(report.insights) == 5 and report.insights[0].source_version == "death_analyzer_v11"
        tempo = next(value for value in report.insights if value.source_module == "tempo")
        assert tempo.status == "UNAVAILABLE" and tempo.source_version == "jungle_tempo_pathing_v17"

        session = Mock(); session.get.return_value = _Response(401)
        client = DynamicRiotClient("secret", session=session); assert client.account_by_riot_id("A", "B").status == RiotStatus.UNAUTHORIZED
        session.get.return_value = _Response(403); assert client.account_by_riot_id("A", "B").status == RiotStatus.FORBIDDEN
        session.get.return_value = _Response(429, headers={"Retry-After": "0"}); assert client.account_by_riot_id("A", "B").status == RiotStatus.RATE_LIMITED
        session.get.return_value = _Response(200, {"puuid": "p"}); assert client.account_by_riot_id("A", "B").ok
        assert "secret" not in repr(client)

        settings.save_api_key("REPLACEMENT_TEST_KEY")
        fake_client = Mock(); fake_client.account_by_riot_id.return_value = _ResponseResult({"puuid": "p"}); fake_client.summoner_by_puuid.return_value = _ResponseResult({"profileIconId": 1, "summonerLevel": 10}); fake_client.ranked_entries.return_value = _ResponseResult([]); fake_client.match_ids.return_value = _ResponseResult(["EXISTING", "NEW", "BAD"])
        fake_client.match.side_effect = lambda match_id: (
            RiotResult(RiotStatus.SERVER_ERROR, message="Riot service error.")
            if match_id == "BAD" else _ResponseResult({"metadata": {"matchId": match_id}})
        )
        fake_client.timeline.return_value = _ResponseResult({"metadata": {}, "info": {"frames": []}})
        analysis_mock = Mock()
        used_keys = []
        service = RiotSyncService(settings, local, cache, analysis_mock, client_factory=lambda key: used_keys.append(key) or fake_client)
        progress = []
        with patch("services.riot_sync.initialize_database") as initialize_db, \
             patch("services.riot_sync.initialize_timeline_tables") as initialize_timelines, \
             patch("services.riot_sync.match_exists", side_effect=lambda match_id: match_id == "EXISTING"), \
             patch("services.riot_sync.timeline_exists", return_value=False), \
             patch("services.riot_sync.save_match") as save_match_mock, \
             patch("services.riot_sync.save_timeline") as save_timeline_mock:
            result = service.sync(lambda message, value: progress.append((message, value)))
        assert result["status"] == "PARTIAL" and len(result["failures"]) == 1
        assert used_keys == ["REPLACEMENT_TEST_KEY"]
        assert [call.args[0] for call in fake_client.match.call_args_list] == ["NEW", "BAD"]
        save_match_mock.assert_called_once()
        assert [call.args[0] for call in save_timeline_mock.call_args_list] == ["EXISTING", "NEW"]
        analysis_mock.generate_for_matches.assert_called_once()
        assert [value for _message, value in progress] == sorted(value for _message, value in progress)
        assert progress[-1][1] == 100 and cache.sync_state()["status"] == "PARTIAL"
        initialize_db.assert_called_once(); initialize_timelines.assert_called_once()

        invalid_client = Mock(); invalid_client.account_by_riot_id.return_value = RiotResult(RiotStatus.UNAUTHORIZED, message="API key is invalid or expired.")
        invalid_service = RiotSyncService(settings, local, cache, analysis_mock, client_factory=lambda _key: invalid_client)
        with patch("services.riot_sync.initialize_database") as untouched:
            invalid_result = invalid_service.sync()
        assert invalid_result["status"] == RiotStatus.UNAUTHORIZED.value
        untouched.assert_not_called()
    print("ZiRcoN Coach V0.1 service checks: PASS")


class _ResponseResult:
    def __init__(self, data): self.data, self.status, self.message = data, RiotStatus.VALID, ""
    @property
    def ok(self): return True


if __name__ == "__main__": main()
