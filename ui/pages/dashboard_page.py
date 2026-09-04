from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.local_data import LocalDataService
from ui.components.stat_card import StatCard


class DashboardPage(QWidget):
    open_match = Signal(str)

    def __init__(self, service: LocalDataService, parent=None) -> None:
        super().__init__(parent)
        self._service = service

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(18)

        title = QLabel("Dashboard")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        self.player_label = QLabel("Local player")
        self.player_label.setObjectName("Muted")
        root.addWidget(self.player_label)

        cards = QGridLayout()
        cards.setHorizontalSpacing(12)
        cards.setVerticalSpacing(12)

        self.games_card = StatCard("Games")
        self.winrate_card = StatCard("Win rate")
        self.kda_card = StatCard("KDA")
        self.cs_card = StatCard("CS / min")

        cards.addWidget(self.games_card, 0, 0)
        cards.addWidget(self.winrate_card, 0, 1)
        cards.addWidget(self.kda_card, 0, 2)
        cards.addWidget(self.cs_card, 0, 3)
        root.addLayout(cards)

        recent_title_row = QHBoxLayout()
        recent_title = QLabel("Recent matches")
        recent_title.setStyleSheet("font-size: 17px; font-weight: 700;")
        recent_title_row.addWidget(recent_title)
        recent_title_row.addStretch(1)
        root.addLayout(recent_title_row)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Champion", "Result", "K / D / A", "CS/min", "Duration", "Played"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.cellDoubleClicked.connect(self._open_row)
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

        hint = QLabel("Double-click a match to open the post-game detail.")
        hint.setObjectName("Muted")
        root.addWidget(hint)

        self.refresh()

    def refresh(self) -> None:
        try:
            player = self._service.player()
            progress = self._service.progress()
            matches = self._service.matches()[:5]
        except Exception as exc:
            self.player_label.setText(f"Local data unavailable: {exc}")
            self.table.setRowCount(0)
            return

        self.player_label.setText(player.riot_id or "Local player")
        self.games_card.set_value(str(progress.total_games))
        self.winrate_card.set_value(
            "—" if progress.win_rate is None else f"{progress.win_rate:.1f}%"
        )
        self.kda_card.set_value("—" if progress.kda is None else f"{progress.kda:.2f}")
        self.cs_card.set_value(
            "—" if progress.cs_per_min is None else f"{progress.cs_per_min:.2f}"
        )

        self.table.setRowCount(len(matches))
        for row, match in enumerate(matches):
            duration = (
                f"{match.duration_seconds // 60}:{match.duration_seconds % 60:02d}"
                if match.duration_seconds
                else "—"
            )
            cs_min = "—" if match.cs_per_min is None else f"{match.cs_per_min:.1f}"
            values = [
                match.champion,
                "Victory" if match.result == "WIN" else "Defeat",
                match.kda_text,
                cs_min,
                duration,
                match.played_at,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(256, match.match_id)
                self.table.setItem(row, column, item)

        self.table.resizeColumnsToContents()

    def _open_row(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return
        match_id = item.data(256)
        if match_id:
            self.open_match.emit(str(match_id))
