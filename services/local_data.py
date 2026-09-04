import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from app.paths import DEFAULT_DB_PATH
from viewmodels import (
    MatchDetailViewModel, MatchSummaryViewModel, PlayerViewModel,
    ProgressViewModel, StatusViewModel,
)


class LocalDataService:
    """Read-only projection of the existing local SQLite history."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def is_available(self) -> bool:
        return self.db_path.exists()

    def _primary_player(self) -> Optional[sqlite3.Row]:
        if not self.is_available():
            return None
        with self._connection() as connection:
            return connection.execute(
                """SELECT puuid, riot_name, riot_tag, COUNT(*) AS games
                   FROM participants GROUP BY puuid
                   ORDER BY games DESC, puuid LIMIT 1"""
            ).fetchone()

    def player(self) -> PlayerViewModel:
        row = self._primary_player()
        if row is None:
            return PlayerViewModel()
        name = row["riot_name"] or "Local player"
        tag = row["riot_tag"]
        return PlayerViewModel(puuid=row["puuid"], riot_id=f"{name}#{tag}" if tag else name)

    def _rows(self, limit: Optional[int] = None) -> list[sqlite3.Row]:
        player = self._primary_player()
        if player is None:
            return []
        query = """SELECT m.match_id, m.game_creation, m.game_duration, m.queue_id,
                          p.champion_name, p.kills, p.deaths, p.assists, p.cs, p.win,
                          p.position, p.item0, p.item1, p.item2, p.item3, p.item4, p.item5, p.item6
                   FROM matches m JOIN participants p ON p.match_id=m.match_id
                   WHERE p.puuid=? ORDER BY m.game_creation DESC, m.match_id DESC"""
        params: list[object] = [player["puuid"]]
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        with self._connection() as connection:
            return list(connection.execute(query, params).fetchall())

    @staticmethod
    def _summary(row: sqlite3.Row) -> MatchSummaryViewModel:
        timestamp = row["game_creation"] or 0
        played_at = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M") if timestamp else "UNKNOWN"
        return MatchSummaryViewModel(
            match_id=row["match_id"], champion=row["champion_name"] or "Unknown champion",
            result="WIN" if row["win"] else "LOSS", kills=row["kills"] or 0,
            deaths=row["deaths"] or 0, assists=row["assists"] or 0, cs=row["cs"] or 0,
            duration_seconds=row["game_duration"] or 0, played_at=played_at,
            queue="Ranked Solo/Duo" if row["queue_id"] == 420 else str(row["queue_id"] or "UNKNOWN"),
            position=row["position"] or "UNKNOWN",
        )

    def matches(self, result_filter: str = "ALL") -> list[MatchSummaryViewModel]:
        rows = [self._summary(row) for row in self._rows()]
        return [row for row in rows if result_filter == "ALL" or row.result == result_filter]

    def match_detail(self, match_id: str) -> Optional[MatchDetailViewModel]:
        for raw in self._rows():
            if raw["match_id"] == match_id:
                items = tuple(int(raw[f"item{index}"] or 0) for index in range(7) if raw[f"item{index}"])
                return MatchDetailViewModel(match=self._summary(raw), items=items)
        return None

    def progress(self) -> ProgressViewModel:
        matches = self.matches()
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
        recent = matches[:min(10, total)]
        previous = matches[min(10, total):min(20, total)]
        comparison = "Need at least 20 local matches to compare two equal windows."
        if len(recent) == len(previous) and recent:
            recent_rate = sum(m.result == "WIN" for m in recent) / len(recent) * 100
            previous_rate = sum(m.result == "WIN" for m in previous) / len(previous) * 100
            comparison = f"Last {len(recent)} win rate: {recent_rate:.0f}% vs previous {len(previous)}: {previous_rate:.0f}%."
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
        if self.is_available():
            rows = self._rows(1)
            count = len(self._rows())
            latest = rows[0].played_at if rows else "No local matches"
        return StatusViewModel(str(self.db_path), self.is_available(), count, latest,
            bool(os.getenv("RIOT_API_KEY")))
