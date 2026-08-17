from bisect import bisect_left, bisect_right
from collections import defaultdict
from statistics import mean, median

from analysis.feature_engine import percentile_rank


# ============================================================
# CONFIGURATION
# ============================================================

SHOP_EVENT_TYPES = {
    "ITEM_PURCHASED",
    "ITEM_SOLD",
    "ITEM_UNDO",
}

SHOP_CLUSTER_GAP_SECONDS = 20
MAX_FRAME_DISTANCE_SECONDS = 75
PRE_RESET_WINDOW_SECONDS = 120
POST_RESET_WINDOW_SECONDS = 120
POST_DEATH_SHOP_MAX_SECONDS = 90
POST_RESET_DEATH_WINDOW_SECONDS = 120
OBJECTIVE_POST_WINDOW_SECONDS = 90
OBJECTIVE_PRE_WINDOW_SECONDS = 120
OBJECTIVE_TIGHT_WINDOW_SECONDS = 45
MIRRORED_RESET_WINDOW_SECONDS = 120

MIN_HISTORICAL_RESET_REFERENCE = 20
MIN_HISTORICAL_RESET_TIME_REFERENCE = 20
RESET_TIME_REFERENCE_RADIUS_SECONDS = 240

# A score de ré-entrée mesure la production APRES le shop/reset proxy.
# Il ne prétend pas mesurer la qualité causale du recall lui-même.
REENTRY_SCORE_WEIGHTS = {
    "post_player_xp_per_min": 0.30,
    "post_player_jungle_cs_per_min": 0.25,
    "post_relative_gold_per_min": 0.15,
    "post_relative_xp_per_min": 0.20,
    "post_relative_jungle_cs_per_min": 0.10,
}


# ============================================================
# GENERIC HELPERS
# ============================================================


def _format_time(timestamp_ms):
    total_seconds = int((timestamp_ms or 0) / 1000)
    return f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"


def _safe_mean(values):
    values = [value for value in values if value is not None]
    return mean(values) if values else None


def _safe_median(values):
    values = [value for value in values if value is not None]
    return median(values) if values else None


def _safe_rate(value, duration_minutes):
    if value is None or duration_minutes is None or duration_minutes <= 0:
        return None
    return value / duration_minutes


def _fmt_optional(value, pattern):
    if value is None:
        return "N/A"
    return pattern.format(value)


def _phase_for_timestamp(timestamp_ms):
    minute = timestamp_ms / 60_000

    if minute < 3:
        return "OPENING"
    if minute < 10:
        return "EARLY_CLEAR"
    if minute < 15:
        return "EARLY_MID"
    if minute < 20:
        return "MID"
    if minute < 25:
        return "MID_LATE"
    return "LATE"


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
        "jungle_cs_diff": (
            player.get("jungle_cs", 0)
            - opponent.get("jungle_cs", 0)
        ),
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
    player_jungle_cs_gain = (
        end["player_jungle_cs"] - start["player_jungle_cs"]
    )

    opponent_gold_gain = end["opponent_gold"] - start["opponent_gold"]
    opponent_xp_gain = end["opponent_xp"] - start["opponent_xp"]
    opponent_jungle_cs_gain = (
        end["opponent_jungle_cs"] - start["opponent_jungle_cs"]
    )

    relative_gold_change = end["gold_diff"] - start["gold_diff"]
    relative_xp_change = end["xp_diff"] - start["xp_diff"]
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
        f"{prefix}_player_jungle_cs_gain": player_jungle_cs_gain,
        f"{prefix}_opponent_gold_gain": opponent_gold_gain,
        f"{prefix}_opponent_xp_gain": opponent_xp_gain,
        f"{prefix}_opponent_jungle_cs_gain": opponent_jungle_cs_gain,
        f"{prefix}_relative_gold_change": relative_gold_change,
        f"{prefix}_relative_xp_change": relative_xp_change,
        f"{prefix}_relative_jungle_cs_change": relative_jungle_cs_change,
        f"{prefix}_player_gold_per_min": _safe_rate(
            player_gold_gain,
            duration_minutes,
        ),
        f"{prefix}_player_xp_per_min": _safe_rate(
            player_xp_gain,
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
        f"{prefix}_relative_jungle_cs_per_min": _safe_rate(
            relative_jungle_cs_change,
            duration_minutes,
        ),
    }


# ============================================================
# SHOP / RESET PROXY EXTRACTION
# ============================================================


def _shop_events_for_participant(bundle, participant_id):
    return sorted(
        [
            event
            for event in bundle.get("events", [])
            if event.get("type") in SHOP_EVENT_TYPES
            and event.get("participant_id") == participant_id
        ],
        key=lambda event: (
            event.get("timestamp", 0),
            event.get("frame_index") or 0,
            event.get("event_index") or 0,
        ),
    )


def _cluster_shop_events(events):
    clusters = []
    current = []

    def flush():
        nonlocal current
        if not current:
            return

        purchases = [
            event
            for event in current
            if event.get("type") == "ITEM_PURCHASED"
        ]

        # A cluster SELL/UNDO sans achat n'est pas utilisé comme reset proxy.
        if purchases:
            clusters.append({
                "start_timestamp": current[0].get("timestamp", 0),
                "end_timestamp": current[-1].get("timestamp", 0),
                "events": list(current),
                "purchase_count": len(purchases),
                "sale_count": sum(
                    event.get("type") == "ITEM_SOLD"
                    for event in current
                ),
                "undo_count": sum(
                    event.get("type") == "ITEM_UNDO"
                    for event in current
                ),
                "purchased_item_ids": [
                    event.get("item_id")
                    for event in purchases
                    if event.get("item_id") is not None
                ],
            })

        current = []

    for event in events:
        if not current:
            current = [event]
            continue

        gap = (
            event.get("timestamp", 0)
            - current[-1].get("timestamp", 0)
        ) / 1000

        if gap <= SHOP_CLUSTER_GAP_SECONDS:
            current.append(event)
        else:
            flush()
            current = [event]

    flush()
    return clusters


def _build_shop_clusters(bundle):
    player_events = _shop_events_for_participant(
        bundle,
        bundle["my_participant_id"],
    )
    opponent_events = _shop_events_for_participant(
        bundle,
        bundle["opponent_participant_id"],
    )

    return (
        _cluster_shop_events(player_events),
        _cluster_shop_events(opponent_events),
    )


# ============================================================
# DEATH / OBJECTIVE / TEMPO CONTEXT
# ============================================================


def _death_rows_by_match(death_dataset):
    result = defaultdict(list)

    for row in death_dataset or []:
        result[row["match_id"]].append(row)

    for rows in result.values():
        rows.sort(key=lambda row: row["timestamp"])

    return result


def _nearest_death_context(deaths, start_timestamp, end_timestamp):
    previous = [
        row
        for row in deaths
        if row["timestamp"] <= start_timestamp
    ]
    following = [
        row
        for row in deaths
        if row["timestamp"] >= end_timestamp
    ]

    previous_death = previous[-1] if previous else None
    next_death = following[0] if following else None

    previous_seconds = (
        (start_timestamp - previous_death["timestamp"]) / 1000
        if previous_death
        else None
    )
    next_seconds = (
        (next_death["timestamp"] - end_timestamp) / 1000
        if next_death
        else None
    )

    return {
        "previous_death_seconds": previous_seconds,
        "previous_death_severity": (
            previous_death.get("death_severity_score")
            if previous_death
            else None
        ),
        "next_death_seconds": next_seconds,
        "next_death_severity": (
            next_death.get("death_severity_score")
            if next_death
            else None
        ),
        "post_death_shop": (
            previous_seconds is not None
            and 0 <= previous_seconds <= POST_DEATH_SHOP_MAX_SECONDS
        ),
        "post_reset_death_120": (
            next_seconds is not None
            and 0 <= next_seconds <= POST_RESET_DEATH_WINDOW_SECONDS
        ),
    }


def _objective_rows_by_match(objective_dataset):
    result = defaultdict(list)

    for row in objective_dataset or []:
        result[row["match_id"]].append(row)

    for rows in result.values():
        rows.sort(key=lambda row: row["timestamp"])

    return result


def _objective_context(objectives, start_timestamp, end_timestamp):
    previous = [
        row
        for row in objectives
        if row["timestamp"] < start_timestamp
    ]
    following = [
        row
        for row in objectives
        if row["timestamp"] > end_timestamp
    ]

    previous_objective = previous[-1] if previous else None
    next_objective = following[0] if following else None

    previous_seconds = (
        (start_timestamp - previous_objective["timestamp"]) / 1000
        if previous_objective
        else None
    )
    next_seconds = (
        (next_objective["timestamp"] - end_timestamp) / 1000
        if next_objective
        else None
    )

    post_objective = (
        previous_seconds is not None
        and 0 <= previous_seconds <= OBJECTIVE_POST_WINDOW_SECONDS
    )
    pre_objective = (
        next_seconds is not None
        and 0 <= next_seconds <= OBJECTIVE_PRE_WINDOW_SECONDS
    )
    tight_pre_objective = (
        next_seconds is not None
        and 0 <= next_seconds <= OBJECTIVE_TIGHT_WINDOW_SECONDS
    )

    if post_objective and pre_objective:
        timing = "BETWEEN_OBJECTIVES"
    elif tight_pre_objective:
        timing = "TIGHT_PRE_OBJECTIVE"
    elif pre_objective:
        timing = "PRE_OBJECTIVE"
    elif post_objective:
        timing = "POST_OBJECTIVE"
    else:
        timing = "NONE"

    return {
        "objective_timing": timing,
        "previous_objective_seconds": previous_seconds,
        "previous_objective_kind": (
            previous_objective.get("objective_kind")
            if previous_objective
            else None
        ),
        "previous_objective_side": (
            previous_objective.get("secured_side")
            if previous_objective
            else None
        ),
        "next_objective_seconds": next_seconds,
        "next_objective_kind": (
            next_objective.get("objective_kind")
            if next_objective
            else None
        ),
        "next_objective_side": (
            next_objective.get("secured_side")
            if next_objective
            else None
        ),
        "post_objective_reset": post_objective,
        "pre_objective_reset": pre_objective,
        "tight_pre_objective_reset": tight_pre_objective,
    }


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
            f"{prefix}_pathing_holes": 0,
            f"{prefix}_pathing_watches": 0,
        }

    farmable = [
        row
        for row in rows
        if row.get("farmable_tempo_interval")
    ]

    return {
        f"{prefix}_tempo_intervals": len(rows),
        f"{prefix}_tempo_score": _weighted_interval_mean(
            rows,
            "tempo_score",
        ),
        f"{prefix}_pathing_score": _weighted_interval_mean(
            farmable,
            "pathing_score",
        ),
        f"{prefix}_pathing_holes": len({
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


def _nearest_opponent_reset(player_cluster, opponent_clusters):
    if not opponent_clusters:
        return {
            "mirrored_reset": False,
            "opponent_reset_delta_seconds": None,
        }

    target = player_cluster["start_timestamp"]
    nearest = min(
        opponent_clusters,
        key=lambda row: abs(row["start_timestamp"] - target),
    )
    delta = (nearest["start_timestamp"] - target) / 1000

    return {
        "mirrored_reset": abs(delta) <= MIRRORED_RESET_WINDOW_SECONDS,
        "opponent_reset_delta_seconds": delta,
    }


# ============================================================
# RESET ANALYSIS
# ============================================================


def _analyze_reset(
    bundle,
    cluster,
    cluster_index,
    previous_cluster,
    opponent_clusters,
    deaths,
    objectives,
    tempo_rows,
):
    start_timestamp = cluster["start_timestamp"]
    end_timestamp = cluster["end_timestamp"]

    frames = bundle["frames"]
    frame_ts = _frame_timestamps(frames)

    pre_pair = _frame_before_or_at(
        frames,
        frame_ts,
        start_timestamp,
    )
    pre_window_pair = _frame_before_or_at(
        frames,
        frame_ts,
        max(0, start_timestamp - PRE_RESET_WINDOW_SECONDS * 1000),
    )

    post_pair = _frame_after_or_at(
        frames,
        frame_ts,
        end_timestamp,
    )
    post_window_pair = _frame_after_or_at(
        frames,
        frame_ts,
        end_timestamp + POST_RESET_WINDOW_SECONDS * 1000,
    )

    pre_state = _relative_state(pre_pair)
    post_state = _relative_state(post_pair)

    pre_window = _window_delta(
        pre_window_pair,
        pre_pair,
        "pre",
    )
    post_window = _window_delta(
        post_pair,
        post_window_pair,
        "post",
    )

    death_context = _nearest_death_context(
        deaths,
        start_timestamp,
        end_timestamp,
    )
    objective_context = _objective_context(
        objectives,
        start_timestamp,
        end_timestamp,
    )
    mirrored_context = _nearest_opponent_reset(
        cluster,
        opponent_clusters,
    )

    frozen_pre = _tempo_window_context(
        tempo_rows,
        max(0, start_timestamp - PRE_RESET_WINDOW_SECONDS * 1000),
        start_timestamp,
        "frozen_pre",
    )
    frozen_post = _tempo_window_context(
        tempo_rows,
        end_timestamp,
        end_timestamp + POST_RESET_WINDOW_SECONDS * 1000,
        "frozen_post",
    )

    reset_origin = (
        "POST_DEATH_SHOP"
        if death_context["post_death_shop"]
        else "VOLUNTARY_RESET_PROXY"
    )

    if reset_origin == "POST_DEATH_SHOP":
        sequence_classification = "POST_DEATH_SHOP"
    elif objective_context["objective_timing"] == "TIGHT_PRE_OBJECTIVE":
        sequence_classification = "VOLUNTARY_TIGHT_PRE_OBJECTIVE"
    elif objective_context["objective_timing"] == "BETWEEN_OBJECTIVES":
        sequence_classification = "VOLUNTARY_BETWEEN_OBJECTIVES"
    elif objective_context["objective_timing"] == "PRE_OBJECTIVE":
        sequence_classification = "VOLUNTARY_PRE_OBJECTIVE"
    elif objective_context["objective_timing"] == "POST_OBJECTIVE":
        sequence_classification = "VOLUNTARY_POST_OBJECTIVE"
    else:
        sequence_classification = "VOLUNTARY_NEUTRAL"

    previous_shop_seconds = (
        (start_timestamp - previous_cluster["end_timestamp"]) / 1000
        if previous_cluster
        else None
    )

    current_gold_before = (
        pre_state.get("player_current_gold")
        if pre_state
        else None
    )
    current_gold_after = (
        post_state.get("player_current_gold")
        if post_state
        else None
    )

    current_gold_drop_proxy = (
        current_gold_before - current_gold_after
        if (
            current_gold_before is not None
            and current_gold_after is not None
        )
        else None
    )

    row = {
        "match_id": bundle["match_id"],
        "game_creation": bundle["game_creation"],
        "game_duration": bundle["game_duration"],
        "champion": bundle["champion"],
        "opponent_champion": bundle["opponent_champion"],
        "win": bundle["win"],
        "reset_index": cluster_index,
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp,
        "duration_seconds": max(0, (end_timestamp - start_timestamp) / 1000),
        "minute": start_timestamp / 60_000,
        "phase": _phase_for_timestamp(start_timestamp),
        "reset_origin": reset_origin,
        "sequence_classification": sequence_classification,
        "purchase_count": cluster["purchase_count"],
        "sale_count": cluster["sale_count"],
        "undo_count": cluster["undo_count"],
        "purchased_item_ids": cluster["purchased_item_ids"],
        "previous_shop_seconds": previous_shop_seconds,
        "current_gold_before_frame": current_gold_before,
        "current_gold_after_frame": current_gold_after,
        "current_gold_drop_proxy": current_gold_drop_proxy,
        "entry_gold_diff": pre_state.get("gold_diff") if pre_state else None,
        "entry_xp_diff": pre_state.get("xp_diff") if pre_state else None,
        "entry_jungle_cs_diff": (
            pre_state.get("jungle_cs_diff") if pre_state else None
        ),
        "entry_player_level": (
            pre_state.get("player_level") if pre_state else None
        ),
        "entry_opponent_level": (
            pre_state.get("opponent_level") if pre_state else None
        ),
        "reentry_gold_diff": post_state.get("gold_diff") if post_state else None,
        "reentry_xp_diff": post_state.get("xp_diff") if post_state else None,
        "reentry_jungle_cs_diff": (
            post_state.get("jungle_cs_diff") if post_state else None
        ),
        **death_context,
        **objective_context,
        **mirrored_context,
        **pre_window,
        **post_window,
        **frozen_pre,
        **frozen_post,
        "reentry_score": None,
        "reentry_label": "WARMUP",
        "reentry_reference_size": 0,
        "reentry_reference_scope": "UNSCORED",
    }

    row["frozen_tempo_score_change"] = (
        row["frozen_post_tempo_score"] - row["frozen_pre_tempo_score"]
        if (
            row.get("frozen_post_tempo_score") is not None
            and row.get("frozen_pre_tempo_score") is not None
        )
        else None
    )

    # Exploratoire uniquement : le currentGold vient d'une frame ~1 min.
    row["high_unspent_gold_context"] = (
        current_gold_before is not None
        and current_gold_before >= 1500
    )

    return row


def build_reset_dataset(
    bundles,
    death_dataset=None,
    tempo_intervals=None,
    objective_dataset=None,
):
    death_by_match = _death_rows_by_match(death_dataset or [])
    objective_by_match = _objective_rows_by_match(objective_dataset or [])

    tempo_by_match = defaultdict(list)
    for interval in tempo_intervals or []:
        tempo_by_match[interval["match_id"]].append(interval)

    dataset = []

    for bundle in bundles:
        player_clusters, opponent_clusters = _build_shop_clusters(bundle)
        previous_cluster = None

        for index, cluster in enumerate(player_clusters, start=1):
            dataset.append(
                _analyze_reset(
                    bundle,
                    cluster,
                    index,
                    previous_cluster,
                    opponent_clusters,
                    death_by_match.get(bundle["match_id"], []),
                    objective_by_match.get(bundle["match_id"], []),
                    tempo_by_match.get(bundle["match_id"], []),
                )
            )
            previous_cluster = cluster

    dataset.sort(
        key=lambda row: (
            row["game_creation"],
            row["match_id"],
            row["start_timestamp"],
        )
    )

    _attach_historical_reentry_scores(dataset)
    return dataset


# ============================================================
# HISTORICAL-ONLY REENTRY SCORE
# ============================================================


def _historical_score(row, reference, weights):
    percentiles = {}

    for feature in weights:
        value = row.get(feature)
        values = [
            old.get(feature)
            for old in reference
            if old.get(feature) is not None
        ]

        if value is None or not values:
            continue

        percentiles[feature] = percentile_rank(values, value)

    weighted_sum = 0.0
    total_weight = 0.0

    for feature, weight in weights.items():
        if feature not in percentiles:
            continue
        weighted_sum += percentiles[feature] * weight
        total_weight += weight

    if total_weight <= 0:
        return None, percentiles

    return weighted_sum / total_weight, percentiles


def _attach_historical_reentry_scores(dataset):
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

    history_phase_origin = defaultdict(list)
    history_champion_phase_origin = defaultdict(list)

    def choose_reference(row):
        champion = row["champion"]
        phase = row["phase"]
        origin = row["reset_origin"]
        target = row["start_timestamp"]
        radius = RESET_TIME_REFERENCE_RADIUS_SECONDS * 1000

        champion_history = history_champion_phase_origin[
            (champion, phase, origin)
        ]
        phase_history = history_phase_origin[(phase, origin)]

        champion_local = [
            old
            for old in champion_history
            if abs(old["start_timestamp"] - target) <= radius
        ]
        phase_local = [
            old
            for old in phase_history
            if abs(old["start_timestamp"] - target) <= radius
        ]

        candidates = (
            (
                "CHAMPION_PHASE_ORIGIN_TIME",
                champion_local,
                MIN_HISTORICAL_RESET_TIME_REFERENCE,
            ),
            (
                "PHASE_ORIGIN_TIME",
                phase_local,
                MIN_HISTORICAL_RESET_TIME_REFERENCE,
            ),
            (
                "CHAMPION_PHASE_ORIGIN",
                champion_history,
                MIN_HISTORICAL_RESET_REFERENCE,
            ),
            (
                "PHASE_ORIGIN",
                phase_history,
                MIN_HISTORICAL_RESET_REFERENCE,
            ),
        )

        for scope, reference, minimum in candidates:
            if len(reference) >= minimum:
                return scope, reference

        return "WARMUP", []

    for match_id in ordered_match_ids:
        rows = sorted(
            by_match[match_id],
            key=lambda row: row["start_timestamp"],
        )

        for row in rows:
            scope, reference = choose_reference(row)
            row["reentry_reference_scope"] = scope
            row["reentry_reference_size"] = len(reference)

            if not reference:
                continue

            score, percentiles = _historical_score(
                row,
                reference,
                REENTRY_SCORE_WEIGHTS,
            )

            row["reentry_score"] = score
            row["reentry_label"] = _score_label(score)

            for feature, value in percentiles.items():
                row[f"{feature}_percentile"] = value

        # Same-match reset clusters never enter one another's reference.
        for row in rows:
            key = (row["phase"], row["reset_origin"])
            champion_key = (
                row["champion"],
                row["phase"],
                row["reset_origin"],
            )
            history_phase_origin[key].append(row)
            history_champion_phase_origin[champion_key].append(row)


# ============================================================
# GAME / PHASE DATASETS
# ============================================================


def _rows_by_match(dataset):
    result = defaultdict(list)
    for row in dataset:
        result[row["match_id"]].append(row)
    return result


def _rate(count, total):
    if total <= 0:
        return None
    return count / total


def _build_game_row(bundle, rows):
    voluntary = [
        row
        for row in rows
        if row["reset_origin"] == "VOLUNTARY_RESET_PROXY"
    ]
    death_shops = [
        row
        for row in rows
        if row["reset_origin"] == "POST_DEATH_SHOP"
    ]
    scored = [
        row
        for row in voluntary
        if row.get("reentry_score") is not None
    ]

    game_minutes = (
        bundle["game_duration"] / 60
        if bundle.get("game_duration")
        else 0
    )

    return {
        "match_id": bundle["match_id"],
        "game_creation": bundle["game_creation"],
        "champion": bundle["champion"],
        "win": bundle["win"],
        "game_duration": bundle["game_duration"],
        "shop_sequences": len(rows),
        "voluntary_reset_count": len(voluntary),
        "death_shop_count": len(death_shops),
        "voluntary_resets_per10": (
            len(voluntary) * 10 / game_minutes
            if game_minutes > 0
            else None
        ),
        "death_shop_rate": _rate(len(death_shops), len(rows)),
        "median_pre_current_gold_voluntary": _safe_median([
            row.get("current_gold_before_frame")
            for row in voluntary
        ]),
        "median_time_since_previous_shop_min": _safe_median([
            row.get("previous_shop_seconds") / 60
            for row in voluntary
            if row.get("previous_shop_seconds") is not None
        ]),
        "mean_post_reset_player_xp_per_min": _safe_mean([
            row.get("post_player_xp_per_min")
            for row in voluntary
        ]),
        "mean_post_reset_player_jungle_cs_per_min": _safe_mean([
            row.get("post_player_jungle_cs_per_min")
            for row in voluntary
        ]),
        "mean_post_reset_relative_gold_per_min": _safe_mean([
            row.get("post_relative_gold_per_min")
            for row in voluntary
        ]),
        "mean_post_reset_relative_xp_per_min": _safe_mean([
            row.get("post_relative_xp_per_min")
            for row in voluntary
        ]),
        "mean_post_reset_relative_jungle_cs_per_min": _safe_mean([
            row.get("post_relative_jungle_cs_per_min")
            for row in voluntary
        ]),
        "mean_reentry_score": _safe_mean([
            row.get("reentry_score")
            for row in scored
        ]),
        "low_reentry_rate": _rate(
            sum(
                row.get("reentry_score") is not None
                and row["reentry_score"] < 25
                for row in voluntary
            ),
            len(scored),
        ),
        "post_reset_death_120_rate": _rate(
            sum(row["post_reset_death_120"] for row in voluntary),
            len(voluntary),
        ),
        "tight_pre_objective_reset_rate": _rate(
            sum(row["tight_pre_objective_reset"] for row in voluntary),
            len(voluntary),
        ),
        "pre_objective_reset_rate": _rate(
            sum(row["pre_objective_reset"] for row in voluntary),
            len(voluntary),
        ),
        "post_objective_reset_rate": _rate(
            sum(row["post_objective_reset"] for row in voluntary),
            len(voluntary),
        ),
        "mirrored_reset_rate": _rate(
            sum(row["mirrored_reset"] for row in voluntary),
            len(voluntary),
        ),
        "high_unspent_gold_context_rate": _rate(
            sum(row["high_unspent_gold_context"] for row in voluntary),
            len(voluntary),
        ),
        "enemy_objective_after_tight_reset_rate": _rate(
            sum(
                row["tight_pre_objective_reset"]
                and row.get("next_objective_side") == "ENEMY"
                for row in voluntary
            ),
            sum(row["tight_pre_objective_reset"] for row in voluntary),
        ),
        "mean_frozen_pre_tempo_score": _safe_mean([
            row.get("frozen_pre_tempo_score")
            for row in voluntary
        ]),
        "mean_frozen_post_tempo_score": _safe_mean([
            row.get("frozen_post_tempo_score")
            for row in voluntary
        ]),
        "mean_frozen_tempo_score_change": _safe_mean([
            row.get("frozen_tempo_score_change")
            for row in voluntary
        ]),
    }


def build_game_reset_dataset(reset_dataset, bundles):
    rows_by_match = _rows_by_match(reset_dataset)
    result = []

    for bundle in bundles:
        result.append(
            _build_game_row(
                bundle,
                rows_by_match.get(bundle["match_id"], []),
            )
        )

    result.sort(
        key=lambda row: (
            row["game_creation"],
            row["match_id"],
        )
    )
    return result


def build_reset_phase_dataset(reset_dataset, bundles):
    rows_by_match = _rows_by_match(reset_dataset)
    result = []

    for bundle in bundles:
        by_phase = defaultdict(list)
        for row in rows_by_match.get(bundle["match_id"], []):
            by_phase[row["phase"]].append(row)

        for phase, rows in by_phase.items():
            voluntary = [
                row
                for row in rows
                if row["reset_origin"] == "VOLUNTARY_RESET_PROXY"
            ]

            if not voluntary:
                continue

            result.append({
                "match_id": bundle["match_id"],
                "game_creation": bundle["game_creation"],
                "champion": bundle["champion"],
                "win": bundle["win"],
                "phase": phase,
                "voluntary_reset_count": len(voluntary),
                "mean_post_reset_player_xp_per_min": _safe_mean([
                    row.get("post_player_xp_per_min")
                    for row in voluntary
                ]),
                "mean_post_reset_player_jungle_cs_per_min": _safe_mean([
                    row.get("post_player_jungle_cs_per_min")
                    for row in voluntary
                ]),
                "mean_post_reset_relative_gold_per_min": _safe_mean([
                    row.get("post_relative_gold_per_min")
                    for row in voluntary
                ]),
                "mean_post_reset_relative_xp_per_min": _safe_mean([
                    row.get("post_relative_xp_per_min")
                    for row in voluntary
                ]),
                "mean_post_reset_relative_jungle_cs_per_min": _safe_mean([
                    row.get("post_relative_jungle_cs_per_min")
                    for row in voluntary
                ]),
                "mean_reentry_score": _safe_mean([
                    row.get("reentry_score")
                    for row in voluntary
                ]),
                "tight_pre_objective_reset_rate": _rate(
                    sum(row["tight_pre_objective_reset"] for row in voluntary),
                    len(voluntary),
                ),
                "post_reset_death_120_rate": _rate(
                    sum(row["post_reset_death_120"] for row in voluntary),
                    len(voluntary),
                ),
            })

    result.sort(
        key=lambda row: (
            row["game_creation"],
            row["match_id"],
            row["phase"],
        )
    )
    return result


# ============================================================
# PROFILE / AUDIT / MATCH RENDERING
# ============================================================


def summarize_reset_profile(game_dataset, win=None):
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
        "shop_sequences": med("shop_sequences"),
        "voluntary_reset_count": med("voluntary_reset_count"),
        "death_shop_rate": med("death_shop_rate"),
        "pre_current_gold": med("median_pre_current_gold_voluntary"),
        "between_shops": med("median_time_since_previous_shop_min"),
        "post_xp": med("mean_post_reset_player_xp_per_min"),
        "post_jcs": med("mean_post_reset_player_jungle_cs_per_min"),
        "post_rel_gold": med("mean_post_reset_relative_gold_per_min"),
        "post_rel_xp": med("mean_post_reset_relative_xp_per_min"),
        "post_rel_jcs": med("mean_post_reset_relative_jungle_cs_per_min"),
        "reentry_score": med("mean_reentry_score"),
        "low_reentry": med("low_reentry_rate"),
        "post_death_120": med("post_reset_death_120_rate"),
        "tight_objective": med("tight_pre_objective_reset_rate"),
        "pre_objective": med("pre_objective_reset_rate"),
        "post_objective": med("post_objective_reset_rate"),
        "mirrored": med("mirrored_reset_rate"),
        "high_gold": med("high_unspent_gold_context_rate"),
        "tempo_pre": med("mean_frozen_pre_tempo_score"),
        "tempo_post": med("mean_frozen_post_tempo_score"),
        "tempo_delta": med("mean_frozen_tempo_score_change"),
    }


def render_reset_profile(title, summary):
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
        f"Shop/Reset proxy / game : {fmt(summary['shop_sequences'])}",
        f"Voluntary reset proxy / game : {fmt(summary['voluntary_reset_count'])}",
        f"Part POST_DEATH_SHOP : {fmt(summary['death_shop_rate'], '{:.1%}')}",
        "",
        "Avant reset volontaire (frame proxy, CONTEXTE) :",
        f"  Current Gold : {fmt(summary['pre_current_gold'], '{:.0f}')}",
        f"  Temps depuis n’importe quel shop précédent : {fmt(summary['between_shops'], '{:.1f} min')}",
        "",
        "Ré-entrée +120s :",
        f"  XP personnelle/min : {fmt(summary['post_xp'], '{:.0f}')}",
        f"  JCS/min            : {fmt(summary['post_jcs'], '{:.2f}')}",
        f"  Gold vs JGL/min    : {fmt(summary['post_rel_gold'], '{:+.0f}')}",
        f"  XP vs JGL/min      : {fmt(summary['post_rel_xp'], '{:+.0f}')}",
        f"  JCS vs JGL/min     : {fmt(summary['post_rel_jcs'], '{:+.2f}')}",
        f"Reentry Score historique : {fmt(summary['reentry_score'], '{:.0f}/100')}",
        f"Ré-entrées <25/100 : {fmt(summary['low_reentry'], '{:.1%}')}",
        f"Death <=120s après reset : {fmt(summary['post_death_120'], '{:.1%}')}",
        "",
        "Timing objectifs (CONTEXTE, pas faute automatique) :",
        f"  Reset <=45s avant objectif : {fmt(summary['tight_objective'], '{:.1%}')}",
        f"  Reset <=120s avant objectif : {fmt(summary['pre_objective'], '{:.1%}')}",
        f"  Reset <=90s après objectif : {fmt(summary['post_objective'], '{:.1%}')}",
        f"  Reset JGL adverse +/-120s : {fmt(summary['mirrored'], '{:.1%}')}",
        f"  Current Gold >=1500 avant reset : {fmt(summary['high_gold'], '{:.1%}')}",
        "",
        "Tempo v17 autour du reset :",
        f"  Avant : {fmt(summary['tempo_pre'], '{:.0f}/100')}",
        f"  Après : {fmt(summary['tempo_post'], '{:.0f}/100')}",
        f"  Delta : {fmt(summary['tempo_delta'], '{:+.1f}')}",
    ])

    return "\n".join(lines)


def render_reset_audit(reset_dataset):
    origin_counts = defaultdict(int)
    class_counts = defaultdict(int)
    objective_timing_counts = defaultdict(int)
    reference_counts = defaultdict(int)

    warmup = 0
    missing_pre = 0
    missing_post = 0
    high_gold = 0
    tight = 0
    tight_enemy = 0
    low_reentry = 0

    for row in reset_dataset:
        origin_counts[row["reset_origin"]] += 1
        class_counts[row["sequence_classification"]] += 1
        objective_timing_counts[row["objective_timing"]] += 1
        reference_counts[row["reentry_reference_scope"]] += 1

        if row.get("reentry_score") is None:
            warmup += 1
        elif row["reentry_score"] < 25:
            low_reentry += 1

        if not row.get("pre_available"):
            missing_pre += 1
        if not row.get("post_available"):
            missing_post += 1
        if row["high_unspent_gold_context"]:
            high_gold += 1
        if row["tight_pre_objective_reset"]:
            tight += 1
            if row.get("next_objective_side") == "ENEMY":
                tight_enemy += 1

    lines = [
        "================================",
        "RECALL / RESET ANALYZER - AUDIT V21",
        "================================",
        "",
        (
            "IMPORTANT : Riot n'expose pas un événement RECALL fiable ici. "
            "Chaque séquence est un SHOP/RESET PROXY construit à partir "
            "des achats en base."
        ),
        "",
        f"Séquences shop/reset proxy : {len(reset_dataset)}",
        f"Fenêtre pré-reset indisponible : {missing_pre}",
        f"Fenêtre ré-entrée +120s indisponible : {missing_post}",
        f"Reentry Score warmup/non scoré : {warmup}",
        f"Reentry Score <25 : {low_reentry}",
        f"Current Gold >=1500 (frame proxy) : {high_gold}",
        f"Reset <=45s avant objectif : {tight}",
        f"... puis objectif ENEMY : {tight_enemy}",
        "",
        "Origine :",
    ]

    for key, count in sorted(origin_counts.items(), key=lambda item: item[1], reverse=True):
        lines.append(f"  {key}: {count}")

    lines.extend(["", "Timing objectif :"])
    for key, count in sorted(objective_timing_counts.items(), key=lambda item: item[1], reverse=True):
        lines.append(f"  {key}: {count}")

    lines.extend(["", "Classifications :"])
    for key, count in sorted(class_counts.items(), key=lambda item: item[1], reverse=True):
        lines.append(f"  {key}: {count}")

    lines.extend(["", "Références historical-only :"])
    for key, count in sorted(reference_counts.items(), key=lambda item: item[1], reverse=True):
        lines.append(f"  {key}: {count}")

    weakest = sorted(
        [
            row
            for row in reset_dataset
            if (
                row["reset_origin"] == "VOLUNTARY_RESET_PROXY"
                and row.get("reentry_score") is not None
            )
        ],
        key=lambda row: row["reentry_score"],
    )[:15]

    tight_rows = sorted(
        [
            row
            for row in reset_dataset
            if (
                row["reset_origin"] == "VOLUNTARY_RESET_PROXY"
                and row["tight_pre_objective_reset"]
            )
        ],
        key=lambda row: row.get("next_objective_seconds") or 9999,
    )[:20]

    lines.extend([
        "",
        "--------------------------------",
        "15 RÉ-ENTRÉES VOLONTAIRES LES PLUS FAIBLES",
        "--------------------------------",
    ])

    if not weakest:
        lines.append("Aucune ré-entrée scorée.")

    for row in weakest:
        lines.append(
            (
                f"{row['champion']} | {'WIN' if row['win'] else 'LOSS'} | "
                f"{row['phase']} | {_format_time(row['start_timestamp'])} | "
                f"Reentry {row['reentry_score']:.0f}/100 | "
                f"XP {_fmt_optional(row.get('post_player_xp_per_min'), '{:.0f}/min')} | "
                f"JCS {_fmt_optional(row.get('post_player_jungle_cs_per_min'), '{:.2f}/min')} | "
                f"vs JGL XP {_fmt_optional(row.get('post_relative_xp_per_min'), '{:+.0f}/min')} | "
                f"nextObj {row.get('next_objective_kind') or '-'} "
                f"{_fmt_optional(row.get('next_objective_seconds'), '{:.0f}s')} "
                f"{row.get('next_objective_side') or '-'} | "
                f"death120={row['post_reset_death_120']} | "
                f"ref {row['reentry_reference_scope']} N={row['reentry_reference_size']}"
            )
        )

    lines.extend([
        "",
        "--------------------------------",
        "RESET PROXY <=45s AVANT OBJECTIF - AUDIT",
        "--------------------------------",
    ])

    if not tight_rows:
        lines.append("Aucun reset volontaire proxy <=45s avant objectif.")

    for row in tight_rows:
        lines.append(
            (
                f"{row['champion']} | {'WIN' if row['win'] else 'LOSS'} | "
                f"{_format_time(row['start_timestamp'])} | "
                f"objectif {row.get('next_objective_kind') or '-'} dans "
                f"{_fmt_optional(row.get('next_objective_seconds'), '{:.0f}s')} "
                f"{row.get('next_objective_side') or '-'} | "
                f"Reentry {_fmt_optional(row.get('reentry_score'), '{:.0f}/100')} | "
                f"currentGoldFrame {_fmt_optional(row.get('current_gold_before_frame'), '{:.0f}')} | "
                f"tempoDelta {_fmt_optional(row.get('frozen_tempo_score_change'), '{:+.1f}')}"
            )
        )

    lines.extend([
        "",
        "Le currentGold avant shop vient de la dernière frame Riot <=75s :",
        "il reste exploratoire et n'est jamais une erreur automatique.",
        "Le Reentry Score mesure la production observée APRES le shop/reset proxy,",
        "pas la causalité du recall lui-même.",
    ])

    return "\n".join(lines)


def get_match_resets(reset_dataset, match_id):
    return sorted(
        [row for row in reset_dataset if row["match_id"] == match_id],
        key=lambda row: row["start_timestamp"],
    )


def render_match_reset_report(reset_dataset, match_id):
    rows = get_match_resets(reset_dataset, match_id)

    lines = [
        "================================",
        "RECALL / RESET ANALYZER - MATCH V21",
        "================================",
        "",
        f"Match : {match_id}",
        f"Séquences shop/reset proxy : {len(rows)}",
        "",
        (
            "SHOP/RESET PROXY = cluster d'achats détecté en base. "
            "Ce n'est pas une preuve d'un recall exact."
        ),
    ]

    if not rows:
        lines.append("Aucune séquence d'achat détectée.")
        return "\n".join(lines)

    for row in rows:
        items = ",".join(str(item) for item in row["purchased_item_ids"]) or "-"

        lines.extend([
            "",
            "--------------------------------",
            (
                f"{_format_time(row['start_timestamp'])} | "
                f"{row['phase']} | {row['reset_origin']}"
            ),
            "--------------------------------",
            (
                f"Achats {row['purchase_count']} | ventes {row['sale_count']} | "
                f"undo {row['undo_count']} | itemIds {items}"
            ),
            (
                "Current Gold frame avant/après : "
                f"{_fmt_optional(row.get('current_gold_before_frame'), '{:.0f}')} -> "
                f"{_fmt_optional(row.get('current_gold_after_frame'), '{:.0f}')} | "
                f"drop proxy {_fmt_optional(row.get('current_gold_drop_proxy'), '{:+.0f}')}"
            ),
            (
                "État avant : "
                f"Gold { _fmt_optional(row.get('entry_gold_diff'), '{:+.0f}') } | "
                f"XP { _fmt_optional(row.get('entry_xp_diff'), '{:+.0f}') } | "
                f"JCS { _fmt_optional(row.get('entry_jungle_cs_diff'), '{:+.0f}') }"
            ),
            (
                "Pré-reset -120s : "
                f"XP {_fmt_optional(row.get('pre_player_xp_per_min'), '{:.0f}/min')} | "
                f"JCS {_fmt_optional(row.get('pre_player_jungle_cs_per_min'), '{:.2f}/min')} | "
                f"vs JGL XP {_fmt_optional(row.get('pre_relative_xp_per_min'), '{:+.0f}/min')} | "
                f"JCS {_fmt_optional(row.get('pre_relative_jungle_cs_per_min'), '{:+.2f}/min')}"
            ),
            (
                "Tempo v17 avant : "
                f"{_fmt_optional(row.get('frozen_pre_tempo_score'), '{:.0f}/100')} | "
                "Pathing "
                f"{_fmt_optional(row.get('frozen_pre_pathing_score'), '{:.0f}/100')}"
            ),
            (
                f"Death avant : {_fmt_optional(row.get('previous_death_seconds'), '{:.0f}s')} | "
                f"severity {_fmt_optional(row.get('previous_death_severity'), '{:.0f}/100')} | "
                f"POST_DEATH={row['post_death_shop']}"
            ),
            (
                f"Timing objectif : {row['objective_timing']} | "
                f"précédent {row.get('previous_objective_kind') or '-'} "
                f"({_fmt_optional(row.get('previous_objective_seconds'), '{:.0f}s')}) | "
                f"suivant {row.get('next_objective_kind') or '-'} "
                f"({_fmt_optional(row.get('next_objective_seconds'), '{:.0f}s')}) "
                f"{row.get('next_objective_side') or '-'}"
            ),
            (
                "Reset JGL adverse proche : "
                f"{row['mirrored_reset']} | delta "
                f"{_fmt_optional(row.get('opponent_reset_delta_seconds'), '{:+.0f}s')}"
            ),
            "",
            (
                "Ré-entrée frame-observable +120s : "
                f"start {_fmt_optional(
                    (row.get('post_start_timestamp') - row['end_timestamp']) / 1000
                    if row.get('post_start_timestamp') is not None
                    else None,
                    '+{:.0f}s'
                )} | "
                f"XP {_fmt_optional(row.get('post_player_xp_per_min'), '{:.0f}/min')} | "
                f"JCS {_fmt_optional(row.get('post_player_jungle_cs_per_min'), '{:.2f}/min')} | "
                f"Gold vs JGL {_fmt_optional(row.get('post_relative_gold_per_min'), '{:+.0f}/min')} | "
                f"XP {_fmt_optional(row.get('post_relative_xp_per_min'), '{:+.0f}/min')} | "
                f"JCS {_fmt_optional(row.get('post_relative_jungle_cs_per_min'), '{:+.2f}/min')}"
            ),
            (
                "Reentry Score : "
                + (
                    f"{row['reentry_score']:.0f}/100 ({row['reentry_label']})"
                    if row.get("reentry_score") is not None
                    else "WARMUP"
                )
                + f" | ref {row['reentry_reference_scope']} "
                f"N={row['reentry_reference_size']}"
            ),
            (
                "Tempo v17 après : "
                f"{_fmt_optional(row.get('frozen_post_tempo_score'), '{:.0f}/100')} | "
                f"Delta {_fmt_optional(row.get('frozen_tempo_score_change'), '{:+.1f}')} | "
                "Pathing "
                f"{_fmt_optional(row.get('frozen_post_pathing_score'), '{:.0f}/100')}"
            ),
            (
                f"Death <=120s après : {row['post_reset_death_120']} | "
                f"dans {_fmt_optional(row.get('next_death_seconds'), '{:.0f}s')} | "
                f"severity {_fmt_optional(row.get('next_death_severity'), '{:.0f}/100')}"
            ),
            (
                f"Classification : {row['sequence_classification']} | "
                f"highGoldContext={row['high_unspent_gold_context']}"
            ),
        ])

    lines.extend([
        "",
        "Important : RESET TIGHT / highGold / death après reset = CONTEXTE.",
        "Aucun de ces éléments n'est une faute automatique sans validation supplémentaire.",
    ])

    return "\n".join(lines)
