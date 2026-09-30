from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QWidget

from services.asset_service import AssetService
from ui.components.asset_icon import AssetIcon
from ui.components.status_badge import SeverityBadge, StatusBadge
from viewmodels import InsightViewModel


PLAYER_TITLES = {
    "DEATH": "Morts",
    "TEMPO": "Déplacements et rythme",
    "OBJECTIVES": "Objectifs",
    "RESETS": "Retours à la base",
    "BUILD": "Objets",
}


def player_insight_title(insight: InsightViewModel) -> str:
    return PLAYER_TITLES.get(insight.category, insight.title)


def player_insight_summary(insight: InsightViewModel) -> str:
    count = len(insight.events)
    summaries = {
        "DEATH": f"{count} moment(s) de mort à revoir, avec les repères disponibles autour de chacun.",
        "TEMPO": "Tes déplacements et ton rythme sont résumés par grandes périodes de la partie.",
        "OBJECTIVES": "Retrouve les objectifs de la partie et ce qui se passait autour de chacun.",
        "RESETS": "Revois tes retours à la base et la façon dont tu as repris la partie, sans jugement automatique.",
        "BUILD": "Retrouve les objets terminés pendant la partie. Ce récapitulatif ne dit pas qu’ils étaient le meilleur choix.",
    }
    return summaries.get(insight.category, "Les moments et repères disponibles pour cette partie.")


def _player_text(value: object) -> str:
    text = str(value or "")
    replacements = (
        ("Évidence Death Analyzer v11", "Repères autour de cette mort"),
        ("Mesures exactes par phase v17", "Résumé de cette période"),
        ("Build final Riot", "Objets en fin de partie"),
        ("Reset / shop", "Retour à la base"),
        ("Écarts relatifs — EXPERIMENTAL", "Écarts observés"),
        ("Écarts relatifs", "Écarts observés"),
        ("Intervalle de frames", "Délai observé"),
        ("Proximité joueur / adverse", "Distance entre les équipes"),
        ("Diff. Gold / XP / JCS / niveau", "Écart d’or, d’XP, de sbires jungle et de niveau"),
        ("Diff. entrée Gold / XP / JCS", "Écart à l’arrivée (or, XP et sbires jungle)"),
        ("Diff. ré-entrée Gold / XP / JCS", "Écart à la reprise (or, XP et sbires jungle)"),
        ("Production post-reset XP / JCS par min", "XP et sbires jungle gagnés par minute après le retour"),
        ("Production relative post-reset Gold / XP / JCS", "Écart par minute (or, XP et sbires jungle)"),
        ("Production après reset vs historique", "Ressources après la reprise, comparées à tes repères"),
        ("Gold avant / dépensé (proxy)", "Or avant le retour / dépense estimée"),
        ("Achats / ventes / annulations", "Objets achetés / vendus / annulés"),
        ("Évidence de contest", "Indices d’affrontement"),
        ("Évidence de trade", "Échange observé"),
        ("Séquence", "Déroulement"),
        ("Séquence v20 :", "Déroulement :"),
        ("v20 :", ""),
        ("Issue", "Résultat"),
        ("Jungle CS", "sbires jungle"),
        ("CS jungle", "sbires jungle"),
        ("CS", "sbires"),
        ("EXPERIMENTAL :", "À interpréter avec prudence :"),
        ("EXPERIMENTAL", "Estimation"),
        ("proxy de reset volontaire", "retour volontaire à la base"),
        ("proxy de reset", "retour à la base"),
        ("proxy", "estimation"),
        ("v11 context:", "Contexte observé :"),
        ("unspent Gold", "or non dépensé"),
        ("enemy jungler was the killer", "jungler adverse impliqué"),
        ("trade observed (enemy jungler killed)", "échange observé après une intervention du jungler adverse"),
        ("trade observed", "échange observé"),
        ("death chain size", "morts rapprochées"),
        ("severe death spiral", "série de morts marquée"),
        ("Gold", "or"),
        ("JCS", "sbires jungle"),
        ("reconstruction", "reconstitution"),
        ("EXACT", "complet"),
        ("PARTIAL", "partiel"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return re.sub(r"\bv\d+\b", "", text).strip()


class InsightCard(QFrame):
    """Concise analyzer support card used by the Overview."""

    def __init__(self, insight: InsightViewModel, parent=None):
        super().__init__(parent)
        self.setObjectName("InsightCard")
        layout = QVBoxLayout(self); layout.setContentsMargins(16, 14, 16, 14); layout.setSpacing(9)
        head = QHBoxLayout(); marker = QLabel(_insight_marker(insight.category)); marker.setObjectName('InsightMarker'); head.addWidget(marker)
        title = QLabel(player_insight_title(insight)); title.setObjectName("SectionTitle"); head.addWidget(title); head.addStretch(); head.addWidget(StatusBadge(insight.status)); layout.addLayout(head)
        summary = QLabel(player_insight_summary(insight)); summary.setWordWrap(True); summary.setObjectName("Muted"); layout.addWidget(summary)
        facts = QHBoxLayout(); events = QLabel(f"{len(insight.events)} moment(s) repéré(s)"); events.setObjectName('InsightFact'); facts.addWidget(events)
        findings = QLabel(f"{len(insight.findings)} piste(s) à revoir"); findings.setObjectName('InsightFact'); facts.addWidget(findings); facts.addStretch(); layout.addLayout(facts)


class AnalyzerEventCard(QFrame):
    """Structured event/phase projection; raw keys remain behind details."""

    def __init__(self, event: dict, assets: AssetService, game_version: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("EventCard")
        root = QVBoxLayout(self); root.setContentsMargins(16, 14, 16, 14); root.setSpacing(10)
        head = QHBoxLayout(); glyph = QLabel('●'); glyph.setObjectName('EventMarker'); head.addWidget(glyph); title_box = QVBoxLayout()
        title = QLabel(_player_text(event.get("title") or "Moment de la partie")); title.setObjectName("EventTitle"); title_box.addWidget(title)
        subtitle = QLabel(_player_text(event.get("subtitle") or "")); subtitle.setObjectName("Muted"); subtitle.setWordWrap(True); title_box.addWidget(subtitle)
        head.addLayout(title_box, 1); severity = str(event.get("severity") or "INFO")
        if severity != "INFO": head.addWidget(SeverityBadge(severity))
        head.addWidget(StatusBadge(str(event.get("status") or "UNKNOWN"))); root.addLayout(head)

        item_ids = [value for value in event.get("item_ids") or [] if value]
        if item_ids:
            strip = QHBoxLayout(); strip.setSpacing(5)
            for item_id in item_ids:
                icon = AssetIcon(assets, 32); icon.load("item", item_id, game_version); strip.addWidget(icon)
            strip.addStretch(); root.addLayout(strip)

        metrics = [value for value in event.get("metrics") or [] if isinstance(value, dict)]
        if metrics:
            grid = QGridLayout(); grid.setHorizontalSpacing(8); grid.setVerticalSpacing(8)
            for index, metric in enumerate(metrics):
                row, column = divmod(index, 3)
                cell = QFrame(); cell.setObjectName('MetricTile'); box = QVBoxLayout(cell); box.setContentsMargins(10, 8, 10, 8); box.setSpacing(3)
                label = QLabel(_player_text(metric.get("label") or "")); label.setObjectName("MicroLabel")
                value = QLabel(_player_text(metric.get("value") if metric.get("value") is not None else "—")); value.setObjectName("MetricValue"); value.setWordWrap(True)
                box.addWidget(label); box.addWidget(value); grid.addWidget(cell, row, column)
            root.addLayout(grid)

        context_values = [_player_text(value) for value in event.get("context") or []]
        if context_values:
            context_title = QLabel('Observations'); context_title.setObjectName('CardTitle'); root.addWidget(context_title)
            for value in context_values[:2]:
                context = QLabel(value); context.setObjectName("ContextLine"); context.setWordWrap(True); root.addWidget(context)
            if len(context_values) > 2:
                extra_button = QToolButton(); extra_button.setText(f"Voir {len(context_values) - 2} observation(s) supplémentaire(s)"); extra_button.setCheckable(True)
                extra_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon); extra_button.setArrowType(Qt.ArrowType.RightArrow); root.addWidget(extra_button, 0, Qt.AlignmentFlag.AlignLeft)
                extra = QLabel('\n'.join('• ' + value for value in context_values[2:])); extra.setObjectName('ContextLine'); extra.setWordWrap(True); extra.setVisible(False); root.addWidget(extra)
                extra_button.toggled.connect(extra.setVisible)
                extra_button.toggled.connect(lambda checked, target=extra_button: target.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow))

def _insight_marker(category: str) -> str:
    return {'DEATH': '✕', 'TEMPO': '↗', 'OBJECTIVES': '◆', 'RESETS': '↺', 'BUILD': '▣'}.get(category, '●')
