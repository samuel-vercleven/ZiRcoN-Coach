from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.bootstrap import AppContext
from ui.pages.dashboard_page import DashboardPage
from ui.pages.match_detail_page import MatchDetailPage
from ui.pages.matches_page import MatchesPage
from ui.pages.progress_page import ProgressPage
from ui.pages.settings_page import SettingsPage


class MainWindow(QMainWindow):
    PAGE_DASHBOARD = 0
    PAGE_MATCHES = 1
    PAGE_PROGRESS = 2
    PAGE_SETTINGS = 3
    PAGE_MATCH_DETAIL = 4

    def __init__(self, context: AppContext, parent=None) -> None:
        super().__init__(parent)
        self.context = context

        self.setWindowTitle("ZiRcoN Coach — V0.1 Alpha")
        self.resize(1260, 780)
        self.setMinimumSize(980, 640)

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(190)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 22, 16, 16)
        side_layout.setSpacing(8)

        brand = QLabel("ZiRcoN Coach")
        brand.setObjectName("Brand")
        side_layout.addWidget(brand)

        self.nav_buttons: list[QPushButton] = []
        for text, index in (
            ("Dashboard", self.PAGE_DASHBOARD),
            ("Matches", self.PAGE_MATCHES),
            ("Progress", self.PAGE_PROGRESS),
            ("Settings", self.PAGE_SETTINGS),
        ):
            button = QPushButton(text)
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, i=index: self.navigate(i))
            self.nav_buttons.append(button)
            side_layout.addWidget(button)

        side_layout.addStretch(1)

        alpha = QLabel("V0.1 Alpha")
        alpha.setObjectName("Muted")
        side_layout.addWidget(alpha)

        root.addWidget(sidebar)

        self.stack = QStackedWidget()

        self.dashboard_page = DashboardPage(context.local_data)
        self.matches_page = MatchesPage(context.local_data)
        self.progress_page = ProgressPage(context.local_data)
        self.settings_page = SettingsPage(context.local_data)
        self.match_detail_page = MatchDetailPage(context.local_data)

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.matches_page)
        self.stack.addWidget(self.progress_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.match_detail_page)

        self.dashboard_page.open_match.connect(self.open_match)
        self.matches_page.open_match.connect(self.open_match)
        self.match_detail_page.back_requested.connect(
            lambda: self.navigate(self.PAGE_MATCHES)
        )

        root.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.statusBar().showMessage(self._initial_status())
        self.navigate(self.PAGE_DASHBOARD)

    def _initial_status(self) -> str:
        try:
            status = self.context.local_data.status()
        except Exception:
            return "Local data unavailable"

        if status.db_available:
            return f"Local data loaded • {status.match_count} match(es)"
        return "No local database found • Settings remains available"

    def navigate(self, index: int) -> None:
        if index == self.PAGE_DASHBOARD:
            self.dashboard_page.refresh()
        elif index == self.PAGE_MATCHES:
            self.matches_page.refresh()
        elif index == self.PAGE_PROGRESS:
            self.progress_page.refresh()
        elif index == self.PAGE_SETTINGS:
            self.settings_page.refresh()

        self.stack.setCurrentIndex(index)

        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)

    def open_match(self, match_id: str) -> None:
        self.match_detail_page.load_match(match_id)
        self.stack.setCurrentIndex(self.PAGE_MATCH_DETAIL)
        for button in self.nav_buttons:
            button.setChecked(False)
