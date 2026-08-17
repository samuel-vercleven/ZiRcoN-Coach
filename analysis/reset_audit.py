from collections import Counter, defaultdict
from math import sqrt
from statistics import median

from analysis.death_cost_analyzer import build_death_cost_dataset
from analysis.jungle_tempo_analyzer import build_tempo_intervals
from analysis.objective_analyzer import build_objective_dataset
from analysis.reset_analyzer import (
    _analyze_reset,
    _attach_historical_reentry_scores,
    _death_rows_by_match,
    _format_time,
    _frame_before_or_at,
    _frame_timestamps,
    _objective_rows_by_match,
    _relative_state,
    _shop_events_for_participant,
    build_game_reset_dataset,
    build_reset_dataset,
    summarize_reset_profile,
)
from database.database import (
    filter_match_ids_by_position,
    get_local_account_by_riot_id,
    get_local_match_ids_by_puuid,
    initialize_database,
    initialize_timeline_tables,
)
from database.tempo_reader import load_tempo_bundles


GAME_NAME = "ZiRcoN1977"
TAG_LINE = "EUW"
QUEUE_ID = 420
ROLE = "JUNGLE"
MATCH_COUNT = 100
TARGET_MATCH_ID = "EUW1_7951911875"


def _fmt(value, pattern="{:.1f}"):
    if value is None:
        return "N/A"
    return pattern.format(value)


def _result(row):
    return "WIN" if row.get("win") else "LOSS"


def _items(cluster):
    values = cluster.get("purchased_item_ids") or []
    return ",".join(str(value) for value in values) or "-"


def _cluster_shop_events(events, threshold_seconds):
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

        if gap <= threshold_seconds:
            current.append(event)
        else:
            flush()
            current = [event]

    flush()
    return clusters


def _build_shop_clusters(bundle, threshold_seconds):
    player_events = _shop_events_for_participant(
        bundle,
        bundle["my_participant_id"],
    )
    opponent_events = _shop_events_for_participant(
        bundle,
        bundle["opponent_participant_id"],
    )

    return (
        _cluster_shop_events(player_events, threshold_seconds),
        _cluster_shop_events(opponent_events, threshold_seconds),
    )


def _build_reset_dataset_for_threshold(
    bundles,
    death_dataset,
    tempo_intervals,
    objective_dataset,
    threshold_seconds,
):
    death_by_match = _death_rows_by_match(death_dataset or [])
    objective_by_match = _objective_rows_by_match(objective_dataset or [])

    tempo_by_match = defaultdict(list)
    for interval in tempo_intervals or []:
        tempo_by_match[interval["match_id"]].append(interval)

    dataset = []

    for bundle in bundles:
        player_clusters, opponent_clusters = _build_shop_clusters(
            bundle,
            threshold_seconds,
        )
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


def _row_key(row):
    return (
        row["match_id"],
        row["start_timestamp"],
        row["end_timestamp"],
    )


def _cluster_key(match_id, cluster):
    return (
        match_id,
        cluster["start_timestamp"],
        cluster["end_timestamp"],
    )


def _events_between(bundle, start_ms, end_ms):
    return [
        event
        for event in bundle.get("events", [])
        if start_ms < event.get("timestamp", 0) < end_ms
    ]


def _event_summary(bundle, events):
    my_id = bundle["my_participant_id"]
    kills = 0
    assists = 0
    deaths = 0
    champion_kills = 0
    objectives = []

    for event in events:
        event_type = event.get("type")
        if event_type == "CHAMPION_KILL":
            champion_kills += 1
            if event.get("killer_id") == my_id:
                kills += 1
            if event.get("victim_id") == my_id:
                deaths += 1
            if my_id in (event.get("assists") or []):
                assists += 1

        if event_type == "ELITE_MONSTER_KILL":
            objectives.append({
                "timestamp": event.get("timestamp", 0),
                "monster_type": event.get("monster_type"),
                "monster_sub_type": event.get("monster_sub_type"),
                "team_id": event.get("team_id"),
            })

    return {
        "player_kills": kills,
        "player_assists": assists,
        "player_deaths": deaths,
        "champion_kills": champion_kills,
        "objectives": objectives,
    }


def _state_at(bundle, timestamp_ms):
    frames = bundle["frames"]
    frame_ts = _frame_timestamps(frames)
    pair = _frame_before_or_at(frames, frame_ts, timestamp_ms)
    return _relative_state(pair)


def _between_state_delta(bundle, first_cluster, second_cluster):
    start = _state_at(bundle, first_cluster["end_timestamp"])
    end = _state_at(bundle, second_cluster["start_timestamp"])

    if not start or not end:
        return {
            "available": False,
            "start_frame": None,
            "end_frame": None,
            "xp_delta": None,
            "jungle_cs_delta": None,
            "gold_delta": None,
            "current_gold_delta": None,
            "position_delta": None,
        }

    start_x = start.get("player_x")
    start_y = start.get("player_y")
    end_x = end.get("player_x")
    end_y = end.get("player_y")
    position_delta = None

    if None not in (start_x, start_y, end_x, end_y):
        position_delta = sqrt(
            (end_x - start_x) ** 2
            + (end_y - start_y) ** 2
        )

    return {
        "available": True,
        "start_frame": start["timestamp"],
        "end_frame": end["timestamp"],
        "xp_delta": end["player_xp"] - start["player_xp"],
        "jungle_cs_delta": (
            end["player_jungle_cs"] - start["player_jungle_cs"]
        ),
        "gold_delta": end["player_gold"] - start["player_gold"],
        "current_gold_delta": (
            end["player_current_gold"] - start["player_current_gold"]
        ),
        "position_delta": position_delta,
        "start_position": (start_x, start_y),
        "end_position": (end_x, end_y),
    }


def _gap_bin(gap):
    if gap <= 25:
        return "20-25"
    if gap <= 30:
        return "25-30"
    if gap <= 35:
        return "30-35"
    if gap <= 40:
        return "35-40"
    return "40-45"


def _classify_pair(gap, state_delta, event_summary):
    if not state_delta.get("available"):
        return "AMBIGUOUS"

    xp_delta = state_delta.get("xp_delta") or 0
    jcs_delta = state_delta.get("jungle_cs_delta") or 0
    gold_delta = state_delta.get("gold_delta") or 0
    movement = state_delta.get("position_delta")

    player_event = (
        event_summary["player_kills"] > 0
        or event_summary["player_assists"] > 0
        or event_summary["player_deaths"] > 0
        or bool(event_summary["objectives"])
    )
    resource_gain = (
        xp_delta > 0
        or jcs_delta > 0
        or gold_delta > 0
    )

    if player_event or resource_gain:
        return "LIKELY_SEPARATE_VISITS"

    if gap <= 30:
        return "LIKELY_SAME_SHOP_VISIT"

    if movement is not None and movement > 2500:
        return "AMBIGUOUS"

    return "LIKELY_SAME_SHOP_VISIT"


def _load_context():
    initialize_database()
    initialize_timeline_tables()

    account = get_local_account_by_riot_id(
        GAME_NAME,
        TAG_LINE,
        queue_id=QUEUE_ID,
    )
    if not account:
        raise RuntimeError("Local Riot profile not found in SQLite history.")

    puuid = account["puuid"]
    match_ids = get_local_match_ids_by_puuid(
        puuid,
        queue_id=QUEUE_ID,
        count=MATCH_COUNT,
    )
    jungle_match_ids = filter_match_ids_by_position(
        match_ids,
        puuid,
        ROLE,
    )
    bundles = load_tempo_bundles(
        puuid,
        position=ROLE,
        queue_id=QUEUE_ID,
    )
    deaths = build_death_cost_dataset(
        puuid,
        position=ROLE,
        queue_id=QUEUE_ID,
    )
    tempo_intervals = build_tempo_intervals(bundles)
    objectives = build_objective_dataset(
        bundles,
        death_dataset=deaths,
        tempo_intervals=tempo_intervals,
    )
    resets_20 = build_reset_dataset(
        bundles,
        death_dataset=deaths,
        tempo_intervals=tempo_intervals,
        objective_dataset=objectives,
    )

    return {
        "account": account,
        "puuid": puuid,
        "match_ids": match_ids,
        "jungle_match_ids": jungle_match_ids,
        "bundles": bundles,
        "deaths": deaths,
        "tempo_intervals": tempo_intervals,
        "objectives": objectives,
        "resets_20": resets_20,
    }


def _build_near_gap_pairs(context):
    rows_by_key = {
        _row_key(row): row
        for row in context["resets_20"]
    }
    pairs = []

    for bundle in context["bundles"]:
        clusters, _ = _build_shop_clusters(bundle, 20)

        for first, second in zip(clusters, clusters[1:]):
            gap = (
                second["start_timestamp"]
                - first["end_timestamp"]
            ) / 1000
            if not (20 < gap <= 45):
                continue

            row_a = rows_by_key.get(_cluster_key(bundle["match_id"], first))
            row_b = rows_by_key.get(_cluster_key(bundle["match_id"], second))
            events = _events_between(
                bundle,
                first["end_timestamp"],
                second["start_timestamp"],
            )
            event_summary = _event_summary(bundle, events)
            state_delta = _between_state_delta(bundle, first, second)
            classification = _classify_pair(
                gap,
                state_delta,
                event_summary,
            )

            pairs.append({
                "bundle": bundle,
                "first_cluster": first,
                "second_cluster": second,
                "first_row": row_a,
                "second_row": row_b,
                "gap": gap,
                "gap_bin": _gap_bin(gap),
                "events": events,
                "event_summary": event_summary,
                "state_delta": state_delta,
                "classification": classification,
            })

    pairs.sort(
        key=lambda pair: (
            pair["gap"],
            pair["bundle"]["game_creation"],
            pair["bundle"]["match_id"],
        )
    )
    return pairs


def _render_pair(pair, index):
    bundle = pair["bundle"]
    first = pair["first_cluster"]
    second = pair["second_cluster"]
    row_a = pair["first_row"]
    row_b = pair["second_row"]
    state = pair["state_delta"]
    events = pair["event_summary"]

    lines = [
        f"PAIR {index:02d}",
        (
            f"match_id={bundle['match_id']} | champion={bundle['champion']} | "
            f"result={'WIN' if bundle['win'] else 'LOSS'} | "
            f"gap={pair['gap']:.2f}s | bin={pair['gap_bin']} | "
            f"audit_class={pair['classification']}"
        ),
        (
            f"first={_format_time(first['start_timestamp'])}-"
            f"{_format_time(first['end_timestamp'])} | "
            f"phase={row_a.get('phase') if row_a else 'N/A'} | "
            f"p/s/u={first['purchase_count']}/"
            f"{first['sale_count']}/{first['undo_count']} | "
            f"items={_items(first)}"
        ),
        (
            f"second={_format_time(second['start_timestamp'])}-"
            f"{_format_time(second['end_timestamp'])} | "
            f"phase={row_b.get('phase') if row_b else 'N/A'} | "
            f"p/s/u={second['purchase_count']}/"
            f"{second['sale_count']}/{second['undo_count']} | "
            f"items={_items(second)}"
        ),
    ]

    if row_a:
        lines.append(
            "first_sequence="
            f"{row_a['reset_origin']} / {row_a['sequence_classification']} | "
            f"prevDeath={_fmt(row_a.get('previous_death_seconds'), '{:.0f}s')} | "
            f"nextObj={row_a.get('next_objective_kind') or '-'} "
            f"{_fmt(row_a.get('next_objective_seconds'), '{:.0f}s')} "
            f"{row_a.get('next_objective_side') or '-'}"
        )

    if row_b:
        lines.append(
            "second_sequence="
            f"{row_b['reset_origin']} / {row_b['sequence_classification']} | "
            f"prevDeath={_fmt(row_b.get('previous_death_seconds'), '{:.0f}s')} | "
            f"nextObj={row_b.get('next_objective_kind') or '-'} "
            f"{_fmt(row_b.get('next_objective_seconds'), '{:.0f}s')} "
            f"{row_b.get('next_objective_side') or '-'}"
        )

    if state.get("available"):
        lines.append(
            "between_frame_delta="
            f"frames {_format_time(state['start_frame'])}->"
            f"{_format_time(state['end_frame'])} | "
            f"XP {state['xp_delta']:+.0f} | "
            f"JCS {state['jungle_cs_delta']:+.0f} | "
            f"Gold {state['gold_delta']:+.0f} | "
            f"currentGold {state['current_gold_delta']:+.0f}"
        )
        lines.append(
            "movement_frame_proxy="
            f"{state.get('start_position')} -> {state.get('end_position')} | "
            f"distance={_fmt(state.get('position_delta'), '{:.0f}')}"
        )
    else:
        lines.append("between_frame_delta=N/A")
        lines.append("movement_frame_proxy=N/A")

    objective_text = ", ".join(
        (
            f"{obj.get('monster_type') or '-'}:"
            f"{obj.get('monster_sub_type') or '-'}@"
            f"{_format_time(obj.get('timestamp'))}"
        )
        for obj in events["objectives"]
    ) or "-"
    lines.append(
        "between_events="
        f"playerK/A/D={events['player_kills']}/"
        f"{events['player_assists']}/{events['player_deaths']} | "
        f"championKills={events['champion_kills']} | "
        f"majorObjectives={objective_text}"
    )
    lines.append("")
    return lines


def _score_distribution(rows):
    scores = sorted(
        row.get("reentry_score")
        for row in rows
        if row.get("reentry_score") is not None
    )

    if not scores:
        return "N/A"

    return (
        f"n={len(scores)} | min={scores[0]:.1f} | "
        f"median={median(scores):.1f} | max={scores[-1]:.1f}"
    )


def _threshold_summary(context, threshold, baseline_count):
    if threshold == 20:
        dataset = context["resets_20"]
    else:
        dataset = _build_reset_dataset_for_threshold(
            context["bundles"],
            context["deaths"],
            context["tempo_intervals"],
            context["objectives"],
            threshold,
        )

    origins = Counter(row["reset_origin"] for row in dataset)
    voluntary = [
        row
        for row in dataset
        if row["reset_origin"] == "VOLUNTARY_RESET_PROXY"
    ]
    scored = [
        row
        for row in dataset
        if row.get("reentry_score") is not None
    ]
    voluntary_scored = [
        row
        for row in voluntary
        if row.get("reentry_score") is not None
    ]
    unscored = [
        row
        for row in dataset
        if row.get("reentry_score") is None
    ]
    target_rows = [
        row
        for row in dataset
        if row["match_id"] == TARGET_MATCH_ID
    ]
    target_origins = Counter(row["reset_origin"] for row in target_rows)
    profile = summarize_reset_profile(
        build_game_reset_dataset(dataset, context["bundles"])
    )

    return {
        "threshold": threshold,
        "dataset": dataset,
        "total": len(dataset),
        "voluntary": origins["VOLUNTARY_RESET_PROXY"],
        "post_death": origins["POST_DEATH_SHOP"],
        "scored": len(scored),
        "voluntary_scored": len(voluntary_scored),
        "unscored": len(unscored),
        "unscored_scopes": Counter(
            row["reentry_reference_scope"]
            for row in unscored
        ),
        "tight_voluntary": sum(
            row["tight_pre_objective_reset"]
            for row in voluntary
        ),
        "target_count": len(target_rows),
        "target_voluntary": target_origins["VOLUNTARY_RESET_PROXY"],
        "target_post_death": target_origins["POST_DEATH_SHOP"],
        "merges": baseline_count - len(dataset),
        "profile": profile,
    }


def _render_threshold_summary(summary):
    profile = summary["profile"] or {}
    return [
        (
            f"threshold={summary['threshold']}s | total={summary['total']} | "
            f"voluntary={summary['voluntary']} | "
            f"postDeath={summary['post_death']} | "
            f"scored={summary['scored']} | "
            f"voluntaryScored={summary['voluntary_scored']} | "
            f"unscored={summary['unscored']} "
            f"{dict(summary['unscored_scopes'])} | "
            f"tightVoluntary={summary['tight_voluntary']} | "
            f"target={summary['target_count']} "
            f"({summary['target_voluntary']} voluntary / "
            f"{summary['target_post_death']} postDeath) | "
            f"mergesVs20={summary['merges']}"
        ),
        (
            "game_level_medians="
            f"shopSeq={_fmt(profile.get('shop_sequences'))} | "
            f"voluntary={_fmt(profile.get('voluntary_reset_count'))} | "
            f"deathShopRate={_fmt(profile.get('death_shop_rate'), '{:.1%}')} | "
            f"postXP={_fmt(profile.get('post_xp'), '{:.0f}')} | "
            f"postJCS={_fmt(profile.get('post_jcs'), '{:.2f}')} | "
            f"postRelGold={_fmt(profile.get('post_rel_gold'), '{:+.0f}')} | "
            f"postRelXP={_fmt(profile.get('post_rel_xp'), '{:+.0f}')} | "
            f"reentryScore={_fmt(profile.get('reentry_score'), '{:.0f}')} | "
            f"lowReentry={_fmt(profile.get('low_reentry'), '{:.1%}')}"
        ),
    ]


def _time_to_objective_bin(seconds):
    if seconds is None:
        return "N/A"
    if seconds <= 15:
        return "0-15"
    if seconds <= 30:
        return "15-30"
    return "30-45"


def _render_tight_objective_audit(context, near_pairs):
    near_keys = set()
    likely_same_keys = set()

    for pair in near_pairs:
        keys = {
            _cluster_key(pair["bundle"]["match_id"], pair["first_cluster"]),
            _cluster_key(pair["bundle"]["match_id"], pair["second_cluster"]),
        }
        near_keys.update(keys)
        if pair["classification"] == "LIKELY_SAME_SHOP_VISIT":
            likely_same_keys.update(keys)

    rows = sorted(
        [
            row
            for row in context["resets_20"]
            if (
                row["reset_origin"] == "VOLUNTARY_RESET_PROXY"
                and row["tight_pre_objective_reset"]
            )
        ],
        key=lambda row: (
            row.get("next_objective_seconds") or 9999,
            row["game_creation"],
            row["match_id"],
            row["start_timestamp"],
        )
    )

    lines = [
        "PART C - ALL VOLUNTARY RESET PROXIES <=45S BEFORE OBJECTIVE",
        f"total={len(rows)}",
        f"by_objective_type={dict(Counter(row.get('next_objective_kind') for row in rows))}",
        f"by_objective_side={dict(Counter(row.get('next_objective_side') for row in rows))}",
        f"by_time_to_objective={dict(Counter(_time_to_objective_bin(row.get('next_objective_seconds')) for row in rows))}",
        f"by_result={dict(Counter(_result(row) for row in rows))}",
        f"by_phase={dict(Counter(row['phase'] for row in rows))}",
        f"reentry_distribution={_score_distribution(rows)}",
        (
            "post_reset_death_120="
            f"{sum(row['post_reset_death_120'] for row in rows)}"
        ),
        (
            "tempo_available="
            f"pre={sum(row.get('frozen_pre_tempo_score') is not None for row in rows)} | "
            f"post={sum(row.get('frozen_post_tempo_score') is not None for row in rows)} | "
            f"delta={sum(row.get('frozen_tempo_score_change') is not None for row in rows)}"
        ),
        (
            "current_gold_context="
            f"highGold={sum(row['high_unspent_gold_context'] for row in rows)} | "
            f"median={_fmt(median([row['current_gold_before_frame'] for row in rows if row.get('current_gold_before_frame') is not None]), '{:.0f}')}"
        ),
    ]

    misclassified_post_death = [
        row
        for row in rows
        if (
            row.get("previous_death_seconds") is not None
            and row["previous_death_seconds"] <= 90
        )
    ]
    split_candidates = [
        row
        for row in rows
        if _row_key(row) in likely_same_keys
    ]
    timing_artifacts = [
        row
        for row in rows
        if (
            row.get("next_objective_seconds") is not None
            and row["next_objective_seconds"] <= 5
        )
    ]

    strategic_candidates = []
    for row in rows:
        flags = []
        if row.get("next_objective_side") == "ALLY":
            flags.append("ALLY_OBJECTIVE")
        if row.get("mirrored_reset"):
            flags.append("MIRRORED_ENEMY_RESET")
        if row.get("high_unspent_gold_context"):
            flags.append("HIGH_GOLD_CONTEXT")
        if (
            row.get("reentry_score") is not None
            and row["reentry_score"] >= 50
        ):
            flags.append("GOOD_REENTRY")
        if row.get("frozen_tempo_score_change") is not None and row["frozen_tempo_score_change"] >= 0:
            flags.append("NON_NEGATIVE_TEMPO_DELTA")
        if flags:
            strategic_candidates.append((row, flags))

    lines.extend([
        (
            "misclassified_post_death_candidates="
            f"{len(misclassified_post_death)}"
        ),
        (
            "split_purchase_cluster_candidates="
            f"{len(split_candidates)}"
        ),
        (
            "objective_timing_artifact_candidates_nextObj<=5s="
            f"{len(timing_artifacts)}"
        ),
        (
            "plausible_strategic_context_candidates="
            f"{len(strategic_candidates)}"
        ),
        "",
        "DETAILED TIGHT OBJECTIVE ROWS",
    ])

    for index, row in enumerate(rows, start=1):
        flags = []
        if _row_key(row) in likely_same_keys:
            flags.append("SPLIT_CLUSTER_CANDIDATE")
        if row in timing_artifacts:
            flags.append("TIMING_ARTIFACT_CANDIDATE")
        if row.get("next_objective_side") == "ALLY":
            flags.append("ALLY_OBJECTIVE_CONTEXT")
        if row.get("mirrored_reset"):
            flags.append("MIRRORED_RESET_CONTEXT")
        if (
            row.get("reentry_score") is not None
            and row["reentry_score"] >= 50
        ):
            flags.append("GOOD_REENTRY_CONTEXT")
        if row.get("high_unspent_gold_context"):
            flags.append("HIGH_GOLD_CONTEXT")

        lines.append(
            (
                f"TIGHT {index:02d} | match={row['match_id']} | "
                f"{row['champion']} {_result(row)} | "
                f"{_format_time(row['start_timestamp'])} {row['phase']} | "
                f"obj={row.get('next_objective_kind') or '-'} "
                f"{row.get('next_objective_side') or '-'} "
                f"in {_fmt(row.get('next_objective_seconds'), '{:.0f}s')} | "
                f"score={_fmt(row.get('reentry_score'), '{:.1f}')} | "
                f"prevDeath={_fmt(row.get('previous_death_seconds'), '{:.0f}s')} | "
                f"death120={row['post_reset_death_120']} | "
                f"tempo={_fmt(row.get('frozen_pre_tempo_score'), '{:.0f}')}"
                f"->{_fmt(row.get('frozen_post_tempo_score'), '{:.0f}')} "
                f"delta={_fmt(row.get('frozen_tempo_score_change'), '{:+.1f}')} | "
                f"currentGold={_fmt(row.get('current_gold_before_frame'), '{:.0f}')} | "
                f"flags={','.join(flags) or '-'}"
            )
        )

    return lines


def _render_target_match(context, near_pairs):
    rows = sorted(
        [
            row
            for row in context["resets_20"]
            if row["match_id"] == TARGET_MATCH_ID
        ],
        key=lambda row: row["start_timestamp"],
    )
    origins = Counter(row["reset_origin"] for row in rows)
    target_pairs = [
        pair
        for pair in near_pairs
        if pair["bundle"]["match_id"] == TARGET_MATCH_ID
    ]
    tight_rows = [
        row
        for row in rows
        if row["tight_pre_objective_reset"]
    ]

    lines = [
        "PART D - TARGET MATCH",
        f"match={TARGET_MATCH_ID}",
        (
            f"sequence_count={len(rows)} | "
            f"voluntary={origins['VOLUNTARY_RESET_PROXY']} | "
            f"postDeath={origins['POST_DEATH_SHOP']}"
        ),
        f"near_threshold_split_candidates={len(target_pairs)}",
        f"tight_pre_objective_proxies={len(tight_rows)}",
    ]

    for row in rows:
        lines.append(
            (
                f"TARGET_ROW | {_format_time(row['start_timestamp'])} | "
                f"{row['phase']} | {row['reset_origin']} | "
                f"{row['sequence_classification']} | "
                f"tight={row['tight_pre_objective_reset']} | "
                f"obj={row.get('next_objective_kind') or '-'} "
                f"{row.get('next_objective_side') or '-'} "
                f"{_fmt(row.get('next_objective_seconds'), '{:.0f}s')} | "
                f"score={_fmt(row.get('reentry_score'), '{:.1f}')} | "
                f"prevDeath={_fmt(row.get('previous_death_seconds'), '{:.0f}s')}"
            )
        )

    return lines


def render_audit_report():
    context = _load_context()
    near_pairs = _build_near_gap_pairs(context)
    pair_classes = Counter(pair["classification"] for pair in near_pairs)
    gap_bins = Counter(pair["gap_bin"] for pair in near_pairs)
    champion_distribution = Counter(
        pair["bundle"]["champion"]
        for pair in near_pairs
    )
    phase_distribution = Counter(
        pair["second_row"]["phase"]
        for pair in near_pairs
        if pair["second_row"]
    )

    lines = [
        "# RESET V21 PRE-FREEZE AUDIT",
        "",
        "Scope: audit-only. Production SHOP_CLUSTER_GAP_SECONDS remains 20s.",
        "No frozen analyzer logic is modified by this report.",
        "",
        "DATASET",
        f"local_match_ids={len(context['match_ids'])}",
        f"jungle_match_ids={len(context['jungle_match_ids'])}",
        f"timeline_bundles={len(context['bundles'])}",
        f"death_rows={len(context['deaths'])}",
        f"tempo_intervals={len(context['tempo_intervals'])}",
        f"objective_rows={len(context['objectives'])}",
        f"reset_rows_20s={len(context['resets_20'])}",
        "",
        "PART A - NEAR-THRESHOLD CLUSTER GAPS",
        f"total_audited_pairs={len(near_pairs)}",
        f"classification_counts={dict(pair_classes)}",
        f"gap_bins={dict(gap_bins)}",
        f"champion_distribution={dict(champion_distribution)}",
        f"phase_distribution={dict(phase_distribution)}",
        "",
        "Classification is audit-only and not used in production logic.",
        "",
    ]

    for index, pair in enumerate(near_pairs, start=1):
        lines.extend(_render_pair(pair, index))

    lines.extend([
        "",
        "PART B - SENSITIVITY ANALYSIS",
    ])

    summaries = [
        _threshold_summary(
            context,
            threshold,
            baseline_count=len(context["resets_20"]),
        )
        for threshold in (20, 30, 45)
    ]

    for summary in summaries:
        lines.extend(_render_threshold_summary(summary))

    lines.extend([
        "",
        (
            "Sensitivity note: comparisons use the same raw history and "
            "existing historical-only scoring architecture. Validation "
            "thresholds and FDR families are not retuned."
        ),
        "",
    ])
    lines.extend(_render_tight_objective_audit(context, near_pairs))
    lines.extend([""])
    lines.extend(_render_target_match(context, near_pairs))

    if pair_classes.get("LIKELY_SAME_SHOP_VISIT", 0) > 0:
        lines.extend([
            "",
            "AUDIT CONCLUSION",
            (
                "REVIEW_REQUIRED: near-threshold pairs include likely same "
                "shop visits under the audit-only heuristic. Any threshold "
                "change must be decided by project review."
            ),
        ])
    else:
        lines.extend([
            "",
            "AUDIT CONCLUSION",
            (
                "REVIEW_REQUIRED: no production change made; freeze readiness "
                "still belongs to project review."
            ),
        ])

    return "\n".join(lines)


if __name__ == "__main__":
    print(render_audit_report())
