from collections.abc import Callable
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

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
        observation = QLabel(f"Ce qu’on observe · {_player_text(focus.observation)}")
        observation.setObjectName("ContextLine")
        observation.setWordWrap(True)
        layout.addWidget(observation)
        why = QLabel(f"Pourquoi y revenir · {_player_text(focus.why_review)}")
        why.setObjectName("Muted")
        why.setWordWrap(True)
        layout.addWidget(why)
        action_title = QLabel("À tester la prochaine partie")
        action_title.setObjectName("CardTitle")
        layout.addWidget(action_title)
        experiment = QLabel(_player_text(focus.next_game_experiment))
        experiment.setObjectName("ContextLine")
        experiment.setWordWrap(True)
        layout.addWidget(experiment)
        if focus.evidence:
            evidence_title = QLabel("Repères de cette partie")
            evidence_title.setObjectName("CardTitle")
            layout.addWidget(evidence_title)
            evidence = QLabel("  ·  ".join(_player_text(value) for value in focus.evidence))
            evidence.setObjectName("Muted")
            evidence.setWordWrap(True)
            layout.addWidget(evidence)
        if not compact:
            limitation = QLabel(_player_text(focus.limitation))
            limitation.setObjectName("MicroLabel")
            limitation.setWordWrap(True)
            layout.addWidget(limitation)
        if open_source is not None:
            action = QPushButton("Ouvrir Coach" if compact else "Revoir les moments associés")
            action.setObjectName("GhostButton")
            action.setCursor(Qt.CursorShape.PointingHandCursor)
            action.clicked.connect(open_source)
            layout.addWidget(action)
