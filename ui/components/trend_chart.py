import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QToolTip, QWidget


class TrendChart(QWidget):
    def __init__(self, values=None, color="#55d6be", parent=None, unit="", fixed_range=None):
        super().__init__(parent)
        self.values = list(values or [])
        self.labels = []
        self.color = QColor(color)
        self.unit = unit
        self.fixed_range = fixed_range
        self.setMinimumHeight(180)
        self.setMouseTracking(True)

    def set_values(self, values, labels=None):
        self.values = list(values)
        self.labels = list(labels or [])
        self.update()

    def _plot(self):
        return QRectF(46, 16, max(1, self.width() - 60), max(1, self.height() - 48))

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#111D2B"))
        available = [float(v) for v in self.values if v is not None]
        if len(available) < 2:
            painter.setPen(QColor("#91A5BB"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Au moins deux relevés sont nécessaires")
            return
        low, high = self.fixed_range or (min(0, min(available)), max(1, math.ceil(max(available))))
        span = max(.001, high - low)
        plot = self._plot()
        for value in (high, (low + high) / 2, low):
            y = plot.bottom() - (value - low) / span * plot.height()
            painter.setPen(QPen(QColor("#23374B"), 1))
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setPen(QColor("#a4b6c9"))
            painter.drawText(QRectF(0, y - 9, 39, 18), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                             f'{value:g}' + ('%' if self.unit == '%' else ''))
        points = [None if value is None else QPointF(
            plot.left() + index * plot.width() / max(1, len(self.values) - 1),
            plot.bottom() - (float(value) - low) / span * plot.height(),
        ) for index, value in enumerate(self.values)]
        painter.setPen(QPen(self.color, 2))
        for first, second in zip(points, points[1:]):
            if first is not None and second is not None:
                painter.drawLine(first, second)
        painter.setBrush(self.color)
        for point in points:
            if point is not None:
                painter.drawEllipse(point, 2.5, 2.5)
        painter.setPen(QColor("#a4b6c9"))
        painter.drawText(QRectF(plot.left(), plot.bottom() + 8, 95, 20), Qt.AlignmentFlag.AlignLeft, 'Plus anciennes')
        painter.drawText(QRectF(plot.right() - 95, plot.bottom() + 8, 95, 20), Qt.AlignmentFlag.AlignRight, 'Plus récentes')

    def mouseMoveEvent(self, event):
        plot = self._plot()
        if not self.values or not plot.contains(event.position()):
            QToolTip.hideText()
            return
        index = round((event.position().x() - plot.left()) / plot.width() * (len(self.values) - 1))
        value = self.values[index]
        shown = 'Information manquante' if value is None else f'{value:.1f} {self.unit}'.strip()
        label = self.labels[index] if index < len(self.labels) else f'Partie {index + 1}'
        QToolTip.showText(event.globalPosition().toPoint(), f'{label}\n{shown}', self)

    def leaveEvent(self, event):
        QToolTip.hideText()
        super().leaveEvent(event)
