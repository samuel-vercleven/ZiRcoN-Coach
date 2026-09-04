from __future__ import annotations

import os

from PySide6.QtCore import QSize, Qt, QThreadPool, QTimer
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QLabel

from services.asset_service import AssetService
from ui.workers import FunctionWorker


class AssetIcon(QLabel):
    _active_workers = set()
    def __init__(self, assets: AssetService, size: int = 46, parent=None):
        super().__init__(parent)
        self.assets, self.icon_size = assets, size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("AssetIcon")
        self._worker = None
        self.set_placeholder("?")

    def sizeHint(self) -> QSize:
        return QSize(self.icon_size, self.icon_size)

    def set_placeholder(self, text: str) -> None:
        pixmap = QPixmap(self.icon_size, self.icon_size)
        pixmap.fill(QColor("#202a38"))
        painter = QPainter(pixmap)
        painter.setPen(QColor("#91a0b5"))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, (text or "?")[:2].upper())
        painter.end()
        self.setPixmap(pixmap)

    def load(self, kind: str, identity, game_version: str = "", fallback: str = "?") -> None:
        self.set_placeholder(fallback)
        if not identity:
            return
        if os.getenv("QT_QPA_PLATFORM", "").lower() == "offscreen":
            self._set_data(self.assets.load_cached(kind, identity, game_version))
            return
        worker = FunctionWorker(self.assets.load, kind, identity, game_version)
        worker.setAutoDelete(False)
        worker.signals.result.connect(self._set_data)
        self._active_workers.add(worker)
        worker.signals.finished.connect(lambda current=worker: QTimer.singleShot(0, lambda: self._active_workers.discard(current)))
        self._worker = worker
        QThreadPool.globalInstance().start(worker)

    def _set_data(self, data) -> None:
        if not data:
            return
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self.setPixmap(pixmap.scaled(self.icon_size, self.icon_size,
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
