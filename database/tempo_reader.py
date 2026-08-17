import json
from collections import defaultdict

from database.database import get_connection


SQL_CHUNK_SIZE = 250

RELEVANT_EVENT_TYPES = (
    "CHAMPION_KILL",
    "ELITE_MONSTER_KILL",
    "BUILDING_KILL",
    "TURRET_PLATE_DESTROYED",
    "ITEM_PURCHASED",
    "ITEM_SOLD",
    "ITEM_UNDO",
    "LEVEL_UP",
)


def ensure_tempo_indexes():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_tempo_frames_match_participant_timestamp
        ON timeline_frames (
            match_id,
            participant_id,
            timestamp
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_tempo_events_match_timestamp_type
        ON timeline_events (
            match_id,
            timestamp,
            event_type
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_tempo_participants_profile
        ON participants (
            puuid,
            position,
            match_id
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_tempo_matches_queue_creation
        ON matches (
            queue_id,
            game_creation
        )
    """)

    connection.commit()
    connection.close()


def _chunks(values, size=SQL_CHUNK_SIZE):
    values = list(values)

    for index in range(
        0,
        len(values),
        size,
    ):
        yield values[
            index:index + size
        ]


def _position_of(player):
    return (
        player.get("teamPosition")
        or player.get("individualPosition")
        or ""
    )


def _build_match_meta(
    match_id,
    game_creation,
    game_duration,
    champion,
    win,
    raw_json,
    puuid,
    position,
):
    try:
        match = json.loads(raw_json)
    except Exception:
        return None

    participants = (
        match.get("info", {})
        .get("participants", [])
    )

    my_player = None

    for player in participants:
        if player.get("puuid") == puuid:
            my_player = player
            break

    if not my_player:
        return None

    my_id = my_player.get("participantId")
    my_team_id = my_player.get("teamId")
    my_position = (
        _position_of(my_player)
        or position
    )

    opponent = None

    for player in participants:
        if (
            player.get("teamId") != my_team_id
            and _position_of(player) == my_position
        ):
            opponent = player
            break

    if opponent is None:
        for player in participants:
            if (
                player.get("teamId") != my_team_id
                and _position_of(player) == position
            ):
                opponent = player
                break

    if opponent is None:
        return None

    players = {}

    for player in participants:
        participant_id = player.get("participantId")

        if participant_id is None:
            continue

        players[participant_id] = {
            "participant_id": participant_id,
            "team_id": player.get("teamId"),
            "position": _position_of(player),
            "champion": player.get("championName"),
            "puuid": player.get("puuid"),
        }

    return {
        "match_id": match_id,
        "game_creation": game_creation or 0,
        "game_duration": game_duration or 0,
        "champion": champion,
        "win": bool(win),
        "my_participant_id": my_id,
        "opponent_participant_id": opponent.get("participantId"),
        "my_team_id": my_team_id,
        "opponent_team_id": opponent.get("teamId"),
        "opponent_champion": opponent.get("championName"),
        "players": players,
    }


def _frame_to_dict(row):
    return {
        "timestamp": row[1],
        "participant_id": row[2],
        "gold": row[3] or 0,
        "current_gold": row[4] or 0,
        "level": row[5] or 0,
        "xp": row[6] or 0,
        "lane_cs": row[7] or 0,
        "jungle_cs": row[8] or 0,
        "cs": (
            (row[7] or 0)
            + (row[8] or 0)
        ),
        "x": row[9],
        "y": row[10],
    }


def _event_to_dict(row):
    raw = {}

    if row[15]:
        try:
            raw = json.loads(row[15])
        except Exception:
            raw = {}

    assists = []

    if row[14]:
        try:
            assists = json.loads(row[14])
        except Exception:
            assists = []

    return {
        "timestamp": row[1] or 0,
        "type": row[2],
        "participant_id": row[3],
        "killer_id": row[4],
        "victim_id": row[5],
        "team_id": row[6],
        "monster_type": row[7],
        "monster_sub_type": row[8],
        "item_id": row[9],
        "x": row[10],
        "y": row[11],
        "frame_index": row[12],
        "event_index": row[13],
        "assists": assists,
        "raw": raw,
    }


def load_tempo_bundles(
    puuid,
    position="JUNGLE",
    queue_id=420,
):
    """
    Charge tout le dataset Tempo avec des lectures massives SQLite.

    Pas de SELECT minute par minute : les frames et événements de
    toutes les games sont chargés par lots, puis filtrés en mémoire.
    """
    ensure_tempo_indexes()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            m.match_id,
            m.game_creation,
            m.game_duration,
            p.champion_name,
            p.win,
            m.raw_json
        FROM participants AS p
        JOIN matches AS m
            ON m.match_id = p.match_id
        WHERE p.puuid = ?
          AND p.position = ?
          AND m.queue_id = ?
        ORDER BY m.game_creation ASC
    """, (
        puuid,
        position,
        queue_id,
    ))

    metas = {}

    for row in cursor.fetchall():
        meta = _build_match_meta(
            match_id=row[0],
            game_creation=row[1],
            game_duration=row[2],
            champion=row[3],
            win=row[4],
            raw_json=row[5],
            puuid=puuid,
            position=position,
        )

        if not meta:
            continue

        if (
            meta["my_participant_id"] is None
            or meta["opponent_participant_id"] is None
        ):
            continue

        metas[meta["match_id"]] = meta

    match_ids = list(metas)

    frames_by_match = defaultdict(
        lambda: defaultdict(dict)
    )

    for chunk in _chunks(match_ids):
        placeholders = ",".join(
            "?" for _ in chunk
        )

        cursor.execute(
            f"""
            SELECT
                match_id,
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
            WHERE match_id IN ({placeholders})
            ORDER BY
                match_id,
                timestamp,
                participant_id
            """,
            tuple(chunk),
        )

        for row in cursor.fetchall():
            match_id = row[0]
            meta = metas.get(match_id)

            if not meta:
                continue

            participant_id = row[2]

            if participant_id not in (
                meta["my_participant_id"],
                meta["opponent_participant_id"],
            ):
                continue

            frame = _frame_to_dict(row)

            frames_by_match[
                match_id
            ][
                frame["timestamp"]
            ][
                participant_id
            ] = frame

    events_by_match = defaultdict(list)

    event_placeholders = ",".join(
        "?" for _ in RELEVANT_EVENT_TYPES
    )

    for chunk in _chunks(match_ids):
        match_placeholders = ",".join(
            "?" for _ in chunk
        )

        cursor.execute(
            f"""
            SELECT
                match_id,
                timestamp,
                event_type,
                participant_id,
                killer_id,
                victim_id,
                team_id,
                monster_type,
                monster_sub_type,
                item_id,
                position_x,
                position_y,
                frame_index,
                event_index,
                assisting_ids_json,
                raw_json
            FROM timeline_events
            WHERE match_id IN ({match_placeholders})
              AND event_type IN ({event_placeholders})
            ORDER BY
                match_id,
                timestamp,
                frame_index,
                event_index
            """,
            tuple(chunk)
            + tuple(RELEVANT_EVENT_TYPES),
        )

        for row in cursor.fetchall():
            events_by_match[
                row[0]
            ].append(
                _event_to_dict(row)
            )

    connection.close()

    bundles = []

    for match_id, meta in metas.items():
        timestamp_map = frames_by_match.get(
            match_id,
            {},
        )

        aligned_frames = []

        for timestamp in sorted(timestamp_map):
            pair = timestamp_map[timestamp]

            player = pair.get(
                meta["my_participant_id"]
            )

            opponent = pair.get(
                meta["opponent_participant_id"]
            )

            if (
                player is None
                or opponent is None
            ):
                continue

            aligned_frames.append({
                "timestamp": timestamp,
                "player": player,
                "opponent": opponent,
            })

        if len(aligned_frames) < 2:
            continue

        bundle = dict(meta)
        bundle["frames"] = aligned_frames
        bundle["events"] = events_by_match.get(
            match_id,
            [],
        )

        bundles.append(bundle)

    bundles.sort(
        key=lambda bundle: (
            bundle["game_creation"],
            bundle["match_id"],
        )
    )

    return bundles
