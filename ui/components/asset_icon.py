from __future__ import annotations

import os

from PySide6.QtCore import QSize, Qt, QThreadPool, QTimer
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QLabel

from services.asset_service import AssetService
from ui.workers import FunctionWorker


class AssetIcon(QLabel):
    """Cache-first image with one shared background request per asset."""

    _active_workers: set[FunctionWorker] = set()
    _pending: dict[tuple[int, str, str, str], FunctionWorker] = {}

    def __init__(self, assets: AssetService, size: int = 46, parent=None):
        super().__init__(parent)
        self.assets, self.icon_size = assets, size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("AssetIcon")
        self.set_placeholder("?")

    def sizeHint(self) -> QSize:
        return QSize(self.icon_size, self.icon_size)

    def set_placeholder(self, text: str) -> None:
        pixmap = QPixmap(self.icon_size, self.icon_size)
        pixmap.fill(QColor("#152332"))
        painter = QPainter(pixmap)
        painter.setPen(QColor("#91A5BB"))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, (text or "?")[:2].upper())
        painter.end()
        self.setPixmap(pixmap)

    def load(self, kind: str, identity, game_version: str = "", fallback: str = "?") -> None:
        self.set_placeholder(fallback)
        if not identity:
            return
        cached = self.assets.load_cached(kind, identity, game_version)
        if cached:
            self._set_data(cached)
            return
        if os.getenv("QT_QPA_PLATFORM", "").lower() == "offscreen":
            return

        key = (id(self.assets), kind, str(identity), game_version)
        worker = self._pending.get(key)
        if worker is None:
            worker = FunctionWorker(self.assets.load, kind, identity, game_version)
            worker.setAutoDelete(False)
            self._pending[key] = worker
            self._active_workers.add(worker)

            def release(current=worker, request_key=key):
                QTimer.singleShot(0, lambda: self._release(request_key, current))

            worker.signals.finished.connect(release)
            QThreadPool.globalInstance().start(worker)
        worker.signals.result.connect(self._set_data)

    @classmethod
    def _release(cls, key, worker) -> None:
        if cls._pending.get(key) is worker:
            cls._pending.pop(key, None)
        cls._active_workers.discard(worker)

    def _set_data(self, data) -> None:
        if not data:
            return
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self.setPixmap(pixmap.scaled(
                self.icon_size, self.icon_size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            ))
