from PySide6.QtWidgets import QLabel


class StatusBadge(QLabel):
    def __init__(self, text: str = "UNKNOWN", parent=None):
        super().__init__(text, parent)
        self.setObjectName("StatusBadge")
        self.set_status(text)

    def set_status(self, status: str) -> None:
        labels = {
            "AVAILABLE": "DISPONIBLE", "PARTIAL": "PARTIEL", "UNAVAILABLE": "INDISPONIBLE",
            "VALID": "VALIDE", "COMPLETE": "TERMINÉ", "CURRENT": "ACTUEL", "CACHED": "CACHE",
            "LOCAL": "LOCAL", "NOT_CONFIGURED": "NON CONFIGURÉE", "CONFIGURED_UNVALIDATED": "CONFIGURÉE · NON VALIDÉE",
            "UNAUTHORIZED_OR_EXPIRED": "NON AUTORISÉE / EXPIRÉE", "FORBIDDEN": "ACCÈS REFUSÉ",
            "RATE_LIMITED": "LIMITE ATTEINTE", "NETWORK_ERROR": "ERREUR RÉSEAU",
            "RIOT_SERVER_ERROR": "ERREUR RIOT", "ERROR": "ERREUR", "FAILED": "ÉCHEC",
            "RUNNING": "EN COURS", "OFFLINE": "HORS LIGNE", "NOT_TESTED": "NON TESTÉE", "TESTING": "TEST EN COURS",
        }
        self.setText(labels.get(status, status.replace("_", " ")))
        self.setProperty("statusCode", status)
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
