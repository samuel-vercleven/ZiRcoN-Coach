from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from ui.components.status_badge import StatusBadge
from viewmodels import InsightViewModel


class InsightCard(QFrame):
    def __init__(self, insight: InsightViewModel, parent=None):
        super().__init__(parent)
        self.setObjectName("InsightCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        title = QLabel(insight.title); title.setObjectName("SectionTitle")
        layout.addWidget(title)
        layout.addWidget(StatusBadge(insight.status))
        summary = QLabel(insight.summary); summary.setWordWrap(True)
        layout.addWidget(summary)
        if insight.evidence:
            evidence = QLabel("\n".join(f"• {line}" for line in insight.evidence))
            evidence.setWordWrap(True); evidence.setObjectName("Evidence")
            layout.addWidget(evidence)
        source = QLabel(f"Source: {insight.source_version or insight.source_module}")
        source.setObjectName("Muted")
        layout.addWidget(source)
