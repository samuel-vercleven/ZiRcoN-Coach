from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QTabWidget, QVBoxLayout, QWidget

from services.asset_service import AssetService
from services.local_data import LocalDataService
from services.post_game_analysis import PostGameAnalysisService
from ui.components.asset_icon import AssetIcon
from ui.components.empty_state import EmptyState
from ui.components.insight_card import AnalyzerEventCard, InsightCard
from ui.components.status_badge import SeverityBadge, StatusBadge
from viewmodels import CoachingReport


def coach_summary_lines(report: CoachingReport) -> tuple[str, ...]:
    """Select only explicit supported findings; never rank by evidence volume."""
    priority = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    candidates = []
    for analyzer_index, insight in enumerate(report.insights):
        if insight.status not in ("AVAILABLE", "PARTIAL"):
            continue
        for finding_index, finding in enumerate(insight.findings):
            if finding.get("supported") is True:
                candidates.append((priority.get(str(finding.get("severity") or "INFO"), 9), analyzer_index, finding_index, finding))
    candidates.sort(key=lambda value: value[:3])
    return tuple(f"{value[3].get('title')}: {value[3].get('detail')}" for value in candidates[:4])


def coach_summary_empty_message(report: CoachingReport) -> str:
    if any(value.status != "AVAILABLE" for value in report.insights):
        return "Synthèse limitée : certaines analyses compatibles sont absentes, partielles ou en erreur. Aucun diagnostic d’absence de problème n’est déduit."
    return "Aucun finding de gameplay explicitement supporté n’émerge des cinq sorties disponibles. Les mesures factuelles restent consultables ci-dessous."


class MatchDetailPage(QWidget):
    back_requested = Signal()

    def __init__(self, service: LocalDataService, analysis: PostGameAnalysisService, assets: AssetService, parent=None):
        super().__init__(parent)
        self.service, self.analysis, self.assets = service, analysis, assets
        root = QVBoxLayout(self); root.setContentsMargins(26, 16, 26, 20); root.setSpacing(10)
        back = QPushButton("← Historique"); back.setObjectName("BackButton"); back.clicked.connect(self.back_requested); root.addWidget(back)
        self.host = QWidget(); self.content = QVBoxLayout(self.host); self.content.setContentsMargins(0, 0, 0, 0); self.content.setSpacing(10); root.addWidget(self.host, 1)
        self.load_empty()

    def _clear(self):
        while self.content.count():
            item = self.content.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide(); widget.setParent(None); widget.deleteLater()

    def load_empty(self):
        self._clear(); self.content.addWidget(EmptyState("Sélectionnez une partie", "Ouvrez une partie depuis l’historique.")); self.content.addStretch()

    def _scroll_panel(self, builder) -> QScrollArea:
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        host = QWidget(); layout = QVBoxLayout(host); layout.setContentsMargins(4, 12, 8, 8); layout.setSpacing(9)
        builder(layout); layout.addStretch(); scroll.setWidget(host); return scroll

    def load_match(self, match_id: str):
        self._clear()
        try:
            detail = self.service.match_detail(match_id)
        except Exception:
            detail = None
        if not detail:
            self.content.addWidget(EmptyState("Partie indisponible", "La ligne locale n’a pas pu être chargée.")); return
        match = detail.match
        hero = QFrame(); hero.setObjectName("HeroCard"); row = QHBoxLayout(hero); row.setContentsMargins(18, 13, 18, 13)
        icon = AssetIcon(self.assets, 66); icon.load("champion", match.champion, match.game_version, match.champion); row.addWidget(icon)
        title_box = QVBoxLayout(); title = QLabel(f"{match.champion}  •  {'VICTOIRE' if match.result == 'WIN' else 'DÉFAITE'}"); title.setObjectName("HeroName"); title.setProperty("result", match.result.lower()); title_box.addWidget(title)
        cs = "—" if match.cs_per_min is None else f"{match.cs_per_min:.1f}/min"
        subtitle = QLabel(f"{match.position}  •  {match.kda_text}  •  {match.cs} CS ({cs})  •  {match.duration_seconds // 60}:{match.duration_seconds % 60:02d}  •  {match.played_at}"); subtitle.setObjectName("Muted"); title_box.addWidget(subtitle)
        items = QHBoxLayout(); items.setSpacing(5)
        inventory = list(detail.items)
        if match.trinket_id in inventory: inventory.remove(match.trinket_id)
        for item_id in inventory[:6]:
            item = AssetIcon(self.assets, 32); item.load("item", item_id, match.game_version); items.addWidget(item)
        if match.trinket_id:
            items.addSpacing(8); item = AssetIcon(self.assets, 32); item.load("item", match.trinket_id, match.game_version); items.addWidget(item)
        items.addStretch(); title_box.addLayout(items); row.addLayout(title_box, 1)
        report = self.analysis.get_match_insights(match_id); row.addWidget(StatusBadge(report.status)); self.content.addWidget(hero)

        summary_card = QFrame(); summary_card.setObjectName("CoachCard"); summary_layout = QVBoxLayout(summary_card); summary_layout.setContentsMargins(15, 11, 15, 11); summary_layout.setSpacing(5)
        summary_title = QLabel("Synthèse coach"); summary_title.setObjectName("SectionTitle"); summary_layout.addWidget(summary_title)
        lines = coach_summary_lines(report)
        if lines:
            for line in lines:
                label = QLabel(f"• {line}"); label.setWordWrap(True); label.setObjectName("ContextLine"); summary_layout.addWidget(label)
        else:
            label = QLabel(coach_summary_empty_message(report))
            label.setWordWrap(True); label.setObjectName("Muted"); summary_layout.addWidget(label)
        boundary = QLabel("Les statuts décrivent le support des données ; la sévérité gameplay est affichée séparément."); boundary.setObjectName("MicroLabel"); summary_layout.addWidget(boundary)
        self.content.addWidget(summary_card)

        tabs = QTabWidget(); self.tabs = tabs
        def overview(layout):
            for insight in report.insights:
                layout.addWidget(InsightCard(insight))
        tabs.addTab(self._scroll_panel(overview), "Vue d’ensemble")
        for insight in report.insights:
            def build(layout, current=insight):
                header = QFrame(); header.setObjectName("AnalyzerHeader"); h = QVBoxLayout(header); h.setContentsMargins(14, 11, 14, 11)
                top = QHBoxLayout(); name = QLabel(current.title); name.setObjectName("SectionTitle"); top.addWidget(name); top.addStretch(); top.addWidget(StatusBadge(current.status)); h.addLayout(top)
                summary = QLabel(current.summary); summary.setWordWrap(True); summary.setObjectName("Muted"); h.addWidget(summary); layout.addWidget(header)
                if current.events:
                    for event in current.events:
                        layout.addWidget(AnalyzerEventCard(event, self.assets, match.game_version))
                else:
                    layout.addWidget(EmptyState("Aucun événement structuré", current.summary))
                if current.technical_details:
                    layout.addWidget(AnalyzerEventCard({"title": "Journal technique", "subtitle": "Événements bruts de reconstruction", "status": current.status, "metrics": [], "context": [], "technical": list(current.technical_details)}, self.assets, match.game_version))
            tabs.addTab(self._scroll_panel(build), insight.title)
        self.content.addWidget(tabs, 1)
