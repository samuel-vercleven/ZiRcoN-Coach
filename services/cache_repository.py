from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from app.paths import DEFAULT_DB_PATH


class CacheRepository:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        if not self.db_path.exists():
            return
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS app_profile_cache (
                puuid TEXT PRIMARY KEY, fetched_at TEXT NOT NULL, profile_json TEXT NOT NULL)""")
            connection.execute("""CREATE TABLE IF NOT EXISTS app_analysis_reports (
                match_id TEXT NOT NULL, analyzer_name TEXT NOT NULL, analyzer_version TEXT NOT NULL,
                generated_at TEXT NOT NULL, status TEXT NOT NULL, report_json TEXT NOT NULL,
                PRIMARY KEY(match_id, analyzer_name, analyzer_version))""")
            connection.execute("""CREATE TABLE IF NOT EXISTS app_sync_state (
                singleton INTEGER PRIMARY KEY CHECK(singleton = 1), completed_at TEXT NOT NULL,
                status TEXT NOT NULL, message TEXT NOT NULL)""")
            connection.execute("""CREATE TABLE IF NOT EXISTS app_account_sync_state (
                puuid TEXT NOT NULL, queue_id INTEGER NOT NULL, completed_at TEXT NOT NULL,
                status TEXT NOT NULL, message TEXT NOT NULL, payload_json TEXT NOT NULL,
                PRIMARY KEY(puuid, queue_id))""")
            connection.commit()

    def save_profile(self, puuid: str, profile: dict) -> None:
        self.initialize()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("INSERT OR REPLACE INTO app_profile_cache VALUES (?, ?, ?)",
                (puuid, datetime.now(timezone.utc).isoformat(), json.dumps(profile, ensure_ascii=False)))
            connection.commit()

    def profile(self, puuid: str) -> dict | None:
        self.initialize()
        if not self.db_path.exists():
            return None
        with closing(sqlite3.connect(self.db_path)) as connection:
            row = connection.execute("SELECT fetched_at, profile_json FROM app_profile_cache WHERE puuid=?", (puuid,)).fetchone()
        if not row:
            return None
        try:
            return {**json.loads(row[1]), "cached_at": row[0]}
        except (ValueError, TypeError):
            return None

    def save_report(self, match_id: str, analyzer: str, version: str, status: str, payload: dict) -> None:
        self.initialize()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("INSERT OR REPLACE INTO app_analysis_reports VALUES (?, ?, ?, ?, ?, ?)",
                (match_id, analyzer, version, datetime.now(timezone.utc).isoformat(), status,
                 json.dumps(payload, ensure_ascii=False)))
            connection.commit()

    def reports(self, match_id: str) -> list[dict]:
        self.initialize()
        if not self.db_path.exists():
            return []
        with closing(sqlite3.connect(self.db_path)) as connection:
            rows = connection.execute("SELECT analyzer_name, analyzer_version, generated_at, status, report_json FROM app_analysis_reports WHERE match_id=?", (match_id,)).fetchall()
        result = []
        for name, version, generated, status, raw in rows:
            try:
                result.append({"analyzer": name, "version": version, "generated_at": generated,
                               "status": status, "payload": json.loads(raw)})
            except (ValueError, TypeError):
                continue
        return result

    def save_sync_result(self, status: str, message: str, puuid: str = "",
                         queue_id: int = 420, payload: dict | None = None) -> None:
        """Persist the latest non-fatal sync result without storing credentials."""
        self.initialize()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                "INSERT OR REPLACE INTO app_sync_state VALUES (1, ?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), status, message),
            )
            if puuid:
                connection.execute(
                    "INSERT OR REPLACE INTO app_account_sync_state VALUES (?, ?, ?, ?, ?, ?)",
                    (puuid, queue_id, datetime.now(timezone.utc).isoformat(), status,
                     message, json.dumps(payload or {}, ensure_ascii=False)),
                )
            connection.commit()

    def sync_state(self, puuid: str = "", queue_id: int = 420) -> dict | None:
        self.initialize()
        if not self.db_path.exists():
            return None
        with closing(sqlite3.connect(self.db_path)) as connection:
            if puuid:
                scoped = connection.execute(
                    "SELECT completed_at, status, message, payload_json FROM app_account_sync_state WHERE puuid=? AND queue_id=?",
                    (puuid, queue_id),
                ).fetchone()
                if scoped:
                    try:
                        payload = json.loads(scoped[3])
                    except (ValueError, TypeError):
                        payload = {}
                    return {"completed_at": scoped[0], "status": scoped[1],
                            "message": scoped[2], "payload": payload,
                            "scope": "ACCOUNT_QUEUE"}
            row = connection.execute(
                "SELECT completed_at, status, message FROM app_sync_state WHERE singleton=1"
            ).fetchone()
        if not row:
            return None
        return {"completed_at": row[0], "status": row[1], "message": row[2],
                "payload": {}, "scope": "LEGACY_GLOBAL"}
