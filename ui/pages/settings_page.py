from PySide6.QtCore import Signal, QThreadPool
from PySide6.QtWidgets import QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from services.local_data import LocalDataService
from services.riot_sync import RiotSyncService
from services.runtime_settings import RuntimeSettingsService
from ui.components.status_badge import StatusBadge
from ui.workers import FunctionWorker


class SettingsPage(QWidget):
    settings_changed = Signal()
    def __init__(self, local: LocalDataService, settings: RuntimeSettingsService, sync: RiotSyncService, parent=None):
        super().__init__(parent); self.local, self.settings, self.sync = local, settings, sync; self.worker = None
        root = QVBoxLayout(self); root.setContentsMargins(26, 20, 26, 22); root.setSpacing(15)
        title = QLabel("Settings & data"); title.setObjectName("PageTitle"); root.addWidget(title)
        api = QFrame(); api.setObjectName("Card"); layout = QVBoxLayout(api); heading = QHBoxLayout(); name = QLabel("Riot API"); name.setObjectName("SectionTitle"); heading.addWidget(name); heading.addStretch(); self.api_badge = StatusBadge("UNKNOWN"); heading.addWidget(self.api_badge); layout.addLayout(heading)
        note = QLabel("The development key stays in .env, is masked here, and takes effect immediately after validation."); note.setObjectName("Muted"); note.setWordWrap(True); layout.addWidget(note)
        form = QFormLayout(); self.riot_id = QLineEdit(); self.key = QLineEdit(); self.key.setEchoMode(QLineEdit.EchoMode.Password); self.key.setPlaceholderText("Paste a replacement key — existing value is never displayed")
        self.scope = QComboBox(); [self.scope.addItem(str(value), value) for value in (20, 50, 100)]; form.addRow("Riot ID", self.riot_id); form.addRow("API key", self.key); form.addRow("Sync latest", self.scope); layout.addLayout(form)
        actions = QHBoxLayout(); self.validate = QPushButton("Validate"); self.validate.setObjectName("CompactButton"); self.save = QPushButton("Validate & save key"); self.save.setObjectName("PrimaryButton"); actions.addWidget(self.validate); actions.addWidget(self.save); actions.addStretch(); layout.addLayout(actions); self.message = QLabel(); self.message.setWordWrap(True); self.message.setObjectName("Muted"); layout.addWidget(self.message); root.addWidget(api)
        data = QFrame(); data.setObjectName("Card"); dl = QVBoxLayout(data); data_title = QLabel("Local data status"); data_title.setObjectName("SectionTitle"); dl.addWidget(data_title); self.data_form = QFormLayout(); self.fields = {name: QLabel() for name in ("Database", "DB available", "Loaded matches", "Latest match", "API configured", "Backend")}
        for name, field in self.fields.items(): field.setWordWrap(True); self.data_form.addRow(name, field)
        dl.addLayout(self.data_form); root.addWidget(data); root.addStretch(); self.validate.clicked.connect(lambda: self._start_validation(False)); self.save.clicked.connect(lambda: self._start_validation(True)); self.refresh()
    def _start_validation(self, save: bool):
        key = self.key.text().strip() or self.settings.api_key(); riot_id = self.riot_id.text().strip(); self.validate.setEnabled(False); self.save.setEnabled(False); self.message.setText("Validating without blocking the UI…")
        worker = FunctionWorker(self.sync.validate_key, key, riot_id); worker.signals.result.connect(lambda result: self._validation_done(result, key, riot_id, save)); worker.signals.error.connect(self._validation_error); self.worker = worker; QThreadPool.globalInstance().start(worker)
    def _validation_done(self, result, key, riot_id, save):
        self.settings.set_api_status(result.status.value); self.api_badge.set_status(result.status.value); self.message.setText(result.message or result.status.value)
        if result.ok and save:
            try:
                self.settings.save_api_key(key); self.settings.save_identity(riot_id, int(self.scope.currentData())); self.key.clear(); self.message.setText("Key validated and saved. It is active immediately."); self.settings_changed.emit()
            except Exception: self.message.setText("Validation passed, but local settings could not be saved.")
        self.validate.setEnabled(True); self.save.setEnabled(True); self.refresh()
    def _validation_error(self, message):
        self.message.setText(message); self.api_badge.set_status("ERROR"); self.validate.setEnabled(True); self.save.setEnabled(True)
    def refresh(self):
        player = self.local.player(); identity = self.settings.identity(); self.riot_id.setText(identity.riot_id if identity else player.riot_id if "#" in player.riot_id else "")
        index = self.scope.findData(self.settings.sync_scope()); self.scope.setCurrentIndex(max(0, index)); status = self.local.status(); self.api_badge.set_status(status.api_status)
        self.fields["Database"].setText(status.db_path); self.fields["DB available"].setText("Yes" if status.db_available else "No"); self.fields["Loaded matches"].setText(str(status.match_count)); self.fields["Latest match"].setText(status.latest_match_date); self.fields["API configured"].setText(self.settings.masked_key()); self.fields["Backend"].setText("Frozen through Phase 2I • zero-gate owner semantics preserved")
