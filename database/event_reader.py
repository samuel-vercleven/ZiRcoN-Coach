import json

from database.database import (
    get_connection,
    get_match_participant_ids,
    get_frame_near_timestamp,
)


def get_match_context(match_id, puuid):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT raw_json
        FROM matches
        WHERE match_id = ?
        """,
        (match_id,),
    )

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    match = json.loads(row[0])

    participants = (
        match.get("info", {})
        .get("participants", [])
    )

    players = {}

    my_player = None

    for player in participants:
        participant_id = player.get(
            "participantId"
        )

        players[participant_id] = {
            "participant_id": participant_id,
            "puuid": player.get("puuid"),
            "champion": player.get(
                "championName"
            ),
            "riot_name": player.get(
                "riotIdGameName"
            ),
            "team_id": player.get("teamId"),
            "position": (
                player.get("teamPosition")
                or player.get("individualPosition")
            ),
        }

        if player.get("puuid") == puuid:
            my_player = players[participant_id]

    ids = get_match_participant_ids(
        match_id,
        puuid,
    )

    if not my_player or not ids:
        return None

    return {
        "match_id": match_id,
        "my_player": my_player,
        "my_participant_id": ids["player_id"],
        "opponent_participant_id": ids["opponent_id"],
        "my_team_id": my_player["team_id"],
        "position": ids["position"],
        "players": players,
    }


def get_raw_events_in_window(
    match_id,
    start_min,
    end_min,
):
    start_ms = start_min * 60 * 1000
    end_ms = end_min * 60 * 1000

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT raw_json
        FROM timeline_events
        WHERE match_id = ?
          AND timestamp >= ?
          AND timestamp < ?
        ORDER BY timestamp ASC
        """,
        (
            match_id,
            start_ms,
            end_ms,
        ),
    )

    rows = cursor.fetchall()
    connection.close()

    events = []

    for row in rows:
        if not row or not row[0]:
            continue

        try:
            events.append(
                json.loads(row[0])
            )
        except (
            TypeError,
            json.JSONDecodeError,
        ):
            continue

    return events


def _player_label(
    participant_id,
    context,
):
    if participant_id in (None, 0):
        return "Inconnu"

    player = context["players"].get(
        participant_id
    )

    if not player:
        return (
            f"Participant {participant_id}"
        )

    champion = (
        player["champion"]
        or f"Participant {participant_id}"
    )

    if (
        participant_id
        == context["my_participant_id"]
    ):
        return f"TOI ({champion})"

    if (
        participant_id
        == context[
            "opponent_participant_id"
        ]
    ):
        return (
            f"JGL ADVERSE ({champion})"
        )

    return champion


def _objective_name(event):
    monster = str(
        event.get("monsterType", "")
    ).upper()

    subtype = str(
        event.get("monsterSubType", "")
    ).upper()

    text = f"{monster} {subtype}"

    if "DRAGON" in text:
        if subtype:
            return f"Dragon ({subtype})"
        return "Dragon"

    if (
        "RIFTHERALD" in text
        or "HERALD" in text
    ):
        return "Héraut"

    if (
        "HORDE" in text
        or "GRUB" in text
    ):
        return "Void Grub"

    if "BARON" in text:
        return "Baron"

    return monster or "Monstre épique"


def _team_from_killer(
    event,
    context,
):
    killer_team = event.get(
        "killerTeamId"
    )

    if killer_team is not None:
        return killer_team

    killer_id = event.get(
        "killerId"
    )

    player = context["players"].get(
        killer_id
    )

    if player:
        return player["team_id"]

    return None


def get_detailed_window_events(
    match_id,
    puuid,
    start_min,
    end_min,
):
    context = get_match_context(
        match_id,
        puuid,
    )

    if not context:
        return []

    raw_events = get_raw_events_in_window(
        match_id,
        start_min,
        end_min,
    )

    my_id = context[
        "my_participant_id"
    ]

    enemy_jungle_id = context[
        "opponent_participant_id"
    ]

    my_team_id = context[
        "my_team_id"
    ]

    normalized = []

    for event in raw_events:
        event_type = event.get("type")
        timestamp = event.get(
            "timestamp",
            0,
        )

        # ====================================================
        # KILLS / DEATHS / ASSISTS
        # ====================================================

        if event_type == "CHAMPION_KILL":
            killer_id = event.get(
                "killerId"
            )

            victim_id = event.get(
                "victimId"
            )

            assists = (
                event.get(
                    "assistingParticipantIds",
                    [],
                )
                or []
            )

            relevant = (
                my_id in (
                    killer_id,
                    victim_id,
                )
                or my_id in assists
                or enemy_jungle_id in (
                    killer_id,
                    victim_id,
                )
                or enemy_jungle_id in assists
            )

            if not relevant:
                continue

            if victim_id == my_id:
                kind = "PLAYER_DEATH"
                importance = 100
                description = (
                    "Mort contre "
                    f"{_player_label(killer_id, context)}"
                )

            elif killer_id == my_id:
                kind = "PLAYER_KILL"
                importance = 90
                description = (
                    "Kill sur "
                    f"{_player_label(victim_id, context)}"
                )

            elif my_id in assists:
                kind = "PLAYER_ASSIST"
                importance = 70
                description = (
                    "Assist sur "
                    f"{_player_label(victim_id, context)}"
                )

            elif killer_id == enemy_jungle_id:
                kind = "ENEMY_JUNGLE_KILL"
                importance = 85
                description = (
                    "Jungler adverse : kill sur "
                    f"{_player_label(victim_id, context)}"
                )

            elif victim_id == enemy_jungle_id:
                kind = "ENEMY_JUNGLE_DEATH"
                importance = 75
                description = (
                    "Jungler adverse mort contre "
                    f"{_player_label(killer_id, context)}"
                )

            else:
                kind = "ENEMY_JUNGLE_ASSIST"
                importance = 55
                description = (
                    "Jungler adverse impliqué dans un kill"
                )

            normalized.append({
                "timestamp": timestamp,
                "kind": kind,
                "importance": importance,
                "description": description,
                "raw": event,
            })

        # ====================================================
        # OBJECTIFS
        # ====================================================

        elif event_type == "ELITE_MONSTER_KILL":
            objective = _objective_name(
                event
            )

            killer_team = _team_from_killer(
                event,
                context,
            )

            if killer_team == my_team_id:
                side = "alliée"
                importance = 85
            elif killer_team is None:
                side = "inconnue"
                importance = 60
            else:
                side = "adverse"
                importance = 90

            normalized.append({
                "timestamp": timestamp,
                "kind": "OBJECTIVE",
                "importance": importance,
                "description": (
                    f"{objective} pris par l'équipe {side}"
                ),
                "raw": event,
            })

        # ====================================================
        # TOURS
        # ====================================================

        elif event_type == "BUILDING_KILL":
            building_type = str(
                event.get(
                    "buildingType",
                    "",
                )
            ).upper()

            if "TOWER" not in building_type:
                continue

            destroyed_team = event.get(
                "teamId"
            )

            if destroyed_team is None:
                side = "inconnue"

            elif destroyed_team == my_team_id:
                side = "adverse"

            else:
                side = "alliée"

            normalized.append({
                "timestamp": timestamp,
                "kind": "TOWER",
                "importance": 65,
                "description": (
                    f"Tour détruite par l'équipe {side}"
                ),
                "raw": event,
            })

        # ====================================================
        # PLAQUES
        # ====================================================

        elif event_type == "TURRET_PLATE_DESTROYED":
            destroyed_team = event.get(
                "teamId"
            )

            if destroyed_team == my_team_id:
                side = "adverse"
            elif destroyed_team is None:
                side = "inconnue"
            else:
                side = "alliée"

            normalized.append({
                "timestamp": timestamp,
                "kind": "PLATE",
                "importance": 45,
                "description": (
                    "Plaque de tour prise par "
                    f"l'équipe {side}"
                ),
                "raw": event,
            })

        # ====================================================
        # ITEMS DU JOUEUR / JGL ADVERSE
        # ====================================================

        elif event_type in (
            "ITEM_PURCHASED",
            "ITEM_SOLD",
            "ITEM_UNDO",
        ):
            participant_id = event.get(
                "participantId"
            )

            if participant_id not in (
                my_id,
                enemy_jungle_id,
            ):
                continue

            who = _player_label(
                participant_id,
                context,
            )

            item_id = event.get(
                "itemId"
            )

            if event_type == "ITEM_PURCHASED":
                action = "achète"

            elif event_type == "ITEM_SOLD":
                action = "vend"

            else:
                action = "annule achat"

            normalized.append({
                "timestamp": timestamp,
                "kind": "ITEM",
                "importance": 35,
                "description": (
                    f"{who} {action} item {item_id}"
                ),
                "raw": event,
            })

        # ====================================================
        # LEVEL UP
        # ====================================================

        elif event_type == "LEVEL_UP":
            participant_id = event.get(
                "participantId"
            )

            if participant_id not in (
                my_id,
                enemy_jungle_id,
            ):
                continue

            level = event.get("level")

            normalized.append({
                "timestamp": timestamp,
                "kind": "LEVEL",
                "importance": 25,
                "description": (
                    f"{_player_label(participant_id, context)} "
                    f"passe niveau {level}"
                ),
                "raw": event,
            })

    normalized.sort(
        key=lambda row: (
            row["timestamp"],
            -row["importance"],
        )
    )

    return normalized


# ============================================================
# TRAJECTOIRE MINUTE PAR MINUTE
# ============================================================

def get_minute_trajectory(
    match_id,
    puuid,
    start_min,
    end_min,
):
    """
    Retourne les snapshots minute par minute du joueur et du
    jungler adverse. Permet de localiser précisément à quelle
    minute un écart de Gold / CS / XP apparaît.
    """
    context = get_match_context(
        match_id,
        puuid,
    )

    if not context:
        return []

    player_id = context[
        "my_participant_id"
    ]

    opponent_id = context[
        "opponent_participant_id"
    ]

    if opponent_id is None:
        return []

    trajectory = []

    for minute in range(
        start_min,
        end_min + 1,
    ):
        timestamp = minute * 60 * 1000

        player = get_frame_near_timestamp(
            match_id,
            player_id,
            timestamp,
        )

        opponent = get_frame_near_timestamp(
            match_id,
            opponent_id,
            timestamp,
        )

        if not player or not opponent:
            continue

        trajectory.append({
            "minute": minute,

            "player_gold": player["gold"],
            "opponent_gold": opponent["gold"],
            "gold_diff": (
                player["gold"]
                - opponent["gold"]
            ),

            "player_cs": player["cs"],
            "opponent_cs": opponent["cs"],
            "cs_diff": (
                player["cs"]
                - opponent["cs"]
            ),

            "player_xp": player["xp"],
            "opponent_xp": opponent["xp"],
            "xp_diff": (
                player["xp"]
                - opponent["xp"]
            ),

            "player_level": player["level"],
            "opponent_level": opponent["level"],
            "level_diff": (
                player["level"]
                - opponent["level"]
            ),
        })

    # Calcul du changement minute par minute.
    previous = None

    for row in trajectory:
        if previous is None:
            row["gold_diff_change"] = None
            row["cs_diff_change"] = None
            row["xp_diff_change"] = None
        else:
            row["gold_diff_change"] = (
                row["gold_diff"]
                - previous["gold_diff"]
            )

            row["cs_diff_change"] = (
                row["cs_diff"]
                - previous["cs_diff"]
            )

            row["xp_diff_change"] = (
                row["xp_diff"]
                - previous["xp_diff"]
            )

        previous = row

    return trajectory
