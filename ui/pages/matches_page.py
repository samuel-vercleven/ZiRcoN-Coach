from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.local_data import LocalDataService


class MatchesPage(QWidget):
    open_match = Signal(str)

    def __init__(self, service: LocalDataService, parent=None) -> None:
        super().__init__(parent)
        self._service = service

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(16)

        title_row = QHBoxLayout()

        title = QLabel("Matches")
        title.setObjectName("PageTitle")
        title_row.addWidget(title)
        title_row.addStretch(1)

        self.filter_box = QComboBox()
        self.filter_box.addItem("All", "ALL")
        self.filter_box.addItem("Wins", "WIN")
        self.filter_box.addItem("Losses", "LOSS")
        self.filter_box.currentIndexChanged.connect(self.refresh)
        title_row.addWidget(self.filter_box)

        root.addLayout(title_row)

        self.status_label = QLabel("")
        self.status_label.setObjectName("Muted")
        root.addWidget(self.status_label)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            [
                "Champion",
                "Result",
                "K / D / A",
                "KDA",
                "CS",
                "CS/min",
                "Duration",
                "Played",
            ]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.cellDoubleClicked.connect(self._open_row)
        self.table.horizontalHeader().setStretchLastSection(True)

        root.addWidget(self.table, 1)
        self.refresh()

    def refresh(self) -> None:
        result_filter = self.filter_box.currentData() or "ALL"

        try:
            matches = self._service.matches(str(result_filter))
        except Exception as exc:
            self.status_label.setText(f"Local data unavailable: {exc}")
            self.table.setRowCount(0)
            return

        self.status_label.setText(f"{len(matches)} local match(es)")
        self.table.setRowCount(len(matches))

        for row, match in enumerate(matches):
            deaths = max(1, match.deaths)
            kda = (match.kills + match.assists) / deaths
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
                f"{kda:.2f}",
                str(match.cs),
                cs_min,
                duration,
                match.played_at,
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
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
