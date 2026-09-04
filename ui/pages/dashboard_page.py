from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from services.asset_service import AssetService
from services.local_data import LocalDataService
from ui.components.asset_icon import AssetIcon
from ui.components.empty_state import EmptyState
from ui.components.match_card import MatchCard
from ui.components.stat_card import StatCard
from ui.components.status_badge import StatusBadge


class DashboardPage(QWidget):
    open_match = Signal(str)

    def __init__(self, service: LocalDataService, assets: AssetService, parent=None):
        super().__init__(parent); self.service, self.assets = service, assets
        root = QVBoxLayout(self); root.setContentsMargins(26, 20, 26, 22); root.setSpacing(16)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        content = QWidget(); self.layout = QVBoxLayout(content); self.layout.setContentsMargins(0, 0, 8, 0); self.layout.setSpacing(16)
        self.hero = QFrame(); self.hero.setObjectName("HeroCard"); hero = QHBoxLayout(self.hero); hero.setContentsMargins(20, 18, 20, 18)
        self.profile_icon = AssetIcon(assets, 72); hero.addWidget(self.profile_icon)
        identity = QVBoxLayout(); self.player_name = QLabel("Local player"); self.player_name.setObjectName("HeroName")
        self.rank = QLabel("Rank unavailable"); self.rank.setObjectName("HeroRank"); self.profile_meta = QLabel(); self.profile_meta.setObjectName("Muted")
        identity.addWidget(self.player_name); identity.addWidget(self.rank); identity.addWidget(self.profile_meta); hero.addLayout(identity, 1)
        self.profile_status = StatusBadge("LOCAL"); hero.addWidget(self.profile_status)
        self.layout.addWidget(self.hero)
        cards = QGridLayout(); cards.setSpacing(10)
        self.cards = [StatCard("LOADED GAMES"), StatCard("WIN RATE"), StatCard("KDA"), StatCard("CS / MIN"), StatCard("DEATHS / GAME")]
        for index, card in enumerate(self.cards): cards.addWidget(card, 0, index)
        self.layout.addLayout(cards)
        recent_header = QHBoxLayout(); title = QLabel("Recent matches"); title.setObjectName("SectionTitle"); recent_header.addWidget(title); recent_header.addStretch()
        self.form = QLabel(); self.form.setObjectName("Muted"); recent_header.addWidget(self.form); self.layout.addLayout(recent_header)
        self.match_host = QWidget(); self.match_layout = QVBoxLayout(self.match_host); self.match_layout.setContentsMargins(0, 0, 0, 0); self.match_layout.setSpacing(8)
        self.layout.addWidget(self.match_host); self.layout.addStretch(); scroll.setWidget(content); root.addWidget(scroll)
        self.refresh()

    def _clear_matches(self):
        while self.match_layout.count():
            item = self.match_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def refresh(self):
        self._clear_matches()
        try:
            player, progress, matches = self.service.player(), self.service.progress(), self.service.matches()[:6]
        except Exception:
            self.match_layout.addWidget(EmptyState("Local data unavailable", "Settings remains available; no network is required to open the app.")); return
        self.player_name.setText(player.riot_id); self.rank.setText(f"{player.rank}{f' • {player.lp} LP' if player.lp is not None else ''}")
        self.profile_meta.setText(f"Level {player.summoner_level or 'UNAVAILABLE'}  •  Ranked Solo/Duo  •  Local-first")
        self.profile_status.set_status(player.profile_status)
        self.profile_icon.load("profileicon", player.profile_icon_id, fallback=player.riot_id)
        values = [str(progress.total_games), "—" if progress.win_rate is None else f"{progress.win_rate:.1f}%",
                  "—" if progress.kda is None else f"{progress.kda:.2f}", "—" if progress.cs_per_min is None else f"{progress.cs_per_min:.1f}",
                  "—" if progress.deaths_per_match is None else f"{progress.deaths_per_match:.1f}"]
        for card, value in zip(self.cards, values): card.set_value(value)
        recent = matches[:5]; wins = sum(row.result == "WIN" for row in recent)
        self.form.setText("Recent form  " + " ".join("W" if row.result == "WIN" else "L" for row in recent) + (f"  •  {wins}/{len(recent)} wins" if recent else ""))
        if not matches:
            self.match_layout.addWidget(EmptyState("No local player data found", "1. Configure Riot ID  2. Add RIOT_API_KEY in Settings  3. Sync matches"))
        for match in matches:
            card = MatchCard(match, self.assets); card.opened.connect(self.open_match); self.match_layout.addWidget(card)
