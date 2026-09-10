from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QVBoxLayout, QWidget

from services.asset_service import AssetService
from services.local_data import LocalDataService
from ui.components.empty_state import EmptyState
from ui.components.match_card import MatchCard


class MatchesPage(QWidget):
    open_match = Signal(str)

    def __init__(self, service: LocalDataService, assets: AssetService, parent=None):
        super().__init__(parent); self.service, self.assets = service, assets
        root = QVBoxLayout(self); root.setContentsMargins(26, 20, 26, 22); root.setSpacing(14)
        header = QHBoxLayout(); intro = QVBoxLayout(); title = QLabel("Historique SoloQ"); title.setObjectName("PageTitle"); self.status = QLabel(); self.status.setObjectName("Muted"); intro.addWidget(title); intro.addWidget(self.status); header.addLayout(intro); header.addStretch()
        self.filter = QComboBox(); self.filter.addItem("Toutes les parties", "ALL"); self.filter.addItem("Victoires", "WIN"); self.filter.addItem("Défaites", "LOSS"); self.filter.currentIndexChanged.connect(self.refresh); header.addWidget(self.filter); root.addLayout(header)
        controls = QHBoxLayout(); self.search = QLineEdit(); self.search.setPlaceholderText("Rechercher un champion…"); self.role = QComboBox(); self.role.addItem("Tous les rôles", "ALL"); self.patch = QComboBox(); self.patch.addItem("Tous les patchs", "ALL"); self.starred = QComboBox(); self.starred.addItem("Toutes", False); self.starred.addItem("Favoris", True)
        for control in (self.search, self.role, self.patch, self.starred): controls.addWidget(control)
        root.addLayout(controls)
        self.search.textChanged.connect(self.refresh); self.role.currentIndexChanged.connect(self.refresh); self.patch.currentIndexChanged.connect(self.refresh); self.starred.currentIndexChanged.connect(self.refresh)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); host = QWidget(); self.list = QVBoxLayout(host); self.list.setContentsMargins(0, 0, 8, 0); self.list.setSpacing(8); self.list.addStretch(); scroll.setWidget(host); root.addWidget(scroll); self.refresh()

    def refresh(self):
        while self.list.count() > 1:
            item = self.list.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide(); widget.setParent(None); widget.deleteLater()
        try:
            all_matches = self.service.matches(str(self.filter.currentData() or "ALL"))
            roles = sorted({match.position for match in all_matches if match.position and match.position != 'UNKNOWN'})
            patches = sorted({'.'.join(match.game_version.split('.')[:2]) for match in all_matches if match.game_version}, reverse=True)
            self._sync_options(self.role, roles); self._sync_options(self.patch, patches)
            query, role, patch = self.search.text().strip().lower(), self.role.currentData(), self.patch.currentData()
            starred_ids = self.service.cache.starred_match_ids() if self.service.cache else set()
            matches = [match for match in all_matches if (not query or query in match.champion.lower())
                       and (role == 'ALL' or match.position == role)
                       and (patch == 'ALL' or match.game_version.startswith(patch))
                       and (not self.starred.currentData() or match.match_id in starred_ids)]
            compositions = self.service.match_compositions(match.match_id for match in matches)
        except Exception:
            matches, compositions = [], {}
        self.status.setText(f"{len(matches)} partie(s) locale(s) • analyse fondée sur les sorties FROZEN")
        if not matches: self.list.insertWidget(0, EmptyState("Aucune partie SoloQ", "Synchronisez lorsqu’une clé API est disponible, ou continuez hors ligne."))
        for index, match in enumerate(matches):
            card = MatchCard(match, self.assets, compositions.get(match.match_id)); card.opened.connect(self.open_match); self.list.insertWidget(index, card)

    @staticmethod
    def _sync_options(combo, values):
        current = combo.currentData(); existing = [combo.itemData(index) for index in range(combo.count())]
        for value in values:
            if value not in existing: combo.addItem(value, value)
        index = combo.findData(current)
        if index >= 0: combo.setCurrentIndex(index)
