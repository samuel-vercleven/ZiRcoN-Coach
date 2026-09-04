from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.bootstrap import AppContext
from services.local_data import LocalDataService
from ui.main_window import MainWindow


def main() -> None:
    app = QApplication.instance() or QApplication([])

    with tempfile.TemporaryDirectory() as temp_dir:
        empty_db_path = Path(temp_dir) / "missing.db"
        context = AppContext(local_data=LocalDataService(empty_db_path))
        window = MainWindow(context)

        assert window.stack.count() == 5
        assert window.stack.currentIndex() == MainWindow.PAGE_DASHBOARD

        window.navigate(MainWindow.PAGE_MATCHES)
        assert window.stack.currentIndex() == MainWindow.PAGE_MATCHES

        window.navigate(MainWindow.PAGE_PROGRESS)
        assert window.stack.currentIndex() == MainWindow.PAGE_PROGRESS

        window.navigate(MainWindow.PAGE_SETTINGS)
        assert window.stack.currentIndex() == MainWindow.PAGE_SETTINGS

        window.close()

    app.processEvents()
    print("ZiRcoN Coach V0.1 Batch 1 smoke: PASS")


if __name__ == "__main__":
    main()
