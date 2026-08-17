from collections import defaultdict
from statistics import mean, median

from analysis.feature_engine import (
    percentile_rank,
)

from database.death_reader import (
    get_role_match_ids,
    get_player_death_events,
    get_relative_snapshot_before_or_at,
    get_relative_snapshot_after_or_at,
    get_relative_snapshot_strictly_after,
    get_events_after_death,
    get_events_before_death,
    get_events_around_death,
)

from database.event_reader import (
    get_match_context,
)


# ============================================================
# CONFIGURATION
# ============================================================

POST_OFFSETS_SECONDS = (
    60,
    120,
    180,
)

OBJECTIVE_WINDOW_SECONDS = 90
TRADE_WINDOW_SECONDS = 12
RECOVERY_MAX_MINUTES = 6

# Une mort très proche d'une précédente avant récupération peut
# faire partie d'une "death spiral".
DEATH_CHAIN_MAX_SECONDS = 240

# Nombre minimum de morts HISTORIQUES antérieures nécessaires
# pour attribuer un percentile composite suffisamment stable.
MIN_HISTORICAL_DEATH_REFERENCE = 10


# ============================================================
# HELPERS
# ============================================================

def _change(
    after,
    baseline,
    key,
):
    if not after or not baseline:
        return None

    return (
        after[key]
        - baseline[key]
    )


def _positive_cost(
    change_value,
):
    if change_value is None:
        return None

    return max(
        0,
        -change_value,
    )


def _objective_kind(event):
    monster = str(
        event.get(
            "monsterType",
            "",
        )
    ).upper()

    subtype = str(
        event.get(
            "monsterSubType",
            "",
        )
    ).upper()

    text = f"{monster} {subtype}"

    if "DRAGON" in text:
        return "DRAGON"

    if (
        "RIFTHERALD" in text
        or "HERALD" in text
    ):
        return "HERALD"

    if (
        "HORDE" in text
        or "GRUB" in text
    ):
        return "GRUB"

    if "BARON" in text:
        return "BARON"

    return "OTHER"


def _killer_team(
    event,
    context,
):
    team_id = event.get(
        "killerTeamId"
    )

    if team_id is not None:
        return team_id

    killer_id = event.get(
        "killerId"
    )

    player = context[
        "players"
    ].get(
        killer_id
    )

    if player:
        return player.get(
            "team_id"
        )

    return None


def _death_advantage_state(
    baseline,
):
    """
    Catégorise grossièrement l'état relatif avant la mort.
    """
    gold = baseline["gold_diff"]
    xp = baseline["xp_diff"]
    cs = baseline["cs_diff"]

    score = 0

    if gold >= 500:
        score += 1
    elif gold <= -500:
        score -= 1

    if xp >= 500:
        score += 1
    elif xp <= -500:
        score -= 1

    if cs >= 8:
        score += 1
    elif cs <= -8:
        score -= 1

    if score >= 2:
        return "EN_AVANCE"

    if score <= -2:
        return "EN_RETARD"

    return "EQUILIBRE"


def _zone_approx(
    x,
    y,
    my_team_id,
):
    """
    Classification volontairement APPROXIMATIVE.

    On évite de prétendre connaître précisément la zone de jungle
    sans polygones officiels. Le but ici est seulement de séparer
    les morts très proches d'une base / bord de map / centre-rivière.

    Summoner's Rift utilise grossièrement des coordonnées 0..15000.
    """
    if x is None or y is None:
        return "INCONNUE"

    if x < 2500 and y < 2500:
        raw = "BLUE_BASE_SIDE"

    elif x > 12500 and y > 12500:
        raw = "RED_BASE_SIDE"

    elif (
        abs(x - y) < 1200
        and 3500 < x < 11500
        and 3500 < y < 11500
    ):
        raw = "RIVER_OR_MID_APPROX"

    elif x < 5000 and y < 8500:
        raw = "BLUE_LOWER_SIDE_APPROX"

    elif y < 5000 and x < 8500:
        raw = "BLUE_LOWER_SIDE_APPROX"

    elif x > 10000 or y > 10000:
        raw = "RED_UPPER_SIDE_APPROX"

    else:
        raw = "MID_MAP_APPROX"

    # Lecture relative allié/adverse uniquement quand c'est raisonnable.
    if my_team_id == 100:
        if raw.startswith("BLUE_"):
            return "COTE_ALLIE_APPROX"
        if raw.startswith("RED_"):
            return "COTE_ADVERSE_APPROX"

    elif my_team_id == 200:
        if raw.startswith("RED_"):
            return "COTE_ALLIE_APPROX"
        if raw.startswith("BLUE_"):
            return "COTE_ADVERSE_APPROX"

    return raw


# ============================================================
# EVENT CONTEXT
# ============================================================

def _event_unique_key(event):
    # Identifiant déterministe pour éviter de compter plusieurs fois
    # le même événement dans les fenêtres de morts qui se chevauchent.
    return "|".join(
        str(value)
        for value in (
            event.get("timestamp"),
            event.get("type"),
            event.get("monsterType"),
            event.get("monsterSubType"),
            event.get("buildingType"),
            event.get("teamId"),
            event.get("killerId"),
            event.get("killerTeamId"),
        )
    )


def _analyze_event_context(
    match_id,
    puuid,
    death_timestamp,
):
    context = get_match_context(
        match_id,
        puuid,
    )

    if not context:
        return {}

    my_team_id = context[
        "my_team_id"
    ]

    enemy_jungle_id = context[
        "opponent_participant_id"
    ]

    after = get_events_after_death(
        match_id,
        death_timestamp,
        seconds=OBJECTIVE_WINDOW_SECONDS,
    )

    before = get_events_before_death(
        match_id,
        death_timestamp,
        seconds=OBJECTIVE_WINDOW_SECONDS,
    )

    result = {
        "enemy_objectives_after": 0,
        "ally_objectives_after": 0,
        "enemy_objectives_before": 0,
        "ally_objectives_before": 0,
        "enemy_towers_after": 0,
        "ally_towers_after": 0,
        "enemy_jungle_kills_after": 0,
        "enemy_objective_types_after": [],
        "enemy_objective_event_keys_after": [],
        "enemy_tower_event_keys_after": [],
        "objective_taken_within_90s_after": False,
        "objective_taken_within_90s_before": False,
    }

    def inspect(events, suffix):
        for event in events:
            event_type = event.get(
                "type"
            )

            if event_type == "ELITE_MONSTER_KILL":
                team_id = _killer_team(
                    event,
                    context,
                )

                if team_id is None:
                    continue

                kind = _objective_kind(
                    event
                )

                if suffix == "after":
                    result[
                        "objective_taken_within_90s_after"
                    ] = True

                else:
                    result[
                        "objective_taken_within_90s_before"
                    ] = True

                if team_id == my_team_id:
                    result[
                        f"ally_objectives_{suffix}"
                    ] += 1

                else:
                    result[
                        f"enemy_objectives_{suffix}"
                    ] += 1

                    if suffix == "after":
                        result[
                            "enemy_objective_types_after"
                        ].append(
                            kind
                        )

                        result[
                            "enemy_objective_event_keys_after"
                        ].append(
                            _event_unique_key(
                                event
                            )
                        )

            elif (
                suffix == "after"
                and event_type == "BUILDING_KILL"
            ):
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
                    continue

                if destroyed_team == my_team_id:
                    result[
                        "enemy_towers_after"
                    ] += 1

                    result[
                        "enemy_tower_event_keys_after"
                    ].append(
                        _event_unique_key(
                            event
                        )
                    )
                else:
                    result[
                        "ally_towers_after"
                    ] += 1

            elif (
                suffix == "after"
                and event_type == "CHAMPION_KILL"
                and event.get(
                    "killerId"
                ) == enemy_jungle_id
            ):
                result[
                    "enemy_jungle_kills_after"
                ] += 1

    inspect(
        before,
        "before",
    )

    inspect(
        after,
        "after",
    )

    return result


def _detect_trade(
    match_id,
    puuid,
    death_timestamp,
):
    context = get_match_context(
        match_id,
        puuid,
    )

    if not context:
        return {
            "trade": False,
            "enemy_jungle_trade": False,
            "player_kills_around_death": 0,
        }

    my_id = context[
        "my_participant_id"
    ]

    enemy_jungle_id = context[
        "opponent_participant_id"
    ]

    events = get_events_around_death(
        match_id,
        death_timestamp,
        before_seconds=TRADE_WINDOW_SECONDS,
        after_seconds=TRADE_WINDOW_SECONDS,
    )

    player_kills = [
        event
        for event in events
        if event.get(
            "killerId"
        ) == my_id
    ]

    return {
        "trade": bool(
            player_kills
        ),

        "enemy_jungle_trade": any(
            event.get(
                "victimId"
            )
            == enemy_jungle_id
            for event in player_kills
        ),

        "player_kills_around_death": (
            len(player_kills)
        ),
    }


# ============================================================
# IMPACT IMMÉDIAT + TRAJECTOIRE POST-MORT
# ============================================================

def _build_bracket_impact(
    match_id,
    puuid,
    death_timestamp,
    baseline,
):
    """
    Mesure principale du coût immédiat.

    On compare :
        dernière frame <= mort
        première frame STRICTEMENT > mort

    Les timelines Riot étant généralement échantillonnées à la
    minute, ce n'est PAS un vrai "60 secondes après la mort".
    C'est l'intervalle de frames qui ENCADRE la mort.

    Avantage :
        toutes les morts sont mesurées sur un intervalle de frame
        comparable (~1 minute), sans dépendre du décalage de la mort
        à l'intérieur de la minute.
    """
    after = (
        get_relative_snapshot_strictly_after(
            match_id,
            puuid,
            death_timestamp,
        )
    )

    if not after:
        return None

    duration = (
        after["player_timestamp"]
        - baseline["player_timestamp"]
    ) / 1000

    seconds_after_death = (
        after["player_timestamp"]
        - death_timestamp
    ) / 1000

    seconds_before_death = (
        death_timestamp
        - baseline["player_timestamp"]
    ) / 1000

    result = {
        "impact_after_player_timestamp": (
            after["player_timestamp"]
        ),

        "impact_after_opponent_timestamp": (
            after["opponent_timestamp"]
        ),

        "impact_interval_seconds": duration,

        "impact_seconds_before_death": (
            seconds_before_death
        ),

        "impact_seconds_after_death": (
            seconds_after_death
        ),
    }

    for key in (
        "gold_diff",
        "cs_diff",
        "xp_diff",
        "level_diff",
    ):
        result[
            f"impact_{key}_change"
        ] = (
            after[key]
            - baseline[key]
        )

    result[
        "impact_player_gold_gain"
    ] = (
        after["player"]["gold"]
        - baseline["player"]["gold"]
    )

    result[
        "impact_opponent_gold_gain"
    ] = (
        after["opponent"]["gold"]
        - baseline["opponent"]["gold"]
    )

    result[
        "impact_player_cs_gain"
    ] = (
        after["player"]["cs"]
        - baseline["player"]["cs"]
    )

    result[
        "impact_opponent_cs_gain"
    ] = (
        after["opponent"]["cs"]
        - baseline["opponent"]["cs"]
    )

    result[
        "impact_player_xp_gain"
    ] = (
        after["player"]["xp"]
        - baseline["player"]["xp"]
    )

    result[
        "impact_opponent_xp_gain"
    ] = (
        after["opponent"]["xp"]
        - baseline["opponent"]["xp"]
    )

    return result



def _build_post_death_tempo_window(
    match_id,
    puuid,
    death_timestamp,
):
    """
    Fenêtre COMPARABLE de tempo post-mort.

    On prend :
        A = première frame STRICTEMENT après la mort
        B = frame suivante environ 60 s plus tard

    Contrairement à l'intervalle qui encadre la mort, cette
    fenêtre contient toujours une minute complète APRES le
    premier état observable post-mort.

    Elle ne mesure pas le coût instantané de la mort ; elle
    mesure si le tempo continue à se dégrader ou se reconstruit
    juste après.
    """
    start = (
        get_relative_snapshot_strictly_after(
            match_id,
            puuid,
            death_timestamp,
        )
    )

    if not start:
        return None

    target = (
        start["player_timestamp"]
        + 60 * 1000
    )

    end = (
        get_relative_snapshot_after_or_at(
            match_id,
            puuid,
            target,
        )
    )

    if not end:
        return None

    duration = (
        end["player_timestamp"]
        - start["player_timestamp"]
    ) / 1000

    result = {
        "post_tempo_start_timestamp": (
            start["player_timestamp"]
        ),
        "post_tempo_end_timestamp": (
            end["player_timestamp"]
        ),
        "post_tempo_duration_seconds": (
            duration
        ),
        "post_tempo_start_seconds_after_death": (
            (
                start["player_timestamp"]
                - death_timestamp
            )
            / 1000
        ),
        "post_tempo_end_seconds_after_death": (
            (
                end["player_timestamp"]
                - death_timestamp
            )
            / 1000
        ),
    }

    for key in (
        "gold_diff",
        "cs_diff",
        "xp_diff",
        "level_diff",
    ):
        result[
            f"post_tempo_{key}_change"
        ] = (
            end[key]
            - start[key]
        )

    result[
        "post_tempo_player_gold_gain"
    ] = (
        end["player"]["gold"]
        - start["player"]["gold"]
    )

    result[
        "post_tempo_opponent_gold_gain"
    ] = (
        end["opponent"]["gold"]
        - start["opponent"]["gold"]
    )

    result[
        "post_tempo_player_cs_gain"
    ] = (
        end["player"]["cs"]
        - start["player"]["cs"]
    )

    result[
        "post_tempo_opponent_cs_gain"
    ] = (
        end["opponent"]["cs"]
        - start["opponent"]["cs"]
    )

    result[
        "post_tempo_player_xp_gain"
    ] = (
        end["player"]["xp"]
        - start["player"]["xp"]
    )

    result[
        "post_tempo_opponent_xp_gain"
    ] = (
        end["opponent"]["xp"]
        - start["opponent"]["xp"]
    )

    return result


def _build_post_death_trajectory(
    match_id,
    puuid,
    death_timestamp,
):
    """
    Trajectoire à partir de la première frame APRES la mort.

    On ne l'appelle plus +1/+2/+3 min de façon absolue :
    chaque ligne affiche son vrai temps après la mort.
    """
    first_after = (
        get_relative_snapshot_strictly_after(
            match_id,
            puuid,
            death_timestamp,
        )
    )

    if not first_after:
        return {}

    metrics = {
        "trajectory_anchor_timestamp": (
            first_after[
                "player_timestamp"
            ]
        ),
    }

    anchor_ts = first_after[
        "player_timestamp"
    ]

    # point 0 = première frame après la mort
    snapshots = [
        (
            0,
            first_after,
        )
    ]

    for step in (
        1,
        2,
        3,
    ):
        target = (
            anchor_ts
            + step * 60 * 1000
        )

        post = (
            get_relative_snapshot_after_or_at(
                match_id,
                puuid,
                target,
            )
        )

        if post:
            snapshots.append(
                (
                    step,
                    post,
                )
            )

    for step, post in snapshots:
        prefix = (
            f"trajectory_{step}"
        )

        metrics[
            f"{prefix}_available"
        ] = True

        metrics[
            f"{prefix}_player_timestamp"
        ] = post[
            "player_timestamp"
        ]

        metrics[
            f"{prefix}_seconds_after_death"
        ] = (
            post["player_timestamp"]
            - death_timestamp
        ) / 1000

        for key in (
            "gold_diff",
            "cs_diff",
            "xp_diff",
            "level_diff",
        ):
            metrics[
                f"{prefix}_{key}"
            ] = post[key]

    return metrics


def _find_recovery(
    match_id,
    puuid,
    death_timestamp,
    baseline,
):
    """
    Récupération SOUTENUE.

    Une simple frame qui repasse brièvement au-dessus du niveau
    pré-mort ne suffit plus. Il faut deux frames consécutives
    au-dessus du baseline pour déclarer la ressource récupérée.

    Cela évite par exemple :
        +XP à 22:00
        -XP à 23:00
    d'être considéré comme une vraie récupération.
    """
    recovery = {
        "gold_recovery_seconds": None,
        "cs_recovery_seconds": None,
        "xp_recovery_seconds": None,
        "level_recovery_seconds": None,
    }

    first_after = (
        get_relative_snapshot_strictly_after(
            match_id,
            puuid,
            death_timestamp,
        )
    )

    if not first_after:
        return recovery

    first_ts = first_after[
        "player_timestamp"
    ]

    snapshots = []

    # +1 pour pouvoir confirmer la dernière candidate
    # avec une frame supplémentaire.
    for step in range(
        0,
        RECOVERY_MAX_MINUTES + 2,
    ):
        target = (
            first_ts
            + step * 60 * 1000
        )

        post = (
            get_relative_snapshot_after_or_at(
                match_id,
                puuid,
                target,
            )
        )

        if post:
            snapshots.append(
                post
            )

    keys = {
        "gold_recovery_seconds": "gold_diff",
        "cs_recovery_seconds": "cs_diff",
        "xp_recovery_seconds": "xp_diff",
        "level_recovery_seconds": "level_diff",
    }

    for recovery_key, metric_key in keys.items():
        baseline_value = baseline[
            metric_key
        ]

        for index in range(
            len(snapshots) - 1
        ):
            current = snapshots[
                index
            ]

            next_snapshot = snapshots[
                index + 1
            ]

            if (
                current[metric_key]
                >= baseline_value
                and next_snapshot[
                    metric_key
                ] >= baseline_value
            ):
                recovery[
                    recovery_key
                ] = int(
                    (
                        current[
                            "player_timestamp"
                        ]
                        - death_timestamp
                    )
                    / 1000
                )

                break

    return recovery


# ============================================================
# SINGLE DEATH
# ============================================================

def analyze_single_death(
    match_info,
    death,
    puuid,
):
    match_id = match_info[
        "match_id"
    ]

    death_timestamp = death[
        "timestamp"
    ]

    context = get_match_context(
        match_id,
        puuid,
    )

    if not context:
        return None

    # Dernière frame AVANT la mort : baseline vraie, pas une frame future.
    baseline = (
        get_relative_snapshot_before_or_at(
            match_id,
            puuid,
            death_timestamp,
        )
    )

    if not baseline:
        return None

    impact = (
        _build_bracket_impact(
            match_id,
            puuid,
            death_timestamp,
            baseline,
        )
    )

    if not impact:
        return None

    trajectory = (
        _build_post_death_trajectory(
            match_id,
            puuid,
            death_timestamp,
        )
    )

    post_tempo = (
        _build_post_death_tempo_window(
            match_id,
            puuid,
            death_timestamp,
        )
    )

    event_context = (
        _analyze_event_context(
            match_id,
            puuid,
            death_timestamp,
        )
    )

    trade = _detect_trade(
        match_id,
        puuid,
        death_timestamp,
    )

    recovery = _find_recovery(
        match_id,
        puuid,
        death_timestamp,
        baseline,
    )

    # Score principal = intervalle de frames qui encadre la mort.
    # Les anciens noms *_60 sont conservés pour compatibilité
    # avec les agrégations existantes, mais ils représentent
    # désormais cet impact "bracket", pas +60 s après la mort.
    gold_change_60 = (
        impact[
            "impact_gold_diff_change"
        ]
    )

    cs_change_60 = (
        impact[
            "impact_cs_diff_change"
        ]
    )

    xp_change_60 = (
        impact[
            "impact_xp_diff_change"
        ]
    )

    my_team_id = context[
        "my_team_id"
    ]

    return {
        "match_id": match_id,
        "game_creation": match_info.get(
            "game_creation"
        ),
        "champion": match_info[
            "champion"
        ],
        "win": match_info[
            "win"
        ],

        "timestamp": death_timestamp,
        "minute": (
            death_timestamp
            / 60_000
        ),

        "killer_id": death[
            "killer_id"
        ],
        "killer_champion": death[
            "killer_champion"
        ],
        "killer_position": death[
            "killer_position"
        ],

        "killed_by_enemy_jungler": (
            death[
                "killed_by_enemy_jungler"
            ]
        ),

        "bounty": death.get(
            "bounty"
        ),
        "shutdown_bounty": death.get(
            "shutdown_bounty"
        ),
        "kill_streak_length": death.get(
            "kill_streak_length"
        ),

        "x": death["x"],
        "y": death["y"],

        "death_zone_approx": (
            _zone_approx(
                death["x"],
                death["y"],
                my_team_id,
            )
        ),

        # Baseline réelle.
        "baseline_player_timestamp": (
            baseline[
                "player_timestamp"
            ]
        ),
        "baseline_opponent_timestamp": (
            baseline[
                "opponent_timestamp"
            ]
        ),

        "seconds_from_baseline_to_death": (
            (
                death_timestamp
                - baseline[
                    "player_timestamp"
                ]
            )
            / 1000
        ),

        "pre_gold_diff": baseline[
            "gold_diff"
        ],
        "pre_cs_diff": baseline[
            "cs_diff"
        ],
        "pre_xp_diff": baseline[
            "xp_diff"
        ],
        "pre_level_diff": baseline[
            "level_diff"
        ],

        "advantage_state_before_death": (
            _death_advantage_state(
                baseline
            )
        ),

        "current_gold_before_death": (
            baseline["player"][
                "current_gold"
            ]
        ),

        # Coût à +1 minute basé sur baseline pré-mort.
        "gold_diff_change_60": (
            gold_change_60
        ),
        "cs_diff_change_60": (
            cs_change_60
        ),
        "xp_diff_change_60": (
            xp_change_60
        ),
        "level_diff_change_60": (
            impact[
                "impact_level_diff_change"
            ]
        ),

        # Episode autour de la mort.
        "gold_cost_60": _positive_cost(
            gold_change_60
        ),
        "cs_cost_60": _positive_cost(
            cs_change_60
        ),
        "xp_cost_60": _positive_cost(
            xp_change_60
        ),

        # Tempo sur une minute complète APRES la première
        # frame observable post-mort.
        "post_tempo_gold_cost": (
            _positive_cost(
                post_tempo[
                    "post_tempo_gold_diff_change"
                ]
            )
            if post_tempo
            else None
        ),

        "post_tempo_cs_cost": (
            _positive_cost(
                post_tempo[
                    "post_tempo_cs_diff_change"
                ]
            )
            if post_tempo
            else None
        ),

        "post_tempo_xp_cost": (
            _positive_cost(
                post_tempo[
                    "post_tempo_xp_diff_change"
                ]
            )
            if post_tempo
            else None
        ),

        **impact,
        **trajectory,
        **(post_tempo or {}),
        **event_context,
        **trade,
        **recovery,
    }


# ============================================================
# DATASET
# ============================================================

def build_death_cost_dataset(
    puuid,
    position="JUNGLE",
    queue_id=420,
):
    matches = get_role_match_ids(
        puuid,
        position=position,
        queue_id=queue_id,
    )

    dataset = []

    for match_info in matches:
        deaths = get_player_death_events(
            match_info[
                "match_id"
            ],
            puuid,
        )

        for death in deaths:
            analyzed = analyze_single_death(
                match_info,
                death,
                puuid,
            )

            if analyzed is not None:
                dataset.append(
                    analyzed
                )

    _attach_personal_cost_scores(
        dataset
    )

    _attach_death_chains(
        dataset
    )

    return dataset


# ============================================================
# COST SCORE
# ============================================================

def _attach_personal_cost_scores(
    dataset,
):
    """
    V11 - SCORE HISTORICAL-ONLY.

    Chaque mort est comparée UNIQUEMENT aux morts provenant de games
    antérieures.

    Une game entière est scorée avec la même référence historique,
    puis ses morts sont ajoutées à la référence seulement après.

    Cela évite :
    - qu'une mort participe à son propre percentile ;
    - qu'une autre mort de la même game influence son score ;
    - que des games FUTURES influencent un score utilisé dans
      le walk-forward chronologique.

    Les premiers matchs servent de warm-up jusqu'à disposer de
    MIN_HISTORICAL_DEATH_REFERENCE morts antérieures.
    """
    if not dataset:
        return

    by_match = defaultdict(
        list
    )

    match_creation = {}

    for row in dataset:
        match_id = row[
            "match_id"
        ]

        by_match[
            match_id
        ].append(
            row
        )

        creation = row.get(
            "game_creation"
        )

        match_creation[
            match_id
        ] = (
            creation
            if creation is not None
            else 0
        )

    ordered_match_ids = sorted(
        by_match,
        key=lambda match_id: (
            match_creation[
                match_id
            ],
            match_id,
        ),
    )

    historical_rows = []

    episode_keys = {
        "gold": "gold_cost_60",
        "cs": "cs_cost_60",
        "xp": "xp_cost_60",
    }

    post_keys = {
        "gold": "post_tempo_gold_cost",
        "cs": "post_tempo_cs_cost",
        "xp": "post_tempo_xp_cost",
    }

    def build_distribution(
        key,
    ):
        return [
            row[key]
            for row in historical_rows
            if row.get(
                key
            ) is not None
        ]

    def attach_dimension(
        row,
        resource_keys,
        prefix,
    ):
        ranks = []

        for resource, key in resource_keys.items():
            values = build_distribution(
                key
            )

            rank_key = (
                f"{prefix}_{resource}_percentile"
            )

            value = row.get(
                key
            )

            if (
                value is None
                or len(
                    values
                )
                < MIN_HISTORICAL_DEATH_REFERENCE
            ):
                row[
                    rank_key
                ] = None

                continue

            rank = percentile_rank(
                values,
                value,
            )

            row[
                rank_key
            ] = rank

            ranks.append(
                rank
            )

        row[
            f"{prefix}_score"
        ] = (
            mean(
                ranks
            )
            if ranks
            else None
        )

    for match_id in ordered_match_ids:
        match_rows = sorted(
            by_match[
                match_id
            ],
            key=lambda row:
                row[
                    "timestamp"
                ],
        )

        reference_size = len(
            historical_rows
        )

        for row in match_rows:
            row[
                "score_reference_size"
            ] = reference_size

            row[
                "score_reference_mode"
            ] = "HISTORICAL_ONLY"

            attach_dimension(
                row,
                episode_keys,
                "episode",
            )

            attach_dimension(
                row,
                post_keys,
                "post_tempo",
            )

            episode_score = row.get(
                "episode_score"
            )

            post_score = row.get(
                "post_tempo_score"
            )

            available = [
                value
                for value in (
                    episode_score,
                    post_score,
                )
                if value is not None
            ]

            severity = (
                max(
                    available
                )
                if available
                else None
            )

            row[
                "death_severity_score"
            ] = severity

            row[
                "resource_cost_score"
            ] = severity

            if severity is None:
                label = "WARMUP"
            elif severity < 25:
                label = "FAIBLE"
            elif severity < 50:
                label = "MODÉRÉ"
            elif severity < 75:
                label = "ÉLEVÉ"
            else:
                label = "TRÈS ÉLEVÉ"

            row[
                "resource_cost_label"
            ] = label

            # Compatibilité anciennes clés.
            row[
                "gold_cost_percentile"
            ] = row.get(
                "episode_gold_percentile"
            )

            row[
                "cs_cost_percentile"
            ] = row.get(
                "episode_cs_percentile"
            )

            row[
                "xp_cost_percentile"
            ] = row.get(
                "episode_xp_percentile"
            )

            historical_gold = (
                build_distribution(
                    "gold_cost_60"
                )
            )

            historical_cs = (
                build_distribution(
                    "cs_cost_60"
                )
            )

            historical_xp = (
                build_distribution(
                    "xp_cost_60"
                )
            )

            median_gold = (
                median(
                    historical_gold
                )
                if historical_gold
                else 0
            )

            median_cs = (
                median(
                    historical_cs
                )
                if historical_cs
                else 0
            )

            median_xp = (
                median(
                    historical_xp
                )
                if historical_xp
                else 0
            )

            row[
                "gold_cost_ratio_vs_median"
            ] = (
                row[
                    "gold_cost_60"
                ]
                / median_gold
                if (
                    median_gold > 0
                    and row.get(
                        "gold_cost_60"
                    )
                    is not None
                )
                else None
            )

            row[
                "cs_cost_ratio_vs_median"
            ] = (
                row[
                    "cs_cost_60"
                ]
                / median_cs
                if (
                    median_cs > 0
                    and row.get(
                        "cs_cost_60"
                    )
                    is not None
                )
                else None
            )

            row[
                "xp_cost_ratio_vs_median"
            ] = (
                row[
                    "xp_cost_60"
                ]
                / median_xp
                if (
                    median_xp > 0
                    and row.get(
                        "xp_cost_60"
                    )
                    is not None
                )
                else None
            )

        # Très important : même game jamais utilisée pour se scorer.
        historical_rows.extend(
            match_rows
        )


# ============================================================
# DEATH CHAINS / SPIRALS
# ============================================================

def _attach_death_chains(
    dataset,
):
    """
    Deux notions distinctes :

    DEATH CHAIN
        morts rapprochées sans récupération XP complète.

    DEATH SPIRAL
        chaîne suffisamment grave selon :
        - nombre de morts,
        - coût moyen,
        - pire mort.

    Cela évite que toute simple paire de morts devienne
    automatiquement une "spirale".
    """
    by_match = defaultdict(
        list
    )

    for row in dataset:
        by_match[
            row["match_id"]
        ].append(
            row
        )

    for match_rows in by_match.values():
        match_rows.sort(
            key=lambda row:
                row["timestamp"]
        )

        previous = None
        chain_id = 0

        for row in match_rows:
            if previous is None:
                chain_id += 1

                row[
                    "death_chain_start"
                ] = True

                row[
                    "seconds_since_previous_death"
                ] = None

            else:
                gap = (
                    row["timestamp"]
                    - previous["timestamp"]
                ) / 1000

                row[
                    "seconds_since_previous_death"
                ] = gap

                # On juge la récupération AU MOMENT de la mort
                # suivante. Une récupération transitoire entre les
                # deux ne suffit donc plus.
                recovered_resources = 0

                if (
                    row["pre_gold_diff"]
                    >= previous[
                        "pre_gold_diff"
                    ]
                ):
                    recovered_resources += 1

                if (
                    row["pre_cs_diff"]
                    >= previous[
                        "pre_cs_diff"
                    ]
                ):
                    recovered_resources += 1

                if (
                    row["pre_xp_diff"]
                    >= previous[
                        "pre_xp_diff"
                    ]
                ):
                    recovered_resources += 1

                recovered_before_next = (
                    recovered_resources >= 2
                )

                if (
                    gap > DEATH_CHAIN_MAX_SECONDS
                    or recovered_before_next
                ):
                    chain_id += 1

                    row[
                        "death_chain_start"
                    ] = True

                else:
                    row[
                        "death_chain_start"
                    ] = False

            row[
                "death_chain_id"
            ] = chain_id

            previous = row

        chains = defaultdict(
            list
        )

        for row in match_rows:
            chains[
                row["death_chain_id"]
            ].append(
                row
            )

        for chain_rows in chains.values():
            size = len(
                chain_rows
            )

            valid_scores = [
                row[
                    "resource_cost_score"
                ]
                for row in chain_rows
                if row[
                    "resource_cost_score"
                ] is not None
            ]

            average_cost = (
                mean(valid_scores)
                if valid_scores
                else 0
            )

            worst_cost = (
                max(valid_scores)
                if valid_scores
                else 0
            )

            size_score = min(
                100,
                max(
                    0,
                    (size - 1) * 35,
                ),
            )

            if size < 2:
                spiral_score = 0
            else:
                spiral_score = (
                    0.45 * average_cost
                    + 0.30 * worst_cost
                    + 0.25 * size_score
                )

            is_spiral = (
                size >= 2
                and spiral_score >= 60
            )

            for row in chain_rows:
                row[
                    "death_chain_size"
                ] = size

                row[
                    "death_chain"
                ] = (
                    size >= 2
                )

                row[
                    "death_spiral_score"
                ] = spiral_score

                row[
                    "death_spiral"
                ] = is_spiral


# ============================================================
# SUMMARY HELPERS
# ============================================================

def _values(
    rows,
    key,
):
    return [
        row[key]
        for row in rows
        if row.get(key) is not None
    ]


def _safe_median(
    values,
):
    return (
        median(values)
        if values
        else None
    )


def _safe_mean(
    values,
):
    return (
        mean(values)
        if values
        else None
    )


# ============================================================
# DEATH-LEVEL SUMMARY
# ============================================================

def summarize_death_costs(
    dataset,
    champion=None,
    win=None,
):
    rows = [
        row
        for row in dataset
        if (
            champion is None
            or row["champion"]
            == champion
        )
        and (
            win is None
            or row["win"] == win
        )
    ]

    if not rows:
        return None

    scored_rows = [
        row
        for row in rows
        if row.get(
            "resource_cost_score"
        ) is not None
    ]

    costly = [
        row
        for row in scored_rows
        if row[
            "resource_cost_score"
        ] >= 75
    ]

    spiral_rows = [
        row
        for row in rows
        if row[
            "death_spiral"
        ]
    ]

    ahead_rows = [
        row
        for row in rows
        if row[
            "advantage_state_before_death"
        ] == "EN_AVANCE"
    ]

    return {
        "deaths": len(rows),

        "median_gold_cost_60": _safe_median(
            _values(
                rows,
                "gold_cost_60",
            )
        ),

        "median_cs_cost_60": _safe_median(
            _values(
                rows,
                "cs_cost_60",
            )
        ),

        "median_xp_cost_60": _safe_median(
            _values(
                rows,
                "xp_cost_60",
            )
        ),

        "scored_deaths": len(
            scored_rows
        ),

        "very_costly_percent": (
            len(costly)
            / len(
                scored_rows
            )
            * 100
            if scored_rows
            else 0
        ),

        "enemy_objective_after_percent": (
            sum(
                1
                for row in rows
                if row[
                    "enemy_objectives_after"
                ] > 0
            )
            / len(rows)
            * 100
        ),

        "killed_by_enemy_jungler_percent": (
            sum(
                1
                for row in rows
                if row[
                    "killed_by_enemy_jungler"
                ]
            )
            / len(rows)
            * 100
        ),

        "trade_percent": (
            sum(
                1
                for row in rows
                if row["trade"]
            )
            / len(rows)
            * 100
        ),

        "death_spiral_percent": (
            len(spiral_rows)
            / len(rows)
            * 100
        ),

        "death_chain_percent": (
            sum(
                1
                for row in rows
                if row.get(
                    "death_chain",
                    False,
                )
            )
            / len(rows)
            * 100
        ),

        "death_while_ahead_percent": (
            len(ahead_rows)
            / len(rows)
            * 100
        ),

        "median_unspent_gold_before_death": (
            _safe_median(
                _values(
                    rows,
                    "current_gold_before_death",
                )
            )
        ),

        "median_gold_recovery_seconds": (
            _safe_median(
                _values(
                    rows,
                    "gold_recovery_seconds",
                )
            )
        ),

        "median_cs_recovery_seconds": (
            _safe_median(
                _values(
                    rows,
                    "cs_recovery_seconds",
                )
            )
        ),

        "median_xp_recovery_seconds": (
            _safe_median(
                _values(
                    rows,
                    "xp_recovery_seconds",
                )
            )
        ),
    }


# ============================================================
# GAME-LEVEL AGGREGATION
# ============================================================

def build_game_death_summary_dataset(
    death_dataset,
    puuid=None,
    position="JUNGLE",
    queue_id=420,
):
    """
    Une ligne = une game.

    V9 :
    - inclut les games à 0 mort ;
    - une game = une observation ;
    - ajoute coûts moyens PAR MORT ;
    - ajoute métriques normalisées /10 min ;
    - déduplique objectifs/tours entre fenêtres de morts chevauchantes.
    """
    grouped = defaultdict(list)

    for row in death_dataset:
        grouped[row["match_id"]].append(row)

    match_infos = {}

    if puuid is not None:
        for match in get_role_match_ids(
            puuid,
            position=position,
            queue_id=queue_id,
        ):
            match_infos[match["match_id"]] = match
    else:
        for match_id, rows in grouped.items():
            match_infos[match_id] = {
                "match_id": match_id,
                "champion": rows[0]["champion"],
                "win": rows[0]["win"],
                "game_creation": None,
                "game_duration": None,
            }

    result = []

    for match_id, match_info in match_infos.items():
        rows = sorted(
            grouped.get(match_id, []),
            key=lambda row: row["timestamp"],
        )

        deaths = len(rows)

        duration_seconds = (
            match_info.get("game_duration")
            or 0
        )

        duration_minutes = (
            duration_seconds / 60
            if duration_seconds > 0
            else None
        )

        per10 = (
            10 / duration_minutes
            if duration_minutes
            else None
        )

        if rows:
            severe_rows = [
                row
                for row in rows
                if (
                    row.get("resource_cost_score")
                    is not None
                    and row["resource_cost_score"] >= 75
                )
            ]

            chain_ids = {
                row["death_chain_id"]
                for row in rows
                if row.get("death_chain", False)
            }

            spiral_ids = {
                row["death_chain_id"]
                for row in rows
                if row.get("death_spiral", False)
            }

            severity_values = _values(
                rows,
                "resource_cost_score",
            )
            episode_values = _values(
                rows,
                "episode_score",
            )
            post_tempo_values = _values(
                rows,
                "post_tempo_score",
            )
            unspent_values = _values(
                rows,
                "current_gold_before_death",
            )

            gold_costs = _values(
                rows,
                "gold_cost_60",
            )
            cs_costs = _values(
                rows,
                "cs_cost_60",
            )
            xp_costs = _values(
                rows,
                "xp_cost_60",
            )

            spiral_scores = _values(
                rows,
                "death_spiral_score",
            )

            unique_enemy_objectives = set()
            unique_enemy_towers = set()

            for row in rows:
                unique_enemy_objectives.update(
                    row.get(
                        "enemy_objective_event_keys_after",
                        [],
                    )
                )
                unique_enemy_towers.update(
                    row.get(
                        "enemy_tower_event_keys_after",
                        [],
                    )
                )

            total_gold = sum(gold_costs)
            total_cs = sum(cs_costs)
            total_xp = sum(xp_costs)

            severe_count = len(severe_rows)

            spiral_deaths = sum(
                1
                for row in rows
                if row.get(
                    "death_spiral",
                    False,
                )
            )

            game_row = {
                "match_id": match_id,
                "game_creation": match_info.get(
                    "game_creation"
                ),
                "game_duration": duration_seconds,
                "game_duration_minutes": duration_minutes,
                "champion": match_info.get("champion"),
                "win": bool(match_info.get("win")),

                "deaths": deaths,
                "has_death": 1,
                "deaths_per_10": (
                    deaths * per10
                    if per10 is not None
                    else None
                ),

                "median_gold_cost_60": _safe_median(
                    gold_costs
                ),
                "median_cs_cost_60": _safe_median(
                    cs_costs
                ),
                "median_xp_cost_60": _safe_median(
                    xp_costs
                ),

                "mean_gold_cost_per_death": _safe_mean(
                    gold_costs
                ),
                "mean_cs_cost_per_death": _safe_mean(
                    cs_costs
                ),
                "mean_xp_cost_per_death": _safe_mean(
                    xp_costs
                ),

                "total_gold_cost_60": total_gold,
                "total_cs_cost_60": total_cs,
                "total_xp_cost_60": total_xp,

                "gold_cost_per_10": (
                    total_gold * per10
                    if per10 is not None
                    else None
                ),
                "cs_cost_per_10": (
                    total_cs * per10
                    if per10 is not None
                    else None
                ),
                "xp_cost_per_10": (
                    total_xp * per10
                    if per10 is not None
                    else None
                ),

                "mean_death_severity": _safe_mean(
                    severity_values
                ),
                "median_death_severity": _safe_median(
                    severity_values
                ),
                "worst_death_score": (
                    max(severity_values)
                    if severity_values
                    else 0
                ),

                "mean_episode_score": _safe_mean(
                    episode_values
                ),
                "mean_post_tempo_score": _safe_mean(
                    post_tempo_values
                ),

                "very_costly_deaths": severe_count,
                "severe_death_rate": (
                    severe_count / deaths
                ),
                "severe_deaths_per_10": (
                    severe_count * per10
                    if per10 is not None
                    else None
                ),

                "death_chain_chains": len(chain_ids),
                "death_spiral_chains": len(spiral_ids),
                "has_death_spiral": (
                    1 if spiral_ids else 0
                ),
                "max_death_spiral_score": (
                    max(spiral_scores)
                    if spiral_scores
                    else 0
                ),
                "death_spiral_deaths": spiral_deaths,
                "death_spiral_deaths_per_10": (
                    spiral_deaths * per10
                    if per10 is not None
                    else None
                ),

                # Ancien total avec chevauchement, conservé seulement
                # pour contrôle interne.
                "enemy_objectives_after_deaths_overlapping": sum(
                    row["enemy_objectives_after"]
                    for row in rows
                ),
                "enemy_towers_after_deaths_overlapping": sum(
                    row["enemy_towers_after"]
                    for row in rows
                ),

                # Valeurs propres V9.
                "enemy_objectives_after_deaths": len(
                    unique_enemy_objectives
                ),
                "enemy_towers_after_deaths": len(
                    unique_enemy_towers
                ),
                "enemy_objectives_after_deaths_per_10": (
                    len(unique_enemy_objectives) * per10
                    if per10 is not None
                    else None
                ),
                "enemy_towers_after_deaths_per_10": (
                    len(unique_enemy_towers) * per10
                    if per10 is not None
                    else None
                ),

                "deaths_while_ahead": sum(
                    1
                    for row in rows
                    if row[
                        "advantage_state_before_death"
                    ] == "EN_AVANCE"
                ),

                "median_unspent_gold_before_death": (
                    _safe_median(
                        unspent_values
                    )
                ),
            }

        else:
            game_row = {
                "match_id": match_id,
                "game_creation": match_info.get(
                    "game_creation"
                ),
                "game_duration": duration_seconds,
                "game_duration_minutes": duration_minutes,
                "champion": match_info.get("champion"),
                "win": bool(match_info.get("win")),

                "deaths": 0,
                "has_death": 0,
                "deaths_per_10": 0,

                "median_gold_cost_60": None,
                "median_cs_cost_60": None,
                "median_xp_cost_60": None,

                "mean_gold_cost_per_death": None,
                "mean_cs_cost_per_death": None,
                "mean_xp_cost_per_death": None,

                "total_gold_cost_60": 0,
                "total_cs_cost_60": 0,
                "total_xp_cost_60": 0,

                "gold_cost_per_10": 0,
                "cs_cost_per_10": 0,
                "xp_cost_per_10": 0,

                "mean_death_severity": 0,
                "median_death_severity": 0,
                "worst_death_score": 0,
                "mean_episode_score": 0,
                "mean_post_tempo_score": 0,

                "very_costly_deaths": 0,
                "severe_death_rate": 0,
                "severe_deaths_per_10": 0,

                "death_chain_chains": 0,
                "death_spiral_chains": 0,
                "has_death_spiral": 0,
                "max_death_spiral_score": 0,
                "death_spiral_deaths": 0,
                "death_spiral_deaths_per_10": 0,

                "enemy_objectives_after_deaths_overlapping": 0,
                "enemy_towers_after_deaths_overlapping": 0,

                "enemy_objectives_after_deaths": 0,
                "enemy_towers_after_deaths": 0,
                "enemy_objectives_after_deaths_per_10": 0,
                "enemy_towers_after_deaths_per_10": 0,

                "deaths_while_ahead": 0,
                "median_unspent_gold_before_death": None,
            }

        result.append(game_row)

    return sorted(
        result,
        key=lambda row: (
            row.get("game_creation")
            or 0
        ),
    )


def summarize_game_death_profiles(
    game_dataset,
    win=None,
):
    rows = [
        row
        for row in game_dataset
        if (
            win is None
            or row["win"] == win
        )
    ]

    if not rows:
        return None

    games_with_death = sum(
        1
        for row in rows
        if row[
            "deaths"
        ] > 0
    )

    return {
        "games": len(rows),

        "games_with_death": (
            games_with_death
        ),

        "zero_death_games": (
            len(rows)
            - games_with_death
        ),

        "median_deaths_per_game": (
            _safe_median(
                _values(
                    rows,
                    "deaths",
                )
            )
        ),

        "median_game_gold_cost": (
            _safe_median(
                _values(
                    rows,
                    "total_gold_cost_60",
                )
            )
        ),

        "median_game_cs_cost": (
            _safe_median(
                _values(
                    rows,
                    "total_cs_cost_60",
                )
            )
        ),

        "median_game_xp_cost": (
            _safe_median(
                _values(
                    rows,
                    "total_xp_cost_60",
                )
            )
        ),

        "median_worst_death_score": (
            _safe_median(
                _values(
                    rows,
                    "worst_death_score",
                )
            )
        ),

        "median_very_costly_deaths": (
            _safe_median(
                _values(
                    rows,
                    "very_costly_deaths",
                )
            )
        ),

        "games_with_death_spiral_percent": (
            sum(
                1
                for row in rows
                if row[
                    "has_death_spiral"
                ] == 1
            )
            / len(rows)
            * 100
        ),

        "median_max_death_spiral_score": (
            _safe_median(
                _values(
                    rows,
                    "max_death_spiral_score",
                )
            )
        ),

        "median_deaths_while_ahead": (
            _safe_median(
                _values(
                    rows,
                    "deaths_while_ahead",
                )
            )
        ),
    }


# ============================================================
# MATCH
# ============================================================

def get_match_death_costs(
    dataset,
    match_id,
):
    return sorted(
        [
            row
            for row in dataset
            if row[
                "match_id"
            ] == match_id
        ],
        key=lambda row:
            row[
                "timestamp"
            ],
    )


# ============================================================
# RENDERING
# ============================================================

def _format_time(
    timestamp,
):
    seconds = int(
        timestamp / 1000
    )

    return (
        f"{seconds // 60:02d}:"
        f"{seconds % 60:02d}"
    )


def _format_recovery(
    seconds,
):
    if seconds is None:
        return (
            f"> {RECOVERY_MAX_MINUTES} min "
            "ou non récupéré"
        )

    return (
        f"{seconds / 60:.1f} min"
    )


def render_death_cost_summary(
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
        return "\n".join(
            lines
        )

    lines.extend([
        "",
        f"Morts analysées : {summary['deaths']}",
        f"Morts avec score historique exploitable : {summary['scored_deaths']}",
        "",
        "Coût médian de l'ÉPISODE encadrant la mort (~1 min, non causal) :",
        f"  Gold relatif : {summary['median_gold_cost_60']:.0f}",
        f"  CS relatifs  : {summary['median_cs_cost_60']:.1f}",
        f"  XP relative  : {summary['median_xp_cost_60']:.0f}",
        "",
        f"Morts à sévérité >= 75/100 : {summary['very_costly_percent']:.1f}%",
        f"Objectif adverse dans les {OBJECTIVE_WINDOW_SECONDS}s après : {summary['enemy_objective_after_percent']:.1f}%",
        f"Tué par le jungler adverse : {summary['killed_by_enemy_jungler_percent']:.1f}%",
        f"Trade détecté : {summary['trade_percent']:.1f}%",
        f"Morts appartenant à une death chain : {summary['death_chain_percent']:.1f}%",
        f"Morts appartenant à une death spiral sévère : {summary['death_spiral_percent']:.1f}%",
        f"Morts commises en étant en avance : {summary['death_while_ahead_percent']:.1f}%",
        f"Gold non dépensé médian avant mort : {summary['median_unspent_gold_before_death']:.0f}",
        "",
        "Temps médian pour retrouver l'écart pré-mort :",
        f"  Gold : {_format_recovery(summary['median_gold_recovery_seconds'])}",
        f"  CS   : {_format_recovery(summary['median_cs_recovery_seconds'])}",
        f"  XP   : {_format_recovery(summary['median_xp_recovery_seconds'])}",
    ])

    return "\n".join(
        lines
    )


def render_game_level_summary(
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
        return "\n".join(
            lines
        )

    lines.extend([
        "",
        f"Games analysées : {summary['games']}",
        f"Games avec >= 1 mort : {summary['games_with_death']}",
        f"Games à 0 mort : {summary['zero_death_games']}",
        f"Morts médianes / game : {summary['median_deaths_per_game']:.1f}",
        "",
        "Coût cumulé médian des morts par game :",
        f"  Gold : {summary['median_game_gold_cost']:.0f}",
        f"  CS   : {summary['median_game_cs_cost']:.1f}",
        f"  XP   : {summary['median_game_xp_cost']:.0f}",
        "",
        f"Pire mort médiane : {summary['median_worst_death_score']:.0f}/100",
        f"Morts à sévérité >= 75/100 médianes / game : {summary['median_very_costly_deaths']:.1f}",
        f"Games avec death spiral SÉVÈRE : {summary['games_with_death_spiral_percent']:.1f}%",
        f"Death Spiral Score max médian : {summary['median_max_death_spiral_score']:.0f}/100",
        f"Morts en étant en avance / game : {summary['median_deaths_while_ahead']:.1f}",
    ])

    return "\n".join(
        lines
    )


def render_match_death_costs(
    rows,
):
    lines = [
        "================================",
        "DEATH ANALYZER APPROFONDI - MATCH",
        "================================",
    ]

    if not rows:
        lines.extend([
            "",
            "Aucune mort exploitable.",
        ])

        return "\n".join(
            lines
        )

    for index, row in enumerate(
        rows,
        start=1,
    ):
        lines.extend([
            "",
            f"MORT #{index} - {_format_time(row['timestamp'])}",
            f"Killer : {row['killer_champion'] or 'inconnu'}",
            f"État à la dernière frame pré-mort : {row['advantage_state_before_death']}",
            f"Zone approx. : {row['death_zone_approx']}",
            f"Gold non dépensé à la dernière frame pré-mort : {row['current_gold_before_death']:.0f}",
        ])

        lines.append(
            f"Référence score : "
            f"{row.get('score_reference_size', 0)} morts historiques antérieures"
        )

        if row[
            "killed_by_enemy_jungler"
        ]:
            lines.append(
                "Contexte : tué par le jungler adverse"
            )

        if row["trade"]:
            trade_text = (
                "OUI - jungler adverse tué"
                if row[
                    "enemy_jungle_trade"
                ]
                else "OUI"
            )

            lines.append(
                f"Trade : {trade_text}"
            )

        if row.get(
            "bounty"
        ) is not None:
            lines.append(
                f"Bounty événement Riot : {row['bounty']}"
            )

        if row.get(
            "shutdown_bounty"
        ) is not None:
            lines.append(
                f"Shutdown bounty Riot : {row['shutdown_bounty']}"
            )

        lines.extend([
            "",
            "Intervalle principal encadrant la mort :",
            f"  Mort : {_format_time(row['timestamp'])}",
            f"  Frame avant : {_format_time(row['baseline_player_timestamp'])}",
            f"  Frame après : {_format_time(row['impact_after_player_timestamp'])}",
            f"  Durée intervalle : {row['impact_interval_seconds']:.0f}s",
            f"  Avant mort dans l'intervalle : {row['impact_seconds_before_death']:.0f}s",
            f"  Après mort dans l'intervalle : {row['impact_seconds_after_death']:.0f}s",
            "",
            "Impact relatif sur cet intervalle :",
            f"  Gold : {row['impact_gold_diff_change']:+.0f}",
            f"  CS   : {row['impact_cs_diff_change']:+.1f}",
            f"  XP   : {row['impact_xp_diff_change']:+.0f}",
            f"  Niv. : {row['impact_level_diff_change']:+.0f}",
            f"  Production Gold : toi {row['impact_player_gold_gain']:.0f} | JGL {row['impact_opponent_gold_gain']:.0f}",
            f"  Production CS   : toi {row['impact_player_cs_gain']:.1f} | JGL {row['impact_opponent_cs_gain']:.1f}",
            f"  Production XP   : toi {row['impact_player_xp_gain']:.0f} | JGL {row['impact_opponent_xp_gain']:.0f}",
            "",
            "Tempo sur la première minute complète observable après la mort :",
        ])

        if row.get(
            "post_tempo_start_timestamp"
        ) is not None:
            lines.extend([
                f"  Début : {_format_time(row['post_tempo_start_timestamp'])} "
                f"(+{row['post_tempo_start_seconds_after_death']:.0f}s)",
                f"  Fin   : {_format_time(row['post_tempo_end_timestamp'])} "
                f"(+{row['post_tempo_end_seconds_after_death']:.0f}s)",
                f"  Gold relatif : {row['post_tempo_gold_diff_change']:+.0f}",
                f"  CS relatifs  : {row['post_tempo_cs_diff_change']:+.1f}",
                f"  XP relative  : {row['post_tempo_xp_diff_change']:+.0f}",
                f"  Production Gold : toi {row['post_tempo_player_gold_gain']:.0f} | "
                f"JGL {row['post_tempo_opponent_gold_gain']:.0f}",
                f"  Production CS   : toi {row['post_tempo_player_cs_gain']:.1f} | "
                f"JGL {row['post_tempo_opponent_cs_gain']:.1f}",
                f"  Production XP   : toi {row['post_tempo_player_xp_gain']:.0f} | "
                f"JGL {row['post_tempo_opponent_xp_gain']:.0f}",
            ])

        lines.extend([
            "",
            "Trajectoire après la mort (timestamps réels) :",
        ])

        for step in (0, 1, 2, 3):
            prefix = f"trajectory_{step}"

            if not row.get(
                f"{prefix}_available"
            ):
                continue

            lines.append(
                f"  {_format_time(row[f'{prefix}_player_timestamp'])} "
                f"(+{row[f'{prefix}_seconds_after_death']:.0f}s) | "
                f"Gold {row[f'{prefix}_gold_diff']:+.0f} | "
                f"CS {row[f'{prefix}_cs_diff']:+.1f} | "
                f"XP {row[f'{prefix}_xp_diff']:+.0f} | "
                f"Niv {row[f'{prefix}_level_diff']:+.0f}"
            )

        score = row.get(
            "resource_cost_score"
        )

        if score is not None:
            lines.extend([
                "",
                f"Score épisode autour de la mort : "
                f"{row['episode_score']:.0f}/100",
                f"Score tempo post-mort comparable : "
                f"{row['post_tempo_score']:.0f}/100"
                if row.get("post_tempo_score") is not None
                else "Score tempo post-mort comparable : indisponible",
                f"Sévérité retenue : {score:.0f}/100 "
                f"({row['resource_cost_label']})",
                f"Percentiles épisode : Gold "
                f"{row['episode_gold_percentile']:.0f}e | "
                f"CS {row['episode_cs_percentile']:.0f}e | "
                f"XP {row['episode_xp_percentile']:.0f}e",
            ])

            if row.get(
                "post_tempo_score"
            ) is not None:
                lines.append(
                    f"Percentiles tempo post-mort : Gold "
                    f"{row['post_tempo_gold_percentile']:.0f}e | "
                    f"CS {row['post_tempo_cs_percentile']:.0f}e | "
                    f"XP {row['post_tempo_xp_percentile']:.0f}e"
                )

        lines.extend([
            "",
            f"Objectif adverse dans {OBJECTIVE_WINDOW_SECONDS}s après : {row['enemy_objectives_after']}",
            f"Objectif allié dans {OBJECTIVE_WINDOW_SECONDS}s après : {row['ally_objectives_after']}",
            f"Tours perdues dans {OBJECTIVE_WINDOW_SECONDS}s après : {row['enemy_towers_after']}",
            f"Kills du jungler adverse dans {OBJECTIVE_WINDOW_SECONDS}s : {row['enemy_jungle_kills_after']}",
            f"Death chain : {'OUI' if row.get('death_chain', False) else 'NON'}",
            f"Taille chaîne de morts : {row['death_chain_size']}",
            f"Death spiral sévère : {'OUI' if row['death_spiral'] else 'NON'}",
            f"Death Spiral Score : {row['death_spiral_score']:.0f}/100",
            "",
            "Récupération de l'écart pré-mort :",
            f"  Gold : {_format_recovery(row['gold_recovery_seconds'])}",
            f"  CS   : {_format_recovery(row['cs_recovery_seconds'])}",
            f"  XP   : {_format_recovery(row['xp_recovery_seconds'])}",
        ])

    valid = [
        row
        for row in rows
        if row[
            "resource_cost_score"
        ] is not None
    ]

    if valid:
        worst = max(
            valid,
            key=lambda row:
                row[
                    "resource_cost_score"
                ],
        )

        lines.extend([
            "",
            "--------------------------------",
            "MORT LA PLUS COÛTEUSE DU MATCH",
            "--------------------------------",
            f"{_format_time(worst['timestamp'])} | {worst['resource_cost_score']:.0f}/100 | {worst['resource_cost_label']}",
            f"État avant mort : {worst['advantage_state_before_death']}",
            f"Death chain : {'OUI' if worst.get('death_chain', False) else 'NON'}",
            f"Death spiral sévère : {'OUI' if worst['death_spiral'] else 'NON'}",
            f"Death Spiral Score : {worst['death_spiral_score']:.0f}/100",
        ])

    return "\n".join(
        lines
    )
