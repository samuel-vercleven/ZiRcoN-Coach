import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from app.paths import DEFAULT_DB_PATH
from viewmodels import (
    MatchDetailViewModel, MatchSummaryViewModel, PlayerViewModel,
    ProgressViewModel, StatusViewModel,
)
from services.cache_repository import CacheRepository
from services.analysis_contracts import ANALYZER_CACHE_VERSIONS, SOLO_QUEUE_ID
from services.runtime_settings import RuntimeSettingsService


class LocalDataService:
    """Read-only projection of the existing local SQLite history."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH,
                 cache: CacheRepository | None = None,
                 settings: RuntimeSettingsService | None = None):
        self.db_path = Path(db_path)
        self.cache = cache
        self.settings = settings

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def is_available(self) -> bool:
        return self.db_path.exists()

    def _primary_player(self) -> Optional[sqlite3.Row]:
        if not self.is_available():
            return None
        with closing(self._connection()) as connection:
            identity = self.settings.identity() if self.settings else None
            if identity:
                configured = connection.execute(
                    """SELECT p.puuid, p.riot_name, p.riot_tag, COUNT(*) AS games
                       FROM participants p JOIN matches m ON m.match_id=p.match_id
                       WHERE m.queue_id=? AND lower(p.riot_name)=lower(?)
                         AND lower(p.riot_tag)=lower(?)
                       GROUP BY p.puuid, p.riot_name, p.riot_tag
                       ORDER BY games DESC, p.puuid LIMIT 1""",
                    (SOLO_QUEUE_ID, identity.game_name, identity.tag_line),
                ).fetchone()
                return configured
            return connection.execute(
                """SELECT p.puuid, p.riot_name, p.riot_tag, COUNT(*) AS games
                   FROM participants p JOIN matches m ON m.match_id=p.match_id
                   WHERE m.queue_id=? GROUP BY p.puuid, p.riot_name, p.riot_tag
                   ORDER BY games DESC, p.puuid LIMIT 1""",
                (SOLO_QUEUE_ID,),
            ).fetchone()

    def player(self) -> PlayerViewModel:
        row = self._primary_player()
        if row is None:
            return PlayerViewModel()
        name = row["riot_name"] or "Local player"
        tag = row["riot_tag"]
        riot_id = f"{name}#{tag}" if tag else name
        profile = self.cache.profile(row["puuid"]) if self.cache else None
        if not profile:
            return PlayerViewModel(puuid=row["puuid"], riot_id=riot_id)
        rank_parts = [str(profile.get("tier") or ""), str(profile.get("rank") or "")]
        rank = " ".join(part for part in rank_parts if part) or "UNRANKED"
        return PlayerViewModel(puuid=row["puuid"], riot_id=str(profile.get("riot_id") or riot_id),
            rank=rank, lp=profile.get("lp"), profile_icon_id=profile.get("profile_icon_id"),
            summoner_level=profile.get("summoner_level"), ranked_wins=profile.get("ranked_wins"),
            ranked_losses=profile.get("ranked_losses"),
            profile_status=self.settings.profile_freshness(row["puuid"]) if self.settings else "CACHED")

    def _rows(self, limit: Optional[int] = None) -> list[sqlite3.Row]:
        player = self._primary_player()
        if player is None:
            return []
        query = """SELECT m.match_id, m.game_creation, m.game_duration, m.queue_id, m.game_version,
                          p.champion_name, p.kills, p.deaths, p.assists, p.cs, p.win,
                          p.position, p.item0, p.item1, p.item2, p.item3, p.item4, p.item5, p.item6
                   FROM matches m JOIN participants p ON p.match_id=m.match_id
                   WHERE p.puuid=? AND m.queue_id=?
                   ORDER BY m.game_creation DESC, m.match_id DESC"""
        params: list[object] = [player["puuid"], SOLO_QUEUE_ID]
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        with closing(self._connection()) as connection:
            return list(connection.execute(query, params).fetchall())

    def _coverage_map(self, match_ids: Iterable[str]) -> dict[str, str]:
        ids = list(match_ids)
        if not ids or not self.cache:
            return {}
        placeholders = ",".join("?" for _ in ids)
        with closing(self._connection()) as connection:
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            if "app_analysis_reports" not in tables:
                return {}
            rows = connection.execute(
                f"SELECT match_id, analyzer_name, analyzer_version, status FROM app_analysis_reports WHERE match_id IN ({placeholders})",
                ids,
            ).fetchall()
        found: dict[str, dict[str, str]] = {}
        for row in rows:
            if ANALYZER_CACHE_VERSIONS.get(row["analyzer_name"]) == row["analyzer_version"]:
                found.setdefault(row["match_id"], {})[row["analyzer_name"]] = row["status"]
        result = {}
        for match_id in ids:
            statuses = found.get(match_id, {})
            if len(statuses) == len(ANALYZER_CACHE_VERSIONS):
                result[match_id] = "AVAILABLE" if all(
                    value == "AVAILABLE" for value in statuses.values()) else "PARTIAL"
            elif statuses:
                result[match_id] = "PARTIAL"
            else:
                result[match_id] = "UNAVAILABLE"
        return result

    @staticmethod
    def _summary(row: sqlite3.Row, analysis_status: str = "UNAVAILABLE") -> MatchSummaryViewModel:
        timestamp = row["game_creation"] or 0
        played_at = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M") if timestamp else "UNKNOWN"
        inventory = tuple(int(row[f"item{index}"]) for index in range(6) if row[f"item{index}"])
        trinket = int(row["item6"]) if row["item6"] else None
        items = inventory + ((trinket,) if trinket else ())
        return MatchSummaryViewModel(
            match_id=row["match_id"], champion=row["champion_name"] or "Unknown champion",
            result="WIN" if row["win"] else "LOSS", kills=row["kills"] or 0,
            deaths=row["deaths"] or 0, assists=row["assists"] or 0, cs=row["cs"] or 0,
            duration_seconds=row["game_duration"] or 0, played_at=played_at,
            queue="Ranked Solo/Duo" if row["queue_id"] == 420 else str(row["queue_id"] or "UNKNOWN"),
            position=row["position"] or "UNKNOWN", items=items, trinket_id=trinket,
            game_version=row["game_version"] or "",
            analysis_status=analysis_status,
        )

    def matches(self, result_filter: str = "ALL") -> list[MatchSummaryViewModel]:
        raw_rows = self._rows()
        coverage = self._coverage_map(row["match_id"] for row in raw_rows)
        rows = [self._summary(row, coverage.get(row["match_id"], "UNAVAILABLE")) for row in raw_rows]
        return [row for row in rows if result_filter == "ALL" or row.result == result_filter]

    def match_detail(self, match_id: str) -> Optional[MatchDetailViewModel]:
        for raw in self._rows():
            if raw["match_id"] == match_id:
                summary = self._summary(raw, self._coverage_map([match_id]).get(match_id, "UNAVAILABLE"))
                return MatchDetailViewModel(match=summary, items=summary.items)
        return None

    def progress(self, window: int | None = None) -> ProgressViewModel:
        all_matches = self.matches()
        matches = all_matches[:window] if window else all_matches
        if not matches:
            return ProgressViewModel()
        total = len(matches)
        wins = sum(match.result == "WIN" for match in matches)
        duration = sum(match.duration_seconds for match in matches)
        deaths = sum(match.deaths for match in matches)
        kills = sum(match.kills for match in matches)
        assists = sum(match.assists for match in matches)
        cs = sum(match.cs for match in matches)
        minutes = duration / 60
        comparison_size = window
        recent = all_matches[:comparison_size] if comparison_size else []
        previous = all_matches[comparison_size:comparison_size * 2] if comparison_size else []
        comparison = "Comparaison désactivée pour l’ensemble de l’historique."
        if comparison_size:
            comparison = f"Il faut au moins {comparison_size * 2} parties locales pour comparer deux fenêtres de {comparison_size}."
        if comparison_size and len(recent) == len(previous) == comparison_size:
            recent_rate = sum(m.result == "WIN" for m in recent) / len(recent) * 100
            previous_rate = sum(m.result == "WIN" for m in previous) / len(previous) * 100
            comparison = f"Taux de victoire : {recent_rate:.0f}% sur les {len(recent)} dernières, contre {previous_rate:.0f}% sur les {len(previous)} précédentes."
        champion: dict[str, list[MatchSummaryViewModel]] = {}
        for match in matches:
            champion.setdefault(match.champion, []).append(match)
        champion_rows = tuple({
            "champion": name, "games": len(rows), "wins": sum(r.result == "WIN" for r in rows),
            "win_rate": sum(r.result == "WIN" for r in rows) / len(rows) * 100,
            "kda": (sum(r.kills + r.assists for r in rows) / max(1, sum(r.deaths for r in rows))),
            "cs_per_min": sum(r.cs for r in rows) / max(1, sum(r.duration_seconds for r in rows) / 60),
        } for name, rows in sorted(champion.items(), key=lambda pair: len(pair[1]), reverse=True))
        return ProgressViewModel(total, wins, total - wins, wins / total * 100,
            (kills + assists) / max(1, deaths), cs / minutes if minutes else None,
            deaths / total, minutes / total if total else None, comparison, champion_rows)

    def status(self) -> StatusViewModel:
        latest = "UNAVAILABLE"
        count = 0
        timeline_count = 0
        analyzed_match_count = 0
        player = self._primary_player()
        puuid = player["puuid"] if player else ""
        sync_state = self.cache.sync_state(puuid, SOLO_QUEUE_ID) if self.cache else None
        if self.is_available():
            rows = self._rows(1)
            with closing(self._connection()) as connection:
                count = connection.execute("SELECT COUNT(*) FROM matches m JOIN participants p ON p.match_id=m.match_id WHERE p.puuid=? AND m.queue_id=?", (puuid, SOLO_QUEUE_ID)).fetchone()[0] if player else 0
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                if "timelines" in tables:
                    timeline_count = connection.execute(
                        "SELECT COUNT(*) FROM timelines t JOIN matches m ON m.match_id=t.match_id JOIN participants p ON p.match_id=m.match_id WHERE p.puuid=? AND m.queue_id=?",
                        (puuid, SOLO_QUEUE_ID),
                    ).fetchone()[0] if player else 0
                if "app_analysis_reports" in tables:
                    scoped_ids = [row[0] for row in connection.execute(
                        "SELECT m.match_id FROM matches m JOIN participants p ON p.match_id=m.match_id WHERE p.puuid=? AND m.queue_id=?",
                        (puuid, SOLO_QUEUE_ID),
                    ).fetchall()] if player else []
                    analyzed_match_count = sum(
                        value in ("AVAILABLE", "PARTIAL")
                        for value in self._coverage_map(scoped_ids).values()
                    )
            latest = self._summary(rows[0]).played_at if rows else "No local matches"
        key_configured = bool(self.settings.api_key()) if self.settings else bool(os.getenv("RIOT_API_KEY"))
        return StatusViewModel(str(self.db_path), self.is_available(), count, latest, key_configured,
            sync_status=(sync_state or {}).get("status", "Hors ligne / aucune synchronisation cette session"),
            api_status=self.settings.api_status() if self.settings else ("CONFIGURED_UNVALIDATED" if key_configured else "NOT_CONFIGURED"),
            timeline_count=timeline_count, analyzed_match_count=analyzed_match_count,
            last_sync_at=(sync_state or {}).get("completed_at", "UNAVAILABLE"))
