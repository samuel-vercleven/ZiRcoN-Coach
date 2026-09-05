from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

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
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); host = QWidget(); self.list = QVBoxLayout(host); self.list.setContentsMargins(0, 0, 8, 0); self.list.setSpacing(8); self.list.addStretch(); scroll.setWidget(host); root.addWidget(scroll); self.refresh()

    def refresh(self):
        while self.list.count() > 1:
            item = self.list.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        try: matches = self.service.matches(str(self.filter.currentData() or "ALL"))
        except Exception: matches = []
        self.status.setText(f"{len(matches)} partie(s) locale(s) • analyse fondée sur les sorties FROZEN")
        if not matches: self.list.insertWidget(0, EmptyState("Aucune partie SoloQ", "Synchronisez lorsqu’une clé API est disponible, ou continuez hors ligne."))
        for index, match in enumerate(matches):
            card = MatchCard(match, self.assets); card.opened.connect(self.open_match); self.list.insertWidget(index, card)
