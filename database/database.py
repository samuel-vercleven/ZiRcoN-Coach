import sqlite3
import json

from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

DB_PATH = Path(__file__).parent / "zircon.db"

SOLOQ_QUEUE_ID = 420


# ============================================================
# CONNEXION
# ============================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


# ============================================================
# INITIALISATION DATABASE
# ============================================================

def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id TEXT PRIMARY KEY,
            game_creation INTEGER,
            game_duration INTEGER,
            game_version TEXT,
            queue_id INTEGER,
            raw_json TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            match_id TEXT NOT NULL,
            puuid TEXT NOT NULL,

            riot_name TEXT,
            riot_tag TEXT,

            team_id INTEGER,
            position TEXT,

            champion_id INTEGER,
            champion_name TEXT,

            kills INTEGER,
            deaths INTEGER,
            assists INTEGER,

            cs INTEGER,
            gold INTEGER,

            damage_to_champions INTEGER,
            vision_score INTEGER,

            win INTEGER,

            item0 INTEGER,
            item1 INTEGER,
            item2 INTEGER,
            item3 INTEGER,
            item4 INTEGER,
            item5 INTEGER,
            item6 INTEGER,

            FOREIGN KEY (match_id)
                REFERENCES matches(match_id),

            UNIQUE(match_id, puuid)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_participants_puuid_position
        ON participants(puuid, position)
    """)

    connection.commit()
    connection.close()


# ============================================================
# MATCH EXISTANT
# ============================================================

def match_exists(match_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM matches
        WHERE match_id = ?
        """,
        (match_id,)
    )

    exists = cursor.fetchone() is not None

    connection.close()

    return exists


# ============================================================
# SAUVEGARDE MATCH
# ============================================================

def save_match(match):
    connection = get_connection()
    cursor = connection.cursor()

    metadata = match["metadata"]
    info = match["info"]

    match_id = metadata["matchId"]

    cursor.execute("""
        INSERT OR IGNORE INTO matches (
            match_id,
            game_creation,
            game_duration,
            game_version,
            queue_id,
            raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        match_id,
        info.get("gameCreation"),
        info.get("gameDuration"),
        info.get("gameVersion"),
        info.get("queueId"),
        json.dumps(
            match,
            ensure_ascii=False
        )
    ))

    for player in info["participants"]:

        cs = (
            player.get(
                "totalMinionsKilled",
                0
            )
            +
            player.get(
                "neutralMinionsKilled",
                0
            )
        )

        position = (
            player.get("teamPosition")
            or
            player.get("individualPosition")
        )

        cursor.execute("""
            INSERT OR IGNORE INTO participants (
                match_id,
                puuid,

                riot_name,
                riot_tag,

                team_id,
                position,

                champion_id,
                champion_name,

                kills,
                deaths,
                assists,

                cs,
                gold,

                damage_to_champions,
                vision_score,

                win,

                item0,
                item1,
                item2,
                item3,
                item4,
                item5,
                item6
            )
            VALUES (
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?,
                ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            match_id,
            player.get("puuid"),

            player.get("riotIdGameName"),
            player.get("riotIdTagline"),

            player.get("teamId"),
            position,

            player.get("championId"),
            player.get("championName"),

            player.get("kills"),
            player.get("deaths"),
            player.get("assists"),

            cs,
            player.get("goldEarned"),

            player.get(
                "totalDamageDealtToChampions"
            ),

            player.get("visionScore"),

            int(
                player.get(
                    "win",
                    False
                )
            ),

            player.get("item0"),
            player.get("item1"),
            player.get("item2"),
            player.get("item3"),
            player.get("item4"),
            player.get("item5"),
            player.get("item6")
        ))

    connection.commit()
    connection.close()


# ============================================================
# FILTRE LOCAL PAR ROLE
# ============================================================

def get_local_account_by_riot_id(
    game_name,
    tag_line,
    queue_id=SOLOQ_QUEUE_ID,
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            p.puuid,
            p.riot_name,
            p.riot_tag,
            COUNT(*) AS games
        FROM participants AS p
        JOIN matches AS m
            ON m.match_id = p.match_id
        WHERE LOWER(p.riot_name) = LOWER(?)
          AND LOWER(p.riot_tag) = LOWER(?)
          AND m.queue_id = ?
        GROUP BY
            p.puuid,
            p.riot_name,
            p.riot_tag
        ORDER BY games DESC
        LIMIT 1
        """,
        (
            game_name,
            tag_line,
            queue_id,
        ),
    )

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    return {
        "puuid": row[0],
        "gameName": row[1] or game_name,
        "tagLine": row[2] or tag_line,
        "source": "LOCAL_DB",
    }


def get_local_match_ids_by_puuid(
    puuid,
    queue_id=SOLOQ_QUEUE_ID,
    count=None,
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT DISTINCT
            m.match_id,
            m.game_creation
        FROM participants AS p
        JOIN matches AS m
            ON m.match_id = p.match_id
        WHERE p.puuid = ?
          AND m.queue_id = ?
        ORDER BY
            m.game_creation DESC,
            m.match_id DESC
    """

    params = [
        puuid,
        queue_id,
    ]

    if count is not None:
        query += """
        LIMIT ?
        """
        params.append(count)

    cursor.execute(
        query,
        tuple(params),
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        row[0]
        for row in rows
    ]


def filter_match_ids_by_position(
    match_ids,
    puuid,
    position
):
    """
    Riot ne permet pas de filtrer directement
    l'historique Match-V5 par rôle.

    On récupère donc les SoloQ puis on filtre
    localement avec la position enregistrée.
    """

    if not match_ids:
        return []

    placeholders = ",".join(
        "?"
        for _ in match_ids
    )

    connection = get_connection()
    cursor = connection.cursor()

    query = f"""
        SELECT match_id
        FROM participants
        WHERE puuid = ?
          AND position = ?
          AND match_id IN ({placeholders})
    """

    params = [
        puuid,
        position,
        *match_ids
    ]

    cursor.execute(
        query,
        params
    )

    matching = {
        row[0]
        for row in cursor.fetchall()
    }

    connection.close()

    # On conserve l'ordre chronologique fourni par Riot
    return [
        match_id
        for match_id in match_ids
        if match_id in matching
    ]


# ============================================================
# STATS JOUEUR
# ============================================================

def get_player_stats(
    puuid,
    position=None
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            COUNT(*),

            SUM(p.win),

            SUM(p.kills),
            SUM(p.deaths),
            SUM(p.assists),

            SUM(p.cs),
            SUM(p.gold),
            SUM(p.damage_to_champions),

            SUM(m.game_duration)

        FROM participants AS p

        JOIN matches AS m
            ON p.match_id = m.match_id

        WHERE p.puuid = ?
          AND m.queue_id = ?
    """

    params = [
        puuid,
        SOLOQ_QUEUE_ID
    ]

    if position is not None:

        query += """
            AND p.position = ?
        """

        params.append(
            position
        )

    cursor.execute(
        query,
        tuple(params)
    )

    row = cursor.fetchone()

    connection.close()

    if not row or row[0] == 0:
        return None

    games = row[0]
    wins = row[1] or 0

    total_kills = row[2] or 0
    total_deaths = row[3] or 0
    total_assists = row[4] or 0

    total_cs = row[5] or 0
    total_gold = row[6] or 0
    total_damage = row[7] or 0

    total_seconds = row[8] or 0
    total_minutes = total_seconds / 60

    return {
        "games": games,

        "wins": wins,

        "losses": (
            games - wins
        ),

        "winrate": (
            wins / games
        ) * 100,

        "kills": (
            total_kills / games
        ),

        "deaths": (
            total_deaths / games
        ),

        "assists": (
            total_assists / games
        ),

        "average_duration": (
            total_minutes / games
            if games > 0
            else 0
        ),

        "cs_per_min": (
            total_cs / total_minutes
            if total_minutes > 0
            else 0
        ),

        "gold_per_min": (
            total_gold / total_minutes
            if total_minutes > 0
            else 0
        ),

        "damage_per_min": (
            total_damage / total_minutes
            if total_minutes > 0
            else 0
        )
    }


# ============================================================
# STATS PAR CHAMPION
# ============================================================

def get_champion_stats(
    puuid,
    position=None
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            p.champion_name,

            COUNT(*) AS games,
            SUM(p.win) AS wins,

            AVG(p.kills),
            AVG(p.deaths),
            AVG(p.assists),

            SUM(p.cs),
            SUM(p.gold),

            SUM(
                p.damage_to_champions
            ),

            SUM(
                m.game_duration
            )

        FROM participants AS p

        JOIN matches AS m
            ON p.match_id = m.match_id

        WHERE p.puuid = ?
          AND m.queue_id = ?
    """

    params = [
        puuid,
        SOLOQ_QUEUE_ID
    ]

    if position is not None:

        query += """
            AND p.position = ?
        """

        params.append(
            position
        )

    query += """
        GROUP BY p.champion_name

        ORDER BY games DESC
    """

    cursor.execute(
        query,
        tuple(params)
    )

    rows = cursor.fetchall()

    connection.close()

    champions = []

    for row in rows:

        games = row[1]

        wins = (
            row[2]
            or 0
        )

        total_seconds = (
            row[9]
            or 0
        )

        total_minutes = (
            total_seconds
            / 60
        )

        champions.append({
            "champion": row[0],

            "games": games,

            "wins": wins,

            "winrate": (
                wins / games
            ) * 100,

            "kills": (
                row[3]
                or 0
            ),

            "deaths": (
                row[4]
                or 0
            ),

            "assists": (
                row[5]
                or 0
            ),

            "cs_per_min": (
                (row[6] or 0)
                / total_minutes
                if total_minutes > 0
                else 0
            ),

            "gold_per_min": (
                (row[7] or 0)
                / total_minutes
                if total_minutes > 0
                else 0
            ),

            "damage_per_min": (
                (row[8] or 0)
                / total_minutes
                if total_minutes > 0
                else 0
            )
        })

    return champions


# ============================================================
# TABLES TIMELINE
# ============================================================

def initialize_timeline_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timelines (
            match_id TEXT PRIMARY KEY,
            raw_json TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeline_frames (
            match_id TEXT NOT NULL,

            timestamp INTEGER NOT NULL,

            participant_id INTEGER NOT NULL,

            total_gold INTEGER,
            current_gold INTEGER,

            level INTEGER,
            xp INTEGER,

            minions_killed INTEGER,
            jungle_minions_killed INTEGER,

            position_x INTEGER,
            position_y INTEGER,

            PRIMARY KEY (
                match_id,
                timestamp,
                participant_id
            )
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeline_events (
            match_id TEXT NOT NULL,

            frame_index INTEGER NOT NULL,
            event_index INTEGER NOT NULL,

            timestamp INTEGER,
            event_type TEXT,

            participant_id INTEGER,
            killer_id INTEGER,
            victim_id INTEGER,

            team_id INTEGER,

            monster_type TEXT,
            monster_sub_type TEXT,

            item_id INTEGER,

            position_x INTEGER,
            position_y INTEGER,

            assisting_ids_json TEXT,
            raw_json TEXT,

            PRIMARY KEY (
                match_id,
                frame_index,
                event_index
            )
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_frames_match_participant
        ON timeline_frames(
            match_id,
            participant_id,
            timestamp
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_match_timestamp
        ON timeline_events(
            match_id,
            timestamp
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# TIMELINE EXISTANTE
# ============================================================

def timeline_exists(match_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1

        FROM timelines

        WHERE match_id = ?
    """, (
        match_id,
    ))

    exists = (
        cursor.fetchone()
        is not None
    )

    connection.close()

    return exists


# ============================================================
# SAUVEGARDE TIMELINE
# ============================================================

def save_timeline(
    match_id,
    timeline
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO timelines (
            match_id,
            raw_json
        )

        VALUES (?, ?)
    """, (
        match_id,

        json.dumps(
            timeline,
            ensure_ascii=False
        )
    ))

    frames = (
        timeline
        .get("info", {})
        .get("frames", [])
    )

    for frame_index, frame in enumerate(
        frames
    ):

        timestamp = frame.get(
            "timestamp",
            0
        )

        participant_frames = (
            frame.get(
                "participantFrames",
                {}
            )
        )

        # ====================================================
        # FRAMES JOUEURS
        # ====================================================

        for (
            participant_key,
            player_frame
        ) in participant_frames.items():

            participant_id = (
                player_frame.get(
                    "participantId"
                )
            )

            if participant_id is None:

                try:
                    participant_id = int(
                        participant_key
                    )

                except ValueError:
                    continue

            position = (
                player_frame.get(
                    "position"
                )
                or {}
            )

            cursor.execute("""
                INSERT OR REPLACE INTO timeline_frames (
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
                )

                VALUES (
                    ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?
                )
            """, (
                match_id,
                timestamp,
                participant_id,

                player_frame.get(
                    "totalGold",
                    0
                ),

                player_frame.get(
                    "currentGold",
                    0
                ),

                player_frame.get(
                    "level",
                    0
                ),

                player_frame.get(
                    "xp",
                    0
                ),

                player_frame.get(
                    "minionsKilled",
                    0
                ),

                player_frame.get(
                    "jungleMinionsKilled",
                    0
                ),

                position.get("x"),
                position.get("y")
            ))

        # ====================================================
        # EVENTS
        # ====================================================

        events = frame.get(
            "events",
            []
        )

        for event_index, event in enumerate(
            events
        ):

            position = (
                event.get("position")
                or {}
            )

            assisting_ids = (
                event.get(
                    "assistingParticipantIds",
                    []
                )
                or []
            )

            cursor.execute("""
                INSERT OR REPLACE INTO timeline_events (
                    match_id,

                    frame_index,
                    event_index,

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

                    assisting_ids_json,
                    raw_json
                )

                VALUES (
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?,
                    ?, ?,
                    ?,
                    ?, ?,
                    ?, ?
                )
            """, (
                match_id,

                frame_index,
                event_index,

                event.get(
                    "timestamp"
                ),

                event.get(
                    "type"
                ),

                event.get(
                    "participantId"
                ),

                event.get(
                    "killerId"
                ),

                event.get(
                    "victimId"
                ),

                event.get(
                    "teamId"
                ),

                event.get(
                    "monsterType"
                ),

                event.get(
                    "monsterSubType"
                ),

                event.get(
                    "itemId"
                ),

                position.get("x"),
                position.get("y"),

                json.dumps(
                    assisting_ids
                ),

                json.dumps(
                    event,
                    ensure_ascii=False
                )
            ))

    connection.commit()
    connection.close()


# ============================================================
# IDENTIFICATION JOUEUR / ADVERSAIRE DIRECT
# ============================================================

def get_match_participant_ids(
    match_id,
    puuid
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT raw_json

        FROM matches

        WHERE match_id = ?
    """, (
        match_id,
    ))

    row = cursor.fetchone()

    connection.close()

    if not row:
        return None

    match = json.loads(
        row[0]
    )

    participants = (
        match["info"]
        ["participants"]
    )

    my_player = None

    for player in participants:

        if player.get("puuid") == puuid:

            my_player = player
            break

    if not my_player:
        return None

    my_participant_id = (
        my_player.get(
            "participantId"
        )
    )

    my_team_id = (
        my_player.get(
            "teamId"
        )
    )

    my_position = (
        my_player.get(
            "teamPosition"
        )
        or
        my_player.get(
            "individualPosition"
        )
    )

    opponent_id = None

    for player in participants:

        enemy_position = (
            player.get(
                "teamPosition"
            )
            or
            player.get(
                "individualPosition"
            )
        )

        if (
            player.get("teamId")
            != my_team_id
            and
            enemy_position
            == my_position
        ):

            opponent_id = (
                player.get(
                    "participantId"
                )
            )

            break

    return {
        "player_id":
            my_participant_id,

        "opponent_id":
            opponent_id,

        "position":
            my_position
    }


# ============================================================
# FRAME PROCHE D'UN TIMING
# ============================================================

def get_frame_near_timestamp(
    match_id,
    participant_id,
    timestamp
):
    if participant_id is None:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            timestamp,

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

        ORDER BY ABS(
            timestamp - ?
        )

        LIMIT 1
    """, (
        match_id,
        participant_id,
        timestamp
    ))

    row = cursor.fetchone()

    connection.close()

    if not row:
        return None

    MAX_DISTANCE_MS = 75_000

    if abs(
        row[0] - timestamp
    ) > MAX_DISTANCE_MS:

        return None

    lane_cs = (
        row[5]
        or 0
    )

    jungle_cs = (
        row[6]
        or 0
    )

    return {
        "timestamp":
            row[0],

        "gold":
            row[1] or 0,

        "current_gold":
            row[2] or 0,

        "level":
            row[3] or 0,

        "xp":
            row[4] or 0,

        "lane_cs":
            lane_cs,

        "jungle_cs":
            jungle_cs,

        "cs":
            lane_cs
            + jungle_cs,

        "x":
            row[7],

        "y":
            row[8]
    }


# ============================================================
# SNAPSHOTS 10 / 15 / 20
# ============================================================

def get_timeline_snapshots(
    match_id,
    puuid,
    minutes=(10, 15, 20)
):
    ids = get_match_participant_ids(
        match_id,
        puuid
    )

    if not ids:
        return []

    player_id = (
        ids["player_id"]
    )

    opponent_id = (
        ids["opponent_id"]
    )

    results = []

    for minute in minutes:

        target_timestamp = (
            minute
            * 60
            * 1000
        )

        player = get_frame_near_timestamp(
            match_id,
            player_id,
            target_timestamp
        )

        opponent = get_frame_near_timestamp(
            match_id,
            opponent_id,
            target_timestamp
        )

        if not player:
            continue

        snapshot = {
            "minute":
                minute,

            "position":
                ids["position"],

            "player":
                player,

            "opponent":
                opponent
        }

        if opponent:

            snapshot["gold_diff"] = (
                player["gold"]
                - opponent["gold"]
            )

            snapshot["cs_diff"] = (
                player["cs"]
                - opponent["cs"]
            )

            snapshot[
                "level_diff"
            ] = (
                player["level"]
                - opponent["level"]
            )

            snapshot["xp_diff"] = (
                player["xp"]
                - opponent["xp"]
            )

        else:

            snapshot[
                "gold_diff"
            ] = None

            snapshot[
                "cs_diff"
            ] = None

            snapshot[
                "level_diff"
            ] = None

            snapshot[
                "xp_diff"
            ] = None

        results.append(
            snapshot
        )

    return results


# ============================================================
# STATS DATABASE TIMELINE
# ============================================================

def get_timeline_database_stats():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM timelines
        """
    )

    timelines = (
        cursor.fetchone()[0]
    )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM timeline_frames
        """
    )

    frames = (
        cursor.fetchone()[0]
    )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM timeline_events
        """
    )

    events = (
        cursor.fetchone()[0]
    )

    connection.close()

    return {
        "timelines":
            timelines,

        "frames":
            frames,

        "events":
            events
    }


# ============================================================
# DATASET TIMELINE
# ============================================================

def get_timeline_dataset(
    puuid,
    minutes=(10, 15, 20),
    position=None
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            p.match_id,
            p.champion_name,
            p.win

        FROM participants AS p

        JOIN matches AS m
            ON p.match_id = m.match_id

        WHERE p.puuid = ?
          AND m.queue_id = ?
    """

    params = [
        puuid,
        SOLOQ_QUEUE_ID
    ]

    if position is not None:

        query += """
            AND p.position = ?
        """

        params.append(
            position
        )

    query += """
        ORDER BY
            m.game_creation DESC
    """

    cursor.execute(
        query,
        tuple(params)
    )

    matches = (
        cursor.fetchall()
    )

    connection.close()

    dataset = []

    for (
        match_id,
        champion,
        win
    ) in matches:

        snapshots = (
            get_timeline_snapshots(
                match_id,
                puuid,
                minutes=minutes
            )
        )

        for snapshot in snapshots:

            if (
                snapshot["opponent"]
                is None
            ):
                continue

            player = (
                snapshot["player"]
            )

            opponent = (
                snapshot["opponent"]
            )

            dataset.append({
                "match_id":
                    match_id,

                "champion":
                    champion,

                "win":
                    bool(win),

                "minute":
                    snapshot["minute"],

                "position":
                    snapshot["position"],

                "gold":
                    player["gold"],

                "cs":
                    player["cs"],

                "level":
                    player["level"],

                "xp":
                    player["xp"],

                "opponent_gold":
                    opponent["gold"],

                "opponent_cs":
                    opponent["cs"],

                "opponent_level":
                    opponent["level"],

                "opponent_xp":
                    opponent["xp"],

                "gold_diff":
                    snapshot[
                        "gold_diff"
                    ],

                "cs_diff":
                    snapshot[
                        "cs_diff"
                    ],

                "level_diff":
                    snapshot[
                        "level_diff"
                    ],

                "xp_diff":
                    snapshot[
                        "xp_diff"
                    ]
            })

    return dataset


# ============================================================
# AGRÉGATION TIMELINE
# ============================================================

def aggregate_timeline_dataset(
    dataset,
    champion=None,
    win=None
):
    filtered = []

    for row in dataset:

        if (
            champion is not None
            and
            row["champion"]
            != champion
        ):
            continue

        if (
            win is not None
            and
            row["win"]
            != win
        ):
            continue

        filtered.append(
            row
        )

    minutes = sorted(
        {
            row["minute"]
            for row in filtered
        }
    )

    results = {}

    for minute in minutes:

        rows = [
            row
            for row in filtered
            if row["minute"]
            == minute
        ]

        if not rows:
            continue

        games = len(
            rows
        )

        def average(key):

            return (
                sum(
                    row[key]
                    for row in rows
                )
                / games
            )

        gold_ahead = sum(
            1
            for row in rows
            if row["gold_diff"] > 0
        )

        cs_ahead = sum(
            1
            for row in rows
            if row["cs_diff"] > 0
        )

        results[minute] = {
            "games":
                games,

            "gold":
                average("gold"),

            "cs":
                average("cs"),

            "level":
                average("level"),

            "xp":
                average("xp"),

            "gold_diff":
                average(
                    "gold_diff"
                ),

            "cs_diff":
                average(
                    "cs_diff"
                ),

            "level_diff":
                average(
                    "level_diff"
                ),

            "xp_diff":
                average(
                    "xp_diff"
                ),

            "gold_ahead_percent":
                (
                    gold_ahead
                    / games
                ) * 100,

            "cs_ahead_percent":
                (
                    cs_ahead
                    / games
                ) * 100
        }

    return results


# ============================================================
# DATASET ÉVÉNEMENTS PAR FENÊTRE
# ============================================================

def get_event_window_dataset(
    puuid,
    windows=(
        (0, 10),
        (10, 15),
        (15, 20)
    ),
    position="JUNGLE"
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            p.match_id,
            p.champion_name,
            p.win,
            m.raw_json

        FROM participants AS p

        JOIN matches AS m
            ON p.match_id = m.match_id

        WHERE p.puuid = ?
          AND m.queue_id = ?
    """

    params = [
        puuid,
        SOLOQ_QUEUE_ID
    ]

    if position is not None:

        query += """
            AND p.position = ?
        """

        params.append(
            position
        )

    query += """
        ORDER BY
            m.game_creation DESC
    """

    cursor.execute(
        query,
        tuple(params)
    )

    matches = (
        cursor.fetchall()
    )

    connection.close()

    dataset = []

    for (
        match_id,
        champion,
        win,
        raw_match
    ) in matches:

        match = json.loads(
            raw_match
        )

        participants = (
            match["info"]
            ["participants"]
        )

        my_player = None

        participant_team_map = {}

        for player in participants:

            participant_team_map[
                player.get(
                    "participantId"
                )
            ] = player.get(
                "teamId"
            )

            if (
                player.get("puuid")
                == puuid
            ):
                my_player = player

        if not my_player:
            continue

        player_id = (
            my_player.get(
                "participantId"
            )
        )

        team_id = (
            my_player.get(
                "teamId"
            )
        )

        my_position = (
            my_player.get(
                "teamPosition"
            )
            or
            my_player.get(
                "individualPosition"
            )
        )

        opponent_id = None

        for player in participants:

            enemy_position = (
                player.get(
                    "teamPosition"
                )
                or
                player.get(
                    "individualPosition"
                )
            )

            if (
                player.get("teamId")
                != team_id
                and
                enemy_position
                == my_position
            ):
                opponent_id = (
                    player.get(
                        "participantId"
                    )
                )

                break

        if opponent_id is None:
            continue

        # ====================================================
        # CHARGEMENT EVENTS
        # ====================================================

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT raw_json

            FROM timeline_events

            WHERE match_id = ?

            ORDER BY timestamp
        """, (
            match_id,
        ))

        event_rows = (
            cursor.fetchall()
        )

        connection.close()

        events = []

        for row in event_rows:

            try:
                events.append(
                    json.loads(
                        row[0]
                    )
                )

            except (
                TypeError,
                json.JSONDecodeError
            ):
                continue

        # ====================================================
        # TIMINGS OBJECTIFS MAJEURS
        # ====================================================

        major_objective_times = []

        for event in events:

            if (
                event.get("type")
                !=
                "ELITE_MONSTER_KILL"
            ):
                continue

            monster = str(
                event.get(
                    "monsterType",
                    ""
                )
            ).upper()

            subtype = str(
                event.get(
                    "monsterSubType",
                    ""
                )
            ).upper()

            objective_text = (
                monster
                + " "
                + subtype
            )

            if any(
                keyword
                in objective_text
                for keyword in (
                    "DRAGON",
                    "RIFTHERALD",
                    "HERALD",
                    "HORDE",
                    "GRUB",
                    "BARON"
                )
            ):
                major_objective_times.append(
                    event.get(
                        "timestamp",
                        0
                    )
                )

        # ====================================================
        # FENÊTRES
        # ====================================================

        for (
            start_min,
            end_min
        ) in windows:

            start_ms = (
                start_min
                * 60
                * 1000
            )

            end_ms = (
                end_min
                * 60
                * 1000
            )

            player_start = (
                get_frame_near_timestamp(
                    match_id,
                    player_id,
                    start_ms
                )
            )

            player_end = (
                get_frame_near_timestamp(
                    match_id,
                    player_id,
                    end_ms
                )
            )

            opponent_start = (
                get_frame_near_timestamp(
                    match_id,
                    opponent_id,
                    start_ms
                )
            )

            opponent_end = (
                get_frame_near_timestamp(
                    match_id,
                    opponent_id,
                    end_ms
                )
            )

            if (
                not player_start
                or
                not player_end
                or
                not opponent_start
                or
                not opponent_end
            ):
                continue

            window_events = [
                event
                for event in events
                if (
                    start_ms
                    <=
                    event.get(
                        "timestamp",
                        0
                    )
                    <
                    end_ms
                )
            ]

            kills = 0
            deaths = 0
            assists = 0

            dragons = 0
            grubs = 0
            heralds = 0
            barons = 0
            towers = 0

            player_kill_times = []
            player_death_times = []

            for event in window_events:

                event_type = (
                    event.get(
                        "type"
                    )
                )

                # ============================================
                # KILLS
                # ============================================

                if (
                    event_type
                    ==
                    "CHAMPION_KILL"
                ):

                    killer_id = (
                        event.get(
                            "killerId"
                        )
                    )

                    victim_id = (
                        event.get(
                            "victimId"
                        )
                    )

                    assisting_ids = (
                        event.get(
                            "assistingParticipantIds",
                            []
                        )
                        or []
                    )

                    if (
                        killer_id
                        == player_id
                    ):

                        kills += 1

                        player_kill_times.append(
                            event.get(
                                "timestamp",
                                0
                            )
                        )

                    if (
                        victim_id
                        == player_id
                    ):

                        deaths += 1

                        player_death_times.append(
                            event.get(
                                "timestamp",
                                0
                            )
                        )

                    if (
                        player_id
                        in assisting_ids
                    ):

                        assists += 1

                # ============================================
                # MONSTRES ÉPIQUES
                # ============================================

                elif (
                    event_type
                    ==
                    "ELITE_MONSTER_KILL"
                ):

                    killer_id = (
                        event.get(
                            "killerId"
                        )
                    )

                    killer_team = (
                        event.get(
                            "killerTeamId"
                        )
                    )

                    if killer_team is None:

                        killer_team = (
                            participant_team_map
                            .get(
                                killer_id
                            )
                        )

                    if (
                        killer_team
                        != team_id
                    ):
                        continue

                    monster = str(
                        event.get(
                            "monsterType",
                            ""
                        )
                    ).upper()

                    subtype = str(
                        event.get(
                            "monsterSubType",
                            ""
                        )
                    ).upper()

                    objective_text = (
                        monster
                        + " "
                        + subtype
                    )

                    if (
                        "DRAGON"
                        in objective_text
                    ):

                        dragons += 1

                    elif (
                        "RIFTHERALD"
                        in objective_text
                        or
                        "HERALD"
                        in objective_text
                    ):

                        heralds += 1

                    elif (
                        "HORDE"
                        in objective_text
                        or
                        "GRUB"
                        in objective_text
                    ):

                        grubs += 1

                    elif (
                        "BARON"
                        in objective_text
                    ):

                        barons += 1

                # ============================================
                # TOURS
                # ============================================

                elif (
                    event_type
                    ==
                    "BUILDING_KILL"
                ):

                    building_type = str(
                        event.get(
                            "buildingType",
                            ""
                        )
                    ).upper()

                    if (
                        "TOWER"
                        not in building_type
                    ):
                        continue

                    killer_id = (
                        event.get(
                            "killerId"
                        )
                    )

                    killer_team = (
                        participant_team_map
                        .get(
                            killer_id
                        )
                    )

                    if (
                        killer_team
                        == team_id
                    ):

                        towers += 1

                    elif (
                        killer_id
                        in (
                            0,
                            None
                        )
                    ):

                        destroyed_team = (
                            event.get(
                                "teamId"
                            )
                        )

                        if (
                            destroyed_team
                            is not None
                            and
                            destroyed_team
                            != team_id
                        ):

                            towers += 1

            # =================================================
            # MORTS / KILLS AUTOUR OBJECTIFS
            # =================================================

            deaths_before_objective = 0
            deaths_after_objective = 0
            kills_before_objective = 0

            for death_time in player_death_times:

                before = any(
                    0
                    <
                    objective_time
                    - death_time
                    <=
                    60_000

                    for objective_time
                    in major_objective_times
                )

                after = any(
                    0
                    <
                    death_time
                    - objective_time
                    <=
                    60_000

                    for objective_time
                    in major_objective_times
                )

                if before:
                    deaths_before_objective += 1

                if after:
                    deaths_after_objective += 1

            for kill_time in player_kill_times:

                before = any(
                    0
                    <
                    objective_time
                    - kill_time
                    <=
                    60_000

                    for objective_time
                    in major_objective_times
                )

                if before:
                    kills_before_objective += 1

            # =================================================
            # DIFFÉRENCES
            # =================================================

            gold_diff_start = (
                player_start["gold"]
                -
                opponent_start["gold"]
            )

            gold_diff_end = (
                player_end["gold"]
                -
                opponent_end["gold"]
            )

            cs_diff_start = (
                player_start["cs"]
                -
                opponent_start["cs"]
            )

            cs_diff_end = (
                player_end["cs"]
                -
                opponent_end["cs"]
            )

            xp_diff_start = (
                player_start["xp"]
                -
                opponent_start["xp"]
            )

            xp_diff_end = (
                player_end["xp"]
                -
                opponent_end["xp"]
            )

            # =================================================
            # DATASET
            # =================================================

            dataset.append({
                "match_id":
                    match_id,

                "champion":
                    champion,

                "win":
                    bool(win),

                "position":
                    my_position,

                "start_min":
                    start_min,

                "end_min":
                    end_min,

                # Personnel

                "gold_gained":
                    (
                        player_end["gold"]
                        -
                        player_start["gold"]
                    ),

                "cs_gained":
                    (
                        player_end["cs"]
                        -
                        player_start["cs"]
                    ),

                "xp_gained":
                    (
                        player_end["xp"]
                        -
                        player_start["xp"]
                    ),

                # Diff adversaire

                "gold_diff_start":
                    gold_diff_start,

                "gold_diff_end":
                    gold_diff_end,

                "gold_diff_change":
                    (
                        gold_diff_end
                        -
                        gold_diff_start
                    ),

                "cs_diff_start":
                    cs_diff_start,

                "cs_diff_end":
                    cs_diff_end,

                "cs_diff_change":
                    (
                        cs_diff_end
                        -
                        cs_diff_start
                    ),

                "xp_diff_start":
                    xp_diff_start,

                "xp_diff_end":
                    xp_diff_end,

                "xp_diff_change":
                    (
                        xp_diff_end
                        -
                        xp_diff_start
                    ),

                # Combat

                "kills":
                    kills,

                "deaths":
                    deaths,

                "assists":
                    assists,

                # Objectifs équipe

                "dragons":
                    dragons,

                "grubs":
                    grubs,

                "heralds":
                    heralds,

                "barons":
                    barons,

                "towers":
                    towers,

                # Timings objectifs

                "deaths_before_objective":
                    deaths_before_objective,

                "deaths_after_objective":
                    deaths_after_objective,

                "kills_before_objective":
                    kills_before_objective
            })

    return dataset


# ============================================================
# AGRÉGATION ÉVÉNEMENTS
# ============================================================

def aggregate_event_windows(
    dataset,
    champion=None,
    win=None
):
    filtered = []

    for row in dataset:

        if (
            champion is not None
            and
            row["champion"]
            != champion
        ):
            continue

        if (
            win is not None
            and
            row["win"]
            != win
        ):
            continue

        filtered.append(
            row
        )

    windows = sorted(
        {
            (
                row["start_min"],
                row["end_min"]
            )
            for row in filtered
        }
    )

    results = {}

    for (
        start_min,
        end_min
    ) in windows:

        rows = [
            row
            for row in filtered
            if (
                row["start_min"]
                == start_min
                and
                row["end_min"]
                == end_min
            )
        ]

        if not rows:
            continue

        games = len(
            rows
        )

        def average(key):

            return (
                sum(
                    row[key]
                    for row in rows
                )
                / games
            )

        results[
            (
                start_min,
                end_min
            )
        ] = {
            "games":
                games,

            "gold_gained":
                average(
                    "gold_gained"
                ),

            "cs_gained":
                average(
                    "cs_gained"
                ),

            "xp_gained":
                average(
                    "xp_gained"
                ),

            "gold_diff_change":
                average(
                    "gold_diff_change"
                ),

            "cs_diff_change":
                average(
                    "cs_diff_change"
                ),

            "xp_diff_change":
                average(
                    "xp_diff_change"
                ),

            "kills":
                average(
                    "kills"
                ),

            "deaths":
                average(
                    "deaths"
                ),

            "assists":
                average(
                    "assists"
                ),

            "dragons":
                average(
                    "dragons"
                ),

            "grubs":
                average(
                    "grubs"
                ),

            "heralds":
                average(
                    "heralds"
                ),

            "barons":
                average(
                    "barons"
                ),

            "towers":
                average(
                    "towers"
                ),

            "deaths_before_objective":
                average(
                    "deaths_before_objective"
                ),

            "deaths_after_objective":
                average(
                    "deaths_after_objective"
                ),

            "kills_before_objective":
                average(
                    "kills_before_objective"
                )
        }

    return results
