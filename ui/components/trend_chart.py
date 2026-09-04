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
        if len(self.values) < 2:
            painter.setPen(QColor("#7f8b9e"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Not enough data")
            return
        margin = 12
        low, high = min(self.values), max(self.values)
        span = max(0.001, high - low)
        width, height = self.width() - margin * 2, self.height() - margin * 2
        points = [QPointF(margin + index * width / (len(self.values) - 1),
                         margin + height - (value - low) / span * height)
                  for index, value in enumerate(self.values)]
        painter.setPen(QPen(self.color, 2))
        for first, second in zip(points, points[1:]):
            painter.drawLine(first, second)
