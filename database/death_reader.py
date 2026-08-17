import json

from database.database import (
    get_connection,
    get_match_participant_ids,
)

from database.event_reader import (
    get_match_context,
)


# ============================================================
# MATCHS À ANALYSER
# ============================================================

def get_role_match_ids(
    puuid,
    position="JUNGLE",
    queue_id=420,
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            m.match_id,
            m.game_creation,
            m.game_duration,
            p.champion_name,
            p.win
        FROM participants p
        JOIN matches m
            ON m.match_id = p.match_id
        WHERE p.puuid = ?
          AND p.position = ?
          AND m.queue_id = ?
        ORDER BY m.game_creation DESC
        """,
        (
            puuid,
            position,
            queue_id,
        ),
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "match_id": row[0],
            "game_creation": row[1],
            "game_duration": row[2],
            "champion": row[3],
            "win": bool(row[4]),
        }
        for row in rows
    ]


# ============================================================
# FRAME HELPERS
# ============================================================

def _frame_row_to_dict(row):
    if not row:
        return None

    return {
        "timestamp": row[0],
        "participant_id": row[1],
        "gold": row[2],
        "current_gold": row[3],
        "level": row[4],
        "xp": row[5],
        "lane_cs": row[6],
        "jungle_cs": row[7],
        "cs": (
            (row[6] or 0)
            + (row[7] or 0)
        ),
        "x": row[8],
        "y": row[9],
    }


def get_frame_before_or_at(
    match_id,
    participant_id,
    timestamp,
):
    """
    Dernière frame réellement disponible avant ou au timestamp.
    Contrairement à une recherche 'nearest', elle ne peut pas
    prendre accidentellement une frame future.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            timestamp,
            participant_id,
            total_gold,
            current_gold,
            level,
            xp,
            minions_killed,
            jungle_minions_killed,
            position_x,
            position_y
        FROM timeline_frames
        WHERE match_id = ?
          AND participant_id = ?
          AND timestamp <= ?
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (
            match_id,
            participant_id,
            timestamp,
        ),
    )

    row = cursor.fetchone()
    connection.close()

    return _frame_row_to_dict(
        row
    )


def get_frame_after_or_at(
    match_id,
    participant_id,
    timestamp,
):
    """
    Première frame réellement disponible après ou au timestamp.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            timestamp,
            participant_id,
            total_gold,
            current_gold,
            level,
            xp,
            minions_killed,
            jungle_minions_killed,
            position_x,
            position_y
        FROM timeline_frames
        WHERE match_id = ?
          AND participant_id = ?
          AND timestamp >= ?
        ORDER BY timestamp ASC
        LIMIT 1
        """,
        (
            match_id,
            participant_id,
            timestamp,
        ),
    )

    row = cursor.fetchone()
    connection.close()

    return _frame_row_to_dict(
        row
    )


def get_relative_snapshot_from_frames(
    player_frame,
    opponent_frame,
):
    if not player_frame or not opponent_frame:
        return None

    return {
        "player_timestamp": player_frame[
            "timestamp"
        ],
        "opponent_timestamp": opponent_frame[
            "timestamp"
        ],
        "player": player_frame,
        "opponent": opponent_frame,

        "gold_diff": (
            player_frame["gold"]
            - opponent_frame["gold"]
        ),

        "current_gold_diff": (
            player_frame["current_gold"]
            - opponent_frame["current_gold"]
        ),

        "cs_diff": (
            player_frame["cs"]
            - opponent_frame["cs"]
        ),

        "xp_diff": (
            player_frame["xp"]
            - opponent_frame["xp"]
        ),

        "level_diff": (
            player_frame["level"]
            - opponent_frame["level"]
        ),
    }




def get_frame_strictly_after(
    match_id,
    participant_id,
    timestamp,
):
    """
    Première frame STRICTEMENT après le timestamp.

    Utile pour encadrer une mort :
        frame précédente < mort < frame suivante

    Cela évite qu'une mort à 19:00 utilise également la frame
    19:00 comme frame "après".
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            timestamp,
            participant_id,
            total_gold,
            current_gold,
            level,
            xp,
            minions_killed,
            jungle_minions_killed,
            position_x,
            position_y
        FROM timeline_frames
        WHERE match_id = ?
          AND participant_id = ?
          AND timestamp > ?
        ORDER BY timestamp ASC
        LIMIT 1
        """,
        (
            match_id,
            participant_id,
            timestamp,
        ),
    )

    row = cursor.fetchone()
    connection.close()

    return _frame_row_to_dict(
        row
    )


def get_relative_snapshot_strictly_after(
    match_id,
    puuid,
    timestamp,
):
    ids = get_match_participant_ids(
        match_id,
        puuid,
    )

    if not ids:
        return None

    player_id = ids["player_id"]
    opponent_id = ids["opponent_id"]

    if opponent_id is None:
        return None

    player_frame = get_frame_strictly_after(
        match_id,
        player_id,
        timestamp,
    )

    opponent_frame = get_frame_strictly_after(
        match_id,
        opponent_id,
        timestamp,
    )

    result = get_relative_snapshot_from_frames(
        player_frame,
        opponent_frame,
    )

    if result:
        result[
            "requested_timestamp"
        ] = timestamp

    return result


def get_relative_snapshot_before_or_at(
    match_id,
    puuid,
    timestamp,
):
    ids = get_match_participant_ids(
        match_id,
        puuid,
    )

    if not ids:
        return None

    player_id = ids["player_id"]
    opponent_id = ids["opponent_id"]

    if opponent_id is None:
        return None

    player_frame = get_frame_before_or_at(
        match_id,
        player_id,
        timestamp,
    )

    opponent_frame = get_frame_before_or_at(
        match_id,
        opponent_id,
        timestamp,
    )

    result = get_relative_snapshot_from_frames(
        player_frame,
        opponent_frame,
    )

    if result:
        result[
            "requested_timestamp"
        ] = timestamp

    return result


def get_relative_snapshot_after_or_at(
    match_id,
    puuid,
    timestamp,
):
    ids = get_match_participant_ids(
        match_id,
        puuid,
    )

    if not ids:
        return None

    player_id = ids["player_id"]
    opponent_id = ids["opponent_id"]

    if opponent_id is None:
        return None

    player_frame = get_frame_after_or_at(
        match_id,
        player_id,
        timestamp,
    )

    opponent_frame = get_frame_after_or_at(
        match_id,
        opponent_id,
        timestamp,
    )

    result = get_relative_snapshot_from_frames(
        player_frame,
        opponent_frame,
    )

    if result:
        result[
            "requested_timestamp"
        ] = timestamp

    return result


# ============================================================
# DEATH EVENTS
# ============================================================

def get_player_death_events(
    match_id,
    puuid,
):
    context = get_match_context(
        match_id,
        puuid,
    )

    if not context:
        return []

    player_id = context[
        "my_participant_id"
    ]

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            timestamp,
            killer_id,
            victim_id,
            position_x,
            position_y,
            raw_json
        FROM timeline_events
        WHERE match_id = ?
          AND event_type = 'CHAMPION_KILL'
          AND victim_id = ?
        ORDER BY timestamp ASC
        """,
        (
            match_id,
            player_id,
        ),
    )

    rows = cursor.fetchall()
    connection.close()

    deaths = []

    for row in rows:
        raw = {}

        if row[5]:
            try:
                raw = json.loads(
                    row[5]
                )
            except (
                TypeError,
                json.JSONDecodeError,
            ):
                raw = {}

        killer_id = row[1]

        killer = context[
            "players"
        ].get(
            killer_id
        )

        deaths.append({
            "timestamp": row[0],
            "killer_id": killer_id,
            "victim_id": row[2],
            "x": row[3],
            "y": row[4],

            "killer_champion": (
                killer.get("champion")
                if killer
                else None
            ),

            "killer_position": (
                killer.get("position")
                if killer
                else None
            ),

            "killer_team_id": (
                killer.get("team_id")
                if killer
                else None
            ),

            "killed_by_enemy_jungler": (
                killer_id
                == context[
                    "opponent_participant_id"
                ]
            ),

            # Riot expose parfois ces champs selon la version.
            # On les conserve seulement lorsqu'ils existent.
            "bounty": raw.get(
                "bounty"
            ),
            "shutdown_bounty": raw.get(
                "shutdownBounty"
            ),
            "kill_streak_length": raw.get(
                "killStreakLength"
            ),

            "raw": raw,
        })

    return deaths


# ============================================================
# EVENTS
# ============================================================

def get_events_in_interval(
    match_id,
    start_timestamp,
    end_timestamp,
    event_types=None,
):
    connection = get_connection()
    cursor = connection.cursor()

    params = [
        match_id,
        start_timestamp,
        end_timestamp,
    ]

    type_clause = ""

    if event_types:
        placeholders = ",".join(
            "?"
            for _ in event_types
        )

        type_clause = (
            f" AND event_type IN "
            f"({placeholders})"
        )

        params.extend(
            event_types
        )

    cursor.execute(
        f"""
        SELECT raw_json
        FROM timeline_events
        WHERE match_id = ?
          AND timestamp >= ?
          AND timestamp <= ?
          {type_clause}
        ORDER BY timestamp ASC
        """,
        params,
    )

    rows = cursor.fetchall()
    connection.close()

    result = []

    for row in rows:
        if not row[0]:
            continue

        try:
            result.append(
                json.loads(
                    row[0]
                )
            )
        except (
            TypeError,
            json.JSONDecodeError,
        ):
            continue

    return result


def get_events_after_death(
    match_id,
    death_timestamp,
    seconds=90,
):
    return get_events_in_interval(
        match_id,
        death_timestamp,
        death_timestamp
        + seconds * 1000,
        event_types=(
            "CHAMPION_KILL",
            "ELITE_MONSTER_KILL",
            "BUILDING_KILL",
        ),
    )


def get_events_before_death(
    match_id,
    death_timestamp,
    seconds=90,
):
    return get_events_in_interval(
        match_id,
        death_timestamp
        - seconds * 1000,
        death_timestamp,
        event_types=(
            "CHAMPION_KILL",
            "ELITE_MONSTER_KILL",
            "BUILDING_KILL",
        ),
    )


def get_events_around_death(
    match_id,
    death_timestamp,
    before_seconds=12,
    after_seconds=12,
):
    return get_events_in_interval(
        match_id,
        death_timestamp
        - before_seconds * 1000,
        death_timestamp
        + after_seconds * 1000,
        event_types=(
            "CHAMPION_KILL",
        ),
    )
