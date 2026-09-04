from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.bootstrap import build_app_context
from app.paths import PROJECT_ROOT
from ui.main_window import MainWindow
from ui.theme import APP_STYLESHEET


def main() -> None:
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(APP_STYLESHEET)
    window = MainWindow(build_app_context())
    target = PROJECT_ROOT / ".cache" / "zircon" / "visual-check"
    target.mkdir(parents=True, exist_ok=True)
    sizes = ((1400, 850, "normal"), (1100, 700, "minimum"))
    pages = ((0, "dashboard"), (1, "matches"), (2, "progress"), (3, "settings"))
    for width, height, size_name in sizes:
        window.resize(width, height)
        window.show()
        for index, page_name in pages:
            window.navigate(index)
            app.processEvents()
            assert window.grab().save(str(target / f"{page_name}-{size_name}.png"))
    matches = window.context.local_data.matches()
    if matches:
        window.open_match(matches[0].match_id)
        app.processEvents()
        assert window.grab().save(str(target / "post-game-normal.png"))
    window.close()
    print(f"ZiRcoN Coach visual render check: PASS ({len(sizes) * len(pages) + bool(matches)} screenshots)")


if __name__ == "__main__":
    main()
