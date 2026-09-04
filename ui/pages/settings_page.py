from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget

from services.local_data import LocalDataService


class SettingsPage(QWidget):
    def __init__(self, service: LocalDataService, parent=None) -> None:
        super().__init__(parent)
        self._service = service

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(18)

        title = QLabel("Settings & Data")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        subtitle = QLabel(
            "V0.1 Alpha is local-first. Riot network sync will be connected "
            "without making API availability a startup requirement."
        )
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        self.form = QFormLayout()
        self.db_path = QLabel()
        self.db_available = QLabel()
        self.match_count = QLabel()
        self.latest_match = QLabel()
        self.api_status = QLabel()
        self.sync_status = QLabel()

        for label in (
            self.db_path,
            self.db_available,
            self.match_count,
            self.latest_match,
            self.api_status,
            self.sync_status,
        ):
            label.setTextInteractionFlags(label.textInteractionFlags())
            label.setWordWrap(True)

        self.form.addRow("Database", self.db_path)
        self.form.addRow("Local DB available", self.db_available)
        self.form.addRow("Loaded matches", self.match_count)
        self.form.addRow("Latest match", self.latest_match)
        self.form.addRow("Riot API configured", self.api_status)
        self.form.addRow("Sync status", self.sync_status)

        root.addLayout(self.form)
        root.addStretch(1)

        self.refresh()

    def refresh(self) -> None:
        try:
            status = self._service.status()
        except Exception as exc:
            self.db_path.setText("Unavailable")
            self.db_available.setText("No")
            self.match_count.setText("0")
            self.latest_match.setText("Unavailable")
            self.api_status.setText("Unknown")
            self.sync_status.setText(str(exc))
            return

        self.db_path.setText(status.db_path)
        self.db_available.setText("Yes" if status.db_available else "No")
        self.match_count.setText(str(status.match_count))
        self.latest_match.setText(status.latest_match_date)
        self.api_status.setText("Yes" if status.api_configured else "No")
        self.sync_status.setText(status.sync_status)
