"""Final-match scoreboard; presentation only, never an optimizer input."""
from html import escape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget, QSizePolicy

from ui.components.asset_icon import AssetIcon
from ui.player_labels import role_label


def shown(value):
    return '—' if value is None else str(value)


class Scoreboard(QFrame):
    def __init__(self, roster, assets, match, parent=None):
        super().__init__(parent)
        self.setObjectName('Scoreboard')
        self._row_layouts = []
        self._compact = None
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(8)
        teams = [[r for r in roster if r['is_enemy'] == enemy] for enemy in (False, True)]
        header = QHBoxLayout()
        for index, team in enumerate(teams):
            win = team[0].get('win') if team else None
            result = 'Victoire' if win == 1 else 'Défaite' if win == 0 else 'Résultat inconnu'
            totals = []
            for key in ('kills', 'deaths', 'assists'):
                totals.append(str(sum(r[key] for r in team)) if team and all(r[key] is not None for r in team) else '—')
            label = QLabel(f"{result}   {' / '.join(totals)}")
            label.setProperty('result', 'win' if win == 1 else 'loss' if win == 0 else '')
            if index:
                label.setAlignment(Qt.AlignmentFlag.AlignRight)
            header.addWidget(label, 1)
            if not index:
                title = QLabel(f"Classé en solo/duo · {match.duration_text}")
                title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                title.setObjectName('MatchChampion')
                header.addWidget(title, 1)
        root.addLayout(header)
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(4)
        order = {'TOP': 0, 'JUNGLE': 1, 'MIDDLE': 2, 'BOTTOM': 3, 'UTILITY': 4}
        for column, team in enumerate(teams):
            team = sorted(team, key=lambda r: order.get(r['position'], 9))
            total_kills = sum(r['kills'] for r in team) if team and all(r['kills'] is not None for r in team) else None
            for index, row in enumerate(team):
                grid.addWidget(self._player(row, assets, match.game_version, total_kills, bool(column)), index, column)
            grid.setColumnStretch(column, 1)
        root.addLayout(grid)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        compact = self.width() < 1050
        if compact == self._compact:
            return
        self._compact = compact
        for card, layout, parts, mirrored in self._row_layouts:
            for part in parts:
                layout.removeWidget(part)
            portrait, identity, stats, items = parts
            card.setFixedHeight(116 if compact else 80)
            if compact:
                layout.addWidget(portrait, 0, 2 if mirrored else 0)
                layout.addWidget(identity, 0, 0 if mirrored else 1, 1, 2)
                layout.addWidget(stats, 1, 1 if mirrored else 0, 1, 2)
                layout.addWidget(items, 1, 0 if mirrored else 2)
            else:
                for column, part in enumerate(reversed(parts) if mirrored else parts):
                    layout.addWidget(part, 0, column)
            for column in range(4):
                layout.setColumnStretch(column, 1 if column in (1, 2) else 0)

    def _player(self, row, assets, version, total_kills, mirrored):
        card = QFrame()
        card.setObjectName('ScoreboardRow')
        card.setProperty('isPlayer', row['is_player'])
        card.setFixedHeight(80)
        layout = QGridLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        portrait = AssetIcon(assets, 46)
        portrait.load('champion', row['champion'], version, row['champion'])
        identity_host = QWidget(); identity = QVBoxLayout(identity_host); identity.setContentsMargins(0, 0, 0, 0)
        name = QLabel(row.get('display_name') or row['champion'])
        name.setTextFormat(Qt.TextFormat.PlainText)
        name.setObjectName('ScoreboardName')
        name.setToolTip(name.text())
        name.setMaximumWidth(160)
        name.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        detail = QLabel(f"{row['champion']} · {role_label(row['position'])}")
        detail.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        detail.setToolTip(detail.text())
        detail.setObjectName('Muted')
        identity.addWidget(name)
        identity.addWidget(detail)
        stats_host = QWidget(); stats = QVBoxLayout(stats_host); stats.setContentsMargins(0, 0, 0, 0); stats.setSpacing(1)
        kda = QLabel(' / '.join(f'<span style="color:{color}">{escape(shown(row[key]))}</span>' for key, color in [('kills', '#40e6b0'), ('deaths', '#ff818b'), ('assists', '#efbf73')]))
        kda.setObjectName('MatchMetric')
        gold = '—' if row['gold'] is None else f"{row['gold']/1000:.1f}k"
        farm = QLabel(f"{shown(row['cs'])} CS · {gold} or")
        kp = '—' if total_kills is None or any(row[k] is None for k in ('kills', 'assists')) else f"{100*(row['kills']+row['assists'])/total_kills:.0f}%" if total_kills else '0%'
        vision = QLabel(f"{kp} participation · vision {shown(row['vision'])}")
        for label in (farm, vision):
            label.setObjectName('ScoreboardMeta')
        for label in (kda, farm, vision):
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stats.addWidget(label)
        items_host = QWidget(); items = QGridLayout(items_host); items.setContentsMargins(0, 0, 0, 0)
        items.setSpacing(3)
        inventory = list(row['items'])[:6]
        for index, item_id in enumerate(inventory):
            if not item_id:
                continue
            icon = AssetIcon(assets, 25)
            icon.load('item', item_id, version)
            items.addWidget(icon, index // 3, index % 3)
        if row.get('trinket'):
            trinket = AssetIcon(assets, 25)
            trinket.load('item', row['trinket'], version)
            items.addWidget(trinket, 0, 3)
        parts = (portrait, identity_host, stats_host, items_host)
        self._row_layouts.append((card, layout, parts, mirrored))
        for column, part in enumerate(reversed(parts) if mirrored else parts):
            layout.addWidget(part, 0, column)
        return card
