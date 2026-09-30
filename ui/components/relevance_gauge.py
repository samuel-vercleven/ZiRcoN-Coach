from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


def relevance_color(value: float) -> QColor:
    """Map the existing score to a color without introducing new score bands."""
    score = max(0.0, min(100.0, float(value)))
    return QColor.fromHsv(round(score * 1.5), 190, 225)


class RelevanceGauge(QWidget):
    """Visualizes the optimizer's relative heuristic score, not win probability."""

    def __init__(self, diameter: int = 76, parent=None):
        super().__init__(parent)
        self.value: float | None = None
        self.setFixedSize(diameter, diameter)
        self.setToolTip("La couleur et le remplissage reprennent le repère de comparaison de l’optimiseur ; ce n’est pas une probabilité de réussite.")

    def set_value(self, value: float | None) -> None:
        self.value = None if value is None else max(0.0, min(100.0, float(value)))
        if self.value is None:
            self.setAccessibleName("Repère d’achat indisponible")
        else:
            self.setAccessibleName(f"Repère d’achat {self.value:.0f}, estimation indicative")
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(7, 7, -7, -7)
        painter.setPen(QPen(QColor("#263c4d"), 6))
        painter.drawArc(rect, 0, 360 * 16)
        if self.value is None:
            color, shown = QColor("#8293a5"), "—"
        else:
            color = relevance_color(self.value)
            shown = f"{self.value:.0f}"
            painter.setPen(QPen(color, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(rect, 90 * 16, int(-self.value / 100.0 * 360 * 16))

        painter.setPen(QColor("#f3f8fc"))
        font = QFont()
        font.setPointSize(16 if self.width() >= 70 else 12)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, shown)
