from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from services.asset_service import AssetService
from ui.components.asset_icon import AssetIcon
from viewmodels import MatchSummaryViewModel


def _composition_entry(value: str) -> tuple[str, str]:
    parts = str(value or "").split(" ", 1)
    if len(parts) == 2 and parts[0] in {"TOP", "JUNGLE", "MIDDLE", "MID", "BOTTOM", "ADC", "UTILITY", "SUPPORT"}:
        return parts[0], parts[1]
    return "", str(value or "Inconnu")


class MatchCard(QFrame):
    """Stable desktop row shared by dashboard and history."""

    opened = Signal(str)

    def __init__(self, match: MatchSummaryViewModel, assets: AssetService,
                 composition: dict | None = None, compact: bool = False, parent=None):
        super().__init__(parent)
        self.match = match
        self.setObjectName("MatchCard")
        self.setProperty("result", match.result.lower())
        self.setFixedHeight(92 if compact else 98)

        grid = QGridLayout(self)
        grid.setContentsMargins(14, 10, 12, 10)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(0)

        champion = QWidget()
        champion_box = QHBoxLayout(champion)
        champion_box.setContentsMargins(0, 0, 0, 0)
        champion_box.setSpacing(10)
        portrait = AssetIcon(assets, 48)
        portrait.load("champion", match.champion, match.game_version, match.champion)
        champion_box.addWidget(portrait)
        identity = QVBoxLayout()
        identity.setSpacing(2)
        name = QLabel(match.champion)
        name.setObjectName("MatchChampion")
        role = QLabel(match.position.title() if match.position else "Rôle inconnu")
        role.setObjectName("Muted")
        identity.addWidget(name)
        identity.addWidget(role)
        champion_box.addLayout(identity)
        champion.setFixedWidth(156)
        grid.addWidget(champion, 0, 0)

        outcome = QVBoxLayout()
        outcome.setSpacing(2)
        result = QLabel(match.result_text.title())
        result.setProperty("result", match.result.lower())
        result.setObjectName("MatchMetric")
        analysis = QLabel(
            "Analyse disponible" if match.analysis_status == "AVAILABLE"
            else "Analyse partielle" if match.analysis_status == "PARTIAL"
            else "Analyse à compléter"
        )
        analysis.setObjectName("Muted")
        outcome.addWidget(result)
        outcome.addWidget(analysis)
        grid.addLayout(outcome, 0, 1)

        grid.addWidget(self._metric(match.kda_text, "KDA"), 0, 2)
        cs = "—" if match.cs_per_min is None else f"{match.cs_per_min:.1f}"
        grid.addWidget(self._metric(cs, "CS/min"), 0, 3)
        grid.addWidget(self._metric(match.duration_text, "Durée"), 0, 4)

        items_host = QWidget()
        items = QHBoxLayout(items_host)
        items.setContentsMargins(0, 0, 0, 0)
        items.setSpacing(4)
        inventory = list(match.items)
        if match.trinket_id in inventory:
            inventory.remove(match.trinket_id)
        for item_id in inventory[:6]:
            item = AssetIcon(assets, 30)
            item.load("item", item_id, match.game_version, "")
            items.addWidget(item)
        for _empty in range(max(0, 6 - len(inventory[:6]))):
            slot = QFrame()
            slot.setFixedSize(30, 30)
            slot.setStyleSheet("background:#0B1521;border:1px solid #1A2B3D;border-radius:6px;")
            items.addWidget(slot)
        if match.trinket_id:
            items.addSpacing(4)
            trinket = AssetIcon(assets, 30)
            trinket.load("item", match.trinket_id, match.game_version, "")
            items.addWidget(trinket)
        items.addStretch()
        items_host.setFixedWidth(228)
        grid.addWidget(items_host, 0, 5)

        self.composition_widget = self._composition(assets, match, composition)
        self.composition_widget.setFixedWidth(132)
        grid.addWidget(self.composition_widget, 0, 6)

        date = QLabel(match.played_at.split(" ")[0])
        date.setObjectName("Muted")
        date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date.setFixedWidth(84)
        grid.addWidget(date, 0, 7)
        button = QPushButton("Ouvrir  ›")
        button.setObjectName("GhostButton")
        button.setFixedWidth(78)
        button.clicked.connect(lambda: self.opened.emit(match.match_id))
        grid.addWidget(button, 0, 8)
        grid.setColumnStretch(1, 1)

    @staticmethod
    def _metric(value: str, label: str) -> QWidget:
        host = QWidget()
        box = QVBoxLayout(host)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(2)
        data = QLabel(value)
        data.setObjectName("MatchMetric")
        micro = QLabel(label)
        micro.setObjectName("Muted")
        box.addWidget(data)
        box.addWidget(micro)
        host.setFixedWidth(64 if label != "KDA" else 90)
        return host

    @staticmethod
    def _composition(assets: AssetService, match: MatchSummaryViewModel, composition: dict | None) -> QWidget:
        host = QFrame()
        host.setObjectName("MatchupStrip")
        grid = QGridLayout(host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(3)
        for row_index, (side, label) in enumerate((('allies', 'Ton équipe'), ('enemies', 'Adversaires'))):
            entries = tuple((composition or {}).get(side) or ())
            for column in range(5):
                role, champion = _composition_entry(entries[column]) if column < len(entries) else ('', '')
                icon = AssetIcon(assets, 24)
                icon.setProperty('player', side == 'allies' and champion.lower() == match.champion.lower())
                icon.setToolTip(f"{label} · {role} {champion}" if champion else f"{label} · indisponible")
                icon.load('champion', champion, match.game_version, champion or '·')
                grid.addWidget(icon, row_index, column)
        return host

    def resizeEvent(self, event):
        self.composition_widget.setVisible(event.size().width() >= 960)
        super().resizeEvent(event)
