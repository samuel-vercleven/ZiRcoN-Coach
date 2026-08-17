from database.event_reader import (
    get_detailed_window_events,
    get_minute_trajectory,
)

from analysis.coaching_engine import (
    find_critical_window,
)


def format_timestamp(timestamp_ms):
    total_seconds = max(
        0,
        int(timestamp_ms / 1000),
    )

    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return f"{minutes:02d}:{seconds:02d}"


def _find_event_row(
    event_dataset,
    match_id,
    start_min,
    end_min,
):
    for row in event_dataset:
        if (
            row["match_id"] == match_id
            and row["start_min"] == start_min
            and row["end_min"] == end_min
        ):
            return row

    return None


def _build_evidence(row, detailed_events):
    evidence = []

    if row is None:
        return evidence

    # ========================================================
    # PREUVES PERSONNELLES
    # ========================================================

    if row["deaths"] >= 2:
        evidence.append({
            "type": "PERSONAL",
            "priority": 100,
            "text": (
                f"{row['deaths']} morts dans la fenêtre : "
                "forte perte potentielle de tempo."
            ),
        })

    elif row["deaths"] >= 1:
        evidence.append({
            "type": "PERSONAL",
            "priority": 75,
            "text": (
                f"{row['deaths']} mort dans la fenêtre."
            ),
        })

    if row["deaths_before_objective"] >= 1:
        evidence.append({
            "type": "PERSONAL",
            "priority": 95,
            "text": (
                f"{row['deaths_before_objective']} mort(s) "
                "moins de 60 s avant un objectif majeur."
            ),
        })

    if row["gold_diff_change"] <= -500:
        evidence.append({
            "type": "PERSONAL",
            "priority": 90,
            "text": (
                "Très forte dégradation relative en gold : "
                f"{row['gold_diff_change']:+.0f}."
            ),
        })

    elif row["gold_diff_change"] <= -250:
        evidence.append({
            "type": "PERSONAL",
            "priority": 70,
            "text": (
                "Dégradation relative en gold : "
                f"{row['gold_diff_change']:+.0f}."
            ),
        })

    if row["xp_diff_change"] <= -700:
        evidence.append({
            "type": "PERSONAL",
            "priority": 90,
            "text": (
                "Très forte perte d'XP relative : "
                f"{row['xp_diff_change']:+.0f}."
            ),
        })

    elif row["xp_diff_change"] <= -350:
        evidence.append({
            "type": "PERSONAL",
            "priority": 70,
            "text": (
                "Perte d'XP relative : "
                f"{row['xp_diff_change']:+.0f}."
            ),
        })

    if row["cs_diff_change"] <= -10:
        evidence.append({
            "type": "PERSONAL",
            "priority": 85,
            "text": (
                "Perte nette de rythme de farm relatif : "
                f"{row['cs_diff_change']:+.1f} CS."
            ),
        })

    elif row["cs_diff_change"] <= -5:
        evidence.append({
            "type": "PERSONAL",
            "priority": 65,
            "text": (
                "Farm relatif en baisse : "
                f"{row['cs_diff_change']:+.1f} CS."
            ),
        })

    # ========================================================
    # CONTEXTE DE PARTIE
    # ========================================================

    enemy_kills = sum(
        1
        for event in detailed_events
        if event["kind"] == "ENEMY_JUNGLE_KILL"
    )

    player_kills = sum(
        1
        for event in detailed_events
        if event["kind"] == "PLAYER_KILL"
    )

    if enemy_kills > player_kills:
        evidence.append({
            "type": "CONTEXT",
            "priority": 60,
            "text": (
                "Le jungler adverse génère davantage de kills "
                f"dans cette fenêtre ({enemy_kills} contre "
                f"{player_kills} kill personnel détecté)."
            ),
        })

    adverse_objectives = sum(
        1
        for event in detailed_events
        if (
            event["kind"] == "OBJECTIVE"
            and "adverse" in event["description"]
        )
    )

    allied_objectives = sum(
        1
        for event in detailed_events
        if (
            event["kind"] == "OBJECTIVE"
            and "alliée" in event["description"]
        )
    )

    if adverse_objectives > allied_objectives:
        evidence.append({
            "type": "CONTEXT",
            "priority": 55,
            "text": (
                "L'équipe adverse prend davantage d'objectifs "
                f"majeurs dans la fenêtre "
                f"({adverse_objectives} contre {allied_objectives})."
            ),
        })

    evidence.sort(
        key=lambda item: item["priority"],
        reverse=True,
    )

    return evidence


def build_critical_window_report(
    event_dataset,
    analyses,
    match_id,
    puuid,
    max_events=14,
):
    critical = find_critical_window(
        analyses
    )

    if critical is None:
        return (
            "Aucune fenêtre critique disponible."
        )

    start_min = critical["start_min"]
    end_min = critical["end_min"]

    row = _find_event_row(
        event_dataset,
        match_id,
        start_min,
        end_min,
    )

    detailed_events = (
        get_detailed_window_events(
            match_id,
            puuid,
            start_min,
            end_min,
        )
    )

    evidence = _build_evidence(
        row,
        detailed_events,
    )

    lines = []

    lines.append(
        "================================"
    )

    lines.append(
        "EXPLICATION DE LA FENÊTRE CRITIQUE"
    )

    lines.append(
        "================================"
    )

    lines.append("")

    lines.append(
        f"Fenêtre : {start_min}-{end_min} min"
    )

    lines.append(
        f"Score personnel : "
        f"{critical['personal_score']:.0f}/100 "
        f"({critical['severity']})"
    )

    if row is not None:
        lines.append("")

        lines.append(
            "Évolution relative face au jungler adverse :"
        )

        lines.append(
            f"  Gold : "
            f"{row['gold_diff_change']:+.0f}"
        )

        lines.append(
            f"  CS   : "
            f"{row['cs_diff_change']:+.1f}"
        )

        lines.append(
            f"  XP   : "
            f"{row['xp_diff_change']:+.0f}"
        )

        lines.append("")

        lines.append(
            "Production personnelle dans la fenêtre :"
        )

        lines.append(
            f"  Gold gagné : "
            f"{row['gold_gained']:.0f}"
        )

        lines.append(
            f"  CS gagnés  : "
            f"{row['cs_gained']:.1f}"
        )

        lines.append(
            f"  XP gagnée  : "
            f"{row['xp_gained']:.0f}"
        )

        lines.append(
            f"  K/D/A      : "
            f"{row['kills']} / "
            f"{row['deaths']} / "
            f"{row['assists']}"
        )

        # Le changement relatif permet de reconstruire
        # la production du jungler adverse :
        # diff_change = gain_joueur - gain_adversaire.
        opponent_gold_gained = (
            row["gold_gained"]
            - row["gold_diff_change"]
        )

        opponent_cs_gained = (
            row["cs_gained"]
            - row["cs_diff_change"]
        )

        opponent_xp_gained = (
            row["xp_gained"]
            - row["xp_diff_change"]
        )

        lines.append("")
        lines.append(
            "Production comparée sur la fenêtre :"
        )

        lines.append(
            f"  Gold  : toi {row['gold_gained']:.0f} | "
            f"JGL adverse {opponent_gold_gained:.0f}"
        )

        lines.append(
            f"  CS    : toi {row['cs_gained']:.1f} | "
            f"JGL adverse {opponent_cs_gained:.1f}"
        )

        lines.append(
            f"  XP    : toi {row['xp_gained']:.0f} | "
            f"JGL adverse {opponent_xp_gained:.0f}"
        )

    # ========================================================
    # TRAJECTOIRE MINUTE PAR MINUTE
    # ========================================================

    trajectory = get_minute_trajectory(
        match_id,
        puuid,
        start_min,
        end_min,
    )

    if trajectory:
        lines.append("")
        lines.append(
            "Trajectoire relative minute par minute :"
        )

        lines.append(
            "  Min | Gold diff | CS diff | XP diff | Niv."
        )

        for point in trajectory:
            lines.append(
                f"  {point['minute']:>3} | "
                f"{point['gold_diff']:+9.0f} | "
                f"{point['cs_diff']:+7.1f} | "
                f"{point['xp_diff']:+7.0f} | "
                f"{point['level_diff']:+3d}"
            )

        # Minute où l'XP relative se dégrade le plus.
        changes = [
            point
            for point in trajectory
            if point["xp_diff_change"] is not None
        ]

        if changes:
            worst_xp = min(
                changes,
                key=lambda point:
                    point["xp_diff_change"],
            )

            worst_gold = min(
                changes,
                key=lambda point:
                    point["gold_diff_change"],
            )

            lines.append("")
            lines.append(
                "Ruptures les plus fortes :"
            )

            lines.append(
                f"  XP : {worst_xp['minute'] - 1}-"
                f"{worst_xp['minute']} min "
                f"({worst_xp['xp_diff_change']:+.0f} relatif)"
            )

            lines.append(
                f"  Gold : {worst_gold['minute'] - 1}-"
                f"{worst_gold['minute']} min "
                f"({worst_gold['gold_diff_change']:+.0f} relatif)"
            )

    if evidence:
        lines.append("")
        lines.append(
            "Éléments observés "
            "(associations, pas causalité prouvée) :"
        )

        for item in evidence[:6]:
            prefix = (
                "PERSONNEL"
                if item["type"] == "PERSONAL"
                else "CONTEXTE"
            )

            lines.append(
                f"  - [{prefix}] "
                f"{item['text']}"
            )

    lines.append("")
    lines.append(
        "Chronologie utile :"
    )

    important_events = sorted(
        detailed_events,
        key=lambda event: (
            -event["importance"],
            event["timestamp"],
        ),
    )[:max_events]

    important_events.sort(
        key=lambda event:
            event["timestamp"]
    )

    if not important_events:
        lines.append(
            "  Aucun événement détaillé pertinent détecté."
        )

    else:
        for event in important_events:
            lines.append(
                f"  {format_timestamp(event['timestamp'])} | "
                f"{event['description']}"
            )

    lines.append("")
    lines.append(
        "Interprétation : le coach signale ici "
        "les événements compatibles avec la perte de tempo. "
        "Il ne transforme pas automatiquement une corrélation "
        "en cause certaine."
    )

    return "\n".join(lines)
