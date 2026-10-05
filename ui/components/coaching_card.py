from collections.abc import Callable
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QToolButton, QVBoxLayout, QWidget

from ui.player_coach import CoachingFocus


def _player_text(value: str) -> str:
    text = value
    for old, new in (
        ("proxy de reset volontaire", "retour volontaire à la base"),
        ("proxy de reset", "retour à la base"),
        ("proxy", "estimation"),
        ("référence historique", "tes parties précédentes"),
        ("indice historique", "repère comparatif"),
        ("composite relatif", "repère comparatif"),
        ("EXPÉRIMENTAL", "estimé"),
        ("pathing", "déplacements"),
    ):
        text = text.replace(old, new).replace(old.upper(), new)
    return re.sub(r"/100\b", "", re.sub(r"\bv\d+\b", "", text)).strip()


class CoachingCard(QFrame):
    """Readable, traceable single coaching focus."""

    def __init__(self, focus: CoachingFocus, compact: bool = False,
                 open_source: Callable[[], None] | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("CoachCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(6)

        heading = QLabel("À retenir" if compact else "Piste de coaching")
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)
        title = QLabel(focus.title)
        title.setObjectName("EventTitle")
        title.setWordWrap(True)
        layout.addWidget(title)
        observation = QLabel(_player_text(focus.observation))
        observation.setObjectName("CoachObservation")
        observation.setWordWrap(True)
        layout.addWidget(observation)
        action_title = QLabel("Ton prochain réflexe")
        action_title.setObjectName("CoachActionHeading")
        layout.addWidget(action_title)
        experiment = QLabel(_player_text(focus.next_game_experiment))
        experiment.setObjectName("CoachAction")
        experiment.setWordWrap(True)
        layout.addWidget(experiment)
        caution = QLabel('Une piste à tester, pas une explication certaine du résultat.'); caution.setObjectName('Muted'); caution.setWordWrap(True); layout.addWidget(caution)
        details = QWidget(); details.setObjectName('CoachEvidenceDetails'); detail_layout = QVBoxLayout(details); detail_layout.setContentsMargins(0, 6, 0, 6); detail_layout.setSpacing(8)
        for value in (focus.why_review, *focus.evidence, focus.limitation):
            label = QLabel(_player_text(value)); label.setObjectName('Muted'); label.setWordWrap(True); detail_layout.addWidget(label)
        layout.addWidget(details); details.hide()
        controls = QHBoxLayout()
        toggle = QToolButton(); toggle.setObjectName('CoachEvidenceToggle'); toggle.setText('Comprendre ce conseil'); toggle.setCheckable(True); toggle.setArrowType(Qt.ArrowType.RightArrow); toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        def reveal(checked):
            details.setVisible(checked); toggle.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
            toggle.setText('Masquer les explications' if checked else 'Comprendre ce conseil')
        toggle.toggled.connect(reveal); controls.addWidget(toggle); controls.addStretch()
        if open_source is not None:
            action = QPushButton("Ouvrir Coach" if compact else "Revoir les moments associés")
            action.setObjectName("GhostButton")
            action.setCursor(Qt.CursorShape.PointingHandCursor)
            action.clicked.connect(open_source)
            controls.addWidget(action)
        layout.addLayout(controls)
