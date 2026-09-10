from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class MomentsTimeline(QWidget):
    """Horizontal factual timeline of locally observed objectives."""
    COLORS = ('#f05e74', '#e4bc57', '#9f72e6', '#42d1b6', '#54a5e8')

    def __init__(self, parent=None):
        super().__init__(parent); self.events = []; self.duration = 0; self.setMinimumHeight(128)

    def set_data(self, events, duration_seconds):
        self.events, self.duration = list(events or [])[:5], max(1, int(duration_seconds or 1)); self.update()

    def paintEvent(self, _event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing); painter.fillRect(self.rect(), QColor('#101c29'))
        left, right, axis_y = 24, self.width() - 24, 76
        painter.setPen(QPen(QColor('#29455a'), 5)); painter.drawLine(left, axis_y, right, axis_y)
        painter.setPen(QColor('#5ad6bf')); painter.drawLine(left, axis_y, right, axis_y)
        if not self.events:
            painter.setPen(QColor('#8491a3')); painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Aucun objectif structuré observé'); return
        for index, event in enumerate(self.events):
            timestamp = float(event.get('timestamp') or 0) / 1000
            x = left + min(1.0, max(0.0, timestamp / self.duration)) * (right - left)
            color = QColor(self.COLORS[index % len(self.COLORS)])
            painter.setPen(QPen(color, 2)); painter.drawLine(int(x), axis_y - 22, int(x), axis_y + 16)
            painter.setBrush(color); painter.drawEllipse(int(x) - 5, axis_y - 5, 10, 10)
            painter.setPen(QColor('#dbe6ef')); painter.drawText(int(x) - 44, 21, 88, 16, Qt.AlignmentFlag.AlignCenter, str(event.get('label') or 'Objectif'))
            painter.setPen(QColor('#8da0b5')); painter.drawText(int(x) - 44, 39, 88, 16, Qt.AlignmentFlag.AlignCenter, f'{int(timestamp // 60):02d}:{int(timestamp % 60):02d}')
        painter.setPen(QColor('#8da0b5')); painter.drawText(left, 112, 'Début'); painter.drawText(right - 30, 112, f'{self.duration // 60}:{self.duration % 60:02d}')
