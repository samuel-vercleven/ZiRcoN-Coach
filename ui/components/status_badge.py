from PySide6.QtWidgets import QLabel, QSizePolicy


class StatusBadge(QLabel):
    def __init__(self, text: str = "UNKNOWN", parent=None):
        super().__init__(text, parent)
        self.setObjectName("StatusBadge")
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.set_status(text)

    def set_status(self, status: str) -> None:
        labels = {
            "AVAILABLE": "DISPONIBLE", "PARTIAL": "À VÉRIFIER", "UNAVAILABLE": "INDISPONIBLE",
            "VALID": "CONNECTÉ", "COMPLETE": "TERMINÉ", "CURRENT": "À JOUR", "CACHED": "ENREGISTRÉ",
            "LOCAL": "SUR CET ORDINATEUR", "NOT_CONFIGURED": "CLÉ MANQUANTE", "CONFIGURED_UNVALIDATED": "À VÉRIFIER",
            "UNAUTHORIZED_OR_EXPIRED": "CLÉ À RENOUVELER", "FORBIDDEN": "ACCÈS REFUSÉ",
            "RATE_LIMITED": "TROP DE DEMANDES", "NETWORK_ERROR": "PAS DE CONNEXION",
            "RIOT_SERVER_ERROR": "SERVICE INDISPONIBLE", "ACCOUNT_NOT_FOUND": "COMPTE INTROUVABLE",
            "REVIEW_REQUIRED": "À VÉRIFIER", "ERROR": "ERREUR", "FAILED": "ÉCHEC",
            "RUNNING": "EN COURS", "OFFLINE": "HORS LIGNE", "NOT_TESTED": "NON VÉRIFIÉE", "TESTING": "VÉRIFICATION…",
            "UNKNOWN": "À VÉRIFIER",
        }
        self.setText(labels.get(status, "À VÉRIFIER"))
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
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.set_severity(severity)

    def set_severity(self, severity: str) -> None:
        labels = {"HIGH": "Impact élevé", "MEDIUM": "À surveiller", "LOW": "Impact faible", "INFO": "Contexte"}
        self.setText(labels.get(severity, severity.replace("_", " ")))
        self.setProperty("tone", severity.lower())
        self.style().unpolish(self)
        self.style().polish(self)
