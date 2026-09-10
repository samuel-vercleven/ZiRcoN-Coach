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
        layout = QVBoxLayout(self); layout.setContentsMargins(16, 14, 16, 14); layout.setSpacing(9)
        head = QHBoxLayout(); marker = QLabel(_insight_marker(insight.category)); marker.setObjectName('InsightMarker'); head.addWidget(marker)
        title = QLabel(insight.title); title.setObjectName("SectionTitle"); head.addWidget(title); head.addStretch(); head.addWidget(StatusBadge(insight.status)); layout.addLayout(head)
        summary = QLabel(insight.summary); summary.setWordWrap(True); summary.setObjectName("Muted"); layout.addWidget(summary)
        facts = QHBoxLayout(); events = QLabel(f"{len(insight.events)} événement(s)"); events.setObjectName('InsightFact'); facts.addWidget(events)
        findings = QLabel(f"{len(insight.findings)} point(s) coach"); findings.setObjectName('InsightFact'); facts.addWidget(findings); facts.addStretch(); layout.addLayout(facts)
        source = QLabel(f"Source · {insight.source_version or insight.source_module}"); source.setObjectName("MicroLabel"); layout.addWidget(source)


class AnalyzerEventCard(QFrame):
    """Structured event/phase projection; raw keys remain behind details."""

    def __init__(self, event: dict, assets: AssetService, game_version: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("EventCard")
        root = QVBoxLayout(self); root.setContentsMargins(16, 14, 16, 14); root.setSpacing(10)
        head = QHBoxLayout(); glyph = QLabel('●'); glyph.setObjectName('EventMarker'); head.addWidget(glyph); title_box = QVBoxLayout()
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
            grid = QGridLayout(); grid.setHorizontalSpacing(8); grid.setVerticalSpacing(8)
            for index, metric in enumerate(metrics):
                row, column = divmod(index, 3)
                cell = QFrame(); cell.setObjectName('MetricTile'); box = QVBoxLayout(cell); box.setContentsMargins(10, 8, 10, 8); box.setSpacing(3)
                label = QLabel(str(metric.get("label") or "")); label.setObjectName("MicroLabel")
                value = QLabel(str(metric.get("value") if metric.get("value") is not None else "—")); value.setObjectName("MetricValue"); value.setWordWrap(True)
                box.addWidget(label); box.addWidget(value); grid.addWidget(cell, row, column)
            root.addLayout(grid)

        context_values = [str(value) for value in event.get("context") or []]
        if context_values:
            context_title = QLabel('Observations'); context_title.setObjectName('CardTitle'); root.addWidget(context_title)
            for value in context_values[:2]:
                context = QLabel(value); context.setObjectName("ContextLine"); context.setWordWrap(True); root.addWidget(context)
            if len(context_values) > 2:
                extra_button = QToolButton(); extra_button.setText(f"Voir {len(context_values) - 2} observation(s) supplémentaire(s)"); extra_button.setCheckable(True)
                extra_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon); extra_button.setArrowType(Qt.ArrowType.RightArrow); root.addWidget(extra_button, 0, Qt.AlignmentFlag.AlignLeft)
                extra = QLabel('\n'.join('• ' + value for value in context_values[2:])); extra.setObjectName('TechnicalDetails'); extra.setWordWrap(True); extra.setVisible(False); root.addWidget(extra)
                extra_button.toggled.connect(extra.setVisible)
                extra_button.toggled.connect(lambda checked, target=extra_button: target.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow))

        technical = [str(value) for value in event.get("technical") or []]
        if technical:
            button = QToolButton(); button.setText("Détails techniques"); button.setCheckable(True)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            button.setArrowType(Qt.ArrowType.RightArrow); root.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
            details = QLabel("\n".join(technical)); details.setObjectName("TechnicalDetails"); details.setWordWrap(True); details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse); details.setVisible(False); root.addWidget(details)
            button.toggled.connect(details.setVisible)
            button.toggled.connect(lambda checked, target=button: target.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow))


def _insight_marker(category: str) -> str:
    return {'DEATH': '✕', 'TEMPO': '↗', 'OBJECTIVES': '◆', 'RESETS': '↺', 'BUILD': '▣'}.get(category, '●')
