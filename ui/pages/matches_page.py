from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Qt, QTimer, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget

from services.asset_service import AssetService
from services.local_data import LocalDataService
from ui.components.empty_state import EmptyState
from ui.components.match_card import MatchCard


class MatchesPage(QWidget):
    open_match = Signal(str)
    PAGE_SIZE = 24

    def __init__(self, service: LocalDataService, assets: AssetService, parent=None):
        super().__init__(parent)
        self.service, self.assets = service, assets
        self._visible_count = self.PAGE_SIZE
        self._filtered_matches = []
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(180)
        self._search_timer.timeout.connect(lambda: self.refresh(reset=True))

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 24, 30, 24)
        root.setSpacing(14)
        header = QHBoxLayout()
        intro = QVBoxLayout()
        self.status = QLabel()
        self.status.setObjectName("Muted")
        intro.addWidget(self.status)
        header.addLayout(intro)
        header.addStretch()
        root.addLayout(header)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher un champion…")
        self.search.setMinimumWidth(280)
        self.search.setMaximumWidth(430)
        self.role = QComboBox()
        self.role.addItem("Tous les rôles", "ALL")
        self.patch = QComboBox()
        self.patch.addItem("Tous les patchs", "ALL")
        self.result = QComboBox()
        self.result.addItem("Tous les résultats", "ALL")
        self.result.addItem("Victoires", "WIN")
        self.result.addItem("Défaites", "LOSS")
        self.starred = QComboBox()
        self.starred.addItem("Toutes les parties", False)
        self.starred.addItem("Favoris", True)
        controls.addWidget(self.search, 1)
        for control in (self.role, self.patch, self.result, self.starred):
            control.setMinimumWidth(145)
            controls.addWidget(control)
        controls.addStretch()
        root.addLayout(controls)

        self.search.textChanged.connect(lambda: self._search_timer.start())
        for control in (self.role, self.patch, self.result, self.starred):
            control.currentIndexChanged.connect(lambda _index: self.refresh(reset=True))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        host = QWidget()
        self.list = QVBoxLayout(host)
        self.list.setContentsMargins(0, 0, 8, 0)
        self.list.setSpacing(8)
        scroll.setWidget(host)
        root.addWidget(scroll)
        self.refresh(reset=True)

    def _clear(self) -> None:
        while self.list.count():
            item = self.list.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def refresh(self, reset: bool = True) -> None:
        if reset:
            self._visible_count = self.PAGE_SIZE
        self._clear()
        try:
            all_matches = self.service.matches("ALL")
            roles = sorted({match.position for match in all_matches if match.position and match.position != "UNKNOWN"})
            patches = sorted({".".join(match.game_version.split(".")[:2]) for match in all_matches if match.game_version}, reverse=True)
            self._sync_options(self.role, roles)
            self._sync_options(self.patch, patches)
            query = self.search.text().strip().lower()
            role, patch, result = self.role.currentData(), self.patch.currentData(), self.result.currentData()
            starred_ids = self.service.cache.starred_match_ids() if self.service.cache else set()
            self._filtered_matches = [
                match for match in all_matches
                if (not query or query in match.champion.lower())
                and (role == "ALL" or match.position == role)
                and (patch == "ALL" or match.game_version.startswith(patch))
                and (result == "ALL" or match.result == result)
                and (not self.starred.currentData() or match.match_id in starred_ids)
            ]
        except Exception:
            self._filtered_matches = []

        visible = self._filtered_matches[:self._visible_count]
        try:
            compositions = self.service.match_compositions(match.match_id for match in visible)
        except Exception:
            compositions = {}
        self.status.setText(
            f"{len(self._filtered_matches)} parties analysées · "
            f"{len(visible)} affichées · données locales"
        )
        if not visible:
            self.list.addWidget(EmptyState(
                "Aucune partie SoloQ",
                "Modifie les filtres ou synchronise les données depuis le bouton en haut.",
            ))
        for match in visible:
            card = MatchCard(match, self.assets, compositions.get(match.match_id))
            card.opened.connect(self.open_match)
            self.list.addWidget(card)
        if len(visible) < len(self._filtered_matches):
            more = QPushButton(f"Afficher {min(self.PAGE_SIZE, len(self._filtered_matches) - len(visible))} parties de plus")
            more.setObjectName("SecondaryButton")
            more.clicked.connect(self._show_more)
            self.list.addWidget(more, 0, Qt.AlignmentFlag.AlignHCenter)
        self.list.addStretch()

    def _show_more(self) -> None:
        self._visible_count += self.PAGE_SIZE
        self.refresh(reset=False)

    @staticmethod
    def _sync_options(combo, values) -> None:
        current = combo.currentData()
        existing = [combo.itemData(index) for index in range(combo.count())]
        with QSignalBlocker(combo):
            for value in values:
                if value not in existing:
                    combo.addItem(value, value)
            index = combo.findData(current)
            if index >= 0:
                combo.setCurrentIndex(index)
