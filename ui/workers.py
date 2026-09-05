from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    progress = Signal(str, int)
    finished = Signal()


class FunctionWorker(QRunnable):
    def __init__(self, function, *args, with_progress: bool = False, **kwargs):
        super().__init__()
        self.function, self.args, self.kwargs = function, args, kwargs
        self.with_progress = with_progress
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            if self.with_progress:
                result = self.function(*self.args, progress=lambda message, value: self._emit(self.signals.progress, message, value), **self.kwargs)
            else:
                result = self.function(*self.args, **self.kwargs)
            self._emit(self.signals.result, result)
        except Exception:
            self._emit(self.signals.error, "L’opération en arrière-plan a échoué. Les données locales sont inchangées.")
        finally:
            self._emit(self.signals.finished)

    @staticmethod
    def _emit(signal, *values):
        # The receiver graph can legitimately disappear while an asset worker
        # finishes during application shutdown.
        try:
            signal.emit(*values)
        except RuntimeError:
            return
