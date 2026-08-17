from bisect import bisect_left, bisect_right
from collections import defaultdict
from math import hypot
from statistics import mean, median

from analysis.feature_engine import percentile_rank


# ============================================================
# CONFIGURATION
# ============================================================

OBJECTIVE_PREP_SECONDS = 120
OBJECTIVE_APPROACH_SECONDS = 60
OBJECTIVE_CONVERSION_SECONDS = 120
OBJECTIVE_FIGHT_PRE_SECONDS = 60
OBJECTIVE_FIGHT_POST_SECONDS = 30
OBJECTIVE_TRADE_PRE_SECONDS = 45
OBJECTIVE_TRADE_POST_SECONDS = 120

MAX_FRAME_DISTANCE_SECONDS = 75
OBJECTIVE_PROXIMITY_NEAR = 2500
OBJECTIVE_PROXIMITY_MID = 4500

# V19 : on évite des labels EXCELLENT/LOW construits sur 8-10 cas.
# La référence locale est privilégiée, mais il faut au moins 20 séquences.
# Sinon on retombe sur champion+famille puis famille globale.
MIN_HISTORICAL_OBJECTIVE_REFERENCE = 20
MIN_HISTORICAL_OBJECTIVE_TIME_REFERENCE = 20
OBJECTIVE_TIME_REFERENCE_RADIUS_SECONDS = 240

# Contest : un kill temporellement proche ne suffit plus.
# Il doit aussi être spatialement proche du pit / objectif.
OBJECTIVE_FIGHT_SPATIAL_RADIUS = 3500

# Compensation ressources : il faut une amplitude significative.
# Ces seuils s'appliquent sur la fenêtre de conversion de 120 s.
RESOURCE_COMPENSATION_GOLD = 300
RESOURCE_COMPENSATION_XP = 400
RESOURCE_COMPENSATION_JUNGLE_CS = 4

PREPARATION_SCORE_WEIGHTS = {
    "prep_player_xp_per_min": 0.25,
    "prep_player_jungle_cs_per_min": 0.20,
    "prep_relative_gold_per_min": 0.10,
    "prep_relative_xp_per_min": 0.25,
    "prep_relative_jungle_cs_per_min": 0.20,
}

CONVERSION_SCORE_WEIGHTS = {
    "conversion_player_xp_per_min": 0.20,
    "conversion_player_jungle_cs_per_min": 0.15,
    "conversion_relative_gold_per_min": 0.20,
    "conversion_relative_xp_per_min": 0.25,
    "conversion_relative_jungle_cs_per_min": 0.20,
}


# ============================================================
# GENERIC HELPERS
# ============================================================

def _format_time(timestamp_ms):
    total_seconds = int((timestamp_ms or 0) / 1000)
    return f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"


def _safe_rate(value, duration_minutes):
    if value is None or duration_minutes is None or duration_minutes <= 0:
        return None
    return value / duration_minutes


def _safe_mean(values):
    values = [value for value in values if value is not None]
    return mean(values) if values else None


def _safe_median(values):
    values = [value for value in values if value is not None]
    return median(values) if values else None


def _fmt_optional(value, pattern):
    if value is None:
        return "N/A"
    return pattern.format(value)


def _score_label(score):
    if score is None:
        return "WARMUP"
    if score < 25:
        return "LOW"
    if score < 50:
        return "BELOW_BASELINE"
    if score < 75:
        return "GOOD"
    return "EXCELLENT"


def _state_from_diffs(gold_diff, xp_diff, jungle_cs_diff):
    score = 0

    if gold_diff >= 300:
        score += 1
    elif gold_diff <= -300:
        score -= 1

    if xp_diff >= 300:
        score += 1
    elif xp_diff <= -300:
        score -= 1

    if jungle_cs_diff >= 5:
        score += 1
    elif jungle_cs_diff <= -5:
        score -= 1

    if score >= 2:
        return "AHEAD"
    if score <= -2:
        return "BEHIND"
    return "EVEN"


def _killer_team(event, bundle):
    raw = event.get("raw") or {}

    team_id = raw.get("killerTeamId")
    if team_id is not None:
        return team_id

    killer_id = event.get("killer_id")
    player = bundle.get("players", {}).get(killer_id)
    if player:
        return player.get("team_id")

    # Some event payloads expose the securing team directly.
    event_team = event.get("team_id")
    if event_team in (100, 200):
        return event_team

    return None


def _event_index(events):
    events = sorted(
        events,
        key=lambda event: (
            event.get("timestamp", 0),
            event.get("frame_index") or 0,
            event.get("event_index") or 0,
        ),
    )
    timestamps = [event.get("timestamp", 0) for event in events]
    return timestamps, events


def _events_between(index, start_ms, end_ms):
    timestamps, events = index
    left = bisect_left(timestamps, start_ms)
    right = bisect_right(timestamps, end_ms)
    return events[left:right]


def _frame_timestamps(frames):
    return [frame["timestamp"] for frame in frames]


def _frame_before_or_at(frames, timestamps, target_ms):
    index = bisect_right(timestamps, target_ms) - 1
    if index < 0:
        return None

    frame = frames[index]
    distance = target_ms - frame["timestamp"]

    if distance > MAX_FRAME_DISTANCE_SECONDS * 1000:
        return None

    return frame


def _frame_after_or_at(frames, timestamps, target_ms):
    index = bisect_left(timestamps, target_ms)
    if index >= len(frames):
        return None

    frame = frames[index]
    distance = frame["timestamp"] - target_ms

    if distance > MAX_FRAME_DISTANCE_SECONDS * 1000:
        return None

    return frame


def _participant_snapshot(pair, side):
    return pair.get(side) if pair else None


def _relative_state(pair):
    if not pair:
        return None

    player = pair.get("player")
    opponent = pair.get("opponent")

    if not player or not opponent:
        return None

    return {
        "timestamp": pair["timestamp"],
        "player_gold": player.get("gold", 0),
        "player_current_gold": player.get("current_gold", 0),
        "player_xp": player.get("xp", 0),
        "player_cs": player.get("cs", 0),
        "player_jungle_cs": player.get("jungle_cs", 0),
        "player_lane_cs": player.get("lane_cs", 0),
        "player_level": player.get("level", 0),
        "player_x": player.get("x"),
        "player_y": player.get("y"),

        "opponent_gold": opponent.get("gold", 0),
        "opponent_current_gold": opponent.get("current_gold", 0),
        "opponent_xp": opponent.get("xp", 0),
        "opponent_cs": opponent.get("cs", 0),
        "opponent_jungle_cs": opponent.get("jungle_cs", 0),
        "opponent_lane_cs": opponent.get("lane_cs", 0),
        "opponent_level": opponent.get("level", 0),
        "opponent_x": opponent.get("x"),
        "opponent_y": opponent.get("y"),

        "gold_diff": player.get("gold", 0) - opponent.get("gold", 0),
        "xp_diff": player.get("xp", 0) - opponent.get("xp", 0),
        "cs_diff": player.get("cs", 0) - opponent.get("cs", 0),
        "jungle_cs_diff": (
            player.get("jungle_cs", 0)
            - opponent.get("jungle_cs", 0)
        ),
        "level_diff": player.get("level", 0) - opponent.get("level", 0),
    }


def _window_delta(start_pair, end_pair, prefix):
    start = _relative_state(start_pair)
    end = _relative_state(end_pair)

    if not start or not end:
        return {
            f"{prefix}_available": False,
            f"{prefix}_duration_seconds": None,
        }

    duration_seconds = end["timestamp"] - start["timestamp"]
    if duration_seconds <= 0:
        return {
            f"{prefix}_available": False,
            f"{prefix}_duration_seconds": duration_seconds,
        }

    duration_minutes = duration_seconds / 60_000

    player_gold_gain = end["player_gold"] - start["player_gold"]
    player_xp_gain = end["player_xp"] - start["player_xp"]
    player_cs_gain = end["player_cs"] - start["player_cs"]
    player_jungle_cs_gain = (
        end["player_jungle_cs"] - start["player_jungle_cs"]
    )

    opponent_gold_gain = end["opponent_gold"] - start["opponent_gold"]
    opponent_xp_gain = end["opponent_xp"] - start["opponent_xp"]
    opponent_cs_gain = end["opponent_cs"] - start["opponent_cs"]
    opponent_jungle_cs_gain = (
        end["opponent_jungle_cs"] - start["opponent_jungle_cs"]
    )

    relative_gold_change = end["gold_diff"] - start["gold_diff"]
    relative_xp_change = end["xp_diff"] - start["xp_diff"]
    relative_cs_change = end["cs_diff"] - start["cs_diff"]
    relative_jungle_cs_change = (
        end["jungle_cs_diff"] - start["jungle_cs_diff"]
    )

    return {
        f"{prefix}_available": True,
        f"{prefix}_start_timestamp": start["timestamp"],
        f"{prefix}_end_timestamp": end["timestamp"],
        f"{prefix}_duration_seconds": duration_seconds,
        f"{prefix}_duration_minutes": duration_minutes,

        f"{prefix}_player_gold_gain": player_gold_gain,
        f"{prefix}_player_xp_gain": player_xp_gain,
        f"{prefix}_player_cs_gain": player_cs_gain,
        f"{prefix}_player_jungle_cs_gain": player_jungle_cs_gain,

        f"{prefix}_opponent_gold_gain": opponent_gold_gain,
        f"{prefix}_opponent_xp_gain": opponent_xp_gain,
        f"{prefix}_opponent_cs_gain": opponent_cs_gain,
        f"{prefix}_opponent_jungle_cs_gain": opponent_jungle_cs_gain,

        f"{prefix}_relative_gold_change": relative_gold_change,
        f"{prefix}_relative_xp_change": relative_xp_change,
        f"{prefix}_relative_cs_change": relative_cs_change,
        f"{prefix}_relative_jungle_cs_change": relative_jungle_cs_change,

        f"{prefix}_player_gold_per_min": _safe_rate(
            player_gold_gain,
            duration_minutes,
        ),
        f"{prefix}_player_xp_per_min": _safe_rate(
            player_xp_gain,
            duration_minutes,
        ),
        f"{prefix}_player_cs_per_min": _safe_rate(
            player_cs_gain,
            duration_minutes,
        ),
        f"{prefix}_player_jungle_cs_per_min": _safe_rate(
            player_jungle_cs_gain,
            duration_minutes,
        ),
        f"{prefix}_opponent_gold_per_min": _safe_rate(
            opponent_gold_gain,
            duration_minutes,
        ),
        f"{prefix}_opponent_xp_per_min": _safe_rate(
            opponent_xp_gain,
            duration_minutes,
        ),
        f"{prefix}_opponent_jungle_cs_per_min": _safe_rate(
            opponent_jungle_cs_gain,
            duration_minutes,
        ),
        f"{prefix}_relative_gold_per_min": _safe_rate(
            relative_gold_change,
            duration_minutes,
        ),
        f"{prefix}_relative_xp_per_min": _safe_rate(
            relative_xp_change,
            duration_minutes,
        ),
        f"{prefix}_relative_cs_per_min": _safe_rate(
            relative_cs_change,
            duration_minutes,
        ),
        f"{prefix}_relative_jungle_cs_per_min": _safe_rate(
            relative_jungle_cs_change,
            duration_minutes,
        ),
    }


def _distance_to_objective(state, objective_x, objective_y, side):
    if not state or objective_x is None or objective_y is None:
        return None

    x = state.get(f"{side}_x")
    y = state.get(f"{side}_y")

    if x is None or y is None:
        return None

    return hypot(x - objective_x, y - objective_y)


def _proximity_label(distance):
    if distance is None:
        return "UNKNOWN"
    if distance <= OBJECTIVE_PROXIMITY_NEAR:
        return "NEAR"
    if distance <= OBJECTIVE_PROXIMITY_MID:
        return "MID"
    return "FAR"


def _event_distance_to_point(event, x, y):
    if x is None or y is None:
        return None

    event_x = event.get("x")
    event_y = event.get("y")

    if event_x is None or event_y is None:
        raw = event.get("raw") or {}
        event_x = raw.get("position", {}).get("x")
        event_y = raw.get("position", {}).get("y")

    if event_x is None or event_y is None:
        return None

    return hypot(event_x - x, event_y - y)


def _spatial_fight_events(events, objective_x, objective_y):
    """
    Garde uniquement les CHAMPION_KILL localisés près de l'objectif.

    Un kill sur une autre lane dans la fenêtre -60/+30 s ne doit plus
    transformer artificiellement l'objectif en "contesté".
    """
    near = []
    located = 0
    unlocated = 0

    for event in events:
        if event.get("type") != "CHAMPION_KILL":
            continue

        distance = _event_distance_to_point(
            event,
            objective_x,
            objective_y,
        )

        if distance is None:
            unlocated += 1
            continue

        located += 1

        if distance <= OBJECTIVE_FIGHT_SPATIAL_RADIUS:
            near.append(event)

    return {
        "events": near,
        "located_kills": located,
        "unlocated_kills": unlocated,
        "near_kills": len(near),
    }


# ============================================================
# OBJECTIVE NORMALIZATION
# ============================================================

def _objective_identity(event):
    monster_type = str(event.get("monster_type") or "").upper()
    monster_sub_type = str(event.get("monster_sub_type") or "").upper()
    raw = event.get("raw") or {}

    combined = " ".join(
        filter(
            None,
            (
                monster_type,
                monster_sub_type,
                str(raw.get("monsterType") or "").upper(),
                str(raw.get("monsterSubType") or "").upper(),
            ),
        )
    )

    if "ELDER" in combined:
        return "ELDER", "ELDER"
    if "DRAGON" in combined:
        return "DRAGON", "DRAGON"
    if "BARON" in combined:
        return "BARON", "BARON"
    if "HERALD" in combined:
        return "HERALD", "HERALD"
    if "HORDE" in combined or "GRUB" in combined:
        return "GRUBS", "GRUBS"
    if "ATAKHAN" in combined:
        return "ATAKHAN", "ATAKHAN"

    return "OTHER_EPIC", "OTHER_EPIC"


def _normalize_objective_events(bundle):
    objectives = []

    for event in bundle.get("events", []):
        if event.get("type") != "ELITE_MONSTER_KILL":
            continue

        kind, family = _objective_identity(event)
        team_id = _killer_team(event, bundle)
        killer_id = event.get("killer_id")

        objectives.append({
            "timestamp": event.get("timestamp", 0),
            "kind": kind,
            "family": family,
            "monster_type": event.get("monster_type"),
            "monster_sub_type": event.get("monster_sub_type"),
            "team_id": team_id,
            "killer_id": killer_id,
            "x": event.get("x"),
            "y": event.get("y"),
            "raw": event.get("raw") or {},
            "source_event": event,
        })

    objectives.sort(key=lambda row: row["timestamp"])

    # Legacy Void Grubs can emit multiple elite-kill events for one encounter.
    # We keep the individual count but expose one encounter row when several
    # GRUBS kills occur close together.
    normalized = []
    grub_cluster = []

    def flush_grubs():
        nonlocal grub_cluster
        if not grub_cluster:
            return

        first = grub_cluster[0]
        team_counts = defaultdict(int)
        killer_ids = []

        for row in grub_cluster:
            team_counts[row.get("team_id")] += 1
            if row.get("killer_id") is not None:
                killer_ids.append(row["killer_id"])

        known_counts = {
            team: count
            for team, count in team_counts.items()
            if team is not None
        }

        if known_counts:
            max_count = max(known_counts.values())
            winners = [
                team
                for team, count in known_counts.items()
                if count == max_count
            ]
            team_id = winners[0] if len(winners) == 1 else None
        else:
            team_id = None

        normalized.append({
            **first,
            "timestamp": int(
                median([row["timestamp"] for row in grub_cluster])
            ),
            "team_id": team_id,
            "grub_kills": len(grub_cluster),
            "grub_team_counts": dict(known_counts),
            "killer_ids": killer_ids,
            "clustered": True,
        })

        grub_cluster = []

    for row in objectives:
        if row["family"] != "GRUBS":
            flush_grubs()
            normalized.append({
                **row,
                "grub_kills": None,
                "grub_team_counts": None,
                "killer_ids": [row["killer_id"]] if row.get("killer_id") else [],
                "clustered": False,
            })
            continue

        if not grub_cluster:
            grub_cluster = [row]
            continue

        if row["timestamp"] - grub_cluster[-1]["timestamp"] <= 90_000:
            grub_cluster.append(row)
        else:
            flush_grubs()
            grub_cluster = [row]

    flush_grubs()

    normalized.sort(key=lambda row: row["timestamp"])

    for index, row in enumerate(normalized, start=1):
        row["objective_index"] = index

    return normalized


# ============================================================
# EVENT CONTEXT
# ============================================================

def _team_kill_counts(events, bundle):
    my_team = bundle["my_team_id"]
    enemy_team = bundle["opponent_team_id"]
    my_id = bundle["my_participant_id"]
    opponent_id = bundle["opponent_participant_id"]

    result = {
        "ally_champion_kills": 0,
        "enemy_champion_kills": 0,
        "player_kills": 0,
        "player_assists": 0,
        "player_deaths": 0,
        "opponent_kills": 0,
        "opponent_assists": 0,
        "opponent_deaths": 0,
    }

    for event in events:
        if event.get("type") != "CHAMPION_KILL":
            continue

        killer_id = event.get("killer_id")
        victim_id = event.get("victim_id")
        assists = event.get("assists") or []
        killer = bundle.get("players", {}).get(killer_id)
        killer_team = killer.get("team_id") if killer else None

        if killer_team == my_team:
            result["ally_champion_kills"] += 1
        elif killer_team == enemy_team:
            result["enemy_champion_kills"] += 1

        if killer_id == my_id:
            result["player_kills"] += 1
        if my_id in assists:
            result["player_assists"] += 1
        if victim_id == my_id:
            result["player_deaths"] += 1

        if killer_id == opponent_id:
            result["opponent_kills"] += 1
        if opponent_id in assists:
            result["opponent_assists"] += 1
        if victim_id == opponent_id:
            result["opponent_deaths"] += 1

    result["player_combat_involvement"] = (
        result["player_kills"]
        + result["player_assists"]
        + result["player_deaths"]
    )

    result["opponent_combat_involvement"] = (
        result["opponent_kills"]
        + result["opponent_assists"]
        + result["opponent_deaths"]
    )

    return result


def _tower_kill_counts(events, bundle):
    my_team = bundle["my_team_id"]
    result = {
        "ally_towers": 0,
        "enemy_towers": 0,
        "ally_plates": 0,
        "enemy_plates": 0,
    }

    for event in events:
        event_type = event.get("type")

        if event_type == "BUILDING_KILL":
            raw = event.get("raw") or {}
            building_type = str(raw.get("buildingType") or "").upper()
            if "TOWER" not in building_type:
                continue

            destroyed_team = event.get("team_id")
            if destroyed_team == my_team:
                result["enemy_towers"] += 1
            elif destroyed_team in (100, 200):
                result["ally_towers"] += 1

        elif event_type == "TURRET_PLATE_DESTROYED":
            destroyed_team = event.get("team_id")
            if destroyed_team == my_team:
                result["enemy_plates"] += 1
            elif destroyed_team in (100, 200):
                result["ally_plates"] += 1

    return result


def _objective_team_side(team_id, bundle):
    if team_id == bundle["my_team_id"]:
        return "ALLY"
    if team_id == bundle["opponent_team_id"]:
        return "ENEMY"
    return "UNKNOWN"


def _counter_objectives(
    all_objectives,
    current,
    bundle,
    start_ms,
    end_ms,
):
    ally = []
    enemy = []

    for objective in all_objectives:
        if objective is current:
            continue
        if not (start_ms <= objective["timestamp"] <= end_ms):
            continue

        side = _objective_team_side(objective.get("team_id"), bundle)
        if side == "ALLY":
            ally.append(objective)
        elif side == "ENEMY":
            enemy.append(objective)

    return ally, enemy


# ============================================================
# DEATH INTEGRATION
# ============================================================

def _death_context(deaths, timestamp):
    pre120 = [
        row
        for row in deaths
        if timestamp - 120_000 <= row["timestamp"] < timestamp
    ]
    pre60 = [
        row
        for row in deaths
        if timestamp - 60_000 <= row["timestamp"] < timestamp
    ]
    pre30 = [
        row
        for row in deaths
        if timestamp - 30_000 <= row["timestamp"] < timestamp
    ]
    post60 = [
        row
        for row in deaths
        if timestamp <= row["timestamp"] <= timestamp + 60_000
    ]
    post120 = [
        row
        for row in deaths
        if timestamp <= row["timestamp"] <= timestamp + 120_000
    ]

    previous = [row for row in deaths if row["timestamp"] < timestamp]
    nearest_pre = max(previous, key=lambda row: row["timestamp"]) if previous else None

    severe_values = [
        row.get("death_severity_score")
        for row in pre120
        if row.get("death_severity_score") is not None
    ]

    return {
        "player_deaths_pre120": len(pre120),
        "player_deaths_pre60": len(pre60),
        "player_deaths_pre30": len(pre30),
        "player_deaths_post60": len(post60),
        "player_deaths_post120": len(post120),
        "nearest_player_death_before_seconds": (
            (timestamp - nearest_pre["timestamp"]) / 1000
            if nearest_pre
            else None
        ),
        "max_pre120_death_severity": max(severe_values) if severe_values else None,
        "pre120_death_rows": pre120,
    }


def _jungler_death_timestamps(bundle):
    my_id = bundle["my_participant_id"]
    opponent_id = bundle["opponent_participant_id"]
    player = []
    opponent = []

    for event in bundle.get("events", []):
        if event.get("type") != "CHAMPION_KILL":
            continue

        victim_id = event.get("victim_id")
        timestamp = event.get("timestamp", 0)

        if victim_id == my_id:
            player.append(timestamp)
        elif victim_id == opponent_id:
            opponent.append(timestamp)

    return sorted(player), sorted(opponent)


def _count_timestamps(timestamps, start_ms, end_ms):
    left = bisect_left(timestamps, start_ms)
    right = bisect_right(timestamps, end_ms)
    return max(0, right - left)


# ============================================================
# FROZEN TEMPO/PATHING INTEGRATION
# ============================================================

def _weighted_interval_mean(rows, key):
    values = []

    for row in rows:
        value = row.get(key)
        if value is None:
            continue
        weight = row.get("duration_minutes") or 1.0
        values.append((value, weight))

    total_weight = sum(weight for _, weight in values)
    if total_weight <= 0:
        return None

    return sum(value * weight for value, weight in values) / total_weight


def _tempo_window_context(tempo_rows, start_ms, end_ms, prefix):
    rows = [
        row
        for row in tempo_rows
        if (
            row.get("end_timestamp", 0) > start_ms
            and row.get("start_timestamp", 0) < end_ms
        )
    ]

    if not rows:
        return {
            f"{prefix}_tempo_intervals": 0,
            f"{prefix}_tempo_score": None,
            f"{prefix}_pathing_score": None,
            f"{prefix}_sustained_pathing_holes": 0,
            f"{prefix}_pathing_watches": 0,
        }

    return {
        f"{prefix}_tempo_intervals": len(rows),
        f"{prefix}_tempo_score": _weighted_interval_mean(
            rows,
            "tempo_score",
        ),
        f"{prefix}_pathing_score": _weighted_interval_mean(
            [row for row in rows if row.get("farmable_tempo_interval")],
            "pathing_score",
        ),
        f"{prefix}_sustained_pathing_holes": len({
            row.get("pathing_hole_episode_id")
            for row in rows
            if row.get("sustained_pathing_hole")
            and row.get("pathing_hole_episode_id")
        }),
        f"{prefix}_pathing_watches": sum(
            1
            for row in rows
            if row.get("single_minute_pathing_watch")
            and not row.get("sustained_pathing_hole")
        ),
    }


def _shopping_counts(events, bundle):
    my_id = bundle["my_participant_id"]
    opponent_id = bundle["opponent_participant_id"]

    player = 0
    opponent = 0

    for event in events:
        if event.get("type") != "ITEM_PURCHASED":
            continue

        participant_id = event.get("participant_id")
        if participant_id == my_id:
            player += 1
        elif participant_id == opponent_id:
            opponent += 1

    return {
        "player_item_purchases": player,
        "opponent_item_purchases": opponent,
    }


# ============================================================
# OBJECTIVE ANALYSIS
# ============================================================

def _contest_evidence(
    player_distance,
    opponent_distance,
    spatial_fight_context,
):
    """
    V20 : contest evidence plus exigeant.

    HIGH
      = fight spatial proche ET implication d'au moins un des deux junglers,
        OU fight spatial proche avec les deux junglers NEAR.

    MEDIUM
      = fight spatial proche sans implication jungle explicite,
        OU les deux junglers sont au moins MID.

    LOW
      = un seul jungler est au moins MID/NEAR.

    UNKNOWN
      = aucune preuve exploitable.

    Un kill de laner proche du pit ne suffit donc plus à classer HIGH.
    """
    player_near = (
        player_distance is not None
        and player_distance <= OBJECTIVE_PROXIMITY_NEAR
    )
    opponent_near = (
        opponent_distance is not None
        and opponent_distance <= OBJECTIVE_PROXIMITY_NEAR
    )

    player_mid = (
        player_distance is not None
        and player_distance <= OBJECTIVE_PROXIMITY_MID
    )
    opponent_mid = (
        opponent_distance is not None
        and opponent_distance <= OBJECTIVE_PROXIMITY_MID
    )

    spatial_fight_happened = (
        spatial_fight_context["ally_champion_kills"]
        + spatial_fight_context["enemy_champion_kills"]
    ) > 0

    jungler_involved = (
        spatial_fight_context["player_combat_involvement"] > 0
        or spatial_fight_context["opponent_combat_involvement"] > 0
    )

    if spatial_fight_happened and (
        jungler_involved
        or (player_near and opponent_near)
    ):
        return "HIGH"

    if spatial_fight_happened or (
        player_mid and opponent_mid
    ):
        return "MEDIUM"

    if player_mid or opponent_mid:
        return "LOW"

    return "UNKNOWN"


def _resource_compensation_components(conversion):
    """
    Retourne des preuves de compensation réellement significatives.

    Les changements sont mesurés sur ~120 s. On ne considère plus
    +1 Gold / +1 XP comme une compensation.
    """
    values = {
        "gold": conversion.get("conversion_relative_gold_change"),
        "xp": conversion.get("conversion_relative_xp_change"),
        "jungle_cs": conversion.get(
            "conversion_relative_jungle_cs_change"
        ),
    }

    favorable = {
        "gold": (
            values["gold"] is not None
            and values["gold"] >= RESOURCE_COMPENSATION_GOLD
        ),
        "xp": (
            values["xp"] is not None
            and values["xp"] >= RESOURCE_COMPENSATION_XP
        ),
        "jungle_cs": (
            values["jungle_cs"] is not None
            and values["jungle_cs"] >= RESOURCE_COMPENSATION_JUNGLE_CS
        ),
    }

    unfavorable = {
        "gold": (
            values["gold"] is not None
            and values["gold"] <= -RESOURCE_COMPENSATION_GOLD
        ),
        "xp": (
            values["xp"] is not None
            and values["xp"] <= -RESOURCE_COMPENSATION_XP
        ),
        "jungle_cs": (
            values["jungle_cs"] is not None
            and values["jungle_cs"] <= -RESOURCE_COMPENSATION_JUNGLE_CS
        ),
    }

    return values, favorable, unfavorable


def _trade_evidence(
    secured_side,
    ally_counter_objectives,
    enemy_counter_objectives,
    tower_context,
    conversion,
):
    _, favorable, unfavorable = _resource_compensation_components(
        conversion
    )

    if secured_side == "ENEMY":
        if ally_counter_objectives:
            return "ALLY_COUNTER_OBJECTIVE"

        if tower_context["ally_towers"] > 0:
            return "ALLY_TOWER_COMPENSATION"

        # Compensation pure ressources :
        # au moins 2 dimensions franchissent un seuil significatif.
        if sum(favorable.values()) >= 2:
            return "ALLY_RESOURCE_COMPENSATION"

    elif secured_side == "ALLY":
        if enemy_counter_objectives:
            return "ENEMY_COUNTER_OBJECTIVE"

        if tower_context["enemy_towers"] > 0:
            return "ENEMY_TOWER_COMPENSATION"

        if sum(unfavorable.values()) >= 2:
            return "ENEMY_RESOURCE_GIVEBACK"

    return "NONE"


def _sequence_classification(row):
    side = row["secured_side"]

    if side == "ENEMY":
        if row["player_deaths_pre60"] > 0:
            return "LOST_AFTER_SHORT_PRE_DEATH"
        if row["trade_evidence"].startswith("ALLY_"):
            return "LOST_WITH_COMPENSATION"
        if row["contest_evidence"] in ("HIGH", "MEDIUM"):
            return "LOST_WITH_CONTEST_EVIDENCE"
        return "LOST_LOW_INFORMATION"

    if side == "ALLY":
        if row["trade_evidence"].startswith("ENEMY_"):
            return "SECURED_WITH_GIVEBACK"
        if row["player_deaths_post60"] > 0:
            return "SECURED_THEN_PLAYER_DEATH"
        return "SECURED"

    return "UNKNOWN_RESULT"


def _analyze_objective(
    bundle,
    objective,
    all_objectives,
    death_rows,
    tempo_rows,
):
    timestamp = objective["timestamp"]
    frames = bundle["frames"]
    frame_ts = _frame_timestamps(frames)
    event_idx = _event_index(bundle.get("events", []))

    prep_start_pair = _frame_before_or_at(
        frames,
        frame_ts,
        max(0, timestamp - OBJECTIVE_PREP_SECONDS * 1000),
    )
    approach_start_pair = _frame_before_or_at(
        frames,
        frame_ts,
        max(0, timestamp - OBJECTIVE_APPROACH_SECONDS * 1000),
    )
    pre_pair = _frame_before_or_at(frames, frame_ts, timestamp)

    post_pair = _frame_after_or_at(frames, frame_ts, timestamp)
    post60_pair = _frame_after_or_at(
        frames,
        frame_ts,
        timestamp + 60_000,
    )
    post120_pair = _frame_after_or_at(
        frames,
        frame_ts,
        timestamp + OBJECTIVE_CONVERSION_SECONDS * 1000,
    )

    prep = _window_delta(prep_start_pair, pre_pair, "prep")
    approach = _window_delta(approach_start_pair, pre_pair, "approach")
    conversion60 = _window_delta(post_pair, post60_pair, "conversion60")
    conversion = _window_delta(post_pair, post120_pair, "conversion")

    pre_state = _relative_state(pre_pair)
    post_state = _relative_state(post_pair)

    objective_x = objective.get("x")
    objective_y = objective.get("y")

    player_distance = _distance_to_objective(
        pre_state,
        objective_x,
        objective_y,
        "player",
    )
    opponent_distance = _distance_to_objective(
        pre_state,
        objective_x,
        objective_y,
        "opponent",
    )

    fight_events = _events_between(
        event_idx,
        max(0, timestamp - OBJECTIVE_FIGHT_PRE_SECONDS * 1000),
        timestamp + OBJECTIVE_FIGHT_POST_SECONDS * 1000,
    )

    # V19 : on sépare les kills simplement proches dans le TEMPS
    # des kills réellement proches de l'OBJECTIF dans l'espace.
    temporal_fight_context = _team_kill_counts(
        fight_events,
        bundle,
    )

    spatial_fight = _spatial_fight_events(
        fight_events,
        objective_x,
        objective_y,
    )

    fight_context = _team_kill_counts(
        spatial_fight["events"],
        bundle,
    )

    # V20 : séparation temporelle stricte.
    # Ce qui arrive AVANT l'objectif décrit le contexte de trade précédent.
    # Ce qui arrive APRÈS l'objectif peut être une compensation/giveback.
    pre_trade_events = _events_between(
        event_idx,
        max(0, timestamp - OBJECTIVE_TRADE_PRE_SECONDS * 1000),
        timestamp - 1,
    )
    post_trade_events = _events_between(
        event_idx,
        timestamp,
        timestamp + OBJECTIVE_TRADE_POST_SECONDS * 1000,
    )

    prior_tower_context = _tower_kill_counts(
        pre_trade_events,
        bundle,
    )
    tower_context = _tower_kill_counts(
        post_trade_events,
        bundle,
    )

    prep_events = _events_between(
        event_idx,
        max(0, timestamp - OBJECTIVE_PREP_SECONDS * 1000),
        timestamp - 1,
    )
    post_events = _events_between(
        event_idx,
        timestamp,
        timestamp + OBJECTIVE_CONVERSION_SECONDS * 1000,
    )

    prep_shop_context = _shopping_counts(prep_events, bundle)
    post_shop_context = _shopping_counts(post_events, bundle)

    frozen_pre_tempo = _tempo_window_context(
        tempo_rows,
        max(0, timestamp - OBJECTIVE_PREP_SECONDS * 1000),
        timestamp,
        "frozen_pre",
    )
    frozen_post_tempo = _tempo_window_context(
        tempo_rows,
        timestamp,
        timestamp + OBJECTIVE_CONVERSION_SECONDS * 1000,
        "frozen_post",
    )

    # Compensations/givebacks = uniquement APRÈS l'objectif courant.
    ally_counter, enemy_counter = _counter_objectives(
        all_objectives,
        objective,
        bundle,
        timestamp + 1,
        timestamp + OBJECTIVE_TRADE_POST_SECONDS * 1000,
    )

    # Contexte antérieur séparé : permet de dire que l'objectif courant
    # est lui-même une compensation d'un objectif ennemi précédent,
    # sans le traiter à tort comme un giveback.
    prior_ally_objectives, prior_enemy_objectives = _counter_objectives(
        all_objectives,
        objective,
        bundle,
        max(0, timestamp - OBJECTIVE_TRADE_PRE_SECONDS * 1000),
        timestamp - 1,
    )

    death_context = _death_context(death_rows, timestamp)
    player_deaths, opponent_deaths = _jungler_death_timestamps(bundle)

    secured_side = _objective_team_side(objective.get("team_id"), bundle)

    killer_id = objective.get("killer_id")
    killer_player = bundle.get("players", {}).get(killer_id)
    killer_position = killer_player.get("position") if killer_player else None

    contest = _contest_evidence(
        player_distance,
        opponent_distance,
        fight_context,
    )

    trade = _trade_evidence(
        secured_side,
        ally_counter,
        enemy_counter,
        tower_context,
        conversion,
    )

    if (
        secured_side == "ALLY"
        and prior_enemy_objectives
    ):
        prior_trade_context = "ALLY_SECURED_AS_COUNTER_OBJECTIVE"
    elif (
        secured_side == "ENEMY"
        and prior_ally_objectives
    ):
        prior_trade_context = "ENEMY_SECURED_AS_COUNTER_OBJECTIVE"
    elif (
        secured_side == "ALLY"
        and prior_tower_context["enemy_towers"] > 0
    ):
        prior_trade_context = "ALLY_SECURED_AFTER_ENEMY_TOWER"
    elif (
        secured_side == "ENEMY"
        and prior_tower_context["ally_towers"] > 0
    ):
        prior_trade_context = "ENEMY_SECURED_AFTER_ALLY_TOWER"
    else:
        prior_trade_context = "NONE"

    (
        resource_values,
        resource_favorable,
        resource_unfavorable,
    ) = _resource_compensation_components(
        conversion
    )

    row = {
        "match_id": bundle["match_id"],
        "game_creation": bundle["game_creation"],
        "game_duration": bundle["game_duration"],
        "champion": bundle["champion"],
        "opponent_champion": bundle["opponent_champion"],
        "win": bundle["win"],

        "objective_index": objective["objective_index"],
        "timestamp": timestamp,
        "minute": timestamp / 60_000,
        "objective_kind": objective["kind"],
        "objective_family": objective["family"],
        "monster_type": objective.get("monster_type"),
        "monster_sub_type": objective.get("monster_sub_type"),
        "grub_kills": objective.get("grub_kills"),
        "grub_team_counts": objective.get("grub_team_counts"),

        "objective_team_id": objective.get("team_id"),
        "secured_side": secured_side,
        "secured_by_ally": secured_side == "ALLY",
        "secured_by_enemy": secured_side == "ENEMY",
        "killer_id": killer_id,
        "killer_position": killer_position,
        "player_secured_objective": killer_id == bundle["my_participant_id"],
        "enemy_jungler_secured_objective": (
            killer_id == bundle["opponent_participant_id"]
        ),

        "objective_x": objective_x,
        "objective_y": objective_y,
        "player_distance_pre": player_distance,
        "opponent_distance_pre": opponent_distance,
        "player_proximity_pre": _proximity_label(player_distance),
        "opponent_proximity_pre": _proximity_label(opponent_distance),

        "entry_gold_diff": pre_state.get("gold_diff") if pre_state else None,
        "entry_xp_diff": pre_state.get("xp_diff") if pre_state else None,
        "entry_jungle_cs_diff": (
            pre_state.get("jungle_cs_diff") if pre_state else None
        ),
        "entry_level_diff": pre_state.get("level_diff") if pre_state else None,
        "entry_player_current_gold": (
            pre_state.get("player_current_gold") if pre_state else None
        ),
        "entry_state": (
            _state_from_diffs(
                pre_state.get("gold_diff", 0),
                pre_state.get("xp_diff", 0),
                pre_state.get("jungle_cs_diff", 0),
            )
            if pre_state
            else "UNKNOWN"
        ),

        "post_gold_diff": post_state.get("gold_diff") if post_state else None,
        "post_xp_diff": post_state.get("xp_diff") if post_state else None,
        "post_jungle_cs_diff": (
            post_state.get("jungle_cs_diff") if post_state else None
        ),

        # Fight / contest diagnostics.
        # Les champs non préfixés représentent désormais uniquement
        # les kills localisés près de l'objectif.
        "contest_evidence": contest,
        "contest_spatial_radius": OBJECTIVE_FIGHT_SPATIAL_RADIUS,
        "contest_spatial_near_kills": spatial_fight["near_kills"],
        "contest_spatial_located_kills": spatial_fight["located_kills"],
        "contest_spatial_unlocated_kills": spatial_fight["unlocated_kills"],

        "temporal_ally_champion_kills": temporal_fight_context[
            "ally_champion_kills"
        ],
        "temporal_enemy_champion_kills": temporal_fight_context[
            "enemy_champion_kills"
        ],
        "temporal_player_combat_involvement": temporal_fight_context[
            "player_combat_involvement"
        ],
        "temporal_opponent_combat_involvement": temporal_fight_context[
            "opponent_combat_involvement"
        ],

        "trade_evidence": trade,
        "prior_trade_context": prior_trade_context,

        "prior_ally_objectives": [
            row.get("objective_kind")
            or row.get("kind")
            or "UNKNOWN"
            for row in prior_ally_objectives
        ],
        "prior_enemy_objectives": [
            row.get("objective_kind")
            or row.get("kind")
            or "UNKNOWN"
            for row in prior_enemy_objectives
        ],
        "prior_ally_towers": prior_tower_context["ally_towers"],
        "prior_enemy_towers": prior_tower_context["enemy_towers"],

        "resource_compensation_gold_change": resource_values["gold"],
        "resource_compensation_xp_change": resource_values["xp"],
        "resource_compensation_jungle_cs_change": resource_values["jungle_cs"],
        "resource_favorable_components": sum(resource_favorable.values()),
        "resource_unfavorable_components": sum(resource_unfavorable.values()),

        "ally_counter_objectives": [
            row.get("objective_kind")
            or row.get("kind")
            or "UNKNOWN"
            for row in ally_counter
        ],
        "enemy_counter_objectives": [
            row.get("objective_kind")
            or row.get("kind")
            or "UNKNOWN"
            for row in enemy_counter
        ],

        "pre_player_item_purchases": prep_shop_context["player_item_purchases"],
        "pre_opponent_item_purchases": prep_shop_context["opponent_item_purchases"],
        "post_player_item_purchases": post_shop_context["player_item_purchases"],
        "post_opponent_item_purchases": post_shop_context["opponent_item_purchases"],

        **frozen_pre_tempo,
        **frozen_post_tempo,

        **fight_context,
        **tower_context,
        **death_context,

        "opponent_deaths_pre60": _count_timestamps(
            opponent_deaths,
            max(0, timestamp - 60_000),
            timestamp - 1,
        ),
        "opponent_deaths_post60": _count_timestamps(
            opponent_deaths,
            timestamp,
            timestamp + 60_000,
        ),

        **prep,
        **approach,
        **conversion60,
        **conversion,

        "preparation_score": None,
        "preparation_label": "WARMUP",
        "preparation_reference_size": 0,
        "preparation_reference_scope": "UNSCORED",

        "conversion_score": None,
        "conversion_label": "WARMUP",
        "conversion_reference_size": 0,
        "conversion_reference_scope": "UNSCORED",
    }

    row["frozen_tempo_score_change"] = (
        row["frozen_post_tempo_score"]
        - row["frozen_pre_tempo_score"]
        if (
            row.get("frozen_pre_tempo_score") is not None
            and row.get("frozen_post_tempo_score") is not None
        )
        else None
    )

    row["frozen_pathing_score_change"] = (
        row["frozen_post_pathing_score"]
        - row["frozen_pre_pathing_score"]
        if (
            row.get("frozen_pre_pathing_score") is not None
            and row.get("frozen_post_pathing_score") is not None
        )
        else None
    )

    row["sequence_classification"] = _sequence_classification(row)

    # Explicitly separate availability risk from resource preparation.
    row["short_pre_objective_death"] = row["player_deaths_pre60"] > 0
    row["pre_objective_death"] = row["player_deaths_pre120"] > 0
    row["opponent_short_pre_objective_death"] = row["opponent_deaths_pre60"] > 0

    return row


def build_objective_dataset(
    bundles,
    death_dataset=None,
    tempo_intervals=None,
):
    death_dataset = death_dataset or []
    tempo_intervals = tempo_intervals or []

    deaths_by_match = defaultdict(list)
    for death in death_dataset:
        deaths_by_match[death["match_id"]].append(death)

    tempo_by_match = defaultdict(list)
    for interval in tempo_intervals:
        tempo_by_match[interval["match_id"]].append(interval)

    dataset = []

    for bundle in bundles:
        objectives = _normalize_objective_events(bundle)
        deaths = sorted(
            deaths_by_match.get(bundle["match_id"], []),
            key=lambda row: row["timestamp"],
        )

        for objective in objectives:
            dataset.append(
                _analyze_objective(
                    bundle,
                    objective,
                    objectives,
                    deaths,
                    tempo_by_match.get(
                        bundle["match_id"],
                        [],
                    ),
                )
            )

    dataset.sort(
        key=lambda row: (
            row["game_creation"],
            row["match_id"],
            row["timestamp"],
        )
    )

    _attach_historical_objective_scores(dataset)
    return dataset


# ============================================================
# HISTORICAL-ONLY OBJECTIVE SCORES
# ============================================================

def _historical_score(row, reference, weights):
    percentiles = {}

    for feature in weights:
        value = row.get(feature)
        values = [
            old_row.get(feature)
            for old_row in reference
            if old_row.get(feature) is not None
        ]

        if value is None or not values:
            continue

        percentiles[feature] = percentile_rank(values, value)

    total_weight = 0.0
    weighted_sum = 0.0

    for feature, weight in weights.items():
        if feature not in percentiles:
            continue
        weighted_sum += percentiles[feature] * weight
        total_weight += weight

    if total_weight <= 0:
        return None, percentiles

    return weighted_sum / total_weight, percentiles


def _attach_historical_objective_scores(dataset):
    by_match = defaultdict(list)
    match_creation = {}

    for row in dataset:
        by_match[row["match_id"]].append(row)
        match_creation[row["match_id"]] = row["game_creation"]

    ordered_match_ids = sorted(
        by_match,
        key=lambda match_id: (
            match_creation[match_id],
            match_id,
        ),
    )

    history_family = defaultdict(list)
    history_family_champion = defaultdict(list)

    def choose_reference(row):
        family = row["objective_family"]
        champion = row["champion"]
        target = row["timestamp"]
        radius = OBJECTIVE_TIME_REFERENCE_RADIUS_SECONDS * 1000

        champion_history = history_family_champion[(family, champion)]
        family_history = history_family[family]

        champion_local = [
            old
            for old in champion_history
            if abs(old["timestamp"] - target) <= radius
        ]
        family_local = [
            old
            for old in family_history
            if abs(old["timestamp"] - target) <= radius
        ]

        candidates = (
            ("CHAMPION_FAMILY_TIME", champion_local, MIN_HISTORICAL_OBJECTIVE_TIME_REFERENCE),
            ("FAMILY_TIME", family_local, MIN_HISTORICAL_OBJECTIVE_TIME_REFERENCE),
            ("CHAMPION_FAMILY", champion_history, MIN_HISTORICAL_OBJECTIVE_REFERENCE),
            ("FAMILY", family_history, MIN_HISTORICAL_OBJECTIVE_REFERENCE),
        )

        for scope, reference, minimum in candidates:
            if len(reference) >= minimum:
                return scope, reference

        return "WARMUP", []

    for match_id in ordered_match_ids:
        rows = sorted(
            by_match[match_id],
            key=lambda row: row["timestamp"],
        )

        for row in rows:
            scope, reference = choose_reference(row)

            row["preparation_reference_scope"] = scope
            row["preparation_reference_size"] = len(reference)
            row["conversion_reference_scope"] = scope
            row["conversion_reference_size"] = len(reference)

            if not reference:
                continue

            prep_score, prep_percentiles = _historical_score(
                row,
                reference,
                PREPARATION_SCORE_WEIGHTS,
            )
            conv_score, conv_percentiles = _historical_score(
                row,
                reference,
                CONVERSION_SCORE_WEIGHTS,
            )

            row["preparation_score"] = prep_score
            row["preparation_label"] = _score_label(prep_score)
            row["conversion_score"] = conv_score
            row["conversion_label"] = _score_label(conv_score)

            for feature, value in prep_percentiles.items():
                row[f"{feature}_percentile"] = value

            for feature, value in conv_percentiles.items():
                row[f"{feature}_percentile"] = value

        # No objective from the current match influences another objective
        # in the same match. The whole game is added only afterwards.
        for row in rows:
            family = row["objective_family"]
            champion = row["champion"]
            history_family[family].append(row)
            history_family_champion[(family, champion)].append(row)


# ============================================================
# GAME-LEVEL AGGREGATION
# ============================================================

def _objective_rows_by_match(dataset):
    result = defaultdict(list)
    for row in dataset:
        result[row["match_id"]].append(row)
    return result


def _rate(count, total):
    if total <= 0:
        return None
    return count / total


def _sum_list(values):
    return sum(value for value in values if value is not None)


def _build_objective_game_row(bundle, rows):
    total = len(rows)
    ally = [row for row in rows if row["secured_side"] == "ALLY"]
    enemy = [row for row in rows if row["secured_side"] == "ENEMY"]

    scored_prep = [row for row in rows if row.get("preparation_score") is not None]
    scored_conv = [row for row in rows if row.get("conversion_score") is not None]

    lost = enemy
    secured = ally

    game_minutes = bundle["game_duration"] / 60 if bundle["game_duration"] else 0

    return {
        "match_id": bundle["match_id"],
        "game_creation": bundle["game_creation"],
        "champion": bundle["champion"],
        "win": bundle["win"],
        "game_duration": bundle["game_duration"],

        "objective_sequences": total,
        "ally_objectives": len(ally),
        "enemy_objectives": len(enemy),
        "ally_objective_rate": _rate(len(ally), total),

        # Personal availability around objective opportunities.
        "pre_objective_death_120_count": sum(row["pre_objective_death"] for row in rows),
        "pre_objective_death_60_count": sum(row["short_pre_objective_death"] for row in rows),
        "pre_objective_death_120_rate": _rate(
            sum(row["pre_objective_death"] for row in rows),
            total,
        ),
        "pre_objective_death_60_rate": _rate(
            sum(row["short_pre_objective_death"] for row in rows),
            total,
        ),

        # Raw preparation measurements.
        "mean_prep_player_xp_per_min": _safe_mean(
            [row.get("prep_player_xp_per_min") for row in rows]
        ),
        "mean_prep_player_jungle_cs_per_min": _safe_mean(
            [row.get("prep_player_jungle_cs_per_min") for row in rows]
        ),
        "mean_prep_relative_gold_per_min": _safe_mean(
            [row.get("prep_relative_gold_per_min") for row in rows]
        ),
        "mean_prep_relative_xp_per_min": _safe_mean(
            [row.get("prep_relative_xp_per_min") for row in rows]
        ),
        "mean_prep_relative_jungle_cs_per_min": _safe_mean(
            [row.get("prep_relative_jungle_cs_per_min") for row in rows]
        ),

        "mean_preparation_score": _safe_mean(
            [row.get("preparation_score") for row in scored_prep]
        ),
        "low_preparation_rate": _rate(
            sum(
                row.get("preparation_score") is not None
                and row["preparation_score"] < 25
                for row in rows
            ),
            len(scored_prep),
        ),

        # Conversion / compensation measurements.
        "mean_conversion_player_xp_per_min": _safe_mean(
            [row.get("conversion_player_xp_per_min") for row in rows]
        ),
        "mean_conversion_player_jungle_cs_per_min": _safe_mean(
            [row.get("conversion_player_jungle_cs_per_min") for row in rows]
        ),
        "mean_conversion_relative_gold_per_min": _safe_mean(
            [row.get("conversion_relative_gold_per_min") for row in rows]
        ),
        "mean_conversion_relative_xp_per_min": _safe_mean(
            [row.get("conversion_relative_xp_per_min") for row in rows]
        ),
        "mean_conversion_relative_jungle_cs_per_min": _safe_mean(
            [row.get("conversion_relative_jungle_cs_per_min") for row in rows]
        ),
        "mean_conversion_score": _safe_mean(
            [row.get("conversion_score") for row in scored_conv]
        ),

        "secured_mean_conversion_score": _safe_mean(
            [row.get("conversion_score") for row in secured]
        ),
        "lost_mean_conversion_score": _safe_mean(
            [row.get("conversion_score") for row in lost]
        ),
        "lost_with_compensation_rate": _rate(
            sum(
                row["trade_evidence"].startswith("ALLY_")
                for row in lost
            ),
            len(lost),
        ),

        # Frozen Tempo/Pathing integration - composites from v17.
        "mean_frozen_pre_tempo_score": _safe_mean(
            [row.get("frozen_pre_tempo_score") for row in rows]
        ),
        "mean_frozen_post_tempo_score": _safe_mean(
            [row.get("frozen_post_tempo_score") for row in rows]
        ),
        "mean_frozen_tempo_score_change": _safe_mean(
            [row.get("frozen_tempo_score_change") for row in rows]
        ),
        "mean_frozen_pre_pathing_score": _safe_mean(
            [row.get("frozen_pre_pathing_score") for row in rows]
        ),
        "pre_objective_pathing_holes": sum(
            row.get("frozen_pre_sustained_pathing_holes", 0)
            for row in rows
        ),

        # Context only.
        "contest_high_medium_rate": _rate(
            sum(row["contest_evidence"] in ("HIGH", "MEDIUM") for row in rows),
            total,
        ),
        "player_secured_objective_count": sum(
            row["player_secured_objective"] for row in rows
        ),
        "enemy_jungler_secured_objective_count": sum(
            row["enemy_jungler_secured_objective"] for row in rows
        ),
        "ally_towers_near_objectives": _sum_list(
            [row.get("ally_towers") for row in rows]
        ),
        "enemy_towers_near_objectives": _sum_list(
            [row.get("enemy_towers") for row in rows]
        ),

        "objective_sequences_per_10": (
            total * 10 / game_minutes
            if game_minutes > 0
            else None
        ),
    }


def build_game_objective_dataset(objective_dataset, bundles):
    rows_by_match = _objective_rows_by_match(objective_dataset)
    result = []

    for bundle in bundles:
        rows = rows_by_match.get(bundle["match_id"], [])
        result.append(_build_objective_game_row(bundle, rows))

    result.sort(
        key=lambda row: (
            row["game_creation"],
            row["match_id"],
        )
    )
    return result


def build_objective_family_game_dataset(objective_dataset, bundles):
    rows_by_match = _objective_rows_by_match(objective_dataset)
    result = []

    for bundle in bundles:
        rows = rows_by_match.get(bundle["match_id"], [])
        by_family = defaultdict(list)

        for row in rows:
            by_family[row["objective_family"]].append(row)

        for family, family_rows in by_family.items():
            game_row = _build_objective_game_row(bundle, family_rows)
            game_row["objective_family"] = family
            result.append(game_row)

    result.sort(
        key=lambda row: (
            row["game_creation"],
            row["match_id"],
            row["objective_family"],
        )
    )
    return result


# ============================================================
# PROFILE / AUDIT / MATCH RENDERING
# ============================================================

def summarize_objective_profile(game_dataset, win=None):
    rows = [
        row
        for row in game_dataset
        if win is None or row["win"] == win
    ]

    if not rows:
        return None

    def med(key):
        return _safe_median([row.get(key) for row in rows])

    return {
        "games": len(rows),
        "objective_sequences": med("objective_sequences"),
        "ally_objective_rate": med("ally_objective_rate"),
        "pre_death_60_rate": med("pre_objective_death_60_rate"),
        "prep_xp": med("mean_prep_player_xp_per_min"),
        "prep_jcs": med("mean_prep_player_jungle_cs_per_min"),
        "prep_rel_xp": med("mean_prep_relative_xp_per_min"),
        "prep_rel_jcs": med("mean_prep_relative_jungle_cs_per_min"),
        "prep_score": med("mean_preparation_score"),
        "conv_rel_gold": med("mean_conversion_relative_gold_per_min"),
        "conv_rel_xp": med("mean_conversion_relative_xp_per_min"),
        "conv_rel_jcs": med("mean_conversion_relative_jungle_cs_per_min"),
        "conv_score": med("mean_conversion_score"),
        "lost_compensation": med("lost_with_compensation_rate"),
        "frozen_pre_tempo": med("mean_frozen_pre_tempo_score"),
        "frozen_post_tempo": med("mean_frozen_post_tempo_score"),
        "frozen_tempo_change": med("mean_frozen_tempo_score_change"),
    }


def render_objective_profile(title, summary):
    lines = [
        "================================",
        title,
        "================================",
    ]

    if not summary:
        lines.append("Pas assez de données.")
        return "\n".join(lines)

    def fmt(value, pattern="{:.1f}"):
        return "N/A" if value is None else pattern.format(value)

    lines.extend([
        "",
        f"Games : {summary['games']}",
        f"Séquences objectifs / game (médiane) : {fmt(summary['objective_sequences'])}",
        f"Taux objectifs équipe (CONTEXTE) : {fmt(summary['ally_objective_rate'], '{:.1%}')}",
        f"Mort joueur <60s avant objectif : {fmt(summary['pre_death_60_rate'], '{:.1%}')}",
        "",
        "Préparation - production personnelle :",
        f"  XP/min  : {fmt(summary['prep_xp'], '{:.0f}')}",
        f"  JCS/min : {fmt(summary['prep_jcs'], '{:.2f}')}",
        "Préparation - variation vs JGL :",
        f"  XP/min  : {fmt(summary['prep_rel_xp'], '{:+.0f}')}",
        f"  JCS/min : {fmt(summary['prep_rel_jcs'], '{:+.2f}')}",
        f"Preparation Score historique : {fmt(summary['prep_score'], '{:.0f}/100')}",
        "",
        "Conversion / compensation +120s :",
        f"  Gold relatif/min : {fmt(summary['conv_rel_gold'], '{:+.0f}')}",
        f"  XP relatif/min   : {fmt(summary['conv_rel_xp'], '{:+.0f}')}",
        f"  JCS relatif/min  : {fmt(summary['conv_rel_jcs'], '{:+.2f}')}",
        f"Conversion Score historique : {fmt(summary['conv_score'], '{:.0f}/100')}",
        f"Objectifs perdus avec compensation détectée : {fmt(summary['lost_compensation'], '{:.1%}')}",
        "",
        "Intégration Tempo/Pathing v17 (scores historical-only déjà figés) :",
        f"  Tempo avant objectif : {fmt(summary['frozen_pre_tempo'], '{:.0f}/100')}",
        f"  Tempo après objectif : {fmt(summary['frozen_post_tempo'], '{:.0f}/100')}",
        f"  Variation Tempo : {fmt(summary['frozen_tempo_change'], '{:+.1f}')}",
    ])

    return "\n".join(lines)


def render_objective_audit(objective_dataset):
    kind_counts = defaultdict(int)
    side_counts = defaultdict(int)
    classification_counts = defaultdict(int)
    contest_counts = defaultdict(int)
    trade_counts = defaultdict(int)
    prior_trade_counts = defaultdict(int)

    missing_prep = 0
    missing_conversion = 0
    unknown_team = 0
    warmup_prep = 0
    warmup_conversion = 0

    spatial_near_kills = 0
    spatial_located_kills = 0
    spatial_unlocated_kills = 0
    resource_compensation_sequences = 0
    resource_giveback_sequences = 0

    for row in objective_dataset:
        kind_counts[row["objective_kind"]] += 1
        side_counts[row["secured_side"]] += 1
        classification_counts[row["sequence_classification"]] += 1
        contest_counts[row["contest_evidence"]] += 1
        trade_counts[row["trade_evidence"]] += 1
        prior_trade_counts[
            row.get("prior_trade_context", "NONE")
        ] += 1

        if not row.get("prep_available"):
            missing_prep += 1
        if not row.get("conversion_available"):
            missing_conversion += 1
        if row["secured_side"] == "UNKNOWN":
            unknown_team += 1
        if row.get("preparation_score") is None:
            warmup_prep += 1
        if row.get("conversion_score") is None:
            warmup_conversion += 1

        spatial_near_kills += row.get(
            "contest_spatial_near_kills",
            0,
        )
        spatial_located_kills += row.get(
            "contest_spatial_located_kills",
            0,
        )
        spatial_unlocated_kills += row.get(
            "contest_spatial_unlocated_kills",
            0,
        )

        if row.get("trade_evidence") == "ALLY_RESOURCE_COMPENSATION":
            resource_compensation_sequences += 1

        if row.get("trade_evidence") == "ENEMY_RESOURCE_GIVEBACK":
            resource_giveback_sequences += 1

    lines = [
        "================================",
        "OBJECTIVE ANALYZER - AUDIT V20",
        "================================",
        "",
        f"Séquences objectifs : {len(objective_dataset)}",
        f"Préparation frame indisponible : {missing_prep}",
        f"Conversion +120s indisponible : {missing_conversion}",
        f"Equipe objectif inconnue : {unknown_team}",
        f"Preparation Score warmup/non scoré : {warmup_prep}",
        f"Conversion Score warmup/non scoré : {warmup_conversion}",
        "",
        (
            "Fight spatial : "
            f"{spatial_near_kills} kills proches objectif | "
            f"{spatial_located_kills} kills avec coordonnées | "
            f"{spatial_unlocated_kills} kills sans coordonnées"
        ),
        (
            "Compensation ressources significative : "
            f"{resource_compensation_sequences} séquences alliées | "
            f"{resource_giveback_sequences} givebacks ennemis"
        ),
        (
            "Seuils ressources (+/- sur ~120s) : "
            f"{RESOURCE_COMPENSATION_GOLD} Gold | "
            f"{RESOURCE_COMPENSATION_XP} XP | "
            f"{RESOURCE_COMPENSATION_JUNGLE_CS} JCS, "
            "au moins 2 dimensions."
        ),
        "",
        "Objectifs détectés :",
    ]

    for key, count in sorted(kind_counts.items(), key=lambda item: item[1], reverse=True):
        lines.append(f"  {key}: {count}")

    lines.extend(["", "Résultat équipe :"])
    for key, count in sorted(side_counts.items()):
        lines.append(f"  {key}: {count}")

    contest_actionable = (
        contest_counts.get("HIGH", 0)
        + contest_counts.get("MEDIUM", 0)
    )
    contest_rate = (
        contest_actionable / len(objective_dataset)
        if objective_dataset
        else 0.0
    )

    lines.extend([
        "",
        (
            "Contest evidence V20 "
            f"(rayon spatial {OBJECTIVE_FIGHT_SPATIAL_RADIUS}) :"
        ),
    ])
    for key, count in sorted(contest_counts.items()):
        lines.append(f"  {key}: {count}")
    lines.append(
        f"  HIGH+MEDIUM : {contest_actionable} "
        f"({contest_rate:.1%})"
    )

    lines.extend(["", "Trade / compensation evidence APRÈS objectif :"])
    for key, count in sorted(trade_counts.items(), key=lambda item: item[1], reverse=True):
        lines.append(f"  {key}: {count}")

    lines.extend(["", "Contexte de trade AVANT objectif courant :"])
    for key, count in sorted(
        prior_trade_counts.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        lines.append(f"  {key}: {count}")

    lines.extend(["", "Classifications de séquence :"])
    for key, count in sorted(
        classification_counts.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        lines.append(f"  {key}: {count}")

    lines.extend([
        "",
        "Important : contest/trade/classification = explication contextuelle,",
        "jamais preuve causale ni attribution automatique de faute au joueur.",
    ])

    return "\n".join(lines)


def get_match_objectives(objective_dataset, match_id):
    return sorted(
        [row for row in objective_dataset if row["match_id"] == match_id],
        key=lambda row: row["timestamp"],
    )


def render_match_objective_report(objective_dataset, match_id):
    rows = get_match_objectives(objective_dataset, match_id)

    lines = [
        "================================",
        "OBJECTIVE ANALYZER - MATCH V20",
        "================================",
        "",
        f"Match : {match_id}",
        f"Séquences objectifs : {len(rows)}",
    ]

    if not rows:
        lines.append("Aucun objectif majeur détecté.")
        return "\n".join(lines)

    for row in rows:
        lines.extend([
            "",
            "--------------------------------",
            (
                f"{_format_time(row['timestamp'])} | "
                f"{row['objective_kind']} | {row['secured_side']}"
            ),
            "--------------------------------",
            (
                f"Killer : {row['killer_position'] or 'N/A'} | "
                f"joueur={row['player_secured_objective']} | "
                f"enemy JGL={row['enemy_jungler_secured_objective']}"
            ),
            (
                f"État entrée : {row['entry_state']} | "
                f"Gold {row['entry_gold_diff']:+.0f} | "
                f"XP {row['entry_xp_diff']:+.0f} | "
                f"JCS {row['entry_jungle_cs_diff']:+.0f}"
                if row["entry_gold_diff"] is not None
                else "État entrée : N/A"
            ),
            (
                f"Distance pré-objectif : joueur {row['player_proximity_pre']} "
                f"({row['player_distance_pre']:.0f}) | "
                f"JGL adverse {row['opponent_proximity_pre']} "
                f"({row['opponent_distance_pre']:.0f})"
                if row["player_distance_pre"] is not None
                and row["opponent_distance_pre"] is not None
                else "Distance pré-objectif : N/A"
            ),
            "",
            (
                "Préparation -120s→objectif : "
                f"XP {row.get('prep_player_xp_per_min', 0):.0f}/min | "
                f"JCS {row.get('prep_player_jungle_cs_per_min', 0):.2f}/min | "
                f"vs JGL XP {row.get('prep_relative_xp_per_min', 0):+.0f}/min | "
                f"JCS {row.get('prep_relative_jungle_cs_per_min', 0):+.2f}/min"
                if row.get("prep_available")
                else "Préparation : N/A"
            ),
            (
                f"Preparation Score : "
                f"{row['preparation_score']:.0f}/100 ({row['preparation_label']}) | "
                f"ref {row['preparation_reference_scope']} "
                f"N={row['preparation_reference_size']}"
                if row.get("preparation_score") is not None
                else (
                    f"Preparation Score : WARMUP | "
                    f"ref {row['preparation_reference_scope']} "
                    f"N={row['preparation_reference_size']}"
                )
            ),
            (
                f"Shop avant : joueur {row['pre_player_item_purchases']} achats | "
                f"enemy JGL {row['pre_opponent_item_purchases']}"
            ),
            (
                "Tempo v17 avant : "
                + _fmt_optional(
                    row.get("frozen_pre_tempo_score"),
                    "{:.0f}/100",
                )
                + " | Pathing "
                + _fmt_optional(
                    row.get("frozen_pre_pathing_score"),
                    "{:.0f}/100",
                )
            ),
            (
                f"Deaths : <120s {row['player_deaths_pre120']} | "
                f"<60s {row['player_deaths_pre60']} | "
                f"<30s {row['player_deaths_pre30']} | "
                f"enemy JGL <60s {row['opponent_deaths_pre60']}"
            ),
            (
                f"Contest evidence : {row['contest_evidence']} | "
                f"fight spatial K "
                f"{row['ally_champion_kills']}-{row['enemy_champion_kills']} | "
                f"involvement joueur {row['player_combat_involvement']} | "
                f"enemy JGL {row['opponent_combat_involvement']} | "
                f"kills localisés {row['contest_spatial_located_kills']} | "
                f"sans coords {row['contest_spatial_unlocated_kills']}"
            ),
            "",
            (
                "Conversion +120s : "
                f"Gold {row.get('conversion_relative_gold_per_min', 0):+.0f}/min | "
                f"XP {row.get('conversion_relative_xp_per_min', 0):+.0f}/min | "
                f"JCS {row.get('conversion_relative_jungle_cs_per_min', 0):+.2f}/min"
                if row.get("conversion_available")
                else "Conversion +120s : N/A"
            ),
            (
                f"Conversion Score : "
                f"{row['conversion_score']:.0f}/100 ({row['conversion_label']}) | "
                f"ref {row['conversion_reference_scope']} "
                f"N={row['conversion_reference_size']}"
                if row.get("conversion_score") is not None
                else (
                    f"Conversion Score : WARMUP | "
                    f"ref {row['conversion_reference_scope']} "
                    f"N={row['conversion_reference_size']}"
                )
            ),
            (
                "Tempo v17 après : "
                + _fmt_optional(
                    row.get("frozen_post_tempo_score"),
                    "{:.0f}/100",
                )
                + " | Δ "
                + _fmt_optional(
                    row.get("frozen_tempo_score_change"),
                    "{:+.1f}",
                )
                + " | Pathing "
                + _fmt_optional(
                    row.get("frozen_post_pathing_score"),
                    "{:.0f}/100",
                )
            ),
            (
                f"Shop après : joueur {row['post_player_item_purchases']} achats | "
                f"enemy JGL {row['post_opponent_item_purchases']}"
            ),
            (
                f"Trade/compensation APRÈS : {row['trade_evidence']} | "
                f"tours alliées {row['ally_towers']} | "
                f"tours ennemies {row['enemy_towers']} | "
                f"counter obj alliés {','.join(row['ally_counter_objectives']) or '-'} | "
                f"ennemis {','.join(row['enemy_counter_objectives']) or '-'}"
            ),
            (
                f"Contexte AVANT : {row.get('prior_trade_context', 'NONE')} | "
                f"obj alliés {','.join(row.get('prior_ally_objectives', [])) or '-'} | "
                f"obj ennemis {','.join(row.get('prior_enemy_objectives', [])) or '-'} | "
                f"tours alliées {row.get('prior_ally_towers', 0)} | "
                f"tours ennemies {row.get('prior_enemy_towers', 0)}"
            ),
            (
                "Ressources compensation (+120s) : "
                f"Gold {_fmt_optional(row.get('resource_compensation_gold_change'), '{:+.0f}')} | "
                f"XP {_fmt_optional(row.get('resource_compensation_xp_change'), '{:+.0f}')} | "
                f"JCS {_fmt_optional(row.get('resource_compensation_jungle_cs_change'), '{:+.0f}')} | "
                f"favorables significatives {row.get('resource_favorable_components', 0)}/3 | "
                f"défavorables significatives {row.get('resource_unfavorable_components', 0)}/3"
            ),
            (
                f"Classification : {row['sequence_classification']}"
            ),
        ])

    lines.extend([
        "",
        "Contest/trade/classification restent des preuves contextuelles V20.",
        "Le coach ne transforme pas automatiquement OBJECTIF PERDU en erreur joueur.",
    ])

    return "\n".join(lines)
