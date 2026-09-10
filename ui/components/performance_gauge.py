from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class PerformanceGauge(QWidget):
    """Purely presentational KDA gauge; it never claims a gameplay grade."""
    def __init__(self, parent=None):
        super().__init__(parent); self.value = None; self.setFixedSize(112, 112)

    def set_value(self, value):
        self.value = value; self.update()

    def paintEvent(self, _event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(10, 10, -10, -10)
        painter.setPen(QPen(QColor('#244153'), 8)); painter.drawArc(rect, 0, 5760)
        if self.value is not None:
            # The fill only gives visual prominence to the displayed KDA. It
            # is intentionally capped and not labeled a performance score.
            span = min(1.0, max(0.0, float(self.value) / 5.0))
            painter.setPen(QPen(QColor('#2de0bd'), 8)); painter.drawArc(rect, 90 * 16, int(-span * 360 * 16))
        painter.setPen(QColor('#f3f8fc')); font = QFont(); font.setPointSize(18); font.setBold(True); painter.setFont(font)
        painter.drawText(self.rect().adjusted(0, -9, 0, 0), Qt.AlignmentFlag.AlignCenter, '—' if self.value is None else f'{self.value:.1f}')
        painter.setPen(QColor('#8da0b5')); font.setPointSize(9); font.setBold(False); painter.setFont(font)
        painter.drawText(self.rect().adjusted(0, 28, 0, 0), Qt.AlignmentFlag.AlignCenter, 'KDA')
