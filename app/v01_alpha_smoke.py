from __future__ import annotations

import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLineEdit, QTabWidget

from app.bootstrap import build_app_context
from ui.main_window import MainWindow


def _sample_database(path: Path) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE matches(match_id TEXT PRIMARY KEY, game_creation INTEGER, game_duration INTEGER, game_version TEXT, queue_id INTEGER, raw_json TEXT)")
        connection.execute("""CREATE TABLE participants(id INTEGER PRIMARY KEY, match_id TEXT, puuid TEXT, riot_name TEXT, riot_tag TEXT,
            team_id INTEGER, position TEXT, champion_id INTEGER, champion_name TEXT, kills INTEGER, deaths INTEGER, assists INTEGER,
            cs INTEGER, gold INTEGER, damage_to_champions INTEGER, vision_score INTEGER, win INTEGER,
            item0 INTEGER, item1 INTEGER, item2 INTEGER, item3 INTEGER, item4 INTEGER, item5 INTEGER, item6 INTEGER)""")
        connection.execute("INSERT INTO matches VALUES ('SAMPLE',1700000000000,1800,'16.16.1',420,'{}')")
        connection.execute("INSERT INTO participants VALUES (1,'SAMPLE','p','Sample','EUW',100,'JUNGLE',1,'Annie',4,2,8,180,1,1,1,1,1001,2003,0,0,0,0,0)")
        connection.commit()


def main() -> None:
    app = QApplication.instance() or QApplication([])

    with tempfile.TemporaryDirectory() as temp_dir:
        empty_db_path = Path(temp_dir) / "missing.db"
        context = build_app_context(empty_db_path)
        window = MainWindow(context)

        assert window.stack.count() == 5
        assert window.stack.currentIndex() == MainWindow.PAGE_DASHBOARD

        window.navigate(MainWindow.PAGE_MATCHES)
        assert window.stack.currentIndex() == MainWindow.PAGE_MATCHES

        window.navigate(MainWindow.PAGE_PROGRESS)
        assert window.stack.currentIndex() == MainWindow.PAGE_PROGRESS

        window.navigate(MainWindow.PAGE_SETTINGS)
        assert window.stack.currentIndex() == MainWindow.PAGE_SETTINGS
        assert window.settings_page.key.echoMode() == QLineEdit.EchoMode.Password

        window.close()

        sample_path = Path(temp_dir) / "sample.db"
        _sample_database(sample_path)
        sample_window = MainWindow(build_app_context(sample_path))
        sample_window.open_match("SAMPLE")
        assert sample_window.stack.currentIndex() == MainWindow.PAGE_MATCH_DETAIL
        assert sample_window.match_detail_page.content.count() >= 5
        tabs = sample_window.match_detail_page.findChildren(QTabWidget)
        assert tabs and tabs[0].count() == 6
        sample_window.resize(1100, 700)
        sample_window._sync_progress("Downloading match 1/2", 35)
        assert sample_window.progress.value() == 35
        sentinel = object()
        sample_window.sync_worker = sentinel
        sample_window.start_sync()
        assert sample_window.sync_worker is sentinel
        sample_window._sync_result({"status": "UNAUTHORIZED_OR_EXPIRED", "message": "Replace key in Settings."})
        assert sample_window.api.text() == "UNAUTHORIZED OR EXPIRED"
        sample_window.close()

    app.processEvents()
    print("ZiRcoN Coach V0.1 Batch 1 smoke: PASS")


if __name__ == "__main__":
    main()
