from __future__ import annotations

from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.local_data import LocalDataService
from ui.components.stat_card import StatCard


class ProgressPage(QWidget):
    def __init__(self, service: LocalDataService, parent=None) -> None:
        super().__init__(parent)
        self._service = service

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(16)

        title = QLabel("Progress")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        cards = QGridLayout()
        self.winrate = StatCard("Win rate")
        self.kda = StatCard("KDA")
        self.cs = StatCard("CS / min")
        self.deaths = StatCard("Deaths / match")

        cards.addWidget(self.winrate, 0, 0)
        cards.addWidget(self.kda, 0, 1)
        cards.addWidget(self.cs, 0, 2)
        cards.addWidget(self.deaths, 0, 3)
        root.addLayout(cards)

        self.comparison = QLabel("")
        self.comparison.setWordWrap(True)
        self.comparison.setObjectName("Muted")
        root.addWidget(self.comparison)

        pool_title = QLabel("Champion pool")
        pool_title.setStyleSheet("font-size: 17px; font-weight: 700;")
        root.addWidget(pool_title)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Champion", "Games", "Wins", "Win rate", "KDA", "CS/min"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

        self.refresh()

    def refresh(self) -> None:
        try:
            data = self._service.progress()
        except Exception as exc:
            self.comparison.setText(f"Local data unavailable: {exc}")
            self.table.setRowCount(0)
            return

        self.winrate.set_value("—" if data.win_rate is None else f"{data.win_rate:.1f}%")
        self.kda.set_value("—" if data.kda is None else f"{data.kda:.2f}")
        self.cs.set_value("—" if data.cs_per_min is None else f"{data.cs_per_min:.2f}")
        self.deaths.set_value(
            "—" if data.deaths_per_match is None else f"{data.deaths_per_match:.2f}"
        )
        self.comparison.setText(data.recent_comparison)

        rows = list(data.champion_rows)
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("champion", "Unknown"),
                str(row.get("games", 0)),
                str(row.get("wins", 0)),
                f"{float(row.get('win_rate', 0)):.1f}%",
                f"{float(row.get('kda', 0)):.2f}",
                f"{float(row.get('cs_per_min', 0)):.2f}",
            ]
            for column, value in enumerate(values):
                self.table.setItem(row_index, column, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()
