from PySide6.QtWidgets import QLabel


class StatusBadge(QLabel):
    def __init__(self, text: str = "UNKNOWN", parent=None):
        super().__init__(text, parent)
        self.setObjectName("StatusBadge")
        self.set_status(text)

    def set_status(self, status: str) -> None:
        self.setText(status.replace("_", " "))
        # Epistemic/data support is deliberately neutral, never gameplay-green.
        tone = "support" if status in ("AVAILABLE", "VALID", "COMPLETE", "EXACT", "RESOLVED", "CURRENT") else "amber" if status in ("PARTIAL", "UNKNOWN", "CONFIGURED_UNVALIDATED", "CACHED") else "red" if status in ("ERROR", "FAILED", "UNAUTHORIZED_OR_EXPIRED", "FORBIDDEN") else "slate"
        self.setProperty("tone", tone)
        self.style().unpolish(self)
        self.style().polish(self)


class SeverityBadge(QLabel):
    def __init__(self, severity: str = "INFO", parent=None):
        super().__init__(parent)
        self.setObjectName("SeverityBadge")
        self.set_severity(severity)

    def set_severity(self, severity: str) -> None:
        labels = {"HIGH": "Impact élevé", "MEDIUM": "À surveiller", "LOW": "Impact faible", "INFO": "Contexte"}
        self.setText(labels.get(severity, severity.replace("_", " ")))
        self.setProperty("tone", severity.lower())
        self.style().unpolish(self)
        self.style().polish(self)
