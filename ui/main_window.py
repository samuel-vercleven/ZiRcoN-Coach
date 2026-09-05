from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QProgressBar, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.bootstrap import AppContext
from ui.components.status_badge import StatusBadge
from ui.pages.dashboard_page import DashboardPage
from ui.pages.match_detail_page import MatchDetailPage
from ui.pages.matches_page import MatchesPage
from ui.pages.progress_page import ProgressPage
from ui.pages.settings_page import SettingsPage
from ui.workers import FunctionWorker


class MainWindow(QMainWindow):
    PAGE_DASHBOARD, PAGE_MATCHES, PAGE_PROGRESS, PAGE_SETTINGS, PAGE_MATCH_DETAIL = range(5)

    def __init__(self, context: AppContext, parent=None):
        super().__init__(parent); self.context = context; self.sync_worker = None
        self.setWindowTitle("ZiRcoN Coach — V0.1 Alpha"); self.resize(1400, 850); self.setMinimumSize(1100, 700)
        central = QWidget(); outer = QHBoxLayout(central); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        sidebar = QFrame(); sidebar.setObjectName("Sidebar"); sidebar.setFixedWidth(210); side = QVBoxLayout(sidebar); side.setContentsMargins(20, 25, 20, 18); side.setSpacing(8)
        brand = QLabel("ZiRcoN Coach"); brand.setObjectName("Brand"); side.addWidget(brand)
        accent = QLabel("POST-GAME FIABLE"); accent.setObjectName("BrandAccent"); side.addWidget(accent); side.addSpacing(24)
        self.nav_buttons = []
        for label, index in (("◈  Tableau de bord", 0), ("▤  Parties", 1), ("⌁  Progression", 2), ("⚙  Réglages", 3)):
            button = QPushButton(label); button.setCheckable(True); button.clicked.connect(lambda checked=False, i=index: self.navigate(i)); side.addWidget(button); self.nav_buttons.append(button)
        side.addStretch(); frozen = QLabel("V0.1 ALPHA\nBackend gelé jusqu’à Phase 2I"); frozen.setObjectName("Muted"); side.addWidget(frozen); outer.addWidget(sidebar)

        workspace = QWidget(); work = QVBoxLayout(workspace); work.setContentsMargins(0, 0, 0, 0); work.setSpacing(0)
        topbar = QFrame(); topbar.setObjectName("Topbar"); top = QHBoxLayout(topbar); top.setContentsMargins(25, 12, 24, 12)
        self.page_title = QLabel("Tableau de bord"); self.page_title.setObjectName("SectionTitle"); top.addWidget(self.page_title); top.addStretch()
        self.player = QLabel(); self.player.setObjectName("Muted"); top.addWidget(self.player)
        key_label = QLabel("CLÉ"); key_label.setObjectName("MicroLabel"); top.addWidget(key_label); self.api = StatusBadge("UNKNOWN"); top.addWidget(self.api)
        sync_label = QLabel("SYNC"); sync_label.setObjectName("MicroLabel"); top.addWidget(sync_label); self.sync_badge = StatusBadge("OFFLINE"); top.addWidget(self.sync_badge)
        self.sync_text = QLabel("Données locales"); self.sync_text.setObjectName("Muted"); top.addWidget(self.sync_text)
        self.sync_button = QPushButton("Synchroniser"); self.sync_button.setObjectName("PrimaryButton"); self.sync_button.clicked.connect(self.start_sync); top.addWidget(self.sync_button); work.addWidget(topbar)
        self.progress = QProgressBar(); self.progress.setRange(0, 100); self.progress.setValue(0); self.progress.setVisible(False); work.addWidget(self.progress)
        self.stack = QStackedWidget(); self.dashboard_page = DashboardPage(context.local_data, context.assets); self.matches_page = MatchesPage(context.local_data, context.assets); self.progress_page = ProgressPage(context.local_data, context.assets); self.settings_page = SettingsPage(context.local_data, context.settings, context.sync); self.match_detail_page = MatchDetailPage(context.local_data, context.analysis, context.assets)
        for page in (self.dashboard_page, self.matches_page, self.progress_page, self.settings_page, self.match_detail_page): self.stack.addWidget(page)
        self.dashboard_page.open_match.connect(self.open_match); self.matches_page.open_match.connect(self.open_match); self.match_detail_page.back_requested.connect(lambda: self.navigate(self.PAGE_MATCHES)); self.settings_page.settings_changed.connect(self.refresh_all)
        work.addWidget(self.stack, 1); outer.addWidget(workspace, 1); self.setCentralWidget(central); self.navigate(0); self.refresh_header()

    def refresh_header(self):
        try:
            player, status = self.context.local_data.player(), self.context.local_data.status()
            self.player.setText(player.riot_id); self.api.set_status(status.api_status); self.sync_badge.set_status(status.sync_status)
            self.statusBar().showMessage(f"Local-first • {status.match_count} partie(s) SoloQ • {status.latest_match_date}")
        except Exception:
            self.player.setText("Joueur local indisponible"); self.api.set_status("UNKNOWN"); self.sync_badge.set_status("OFFLINE")

    def navigate(self, index):
        pages = [self.dashboard_page, self.matches_page, self.progress_page, self.settings_page]
        if index < 4: pages[index].refresh()
        self.stack.setCurrentIndex(index); names = ["Tableau de bord", "Historique", "Progression", "Réglages et données", "Analyse post-game"]
        self.page_title.setText(names[index]); [button.setChecked(i == index) for i, button in enumerate(self.nav_buttons)]

    def open_match(self, match_id):
        self.match_detail_page.load_match(match_id); self.stack.setCurrentIndex(self.PAGE_MATCH_DETAIL); self.page_title.setText("Analyse post-game"); [button.setChecked(False) for button in self.nav_buttons]

    def start_sync(self):
        if self.sync_worker: return
        self.sync_button.setEnabled(False); self.progress.setVisible(True); self.progress.setValue(1); self.sync_text.setText("Synchronisation…"); self.sync_badge.set_status("RUNNING")
        worker = FunctionWorker(self.context.sync.sync, with_progress=True); worker.signals.progress.connect(self._sync_progress); worker.signals.result.connect(self._sync_result); worker.signals.error.connect(self._sync_failed); worker.signals.finished.connect(self._sync_finished); self.sync_worker = worker; QThreadPool.globalInstance().start(worker)

    def _sync_progress(self, message, value): self.sync_text.setText(message); self.progress.setValue(value)
    def _sync_result(self, result):
        status = result.get("status", "ERROR"); message = result.get("message", status); self.refresh_all(); self.sync_text.setText(message); self.sync_badge.set_status(status); self.api.set_status(self.context.settings.api_status())
    def _sync_failed(self, message): self.sync_text.setText(message); self.sync_badge.set_status("ERROR"); self.api.set_status(self.context.settings.api_status())
    def _sync_finished(self): self.sync_worker = None; self.sync_button.setEnabled(True); self.progress.setVisible(False)
    def refresh_all(self): self.dashboard_page.refresh(); self.matches_page.refresh(); self.progress_page.refresh(); self.settings_page.refresh(); self.refresh_header()
