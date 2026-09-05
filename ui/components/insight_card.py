from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QWidget

from services.asset_service import AssetService
from ui.components.asset_icon import AssetIcon
from ui.components.status_badge import SeverityBadge, StatusBadge
from viewmodels import InsightViewModel


class InsightCard(QFrame):
    """Concise analyzer support card used by the Overview."""

    def __init__(self, insight: InsightViewModel, parent=None):
        super().__init__(parent)
        self.setObjectName("InsightCard")
        layout = QVBoxLayout(self); layout.setContentsMargins(16, 13, 16, 13); layout.setSpacing(7)
        head = QHBoxLayout(); title = QLabel(insight.title); title.setObjectName("SectionTitle")
        head.addWidget(title); head.addStretch(); head.addWidget(StatusBadge(insight.status)); layout.addLayout(head)
        summary = QLabel(insight.summary); summary.setWordWrap(True); summary.setObjectName("Muted"); layout.addWidget(summary)
        source = QLabel(f"Source : {insight.source_version or insight.source_module}"); source.setObjectName("MicroLabel"); layout.addWidget(source)


class AnalyzerEventCard(QFrame):
    """Structured event/phase projection; raw keys remain behind details."""

    def __init__(self, event: dict, assets: AssetService, game_version: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("EventCard")
        root = QVBoxLayout(self); root.setContentsMargins(15, 13, 15, 13); root.setSpacing(8)
        head = QHBoxLayout(); title_box = QVBoxLayout()
        title = QLabel(str(event.get("title") or "Événement")); title.setObjectName("EventTitle"); title_box.addWidget(title)
        subtitle = QLabel(str(event.get("subtitle") or "")); subtitle.setObjectName("Muted"); subtitle.setWordWrap(True); title_box.addWidget(subtitle)
        head.addLayout(title_box, 1); severity = str(event.get("severity") or "INFO")
        if severity != "INFO": head.addWidget(SeverityBadge(severity))
        head.addWidget(StatusBadge(str(event.get("status") or "UNKNOWN"))); root.addLayout(head)

        item_ids = [value for value in event.get("item_ids") or [] if value]
        if item_ids:
            strip = QHBoxLayout(); strip.setSpacing(5)
            for item_id in item_ids:
                icon = AssetIcon(assets, 32); icon.load("item", item_id, game_version); strip.addWidget(icon)
            strip.addStretch(); root.addLayout(strip)

        metrics = [value for value in event.get("metrics") or [] if isinstance(value, dict)]
        if metrics:
            grid = QGridLayout(); grid.setHorizontalSpacing(18); grid.setVerticalSpacing(6)
            for index, metric in enumerate(metrics):
                row, column = divmod(index, 2)
                cell = QWidget(); box = QVBoxLayout(cell); box.setContentsMargins(0, 0, 0, 0); box.setSpacing(1)
                label = QLabel(str(metric.get("label") or "")); label.setObjectName("MicroLabel")
                value = QLabel(str(metric.get("value") if metric.get("value") is not None else "—")); value.setObjectName("MetricValue"); value.setWordWrap(True)
                box.addWidget(label); box.addWidget(value); grid.addWidget(cell, row, column)
            root.addLayout(grid)

        for value in event.get("context") or []:
            context = QLabel(f"• {value}"); context.setObjectName("ContextLine"); context.setWordWrap(True); root.addWidget(context)

        technical = [str(value) for value in event.get("technical") or []]
        if technical:
            button = QToolButton(); button.setText("Détails techniques"); button.setCheckable(True)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            button.setArrowType(Qt.ArrowType.RightArrow); root.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
            details = QLabel("\n".join(technical)); details.setObjectName("TechnicalDetails"); details.setWordWrap(True); details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse); details.setVisible(False); root.addWidget(details)
            button.toggled.connect(details.setVisible)
            button.toggled.connect(lambda checked, target=button: target.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow))
