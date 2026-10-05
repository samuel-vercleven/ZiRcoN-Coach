"""Opt-in QML desktop exploration; classic presentation stays available."""
import json
import os
from pathlib import Path
import sys
import re
import traceback

from PySide6.QtCore import QDir, QLockFile, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication, QFrame, QPushButton, QMessageBox

from app.paths import DEFAULT_DB_PATH, DATA_ROOT, PROJECT_ROOT
from app.version import VERSION


class QuickApplication:
    def run(self):
        smoke = '--smoke-check' in sys.argv
        if smoke:
            os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
            os.environ.setdefault('QT_QUICK_BACKEND', 'software')
        DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        from database import database as legacy
        legacy.DB_PATH = DEFAULT_DB_PATH
        from app.bootstrap import build_app_context
        from ui.quick.bridge import QuickBridge, CachedImages
        from ui.theme import apply_zircon_theme
        app = QApplication.instance() or QApplication(sys.argv)
        app.setApplicationName('ZiRcoN Coach')
        app.setApplicationVersion(VERSION)
        app.setWindowIcon(QIcon(str(PROJECT_ROOT / 'resources' / 'zircon.svg')))
        self.callback_errors = []
        def exception_handler(kind, value, tb):
            detail = re.sub(r'RGAPI-[A-Za-z0-9-]+', '<clé masquée>', ''.join(traceback.format_exception(kind, value, tb)))
            self.callback_errors.append(detail)
            log = DATA_ROOT / 'logs' / 'qml-callback-errors.log'
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open('a', encoding='utf-8') as stream:
                stream.write(detail)
            if not smoke:
                QMessageBox.warning(None, 'ZiRcoN Coach', 'Cette action n’a pas pu être terminée. Tes parties restent enregistrées.')
        sys.excepthook = exception_handler
        # Also prepares OS fonts and the unchanged fallback window.
        apply_zircon_theme(app)
        QQuickStyle.setStyle('Basic')
        self.lock = QLockFile(QDir.temp().filePath('zircon-coach-ui.lock'))
        if not smoke and not self.lock.tryLock(100):
            return 0
        self.context = build_app_context()
        self.bridge = QuickBridge(self.context, offline=smoke)
        self.engine = QQmlApplicationEngine()
        self.warnings = []
        self.engine.warnings.connect(self._qml_warnings)
        self.engine.rootContext().setContextProperty('coach', self.bridge)
        self.theme = 'turquoise'
        if '--theme' in sys.argv:
            self.theme = sys.argv[sys.argv.index('--theme') + 1]
        if self.theme not in ('turquoise', 'belveth'):
            raise ValueError('Unknown QML theme')
        self.engine.rootContext().setContextProperty('initialTheme', self.theme)
        self.engine.rootContext().setContextProperty('resourceRoot', QUrl.fromLocalFile(str(PROJECT_ROOT / 'resources')).toString())
        self.engine.addImageProvider('cached', CachedImages(self.context.assets))
        self.engine.load(QUrl.fromLocalFile(str(PROJECT_ROOT / 'ui' / 'quick' / 'qml' / 'Main.qml')))
        if not self.engine.rootObjects():
            raise RuntimeError('The QML window could not be loaded')
        self.window = self.engine.rootObjects()[0]
        self.classic = None
        self.bridge.classicRequested.connect(self._open_classic)
        try:
            if smoke:
                return self._smoke(app)
            if '--preview-capture' in sys.argv:
                from PySide6.QtCore import QTimer
                path = Path(sys.argv[sys.argv.index('--preview-capture') + 1])
                path.parent.mkdir(parents=True, exist_ok=True)
                QTimer.singleShot(1500, lambda: self.window.grabWindow().save(str(path)))
            return app.exec()
        finally:
            self.bridge.shutdown()
            app.processEvents()
            # Delete QML bindings before context objects: avoid shutdown warnings.
            self.window.close()
            from shiboken6 import delete
            delete(self.engine)
            if smoke:
                assert not self.warnings, '\n'.join(self.warnings)
                assert not self.callback_errors, '\n'.join(self.callback_errors)

    def _qml_warnings(self, errors):
        messages = [error.toString() for error in errors]
        self.warnings.extend(messages)
        log = DATA_ROOT / 'logs' / 'qml-runtime.log'
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('a', encoding='utf-8') as stream:
            stream.write('\n'.join(messages) + '\n')

    def _open_classic(self, settings):
        if self.classic is None:
            from ui.main_window import MainWindow
            self.classic = MainWindow(self.context)
            back = QPushButton('Revenir à la nouvelle interface')
            back.clicked.connect(self._return_quick)
            self.classic.findChild(QFrame, 'Topbar').layout().insertWidget(1, back)
        if settings:
            self.classic.navigate(3)
        self.classic.show()
        self.classic.raise_()
        self.window.hide()
        # One process and one lock, never spawn competing UI instances.

    def _return_quick(self):
        self.bridge.refresh()
        self.window.setProperty('page', 'home')
        self.window.show()
        self.window.raise_()
        self.classic.hide()

    def _smoke(self, app):
        from PySide6.QtTest import QTest
        from PySide6.QtCore import QObject, QPoint, Qt
        directory = DATA_ROOT / '.cache' / 'zircon' / 'quick-visual-check'
        if self.theme == 'belveth':
            directory = directory / 'belveth'
        directory.mkdir(parents=True, exist_ok=True)
        captures = []
        def settle():
            QTest.qWait(350)
            app.processEvents()
        def capture(name):
            settle()
            path = directory / (name + '.png')
            assert self.window.grabWindow().save(str(path)), 'QML capture failed'
            captures.append(str(path))
        def click(name):
            def find(item):
                if item.objectName() == name:
                    return item
                for child in item.childItems():
                    found = find(child)
                    if found is not None:
                        return found
                return None
            button = find(self.window.contentItem())
            assert button is not None, name
            position = button.mapToScene(button.boundingRect().center()).toPoint()
            QTest.mouseClick(self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, position)
            settle()
        for width, height in ((1600, 960), (1120, 720)):
            self.window.resize(width, height)
            self.window.setProperty('page', 'home')
            capture(f'{width}-home')
            click('historyButton')
            assert self.window.property('page') == 'history'
            capture(f'{width}-history')
            click('progressButton')
            assert self.window.property('page') == 'progress'
            capture(f'{width}-progress')
        matches = self.bridge.state['matches']
        selected = []
        if '--smoke-match' in sys.argv:
            selected.append(sys.argv[sys.argv.index('--smoke-match') + 1])
        elif matches:
            replay = PROJECT_ROOT / 'logs' / 'build_optimizer' / 'contextual_replay.json'
            if replay.is_file():
                ids = {row['match_id'] for row in json.loads(replay.read_text(encoding='utf-8')).get('rows', [])}
                preferred = next((row for row in matches if row['id'] in ids and row['champion'] == 'Viego'), None)
                if preferred:
                    selected.append(preferred['id'])
        selected += [row['id'] for row in matches[:2] if row['id'] not in selected]
        for match_id in selected:
            assert self.bridge.openMatch(match_id)
            self.bridge.wait_for_workers()
            settle()
            assert not self.bridge.busy, 'Background result was not delivered'
            for team in ('allies', 'enemies'):
                assert all(all(item > 0 for item in row['items']) for row in self.bridge.detail[team])
            for width, height in ((1600, 960), (1120, 720)):
                self.window.resize(width, height)
                self.window.setProperty('page', 'match')
                for index, name in enumerate(('summary', 'coach', 'build', 'timeline')):
                    self.window.setProperty('matchTab', index)
                    capture(f'{width}-{match_id}-{name}')
            # Reselecting the same game reuses the existing optimizer result.
            assert self.bridge.openMatch(match_id) and not self.bridge.busy
        assert len(self.engine.rootObjects()) == 1, 'Navigation recreated the window'
        initial_mode = self.window.property('belvethMode')
        if selected:
            # Prefer the cached reviewed Viego game so live comparison includes
            # the actual recommendation gauge, not only an abstention card.
            assert self.bridge.openMatch(selected[0]) and not self.bridge.busy
            self.window.setProperty('matchTab', 0)
        settle()
        before_color = self.window.grabWindow().pixelColor(210, 12)
        state_before = self.bridge.detail.copy(), self.bridge.build.copy()
        click('turquoiseThemeButton' if initial_mode else 'belvethThemeButton')
        assert self.window.property('belvethMode') != initial_mode
        assert self.window.grabWindow().pixelColor(210, 12) != before_color, 'Theme failed to repaint'
        assert state_before == (self.bridge.detail, self.bridge.build), 'Theme mutated match analysis'
        capture('theme-comparison')
        if selected:
            self.window.setProperty('matchTab', 2)
            capture('theme-comparison-build')
        click('belvethThemeButton' if initial_mode else 'turquoiseThemeButton')
        assert self.window.property('belvethMode') == initial_mode
        self._open_classic(True)
        assert self.classic.settings_page is not None
        assert not self.window.isVisible() and self.classic.isVisible()
        self._return_quick()
        assert self.window.isVisible() and not self.classic.isVisible()
        self.classic.close()
        assert not self.warnings, '\n'.join(self.warnings)
        assert not self.callback_errors, '\n'.join(self.callback_errors)
        result = {'passed': True, 'presentation': 'Qt Quick / QML exploration', 'theme': self.theme, 'matches': len(selected),
                  'captures': captures, 'qml_warnings': self.warnings,
                  'database_path': str(self.context.local_data.db_path)}
        if '--smoke-output' in sys.argv:
            path = Path(sys.argv[sys.argv.index('--smoke-output') + 1])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps({**result, 'captures': len(captures)}, ensure_ascii=True))
        return 0
