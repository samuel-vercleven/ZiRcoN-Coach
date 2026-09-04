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
from ui.main_window import MainWindow


def main() -> None:
    issues = []
    required = ["run_app.py", "ui/main_window.py", "ui/pages/dashboard_page.py", "ui/pages/matches_page.py",
                "ui/pages/match_detail_page.py", "ui/pages/progress_page.py", "ui/pages/settings_page.py",
                "services/riot_client.py", "services/riot_sync.py", "services/post_game_analysis.py"]
    issues.extend(f"missing:{path}" for path in required if not (PROJECT_ROOT / path).exists())
    app = QApplication.instance() or QApplication([])
    window = MainWindow(build_app_context())
    for index in range(4):
        window.navigate(index)
        if window.stack.currentIndex() != index: issues.append(f"navigation:{index}")
    if window.stack.count() != 5: issues.append("page-count")
    window.close(); app.processEvents()
    status = subprocess.run(["git", "status", "--porcelain"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    changed = {line[3:].replace("\\", "/") for line in status.stdout.splitlines() if len(line) > 3}
    frozen = sorted(changed.intersection(FROZEN_FILES))
    issues.extend(f"frozen:{path}" for path in frozen)
    tracked = subprocess.run(["git", "ls-files"], cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.splitlines()
    if ".env" in tracked: issues.append("secret:.env-tracked")
    print("ZiRcoN Coach V0.1 Alpha audit")
    print(f"Required product files: {len(required) - sum(x.startswith('missing:') for x in issues)}/{len(required)}")
    print(f"Required pages: {window.stack.count()}/5")
    print(f"Frozen modifications: {len(frozen)}")
    print(f"Secret exposure checks: {'PASS' if not any(x.startswith('secret:') for x in issues) else 'FAIL'}")
    if issues:
        print("STATUS : REVIEW_REQUIRED")
        for issue in issues: print(f"- {issue}")
        raise SystemExit(1)
    print("STATUS : PASS / REVIEW_REQUIRED FOR ALPHA FREEZE")


if __name__ == "__main__": main()
