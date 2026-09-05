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
        scroll = QScrollArea(); scroll.setWidgetResizable(True); content = QWidget(); self.layout = QVBoxLayout(content); self.layout.setContentsMargins(0, 0, 8, 0); self.layout.setSpacing(16)
        self.hero = QFrame(); self.hero.setObjectName("HeroCard"); hero = QHBoxLayout(self.hero); hero.setContentsMargins(20, 18, 20, 18); self.profile_icon = AssetIcon(assets, 72); hero.addWidget(self.profile_icon)
        identity = QVBoxLayout(); self.player_name = QLabel("Joueur local"); self.player_name.setObjectName("HeroName"); self.rank = QLabel("Rang indisponible"); self.rank.setObjectName("HeroRank"); self.profile_meta = QLabel(); self.profile_meta.setObjectName("Muted"); identity.addWidget(self.player_name); identity.addWidget(self.rank); identity.addWidget(self.profile_meta); hero.addLayout(identity, 1)
        self.profile_status = StatusBadge("LOCAL"); hero.addWidget(self.profile_status); self.layout.addWidget(self.hero)
        cards = QGridLayout(); cards.setSpacing(10); self.cards = [StatCard("PARTIES SOLOQ"), StatCard("TAUX DE VICTOIRE"), StatCard("KDA"), StatCard("CS / MIN"), StatCard("MORTS / PARTIE")]
        for index, card in enumerate(self.cards): cards.addWidget(card, 0, index)
        self.layout.addLayout(cards)
        recent_header = QHBoxLayout(); title = QLabel("Parties récentes"); title.setObjectName("SectionTitle"); recent_header.addWidget(title); recent_header.addStretch(); self.form = QLabel(); self.form.setObjectName("Muted"); recent_header.addWidget(self.form); self.layout.addLayout(recent_header)
        self.match_host = QWidget(); self.match_layout = QVBoxLayout(self.match_host); self.match_layout.setContentsMargins(0, 0, 0, 0); self.match_layout.setSpacing(8); self.layout.addWidget(self.match_host); self.layout.addStretch(); scroll.setWidget(content); root.addWidget(scroll); self.refresh()

    def _clear_matches(self):
        while self.match_layout.count():
            item = self.match_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def refresh(self):
        self._clear_matches()
        try:
            player, progress, matches = self.service.player(), self.service.progress(), self.service.matches()[:6]
        except Exception:
            self.match_layout.addWidget(EmptyState("Données locales indisponibles", "Les réglages restent accessibles ; aucun réseau n’est requis pour ouvrir l’application.")); return
        self.player_name.setText(player.riot_id); self.rank.setText(f"{player.rank}{f' • {player.lp} LP' if player.lp is not None else ''}")
        ranked_total = (player.ranked_wins or 0) + (player.ranked_losses or 0)
        ranked_record = "Classement W/L indisponible" if not ranked_total else f"{player.ranked_wins} V / {player.ranked_losses} D · {player.ranked_wins / ranked_total * 100:.1f}% WR"
        self.profile_meta.setText(f"Niveau {player.summoner_level or 'INDISPONIBLE'}  •  {ranked_record}  •  SoloQ  •  Local-first")
        self.profile_status.set_status(player.profile_status); self.profile_icon.load("profileicon", player.profile_icon_id, fallback=player.riot_id)
        values = [str(progress.total_games), "—" if progress.win_rate is None else f"{progress.win_rate:.1f}%", "—" if progress.kda is None else f"{progress.kda:.2f}", "—" if progress.cs_per_min is None else f"{progress.cs_per_min:.1f}", "—" if progress.deaths_per_match is None else f"{progress.deaths_per_match:.1f}"]
        for card, value in zip(self.cards, values): card.set_value(value)
        recent = matches[:5]; wins = sum(row.result == "WIN" for row in recent); self.form.setText("Forme récente  " + " ".join("V" if row.result == "WIN" else "D" for row in recent) + (f"  •  {wins}/{len(recent)} victoires" if recent else ""))
        if not matches:
            self.match_layout.addWidget(EmptyState("Aucune donnée SoloQ pour le compte actif", "1. Configurez le Riot ID  2. Ajoutez la clé dans Réglages  3. Synchronisez"))
        for match in matches:
            card = MatchCard(match, self.assets); card.opened.connect(self.open_match); self.match_layout.addWidget(card)
