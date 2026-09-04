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
                result = self.function(*self.args, progress=self.signals.progress.emit, **self.kwargs)
            else:
                result = self.function(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception:
            self.signals.error.emit("The background operation failed. Local data is unchanged.")
        finally:
            self.signals.finished.emit()
