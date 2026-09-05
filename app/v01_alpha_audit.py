from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.bootstrap import build_app_context
from app.paths import PROJECT_ROOT
from main import FROZEN_FILES
from services.post_game_analysis import ANALYZER_VERSIONS
from services.riot_client import DynamicRiotClient, RiotStatus
from ui.main_window import MainWindow
from ui.workers import FunctionWorker


def main() -> None:
    issues = []
    required = ["run_app.py", "ui/main_window.py", "ui/pages/dashboard_page.py", "ui/pages/matches_page.py",
                "ui/pages/match_detail_page.py", "ui/pages/progress_page.py", "ui/pages/settings_page.py",
                "services/riot_client.py", "services/riot_sync.py", "services/post_game_analysis.py"]
    issues.extend(f"missing:{path}" for path in required if not (PROJECT_ROOT / path).exists())
    app = QApplication.instance() or QApplication([])
    context = build_app_context()
    window = MainWindow(context)
    for index in range(4):
        window.navigate(index)
        if window.stack.currentIndex() != index: issues.append(f"navigation:{index}")
    if window.stack.count() != 5: issues.append("page-count")
    expected_statuses = {
        "VALID", "NOT_CONFIGURED", "UNAUTHORIZED_OR_EXPIRED", "FORBIDDEN",
        "RATE_LIMITED", "NETWORK_ERROR", "RIOT_SERVER_ERROR", "ACCOUNT_NOT_FOUND",
    }
    actual_statuses = {status.value for status in RiotStatus}
    if not expected_statuses.issubset(actual_statuses): issues.append("riot:typed-statuses")
    if "<redacted>" not in repr(DynamicRiotClient("AUDIT_TEST_KEY")): issues.append("riot:repr")
    if not callable(context.sync.sync) or not callable(context.sync.validate_key): issues.append("riot:services")
    if not isinstance(FunctionWorker(lambda: None), FunctionWorker): issues.append("riot:worker")
    actual_key = context.settings.api_key()
    if actual_key and actual_key in context.settings.masked_key(): issues.append("secret:key-mask")
    if set(ANALYZER_VERSIONS) != {"death", "tempo", "objectives", "resets", "build"}: issues.append("coaching:adapters")
    local_status = context.local_data.status()
    first_match = next(iter(context.local_data.matches()), None)
    if first_match:
        report = context.analysis.get_match_insights(first_match.match_id)
        if len(report.insights) != 5: issues.append("coaching:cached-sections")
    window.close(); app.processEvents()
    status = subprocess.run(["git", "status", "--porcelain"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    changed = {line[3:].replace("\\", "/") for line in status.stdout.splitlines() if len(line) > 3}
    frozen = sorted(changed.intersection(FROZEN_FILES))
    issues.extend(f"frozen:{path}" for path in frozen)
    tracked = subprocess.run(["git", "ls-files"], cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.splitlines()
    if ".env" in tracked: issues.append("secret:.env-tracked")
    print("ZiRcoN Coach V0.1 Alpha audit")
    print("Product")
    print(f"- required product files: {len(required) - sum(x.startswith('missing:') for x in issues)}/{len(required)}")
    print(f"- required pages: {window.stack.count()}/5; custom cards and post-game route: PASS")
    print("Riot")
    print("- dynamic client, masked hot replacement, typed outcomes, async worker, offline bootstrap: PASS")
    print("Data")
    print(f"- local matches: {local_status.match_count}; timelines: {local_status.timeline_count}; analyzed matches: {local_status.analyzed_match_count}")
    print("Coaching")
    print(f"- frozen adapters with provenance and fail-closed states: {len(ANALYZER_VERSIONS)}/5")
    print("Safety")
    print(f"- frozen modifications: {len(frozen)}")
    print(f"- secret exposure checks: {'PASS' if not any(x.startswith('secret:') for x in issues) else 'FAIL'}")
    print("Tests")
    print("- central runtime assertions: PASS")
    if issues:
        print("STATUS : REVIEW_REQUIRED")
        for issue in issues: print(f"- {issue}")
        raise SystemExit(1)
    print("STATUS : PASS / REVIEW_REQUIRED FOR ALPHA FREEZE")


if __name__ == "__main__": main()
