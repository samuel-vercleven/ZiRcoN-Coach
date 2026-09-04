from PySide6.QtWidgets import QLabel


class StatusBadge(QLabel):
    def __init__(self, text: str = "UNKNOWN", parent=None):
        super().__init__(text, parent)
        self.setObjectName("StatusBadge")
        self.set_status(text)

    def set_status(self, status: str) -> None:
        self.setText(status.replace("_", " "))
        tone = "green" if status in ("AVAILABLE", "VALID", "COMPLETE", "EXACT", "RESOLVED") else "amber" if status in ("PARTIAL", "UNKNOWN", "CONFIGURED_UNVALIDATED") else "red" if status in ("ERROR", "FAILED", "UNAUTHORIZED_OR_EXPIRED", "FORBIDDEN") else "slate"
        self.setProperty("tone", tone)
        self.style().unpolish(self)
        self.style().polish(self)
