from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from services.asset_service import AssetService
from ui.components.asset_icon import AssetIcon
from ui.components.status_badge import StatusBadge
from viewmodels import MatchSummaryViewModel


class MatchCard(QFrame):
    opened = Signal(str)

    def __init__(self, match: MatchSummaryViewModel, assets: AssetService, parent=None):
        super().__init__(parent)
        self.match = match
        self.setObjectName("MatchCard")
        self.setProperty("result", match.result.lower())
        root = QHBoxLayout(self)
        root.setContentsMargins(14, 11, 12, 11)
        root.setSpacing(14)
        icon = AssetIcon(assets, 44)
        icon.load("champion", match.champion, match.game_version, match.champion)
        root.addWidget(icon)

        identity = QVBoxLayout()
        name = QLabel(match.champion)
        name.setObjectName("MatchChampion")
        identity.addWidget(name)
        result = QLabel(f"{'VICTORY' if match.result == 'WIN' else 'DEFEAT'}  •  {match.position}")
        result.setProperty("result", match.result.lower())
        identity.addWidget(result)
        root.addLayout(identity, 2)

        for title, value in (("K / D / A", match.kda_text),
                             ("CS / MIN", "—" if match.cs_per_min is None else f"{match.cs_per_min:.1f}"),
                             ("DURATION", f"{match.duration_seconds // 60}:{match.duration_seconds % 60:02d}")):
            box = QVBoxLayout()
            label = QLabel(title); label.setObjectName("MicroLabel")
            data = QLabel(value); data.setObjectName("MatchMetric")
            box.addWidget(label); box.addWidget(data)
            root.addLayout(box, 1)

        self.items_widget = QFrame(); items = QHBoxLayout(self.items_widget); items.setContentsMargins(0, 0, 0, 0); items.setSpacing(3)
        for item_id in match.items[:4]:
            item = AssetIcon(assets, 24); item.load("item", item_id, match.game_version, "")
            items.addWidget(item)
        root.addWidget(self.items_widget)
        side = QVBoxLayout()
        self.date = QLabel(match.played_at.split(" ")[0]); self.date.setObjectName("Muted")
        side.addWidget(self.date, 0, Qt.AlignmentFlag.AlignRight)
        side.addWidget(StatusBadge(match.analysis_status), 0, Qt.AlignmentFlag.AlignRight)
        root.addLayout(side)
        button = QPushButton("Open")
        button.setObjectName("CompactButton")
        button.clicked.connect(lambda: self.opened.emit(match.match_id))
        root.addWidget(button)

    def resizeEvent(self, event):
        compact = event.size().width() < 920
        self.items_widget.setVisible(not compact)
        self.date.setVisible(not compact)
        super().resizeEvent(event)
