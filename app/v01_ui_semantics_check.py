from __future__ import annotations

import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton, QTabWidget, QWidget

from services.runtime_settings import RuntimeSettingsService
from services.riot_client import DynamicRiotClient, RiotResult, RiotStatus
from ui.components.status_badge import StatusBadge
from ui.components.coaching_card import CoachingCard
from ui.components.trend_chart import TrendChart
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
    assert "Synthèse limitée" in missing_message and "absence de problème" in missing_message

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
    assert any("DRAGON (111 s)" in value for value in reset_focus.evidence)
    assert "ne suffit pas à juger le reset" in reset_focus.why_review

    death_after_reset_report = CoachingReport("m", (
        InsightViewModel("RESETS", "Recalls / Resets", "x", status="AVAILABLE", source_module="resets",
                         findings=({"title": "Production après reset à 03:35", "detail": "Sous la référence historique.", "severity": "MEDIUM", "supported": True},),
                         events=({"title": "Reset / shop à 03:35", "metrics": [
                             {"label": "Origine", "value": "proxy de reset volontaire"},
                             {"label": "Production après reset vs historique", "value": "5.2/100 · faible"},
                         ], "context": ["mort observée dans les 120 s après le proxy de reset"]},)),
    ), "AVAILABLE")
    death_after_reset, = coaching_focuses(death_after_reset_report)
    assert "Une mort est observée" in death_after_reset.why_review
    assert "ne prouvent pas" in death_after_reset.why_review
    assert "menaces" in death_after_reset.next_game_experiment

    tabs = QTabWidget(); overview_tab = QWidget(); coach_tab = QWidget(); death_tab = QWidget()
    tabs.addTab(overview_tab, "Vue d’ensemble"); tabs.addTab(coach_tab, "Analyse coach")
    tabs.addTab(death_tab, focus.source_tab_title)
    card = CoachingCard(focus, open_source=MatchDetailPage._open_tab(tabs, focus.source_tab_title))
    source_action = card.findChild(QPushButton, "GhostButton")
    assert source_action is not None and source_action.text() == "Voir les événements associés"
    source_action.click()
    assert tabs.currentWidget() is death_tab

    compact = CoachingCard(focus, compact=True, open_source=MatchDetailPage._open_tab(tabs, "Analyse coach"))
    compact_action = compact.findChild(QPushButton, "GhostButton")
    assert compact_action is not None and compact_action.text() == "Ouvrir l’analyse coach"
    compact_action.click()
    assert tabs.currentWidget() is coach_tab

    chart = TrendChart(); chart.set_values([2.0, None, 3.0])
    assert chart.values == [2.0, None, 3.0] and chart.values[1] is None
    app.processEvents()
    print("ZiRcoN Coach UI/status semantics check: PASS")


if __name__ == "__main__": main()
