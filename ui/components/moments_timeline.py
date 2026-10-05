"""Timestamp-faithful objective rail with a separate, collision-free legend."""
import math

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGridLayout, QPushButton, QToolButton, QToolTip, QVBoxLayout, QWidget


def event_clock(event):
    seconds = int(event['timestamp'] / 1000)
    return f'{seconds // 60:02d}:{seconds % 60:02d}'


def event_label(event):
    return {'DRAGON': 'Dragon', 'RIFTHERALD': 'Héraut', 'BARON_NASHOR': 'Baron',
            'HORDE': 'Larves du Néant', 'ATAKHAN': 'Atakhan'}.get(event.get('label'), event.get('label') or 'Objectif')


class _ObjectiveRail(QWidget):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setFixedHeight(76)
        self.setMouseTracking(True)
        self.setAccessibleName('Repères des objectifs regroupés lorsqu’ils sont proches')

    def groups(self):
        """Keep true marker positions; use one count badge for nearby events."""
        span = max(1, self.width() - 48)
        groups = []
        for index, event in enumerate(self.owner.events):
            x = 24 + min(1, event['timestamp'] / 1000 / self.owner.duration) * span
            if groups and x - groups[-1][0] < 36:
                groups[-1][1].append(index)
            else:
                groups.append((x, [index]))
        return groups

    def paintEvent(self, _event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor('#29455a'), 3))
        painter.drawLine(24, 27, max(24, self.width() - 24), 27)
        for x, indices in self.groups():
            painter.setPen(QPen(QColor('#5ad6bf'), 2))
            # Small ticks remain at the actual timestamps, even inside a group.
            for index in indices:
                true_x = 24 + min(1, self.owner.events[index]['timestamp'] / 1000 / self.owner.duration) * max(1, self.width() - 48)
                painter.drawLine(QPointF(true_x, 35), QPointF(true_x, 41))
            painter.setBrush(QColor('#163e47')); painter.drawEllipse(QPointF(x, 27), 14, 14)
            painter.setPen(QColor('#98f2db'))
            painter.drawText(QRectF(x - 14, 13, 28, 28), Qt.AlignmentFlag.AlignCenter,
                             str(indices[0] + 1) if len(indices) == 1 else f'×{len(indices)}')
        painter.setPen(QColor('#a4b6c9'))
        painter.drawText(QRectF(24, 50, 80, 20), Qt.AlignmentFlag.AlignLeft, 'Début')
        end = int(self.owner.duration)
        painter.drawText(QRectF(self.width() - 104, 50, 80, 20), Qt.AlignmentFlag.AlignRight,
                         f'{end // 60:02d}:{end % 60:02d}')

    def mouseMoveEvent(self, event):
        for x, indices in self.groups():
            if abs(event.position().x() - x) < 18 and abs(event.position().y() - 27) < 18:
                text = '\n'.join(f'{index + 1} · {event_clock(self.owner.events[index])} · {event_label(self.owner.events[index])}' for index in indices)
                QToolTip.showText(event.globalPosition().toPoint(), text, self)
                return
        QToolTip.hideText()

    def leaveEvent(self, event):
        QToolTip.hideText(); super().leaveEvent(event)


class MomentsTimeline(QWidget):
    moment_selected = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.events = []; self.duration = 1; self._columns = 0
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(6)
        self.rail = _ObjectiveRail(self); layout.addWidget(self.rail)
        self.legend = QGridLayout(); self.legend.setSpacing(6); layout.addLayout(self.legend)
        self.expand = QToolButton(); self.expand.setObjectName('MomentsToggle'); self.expand.setCheckable(True)
        self.expand.toggled.connect(self._layout_events); layout.addWidget(self.expand)
        self.buttons = []

    def set_data(self, events, duration):
        self.events = sorted((dict(e) for e in (events or []) if isinstance(e.get('timestamp'), (int, float))
                              and math.isfinite(e['timestamp']) and e['timestamp'] >= 0), key=lambda e: e['timestamp'])
        self.duration = max(1, float(duration or 1), max((e['timestamp'] / 1000 for e in self.events), default=1))
        for button in self.buttons: self.legend.removeWidget(button); button.hide(); button.deleteLater()
        self.buttons = []
        for index, event in enumerate(self.events):
            button = QPushButton(f'{index + 1} · {event_clock(event)}  {event_label(event)}', self)
            button.setObjectName('MomentChip'); button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setToolTip('Voir ce moment sur la courbe d’or')
            button.clicked.connect(lambda checked=False, e=event: self.moment_selected.emit(int(e['timestamp'] / 1000), event_label(e)))
            self.buttons.append(button)
        self.expand.setChecked(False); self._layout_events(); self.rail.update()
        self.setAccessibleName(f'{len(self.events)} objectifs observés' if self.events else 'Aucun objectif structuré observé')

    def _layout_events(self):
        while self.legend.count(): self.legend.takeAt(0)
        self._columns = max(1, min(3, self.width() // 220))
        for index, button in enumerate(self.buttons):
            visible = self.expand.isChecked() or index < 6
            if visible: self.legend.addWidget(button, index // self._columns, index % self._columns)
            button.setVisible(visible)
        self.expand.setVisible(len(self.events) > 6 or not self.events)
        self.expand.setEnabled(bool(self.events))
        self.expand.setText(('Réduire les repères' if self.expand.isChecked() else f'Voir les {len(self.events) - 6} autres moments')
                            if self.events else 'Aucun objectif structuré observé')
        self.rail.update(); self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._columns != max(1, min(3, self.width() // 220)): self._layout_events()
