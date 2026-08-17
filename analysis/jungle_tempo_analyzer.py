from bisect import bisect_left, bisect_right
from collections import defaultdict
from math import hypot
from statistics import mean, median

from analysis.feature_engine import percentile_rank


ANALYSIS_START_SECONDS = 120

GOOD_FRAME_MIN_SECONDS = 45
GOOD_FRAME_MAX_SECONDS = 75

DEATH_CONTAMINATION_SECONDS = 90
OBJECTIVE_CONTEXT_SECONDS = 90

MIN_HISTORICAL_PHASE_INTERVALS = 20
MIN_HISTORICAL_CONTEXT_INTERVALS = 20

TEMPO_COLLAPSE_THRESHOLD = 25
TEMPO_LOW_THRESHOLD = 40
TEMPO_GOOD_THRESHOLD = 60
TEMPO_SURGE_THRESHOLD = 80


PHASES = (
    ("OPENING", 0, 180),
    ("EARLY_CLEAR", 180, 600),
    ("EARLY_MID", 600, 900),
    ("MID", 900, 1200),
    ("MID_LATE", 1200, 1500),
    ("LATE", 1500, None),
)


TEMPO_SCORE_WEIGHTS = {
    # Le score est surtout orienté jungle :
    # XP + Jungle CS dominent, le Gold relatif capture la conversion.
    # Le CS total reste disponible comme diagnostic mais n'entre plus
    # dans le composite principal car une wave de lane peut le gonfler.
    "relative_gold_per_min": 0.20,
    "relative_xp_per_min": 0.20,
    "relative_jungle_cs_per_min": 0.15,
    "player_gold_per_min": 0.10,
    "player_xp_per_min": 0.20,
    "player_jungle_cs_per_min": 0.15,
}

# Score PATHING séparé : il ne dépend PAS de ce que fait le jungler
# adverse. Il mesure uniquement la production personnelle sur une
# fenêtre où le joueur est disponible pour farm/path et ne prend pas
# une wave de lane.
PATHING_SCORE_WEIGHTS = {
    "player_xp_per_min": 0.55,
    "player_jungle_cs_per_min": 0.45,
}

MIN_HISTORICAL_PATHING_INTERVALS = 20
MIN_TIME_LOCAL_REFERENCE = 20
TIME_LOCAL_RADII_SECONDS = (120, 180)
PATHING_BOUNDARY_GUARD_SECONDS = 60
PATHING_WATCH_THRESHOLD = 30
PATHING_SUSTAINED_THRESHOLD = 35


def _phase_for_timestamp(
    timestamp_ms,
):
    seconds = (
        timestamp_ms / 1000
    )

    for (
        label,
        start,
        end,
    ) in PHASES:
        if (
            seconds >= start
            and (
                end is None
                or seconds < end
            )
        ):
            return label

    return "UNKNOWN"


def _safe_rate(
    value,
    duration_minutes,
):
    if (
        value is None
        or duration_minutes <= 0
    ):
        return None

    return (
        value / duration_minutes
    )


def _distance(
    first_frame,
    second_frame,
):
    first_x = first_frame.get("x")
    first_y = first_frame.get("y")
    second_x = second_frame.get("x")
    second_y = second_frame.get("y")

    if None in (
        first_x,
        first_y,
        second_x,
        second_y,
    ):
        return None

    return hypot(
        second_x - first_x,
        second_y - first_y,
    )


def _state_from_diffs(
    gold_diff,
    xp_diff,
    cs_diff,
):
    score = 0

    if gold_diff >= 300:
        score += 1
    elif gold_diff <= -300:
        score -= 1

    if xp_diff >= 300:
        score += 1
    elif xp_diff <= -300:
        score -= 1

    if cs_diff >= 5:
        score += 1
    elif cs_diff <= -5:
        score -= 1

    if score >= 2:
        return "AHEAD"

    if score <= -2:
        return "BEHIND"

    return "EVEN"


def _killer_team(
    event,
    bundle,
):
    raw = event.get(
        "raw",
        {},
    )

    team_id = raw.get(
        "killerTeamId"
    )

    if team_id is not None:
        return team_id

    killer_id = event.get(
        "killer_id"
    )

    player = bundle[
        "players"
    ].get(
        killer_id
    )

    if player:
        return player.get(
            "team_id"
        )

    return None


def _event_index(
    events,
):
    timestamps = [
        event["timestamp"]
        for event in events
    ]

    return (
        timestamps,
        events,
    )


def _events_between(
    index,
    start_ms,
    end_ms,
):
    timestamps, events = index

    # Intervalle temporel (start, end] :
    # un événement exactement sur une frontière de frame n'est
    # attribué qu'à UN seul intervalle, jamais aux deux.
    left = bisect_right(
        timestamps,
        start_ms,
    )

    right = bisect_right(
        timestamps,
        end_ms,
    )

    return events[
        left:right
    ]


def _champion_context(
    interval_events,
    bundle,
):
    my_id = bundle[
        "my_participant_id"
    ]

    opponent_id = bundle[
        "opponent_participant_id"
    ]

    result = {
        "player_kills": 0,
        "player_deaths": 0,
        "player_assists": 0,
        "opponent_kills": 0,
        "opponent_deaths": 0,
        "opponent_assists": 0,
    }

    for event in interval_events:
        if event.get(
            "type"
        ) != "CHAMPION_KILL":
            continue

        killer_id = event.get(
            "killer_id"
        )

        victim_id = event.get(
            "victim_id"
        )

        assists = (
            event.get(
                "assists"
            )
            or []
        )

        if killer_id == my_id:
            result[
                "player_kills"
            ] += 1

        if victim_id == my_id:
            result[
                "player_deaths"
            ] += 1

        if my_id in assists:
            result[
                "player_assists"
            ] += 1

        if killer_id == opponent_id:
            result[
                "opponent_kills"
            ] += 1

        if victim_id == opponent_id:
            result[
                "opponent_deaths"
            ] += 1

        if opponent_id in assists:
            result[
                "opponent_assists"
            ] += 1

    return result


def _objective_context(
    interval_events,
    bundle,
):
    result = {
        "team_objectives": 0,
        "enemy_objectives": 0,
        "team_towers": 0,
        "enemy_towers": 0,
        "team_plates": 0,
        "enemy_plates": 0,
    }

    my_team_id = bundle[
        "my_team_id"
    ]

    for event in interval_events:
        event_type = event.get(
            "type"
        )

        if event_type == (
            "ELITE_MONSTER_KILL"
        ):
            killer_team = (
                _killer_team(
                    event,
                    bundle,
                )
            )

            if killer_team == (
                my_team_id
            ):
                result[
                    "team_objectives"
                ] += 1

            elif killer_team is not None:
                result[
                    "enemy_objectives"
                ] += 1

        elif event_type == (
            "BUILDING_KILL"
        ):
            raw = event.get(
                "raw",
                {},
            )

            building_type = str(
                raw.get(
                    "buildingType",
                    "",
                )
            ).upper()

            if "TOWER" not in (
                building_type
            ):
                continue

            destroyed_team = (
                event.get(
                    "team_id"
                )
            )

            if destroyed_team == (
                my_team_id
            ):
                result[
                    "enemy_towers"
                ] += 1

            elif destroyed_team is not None:
                result[
                    "team_towers"
                ] += 1

        elif event_type == (
            "TURRET_PLATE_DESTROYED"
        ):
            destroyed_team = (
                event.get(
                    "team_id"
                )
            )

            if destroyed_team == (
                my_team_id
            ):
                result[
                    "enemy_plates"
                ] += 1

            elif destroyed_team is not None:
                result[
                    "team_plates"
                ] += 1

    return result


def _shopping_context(
    interval_events,
    bundle,
):
    my_id = bundle[
        "my_participant_id"
    ]

    opponent_id = bundle[
        "opponent_participant_id"
    ]

    player_purchases = 0
    opponent_purchases = 0

    for event in interval_events:
        if event.get(
            "type"
        ) != "ITEM_PURCHASED":
            continue

        participant_id = (
            event.get(
                "participant_id"
            )
        )

        if participant_id == my_id:
            player_purchases += 1

        elif participant_id == (
            opponent_id
        ):
            opponent_purchases += 1

    return {
        "player_purchases": (
            player_purchases
        ),
        "opponent_purchases": (
            opponent_purchases
        ),
        "player_shop_context": (
            player_purchases > 0
        ),
        "opponent_shop_context": (
            opponent_purchases > 0
        ),
    }


def _death_timestamps(
    bundle,
):
    my_id = bundle[
        "my_participant_id"
    ]

    opponent_id = bundle[
        "opponent_participant_id"
    ]

    player = []
    opponent = []

    for event in bundle["events"]:
        if event.get(
            "type"
        ) != "CHAMPION_KILL":
            continue

        victim_id = event.get(
            "victim_id"
        )

        if victim_id == my_id:
            player.append(
                event["timestamp"]
            )

        elif victim_id == (
            opponent_id
        ):
            opponent.append(
                event["timestamp"]
            )

    return (
        sorted(player),
        sorted(opponent),
    )


def _has_timestamp_in_window(
    timestamps,
    start_ms,
    end_ms,
):
    left = bisect_left(
        timestamps,
        start_ms,
    )

    return (
        left < len(timestamps)
        and timestamps[left]
        <= end_ms
    )


def _tempo_label(
    score,
):
    if score is None:
        return "WARMUP"

    if score < (
        TEMPO_COLLAPSE_THRESHOLD
    ):
        return "COLLAPSE"

    if score < (
        TEMPO_LOW_THRESHOLD
    ):
        return "LOW"

    if score < (
        TEMPO_GOOD_THRESHOLD
    ):
        return "NEUTRAL"

    if score < (
        TEMPO_SURGE_THRESHOLD
    ):
        return "GOOD"

    return "SURGE"


def _context_bucket(
    row,
):
    """
    Contexte principal d'un intervalle.

    Le Tempo Score n'est plus obligé de comparer un reset à une minute
    de farm pur : on essaie d'abord de trouver une référence historique
    avec le même champion, la même phase et le même type de contexte.
    """
    tags = []

    if row.get(
        "reset_context"
    ):
        tags.append(
            "RESET"
        )

    if row.get(
        "combat_context"
    ):
        tags.append(
            "COMBAT"
        )

    if row.get(
        "objective_direct_context"
    ):
        tags.append(
            "OBJECTIVE"
        )

    elif row.get(
        "objective_nearby_context"
    ):
        tags.append(
            "OBJECTIVE_NEARBY"
        )

    if row.get(
        "lane_catch_context"
    ):
        tags.append(
            "LANE_CATCH"
        )

    if not tags:
        return "FREE"

    return "+".join(
        tags
    )


def build_tempo_intervals(
    bundles,
):
    dataset = []

    for bundle in bundles:
        frames = bundle["frames"]
        event_index = _event_index(
            bundle["events"]
        )

        (
            player_deaths,
            opponent_deaths,
        ) = _death_timestamps(
            bundle
        )

        for index in range(
            1,
            len(frames),
        ):
            start = frames[
                index - 1
            ]

            end = frames[index]

            start_ts = start[
                "timestamp"
            ]

            end_ts = end[
                "timestamp"
            ]

            duration_seconds = (
                end_ts - start_ts
            ) / 1000

            if duration_seconds <= 0:
                continue

            duration_minutes = (
                duration_seconds / 60
            )

            player_start = start[
                "player"
            ]

            player_end = end[
                "player"
            ]

            opponent_start = start[
                "opponent"
            ]

            opponent_end = end[
                "opponent"
            ]

            player_gold_gain = (
                player_end["gold"]
                - player_start["gold"]
            )

            opponent_gold_gain = (
                opponent_end["gold"]
                - opponent_start["gold"]
            )

            player_xp_gain = (
                player_end["xp"]
                - player_start["xp"]
            )

            opponent_xp_gain = (
                opponent_end["xp"]
                - opponent_start["xp"]
            )

            player_cs_gain = (
                player_end["cs"]
                - player_start["cs"]
            )

            opponent_cs_gain = (
                opponent_end["cs"]
                - opponent_start["cs"]
            )

            player_jungle_cs_gain = (
                player_end[
                    "jungle_cs"
                ]
                - player_start[
                    "jungle_cs"
                ]
            )

            opponent_jungle_cs_gain = (
                opponent_end[
                    "jungle_cs"
                ]
                - opponent_start[
                    "jungle_cs"
                ]
            )

            player_lane_cs_gain = (
                player_end[
                    "lane_cs"
                ]
                - player_start[
                    "lane_cs"
                ]
            )

            opponent_lane_cs_gain = (
                opponent_end[
                    "lane_cs"
                ]
                - opponent_start[
                    "lane_cs"
                ]
            )

            start_gold_diff = (
                player_start["gold"]
                - opponent_start["gold"]
            )

            end_gold_diff = (
                player_end["gold"]
                - opponent_end["gold"]
            )

            start_xp_diff = (
                player_start["xp"]
                - opponent_start["xp"]
            )

            end_xp_diff = (
                player_end["xp"]
                - opponent_end["xp"]
            )

            start_cs_diff = (
                player_start["cs"]
                - opponent_start["cs"]
            )

            end_cs_diff = (
                player_end["cs"]
                - opponent_end["cs"]
            )

            start_jungle_cs_diff = (
                player_start[
                    "jungle_cs"
                ]
                - opponent_start[
                    "jungle_cs"
                ]
            )

            end_jungle_cs_diff = (
                player_end[
                    "jungle_cs"
                ]
                - opponent_end[
                    "jungle_cs"
                ]
            )

            relative_gold_change = (
                end_gold_diff
                - start_gold_diff
            )

            relative_xp_change = (
                end_xp_diff
                - start_xp_diff
            )

            relative_cs_change = (
                end_cs_diff
                - start_cs_diff
            )

            relative_jungle_cs_change = (
                end_jungle_cs_diff
                - start_jungle_cs_diff
            )

            interval_events = (
                _events_between(
                    event_index,
                    start_ts,
                    end_ts,
                )
            )

            extended_events = (
                _events_between(
                    event_index,
                    max(
                        0,
                        start_ts
                        - OBJECTIVE_CONTEXT_SECONDS
                        * 1000,
                    ),
                    end_ts
                    + OBJECTIVE_CONTEXT_SECONDS
                    * 1000,
                )
            )

            champion_context = (
                _champion_context(
                    interval_events,
                    bundle,
                )
            )

            objective_context = (
                _objective_context(
                    interval_events,
                    bundle,
                )
            )

            nearby_objective_context = (
                _objective_context(
                    extended_events,
                    bundle,
                )
            )

            shopping_context = (
                _shopping_context(
                    interval_events,
                    bundle,
                )
            )

            death_window_start = (
                start_ts
                - DEATH_CONTAMINATION_SECONDS
                * 1000
            )

            player_death_affected = (
                _has_timestamp_in_window(
                    player_deaths,
                    death_window_start,
                    end_ts,
                )
            )

            opponent_death_affected = (
                _has_timestamp_in_window(
                    opponent_deaths,
                    death_window_start,
                    end_ts,
                )
            )

            death_free = (
                not player_death_affected
                and not opponent_death_affected
            )

            good_frame = (
                GOOD_FRAME_MIN_SECONDS
                <= duration_seconds
                <= GOOD_FRAME_MAX_SECONDS
            )

            # L'intervalle entier doit commencer après le seuil.
            # V13 utilisait end_ts et incluait donc 01:00→02:00
            # malgré un ANALYSIS_START_SECONDS = 120.
            after_analysis_start = (
                start_ts
                >= ANALYSIS_START_SECONDS
                * 1000
            )

            core_interval = (
                death_free
                and good_frame
                and after_analysis_start
            )

            player_distance = (
                _distance(
                    player_start,
                    player_end,
                )
            )

            opponent_distance = (
                _distance(
                    opponent_start,
                    opponent_end,
                )
            )

            start_state = (
                _state_from_diffs(
                    start_gold_diff,
                    start_xp_diff,
                    start_cs_diff,
                )
            )

            end_state = (
                _state_from_diffs(
                    end_gold_diff,
                    end_xp_diff,
                    end_cs_diff,
                )
            )

            worsened_resources = sum(
                1
                for value in (
                    relative_gold_change,
                    relative_xp_change,
                    relative_cs_change,
                )
                if value < 0
            )

            improved_resources = sum(
                1
                for value in (
                    relative_gold_change,
                    relative_xp_change,
                    relative_cs_change,
                )
                if value > 0
            )

            lead_bleed = (
                start_state == "AHEAD"
                and worsened_resources
                >= 2
            )

            recovery_push = (
                start_state == "BEHIND"
                and improved_resources
                >= 2
            )

            row = {
                "match_id": bundle["match_id"],
                "game_creation": bundle["game_creation"],
                "champion": bundle["champion"],
                "opponent_champion": bundle["opponent_champion"],
                "win": bundle["win"],
                "game_duration": bundle["game_duration"],

                "start_timestamp": start_ts,
                "end_timestamp": end_ts,
                "duration_seconds": duration_seconds,
                "duration_minutes": duration_minutes,

                "phase": _phase_for_timestamp(
                    start_ts
                ),

                "good_frame": good_frame,
                "death_free": death_free,
                "player_death_affected": (
                    player_death_affected
                ),
                "opponent_death_affected": (
                    opponent_death_affected
                ),
                "core_interval": core_interval,

                "player_gold_gain": player_gold_gain,
                "player_xp_gain": player_xp_gain,
                "player_cs_gain": player_cs_gain,
                "player_jungle_cs_gain": (
                    player_jungle_cs_gain
                ),
                "player_lane_cs_gain": (
                    player_lane_cs_gain
                ),

                "opponent_gold_gain": opponent_gold_gain,
                "opponent_xp_gain": opponent_xp_gain,
                "opponent_cs_gain": opponent_cs_gain,
                "opponent_jungle_cs_gain": (
                    opponent_jungle_cs_gain
                ),
                "opponent_lane_cs_gain": (
                    opponent_lane_cs_gain
                ),

                "player_gold_per_min": _safe_rate(
                    player_gold_gain,
                    duration_minutes,
                ),
                "player_xp_per_min": _safe_rate(
                    player_xp_gain,
                    duration_minutes,
                ),
                "player_cs_per_min": _safe_rate(
                    player_cs_gain,
                    duration_minutes,
                ),
                "player_jungle_cs_per_min": _safe_rate(
                    player_jungle_cs_gain,
                    duration_minutes,
                ),

                "opponent_gold_per_min": _safe_rate(
                    opponent_gold_gain,
                    duration_minutes,
                ),
                "opponent_xp_per_min": _safe_rate(
                    opponent_xp_gain,
                    duration_minutes,
                ),
                "opponent_cs_per_min": _safe_rate(
                    opponent_cs_gain,
                    duration_minutes,
                ),

                "start_gold_diff": start_gold_diff,
                "end_gold_diff": end_gold_diff,
                "start_xp_diff": start_xp_diff,
                "end_xp_diff": end_xp_diff,
                "start_cs_diff": start_cs_diff,
                "end_cs_diff": end_cs_diff,
                "start_jungle_cs_diff": (
                    start_jungle_cs_diff
                ),
                "end_jungle_cs_diff": (
                    end_jungle_cs_diff
                ),

                "relative_gold_change": (
                    relative_gold_change
                ),
                "relative_xp_change": (
                    relative_xp_change
                ),
                "relative_cs_change": (
                    relative_cs_change
                ),
                "relative_jungle_cs_change": (
                    relative_jungle_cs_change
                ),

                "relative_gold_per_min": _safe_rate(
                    relative_gold_change,
                    duration_minutes,
                ),
                "relative_xp_per_min": _safe_rate(
                    relative_xp_change,
                    duration_minutes,
                ),
                "relative_cs_per_min": _safe_rate(
                    relative_cs_change,
                    duration_minutes,
                ),
                "relative_jungle_cs_per_min": _safe_rate(
                    relative_jungle_cs_change,
                    duration_minutes,
                ),

                "start_state": start_state,
                "end_state": end_state,
                "worsened_resources": (
                    worsened_resources
                ),
                "improved_resources": (
                    improved_resources
                ),
                "lead_bleed": lead_bleed,
                "recovery_push": recovery_push,

                "player_distance": player_distance,
                "opponent_distance": opponent_distance,
                "player_distance_per_min": (
                    _safe_rate(
                        player_distance,
                        duration_minutes,
                    )
                    if player_distance is not None
                    else None
                ),

                "player_current_gold_start": (
                    player_start[
                        "current_gold"
                    ]
                ),
                "player_current_gold_end": (
                    player_end[
                        "current_gold"
                    ]
                ),
                "opponent_current_gold_start": (
                    opponent_start[
                        "current_gold"
                    ]
                ),
                "opponent_current_gold_end": (
                    opponent_end[
                        "current_gold"
                    ]
                ),

                **champion_context,
                **objective_context,
                **shopping_context,

                "nearby_team_objectives": (
                    nearby_objective_context[
                        "team_objectives"
                    ]
                ),
                "nearby_enemy_objectives": (
                    nearby_objective_context[
                        "enemy_objectives"
                    ]
                ),
                "nearby_team_towers": (
                    nearby_objective_context[
                        "team_towers"
                    ]
                ),
                "nearby_enemy_towers": (
                    nearby_objective_context[
                        "enemy_towers"
                    ]
                ),
            }

            row[
                "player_combat_context"
            ] = (
                row["player_kills"]
                + row["player_assists"]
                + row["player_deaths"]
            ) > 0

            row[
                "opponent_combat_context"
            ] = (
                row["opponent_kills"]
                + row["opponent_assists"]
                + row["opponent_deaths"]
            ) > 0

            # Compatibilité avec les versions précédentes.
            row["combat_context"] = row[
                "player_combat_context"
            ]

            row[
                "objective_direct_context"
            ] = (
                row["team_objectives"]
                + row["enemy_objectives"]
            ) > 0

            row[
                "objective_nearby_context"
            ] = (
                row["nearby_team_objectives"]
                + row["nearby_enemy_objectives"]
            ) > 0

            # Compatibilité : objective_context reste la version large ±90s.
            row["objective_context"] = row[
                "objective_nearby_context"
            ]

            row["reset_context"] = (
                row["player_shop_context"]
            )

            # Un jungler qui prend/couvre une wave n'est pas automatiquement
            # en "mauvais pathing jungle". Ce contexte est donc explicite.
            row[
                "lane_catch_context"
            ] = (
                row[
                    "player_lane_cs_gain"
                ] >= 3
            )

            row["context_bucket"] = (
                _context_bucket(
                    row
                )
            )

            # Trois niveaux de pureté :
            #
            # CORE       : seulement hors contamination death.
            # FARMABLE   : pas de reset/combat/objectif DIRECT.
            # STRICT_FREE: FARMABLE + aucun objectif à ±90s.
            #
            # On garde FREE comme alias STRICT_FREE pour compatibilité.
            row[
                "farmable_tempo_interval"
            ] = (
                row["core_interval"]
                and not row[
                    "reset_context"
                ]
                and not row[
                    "player_combat_context"
                ]
                and not row[
                    "objective_direct_context"
                ]
            )

            row[
                "mirrored_farmable_interval"
            ] = (
                row[
                    "farmable_tempo_interval"
                ]
                and not row[
                    "opponent_shop_context"
                ]
                and not row[
                    "opponent_combat_context"
                ]
            )

            row[
                "strict_free_tempo_interval"
            ] = (
                row[
                    "farmable_tempo_interval"
                ]
                and not row[
                    "objective_nearby_context"
                ]
            )

            row[
                "free_tempo_interval"
            ] = row[
                "strict_free_tempo_interval"
            ]

            # Candidat pathing/farm : fenêtre farmable sans prise de wave.
            row[
                "pathing_candidate_interval"
            ] = (
                row[
                    "farmable_tempo_interval"
                ]
                and not row[
                    "lane_catch_context"
                ]
            )

            dataset.append(row)

    dataset.sort(
        key=lambda row: (
            row["game_creation"],
            row["match_id"],
            row["start_timestamp"],
        )
    )

    _attach_historical_tempo_scores(
        dataset
    )

    _attach_pathing_boundary_guards(
        dataset
    )

    _attach_interval_diagnostics(
        dataset
    )

    _attach_sustained_pathing_holes(
        dataset
    )

    return dataset


def _attach_historical_tempo_scores(
    dataset,
):
    """
    Deux scores distincts, tous deux historical-only :

    TEMPO SCORE
      - joueur + adversaire ;
      - référence champion/phase/contexte avec fallback contrôlé ;
      - sert au diagnostic général de tempo.

    PATHING SCORE
      - production PERSONNELLE seulement ;
      - uniquement sur les fenêtres pathing_candidate ;
      - XP + Jungle CS ;
      - référence champion+phase, puis phase globale ;
      - ne peut donc pas devenir mauvais simplement parce que le JGL
        adverse gagne un fight ailleurs.

    Une game entière utilise uniquement l'historique des games
    antérieures : aucune fuite temporelle intra-game ou future.
    """
    by_match = defaultdict(list)
    match_creation = {}

    for row in dataset:
        by_match[
            row["match_id"]
        ].append(row)

        match_creation[
            row["match_id"]
        ] = row["game_creation"]

    ordered_match_ids = sorted(
        by_match,
        key=lambda match_id: (
            match_creation[match_id],
            match_id,
        ),
    )

    # General tempo references.
    history_champion_phase_context = defaultdict(list)
    history_phase_context = defaultdict(list)
    history_champion_phase = defaultdict(list)
    history_phase = defaultdict(list)

    # Pathing-only references.
    pathing_history_champion_phase = defaultdict(list)
    pathing_history_phase = defaultdict(list)

    def local_subset(
        reference,
        row,
        radius_seconds,
    ):
        target = row[
            "start_timestamp"
        ]

        radius_ms = (
            radius_seconds
            * 1000
        )

        return [
            old_row
            for old_row in reference
            if abs(
                old_row[
                    "start_timestamp"
                ]
                - target
            ) <= radius_ms
        ]

    def choose_tempo_reference(row):
        champion = row["champion"]
        phase = row["phase"]
        context = row["context_bucket"]

        champion_context = (
            history_champion_phase_context[
                (champion, phase, context)
            ]
        )

        phase_context = (
            history_phase_context[
                (phase, context)
            ]
        )

        champion_phase = (
            history_champion_phase[
                (champion, phase)
            ]
        )

        phase_global = (
            history_phase[
                phase
            ]
        )

        # Priorité aux références proches dans le temps de game.
        # 03:00 n'est ainsi pas comparé directement à 09:00 si
        # l'historique permet une référence plus locale.
        for radius in TIME_LOCAL_RADII_SECONDS:
            local_candidates = (
                (
                    f"CHAMPION_PHASE_CONTEXT_TIME_{radius}s",
                    local_subset(
                        champion_context,
                        row,
                        radius,
                    ),
                ),
                (
                    f"PHASE_CONTEXT_TIME_{radius}s",
                    local_subset(
                        phase_context,
                        row,
                        radius,
                    ),
                ),
                (
                    f"CHAMPION_PHASE_TIME_{radius}s",
                    local_subset(
                        champion_phase,
                        row,
                        radius,
                    ),
                ),
                (
                    f"PHASE_TIME_{radius}s",
                    local_subset(
                        phase_global,
                        row,
                        radius,
                    ),
                ),
            )

            for (
                scope,
                reference,
            ) in local_candidates:
                if len(
                    reference
                ) >= MIN_TIME_LOCAL_REFERENCE:
                    return (
                        scope,
                        reference,
                    )

        candidates = (
            (
                "CHAMPION_PHASE_CONTEXT",
                champion_context,
            ),
            (
                "PHASE_CONTEXT",
                phase_context,
            ),
            (
                "CHAMPION_PHASE",
                champion_phase,
            ),
            (
                "PHASE_GLOBAL",
                phase_global,
            ),
        )

        for (
            scope,
            reference,
        ) in candidates:
            if len(
                reference
            ) >= MIN_HISTORICAL_CONTEXT_INTERVALS:
                return (
                    scope,
                    reference,
                )

        return "WARMUP", []

    def choose_pathing_reference(row):
        champion = row["champion"]
        phase = row["phase"]

        champion_phase = (
            pathing_history_champion_phase[
                (champion, phase)
            ]
        )

        phase_global = (
            pathing_history_phase[
                phase
            ]
        )

        for radius in TIME_LOCAL_RADII_SECONDS:
            local_candidates = (
                (
                    f"CHAMPION_PHASE_PATHING_TIME_{radius}s",
                    local_subset(
                        champion_phase,
                        row,
                        radius,
                    ),
                ),
                (
                    f"PHASE_PATHING_TIME_{radius}s",
                    local_subset(
                        phase_global,
                        row,
                        radius,
                    ),
                ),
            )

            for (
                scope,
                reference,
            ) in local_candidates:
                if len(
                    reference
                ) >= MIN_TIME_LOCAL_REFERENCE:
                    return (
                        scope,
                        reference,
                    )

        candidates = (
            (
                "CHAMPION_PHASE_PATHING",
                champion_phase,
            ),
            (
                "PHASE_PATHING",
                phase_global,
            ),
        )

        for (
            scope,
            reference,
        ) in candidates:
            if len(
                reference
            ) >= MIN_HISTORICAL_PATHING_INTERVALS:
                return (
                    scope,
                    reference,
                )

        return "WARMUP", []

    def attach_percentiles(row, reference, features):
        result = {}

        for feature in features:
            values = [
                old_row[feature]
                for old_row in reference
                if old_row.get(feature) is not None
            ]

            value = row.get(feature)

            if value is None or not values:
                continue

            result[feature] = percentile_rank(
                values,
                value,
            )

        return result

    for match_id in ordered_match_ids:
        rows = sorted(
            by_match[match_id],
            key=lambda row: row["start_timestamp"],
        )

        for row in rows:
            # ------------------------------------------------
            # Defaults
            # ------------------------------------------------
            row["tempo_reference_size"] = 0
            row["tempo_reference_scope"] = "UNSCORED"
            row["tempo_score"] = None
            row["tempo_label"] = "UNSCORED"
            row["own_production_score"] = None
            row["relative_tempo_score"] = None

            row["pathing_reference_size"] = 0
            row["pathing_reference_scope"] = "UNSCORED"
            row["pathing_score"] = None
            row["pathing_label"] = "UNSCORED"
            row["pathing_xp_percentile"] = None
            row["pathing_jungle_cs_percentile"] = None

            # ------------------------------------------------
            # General tempo score
            # ------------------------------------------------
            if row["core_interval"]:
                tempo_scope, tempo_reference = (
                    choose_tempo_reference(row)
                )

                row["tempo_reference_scope"] = tempo_scope
                row["tempo_reference_size"] = len(tempo_reference)

                if tempo_reference:
                    percentiles = attach_percentiles(
                        row,
                        tempo_reference,
                        TEMPO_SCORE_WEIGHTS,
                    )

                    weighted_sum = 0.0
                    total_weight = 0.0

                    for feature, weight in TEMPO_SCORE_WEIGHTS.items():
                        percentile = percentiles.get(feature)

                        if percentile is None:
                            continue

                        weighted_sum += percentile * weight
                        total_weight += weight

                    score = (
                        weighted_sum / total_weight
                        if total_weight > 0
                        else None
                    )

                    own_features = (
                        "player_gold_per_min",
                        "player_xp_per_min",
                        "player_jungle_cs_per_min",
                    )

                    relative_features = (
                        "relative_gold_per_min",
                        "relative_xp_per_min",
                        "relative_jungle_cs_per_min",
                    )

                    own_values = [
                        percentiles[feature]
                        for feature in own_features
                        if feature in percentiles
                    ]

                    relative_values = [
                        percentiles[feature]
                        for feature in relative_features
                        if feature in percentiles
                    ]

                    row["own_production_score"] = (
                        mean(own_values)
                        if own_values
                        else None
                    )

                    row["relative_tempo_score"] = (
                        mean(relative_values)
                        if relative_values
                        else None
                    )

                    row["tempo_score"] = score
                    row["tempo_label"] = _tempo_label(score)

                    for feature, percentile in percentiles.items():
                        row[
                            f"{feature}_percentile"
                        ] = percentile

                else:
                    row["tempo_label"] = "WARMUP"

            # ------------------------------------------------
            # Pathing score: own XP + own Jungle CS only.
            # ------------------------------------------------
            if row["pathing_candidate_interval"]:
                path_scope, path_reference = (
                    choose_pathing_reference(row)
                )

                row["pathing_reference_scope"] = path_scope
                row["pathing_reference_size"] = len(path_reference)

                if path_reference:
                    path_percentiles = attach_percentiles(
                        row,
                        path_reference,
                        PATHING_SCORE_WEIGHTS,
                    )

                    weighted_sum = 0.0
                    total_weight = 0.0

                    for feature, weight in PATHING_SCORE_WEIGHTS.items():
                        percentile = path_percentiles.get(feature)

                        if percentile is None:
                            continue

                        weighted_sum += percentile * weight
                        total_weight += weight

                    pathing_score = (
                        weighted_sum / total_weight
                        if total_weight > 0
                        else None
                    )

                    row["pathing_score"] = pathing_score
                    row["pathing_xp_percentile"] = (
                        path_percentiles.get(
                            "player_xp_per_min"
                        )
                    )
                    row["pathing_jungle_cs_percentile"] = (
                        path_percentiles.get(
                            "player_jungle_cs_per_min"
                        )
                    )

                    if pathing_score is None:
                        row["pathing_label"] = "WARMUP"
                    elif pathing_score < PATHING_WATCH_THRESHOLD:
                        row["pathing_label"] = "LOW"
                    elif pathing_score < 50:
                        row["pathing_label"] = "BELOW_BASELINE"
                    elif pathing_score < 70:
                        row["pathing_label"] = "NORMAL"
                    else:
                        row["pathing_label"] = "STRONG"

                else:
                    row["pathing_label"] = "WARMUP"

        # ----------------------------------------------------
        # Only AFTER scoring the whole game do we update refs.
        # ----------------------------------------------------
        for row in rows:
            if row["core_interval"]:
                champion = row["champion"]
                phase = row["phase"]
                context = row["context_bucket"]

                history_champion_phase_context[
                    (champion, phase, context)
                ].append(row)

                history_phase_context[
                    (phase, context)
                ].append(row)

                history_champion_phase[
                    (champion, phase)
                ].append(row)

                history_phase[phase].append(row)

            if row["pathing_candidate_interval"]:
                champion = row["champion"]
                phase = row["phase"]

                pathing_history_champion_phase[
                    (champion, phase)
                ].append(row)

                pathing_history_phase[
                    phase
                ].append(row)


def _attach_pathing_boundary_guards(
    dataset,
):
    """
    V17 - GUARD BAND POUR LES ALERTES PATHING.

    FARMABLE reste une mesure de production personnelle.

    Mais pour déclencher WATCH / TROU DE PATHING, on exige aussi
    qu'il n'y ait pas de contexte majeur dans les ~60 secondes
    immédiatement AVANT ou APRÈS la fenêtre.

    Cela évite de transformer en "mauvais pathing" :
    - l'approche d'un combat ;
    - la sortie/entrée d'un reset ;
    - la préparation ou sortie d'un objectif ;
    - une death juste après la fenêtre ;
    - une prise de wave adjacente.

    Le guard ne modifie PAS les métriques de mesure FARMABLE.
    Il ne sert qu'à la logique d'alerte.
    """
    by_match = defaultdict(
        list
    )

    for row in dataset:
        by_match[
            row[
                "match_id"
            ]
        ].append(
            row
        )

    guard_ms = (
        PATHING_BOUNDARY_GUARD_SECONDS
        * 1000
    )

    for rows in by_match.values():
        rows = sorted(
            rows,
            key=lambda row:
                row[
                    "start_timestamp"
                ],
        )

        for row in rows:
            row[
                "pathing_guard_clean"
            ] = False

            row[
                "pathing_guard_contexts"
            ] = []

            row[
                "pathing_alert_candidate"
            ] = False

            if not row[
                "pathing_candidate_interval"
            ]:
                continue

            guard_start = max(
                0,
                row[
                    "start_timestamp"
                ]
                - guard_ms,
            )

            guard_end = (
                row[
                    "end_timestamp"
                ]
                + guard_ms
            )

            neighbors = [
                candidate
                for candidate in rows
                if (
                    candidate[
                        "end_timestamp"
                    ] > guard_start
                    and candidate[
                        "start_timestamp"
                    ] < guard_end
                )
            ]

            contexts = []

            if any(
                candidate.get(
                    "reset_context"
                )
                for candidate in neighbors
            ):
                contexts.append(
                    "RESET"
                )

            if any(
                candidate.get(
                    "player_combat_context"
                )
                for candidate in neighbors
            ):
                contexts.append(
                    "COMBAT_JOUEUR"
                )

            if any(
                candidate.get(
                    "objective_direct_context"
                )
                for candidate in neighbors
            ):
                contexts.append(
                    "OBJECTIF_DIRECT"
                )

            if any(
                candidate.get(
                    "player_death_affected"
                )
                for candidate in neighbors
            ):
                contexts.append(
                    "DEATH_WINDOW"
                )

            if any(
                candidate.get(
                    "lane_catch_context"
                )
                for candidate in neighbors
            ):
                contexts.append(
                    "LANE_CATCH"
                )

            row[
                "pathing_guard_contexts"
            ] = contexts

            row[
                "pathing_guard_clean"
            ] = (
                len(
                    contexts
                ) == 0
            )

            row[
                "pathing_alert_candidate"
            ] = (
                row[
                    "pathing_candidate_interval"
                ]
                and row[
                    "pathing_guard_clean"
                ]
            )



def _attach_interval_diagnostics(
    dataset,
):
    for row in dataset:
        tempo_score = row.get(
            "tempo_score"
        )

        pathing_score = row.get(
            "pathing_score"
        )

        row[
            "tempo_collapse"
        ] = (
            tempo_score is not None
            and tempo_score
            < TEMPO_COLLAPSE_THRESHOLD
        )

        row[
            "tempo_surge"
        ] = (
            tempo_score is not None
            and tempo_score
            >= TEMPO_SURGE_THRESHOLD
        )

        row[
            "dual_negative"
        ] = (
            row[
                "core_interval"
            ]
            and row[
                "worsened_resources"
            ] >= 2
        )

        row[
            "triple_negative"
        ] = (
            row[
                "core_interval"
            ]
            and row[
                "worsened_resources"
            ] == 3
        )

        row[
            "free_tempo_collapse"
        ] = (
            row[
                "strict_free_tempo_interval"
            ]
            and row[
                "tempo_collapse"
            ]
        )

        row[
            "farmable_tempo_collapse"
        ] = (
            row[
                "farmable_tempo_interval"
            ]
            and row[
                "tempo_collapse"
            ]
        )

        # V15 : le WATCH pathing dépend du PATHING SCORE personnel,
        # jamais directement du score relatif au jungler adverse.
        row[
            "single_minute_pathing_watch"
        ] = (
            row[
                "pathing_alert_candidate"
            ]
            and pathing_score is not None
            and pathing_score
            < PATHING_WATCH_THRESHOLD
        )

        row[
            "contextual_low_tempo"
        ] = (
            row[
                "core_interval"
            ]
            and not row[
                "pathing_candidate_interval"
            ]
            and row[
                "tempo_collapse"
            ]
        )

        row[
            "low_production_unexplained"
        ] = row[
            "single_minute_pathing_watch"
        ]

        # Initialisation des épisodes soutenus.
        row[
            "sustained_pathing_hole"
        ] = False
        row[
            "pathing_hole_episode_id"
        ] = None
        row[
            "pathing_hole_duration_min"
        ] = None
        row[
            "pathing_hole_score"
        ] = None
        row[
            "pathing_hole_confidence"
        ] = None

        # Production personnelle pendant l'épisode.
        row[
            "pathing_hole_own_xp_per_min"
        ] = None
        row[
            "pathing_hole_own_jungle_cs_per_min"
        ] = None

        # Comparaison adverse = contexte, pas critère de déclenchement.
        row[
            "pathing_hole_relative_gold_per_min"
        ] = None
        row[
            "pathing_hole_relative_xp_per_min"
        ] = None
        row[
            "pathing_hole_relative_jungle_cs_per_min"
        ] = None

        # Clés legacy conservées pour compatibilité d'affichage.
        row[
            "pathing_hole_gold_per_min"
        ] = None
        row[
            "pathing_hole_xp_per_min"
        ] = None
        row[
            "pathing_hole_cs_per_min"
        ] = None


def _attach_sustained_pathing_holes(
    dataset,
):
    """
    Alerte PATHING V15.

    - une fenêtre isolée faible = WATCH ;
    - une alerte forte exige >= 2 fenêtres consécutives (~2 min) ;
    - le déclencheur est la production PERSONNELLE historique
      (XP + Jungle CS), pas la réussite du jungler adverse ;
    - les valeurs relatives vs JGL sont seulement rapportées comme
      contexte/opportunity cost.
    """
    by_match = defaultdict(list)

    for row in dataset:
        by_match[
            row[
                "match_id"
            ]
        ].append(row)

    for match_id, rows in by_match.items():
        rows = sorted(
            rows,
            key=lambda row:
                row[
                    "start_timestamp"
                ],
        )

        current = []
        episode_index = 0

        def flush():
            nonlocal current
            nonlocal episode_index

            if len(current) < 2:
                current = []
                return

            duration = sum(
                row[
                    "duration_minutes"
                ]
                for row in current
            )

            if duration < 1.5:
                current = []
                return

            scored_rows = [
                row
                for row in current
                if row.get(
                    "pathing_score"
                ) is not None
            ]

            if len(scored_rows) < 2:
                current = []
                return

            score_weight = sum(
                row[
                    "duration_minutes"
                ]
                for row in scored_rows
            )

            weighted_score = sum(
                row[
                    "pathing_score"
                ]
                * row[
                    "duration_minutes"
                ]
                for row in scored_rows
            ) / score_weight

            # Au moins une des deux dimensions doit être franchement
            # faible en moyenne. Cela évite un score composite faible
            # créé uniquement par de petites baisses partout.
            xp_percentiles = [
                row[
                    "pathing_xp_percentile"
                ]
                for row in scored_rows
                if row.get(
                    "pathing_xp_percentile"
                ) is not None
            ]

            jcs_percentiles = [
                row[
                    "pathing_jungle_cs_percentile"
                ]
                for row in scored_rows
                if row.get(
                    "pathing_jungle_cs_percentile"
                ) is not None
            ]

            mean_xp_percentile = (
                mean(xp_percentiles)
                if xp_percentiles
                else 50
            )

            mean_jcs_percentile = (
                mean(jcs_percentiles)
                if jcs_percentiles
                else 50
            )

            is_hole = (
                weighted_score
                < PATHING_SUSTAINED_THRESHOLD
                and min(
                    mean_xp_percentile,
                    mean_jcs_percentile,
                ) < 30
            )

            if not is_hole:
                current = []
                return

            episode_index += 1

            episode_id = (
                f"{match_id}:PATH:{episode_index}"
            )

            strict_share = sum(
                row[
                    "duration_minutes"
                ]
                for row in current
                if row[
                    "strict_free_tempo_interval"
                ]
            ) / duration

            confidence = (
                "HIGH"
                if strict_share >= 0.75
                else "MEDIUM"
            )

            own_xp_rate = sum(
                row[
                    "player_xp_gain"
                ]
                for row in current
            ) / duration

            own_jcs_rate = sum(
                row[
                    "player_jungle_cs_gain"
                ]
                for row in current
            ) / duration

            relative_gold_rate = sum(
                row[
                    "relative_gold_change"
                ]
                for row in current
            ) / duration

            relative_xp_rate = sum(
                row[
                    "relative_xp_change"
                ]
                for row in current
            ) / duration

            relative_jcs_rate = sum(
                row[
                    "relative_jungle_cs_change"
                ]
                for row in current
            ) / duration

            for row in current:
                row[
                    "sustained_pathing_hole"
                ] = True
                row[
                    "pathing_hole_episode_id"
                ] = episode_id
                row[
                    "pathing_hole_duration_min"
                ] = duration
                row[
                    "pathing_hole_score"
                ] = weighted_score
                row[
                    "pathing_hole_confidence"
                ] = confidence

                row[
                    "pathing_hole_own_xp_per_min"
                ] = own_xp_rate
                row[
                    "pathing_hole_own_jungle_cs_per_min"
                ] = own_jcs_rate

                row[
                    "pathing_hole_relative_gold_per_min"
                ] = relative_gold_rate
                row[
                    "pathing_hole_relative_xp_per_min"
                ] = relative_xp_rate
                row[
                    "pathing_hole_relative_jungle_cs_per_min"
                ] = relative_jcs_rate

                # Legacy mappings.
                row[
                    "pathing_hole_gold_per_min"
                ] = relative_gold_rate
                row[
                    "pathing_hole_xp_per_min"
                ] = relative_xp_rate
                row[
                    "pathing_hole_cs_per_min"
                ] = relative_jcs_rate

            current = []

        previous_end = None

        for row in rows:
            pathing_score = row.get(
                "pathing_score"
            )

            # On construit une séquence seulement tant que la production
            # personnelle reste sous le niveau médian historique.
            eligible = (
                row[
                    "pathing_alert_candidate"
                ]
                and pathing_score is not None
                and pathing_score < 50
            )

            contiguous = (
                previous_end is None
                or abs(
                    row[
                        "start_timestamp"
                    ]
                    - previous_end
                ) <= 5_000
            )

            if eligible and contiguous:
                current.append(row)
                previous_end = row[
                    "end_timestamp"
                ]

            else:
                flush()
                current = []

                if eligible:
                    current = [row]
                    previous_end = row[
                        "end_timestamp"
                    ]
                else:
                    previous_end = None

        flush()


def _sum_duration(rows):
    return sum(
        row["duration_minutes"]
        for row in rows
    )


def _weighted_rate_from_gains(
    rows,
    key,
):
    duration = _sum_duration(
        rows
    )

    if duration <= 0:
        return None

    total = sum(
        row.get(key, 0)
        or 0
        for row in rows
    )

    return (
        total / duration
    )


def _weighted_mean(
    rows,
    key,
):
    values = []

    for row in rows:
        value = row.get(key)

        if value is None:
            continue

        values.append(
            (
                value,
                row[
                    "duration_minutes"
                ],
            )
        )

    total_weight = sum(
        weight
        for (
            _,
            weight,
        ) in values
    )

    if total_weight <= 0:
        return None

    return sum(
        value * weight
        for (
            value,
            weight,
        ) in values
    ) / total_weight


def _ratio_duration(
    rows,
    predicate,
):
    total = _sum_duration(
        rows
    )

    if total <= 0:
        return None

    positive = sum(
        row["duration_minutes"]
        for row in rows
        if predicate(row)
    )

    return (
        positive / total
    )


def _longest_negative_streak(
    rows,
):
    rows = sorted(
        rows,
        key=lambda row:
            row["start_timestamp"],
    )

    longest = 0.0
    current = 0.0

    for row in rows:
        if row["dual_negative"]:
            current += row[
                "duration_minutes"
            ]

            longest = max(
                longest,
                current,
            )

        else:
            current = 0.0

    return longest


def _recovery_times(
    rows,
):
    rows = sorted(
        (
            row
            for row in rows
            if row["core_interval"]
        ),
        key=lambda row:
            row["start_timestamp"],
    )

    recoveries = []

    for index, row in enumerate(rows):
        if not row["tempo_collapse"]:
            continue

        baseline = (
            row["start_gold_diff"],
            row["start_xp_diff"],
            row["start_cs_diff"],
        )

        recovery = None

        for later in rows[
            index + 1:
        ]:
            recovered = sum(
                (
                    later["end_gold_diff"]
                    >= baseline[0],
                    later["end_xp_diff"]
                    >= baseline[1],
                    later["end_cs_diff"]
                    >= baseline[2],
                )
            )

            if recovered >= 2:
                recovery = (
                    later["end_timestamp"]
                    - row["end_timestamp"]
                ) / 60000

                break

        if recovery is not None:
            recoveries.append(
                recovery
            )

    return recoveries


def build_game_tempo_dataset(
    interval_dataset,
    bundles,
):
    by_match = defaultdict(list)

    for row in interval_dataset:
        by_match[
            row["match_id"]
        ].append(row)

    bundle_by_match = {
        bundle[
            "match_id"
        ]: bundle
        for bundle in bundles
    }

    result = []

    for (
        match_id,
        bundle,
    ) in bundle_by_match.items():
        rows = by_match.get(
            match_id,
            [],
        )

        eligible = [
            row
            for row in rows
            if (
                row[
                    "good_frame"
                ]
                and row[
                    "start_timestamp"
                ]
                >= ANALYSIS_START_SECONDS
                * 1000
            )
        ]

        core = [
            row
            for row in rows
            if row[
                "core_interval"
            ]
        ]

        free = [
            row
            for row in core
            if row[
                "strict_free_tempo_interval"
            ]
        ]

        farmable = [
            row
            for row in core
            if row[
                "farmable_tempo_interval"
            ]
        ]

        mirrored = [
            row
            for row in core
            if row[
                "mirrored_farmable_interval"
            ]
        ]

        pathing_rows = [
            row
            for row in farmable
            if row[
                "pathing_candidate_interval"
            ]
        ]

        scored = [
            row
            for row in core
            if row.get(
                "tempo_score"
            ) is not None
        ]

        free_scored = [
            row
            for row in free
            if row.get(
                "tempo_score"
            ) is not None
        ]

        farmable_scored = [
            row
            for row in farmable
            if row.get(
                "tempo_score"
            ) is not None
        ]

        pathing_scored = [
            row
            for row in pathing_rows
            if row.get(
                "pathing_score"
            ) is not None
        ]

        total_eligible_minutes = (
            _sum_duration(
                eligible
            )
        )

        clean_minutes = (
            _sum_duration(
                core
            )
        )

        free_minutes = (
            _sum_duration(
                free
            )
        )

        farmable_minutes = (
            _sum_duration(
                farmable
            )
        )

        mirrored_minutes = (
            _sum_duration(
                mirrored
            )
        )

        pathing_minutes = (
            _sum_duration(
                pathing_rows
            )
        )

        coverage = (
            clean_minutes
            / total_eligible_minutes
            if total_eligible_minutes
            > 0
            else None
        )

        free_coverage = (
            free_minutes
            / total_eligible_minutes
            if total_eligible_minutes
            > 0
            else None
        )

        free_share_of_core = (
            free_minutes
            / clean_minutes
            if clean_minutes > 0
            else None
        )

        farmable_coverage = (
            farmable_minutes
            / total_eligible_minutes
            if total_eligible_minutes > 0
            else None
        )

        mirrored_coverage = (
            mirrored_minutes
            / total_eligible_minutes
            if total_eligible_minutes > 0
            else None
        )

        pathing_coverage = (
            pathing_minutes
            / total_eligible_minutes
            if total_eligible_minutes > 0
            else None
        )

        player_deaths = sum(
            row[
                "player_deaths"
            ]
            for row in rows
        )

        opponent_deaths = sum(
            row[
                "opponent_deaths"
            ]
            for row in rows
        )

        recoveries = (
            _recovery_times(
                rows
            )
        )

        game_minutes = (
            bundle[
                "game_duration"
            ]
            / 60
            if bundle[
                "game_duration"
            ] > 0
            else 0
        )

        per10 = (
            10
            / game_minutes
            if game_minutes > 0
            else None
        )

        collapse_count = sum(
            1
            for row in scored
            if row[
                "tempo_collapse"
            ]
        )

        free_collapse_count = sum(
            1
            for row in free_scored
            if row[
                "free_tempo_collapse"
            ]
        )

        contextual_low_count = sum(
            1
            for row in scored
            if row[
                "contextual_low_tempo"
            ]
        )

        lead_bleed_minutes = sum(
            row[
                "duration_minutes"
            ]
            for row in core
            if row[
                "lead_bleed"
            ]
        )

        sustained_pathing_ids = {
            row[
                "pathing_hole_episode_id"
            ]
            for row in pathing_scored
            if row.get(
                "sustained_pathing_hole"
            )
            and row.get(
                "pathing_hole_episode_id"
            ) is not None
        }

        sustained_pathing_scores = [
            row[
                "pathing_hole_score"
            ]
            for row in pathing_scored
            if row.get(
                "sustained_pathing_hole"
            )
            and row.get(
                "pathing_hole_score"
            ) is not None
        ]

        pathing_watch_count = sum(
            1
            for row in pathing_scored
            if row[
                "single_minute_pathing_watch"
            ]
            and not row[
                "sustained_pathing_hole"
            ]
        )

        result.append({
            "match_id": match_id,
            "game_creation": (
                bundle[
                    "game_creation"
                ]
            ),
            "game_duration": (
                bundle[
                    "game_duration"
                ]
            ),
            "champion": (
                bundle[
                    "champion"
                ]
            ),
            "opponent_champion": (
                bundle[
                    "opponent_champion"
                ]
            ),
            "win": (
                bundle[
                    "win"
                ]
            ),

            "player_deaths": (
                player_deaths
            ),
            "opponent_deaths": (
                opponent_deaths
            ),

            "eligible_tempo_minutes": (
                total_eligible_minutes
            ),

            # Hors deaths uniquement.
            "clean_tempo_minutes": (
                clean_minutes
            ),
            "clean_coverage_ratio": (
                coverage
            ),

            # Hors deaths + hors reset/combat/objectif.
            "free_tempo_minutes": (
                free_minutes
            ),
            "free_coverage_ratio": (
                free_coverage
            ),
            "free_share_of_core": (
                free_share_of_core
            ),

            "farmable_tempo_minutes": (
                farmable_minutes
            ),
            "farmable_coverage_ratio": (
                farmable_coverage
            ),
            "mirrored_farmable_minutes": (
                mirrored_minutes
            ),
            "mirrored_farmable_coverage_ratio": (
                mirrored_coverage
            ),
            "pathing_candidate_minutes": (
                pathing_minutes
            ),
            "pathing_candidate_coverage_ratio": (
                pathing_coverage
            ),

            # =================================================
            # HORS DEATHS - PRODUCTION
            # =================================================
            "clean_player_gold_per_min": (
                _weighted_rate_from_gains(
                    core,
                    "player_gold_gain",
                )
            ),
            "clean_player_xp_per_min": (
                _weighted_rate_from_gains(
                    core,
                    "player_xp_gain",
                )
            ),
            "clean_player_cs_per_min": (
                _weighted_rate_from_gains(
                    core,
                    "player_cs_gain",
                )
            ),
            "clean_player_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    core,
                    "player_jungle_cs_gain",
                )
            ),

            "clean_relative_gold_per_min": (
                _weighted_rate_from_gains(
                    core,
                    "relative_gold_change",
                )
            ),
            "clean_relative_xp_per_min": (
                _weighted_rate_from_gains(
                    core,
                    "relative_xp_change",
                )
            ),
            "clean_relative_cs_per_min": (
                _weighted_rate_from_gains(
                    core,
                    "relative_cs_change",
                )
            ),
            "clean_relative_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    core,
                    "relative_jungle_cs_change",
                )
            ),

            # =================================================
            # FREE TEMPO - PATHING/FARM LE PLUS PUR DISPONIBLE
            # =================================================
            "free_player_gold_per_min": (
                _weighted_rate_from_gains(
                    free,
                    "player_gold_gain",
                )
            ),
            "free_player_xp_per_min": (
                _weighted_rate_from_gains(
                    free,
                    "player_xp_gain",
                )
            ),
            "free_player_cs_per_min": (
                _weighted_rate_from_gains(
                    free,
                    "player_cs_gain",
                )
            ),
            "free_player_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    free,
                    "player_jungle_cs_gain",
                )
            ),

            "free_relative_gold_per_min": (
                _weighted_rate_from_gains(
                    free,
                    "relative_gold_change",
                )
            ),
            "free_relative_xp_per_min": (
                _weighted_rate_from_gains(
                    free,
                    "relative_xp_change",
                )
            ),
            "free_relative_cs_per_min": (
                _weighted_rate_from_gains(
                    free,
                    "relative_cs_change",
                )
            ),
            "free_relative_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    free,
                    "relative_jungle_cs_change",
                )
            ),

            # =================================================
            # FARMABLE - couverture plus large que STRICT_FREE
            # =================================================
            "farmable_player_gold_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "player_gold_gain",
                )
            ),
            "farmable_player_xp_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "player_xp_gain",
                )
            ),
            "farmable_player_cs_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "player_cs_gain",
                )
            ),
            "farmable_player_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "player_jungle_cs_gain",
                )
            ),
            "farmable_relative_gold_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "relative_gold_change",
                )
            ),
            "farmable_relative_xp_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "relative_xp_change",
                )
            ),
            "farmable_relative_cs_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "relative_cs_change",
                )
            ),
            "farmable_relative_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "relative_jungle_cs_change",
                )
            ),

            # =================================================
            # MIRRORED FARMABLE - comparaison directe des JGL
            # =================================================
            "mirrored_relative_gold_per_min": (
                _weighted_rate_from_gains(
                    mirrored,
                    "relative_gold_change",
                )
            ),
            "mirrored_relative_xp_per_min": (
                _weighted_rate_from_gains(
                    mirrored,
                    "relative_xp_change",
                )
            ),
            "mirrored_relative_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    mirrored,
                    "relative_jungle_cs_change",
                )
            ),

            # =================================================
            # STABILITÉ
            # =================================================
            "dual_negative_ratio": (
                _ratio_duration(
                    core,
                    lambda row:
                        row[
                            "dual_negative"
                        ],
                )
            ),
            "triple_negative_ratio": (
                _ratio_duration(
                    core,
                    lambda row:
                        row[
                            "triple_negative"
                        ],
                )
            ),

            "free_dual_negative_ratio": (
                _ratio_duration(
                    free,
                    lambda row:
                        row[
                            "dual_negative"
                        ],
                )
            ),

            "free_triple_negative_ratio": (
                _ratio_duration(
                    free,
                    lambda row:
                        row[
                            "triple_negative"
                        ],
                )
            ),

            "farmable_dual_negative_ratio": (
                _ratio_duration(
                    farmable,
                    lambda row:
                        row[
                            "dual_negative"
                        ],
                )
            ),

            "farmable_triple_negative_ratio": (
                _ratio_duration(
                    farmable,
                    lambda row:
                        row[
                            "triple_negative"
                        ],
                )
            ),

            "lead_bleed_ratio": (
                lead_bleed_minutes
                / clean_minutes
                if clean_minutes > 0
                else None
            ),

            "max_negative_streak_min": (
                _longest_negative_streak(
                    core
                )
            ),

            "free_max_negative_streak_min": (
                _longest_negative_streak(
                    free
                )
            ),

            "worst_gold_loss_per_min": max(
                (
                    max(
                        0,
                        -row[
                            "relative_gold_per_min"
                        ],
                    )
                    for row in core
                    if row.get(
                        "relative_gold_per_min"
                    ) is not None
                ),
                default=0,
            ),

            "worst_xp_loss_per_min": max(
                (
                    max(
                        0,
                        -row[
                            "relative_xp_per_min"
                        ],
                    )
                    for row in core
                    if row.get(
                        "relative_xp_per_min"
                    ) is not None
                ),
                default=0,
            ),

            "worst_cs_loss_per_min": max(
                (
                    max(
                        0,
                        -row[
                            "relative_cs_per_min"
                        ],
                    )
                    for row in core
                    if row.get(
                        "relative_cs_per_min"
                    ) is not None
                ),
                default=0,
            ),

            "free_worst_gold_loss_per_min": max(
                (
                    max(
                        0,
                        -row[
                            "relative_gold_per_min"
                        ],
                    )
                    for row in free
                    if row.get(
                        "relative_gold_per_min"
                    ) is not None
                ),
                default=0,
            ),

            "free_worst_xp_loss_per_min": max(
                (
                    max(
                        0,
                        -row[
                            "relative_xp_per_min"
                        ],
                    )
                    for row in free
                    if row.get(
                        "relative_xp_per_min"
                    ) is not None
                ),
                default=0,
            ),

            "free_worst_cs_loss_per_min": max(
                (
                    max(
                        0,
                        -row[
                            "relative_cs_per_min"
                        ],
                    )
                    for row in free
                    if row.get(
                        "relative_cs_per_min"
                    ) is not None
                ),
                default=0,
            ),

            # =================================================
            # COMPOSITES HISTORIQUES
            # =================================================
            "mean_tempo_score": (
                _weighted_mean(
                    scored,
                    "tempo_score",
                )
            ),
            "mean_own_production_score": (
                _weighted_mean(
                    scored,
                    "own_production_score",
                )
            ),
            "mean_relative_tempo_score": (
                _weighted_mean(
                    scored,
                    "relative_tempo_score",
                )
            ),

            "free_mean_tempo_score": (
                _weighted_mean(
                    free_scored,
                    "tempo_score",
                )
            ),

            "mean_pathing_score": (
                _weighted_mean(
                    pathing_scored,
                    "pathing_score",
                )
            ),

            "tempo_collapse_ratio": (
                _ratio_duration(
                    scored,
                    lambda row:
                        row[
                            "tempo_collapse"
                        ],
                )
            ),

            "free_tempo_collapse_ratio": (
                _ratio_duration(
                    free_scored,
                    lambda row:
                        row[
                            "free_tempo_collapse"
                        ],
                )
            ),

            "tempo_collapse_count": (
                collapse_count
            ),
            "tempo_collapse_per_10": (
                collapse_count
                * per10
                if per10 is not None
                else None
            ),

            "free_tempo_collapse_count": (
                free_collapse_count
            ),
            "free_tempo_collapse_per_10": (
                free_collapse_count
                * per10
                if per10 is not None
                else None
            ),

            "contextual_low_tempo_count": (
                contextual_low_count
            ),

            "median_collapse_recovery_min": (
                median(
                    recoveries
                )
                if recoveries
                else None
            ),

            # =================================================
            # ALERTES PATHING SOUTENUES
            # =================================================
            "sustained_pathing_holes": (
                len(
                    sustained_pathing_ids
                )
            ),
            "sustained_pathing_holes_per_10": (
                len(
                    sustained_pathing_ids
                )
                * per10
                if per10 is not None
                else None
            ),
            "worst_sustained_pathing_score": (
                min(
                    sustained_pathing_scores
                )
                if sustained_pathing_scores
                else None
            ),
            "single_minute_pathing_watches": (
                pathing_watch_count
            ),

            # =================================================
            # CONTEXTE
            # =================================================
            "reset_context_ratio": (
                _ratio_duration(
                    eligible,
                    lambda row:
                        row[
                            "reset_context"
                        ],
                )
            ),
            "combat_context_ratio": (
                _ratio_duration(
                    eligible,
                    lambda row:
                        row[
                            "player_combat_context"
                        ],
                )
            ),
            "opponent_combat_context_ratio": (
                _ratio_duration(
                    eligible,
                    lambda row:
                        row[
                            "opponent_combat_context"
                        ],
                )
            ),
            "objective_context_ratio": (
                _ratio_duration(
                    eligible,
                    lambda row:
                        row[
                            "objective_context"
                        ],
                )
            ),
            "player_death_affected_ratio": (
                _ratio_duration(
                    eligible,
                    lambda row:
                        row[
                            "player_death_affected"
                        ],
                )
            ),
            "opponent_death_affected_ratio": (
                _ratio_duration(
                    eligible,
                    lambda row:
                        row[
                            "opponent_death_affected"
                        ],
                )
            ),
        })

    result.sort(
        key=lambda row: (
            row[
                "game_creation"
            ],
            row[
                "match_id"
            ],
        )
    )

    return result


def build_game_phase_tempo_dataset(
    interval_dataset,
    game_tempo_dataset,
):
    """
    Une ligne = une game x une phase.

    V14 :
    - conserve les métriques hors deaths ;
    - ajoute FARMABLE ;
    - stocke l'état à l'entrée de phase ;
    - stocke les morts AVANT la phase.

    Le test conditionnel de phase ne doit jamais utiliser les morts
    FUTURES de la game pour juger un tempo EARLY.
    """
    total_death_map = {
        row[
            "match_id"
        ]: row[
            "player_deaths"
        ]
        for row in game_tempo_dataset
    }

    all_by_match = defaultdict(
        list
    )

    by_match_phase = defaultdict(
        list
    )

    for row in interval_dataset:
        all_by_match[
            row[
                "match_id"
            ]
        ].append(
            row
        )

        if not row[
            "core_interval"
        ]:
            continue

        by_match_phase[
            (
                row[
                    "match_id"
                ],
                row[
                    "phase"
                ],
            )
        ].append(
            row
        )

    phase_start_seconds = {
        label: start
        for (
            label,
            start,
            _,
        ) in PHASES
    }

    result = []

    for (
        match_id,
        phase,
    ), rows in (
        by_match_phase.items()
    ):
        rows = sorted(
            rows,
            key=lambda row:
                row[
                    "start_timestamp"
                ],
        )

        farmable = [
            row
            for row in rows
            if row[
                "farmable_tempo_interval"
            ]
        ]

        mirrored = [
            row
            for row in rows
            if row[
                "mirrored_farmable_interval"
            ]
        ]

        strict_free = [
            row
            for row in rows
            if row[
                "strict_free_tempo_interval"
            ]
        ]

        first = rows[0]

        phase_start_ms = (
            phase_start_seconds.get(
                phase,
                0,
            )
            * 1000
        )

        match_rows = sorted(
            all_by_match[
                match_id
            ],
            key=lambda row:
                row[
                    "start_timestamp"
                ],
        )

        deaths_before_phase = sum(
            row[
                "player_deaths"
            ]
            for row in match_rows
            if row[
                "end_timestamp"
            ] <= phase_start_ms
        )

        opponent_deaths_before_phase = sum(
            row[
                "opponent_deaths"
            ]
            for row in match_rows
            if row[
                "end_timestamp"
            ] <= phase_start_ms
        )

        # Première frame/intervalle disponible au début de la phase,
        # même si elle est ensuite exclue du CORE.
        entry_candidates = [
            row
            for row in match_rows
            if (
                row[
                    "phase"
                ] == phase
                and row[
                    "start_timestamp"
                ] >= phase_start_ms
            )
        ]

        entry = (
            entry_candidates[0]
            if entry_candidates
            else first
        )

        result.append({
            "match_id": (
                match_id
            ),
            "game_creation": (
                first[
                    "game_creation"
                ]
            ),
            "champion": (
                first[
                    "champion"
                ]
            ),
            "win": (
                first[
                    "win"
                ]
            ),
            "phase": (
                phase
            ),

            # Total game conservé pour diagnostic seulement.
            "player_deaths": (
                total_death_map.get(
                    match_id,
                    0,
                )
            ),

            # Variable temporellement valide pour la phase.
            "player_deaths_before_phase": (
                deaths_before_phase
            ),
            "opponent_deaths_before_phase": (
                opponent_deaths_before_phase
            ),

            "phase_entry_state": (
                entry[
                    "start_state"
                ]
            ),
            "phase_entry_gold_diff": (
                entry[
                    "start_gold_diff"
                ]
            ),
            "phase_entry_xp_diff": (
                entry[
                    "start_xp_diff"
                ]
            ),
            "phase_entry_cs_diff": (
                entry[
                    "start_cs_diff"
                ]
            ),

            "phase_core_minutes": (
                _sum_duration(
                    rows
                )
            ),
            "phase_farmable_minutes": (
                _sum_duration(
                    farmable
                )
            ),
            "phase_mirrored_minutes": (
                _sum_duration(
                    mirrored
                )
            ),
            "phase_free_minutes": (
                _sum_duration(
                    strict_free
                )
            ),

            "phase_player_gold_per_min": (
                _weighted_rate_from_gains(
                    rows,
                    "player_gold_gain",
                )
            ),
            "phase_player_xp_per_min": (
                _weighted_rate_from_gains(
                    rows,
                    "player_xp_gain",
                )
            ),
            "phase_player_cs_per_min": (
                _weighted_rate_from_gains(
                    rows,
                    "player_cs_gain",
                )
            ),
            "phase_player_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    rows,
                    "player_jungle_cs_gain",
                )
            ),

            "phase_relative_gold_per_min": (
                _weighted_rate_from_gains(
                    rows,
                    "relative_gold_change",
                )
            ),
            "phase_relative_xp_per_min": (
                _weighted_rate_from_gains(
                    rows,
                    "relative_xp_change",
                )
            ),
            "phase_relative_cs_per_min": (
                _weighted_rate_from_gains(
                    rows,
                    "relative_cs_change",
                )
            ),
            "phase_relative_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    rows,
                    "relative_jungle_cs_change",
                )
            ),

            # FARMABLE : meilleure couverture actionnable.
            "phase_farmable_player_gold_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "player_gold_gain",
                )
            ),
            "phase_farmable_player_xp_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "player_xp_gain",
                )
            ),
            "phase_farmable_player_cs_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "player_cs_gain",
                )
            ),
            "phase_farmable_player_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "player_jungle_cs_gain",
                )
            ),

            "phase_farmable_relative_gold_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "relative_gold_change",
                )
            ),
            "phase_farmable_relative_xp_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "relative_xp_change",
                )
            ),
            "phase_farmable_relative_cs_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "relative_cs_change",
                )
            ),
            "phase_farmable_relative_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "relative_jungle_cs_change",
                )
            ),

            # MIRRORED FARMABLE : comparaison directe des deux JGL.
            "phase_mirrored_relative_gold_per_min": (
                _weighted_rate_from_gains(
                    mirrored,
                    "relative_gold_change",
                )
            ),
            "phase_mirrored_relative_xp_per_min": (
                _weighted_rate_from_gains(
                    mirrored,
                    "relative_xp_change",
                )
            ),
            "phase_mirrored_relative_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    mirrored,
                    "relative_jungle_cs_change",
                )
            ),

            # STRICT FREE : haute pureté mais faible couverture.
            "phase_free_player_gold_per_min": (
                _weighted_rate_from_gains(
                    strict_free,
                    "player_gold_gain",
                )
            ),
            "phase_free_player_xp_per_min": (
                _weighted_rate_from_gains(
                    strict_free,
                    "player_xp_gain",
                )
            ),
            "phase_free_player_cs_per_min": (
                _weighted_rate_from_gains(
                    strict_free,
                    "player_cs_gain",
                )
            ),

            "phase_free_relative_gold_per_min": (
                _weighted_rate_from_gains(
                    strict_free,
                    "relative_gold_change",
                )
            ),
            "phase_free_relative_xp_per_min": (
                _weighted_rate_from_gains(
                    strict_free,
                    "relative_xp_change",
                )
            ),
            "phase_free_relative_cs_per_min": (
                _weighted_rate_from_gains(
                    strict_free,
                    "relative_cs_change",
                )
            ),
            "phase_free_relative_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    strict_free,
                    "relative_jungle_cs_change",
                )
            ),
        })

    result.sort(
        key=lambda row: (
            row[
                "game_creation"
            ],
            row[
                "match_id"
            ],
            row[
                "phase"
            ],
        )
    )

    return result


def summarize_match_phases(
    interval_dataset,
    match_id,
):
    rows = [
        row
        for row in interval_dataset
        if row[
            "match_id"
        ] == match_id
    ]

    phases = {}

    for phase, _, _ in PHASES:
        phase_rows = [
            row
            for row in rows
            if (
                row[
                    "phase"
                ] == phase
                and row[
                    "core_interval"
                ]
            )
        ]

        if not phase_rows:
            continue

        farmable = [
            row
            for row in phase_rows
            if row[
                "farmable_tempo_interval"
            ]
        ]

        mirrored = [
            row
            for row in phase_rows
            if row[
                "mirrored_farmable_interval"
            ]
        ]

        strict = [
            row
            for row in phase_rows
            if row[
                "strict_free_tempo_interval"
            ]
        ]

        scored = [
            row
            for row in phase_rows
            if row.get(
                "tempo_score"
            ) is not None
        ]

        pathing_scored = [
            row
            for row in farmable
            if (
                row[
                    "pathing_candidate_interval"
                ]
                and row.get(
                    "pathing_score"
                ) is not None
            )
        ]

        sustained_ids = {
            row[
                "pathing_hole_episode_id"
            ]
            for row in pathing_scored
            if (
                row.get(
                    "sustained_pathing_hole"
                )
                and row.get(
                    "pathing_hole_episode_id"
                )
            )
        }

        phases[phase] = {
            "minutes": _sum_duration(
                phase_rows
            ),
            "farmable_minutes": _sum_duration(
                farmable
            ),
            "mirrored_minutes": _sum_duration(
                mirrored
            ),
            "strict_minutes": _sum_duration(
                strict
            ),

            "player_xp_per_min": (
                _weighted_rate_from_gains(
                    phase_rows,
                    "player_xp_gain",
                )
            ),
            "player_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    phase_rows,
                    "player_jungle_cs_gain",
                )
            ),
            "relative_gold_per_min": (
                _weighted_rate_from_gains(
                    phase_rows,
                    "relative_gold_change",
                )
            ),
            "relative_xp_per_min": (
                _weighted_rate_from_gains(
                    phase_rows,
                    "relative_xp_change",
                )
            ),
            "relative_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    phase_rows,
                    "relative_jungle_cs_change",
                )
            ),

            "farmable_xp_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "player_xp_gain",
                )
            ),
            "farmable_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    farmable,
                    "player_jungle_cs_gain",
                )
            ),

            "mirrored_relative_gold_per_min": (
                _weighted_rate_from_gains(
                    mirrored,
                    "relative_gold_change",
                )
            ),
            "mirrored_relative_xp_per_min": (
                _weighted_rate_from_gains(
                    mirrored,
                    "relative_xp_change",
                )
            ),
            "mirrored_relative_jungle_cs_per_min": (
                _weighted_rate_from_gains(
                    mirrored,
                    "relative_jungle_cs_change",
                )
            ),

            "tempo_score": _weighted_mean(
                scored,
                "tempo_score",
            ),
            "pathing_score": _weighted_mean(
                pathing_scored,
                "pathing_score",
            ),

            "sustained_pathing_holes": len(
                sustained_ids
            ),
            "single_minute_watches": sum(
                1
                for row in pathing_scored
                if (
                    row[
                        "single_minute_pathing_watch"
                    ]
                    and not row[
                        "sustained_pathing_hole"
                    ]
                )
            ),
        }

    return phases


def _format_minute(
    timestamp_ms,
):
    total_seconds = int(
        timestamp_ms / 1000
    )

    return (
        f"{total_seconds // 60:02d}:"
        f"{total_seconds % 60:02d}"
    )


def _fmt_optional(
    value,
    pattern,
    fallback="N/A",
):
    if value is None:
        return fallback

    return pattern.format(
        value
    )


def render_match_tempo_report(
    interval_dataset,
    match_id,
):
    rows = [
        row
        for row in interval_dataset
        if row[
            "match_id"
        ] == match_id
    ]

    if not rows:
        return (
            "Aucune donnée Tempo pour ce match."
        )

    core = [
        row
        for row in rows
        if row[
            "core_interval"
        ]
    ]

    farmable = [
        row
        for row in core
        if row[
            "farmable_tempo_interval"
        ]
    ]

    mirrored = [
        row
        for row in core
        if row[
            "mirrored_farmable_interval"
        ]
    ]

    strict = [
        row
        for row in core
        if row[
            "strict_free_tempo_interval"
        ]
    ]

    scored = [
        row
        for row in core
        if row.get(
            "tempo_score"
        ) is not None
    ]

    pathing_scored = [
        row
        for row in farmable
        if (
            row[
                "pathing_candidate_interval"
            ]
            and row.get(
                "pathing_score"
            ) is not None
        )
    ]

    phases = summarize_match_phases(
        interval_dataset,
        match_id,
    )

    lines = [
        "================================",
        "JUNGLE TEMPO ANALYZER - MATCH V17",
        "================================",
        "",
        f"Match : {match_id}",
        (
            f"Hors deaths : {len(core)} intervalles | "
            f"FARMABLE joueur : {len(farmable)} | "
            f"MIRRORED : {len(mirrored)} | "
            f"STRICT FREE : {len(strict)}"
        ),
        "",
        (
            "PATHING SCORE = production personnelle XP + Jungle CS. "
            "La réussite du jungler adverse ne peut pas déclencher seule une alerte pathing."
        ),
        (
            "MIRRORED = comparaison directe uniquement quand aucun des deux junglers "
            "n'est en kill/assist/death/shop pendant la fenêtre."
        ),
        (
            f"ALERTE PATHING V17 = FARMABLE + guard ±"
            f"{PATHING_BOUNDARY_GUARD_SECONDS}s sans "
            "reset/combat/objectif/death/lane-catch proche."
        ),
        "",
        "--------------------------------",
        "PHASES",
        "--------------------------------",
    ]

    for phase, summary in phases.items():
        lines.extend([
            "",
            (
                f"{phase} | "
                f"{summary['minutes']:.1f} min clean | "
                f"{summary['farmable_minutes']:.1f} farmable | "
                f"{summary['mirrored_minutes']:.1f} mirrored"
            ),
            (
                "Tempo global vs JGL : "
                f"Gold {summary['relative_gold_per_min']:+.0f}/min | "
                f"XP {summary['relative_xp_per_min']:+.0f}/min | "
                f"JCS {summary['relative_jungle_cs_per_min']:+.2f}/min"
            ),
            (
                "Pathing personnel FARMABLE : "
                + _fmt_optional(
                    summary[
                        "farmable_xp_per_min"
                    ],
                    "{:.0f} XP/min",
                )
                + " | "
                + _fmt_optional(
                    summary[
                        "farmable_jungle_cs_per_min"
                    ],
                    "{:.2f} JCS/min",
                )
            ),
            (
                "Comparaison MIRRORED : "
                + _fmt_optional(
                    summary[
                        "mirrored_relative_gold_per_min"
                    ],
                    "{:+.0f} G/min",
                )
                + " | "
                + _fmt_optional(
                    summary[
                        "mirrored_relative_xp_per_min"
                    ],
                    "{:+.0f} XP/min",
                )
                + " | "
                + _fmt_optional(
                    summary[
                        "mirrored_relative_jungle_cs_per_min"
                    ],
                    "{:+.2f} JCS/min",
                )
            ),
            (
                "Scores historiques : "
                + _fmt_optional(
                    summary[
                        "tempo_score"
                    ],
                    "Tempo {:.0f}/100",
                )
                + " | "
                + _fmt_optional(
                    summary[
                        "pathing_score"
                    ],
                    "Pathing {:.0f}/100",
                )
            ),
            (
                f"Alertes pathing soutenues : "
                f"{summary['sustained_pathing_holes']} | "
                f"WATCH isolés : {summary['single_minute_watches']}"
            ),
        ])

    episodes = {}

    for row in pathing_scored:
        episode_id = row.get(
            "pathing_hole_episode_id"
        )

        if (
            row.get(
                "sustained_pathing_hole"
            )
            and episode_id
        ):
            episodes.setdefault(
                episode_id,
                row,
            )

    lines.extend([
        "",
        "--------------------------------",
        "TROUS DE PATHING SOUTENUS",
        "--------------------------------",
    ])

    if not episodes:
        lines.append(
            "Aucun trou soutenu >= ~2 min détecté."
        )
    else:
        for episode_id, row in sorted(
            episodes.items(),
            key=lambda pair:
                pair[1][
                    "pathing_hole_score"
                ],
        ):
            episode_rows = [
                candidate
                for candidate in pathing_scored
                if candidate.get(
                    "pathing_hole_episode_id"
                ) == episode_id
            ]

            episode_start = min(
                item[
                    "start_timestamp"
                ]
                for item in episode_rows
            )

            episode_end = max(
                item[
                    "end_timestamp"
                ]
                for item in episode_rows
            )

            lines.extend([
                "",
                (
                    f"{_format_minute(episode_start)}→"
                    f"{_format_minute(episode_end)} | "
                    f"Pathing {row['pathing_hole_score']:.0f}/100 | "
                    f"confiance {row['pathing_hole_confidence']}"
                ),
                (
                    "Production propre : "
                    f"{row['pathing_hole_own_xp_per_min']:.0f} XP/min | "
                    f"{row['pathing_hole_own_jungle_cs_per_min']:.2f} JCS/min"
                ),
                (
                    "Contexte vs JGL : "
                    f"Gold {row['pathing_hole_relative_gold_per_min']:+.0f}/min | "
                    f"XP {row['pathing_hole_relative_xp_per_min']:+.0f}/min | "
                    f"JCS {row['pathing_hole_relative_jungle_cs_per_min']:+.2f}/min"
                ),
                (
                    "Interprétation : production personnelle durablement basse "
                    "pour cette phase/champion ; candidat pathing/farm à revoir."
                ),
            ])

    watches = sorted(
        (
            row
            for row in pathing_scored
            if (
                row[
                    "single_minute_pathing_watch"
                ]
                and not row[
                    "sustained_pathing_hole"
                ]
            )
        ),
        key=lambda row:
            row[
                "pathing_score"
            ],
    )[:5]

    lines.extend([
        "",
        "--------------------------------",
        "WATCH PATHING 1 MINUTE",
        "--------------------------------",
    ])

    if not watches:
        lines.append(
            "Aucun WATCH isolé."
        )
    else:
        for row in watches:
            opponent_context = (
                " | JGL adverse en combat"
                if row[
                    "opponent_combat_context"
                ]
                else ""
            )

            lines.append(
                (
                    f"{_format_minute(row['start_timestamp'])}→"
                    f"{_format_minute(row['end_timestamp'])} | "
                    f"Pathing {row['pathing_score']:.0f}/100 | "
                    f"{row['player_xp_per_min']:.0f} XP/min | "
                    f"{row['player_jungle_cs_per_min']:.2f} JCS/min"
                    f"{opponent_context}"
                )
            )

    contextual = sorted(
        (
            row
            for row in scored
            if row[
                "contextual_low_tempo"
            ]
        ),
        key=lambda row:
            row[
                "tempo_score"
            ],
    )[:5]

    lines.extend([
        "",
        "--------------------------------",
        "FAIBLE TEMPO CONTEXTUALISÉ",
        "PAS UNE ERREUR AUTOMATIQUE",
        "--------------------------------",
    ])

    if not contextual:
        lines.append(
            "Aucune fenêtre contextualisée très faible."
        )
    else:
        for row in contextual:
            lines.append(
                (
                    f"{_format_minute(row['start_timestamp'])}→"
                    f"{_format_minute(row['end_timestamp'])} | "
                    f"Tempo {row['tempo_score']:.0f}/100 | "
                    f"{row['context_bucket']}"
                )
            )

    return "\n".join(lines)


def summarize_tempo_profile(
    game_dataset,
    win=None,
):
    rows = [
        row
        for row in game_dataset
        if (
            win is None
            or row[
                "win"
            ] == win
        )
    ]

    if not rows:
        return None

    def med(key):
        values = [
            row[key]
            for row in rows
            if row.get(
                key
            ) is not None
        ]

        return (
            median(values)
            if values
            else None
        )

    games_with_holes = sum(
        1
        for row in rows
        if row.get(
            "sustained_pathing_holes",
            0,
        ) > 0
    )

    games_with_watches = sum(
        1
        for row in rows
        if row.get(
            "single_minute_pathing_watches",
            0,
        ) > 0
    )

    return {
        "games": len(rows),

        "clean_minutes": med(
            "clean_tempo_minutes"
        ),
        "clean_coverage": med(
            "clean_coverage_ratio"
        ),
        "farmable_minutes": med(
            "farmable_tempo_minutes"
        ),
        "farmable_coverage": med(
            "farmable_coverage_ratio"
        ),
        "mirrored_minutes": med(
            "mirrored_farmable_minutes"
        ),
        "mirrored_coverage": med(
            "mirrored_farmable_coverage_ratio"
        ),
        "strict_minutes": med(
            "free_tempo_minutes"
        ),
        "strict_coverage": med(
            "free_coverage_ratio"
        ),

        "clean_relative_gold": med(
            "clean_relative_gold_per_min"
        ),
        "clean_relative_xp": med(
            "clean_relative_xp_per_min"
        ),
        "clean_relative_jcs": med(
            "clean_relative_jungle_cs_per_min"
        ),

        "farmable_xp": med(
            "farmable_player_xp_per_min"
        ),
        "farmable_jcs": med(
            "farmable_player_jungle_cs_per_min"
        ),

        "mirrored_relative_gold": med(
            "mirrored_relative_gold_per_min"
        ),
        "mirrored_relative_xp": med(
            "mirrored_relative_xp_per_min"
        ),
        "mirrored_relative_jcs": med(
            "mirrored_relative_jungle_cs_per_min"
        ),

        "tempo_score": med(
            "mean_tempo_score"
        ),
        "pathing_score": med(
            "mean_pathing_score"
        ),

        "holes_median": med(
            "sustained_pathing_holes"
        ),
        "holes_total": sum(
            row.get(
                "sustained_pathing_holes",
                0,
            )
            for row in rows
        ),
        "games_with_holes_percent": (
            games_with_holes
            / len(rows)
            * 100
        ),

        "watches_median": med(
            "single_minute_pathing_watches"
        ),
        "watches_total": sum(
            row.get(
                "single_minute_pathing_watches",
                0,
            )
            for row in rows
        ),
        "games_with_watches_percent": (
            games_with_watches
            / len(rows)
            * 100
        ),
    }


def render_tempo_profile(
    title,
    summary,
):
    lines = [
        "================================",
        title,
        "================================",
    ]

    if not summary:
        lines.append(
            "Pas assez de données."
        )

        return "\n".join(lines)

    lines.extend([
        "",
        f"Games : {summary['games']}",
        "",
        "Couverture médiane :",
        (
            "  Hors deaths : "
            + _fmt_optional(
                summary[
                    "clean_minutes"
                ],
                "{:.1f} min",
            )
            + " | "
            + _fmt_optional(
                summary[
                    "clean_coverage"
                ],
                "{:.1%}",
            )
        ),
        (
            "  FARMABLE joueur : "
            + _fmt_optional(
                summary[
                    "farmable_minutes"
                ],
                "{:.1f} min",
            )
            + " | "
            + _fmt_optional(
                summary[
                    "farmable_coverage"
                ],
                "{:.1%}",
            )
        ),
        (
            "  MIRRORED : "
            + _fmt_optional(
                summary[
                    "mirrored_minutes"
                ],
                "{:.1f} min",
            )
            + " | "
            + _fmt_optional(
                summary[
                    "mirrored_coverage"
                ],
                "{:.1%}",
            )
        ),
        (
            "  STRICT FREE : "
            + _fmt_optional(
                summary[
                    "strict_minutes"
                ],
                "{:.1f} min",
            )
            + " | "
            + _fmt_optional(
                summary[
                    "strict_coverage"
                ],
                "{:.1%}",
            )
        ),
        "",
        "Tempo global hors deaths vs JGL :",
        (
            "  Gold "
            + _fmt_optional(
                summary[
                    "clean_relative_gold"
                ],
                "{:+.0f}/min",
            )
            + " | XP "
            + _fmt_optional(
                summary[
                    "clean_relative_xp"
                ],
                "{:+.0f}/min",
            )
            + " | JCS "
            + _fmt_optional(
                summary[
                    "clean_relative_jcs"
                ],
                "{:+.2f}/min",
            )
        ),
        "",
        "Pathing personnel FARMABLE :",
        (
            "  XP "
            + _fmt_optional(
                summary[
                    "farmable_xp"
                ],
                "{:.0f}/min",
            )
            + " | JCS "
            + _fmt_optional(
                summary[
                    "farmable_jcs"
                ],
                "{:.2f}/min",
            )
        ),
        "",
        "Comparaison neutre MIRRORED vs JGL :",
        (
            "  Gold "
            + _fmt_optional(
                summary[
                    "mirrored_relative_gold"
                ],
                "{:+.0f}/min",
            )
            + " | XP "
            + _fmt_optional(
                summary[
                    "mirrored_relative_xp"
                ],
                "{:+.0f}/min",
            )
            + " | JCS "
            + _fmt_optional(
                summary[
                    "mirrored_relative_jcs"
                ],
                "{:+.2f}/min",
            )
        ),
        "",
        (
            "Tempo Score médian : "
            + _fmt_optional(
                summary[
                    "tempo_score"
                ],
                "{:.0f}/100",
            )
        ),
        (
            "Pathing Score médian : "
            + _fmt_optional(
                summary[
                    "pathing_score"
                ],
                "{:.0f}/100",
            )
        ),
        "",
        (
            f"Trous soutenus : {summary['holes_total']} total | "
            f"{summary['games_with_holes_percent']:.1f}% des games | "
            + _fmt_optional(
                summary[
                    "holes_median"
                ],
                "médiane {:.1f}/game",
            )
        ),
        (
            f"WATCH isolés : {summary['watches_total']} total | "
            f"{summary['games_with_watches_percent']:.1f}% des games | "
            + _fmt_optional(
                summary[
                    "watches_median"
                ],
                "médiane {:.1f}/game",
            )
        ),
    ])

    return "\n".join(lines)



# ============================================================
# V16 - PATHING ALERT AUDIT
# ============================================================

def render_pathing_alert_audit(
    interval_dataset,
    max_watches=12,
):
    """
    Audit de clôture des alertes pathing.

    Objectif :
    - voir TOUTES les alertes soutenues ;
    - vérifier leur contexte aux frontières ;
    - voir quelle référence historique a réellement servi ;
    - ne pas figer des seuils sur seulement un compteur global.
    """
    by_match = defaultdict(list)

    for row in interval_dataset:
        by_match[
            row[
                "match_id"
            ]
        ].append(
            row
        )

    episode_rows = defaultdict(list)
    watches = []
    scope_counts = defaultdict(int)
    scored_pathing = 0
    local_reference_count = 0
    rejected_by_guard = 0
    guard_reasons = defaultdict(int)

    for row in interval_dataset:
        if (
            row.get(
                "pathing_candidate_interval"
            )
            and not row.get(
                "pathing_guard_clean",
                False,
            )
        ):
            rejected_by_guard += 1

            for reason in row.get(
                "pathing_guard_contexts",
                [],
            ):
                guard_reasons[
                    reason
                ] += 1

        if row.get(
            "pathing_score"
        ) is not None:
            scored_pathing += 1

            scope = row.get(
                "pathing_reference_scope",
                "UNKNOWN",
            )

            scope_counts[
                scope
            ] += 1

            if "TIME_" in scope:
                local_reference_count += 1

        episode_id = row.get(
            "pathing_hole_episode_id"
        )

        if (
            row.get(
                "sustained_pathing_hole"
            )
            and episode_id
        ):
            episode_rows[
                episode_id
            ].append(
                row
            )

        if (
            row.get(
                "single_minute_pathing_watch"
            )
            and not row.get(
                "sustained_pathing_hole"
            )
        ):
            watches.append(
                row
            )

    episodes = []

    for (
        episode_id,
        rows,
    ) in episode_rows.items():
        rows = sorted(
            rows,
            key=lambda row:
                row[
                    "start_timestamp"
                ],
        )

        first = rows[0]
        last = rows[-1]

        match_rows = sorted(
            by_match[
                first[
                    "match_id"
                ]
            ],
            key=lambda row:
                row[
                    "start_timestamp"
                ],
        )

        start_ts = first[
            "start_timestamp"
        ]
        end_ts = last[
            "end_timestamp"
        ]

        boundary_start = max(
            0,
            start_ts
            - 60_000,
        )

        boundary_end = (
            end_ts
            + 60_000
        )

        boundary_rows = [
            row
            for row in match_rows
            if (
                row[
                    "end_timestamp"
                ] > boundary_start
                and row[
                    "start_timestamp"
                ] < boundary_end
            )
        ]

        boundary_context = []

        if any(
            row.get(
                "reset_context"
            )
            for row in boundary_rows
        ):
            boundary_context.append(
                "RESET±1m"
            )

        if any(
            row.get(
                "player_combat_context"
            )
            for row in boundary_rows
        ):
            boundary_context.append(
                "COMBAT_JOUEUR±1m"
            )

        if any(
            row.get(
                "objective_direct_context"
            )
            for row in boundary_rows
        ):
            boundary_context.append(
                "OBJECTIF_DIRECT±1m"
            )

        if any(
            row.get(
                "objective_nearby_context"
            )
            for row in rows
        ):
            boundary_context.append(
                "OBJECTIF_PROCHE"
            )

        if any(
            row.get(
                "lane_catch_context"
            )
            for row in boundary_rows
        ):
            boundary_context.append(
                "LANE_CATCH±1m"
            )

        if any(
            row.get(
                "player_death_affected"
            )
            for row in boundary_rows
        ):
            boundary_context.append(
                "DEATH_WINDOW±1m"
            )

        duration = sum(
            row[
                "duration_minutes"
            ]
            for row in rows
        )

        strict_share = (
            sum(
                row[
                    "duration_minutes"
                ]
                for row in rows
                if row.get(
                    "strict_free_tempo_interval"
                )
            )
            / duration
            if duration > 0
            else 0
        )

        mirrored_share = (
            sum(
                row[
                    "duration_minutes"
                ]
                for row in rows
                if row.get(
                    "mirrored_farmable_interval"
                )
            )
            / duration
            if duration > 0
            else 0
        )

        xp_percentiles = [
            row[
                "pathing_xp_percentile"
            ]
            for row in rows
            if row.get(
                "pathing_xp_percentile"
            ) is not None
        ]

        jcs_percentiles = [
            row[
                "pathing_jungle_cs_percentile"
            ]
            for row in rows
            if row.get(
                "pathing_jungle_cs_percentile"
            ) is not None
        ]

        references = sorted({
            row.get(
                "pathing_reference_scope",
                "UNKNOWN",
            )
            for row in rows
        })

        reference_sizes = [
            row.get(
                "pathing_reference_size",
                0,
            )
            for row in rows
        ]

        episodes.append({
            "episode_id": episode_id,
            "match_id": first[
                "match_id"
            ],
            "champion": first[
                "champion"
            ],
            "win": first[
                "win"
            ],
            "phase": first[
                "phase"
            ],
            "start": start_ts,
            "end": end_ts,
            "duration": duration,
            "score": first.get(
                "pathing_hole_score"
            ),
            "confidence": first.get(
                "pathing_hole_confidence"
            ),
            "own_xp": first.get(
                "pathing_hole_own_xp_per_min"
            ),
            "own_jcs": first.get(
                "pathing_hole_own_jungle_cs_per_min"
            ),
            "relative_gold": first.get(
                "pathing_hole_relative_gold_per_min"
            ),
            "relative_xp": first.get(
                "pathing_hole_relative_xp_per_min"
            ),
            "relative_jcs": first.get(
                "pathing_hole_relative_jungle_cs_per_min"
            ),
            "xp_pct": (
                mean(
                    xp_percentiles
                )
                if xp_percentiles
                else None
            ),
            "jcs_pct": (
                mean(
                    jcs_percentiles
                )
                if jcs_percentiles
                else None
            ),
            "strict_share": strict_share,
            "mirrored_share": mirrored_share,
            "boundary_context": (
                boundary_context
            ),
            "references": (
                references
            ),
            "min_reference_size": (
                min(
                    reference_sizes
                )
                if reference_sizes
                else 0
            ),
        })

    episodes.sort(
        key=lambda item: (
            item[
                "score"
            ]
            if item[
                "score"
            ] is not None
            else 100,
            item[
                "match_id"
            ],
        )
    )

    watches = sorted(
        watches,
        key=lambda row:
            row[
                "pathing_score"
            ],
    )

    by_phase = defaultdict(int)
    by_champion = defaultdict(int)
    win_episodes = 0
    loss_episodes = 0

    for episode in episodes:
        by_phase[
            episode[
                "phase"
            ]
        ] += 1

        by_champion[
            episode[
                "champion"
            ]
        ] += 1

        if episode[
            "win"
        ]:
            win_episodes += 1
        else:
            loss_episodes += 1

    lines = [
        "================================",
        "PATHING ALERT AUDIT V17",
        "================================",
        "",
        (
            f"Intervalles pathing scorés : "
            f"{scored_pathing}"
        ),
        (
            f"Référence TIME-LOCAL utilisée : "
            f"{local_reference_count} "
            f"({local_reference_count / scored_pathing * 100:.1f}%)"
            if scored_pathing
            else "Référence TIME-LOCAL utilisée : 0"
        ),
        (
            f"Alertes soutenues : "
            f"{len(episodes)} "
            f"(wins {win_episodes} / losses {loss_episodes})"
        ),
        (
            f"WATCH isolés : "
            f"{len(watches)}"
        ),
        (
            f"Fenêtres FARMABLE rejetées pour alerte par guard ±"
            f"{PATHING_BOUNDARY_GUARD_SECONDS}s : "
            f"{rejected_by_guard}"
        ),
        "",
        "Raisons de rejet guard :",
    ]

    if guard_reasons:
        for (
            reason,
            count,
        ) in sorted(
            guard_reasons.items(),
            key=lambda item:
                item[1],
            reverse=True,
        ):
            lines.append(
                f"  {reason} : {count}"
            )
    else:
        lines.append(
            "  Aucune."
        )

    lines.extend([
        "",
        "Références historiques utilisées :",
    ])

    if scope_counts:
        for (
            scope,
            count,
        ) in sorted(
            scope_counts.items(),
            key=lambda item:
                item[1],
            reverse=True,
        ):
            lines.append(
                f"  {scope} : {count}"
            )
    else:
        lines.append(
            "  Aucune référence scorée."
        )

    lines.extend([
        "",
        "Alertes par phase : "
        + (
            ", ".join(
                f"{phase}={count}"
                for (
                    phase,
                    count,
                ) in sorted(
                    by_phase.items()
                )
            )
            if by_phase
            else "aucune"
        ),
        (
            "Alertes par champion : "
            + (
                ", ".join(
                    f"{champion}={count}"
                    for (
                        champion,
                        count,
                    ) in sorted(
                        by_champion.items(),
                        key=lambda item:
                            item[1],
                        reverse=True,
                    )
                )
                if by_champion
                else "aucune"
            )
        ),
        "",
        "--------------------------------",
        "TOUTES LES ALERTES SOUTENUES",
        "--------------------------------",
    ])

    if not episodes:
        lines.append(
            "Aucune alerte soutenue."
        )

    for (
        index,
        episode,
    ) in enumerate(
        episodes,
        start=1,
    ):
        context = (
            ", ".join(
                episode[
                    "boundary_context"
                ]
            )
            if episode[
                "boundary_context"
            ]
            else "AUCUN CONTEXTE ±1m DÉTECTÉ"
        )

        references = ", ".join(
            episode[
                "references"
            ]
        )

        lines.extend([
            "",
            (
                f"ALERTE #{index} | "
                f"{episode['champion']} | "
                f"{'WIN' if episode['win'] else 'LOSS'} | "
                f"{episode['phase']}"
            ),
            (
                f"Match : "
                f"{episode['match_id']}"
            ),
            (
                f"Temps : "
                f"{_format_minute(episode['start'])}"
                f"→"
                f"{_format_minute(episode['end'])} "
                f"({episode['duration']:.1f} min)"
            ),
            (
                f"Pathing Score agrégé : "
                f"{episode['score']:.1f}/100 | "
                f"confiance {episode['confidence']}"
                if episode[
                    "score"
                ] is not None
                else "Pathing Score agrégé : N/A"
            ),
            (
                "Production perso : "
                f"{episode['own_xp']:.0f} XP/min | "
                f"{episode['own_jcs']:.2f} JCS/min"
                if (
                    episode[
                        "own_xp"
                    ] is not None
                    and episode[
                        "own_jcs"
                    ] is not None
                )
                else "Production perso : N/A"
            ),
            (
                "Percentiles perso moyens : "
                f"XP {episode['xp_pct']:.0f}e | "
                f"JCS {episode['jcs_pct']:.0f}e"
                if (
                    episode[
                        "xp_pct"
                    ] is not None
                    and episode[
                        "jcs_pct"
                    ] is not None
                )
                else "Percentiles perso moyens : N/A"
            ),
            (
                "Contexte relatif vs JGL : "
                f"Gold {episode['relative_gold']:+.0f}/min | "
                f"XP {episode['relative_xp']:+.0f}/min | "
                f"JCS {episode['relative_jcs']:+.2f}/min"
                if (
                    episode[
                        "relative_gold"
                    ] is not None
                    and episode[
                        "relative_xp"
                    ] is not None
                    and episode[
                        "relative_jcs"
                    ] is not None
                )
                else "Contexte relatif vs JGL : N/A"
            ),
            (
                f"STRICT share : "
                f"{episode['strict_share']:.0%} | "
                f"MIRRORED share : "
                f"{episode['mirrored_share']:.0%}"
            ),
            (
                f"Contexte aux frontières : "
                f"{context}"
            ),
            (
                f"Référence : "
                f"{references} | "
                f"N min={episode['min_reference_size']}"
            ),
        ])

    lines.extend([
        "",
        "--------------------------------",
        f"{min(max_watches, len(watches))} WATCH LES PLUS FAIBLES",
        "--------------------------------",
    ])

    if not watches:
        lines.append(
            "Aucun WATCH."
        )

    for row in watches[
        :max_watches
    ]:
        lines.append(
            (
                f"{row['champion']} | "
                f"{'WIN' if row['win'] else 'LOSS'} | "
                f"{row['phase']} | "
                f"{_format_minute(row['start_timestamp'])}"
                f"→"
                f"{_format_minute(row['end_timestamp'])} | "
                f"Pathing {row['pathing_score']:.0f}/100 | "
                f"XP {row['player_xp_per_min']:.0f}/min | "
                f"JCS {row['player_jungle_cs_per_min']:.2f}/min | "
                f"ref {row['pathing_reference_scope']} "
                f"N={row['pathing_reference_size']}"
            )
        )

    lines.extend([
        "",
        "Règle de décision :",
        (
            "- V17 filtre AVANT déclenchement les frontières "
            "RESET/COMBAT/OBJECTIF/DEATH/LANE_CATCH à ±60s ;"
        ),
        (
            "- si les alertes restantes sont propres et plausibles, "
            "les seuils pathing pourront être figés."
        ),
    ])

    return "\n".join(
        lines
    )
