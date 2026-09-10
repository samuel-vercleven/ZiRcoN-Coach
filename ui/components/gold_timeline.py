from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class GoldTimeline(QWidget):
    """Small, factual team-gold-delta chart for a completed local match."""
    def __init__(self, parent=None):
        super().__init__(parent); self.points = []; self.setMinimumHeight(190)

    def set_points(self, points):
        self.points = list(points or []); self.update()

    def paintEvent(self, _event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor('#101a26')); margin = 28
        values = [point['delta'] for point in self.points if isinstance(point.get('delta'), (int, float))]
        if len(values) < 2:
            painter.setPen(QColor('#8491a3')); painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Timeline locale indisponible'); return
        maximum = max(500, max(abs(value) for value in values)); width, height = self.width() - margin * 2, self.height() - margin * 2
        zero = margin + height / 2
        painter.setPen(QPen(QColor('#314258'), 1)); painter.drawLine(margin, int(zero), margin + width, int(zero))
        painter.setPen(QColor('#8491a3')); painter.drawText(margin, margin - 8, f'+{maximum:,.0f} or'.replace(',', ' ')); painter.drawText(margin, self.height() - 5, f'-{maximum:,.0f} or'.replace(',', ' '))
        path = []
        for index, point in enumerate(self.points):
            delta = point.get('delta')
            if not isinstance(delta, (int, float)): continue
            path.append(QPointF(margin + index * width / max(1, len(self.points) - 1), zero - delta / maximum * height / 2))
        painter.setPen(QPen(QColor('#58d0b4'), 2.5))
        for first, second in zip(path, path[1:]): painter.drawLine(first, second)
        painter.setPen(QColor('#8491a3')); painter.drawText(margin, self.height() - 5, 'Début'); painter.drawText(self.width() - margin - 25, self.height() - 5, 'Fin')
