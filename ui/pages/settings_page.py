from PySide6.QtCore import QThreadPool, Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QScrollArea

from services.local_data import LocalDataService
from services.riot_sync import RiotSyncService
from services.runtime_settings import RuntimeSettingsService
from ui.components.status_badge import StatusBadge
from ui.workers import FunctionWorker


def _player_sync_message(message: str) -> str:
    if not message:
        return "Aucun import récent."
    folded = message.casefold()
    if "échecs 0" in folded:
        return "Import terminé sans problème."
    if "échec" in folded or "failed" in folded or "error" in folded:
        return "Import terminé, mais certaines informations n’ont pas pu être récupérées. Tu peux réessayer."
    return "Import terminé. Tes parties sont prêtes à être consultées."


def _player_validation_message(result) -> str:
    if result.ok:
        return "La clé fonctionne."
    messages = {
        "NOT_CONFIGURED": "Ajoute une clé Riot pour importer tes parties.",
        "UNAUTHORIZED_OR_EXPIRED": "Cette clé n’est plus valide. Vérifie-la puis réessaie.",
        "FORBIDDEN": "Cette clé n’a pas l’autorisation nécessaire.",
        "NETWORK_ERROR": "Connexion à Riot impossible pour le moment.",
        "ACCOUNT_NOT_FOUND": "Compte Riot introuvable. Vérifie ton identifiant.",
        "RATE_LIMITED": "Trop de demandes pour le moment. Réessaie un peu plus tard.",
        "RIOT_SERVER_ERROR": "Le service Riot ne répond pas correctement. Réessaie plus tard.",
    }
    return messages.get(result.status.value, "La clé n’a pas pu être vérifiée. Vérifie les informations puis réessaie.")


class SettingsPage(QWidget):
    settings_changed = Signal()

    def __init__(self, local: LocalDataService, settings: RuntimeSettingsService, sync: RiotSyncService, parent=None):
        super().__init__(parent); self.local, self.settings, self.sync = local, settings, sync; self.worker = None
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); host = QWidget(); root = QVBoxLayout(host)
        scroll.setWidget(host); outer.addWidget(scroll)
        root.setContentsMargins(30, 24, 30, 24); root.setSpacing(15)
        api = QFrame(); api.setObjectName("Card"); layout = QVBoxLayout(api)
        heading = QHBoxLayout(); name = QLabel("Connexion à Riot Games"); name.setObjectName("SectionTitle"); heading.addWidget(name); heading.addStretch(); heading.addWidget(QLabel("ÉTAT")); self.api_badge = StatusBadge("UNKNOWN"); heading.addWidget(self.api_badge); layout.addLayout(heading)
        note = QLabel("Renseigne ton identifiant Riot et une clé d’accès pour importer tes parties. La clé reste masquée et enregistrée sur cet ordinateur."); note.setObjectName("Muted"); note.setWordWrap(True); layout.addWidget(note)
        form = QFormLayout(); self.riot_id = QLineEdit(); self.key = QLineEdit(); self.key.setEchoMode(QLineEdit.EchoMode.Password); self.key.setPlaceholderText("Colle ta clé Riot ici — elle restera masquée")
        self.scope = QComboBox(); [self.scope.addItem(str(value), value) for value in (20, 50, 100)]; form.addRow("Riot ID", self.riot_id); form.addRow("Clé d’accès", self.key); form.addRow("Parties à importer", self.scope); layout.addLayout(form)
        candidate = QHBoxLayout(); candidate.addWidget(QLabel("VÉRIFICATION DE LA CLÉ")); self.candidate_badge = StatusBadge("NOT_TESTED"); candidate.addWidget(self.candidate_badge); candidate.addStretch(); layout.addLayout(candidate)
        actions = QHBoxLayout(); self.account_save = QPushButton("Enregistrer le compte"); self.account_save.setObjectName("CompactButton"); self.validate = QPushButton("Vérifier la clé"); self.validate.setObjectName("CompactButton"); self.save = QPushButton("Enregistrer et activer"); self.save.setObjectName("PrimaryButton"); actions.addWidget(self.account_save); actions.addWidget(self.validate); actions.addWidget(self.save); actions.addStretch(); layout.addLayout(actions)
        self.message = QLabel(); self.message.setWordWrap(True); self.message.setObjectName("Muted"); layout.addWidget(self.message); root.addWidget(api)

        data = QFrame(); data.setObjectName("Card"); dl = QVBoxLayout(data); data_title = QLabel("Tes données de partie"); data_title.setObjectName("SectionTitle"); dl.addWidget(data_title)
        self.data_form = QFormLayout(); labels = ("Parties enregistrées", "Détails de partie disponibles", "Parties analysées", "Partie la plus récente", "Dernière mise à jour", "Résultat de l’import", "Clé enregistrée")
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
        self.validate.setEnabled(False); self.save.setEnabled(False); self.candidate_badge.set_status("TESTING"); self.message.setText("Vérification de la clé…")
        worker = FunctionWorker(self.sync.validate_key, key, riot_id); worker.signals.result.connect(lambda result: self._validation_done(result, key, riot_id, save)); worker.signals.error.connect(self._validation_error); self.worker = worker; QThreadPool.globalInstance().start(worker)

    def _validation_done(self, result, key, riot_id, save):
        self.candidate_badge.set_status(result.status.value); self.message.setText(_player_validation_message(result))
        if result.ok and save:
            try:
                self.settings.save_api_key(key); self.settings.save_identity(riot_id, int(self.scope.currentData())); self.key.clear(); self.message.setText("Clé enregistrée et prête à l’emploi."); self.settings_changed.emit()
            except Exception:
                self.message.setText("Clé vérifiée, mais elle n’a pas pu être enregistrée sur cet ordinateur.")
        self.validate.setEnabled(True); self.save.setEnabled(True); self.refresh()

    def _validation_error(self, message):
        self.message.setText("La clé n’a pas pu être vérifiée. Réessaie dans un instant."); self.candidate_badge.set_status("ERROR"); self.validate.setEnabled(True); self.save.setEnabled(True)

    def refresh(self):
        player = self.local.player(); identity = self.settings.identity(); self.riot_id.setText(identity.riot_id if identity else player.riot_id if "#" in player.riot_id else "")
        index = self.scope.findData(self.settings.sync_scope()); self.scope.setCurrentIndex(max(0, index)); status = self.local.status(); self.api_badge.set_status(status.api_status)
        self.fields["Parties enregistrées"].setText(str(status.match_count)); self.fields["Détails de partie disponibles"].setText(str(status.timeline_count)); self.fields["Parties analysées"].setText(str(status.analyzed_match_count)); self.fields["Partie la plus récente"].setText(status.latest_match_date); self.fields["Dernière mise à jour"].setText(status.last_sync_at); self.fields["Résultat de l’import"].setText(_player_sync_message(status.sync_message)); self.fields["Clé enregistrée"].setText("Oui" if self.settings.masked_key() else "Non")
