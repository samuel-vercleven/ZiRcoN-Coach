from __future__ import annotations

import os
import json
from pathlib import Path

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QApplication, QToolButton, QScrollArea

from app.bootstrap import build_app_context
from app.paths import PROJECT_ROOT
from ui.main_window import MainWindow
from ui.theme import apply_zircon_theme


def main() -> None:
    app = QApplication.instance() or QApplication([])
    apply_zircon_theme(app)
    window = MainWindow(build_app_context())
    target = PROJECT_ROOT / ".cache" / "zircon" / "visual-check"
    target.mkdir(parents=True, exist_ok=True)
    sizes = ((1600, 900, "desktop"), (1180, 720, "minimum"))
    pages = ((0, "dashboard"), (1, "matches"), (2, "progress"), (3, "settings"))
    for width, height, size_name in sizes:
        window.resize(width, height)
        window.show()
        for index, page_name in pages:
            window.navigate(index)
            app.processEvents()
            assert window.grab().save(str(target / f"{page_name}-{size_name}.png"))
    matches = window.context.local_data.matches()
    post_game_captures = 0
    if matches:
        selected = matches[0]
        replay_path = PROJECT_ROOT / "logs" / "build_optimizer" / "contextual_replay.json"
        if replay_path.exists():
            try:
                replay = json.loads(replay_path.read_text(encoding="utf-8"))
                recommended_ids = {row.get("match_id") for row in replay.get("rows", [])}
                selected = next((match for match in matches if match.match_id in recommended_ids), selected)
            except (OSError, ValueError):
                pass
        window.open_match(selected.match_id)
        QThreadPool.globalInstance().waitForDone(5000)
        app.processEvents()
        for width, height, size_name in sizes:
            window.resize(width, height)
            for _ in range(4): app.processEvents()
            for tab_index in range(window.match_detail_page.tabs.count()):
                window.match_detail_page.tabs.setCurrentIndex(tab_index); app.processEvents()
                for _ in range(4): app.processEvents()
                if window.match_detail_page.tabs.tabText(tab_index) == "Objets":
                    assert QThreadPool.globalInstance().waitForDone(30000), "Build Optimizer UI worker timed out"
                    app.processEvents()
                    assert window.match_detail_page._optimizer_worker is None, "Build Optimizer UI result was not applied"
                    first = window.match_detail_page._optimizer_layout.itemAt(0).widget()
                    assert first is not None and first.isVisible() and first.height() > 0, "Build Optimizer result has no visible layout"
                    from PySide6.QtWidgets import QLabel
                    labels = [label.text() for label in first.findChildren(QLabel) if label.text()]
                    assert labels and "Préparation du conseil…" not in labels, "Build advice stayed empty/loading"
                    assert not any(word in " ".join(labels).casefold() for word in (
                        "heuristique", "snapshot", "data dragon", "proxy de reset", "archétype",
                        "profil spécifique", "légalité v1", "référence historique", "couverture de recette",
                    )), "Technical wording leaked into player view"
                assert window.grab().save(str(target / f"post-game-{tab_index}-{size_name}.png"))
                post_game_captures += 1
            tabs = window.match_detail_page.tabs
            tabs.setCurrentIndex(0); app.processEvents()
            summary = tabs.currentWidget()
            assert isinstance(summary, QScrollArea)
            assert summary.horizontalScrollBar().maximum() == 0, 'Match summary overflows horizontally'
            tabs.setCurrentIndex(1); app.processEvents()
            toggles = [button for button in tabs.currentWidget().findChildren(QToolButton) if button.objectName() == 'CoachSectionToggle']
            if toggles:
                toggle = toggles[0]
                if not toggle.isChecked(): toggle.click()
                app.processEvents()
                tabs.currentWidget().ensureWidgetVisible(toggle)
                app.processEvents()
                jumps = [button for button in tabs.currentWidget().findChildren(QToolButton) if button.objectName() == 'TimelineJumpButton']
                if jumps:
                    tabs.currentWidget().ensureWidgetVisible(jumps[0])
                    for _ in range(4): app.processEvents()
                assert window.grab().save(str(target / f'coach-expanded-{size_name}.png')); post_game_captures += 1
                if jumps:
                    jumps[0].click(); app.processEvents()
                    assert tabs.tabText(tabs.currentIndex()) == 'Déroulé'
                    assert window.match_detail_page._story_chart.focus_timestamp is not None
                    assert window.grab().save(str(target / f'coach-timeline-jump-{size_name}.png')); post_game_captures += 1
        death_match = next((match for match in matches if match.deaths is not None and match.deaths > 0), None)
        if death_match:
            window.open_match(death_match.match_id); window.match_detail_page.tabs.setCurrentIndex(1)
            for width, height, size_name in sizes:
                window.resize(width, height); app.processEvents()
                assert window.grab().save(str(target / f"post-game-deaths-{size_name}.png")); post_game_captures += 1
    window.close()
    print(f"ZiRcoN Coach visual render check: PASS ({len(sizes) * len(pages) + post_game_captures} screenshots)")


if __name__ == "__main__":
    main()
