from __future__ import annotations

from PySide6.QtCore import QThreadPool, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QTabWidget, QVBoxLayout, QWidget

from services.asset_service import AssetService
from services.local_data import LocalDataService
from services.post_game_analysis import PostGameAnalysisService
from services.build_optimizer_presentation import BuildOptimizerPresentationService
from ui.components.asset_icon import AssetIcon
from ui.components.empty_state import EmptyState
from ui.components.insight_card import AnalyzerEventCard, InsightCard
from ui.components.status_badge import SeverityBadge, StatusBadge
from ui.workers import FunctionWorker
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

    def __init__(self, service: LocalDataService, analysis: PostGameAnalysisService,
                 optimizer: BuildOptimizerPresentationService, assets: AssetService, parent=None):
        super().__init__(parent)
        self.service, self.analysis, self.optimizer, self.assets = service, analysis, optimizer, assets
        self._optimizer_worker = None; self._optimizer_match_id = None; self._optimizer_layout = None; self._optimizer_version = 0
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

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide(); widget.setParent(None); widget.deleteLater()

    def _optimizer_tab(self, tabs, match):
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        host = QWidget(); layout = QVBoxLayout(host); layout.setContentsMargins(4, 12, 8, 8); layout.setSpacing(10)
        scroll.setWidget(host); tabs.addTab(scroll, "Build Optimizer")
        self._optimizer_layout, self._optimizer_match_id = layout, match.match_id
        self._optimizer_version += 1; version = self._optimizer_version
        layout.addWidget(EmptyState("Calcul de la recommandation", "Lecture locale des frames et du catalogue exact ; aucun téléchargement n’est déclenché."))
        layout.addStretch()
        worker = FunctionWorker(self.optimizer.recommendation_for_match, match.match_id)
        worker.setAutoDelete(False)
        worker.signals.result.connect(lambda result, current=match.match_id, token=version: self._show_optimizer_result(current, token, result, match.game_version))
        worker.signals.error.connect(lambda _message, current=match.match_id, token=version: self._show_optimizer_result(
            current, token, {'status': 'UNAVAILABLE', 'reason': 'CALCUL_LOCAL_INDISPONIBLE'}, match.game_version))
        worker.signals.finished.connect(lambda current=worker: setattr(self, '_optimizer_worker', None) if self._optimizer_worker is current else None)
        self._optimizer_worker = worker; QThreadPool.globalInstance().start(worker)

    def _show_optimizer_result(self, match_id, version, result, game_version):
        if match_id != self._optimizer_match_id or version != self._optimizer_version or self._optimizer_layout is None:
            return
        layout = self._optimizer_layout; self._clear_layout(layout)
        status = result.get('status', 'UNAVAILABLE') if isinstance(result, dict) else 'UNAVAILABLE'
        if status != 'SUPPORTED_HEURISTIC':
            card = QFrame(); card.setObjectName("CoachCard"); box = QVBoxLayout(card); box.setContentsMargins(15, 12, 15, 12); box.setSpacing(6)
            heading = QHBoxLayout(); title = QLabel("Recommandation indisponible"); title.setObjectName("SectionTitle"); heading.addWidget(title); heading.addStretch(); heading.addWidget(StatusBadge("PARTIAL")); box.addLayout(heading)
            message = QLabel("ZiRcoN s’abstient : " + str(result.get('reason') or 'contexte, patch ou historique insuffisant.'))
            message.setObjectName("Muted"); message.setWordWrap(True); box.addWidget(message)
            note = QLabel("Aucune recommandation n’est inventée lorsque les données locales ne permettent pas de reconstruire un contexte fiable.")
            note.setObjectName("MicroLabel"); note.setWordWrap(True); box.addWidget(note); layout.addWidget(card); layout.addStretch(); return
        card = QFrame(); card.setObjectName("CoachCard"); box = QVBoxLayout(card); box.setContentsMargins(15, 12, 15, 12); box.setSpacing(8)
        header = QHBoxLayout(); title = QLabel("Recommandation Build Optimizer"); title.setObjectName("SectionTitle"); header.addWidget(title); header.addStretch(); header.addWidget(StatusBadge("AVAILABLE")); box.addLayout(header)
        context = QLabel(f"{result['champion']} · {result['profile']} · snapshot post-game à {result['snapshot_label']} · {result['baseline_samples']} partie(s) de référence")
        context.setObjectName("Muted"); context.setWordWrap(True); box.addWidget(context)
        choice = QHBoxLayout(); icon = AssetIcon(self.assets, 46); icon.load("item", result.get('target_item'), game_version, result.get('target_name') or '?'); choice.addWidget(icon)
        choice_text = QVBoxLayout(); item_name = QLabel(result.get('target_name') or 'Objet inconnu'); item_name.setObjectName("EventTitle"); choice_text.addWidget(item_name)
        score = QLabel(f"Score heuristique : {result.get('score', 0):.1f}/100 · si shopping maintenant")
        score.setObjectName("ContextLine"); choice_text.addWidget(score); choice.addLayout(choice_text, 1); box.addLayout(choice)
        reasons = result.get('reasons') or ()
        if reasons:
            why = QLabel("Pourquoi :"); why.setObjectName("CardTitle"); box.addWidget(why)
            for reason in reasons[:5]:
                line = QLabel("• " + str(reason)); line.setObjectName("ContextLine"); line.setWordWrap(True); box.addWidget(line)
        steps = result.get('buy_now_named') or ()
        purchase = QLabel("Acheter maintenant : " + (" → ".join(f"{step['name']} ({step['cost']} PO)" for step in steps) if steps else "Aucun achat réalisable avec le gold de cette frame."))
        purchase.setObjectName("Muted"); purchase.setWordWrap(True); box.addWidget(purchase)
        alternatives = result.get('alternatives_named') or ()
        if alternatives:
            alternatives_label = QLabel("Alternatives : " + " · ".join(f"{row['name']} ({row['score']:.1f})" for row in alternatives))
            alternatives_label.setObjectName("Muted"); alternatives_label.setWordWrap(True); box.addWidget(alternatives_label)
        limitation = QLabel("Heuristique déterministe, pas un simulateur de combat ni une preuve d’item optimal. Les possessions Viego et ses stats personnelles restent explicitement hors modèle.")
        limitation.setObjectName("MicroLabel"); limitation.setWordWrap(True); box.addWidget(limitation)
        layout.addWidget(card); layout.addStretch()

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
        title_box = QVBoxLayout(); title = QLabel(f"{match.champion}  •  {match.result_text}"); title.setObjectName("HeroName"); title.setProperty("result", match.result.lower()); title_box.addWidget(title)
        cs = "—" if match.cs_per_min is None else f"{match.cs_per_min:.1f}/min"
        subtitle = QLabel(f"{match.position}  •  {match.kda_text}  •  {match.cs if match.cs is not None else '—'} CS ({cs})  •  {match.duration_text}  •  {match.played_at}"); subtitle.setObjectName("Muted"); title_box.addWidget(subtitle)
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
        self._optimizer_tab(tabs, match)
        self.content.addWidget(tabs, 1)
