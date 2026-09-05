from __future__ import annotations

import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from services.runtime_settings import RuntimeSettingsService
from services.riot_client import DynamicRiotClient, RiotResult, RiotStatus
from ui.components.status_badge import StatusBadge
from ui.components.trend_chart import TrendChart
from ui.pages.match_detail_page import coach_summary_empty_message, coach_summary_lines
from ui.pages.settings_page import SettingsPage
from viewmodels import CoachingReport, InsightViewModel


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

    chart = TrendChart(); chart.set_values([2.0, None, 3.0])
    assert chart.values == [2.0, None, 3.0] and chart.values[1] is None
    app.processEvents()
    print("ZiRcoN Coach UI/status semantics check: PASS")


if __name__ == "__main__": main()
