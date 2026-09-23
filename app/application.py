from __future__ import annotations

import sys

from PySide6.QtCore import QDir, QLockFile
from PySide6.QtWidgets import QApplication

from app.bootstrap import build_app_context
from ui.main_window import MainWindow
from ui.theme import apply_zircon_theme


class ZirconCoachApplication:
    VERSION = "0.1.0-alpha"

    def __init__(self) -> None:
        self._qt_app: QApplication | None = None
        self._window: MainWindow | None = None
        self._instance_lock: QLockFile | None = None

    def run(self) -> int:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        self._qt_app = app
        app.setApplicationName("ZiRcoN Coach")
        app.setApplicationVersion(self.VERSION)
        apply_zircon_theme(app)

        # Repeated clicks or launchers cannot create competing windows.
        self._instance_lock = QLockFile(QDir.temp().filePath("zircon-coach-ui.lock"))
        if not self._instance_lock.tryLock(100):
            return 0

        context = build_app_context()
        self._window = MainWindow(context)
        self._window.show()

        return app.exec()
