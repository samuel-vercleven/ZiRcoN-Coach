from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QTabWidget, QVBoxLayout, QWidget

from services.asset_service import AssetService
from services.local_data import LocalDataService
from services.post_game_analysis import PostGameAnalysisService
from ui.components.asset_icon import AssetIcon
from ui.components.empty_state import EmptyState
from ui.components.insight_card import InsightCard
from ui.components.status_badge import StatusBadge


class MatchDetailPage(QWidget):
    back_requested = Signal()
    def __init__(self, service: LocalDataService, analysis: PostGameAnalysisService, assets: AssetService, parent=None):
        super().__init__(parent); self.service, self.analysis, self.assets = service, analysis, assets
        root = QVBoxLayout(self); root.setContentsMargins(26, 18, 26, 22); root.setSpacing(12)
        back = QPushButton("← Match history"); back.clicked.connect(self.back_requested); root.addWidget(back)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.host = QWidget(); self.content = QVBoxLayout(self.host); self.content.setContentsMargins(0, 0, 8, 0); self.content.setSpacing(14); self.scroll.setWidget(self.host); root.addWidget(self.scroll)
        self.load_empty()
    def _clear(self):
        while self.content.count():
            item = self.content.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        self.scroll.verticalScrollBar().setValue(0)
    def load_empty(self):
        self._clear(); self.content.addWidget(EmptyState("Select a match", "Open a match from Match History.")); self.content.addStretch()
    def load_match(self, match_id: str):
        self._clear()
        try: detail = self.service.match_detail(match_id)
        except Exception: detail = None
        if not detail:
            self.content.addWidget(EmptyState("Match unavailable", "The local row could not be loaded.")); return
        match = detail.match; hero = QFrame(); hero.setObjectName("HeroCard"); row = QHBoxLayout(hero); row.setContentsMargins(18, 16, 18, 16)
        icon = AssetIcon(self.assets, 76); icon.load("champion", match.champion, match.game_version, match.champion); row.addWidget(icon)
        title_box = QVBoxLayout(); title = QLabel(f"{match.champion}  •  {'VICTORY' if match.result == 'WIN' else 'DEFEAT'}"); title.setObjectName("HeroName"); title.setProperty("result", match.result.lower()); title_box.addWidget(title)
        cs = "—" if match.cs_per_min is None else f"{match.cs_per_min:.1f}/min"
        subtitle = QLabel(f"{match.position}  •  {match.kda_text}  •  {match.cs} CS ({cs})  •  {match.duration_seconds // 60}:{match.duration_seconds % 60:02d}  •  {match.played_at}"); subtitle.setObjectName("Muted"); title_box.addWidget(subtitle)
        items = QHBoxLayout(); items.setSpacing(5)
        for item_id in detail.items:
            item = AssetIcon(self.assets, 34); item.load("item", item_id, match.game_version); items.addWidget(item)
        items.addStretch(); title_box.addLayout(items); row.addLayout(title_box, 1)
        report = self.analysis.get_match_insights(match_id); row.addWidget(StatusBadge(report.status)); self.content.addWidget(hero)
        summary_title = QLabel("Coach Summary"); summary_title.setObjectName("SectionTitle"); self.content.addWidget(summary_title)
        supported = [value for value in report.insights if value.status in ("AVAILABLE", "PARTIAL")]
        if not supported:
            summary = QLabel("No high-confidence issue was identified in the available cached analyzers.")
            summary.setWordWrap(True); summary.setObjectName("Muted"); self.content.addWidget(summary)
        else:
            ranked = sorted(
                supported,
                key=lambda value: (value.status != "AVAILABLE", -len(value.evidence)),
            )[:4]
            for value in ranked:
                summary = QLabel(f"• {value.title}: {value.summary}")
                summary.setWordWrap(True); summary.setObjectName("Muted"); self.content.addWidget(summary)
        boundary = QLabel("Evidence-gated summaries from frozen analyzers. Status describes data support, not whether a play was good or bad."); boundary.setWordWrap(True); boundary.setObjectName("Muted"); self.content.addWidget(boundary)
        tabs = QTabWidget(); overview = QWidget(); overview_layout = QVBoxLayout(overview); overview_layout.setContentsMargins(0, 12, 0, 0)
        for insight in report.insights: overview_layout.addWidget(InsightCard(insight))
        overview_layout.addStretch(); overview_scroll = QScrollArea(); overview_scroll.setWidgetResizable(True); overview_scroll.setWidget(overview); tabs.addTab(overview_scroll, "Overview")
        for insight in report.insights:
            panel = QWidget(); layout = QVBoxLayout(panel); layout.addWidget(InsightCard(insight)); layout.addStretch(); tabs.addTab(panel, insight.title)
        self.content.addWidget(tabs); self.content.addStretch(); self.scroll.verticalScrollBar().setValue(0)
