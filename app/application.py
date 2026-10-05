from __future__ import annotations

import sys
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import re
import traceback
from pathlib import Path

from PySide6.QtCore import QDir, QLockFile
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from ui.theme import apply_zircon_theme
from app.paths import DATA_ROOT, DEFAULT_DB_PATH, PROJECT_ROOT
from app.version import VERSION


class ZirconCoachApplication:
    VERSION = VERSION

    def __init__(self) -> None:
        self._qt_app: QApplication | None = None
        self._window = None
        self._instance_lock: QLockFile | None = None

    def run(self) -> int:
        smoke = '--smoke-check' in sys.argv
        if smoke:
            os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Configure the existing database dependency before analyzers import it.
        from database import database as legacy_database
        legacy_database.DB_PATH = DEFAULT_DB_PATH
        from app.bootstrap import build_app_context
        from ui.main_window import MainWindow

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        self._qt_app = app
        app.setApplicationName("ZiRcoN Coach")
        app.setApplicationVersion(self.VERSION)
        app.setWindowIcon(QIcon(str(PROJECT_ROOT / 'resources' / 'zircon.svg')))
        apply_zircon_theme(app)

        log_dir = DATA_ROOT / 'logs'; log_dir.mkdir(parents=True, exist_ok=True)
        logger = logging.getLogger('zircon.runtime'); logger.setLevel(logging.ERROR)
        handler = RotatingFileHandler(log_dir / 'application.log', maxBytes=1_000_000, backupCount=2, encoding='utf-8')
        logger.addHandler(handler)
        callback_errors = []
        def exception_handler(kind, value, tb):
            detail = ''.join(traceback.format_exception(kind, value, tb))
            logger.error(re.sub(r'RGAPI-[A-Za-z0-9-]+', '<clé masquée>', detail))
            if smoke:
                callback_errors.append(detail)
                if sys.stderr is not None: sys.__excepthook__(kind, value, tb)
            else:
                QMessageBox.warning(self._window, 'ZiRcoN Coach', 'Une action n’a pas pu être terminée. Réessaie ; tes parties enregistrées restent disponibles.')
        sys.excepthook = exception_handler

        # Repeated clicks or launchers cannot create competing windows.
        self._instance_lock = QLockFile(QDir.temp().filePath("zircon-coach-ui.lock"))
        if not smoke and not self._instance_lock.tryLock(100):
            return 0

        context = build_app_context()
        self._window = MainWindow(context)
        if smoke:
            from PySide6.QtCore import QThreadPool
            from PySide6.QtGui import QFontMetrics
            assert QFontMetrics(app.font()).inFont('A'), 'UI font cannot display ordinary text'
            self._window.show()
            for page in range(5):
                self._window.navigate(page)
                app.processEvents()
            assert context.local_data.db_path.resolve() == legacy_database.DB_PATH.resolve()
            assert context.build_optimizer._catalog('16.18') is not None
            assert QThreadPool.globalInstance().waitForDone(10000)
            app.processEvents()
            available_matches = context.local_data.matches()
            requested = sys.argv[sys.argv.index('--smoke-match') + 1] if '--smoke-match' in sys.argv else None
            preferred = next((match for match in available_matches if match.match_id == requested), None)
            matches = ([preferred] if preferred else []) + [match for match in available_matches if match is not preferred][:3 - int(preferred is not None)]
            if not context.settings.api_key():
                self._window.start_sync()
                assert self._window.stack.currentWidget() is self._window.settings_page
                assert self._window.sync_worker is None
                assert self._window.settings_page.fields['Clé enregistrée'].text() == 'Non'
            if not matches:
                self._window.dashboard_page.review_latest.click()
                assert self._window.stack.currentWidget() is self._window.settings_page
            for match in matches:
                self._window.open_match(match.match_id)
                assert QThreadPool.globalInstance().waitForDone(45000)
                app.processEvents()
                tabs = self._window.match_detail_page.tabs
                assert [tabs.tabText(i) for i in range(tabs.count())] == ['Résumé', 'Coach', 'Objets', 'Déroulé', 'Notes']
                assert self._window.match_detail_page._optimizer_worker is None
                from PySide6.QtWidgets import QLabel
                advice = self._window.match_detail_page._optimizer_layout.itemAt(0).widget()
                labels = [label.text() for label in advice.findChildren(QLabel)]
                assert labels and 'Préparation du conseil' not in labels, 'Item advice is still loading'
            captures = DATA_ROOT / 'smoke-captures'; captures.mkdir(exist_ok=True)
            for page in range(4):
                self._window.navigate(page)
                for _ in range(4): app.processEvents()
                assert self._window.grab().save(str(captures / f'page-{page}.png'))
            if matches:
                self._window.open_match(matches[0].match_id)
                assert QThreadPool.globalInstance().waitForDone(45000)
                app.processEvents()
                for index in range(5):
                    self._window.match_detail_page.tabs.setCurrentIndex(index)
                    for _ in range(4): app.processEvents()
                    assert self._window.grab().save(str(captures / f'match-{index}.png'))
            output = DATA_ROOT / 'smoke-result.json'
            if '--smoke-output' in sys.argv:
                output = Path(sys.argv[sys.argv.index('--smoke-output') + 1])
            output.parent.mkdir(parents=True, exist_ok=True)
            assert not callback_errors, 'Unhandled UI callback error; see application.log'
            output.write_text(json.dumps({'passed': True, 'version': self.VERSION,
                'initialized_pages': self._window.initialized_page_count,
                'database_path': str(DEFAULT_DB_PATH), 'catalog_16_18': True,
                'matches_opened': len(matches)}), encoding='utf-8')
            self._window.close()
            return 0
        self._window.show()

        return app.exec()
