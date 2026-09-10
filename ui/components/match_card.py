from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from services.asset_service import AssetService
from ui.components.asset_icon import AssetIcon
from ui.components.status_badge import StatusBadge
from viewmodels import MatchSummaryViewModel


class MatchCard(QFrame):
    opened = Signal(str)

    def __init__(self, match: MatchSummaryViewModel, assets: AssetService, composition: dict | None = None, parent=None):
        super().__init__(parent); self.match = match; self.setObjectName("MatchCard"); self.setProperty("result", match.result.lower())
        outer = QVBoxLayout(self); outer.setContentsMargins(16, 12, 14, 12); outer.setSpacing(9)
        root = QHBoxLayout(); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(14)
        icon = AssetIcon(assets, 44); icon.load("champion", match.champion, match.game_version, match.champion); root.addWidget(icon)
        identity = QVBoxLayout(); name = QLabel(match.champion); name.setObjectName("MatchChampion"); identity.addWidget(name)
        result = QLabel(f"{match.result_text}  •  {match.position}"); result.setProperty("result", match.result.lower()); identity.addWidget(result); root.addLayout(identity, 2)
        for title, value in (("K / D / A", match.kda_text), ("CS / MIN", "—" if match.cs_per_min is None else f"{match.cs_per_min:.1f}"), ("DURÉE", match.duration_text)):
            box = QVBoxLayout(); label = QLabel(title); label.setObjectName("MicroLabel"); data = QLabel(value); data.setObjectName("MatchMetric"); box.addWidget(label); box.addWidget(data); root.addLayout(box, 1)
        self.items_widget = QFrame(); items = QHBoxLayout(self.items_widget); items.setContentsMargins(0, 0, 0, 0); items.setSpacing(3)
        inventory = list(match.items)
        if match.trinket_id in inventory: inventory.remove(match.trinket_id)
        for item_id in inventory[:6]:
            item = AssetIcon(assets, 24); item.load("item", item_id, match.game_version, ""); items.addWidget(item)
        if match.trinket_id:
            items.addSpacing(5); trinket = AssetIcon(assets, 24); trinket.load("item", match.trinket_id, match.game_version, ""); items.addWidget(trinket)
        root.addWidget(self.items_widget)
        side = QVBoxLayout(); self.date = QLabel(match.played_at.split(" ")[0]); self.date.setObjectName("Muted"); side.addWidget(self.date, 0, Qt.AlignmentFlag.AlignRight); side.addWidget(StatusBadge(match.analysis_status), 0, Qt.AlignmentFlag.AlignRight); root.addLayout(side)
        button = QPushButton("Ouvrir"); button.setObjectName("CompactButton"); button.clicked.connect(lambda: self.opened.emit(match.match_id)); root.addWidget(button); outer.addLayout(root)
        self.composition_widget = QFrame(); self.composition_widget.setObjectName("MatchupStrip"); composition_box = QVBoxLayout(self.composition_widget); composition_box.setContentsMargins(10, 7, 10, 7); composition_box.setSpacing(3)
        allies = "  •  ".join((composition or {}).get('allies') or ())
        enemies = "  •  ".join((composition or {}).get('enemies') or ())
        ally_line = QLabel("AVEC  ·  " + (allies or "Composition locale indisponible")); ally_line.setObjectName("MatchupLine"); ally_line.setProperty("side", "ally"); ally_line.setWordWrap(True); composition_box.addWidget(ally_line)
        enemy_line = QLabel("CONTRE  ·  " + (enemies or "Composition adverse indisponible")); enemy_line.setObjectName("MatchupLine"); enemy_line.setProperty("side", "enemy"); enemy_line.setWordWrap(True); composition_box.addWidget(enemy_line)
        self.composition_widget.setVisible(composition is not None); outer.addWidget(self.composition_widget)

    def resizeEvent(self, event):
        compact = event.size().width() < 850; self.items_widget.setVisible(not compact); self.date.setVisible(not compact); super().resizeEvent(event)
