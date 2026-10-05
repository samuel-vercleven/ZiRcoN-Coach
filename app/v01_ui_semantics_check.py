from __future__ import annotations

import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTabWidget, QToolButton, QWidget

from services.runtime_settings import RuntimeSettingsService
from services.build_optimizer_presentation import player_facing_reasons
from services.riot_client import DynamicRiotClient, RiotResult, RiotStatus
from ui.components.status_badge import StatusBadge
from ui.components.coaching_card import CoachingCard
from ui.components.gold_timeline import GoldTimeline
from ui.components.moments_timeline import MomentsTimeline
from ui.components.insight_card import AnalyzerEventCard, InsightCard, event_timestamp_seconds
from ui.components.trend_chart import TrendChart
from ui.components.relevance_gauge import RelevanceGauge, relevance_color
from ui.pages.match_detail_page import MatchDetailPage, coach_summary_empty_message, coach_summary_lines
from ui.pages.settings_page import SettingsPage
from viewmodels import CoachingReport, InsightViewModel
from ui.player_coach import coaching_focuses


def main() -> None:
    app = QApplication.instance() or QApplication([])
    support = StatusBadge("AVAILABLE")
    assert support.property("tone") == "support" and support.property("tone") != "green"

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory); env = root / ".env"; env.write_text("RIOT_API_KEY=ACTIVE_TEST_KEY\n", encoding="utf-8")
        settings = RuntimeSettingsService(env, root / "settings.json")
        settings.set_api_status("VALID")
        # A rejected or accepted-but-unsaved candidate has no API that mutates
        # the active credential. Only save_api_key activates the replacement.
        candidate_status = "UNAUTHORIZED_OR_EXPIRED"
        assert candidate_status != settings.api_status() and settings.api_key() == "ACTIVE_TEST_KEY"
        local = Mock()
        local.player.return_value = SimpleNamespace(riot_id="Player#EUW")
        local.status.return_value = SimpleNamespace(api_status="VALID", db_path="test.db", db_available=True,
            match_count=0, timeline_count=0, analyzed_match_count=0, latest_match_date="—", last_sync_at="—", sync_message="")
        page = SettingsPage(local, settings, Mock())
        settings_copy = " ".join(label.text() for label in page.findChildren(QLabel)).casefold()
        assert not any(term in settings_copy for term in ("backend", ".env", "candidate", "timelines", "base de données"))
        page._validation_done(RiotResult(RiotStatus.UNAUTHORIZED, message="candidate rejected"), "BAD_CANDIDATE", "Player#EUW", False)
        assert settings.api_key() == "ACTIVE_TEST_KEY" and settings.api_status() == "VALID"
        settings.save_api_key("REPLACEMENT_TEST_KEY")
        assert settings.api_key() == "REPLACEMENT_TEST_KEY" and settings.api_status() == "VALID"
        assert DynamicRiotClient._retry_seconds("malformed") == 1
        assert DynamicRiotClient._retry_seconds("nan") == 1

    unavailable = CoachingReport("m", (
        InsightViewModel("DEATH", "Morts", "absent", status="UNAVAILABLE"),
        InsightViewModel("TEMPO", "Tempo", "absent", status="UNAVAILABLE"),
    ), "UNAVAILABLE")
    assert coach_summary_lines(unavailable) == ()
    missing_message = coach_summary_empty_message(unavailable)
    assert "informations" in missing_message and "données incomplètes" in missing_message

    report = CoachingReport("m", (
        InsightViewModel("DEATH", "Morts", "x", status="AVAILABLE", evidence=tuple("x" for _ in range(99))),
        InsightViewModel("TEMPO", "Tempo", "x", status="AVAILABLE", evidence=("x",),
                         findings=({"title": "Finding exact", "detail": "Signal v17", "severity": "MEDIUM", "supported": True},)),
    ), "AVAILABLE")
    assert coach_summary_lines(report) == ("Finding exact: Signal v17",)

    death_report = CoachingReport("m", (
        InsightViewModel(
            "DEATH", "Morts", "1 mort avec un repère à revoir", status="AVAILABLE",
            source_module="death", source_version="death_v11",
            findings=({"title": "Signal historique EXPERIMENTAL — HIGH",
                       "detail": "À 18:42, indice comparatif élevé; sans causalité.",
                       "severity": "HIGH", "supported": True},),
            events=({"title": "Mort à 18:42", "metrics": [
                {"label": "Tueur", "value": "Jarvan IV"},
                {"label": "État avant la mort", "value": "BEHIND"},
            ]},),
        ),
    ), "AVAILABLE")
    focus, = coaching_focuses(death_report)
    assert coaching_focuses(death_report, limit=0) == ()
    assert focus.source_tab_title == "Morts"
    assert "18:42" in focus.observation and "Jarvan IV" in " ".join(focus.evidence)

    varied_report = CoachingReport("m", (
        InsightViewModel("RESETS", "Recalls / Resets", "x", status="AVAILABLE", source_module="resets",
                         findings=({"title": "Production après reset à 04:59", "detail": "Sous la référence", "severity": "MEDIUM", "supported": True},
                                   {"title": "Production après reset à 14:08", "detail": "Sous la référence", "severity": "MEDIUM", "supported": True})),
        InsightViewModel("OBJECTIVES", "Objectifs", "x", status="AVAILABLE", source_module="objectives",
                         findings=({"title": "Objectif à revoir", "detail": "Contexte observé", "severity": "LOW", "supported": True},)),
    ), "AVAILABLE")
    varied = coaching_focuses(varied_report)
    assert len(varied) == 2 and [item.source_tab_title for item in varied] == ["Recalls / Resets", "Objectifs"]

    reset_report = CoachingReport("m", (
        InsightViewModel("RESETS", "Recalls / Resets", "x", status="AVAILABLE", source_module="resets",
                         findings=({"title": "Production après reset à 04:59",
                                    "detail": "Production observée sous la référence historique v21 (38.8/100, N=26).",
                                    "severity": "MEDIUM", "supported": True},),
                         events=({"title": "Reset / shop à 04:59", "metrics": [
                             {"label": "Origine", "value": "proxy de reset volontaire"},
                             {"label": "Timing objectif", "value": "avant un objectif"},
                             {"label": "Production après reset vs historique", "value": "38.8/100 · sous la référence"},
                         ], "context": ["timing objectif : avant un objectif · suivant DRAGON (111 s)"]},)),
    ), "AVAILABLE")
    reset_focus, = coaching_focuses(reset_report)
    assert "temps" in reset_focus.why_review and "objectif" in reset_focus.next_game_experiment
    assert any("proximité d’un objectif" in value for value in reset_focus.evidence)
    assert "ne juge pas à lui seul ton choix" in reset_focus.why_review

    death_after_reset_report = CoachingReport("m", (
        InsightViewModel("RESETS", "Recalls / Resets", "x", status="AVAILABLE", source_module="resets",
                         findings=({"title": "Production après reset à 03:35", "detail": "Sous la référence historique.", "severity": "MEDIUM", "supported": True},),
                         events=({"title": "Reset / shop à 03:35", "metrics": [
                             {"label": "Origine", "value": "proxy de reset volontaire"},
                             {"label": "Production après reset vs historique", "value": "5.2/100 · faible"},
                         ], "context": ["mort observée dans les 120 s après le proxy de reset"]},)),
    ), "AVAILABLE")
    death_after_reset, = coaching_focuses(death_after_reset_report)
    assert "Une mort est survenue" in death_after_reset.why_review
    assert "sans en conclure" in death_after_reset.why_review
    assert "menaces" in death_after_reset.next_game_experiment
    assert len(death_after_reset.next_game_experiment) < 125
    assert '5.2' not in death_after_reset.observation
    assert any('5.2' in value for value in death_after_reset.evidence)

    tabs = QTabWidget(); overview_tab = QWidget(); coach_tab = QWidget(); object_tab = QWidget()
    tabs.addTab(overview_tab, "Résumé"); tabs.addTab(coach_tab, "Coach"); tabs.addTab(object_tab, "Objets")
    card = CoachingCard(focus, open_source=MatchDetailPage._open_tab(tabs, focus.source_tab_title))
    source_action = card.findChild(QPushButton, "GhostButton")
    assert source_action is not None and source_action.text() == "Revoir les moments associés"
    source_action.click()
    assert tabs.currentWidget() is coach_tab

    compact = CoachingCard(focus, compact=True, open_source=MatchDetailPage._open_tab(tabs, "Coach"))
    compact_action = compact.findChild(QPushButton, "GhostButton")
    assert compact_action is not None and compact_action.text() == "Ouvrir Coach"
    compact_action.click()
    assert tabs.currentWidget() is coach_tab

    local_story = Mock()
    local_story.match_story.return_value = {'points': [{'timestamp': 0, 'delta': 0}, {'timestamp': 1200000, 'delta': 1000}], 'events': []}
    detail_page = MatchDetailPage(local_story, Mock(), Mock(), Mock())
    detail_page.tabs = QTabWidget()
    synthetic_match = SimpleNamespace(match_id='m', game_version='16.18.1')
    detail_page._coach_tab(detail_page.tabs, synthetic_match, death_report)
    detail_page._story_tab(detail_page.tabs, synthetic_match)
    section_toggle = detail_page.tabs.widget(0).findChild(QToolButton, 'CoachSectionToggle')
    section_details = detail_page.tabs.widget(0).findChild(QWidget, 'CoachSectionDetails')
    assert section_toggle is not None and section_details.isHidden()
    source_jump = detail_page.tabs.widget(0).findChild(QPushButton, 'GhostButton')
    source_jump.click(); app.processEvents()
    assert section_toggle.isChecked() and not section_details.isHidden()
    section_toggle.click()
    section_toggle.click()
    assert not section_details.isHidden()
    jump = section_details.findChild(QToolButton, 'TimelineJumpButton')
    assert jump is not None and '18:42' in jump.text()
    jump.click()
    assert detail_page.tabs.currentWidget() is detail_page._story_scroll
    assert detail_page._story_chart.focus_timestamp == 18 * 60 + 42
    assert '18:42' in detail_page._story_selection.text()
    assert event_timestamp_seconds({'title': 'Mort à 18:42', 'timestamp': 9999999}) == 1122
    assert event_timestamp_seconds({'title': 'Moment', 'timestamp': 42000}) == 42
    assert event_timestamp_seconds({'title': 'Phase early'}) is None
    assert event_timestamp_seconds({'timestamp': 'unknown'}) is None

    assert relevance_color(82).green() > relevance_color(10).green()
    assert relevance_color(-10) == relevance_color(0)
    assert relevance_color(110) == relevance_color(100)
    gauge = RelevanceGauge(76); gauge.set_value(82)
    assert gauge.accessibleName() == "Repère d’achat 82, estimation indicative"
    assert "/100" not in gauge.toolTip()

    full_card = CoachingCard(reset_focus)
    evidence_details = full_card.findChild(QWidget, 'CoachEvidenceDetails')
    evidence_toggle = full_card.findChild(QToolButton, 'CoachEvidenceToggle')
    assert evidence_details.isHidden() and not evidence_toggle.isChecked()
    evidence_toggle.click(); assert not evidence_details.isHidden()
    assert any('38.8' in label.text() for label in evidence_details.findChildren(QLabel))
    evidence_toggle.click(); assert evidence_details.isHidden()
    coaching_copy = " ".join(label.text() for label in full_card.findChildren(QLabel)).casefold()
    assert not any(term in coaching_copy for term in ("proxy", "v21", "expérimental", "historique"))

    old_insight = InsightViewModel("RESETS", "Recalls / Resets", "Séquence proxy de reset volontaire v21.",
                                   status="AVAILABLE", events=({"title": "Reset / shop à 03:35",
                                   "subtitle": "Évidence v21", "technical": ["reset_id=123"],
                                   "metrics": [{"label": "Gold avant / dépensé (proxy)", "value": "EXPERIMENTAL"}],
                                   "context": ["séquence v21 : proxy de reset"]},))
    player_card = InsightCard(old_insight)
    event_card = AnalyzerEventCard(old_insight.events[0], Mock())
    rendered_copy = " ".join(label.text() for widget in (player_card, event_card) for label in widget.findChildren(QLabel)).casefold()
    assert not any(term in rendered_copy for term in ("proxy", "v21", "reset_id", "recalls / resets", "experimental"))

    recommendation_copy = player_facing_reasons((
        "Direction AP compatible avec l’archétype Mage.",
        "La résistance magique ennemie est élevée dans la référence historique.",
        "Un progrès de recette réalisable est disponible.",
        "La couverture de recette utilise seulement coûts et composants observés.",
        "Le contrat de légalité v1 et le plan de recette sont supportés.",
    ), "AurelionSol")
    joined_recommendation_copy = " ".join(recommendation_copy).casefold()
    assert "puissance magique" in joined_recommendation_copy
    assert "résistance magique" in joined_recommendation_copy
    assert "référence historique" not in joined_recommendation_copy
    assert "couverture de recette" not in joined_recommendation_copy
    assert "légalité v1" not in joined_recommendation_copy

    chart = TrendChart(); chart.set_values([2.0, None, 3.0])
    assert chart.values == [2.0, None, 3.0] and chart.values[1] is None
    gold = GoldTimeline(); gold.set_points([{'timestamp': 120000, 'delta': -500}, {'timestamp': 0, 'delta': 0},
        {'timestamp': 60000, 'delta': None}, {'timestamp': float('nan'), 'delta': 100}])
    assert [point['timestamp'] for point in gold.points] == [0, 60000, 120000]
    assert gold.points[1]['delta'] is None
    gold.resize(650, 230); gold.show(); assert not gold.grab().isNull()
    moments = MomentsTimeline(); moments.resize(650, 250)
    dense_events = [{'timestamp': timestamp, 'label': 'HORDE'} for timestamp in (501000, 502000, 503000, 504000, 505000)]
    dense_events += [{'timestamp': 691000, 'label': 'DRAGON'}, {'timestamp': 762000, 'label': 'Tour'}]
    moments.set_data(list(reversed(dense_events)), 1897); moments.show(); app.processEvents()
    assert len(moments.events) == 7 and moments.events[0]['timestamp'] == 501000
    assert len(moments.rail.groups()[0][1]) == 5
    assert sum(not button.isHidden() for button in moments.buttons) == 6
    moments.expand.click(); assert all(not button.isHidden() for button in moments.buttons)
    selected = []; moments.moment_selected.connect(lambda seconds, label: selected.append((seconds, label)))
    moments.buttons[0].click(); assert selected == [(501, 'Larves du Néant')]
    for width in (360, 650, 1100):
        moments.resize(width, 280); app.processEvents()
        geometries = [button.geometry() for button in moments.buttons]
        assert not any(a.intersects(b) for index, a in enumerate(geometries) for b in geometries[index + 1:])
        assert not moments.grab().isNull()
    moments.set_data([], 1897); assert not moments.buttons and not moments.expand.isEnabled()
    app.processEvents()
    print("ZiRcoN Coach UI/status semantics check: PASS")


if __name__ == "__main__": main()
