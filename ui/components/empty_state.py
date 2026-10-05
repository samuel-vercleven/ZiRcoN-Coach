from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class EmptyState(QWidget):
    def __init__(self, title: str, message: str, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 28, 20, 28)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-size: 18px; font-weight: 700;")

        message_label = QLabel(message)
        message_label.setObjectName("Muted")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setMinimumHeight(message_label.fontMetrics().lineSpacing() * 3)

        layout.addWidget(title_label)
        layout.addWidget(message_label)
