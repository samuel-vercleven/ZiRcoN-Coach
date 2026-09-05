from PySide6.QtCore import QThreadPool, Signal
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
        title = QLabel("Réglages et données"); title.setObjectName("PageTitle"); root.addWidget(title)
        api = QFrame(); api.setObjectName("Card"); layout = QVBoxLayout(api)
        heading = QHBoxLayout(); name = QLabel("Accès Riot API"); name.setObjectName("SectionTitle"); heading.addWidget(name); heading.addStretch(); heading.addWidget(QLabel("CLÉ ACTIVE")); self.api_badge = StatusBadge("UNKNOWN"); heading.addWidget(self.api_badge); layout.addLayout(heading)
        note = QLabel("La clé de développement reste dans .env, n’est jamais affichée et devient active immédiatement après validation + sauvegarde. Tester une candidate ne modifie pas la clé active."); note.setObjectName("Muted"); note.setWordWrap(True); layout.addWidget(note)
        form = QFormLayout(); self.riot_id = QLineEdit(); self.key = QLineEdit(); self.key.setEchoMode(QLineEdit.EchoMode.Password); self.key.setPlaceholderText("Coller une clé candidate — la valeur active reste masquée")
        self.scope = QComboBox(); [self.scope.addItem(str(value), value) for value in (20, 50, 100)]; form.addRow("Riot ID", self.riot_id); form.addRow("Clé candidate", self.key); form.addRow("Dernières parties", self.scope); layout.addLayout(form)
        candidate = QHBoxLayout(); candidate.addWidget(QLabel("VALIDATION CANDIDATE")); self.candidate_badge = StatusBadge("NOT_TESTED"); candidate.addWidget(self.candidate_badge); candidate.addStretch(); layout.addLayout(candidate)
        actions = QHBoxLayout(); self.account_save = QPushButton("Enregistrer le compte"); self.account_save.setObjectName("CompactButton"); self.validate = QPushButton("Tester la candidate"); self.validate.setObjectName("CompactButton"); self.save = QPushButton("Valider et activer"); self.save.setObjectName("PrimaryButton"); actions.addWidget(self.account_save); actions.addWidget(self.validate); actions.addWidget(self.save); actions.addStretch(); layout.addLayout(actions)
        self.message = QLabel(); self.message.setWordWrap(True); self.message.setObjectName("Muted"); layout.addWidget(self.message); root.addWidget(api)

        data = QFrame(); data.setObjectName("Card"); dl = QVBoxLayout(data); data_title = QLabel("État des données locales — compte actif / SoloQ"); data_title.setObjectName("SectionTitle"); dl.addWidget(data_title)
        self.data_form = QFormLayout(); labels = ("Base de données", "Base disponible", "Parties chargées", "Timelines en cache", "Parties analysées", "Partie la plus récente", "Dernière sync", "Clé configurée", "Backend")
        self.fields = {label: QLabel() for label in labels}
        for label, field in self.fields.items(): field.setWordWrap(True); self.data_form.addRow(label, field)
        dl.addLayout(self.data_form); root.addWidget(data); root.addStretch()
        self.account_save.clicked.connect(self._save_account); self.validate.clicked.connect(lambda: self._start_validation(False)); self.save.clicked.connect(lambda: self._start_validation(True)); self.refresh()

    def _save_account(self):
        try:
            self.settings.save_identity(self.riot_id.text().strip(), int(self.scope.currentData()))
            self.message.setText("Compte actif et périmètre enregistrés localement."); self.settings_changed.emit()
        except ValueError as error:
            self.message.setText(str(error))

    def _start_validation(self, save: bool):
        key = self.key.text().strip() or self.settings.api_key(); riot_id = self.riot_id.text().strip()
        self.validate.setEnabled(False); self.save.setEnabled(False); self.candidate_badge.set_status("TESTING"); self.message.setText("Validation non bloquante de la candidate…")
        worker = FunctionWorker(self.sync.validate_key, key, riot_id); worker.signals.result.connect(lambda result: self._validation_done(result, key, riot_id, save)); worker.signals.error.connect(self._validation_error); self.worker = worker; QThreadPool.globalInstance().start(worker)

    def _validation_done(self, result, key, riot_id, save):
        self.candidate_badge.set_status(result.status.value); self.message.setText(result.message or result.status.value)
        if result.ok and save:
            try:
                self.settings.save_api_key(key); self.settings.save_identity(riot_id, int(self.scope.currentData())); self.key.clear(); self.message.setText("Candidate validée, enregistrée et active immédiatement."); self.settings_changed.emit()
            except Exception:
                self.message.setText("Validation réussie, mais sauvegarde locale impossible.")
        self.validate.setEnabled(True); self.save.setEnabled(True); self.refresh()

    def _validation_error(self, message):
        self.message.setText(message); self.candidate_badge.set_status("ERROR"); self.validate.setEnabled(True); self.save.setEnabled(True)

    def refresh(self):
        player = self.local.player(); identity = self.settings.identity(); self.riot_id.setText(identity.riot_id if identity else player.riot_id if "#" in player.riot_id else "")
        index = self.scope.findData(self.settings.sync_scope()); self.scope.setCurrentIndex(max(0, index)); status = self.local.status(); self.api_badge.set_status(status.api_status)
        self.fields["Base de données"].setText(status.db_path); self.fields["Base disponible"].setText("Oui" if status.db_available else "Non"); self.fields["Parties chargées"].setText(str(status.match_count)); self.fields["Timelines en cache"].setText(str(status.timeline_count)); self.fields["Parties analysées"].setText(str(status.analyzed_match_count)); self.fields["Partie la plus récente"].setText(status.latest_match_date); self.fields["Dernière sync"].setText(status.last_sync_at); self.fields["Clé configurée"].setText(self.settings.masked_key()); self.fields["Backend"].setText("Gelé jusqu’à Phase 2I · zero-gate owner semantics préservé")
