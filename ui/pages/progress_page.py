from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from services.asset_service import AssetService
from services.local_data import LocalDataService
from ui.components.asset_icon import AssetIcon
from ui.components.stat_card import StatCard
from ui.components.trend_chart import TrendChart


class ProgressPage(QWidget):
    def __init__(self, service: LocalDataService, assets: AssetService, parent=None):
        super().__init__(parent); self.service, self.assets = service, assets
        root = QVBoxLayout(self); root.setContentsMargins(26, 20, 26, 22); root.setSpacing(14)
        head = QHBoxLayout(); title = QLabel("Progress"); title.setObjectName("PageTitle"); head.addWidget(title); head.addStretch(); self.window = QComboBox()
        for text, data in (("Last 10", 10), ("Last 20", 20), ("Last 50", 50), ("All loaded", None)): self.window.addItem(text, data)
        self.window.setCurrentIndex(1); self.window.currentIndexChanged.connect(self.refresh); head.addWidget(self.window); root.addLayout(head)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); host = QWidget(); self.layout = QVBoxLayout(host); self.layout.setContentsMargins(0, 0, 8, 0); self.layout.setSpacing(14)
        cards = QGridLayout(); self.cards = [StatCard("WIN RATE"), StatCard("KDA"), StatCard("CS / MIN"), StatCard("DEATHS / GAME")]
        for i, card in enumerate(self.cards): cards.addWidget(card, 0, i)
        self.layout.addLayout(cards); self.comparison = QLabel(); self.comparison.setObjectName("Muted"); self.layout.addWidget(self.comparison)
        charts = QHBoxLayout(); self.result_chart = TrendChart(color="#48c78e"); self.cs_chart = TrendChart(color="#55aee8"); self.death_chart = TrendChart(color="#ef7b80")
        for title_text, chart in (("Result trend", self.result_chart), ("CS/min trend", self.cs_chart), ("Deaths trend", self.death_chart)):
            box = QFrame(); box.setObjectName("Card"); layout = QVBoxLayout(box); label = QLabel(title_text); label.setObjectName("SectionTitle"); layout.addWidget(label); layout.addWidget(chart); charts.addWidget(box)
        self.layout.addLayout(charts); pool = QLabel("Champion pool"); pool.setObjectName("SectionTitle"); self.layout.addWidget(pool)
        self.pool_host = QWidget(); self.pool = QVBoxLayout(self.pool_host); self.pool.setContentsMargins(0, 0, 0, 0); self.layout.addWidget(self.pool_host); self.layout.addStretch(); scroll.setWidget(host); root.addWidget(scroll); self.refresh()
    def refresh(self):
        while self.pool.count():
            item = self.pool.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        window = self.window.currentData(); data = self.service.progress(window); matches = self.service.matches(); selected = matches[:window] if window else matches
        values = [data.win_rate, data.kda, data.cs_per_min, data.deaths_per_match]
        for card, value in zip(self.cards, values): card.set_value("—" if value is None else f"{value:.1f}")
        self.comparison.setText(data.recent_comparison)
        ordered = list(reversed(selected)); self.result_chart.set_values([1 if m.result == "WIN" else 0 for m in ordered]); self.cs_chart.set_values([m.cs_per_min or 0 for m in ordered]); self.death_chart.set_values([m.deaths for m in ordered])
        for row in data.champion_rows[:12]:
            card = QFrame(); card.setObjectName("MatchCard"); line = QHBoxLayout(card); icon = AssetIcon(self.assets, 36); icon.load("champion", row["champion"], fallback=row["champion"]); line.addWidget(icon)
            name = QLabel(row["champion"]); name.setObjectName("MatchChampion"); line.addWidget(name, 2)
            for text in (f"{row['games']} games", f"{row['win_rate']:.0f}% WR", f"{row['kda']:.2f} KDA", f"{row['cs_per_min']:.1f} CS/min"): line.addWidget(QLabel(text), 1)
            self.pool.addWidget(card)
