from __future__ import annotations

from PySide6.QtCore import Qt, QThreadPool, QTimer, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QScrollArea, QTabWidget, QToolButton, QVBoxLayout, QWidget

from services.asset_service import AssetService
from services.local_data import LocalDataService
from services.post_game_analysis import PostGameAnalysisService
from services.build_optimizer_presentation import BuildOptimizerPresentationService
from ui.components.asset_icon import AssetIcon
from ui.components.empty_state import EmptyState
from ui.components.insight_card import AnalyzerEventCard, InsightCard, player_insight_summary, player_insight_title
from ui.components.coaching_card import CoachingCard
from ui.components.gold_timeline import GoldTimeline
from ui.components.moments_timeline import MomentsTimeline
from ui.components.performance_gauge import PerformanceGauge
from ui.components.relevance_gauge import RelevanceGauge
from ui.components.status_badge import SeverityBadge, StatusBadge
from ui.workers import FunctionWorker
from viewmodels import CoachingReport
from ui.player_coach import coaching_empty_message, coaching_focuses


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
        return "Certaines informations de cette partie manquent. Je préfère ne pas tirer de conclusion à partir de données incomplètes."
    return "Je n’ai pas repéré de conseil assez clair dans les informations disponibles. Cela ne veut pas dire que la partie était parfaite."


class MatchDetailPage(QWidget):
    back_requested = Signal()

    def __init__(self, service: LocalDataService, analysis: PostGameAnalysisService,
                 optimizer: BuildOptimizerPresentationService, assets: AssetService, parent=None):
        super().__init__(parent)
        self.service, self.analysis, self.optimizer, self.assets = service, analysis, optimizer, assets
        self._optimizer_worker = None; self._optimizer_match_id = None; self._optimizer_layout = None; self._optimizer_preview_layout = None; self._optimizer_version = 0
        root = QVBoxLayout(self); root.setContentsMargins(30, 24, 30, 24); root.setSpacing(14)
        back = QPushButton("‹  Retour à l’historique"); back.setObjectName("BackButton"); back.clicked.connect(self.back_requested); root.addWidget(back, 0, Qt.AlignmentFlag.AlignLeft)
        self.host = QWidget(); self.content = QVBoxLayout(self.host); self.content.setContentsMargins(0, 0, 0, 0); self.content.setSpacing(10); root.addWidget(self.host, 1)
        self.load_empty()

    def _clear(self):
        self._optimizer_version += 1
        self._optimizer_layout = None
        self._optimizer_preview_layout = None
        self._optimizer_preview_match_id = None
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
    def _open_tab(tabs: QTabWidget, _source_title: str):
        """Open the consolidated Coach tab for any finding's source analysis."""
        def open_tab():
            for index in range(tabs.count()):
                if tabs.tabText(index) == "Coach":
                    tabs.setCurrentIndex(index)
                    return
        return open_tab

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
        scroll.setWidget(host); tabs.addTab(scroll, "Objets")
        self._optimizer_layout, self._optimizer_match_id = layout, match.match_id
        self._optimizer_version += 1; version = self._optimizer_version
        layout.addWidget(EmptyState("Préparation du conseil", "J’examine les objets et les adversaires rencontrés pendant la partie."))
        layout.addStretch()
        worker = FunctionWorker(self.optimizer.recommendation_for_match, match.match_id)
        worker.setAutoDelete(False)
        worker.signals.result.connect(lambda result, current=match.match_id, token=version: self._show_optimizer_result(current, token, result, match.game_version))
        worker.signals.error.connect(lambda _message, current=match.match_id, token=version: self._show_optimizer_result(
            current, token, {'status': 'UNAVAILABLE', 'reason': 'Impossible de préparer le conseil pour le moment. Réessaie plus tard.'}, match.game_version))
        worker.signals.finished.connect(lambda current=worker: setattr(self, '_optimizer_worker', None) if self._optimizer_worker is current else None)
        self._optimizer_worker = worker; QThreadPool.globalInstance().start(worker)

    def _match_summary_tab(self, tabs, match, report):
        roster = self.service.match_roster(match.match_id)
        def build(layout):
            if not roster:
                layout.addWidget(EmptyState("Composition indisponible", "Les participants de cette partie ne sont pas présents localement.")); return
            from ui.components.scoreboard import Scoreboard
            layout.addWidget(Scoreboard(roster, self.assets, match))
            focuses = coaching_focuses(report, limit=1)
            if focuses:
                layout.addWidget(CoachingCard(
                    focuses[0], compact=True,
                    open_source=self._open_tab(tabs, "Coach"),
                ))
            else:
                prompt = QLabel(coaching_empty_message(report)); prompt.setObjectName('Muted'); prompt.setWordWrap(True); layout.addWidget(prompt)
            player_row = next((row for row in roster if row['is_player']), None)
            opponent = next((row for row in roster if row['is_enemy'] and player_row and row['position'] == player_row['position']), None)
            dashboard = QGridLayout(); dashboard.setHorizontalSpacing(12); dashboard.setVerticalSpacing(12)
            performance = QFrame(); performance.setObjectName('DashboardCard'); performance_box = QVBoxLayout(performance); performance_box.setContentsMargins(16, 14, 16, 14); performance_box.setSpacing(7)
            performance_title = QLabel('Performance'); performance_title.setObjectName('SectionTitle'); performance_box.addWidget(performance_title)
            def shown(value): return '—' if value is None else f"{value:,}".replace(',', ' ')
            if player_row:
                kda = (player_row['kills'] or 0) + (player_row['assists'] or 0)
                ratio = kda / max(1, player_row['deaths'] or 0)
                performance_top = QHBoxLayout(); gauge = PerformanceGauge(); gauge.set_value(ratio); performance_top.addWidget(gauge)
                score_box = QVBoxLayout(); score = QLabel(f"{ratio:.1f} KDA"); score.setObjectName('PerformanceScore'); score_box.addWidget(score)
                score_detail = QLabel(f"{shown(player_row['kills'])} / {shown(player_row['deaths'])} / {shown(player_row['assists'])}\n{match.duration_text} · {match.queue}"); score_detail.setObjectName('Muted'); score_box.addWidget(score_detail); score_box.addStretch(); performance_top.addLayout(score_box, 1); performance_box.addLayout(performance_top)
                metrics = QLabel(f"{shown(player_row['kills'])}/{shown(player_row['deaths'])}/{shown(player_row['assists'])}  ·  {shown(player_row['cs'])} CS  ·  {shown(player_row['gold'])} or\n{shown(player_row['damage'])} dégâts champions  ·  vision {shown(player_row['vision'])}")
                metrics.setObjectName('ContextLine'); metrics.setWordWrap(True); performance_box.addWidget(metrics)
                if opponent:
                    lane = QLabel(f"Matchup {player_row['position']} : {player_row['champion']} vs {opponent['champion']} · {shown(player_row['cs'])} vs {shown(opponent['cs'])} CS")
                    lane.setObjectName('MicroLabel'); lane.setWordWrap(True); performance_box.addWidget(lane)
            dashboard.addWidget(performance, 0, 0)
            build = QFrame(); build.setObjectName('DashboardCard'); build_box = QVBoxLayout(build); build_box.setContentsMargins(16, 14, 16, 14); build_box.setSpacing(7)
            build_title = QLabel('Build final'); build_title.setObjectName('SectionTitle'); build_box.addWidget(build_title)
            build_note = QLabel('Objets à la fin de la partie'); build_note.setObjectName('Muted'); build_box.addWidget(build_note)
            item_row = QHBoxLayout(); item_row.setSpacing(6)
            for item_id in match.items[:6]:
                icon = AssetIcon(self.assets, 38); icon.load('item', item_id, match.game_version); item_row.addWidget(icon)
            item_row.addStretch(); build_box.addLayout(item_row)
            runes = QLabel('Runes : informations non disponibles'); runes.setObjectName('MicroLabel'); runes.setWordWrap(True); build_box.addWidget(runes); dashboard.addWidget(build, 0, 1)
            preview = QFrame(); preview.setObjectName('OptimizerPreview'); preview_box = QVBoxLayout(preview); preview_box.setContentsMargins(16, 14, 16, 14); preview_box.setSpacing(7)
            preview_title = QLabel('Conseil de build'); preview_title.setObjectName('SectionTitle'); preview_box.addWidget(preview_title)
            waiting = QLabel('Préparation du conseil…'); waiting.setObjectName('Muted'); waiting.setWordWrap(True); preview_box.addWidget(waiting)
            self._optimizer_preview_layout = preview_box; self._optimizer_preview_match_id = match.match_id
            dashboard.addWidget(preview, 0, 2)
            for column in range(3): dashboard.setColumnStretch(column, 1)
            layout.addLayout(dashboard)
            story = self.service.match_story(match.match_id)
            gold = QFrame(); gold.setObjectName('TimelineCard'); gold_box = QVBoxLayout(gold); gold_box.setContentsMargins(16, 14, 16, 14)
            gold_title = QLabel('Évolution de l’avantage en or'); gold_title.setObjectName('SectionTitle'); gold_box.addWidget(gold_title)
            gold_note = QLabel('Vert : ton équipe en avance · Rouge : équipe adverse en avance · Survole pour lire un relevé.'); gold_note.setObjectName('Muted'); gold_note.setWordWrap(True); gold_box.addWidget(gold_note)
            chart = GoldTimeline(); chart.set_points(story.get('points')); gold_box.addWidget(chart); layout.addWidget(gold)
            lower = QGridLayout(); lower.setHorizontalSpacing(12)
            moments = QFrame(); moments.setObjectName('TimelineCard'); moments_box = QVBoxLayout(moments); moments_box.setContentsMargins(16, 14, 16, 14); moments_box.setSpacing(6)
            moments_title = QLabel('Objectifs & tours'); moments_title.setObjectName('SectionTitle'); moments_box.addWidget(moments_title)
            timeline = MomentsTimeline(); timeline.set_data(story.get('events'), match.duration_seconds)
            timeline.moment_selected.connect(self._open_story_moment)
            moments_box.addWidget(timeline); lower.addWidget(moments, 0, 0)
            recap = QFrame(); recap.setObjectName('RecapCard'); recap_box = QVBoxLayout(recap); recap_box.setContentsMargins(16, 14, 16, 14); recap_box.setSpacing(6)
            recap_title = QLabel('Résumé de la partie'); recap_title.setObjectName('SectionTitle'); recap_box.addWidget(recap_title)
            recap_text = QLabel(f"{match.result_text} · {match.champion} · {match.kda_text} KDA\nOuvre Coach pour voir les moments à revoir."); recap_text.setObjectName('ContextLine'); recap_text.setWordWrap(True); recap_box.addWidget(recap_text); recap_box.addStretch(); lower.addWidget(recap, 0, 1)
            lower.setColumnStretch(0, 2); lower.setColumnStretch(1, 1); layout.addLayout(lower)
            boundary = QLabel("Le résumé montre le résultat final. Le conseil de build s’appuie sur l’or, les objets et les adversaires observés à un moment précis de la partie.")
            boundary.setObjectName("MicroLabel"); boundary.setWordWrap(True); layout.addWidget(boundary)
        tabs.addTab(self._scroll_panel(build), "Résumé")

    def _show_optimizer_preview(self, match_id, result, game_version):
        if match_id != getattr(self, '_optimizer_preview_match_id', None) or self._optimizer_preview_layout is None:
            return
        layout = self._optimizer_preview_layout; self._clear_layout(layout)
        status = result.get('status', 'UNAVAILABLE') if isinstance(result, dict) else 'UNAVAILABLE'
        title = QLabel('Conseil de build'); title.setObjectName('SectionTitle'); layout.addWidget(title)
        if status != 'SUPPORTED_HEURISTIC':
            unavailable = QLabel('Pas de conseil : ' + str(result.get('reason') or 'contexte local insuffisant.'))
            unavailable.setObjectName('Muted'); unavailable.setWordWrap(True); layout.addWidget(unavailable); return
        choice = QHBoxLayout(); icon = AssetIcon(self.assets, 40); icon.load('item', result.get('target_item'), game_version, result.get('target_name') or '?'); choice.addWidget(icon)
        gauge = RelevanceGauge(58); gauge.set_value(result.get('score', 0)); choice.addWidget(gauge)
        text = QVBoxLayout(); item = QLabel(result.get('target_name') or 'Objet inconnu'); item.setObjectName('EventTitle'); text.addWidget(item)
        score = QLabel(f"Pertinence estimée · vers {result.get('snapshot_label', '—')}"); score.setObjectName('OptimizerScore'); score.setWordWrap(True); text.addWidget(score); choice.addLayout(text, 1); layout.addLayout(choice)
        reason = next(iter(result.get('reasons') or ()), 'Direction contextualisée par les observations locales.')
        why = QLabel(reason); why.setObjectName('Muted'); why.setWordWrap(True); layout.addWidget(why)

    def _story_tab(self, tabs, match):
        story = self.service.match_story(match.match_id)
        def build(layout):
            card = QFrame(); card.setObjectName('Card'); box = QVBoxLayout(card); box.setContentsMargins(18, 15, 18, 15); box.setSpacing(9)
            title = QLabel('Déroulé de la partie'); title.setObjectName('SectionTitle'); box.addWidget(title)
            note = QLabel("Écart d’or entre les équipes : au-dessus de zéro, ton équipe avait l’avantage. Cette courbe montre l’évolution de la partie, pas ce qui l’a causée.")
            note.setObjectName('Muted'); note.setWordWrap(True); box.addWidget(note)
            self._story_selection = QLabel(); self._story_selection.setObjectName('ContextLine'); self._story_selection.setWordWrap(True); self._story_selection.hide(); box.addWidget(self._story_selection)
            chart = GoldTimeline(); chart.set_points(story.get('points')); box.addWidget(chart)
            self._story_chart = chart
            layout.addWidget(card)
            events = story.get('events') or ()
            if events:
                milestones = QFrame(); milestones.setObjectName('Card'); line = QVBoxLayout(milestones); line.setContentsMargins(18, 15, 18, 15); line.setSpacing(6)
                heading = QLabel('Moments observés'); heading.setObjectName('SectionTitle'); line.addWidget(heading)
                for event in events:
                    seconds = int(event.get('timestamp', 0) // 1000)
                    from ui.components.moments_timeline import event_label
                    label = QToolButton(); label.setText(f"{seconds // 60:02d}:{seconds % 60:02d}  ·  {event_label(event)}"); label.setObjectName('TimelineJumpButton')
                    label.clicked.connect(lambda checked=False, time=seconds, text=event_label(event): self._open_story_moment(time, text)); line.addWidget(label)
                layout.addWidget(milestones)
        self._story_scroll = self._scroll_panel(build)
        tabs.addTab(self._story_scroll, 'Déroulé')

    def _open_story_moment(self, seconds: int, label: str):
        """Select a factual clock on the post-game chart, without creating an event."""
        self.tabs.setCurrentWidget(self._story_scroll)
        self._story_selection.setText(f"Moment sélectionné · {seconds // 60:02d}:{seconds % 60:02d} · {label}\nLe trait jaune indique cette heure. Survole la courbe pour lire un relevé d’or disponible.")
        self._story_selection.show()
        self._story_chart.set_focus(seconds)
        QTimer.singleShot(0, lambda: self._story_scroll.ensureWidgetVisible(self._story_selection))

    def _journal_tab(self, tabs, match):
        cache = self.service.cache
        journal = cache.match_journal(match.match_id) if cache else {'starred': False, 'note': ''}
        def build(layout):
            card = QFrame(); card.setObjectName('Card'); box = QVBoxLayout(card); box.setContentsMargins(18, 15, 18, 15); box.setSpacing(9)
            title = QLabel('Notes de coaching'); title.setObjectName('SectionTitle'); box.addWidget(title)
            note = QLabel('Garde ici une leçon courte à revoir. Cette note reste sur cet ordinateur.'); note.setObjectName('Muted'); note.setWordWrap(True); box.addWidget(note)
            favorite = QPushButton('★ Partie à revoir'); favorite.setObjectName('CompactButton'); favorite.setCheckable(True); favorite.setChecked(bool(journal['starred'])); box.addWidget(favorite, 0)
            editor = QPlainTextEdit(); editor.setPlaceholderText('Exemple : mieux préparer le dragon à 14:00.'); editor.setPlainText(journal['note']); editor.setMaximumHeight(150); box.addWidget(editor)
            save = QPushButton('Enregistrer ma note'); save.setObjectName('PrimaryButton'); box.addWidget(save, 0)
            status = QLabel(''); status.setObjectName('Muted'); box.addWidget(status)
            def persist():
                if not cache: status.setText('Sauvegarde indisponible sur cet ordinateur.'); return
                try:
                    cache.save_match_journal(match.match_id, favorite.isChecked(), editor.toPlainText()); status.setText('Note enregistrée sur cet ordinateur.')
                except Exception:
                    status.setText('Enregistrement local impossible.')
            save.clicked.connect(persist); layout.addWidget(card)
        tabs.addTab(self._scroll_panel(build), 'Notes')

    def _show_optimizer_result(self, match_id, version, result, game_version):
        if match_id != self._optimizer_match_id or version != self._optimizer_version or self._optimizer_layout is None:
            return
        layout = self._optimizer_layout; self._clear_layout(layout)
        status = result.get('status', 'UNAVAILABLE') if isinstance(result, dict) else 'UNAVAILABLE'
        self._show_optimizer_preview(match_id, result, game_version)
        if status != 'SUPPORTED_HEURISTIC':
            card = QFrame(); card.setObjectName("CoachCard"); box = QVBoxLayout(card); box.setContentsMargins(15, 12, 15, 12); box.setSpacing(6)
            heading = QHBoxLayout(); title = QLabel("Pas de conseil pour cette partie"); title.setObjectName("SectionTitle"); heading.addWidget(title); heading.addStretch(); heading.addWidget(StatusBadge("PARTIAL")); box.addLayout(heading)
            message = QLabel("ZiRcoN s’abstient : " + str(result.get('reason') or 'contexte, patch ou historique insuffisant.'))
            message.setObjectName("Muted"); message.setWordWrap(True); box.addWidget(message)
            note = QLabel("Mieux vaut ne rien conseiller que te proposer un achat qui ne correspondrait pas à la situation.")
            note.setObjectName("MicroLabel"); note.setWordWrap(True); box.addWidget(note); layout.addWidget(card); layout.addStretch(); return
        card = QFrame(); card.setObjectName("OptimizerHero"); box = QVBoxLayout(card); box.setContentsMargins(20, 17, 20, 17); box.setSpacing(10)
        header = QHBoxLayout(); title = QLabel("Piste d’achat à examiner"); title.setObjectName("SectionTitle"); header.addWidget(title); header.addStretch(); header.addWidget(StatusBadge("AVAILABLE")); box.addLayout(header)
        context = QLabel(f"Pour {result['champion']} · situation vers {result['snapshot_label']} · repères issus de {result['baseline_samples']} partie(s) précédente(s)")
        context.setObjectName("Muted"); context.setWordWrap(True); box.addWidget(context)
        choice = QHBoxLayout(); icon = AssetIcon(self.assets, 46); icon.load("item", result.get('target_item'), game_version, result.get('target_name') or '?'); choice.addWidget(icon)
        choice_text = QVBoxLayout(); item_name = QLabel(result.get('target_name') or 'Objet inconnu'); item_name.setObjectName("EventTitle"); choice_text.addWidget(item_name)
        gauge = RelevanceGauge(82); gauge.set_value(result.get("score", 0)); choice.addWidget(gauge)
        score = QLabel("Pertinence estimée"); score.setObjectName("ContextLine"); score.setWordWrap(True); choice_text.addWidget(score)
        score_note = QLabel("Repère de comparaison, pas une probabilité de réussite.")
        score_note.setObjectName("MicroLabel"); score_note.setWordWrap(True); choice_text.addWidget(score_note)
        choice.addLayout(choice_text, 1); box.addLayout(choice)
        reasons = result.get('reasons') or ()
        if reasons:
            why = QLabel("Pourquoi :"); why.setObjectName("CardTitle"); box.addWidget(why)
            for reason in reasons[:5]:
                line = QLabel("• " + str(reason)); line.setObjectName("ContextLine"); line.setWordWrap(True); box.addWidget(line)
        steps = result.get('buy_now_named') or ()
        purchase = QLabel("Étapes d’achat possibles à ce moment : " + (" → ".join(f"{step['name']} ({step['cost']} PO)" for step in steps) if steps else "tu n’avais pas assez d’or pour terminer cet objet à ce moment."))
        purchase.setObjectName("Muted"); purchase.setWordWrap(True); box.addWidget(purchase)
        alternatives = result.get('alternatives_named') or ()
        if alternatives:
            alternatives_label = QLabel("Autres objets à envisager : " + " · ".join(row['name'] for row in alternatives))
            alternatives_label.setObjectName("Muted"); alternatives_label.setWordWrap(True); box.addWidget(alternatives_label)
        enemy_snapshot = result.get('enemy_snapshot') or ()
        if enemy_snapshot:
            readable = []
            for enemy in enemy_snapshot:
                stats = []
                if enemy.get('health_max') is not None: stats.append(f"{int(enemy['health_max'])} PV max")
                if enemy.get('armor') is not None: stats.append(f"{int(enemy['armor'])} armure")
                readable.append(enemy.get('champion', 'Inconnu') + (f" ({', '.join(stats)})" if stats else ""))
            matchup = QLabel("Adversaires présents à ce moment : " + " · ".join(readable))
            matchup.setObjectName("ContextLine"); matchup.setWordWrap(True); box.addWidget(matchup)
        limitations = ["C’est une piste à vérifier, pas la preuve qu’un objet était le meilleur choix."]
        if result.get('profile_scope') == 'GENERIC_CLASS_ARCHETYPE':
            limitations.append("Ce conseil s’appuie surtout sur le style général du champion ; il est moins personnalisé.")
        if result.get('champion') == 'Viego':
            limitations.append("Avec Viego, les objets et les caractéristiques peuvent changer lorsqu’il prend possession d’un adversaire ; cette situation n’est pas prise en compte ici.")
        limitation = QLabel(" ".join(limitations))
        limitation.setObjectName("MicroLabel"); limitation.setWordWrap(True); box.addWidget(limitation)
        layout.addWidget(card); layout.addStretch()

    def _coach_tab(self, tabs, match, report):
        sections = {}
        def open_section(title):
            section = sections.get(title)
            if section:
                toggle, group = section
                toggle.setChecked(True)
                QTimer.singleShot(0, lambda: scroll.ensureWidgetVisible(group, 0, 15))
        def build(layout):
            summary_card = QFrame(); summary_card.setObjectName("CoachCard"); summary_layout = QVBoxLayout(summary_card); summary_layout.setContentsMargins(17, 14, 17, 14); summary_layout.setSpacing(7)
            summary_title = QLabel("Synthèse coach"); summary_title.setObjectName("SectionTitle"); summary_layout.addWidget(summary_title)
            focuses = coaching_focuses(report)
            if focuses:
                for focus in focuses:
                    summary_layout.addWidget(CoachingCard(focus, open_source=lambda checked=False, title=focus.source_tab_title: open_section(title)))
            else:
                label = QLabel(coaching_empty_message(report)); label.setWordWrap(True); label.setObjectName("Muted"); summary_layout.addWidget(label)
            boundary = QLabel("Ces pistes aident à revoir la partie et à tester une habitude. Ce ne sont pas des explications certaines du résultat."); boundary.setObjectName("MicroLabel"); boundary.setWordWrap(True); summary_layout.addWidget(boundary)
            layout.addWidget(summary_card)

            heading = QLabel("Détails par thème"); heading.setObjectName("SectionTitle"); layout.addWidget(heading)
            for current in report.insights:
                group = QFrame(); group.setObjectName("AnalyzerHeader"); group_layout = QVBoxLayout(group); group_layout.setContentsMargins(14, 11, 14, 11)
                top = QHBoxLayout()
                toggle = QToolButton(); toggle.setObjectName("CoachSectionToggle")
                toggle.setText(f"{player_insight_title(current)} · {len(current.events)} moment(s)")
                toggle.setCheckable(True); toggle.setArrowType(Qt.ArrowType.RightArrow)
                toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
                toggle.setCursor(Qt.CursorShape.PointingHandCursor); top.addWidget(toggle, 1)
                top.addWidget(StatusBadge(current.status)); group_layout.addLayout(top)
                details = QWidget(); details.setObjectName("CoachSectionDetails"); h = QVBoxLayout(details); h.setContentsMargins(0, 8, 0, 0)
                summary = QLabel(player_insight_summary(current)); summary.setWordWrap(True); summary.setObjectName("Muted"); h.addWidget(summary)
                for event in current.events:
                    h.addWidget(AnalyzerEventCard(event, self.assets, match.game_version, on_timeline=self._open_story_moment))
                if not current.events:
                    h.addWidget(EmptyState("Aucun moment disponible", "Les informations de ce thème ne permettent pas de détailler un moment précis."))
                group_layout.addWidget(details); details.hide()
                toggle.toggled.connect(details.setVisible)
                toggle.toggled.connect(lambda checked, target=toggle: target.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow))
                sections[current.title] = (toggle, group)
                layout.addWidget(group)
        scroll = self._scroll_panel(build)
        tabs.addTab(scroll, "Coach")

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

        tabs = QTabWidget(); self.tabs = tabs
        self._match_summary_tab(tabs, match, report)
        self._coach_tab(tabs, match, report)
        self._optimizer_tab(tabs, match)
        self._story_tab(tabs, match)
        self._journal_tab(tabs, match)
        self.content.addWidget(tabs, 1)
