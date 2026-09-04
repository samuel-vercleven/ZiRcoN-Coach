from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from services.local_data import LocalDataService


class MatchDetailPage(QWidget):
    back_requested = Signal()

    def __init__(self, service: LocalDataService, parent=None) -> None:
        super().__init__(parent)
        self._service = service
        self._match_id: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(14)

        top = QHBoxLayout()
        back = QPushButton("← Back to matches")
        back.clicked.connect(self.back_requested.emit)
        top.addWidget(back)
        top.addStretch(1)
        root.addLayout(top)

        self.title = QLabel("Match detail")
        self.title.setObjectName("PageTitle")
        root.addWidget(self.title)

        self.summary = QLabel("Select a match.")
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)

        self.items = QLabel("")
        self.items.setObjectName("Muted")
        root.addWidget(self.items)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 8, 0, 8)
        self.content_layout.setSpacing(12)

        self.analysis_card = QFrame()
        self.analysis_card.setObjectName("Card")
        card_layout = QVBoxLayout(self.analysis_card)
        card_layout.setContentsMargins(16, 14, 16, 14)

        analysis_title = QLabel("Post-game coaching")
        analysis_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        card_layout.addWidget(analysis_title)

        self.analysis_text = QLabel(
            "Analyzer integration has not been connected to the Alpha UI yet. "
            "This page currently shows only exact local match facts."
        )
        self.analysis_text.setWordWrap(True)
        self.analysis_text.setObjectName("Muted")
        card_layout.addWidget(self.analysis_text)

        self.content_layout.addWidget(self.analysis_card)
        self.content_layout.addStretch(1)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def load_match(self, match_id: str) -> None:
        self._match_id = match_id

        try:
            detail = self._service.match_detail(match_id)
        except Exception as exc:
            self.title.setText("Match detail")
            self.summary.setText(f"Unable to load local match: {exc}")
            self.items.setText("")
            return

        if detail is None:
            self.title.setText("Match detail")
            self.summary.setText("Match not found in the local database.")
            self.items.setText("")
            return

        match = detail.match
        result = "VICTORY" if match.result == "WIN" else "DEFEAT"

        self.title.setText(f"{match.champion} — {result}")
        self.summary.setText(
            f"{match.kda_text}  •  {match.cs} CS  •  "
            f"{match.queue}  •  {match.played_at}"
        )
        self.items.setText(
            "Items: " + (", ".join(str(item) for item in detail.items) if detail.items else "Unavailable")
        )
