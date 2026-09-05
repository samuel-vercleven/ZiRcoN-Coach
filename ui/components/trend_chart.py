from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class TrendChart(QWidget):
    def __init__(self, values=None, color="#55d6be", parent=None):
        super().__init__(parent)
        self.values = list(values or [])
        self.color = QColor(color)
        self.setMinimumHeight(100)

    def set_values(self, values):
        self.values = list(values)
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#151b25"))
        available = [float(value) for value in self.values if value is not None]
        if len(available) < 2:
            painter.setPen(QColor("#7f8b9e"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Données insuffisantes")
            return
        margin = 12
        low, high = min(available), max(available)
        span = max(0.001, high - low)
        width, height = self.width() - margin * 2, self.height() - margin * 2
        painter.setPen(QPen(QColor("#263142"), 1))
        painter.drawLine(margin, margin + height // 2, margin + width, margin + height // 2)
        points = [None if value is None else QPointF(
            margin + index * width / max(1, len(self.values) - 1),
            margin + height - (float(value) - low) / span * height,
        ) for index, value in enumerate(self.values)]
        painter.setPen(QPen(self.color, 2))
        for first, second in zip(points, points[1:]):
            if first is not None and second is not None:
                painter.drawLine(first, second)
        painter.setPen(QColor("#7f8b9e"))
        painter.drawText(margin, margin + 9, f"{high:.1f}")
        painter.drawText(margin, margin + height, f"{low:.1f}")
