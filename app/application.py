from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.bootstrap import build_app_context
from ui.main_window import MainWindow
from ui.theme import APP_STYLESHEET


class ZirconCoachApplication:
    VERSION = "0.1.0-alpha"

    def __init__(self) -> None:
        self._qt_app: QApplication | None = None
        self._window: MainWindow | None = None

    def run(self) -> int:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        self._qt_app = app
        app.setApplicationName("ZiRcoN Coach")
        app.setApplicationVersion(self.VERSION)
        app.setStyleSheet(APP_STYLESHEET)

        context = build_app_context()
        self._window = MainWindow(context)
        self._window.show()

        return app.exec()
