from __future__ import annotations

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QProgressBar, QPushButton,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from app.bootstrap import AppContext
from ui.pages.dashboard_page import DashboardPage
from ui.pages.match_detail_page import MatchDetailPage
from ui.pages.matches_page import MatchesPage
from ui.pages.progress_page import ProgressPage
from ui.pages.settings_page import SettingsPage
from ui.workers import FunctionWorker


class MainWindow(QMainWindow):
    PAGE_DASHBOARD, PAGE_MATCHES, PAGE_PROGRESS, PAGE_SETTINGS, PAGE_MATCH_DETAIL = range(5)
    PAGE_NAMES = ("Tableau de bord", "Historique", "Progression", "Réglages", "Analyse post-game")

    def __init__(self, context: AppContext, parent=None):
        super().__init__(parent)
        self.context = context
        self.sync_worker = None
        self._pages: dict[int, QWidget] = {}
        self.dashboard_page = None
        self.matches_page = None
        self.progress_page = None
        self.settings_page = None
        self.match_detail_page = None
        QThreadPool.globalInstance().setMaxThreadCount(6)

        self.setWindowTitle("ZiRcoN Coach — V0.1 Alpha")
        self.resize(1600, 900)
        self.setMinimumSize(1100, 700)
        central = QWidget()
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_sidebar())

        workspace = QWidget()
        work = QVBoxLayout(workspace)
        work.setContentsMargins(0, 0, 0, 0)
        work.setSpacing(0)
        work.addWidget(self._build_topbar())
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)
        work.addWidget(self.progress)
        self.stack = QStackedWidget()
        work.addWidget(self.stack, 1)
        outer.addWidget(workspace, 1)
        self.setCentralWidget(central)

        # Startup contract: only the dashboard exists until navigation asks for more.
        self._ensure_page(self.PAGE_DASHBOARD)
        self.navigate(self.PAGE_DASHBOARD)
        self.refresh_header()

    @property
    def initialized_page_count(self) -> int:
        return len(self._pages)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(20, 26, 20, 20)
        side.setSpacing(7)
        brand = QLabel("ZiRcoN Coach")
        brand.setObjectName("Brand")
        side.addWidget(brand)
        accent = QLabel("Post-game analytics")
        accent.setObjectName("BrandAccent")
        side.addWidget(accent)
        side.addSpacing(22)
        self.nav_buttons = []
        for label, index in (("Tableau de bord", 0), ("Historique", 1), ("Progression", 2), ("Réglages", 3)):
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setMinimumHeight(44)
            button.clicked.connect(lambda checked=False, page=index: self.navigate(page))
            side.addWidget(button)
            self.nav_buttons.append(button)
        side.addStretch()
        version = QLabel("V0.1 Alpha")
        version.setObjectName("Muted")
        side.addWidget(version)
        local = QLabel("●  Données locales")
        local.setStyleSheet("color: #43D39E; font-size: 11px;")
        side.addWidget(local)
        return sidebar

    def _build_topbar(self) -> QFrame:
        from ui.components.status_badge import StatusBadge

        topbar = QFrame()
        topbar.setObjectName("Topbar")
        topbar.setFixedHeight(66)
        top = QHBoxLayout(topbar)
        top.setContentsMargins(30, 12, 30, 12)
        top.setSpacing(12)
        self.page_title = QLabel("Tableau de bord")
        self.page_title.setObjectName("SectionTitle")
        top.addWidget(self.page_title)
        top.addStretch()
        self.player = QLabel()
        self.player.setObjectName("Muted")
        self.player.setMaximumWidth(180)
        self.player.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        top.addWidget(self.player)
        self.connection = QLabel("●  Local")
        self.connection.setStyleSheet("color: #43D39E; font-size: 12px;")
        top.addWidget(self.connection)

        # Compatibility state stays available to tests, but technical failures live in Settings.
        self.api = StatusBadge("UNKNOWN")
        self.sync_badge = StatusBadge("OFFLINE")
        self.sync_text = QLabel("Données locales")
        self.sync_text.setMaximumWidth(140)
        for widget in (self.api, self.sync_badge, self.sync_text):
            widget.hide()
            top.addWidget(widget)
        self.sync_button = QPushButton("Synchroniser")
        self.sync_button.setObjectName("PrimaryButton")
        self.sync_button.clicked.connect(self.start_sync)
        top.addWidget(self.sync_button)
        return topbar

    def _ensure_page(self, index: int) -> QWidget:
        if index in self._pages:
            return self._pages[index]
        if index == self.PAGE_DASHBOARD:
            page = DashboardPage(self.context.local_data, self.context.assets)
            page.open_match.connect(self.open_match)
            self.dashboard_page = page
        elif index == self.PAGE_MATCHES:
            page = MatchesPage(self.context.local_data, self.context.assets)
            page.open_match.connect(self.open_match)
            self.matches_page = page
        elif index == self.PAGE_PROGRESS:
            page = ProgressPage(self.context.local_data, self.context.assets)
            self.progress_page = page
        elif index == self.PAGE_SETTINGS:
            page = SettingsPage(self.context.local_data, self.context.settings, self.context.sync)
            page.settings_changed.connect(self.refresh_all)
            self.settings_page = page
        elif index == self.PAGE_MATCH_DETAIL:
            page = MatchDetailPage(
                self.context.local_data, self.context.analysis,
                self.context.build_optimizer, self.context.assets,
            )
            page.back_requested.connect(lambda: self.navigate(self.PAGE_MATCHES))
            self.match_detail_page = page
        else:
            raise ValueError(f"Unknown page: {index}")
        self._pages[index] = page
        self.stack.addWidget(page)
        return page

    def refresh_header(self) -> None:
        try:
            player, status = self.context.local_data.player(), self.context.local_data.status()
            self.player.setText(player.riot_id)
            self.api.set_status(status.api_status)
            self.sync_badge.set_status(status.sync_status)
            self.statusBar().showMessage(
                f"{status.match_count} partie(s) SoloQ · dernière partie {status.latest_match_date}"
            )
        except Exception:
            self.player.setText("Joueur local indisponible")
            self.api.set_status("UNKNOWN")
            self.sync_badge.set_status("OFFLINE")

    def navigate(self, index: int) -> None:
        page = self._ensure_page(index)
        self.stack.setCurrentWidget(page)
        self.page_title.setText(self.PAGE_NAMES[index])
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)

    def open_match(self, match_id: str) -> None:
        page = self._ensure_page(self.PAGE_MATCH_DETAIL)
        page.load_match(match_id)
        self.stack.setCurrentWidget(page)
        self.page_title.setText(self.PAGE_NAMES[self.PAGE_MATCH_DETAIL])
        for button in self.nav_buttons:
            button.setChecked(False)

    def start_sync(self) -> None:
        if self.sync_worker:
            return
        self.sync_button.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(1)
        self.sync_text.setText("Synchronisation…")
        self.sync_badge.set_status("RUNNING")
        worker = FunctionWorker(self.context.sync.sync, with_progress=True)
        worker.signals.progress.connect(self._sync_progress)
        worker.signals.result.connect(self._sync_result)
        worker.signals.error.connect(self._sync_failed)
        worker.signals.finished.connect(self._sync_finished)
        self.sync_worker = worker
        QThreadPool.globalInstance().start(worker)

    def _sync_progress(self, message, value):
        self.sync_text.setText(message)
        self.progress.setValue(value)

    def _sync_result(self, result):
        status = result.get("status", "ERROR")
        self.refresh_all()
        self.sync_text.setText(result.get("message", status))
        self.sync_badge.set_status(status)
        self.api.set_status(self.context.settings.api_status())

    def _sync_failed(self, message):
        self.sync_text.setText(message)
        self.sync_badge.set_status("ERROR")
        self.api.set_status(self.context.settings.api_status())

    def _sync_finished(self):
        self.sync_worker = None
        self.sync_button.setEnabled(True)
        self.progress.setVisible(False)

    def refresh_all(self) -> None:
        # Navigation only shows pages. Explicit data changes refresh initialized pages.
        for page in tuple(self._pages.values()):
            refresh = getattr(page, "refresh", None)
            if callable(refresh):
                refresh()
        self.refresh_header()
