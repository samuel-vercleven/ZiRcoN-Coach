from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from ui.player_coach import CoachingFocus


class CoachingCard(QFrame):
    """Readable, traceable single coaching focus."""

    def __init__(self, focus: CoachingFocus, compact: bool = False,
                 open_source: Callable[[], None] | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("CoachCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(6)

        heading = QLabel("À revoir" if compact else "Piste de coaching")
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)
        title = QLabel(focus.title)
        title.setObjectName("EventTitle")
        title.setWordWrap(True)
        layout.addWidget(title)
        observation = QLabel(f"Ce qu’on observe · {focus.observation}")
        observation.setObjectName("ContextLine")
        observation.setWordWrap(True)
        layout.addWidget(observation)
        why = QLabel(f"Pourquoi y revenir · {focus.why_review}")
        why.setObjectName("Muted")
        why.setWordWrap(True)
        layout.addWidget(why)
        action_title = QLabel("À tester la prochaine partie")
        action_title.setObjectName("CardTitle")
        layout.addWidget(action_title)
        experiment = QLabel(focus.next_game_experiment)
        experiment.setObjectName("ContextLine")
        experiment.setWordWrap(True)
        layout.addWidget(experiment)
        if focus.evidence:
            evidence_title = QLabel("Repères de cette partie")
            evidence_title.setObjectName("CardTitle")
            layout.addWidget(evidence_title)
            evidence = QLabel("  ·  ".join(focus.evidence))
            evidence.setObjectName("Muted")
            evidence.setWordWrap(True)
            layout.addWidget(evidence)
        if not compact:
            limitation = QLabel(focus.limitation)
            limitation.setObjectName("MicroLabel")
            limitation.setWordWrap(True)
            layout.addWidget(limitation)
            source = QLabel(f"Données : {focus.source}")
            source.setObjectName("MicroLabel")
            source.setWordWrap(True)
            layout.addWidget(source)
        if open_source is not None:
            action = QPushButton("Ouvrir l’analyse coach" if compact else "Voir les événements associés")
            action.setObjectName("GhostButton")
            action.setCursor(Qt.CursorShape.PointingHandCursor)
            action.clicked.connect(open_source)
            layout.addWidget(action)
