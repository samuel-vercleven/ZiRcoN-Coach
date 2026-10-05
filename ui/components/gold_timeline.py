import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QToolTip, QWidget


class GoldTimeline(QWidget):
    """Factual, timestamp-scaled team gold chart with a selected event clock."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []
        self.focus_timestamp = None
        self.setMinimumHeight(220)
        self.setMouseTracking(True)
        self.setAccessibleName("Écart d’or entre les équipes selon le temps de partie")

    def set_points(self, points):
        self.points = list(points or [])
        self.update()

    def set_focus(self, timestamp_seconds):
        self.focus_timestamp = None if timestamp_seconds is None else max(0, int(timestamp_seconds))
        self.update()

    def _plot(self):
        return QRectF(76, 28, max(1, self.width() - 96), max(1, self.height() - 62))

    def _duration(self):
        return max((float(p.get('timestamp') or 0) / 1000 for p in self.points), default=0)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor('#101a26'))
        available = [p for p in self.points if isinstance(p.get('delta'), (int, float))]
        duration = self._duration()
        if len(available) < 2 or duration <= 0:
            painter.setPen(QColor('#91a5bb'))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Évolution de l’or indisponible')
            return
        plot = self._plot()
        maximum = max(1000, math.ceil(max(abs(p['delta']) for p in available) / 1000) * 1000)
        for value in (maximum, 0, -maximum):
            y = plot.center().y() - value / maximum * plot.height() / 2
            painter.setPen(QPen(QColor('#40536a' if value == 0 else '#23374b'), 1))
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setPen(QColor('#a4b6c9'))
            label = ('+' if value > 0 else '') + f'{value:,}'.replace(',', ' ') + ' PO'
            painter.drawText(QRectF(0, y - 10, 68, 20), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)
        previous = None
        for point in self.points:
            delta = point.get('delta')
            if not isinstance(delta, (int, float)):
                previous = None
                continue
            current = QPointF(plot.left() + float(point.get('timestamp') or 0) / 1000 / duration * plot.width(),
                              plot.center().y() - delta / maximum * plot.height() / 2)
            if previous is not None:
                painter.setPen(QPen(QColor('#58d0b4'), 2.5))
                painter.drawLine(previous, current)
            previous = current
        painter.setPen(QColor('#a4b6c9'))
        for ratio in (0, .25, .5, .75, 1):
            seconds = round(duration * ratio)
            x = plot.left() + ratio * plot.width()
            painter.drawText(QRectF(x - 26, plot.bottom() + 9, 52, 20), Qt.AlignmentFlag.AlignCenter,
                             f'{seconds // 60:02d}:{seconds % 60:02d}')
        if self.focus_timestamp is not None:
            x = plot.left() + min(1, self.focus_timestamp / duration) * plot.width()
            painter.setPen(QPen(QColor('#f2c66d'), 2, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
            painter.drawText(QRectF(min(max(x - 30, plot.left()), plot.right() - 60), 2, 60, 22),
                             Qt.AlignmentFlag.AlignCenter, f'{self.focus_timestamp // 60:02d}:{self.focus_timestamp % 60:02d}')

    def mouseMoveEvent(self, event):
        duration = self._duration()
        plot = self._plot()
        available = [p for p in self.points if isinstance(p.get('delta'), (int, float))]
        if not available or duration <= 0 or not plot.contains(event.position()):
            QToolTip.hideText()
            return
        requested = (event.position().x() - plot.left()) / plot.width() * duration
        point = min(available, key=lambda p: abs(float(p.get('timestamp') or 0) / 1000 - requested))
        seconds = int(float(point.get('timestamp') or 0) / 1000)
        delta = point['delta']
        team = 'Ton équipe' if delta >= 0 else 'Équipe adverse'
        QToolTip.showText(event.globalPosition().toPoint(), f"Relevé {seconds // 60:02d}:{seconds % 60:02d}\n{team} : {abs(delta):,.0f} PO d’avance".replace(',', ' '), self)

    def leaveEvent(self, event):
        QToolTip.hideText()
        super().leaveEvent(event)
