import hashlib
import math
import random
from statistics import median

from analysis.feature_engine import describe

from analysis.benchmarks import (
    BOOTSTRAP_ITERATIONS,
    cliffs_delta,
    cliff_effect_label,
    bootstrap_effect,
    iqr_overlap_ratio,
    find_best_threshold,
    calculate_reliability,
    reliability_label,
)


PERMUTATION_ITERATIONS = 2000


GAME_DEATH_FEATURE_CONFIG = {
    "deaths": {
        "label": "Morts / game",
        "favorable": "lower",
        "category": "VOLUME",
        "scope": "PERSONNEL",
        "derived": False,
    },
    "deaths_per_10": {
        "label": "Morts / 10 min",
        "favorable": "lower",
        "category": "VOLUME",
        "scope": "PERSONNEL",
        "derived": False,
    },

    "total_gold_cost_60": {
        "label": "Coût Gold cumulé des épisodes de mort",
        "favorable": "lower",
        "category": "COÛT TOTAL",
        "scope": "PERSONNEL",
        "derived": False,
    },
    "total_cs_cost_60": {
        "label": "Coût CS cumulé des épisodes de mort",
        "favorable": "lower",
        "category": "COÛT TOTAL",
        "scope": "PERSONNEL",
        "derived": False,
    },
    "total_xp_cost_60": {
        "label": "Coût XP cumulé des épisodes de mort",
        "favorable": "lower",
        "category": "COÛT TOTAL",
        "scope": "PERSONNEL",
        "derived": False,
    },

    "gold_cost_per_10": {
        "label": "Coût Gold des morts / 10 min",
        "favorable": "lower",
        "category": "COÛT NORMALISÉ",
        "scope": "PERSONNEL",
        "derived": False,
    },
    "cs_cost_per_10": {
        "label": "Coût CS des morts / 10 min",
        "favorable": "lower",
        "category": "COÛT NORMALISÉ",
        "scope": "PERSONNEL",
        "derived": False,
    },
    "xp_cost_per_10": {
        "label": "Coût XP des morts / 10 min",
        "favorable": "lower",
        "category": "COÛT NORMALISÉ",
        "scope": "PERSONNEL",
        "derived": False,
    },

    "mean_gold_cost_per_death": {
        "label": "Coût Gold moyen par mort",
        "favorable": "lower",
        "category": "COÛT PAR MORT",
        "scope": "PERSONNEL",
        "derived": False,
    },
    "mean_cs_cost_per_death": {
        "label": "Coût CS moyen par mort",
        "favorable": "lower",
        "category": "COÛT PAR MORT",
        "scope": "PERSONNEL",
        "derived": False,
    },
    "mean_xp_cost_per_death": {
        "label": "Coût XP moyen par mort",
        "favorable": "lower",
        "category": "COÛT PAR MORT",
        "scope": "PERSONNEL",
        "derived": False,
    },

    "mean_death_severity": {
        "label": "Sévérité moyenne des morts",
        "favorable": "lower",
        "category": "SÉVÉRITÉ",
        "scope": "PERSONNEL",
        "derived": True,
    },
    "worst_death_score": {
        "label": "Pire mort de la game",
        "favorable": "lower",
        "category": "SÉVÉRITÉ",
        "scope": "PERSONNEL",
        "derived": True,
    },
    "very_costly_deaths": {
        "label": "Nombre de morts à sévérité >= 75/100",
        "favorable": "lower",
        "category": "SÉVÉRITÉ",
        "scope": "PERSONNEL",
        "derived": True,
    },
    "severe_death_rate": {
        "label": "Part des morts à sévérité >= 75/100",
        "favorable": "lower",
        "category": "SÉVÉRITÉ",
        "scope": "PERSONNEL",
        "derived": True,
    },
    "severe_deaths_per_10": {
        "label": "Morts à sévérité >=75 / 10 min",
        "favorable": "lower",
        "category": "SÉVÉRITÉ",
        "scope": "PERSONNEL",
        "derived": True,
    },
    "mean_episode_score": {
        "label": "Score épisode moyen",
        "favorable": "lower",
        "category": "TIMING",
        "scope": "PERSONNEL",
        "derived": True,
    },
    "mean_post_tempo_score": {
        "label": "Score tempo post-mort moyen",
        "favorable": "lower",
        "category": "TIMING",
        "scope": "PERSONNEL",
        "derived": True,
    },
    "death_chain_chains": {
        "label": "Death chains / game",
        "favorable": "lower",
        "category": "CHAÎNES",
        "scope": "PERSONNEL",
        "derived": True,
    },
    "has_death_spiral": {
        "label": "Death spiral sévère présente",
        "favorable": "lower",
        "category": "SPIRAL",
        "scope": "PERSONNEL",
        "derived": True,
    },
    "max_death_spiral_score": {
        "label": "Death Spiral Score maximal",
        "favorable": "lower",
        "category": "SPIRAL",
        "scope": "PERSONNEL",
        "derived": True,
    },
    "death_spiral_deaths": {
        "label": "Morts appartenant à une spiral sévère",
        "favorable": "lower",
        "category": "SPIRAL",
        "scope": "PERSONNEL",
        "derived": True,
    },
    "death_spiral_deaths_per_10": {
        "label": "Morts en spiral sévère / 10 min",
        "favorable": "lower",
        "category": "SPIRAL",
        "scope": "PERSONNEL",
        "derived": True,
    },

    "enemy_objectives_after_deaths": {
        "label": "Objectifs adverses uniques après tes morts",
        "favorable": "lower",
        "category": "CONSÉQUENCES",
        "scope": "CONTEXTE",
        "derived": False,
    },
    "enemy_towers_after_deaths": {
        "label": "Tours perdues uniques après tes morts",
        "favorable": "lower",
        "category": "CONSÉQUENCES",
        "scope": "CONTEXTE",
        "derived": False,
    },
    "enemy_objectives_after_deaths_per_10": {
        "label": "Objectifs adverses uniques après morts / 10 min",
        "favorable": "lower",
        "category": "CONSÉQUENCES",
        "scope": "CONTEXTE",
        "derived": False,
    },
    "enemy_towers_after_deaths_per_10": {
        "label": "Tours perdues uniques après morts / 10 min",
        "favorable": "lower",
        "category": "CONSÉQUENCES",
        "scope": "CONTEXTE",
        "derived": False,
    },

    "deaths_while_ahead": {
        "label": "Morts alors que tu étais en avance",
        "favorable": "lower",
        "category": "EXPLORATOIRE",
        "scope": "EXPLORATOIRE",
        "derived": False,
    },
    "median_unspent_gold_before_death": {
        "label": "Gold non dépensé médian avant mort",
        "favorable": "lower",
        "category": "ÉCONOMIE",
        "scope": "EXPLORATOIRE",
        "derived": False,
    },
}


def _stable_seed(*parts):
    payload = "|".join(
        str(part)
        for part in parts
    )
    digest = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()
    return int(
        digest[:8],
        16,
    )


def _feature_rows(
    game_dataset,
    feature,
):
    result = []

    for row in game_dataset:
        value = row.get(feature)

        if value is None:
            continue

        result.append({
            "match_id": row["match_id"],
            "game_creation": (
                row.get("game_creation")
                or 0
            ),
            "win": bool(row["win"]),
            "value": float(value),
        })

    return result


def _predict_win(
    value,
    threshold,
    favorable,
):
    if favorable == "higher":
        return value >= threshold
    return value <= threshold


def cross_validated_balanced_accuracy(
    rows,
    favorable,
    max_folds=5,
):
    wins = [
        row
        for row in rows
        if row["win"]
    ]
    losses = [
        row
        for row in rows
        if not row["win"]
    ]

    folds = min(
        max_folds,
        len(wins),
        len(losses),
    )

    if folds < 3:
        return None

    wins = sorted(
        wins,
        key=lambda row: (
            row["game_creation"],
            row["match_id"],
        ),
    )
    losses = sorted(
        losses,
        key=lambda row: (
            row["game_creation"],
            row["match_id"],
        ),
    )

    assignments = {}

    for group in (
        wins,
        losses,
    ):
        for index, row in enumerate(group):
            assignments[
                row["match_id"]
            ] = index % folds

    correct_wins = 0
    total_wins = 0
    correct_losses = 0
    total_losses = 0
    thresholds = []

    for fold in range(folds):
        train = [
            row
            for row in rows
            if assignments[
                row["match_id"]
            ] != fold
        ]
        test = [
            row
            for row in rows
            if assignments[
                row["match_id"]
            ] == fold
        ]

        train_wins = [
            row["value"]
            for row in train
            if row["win"]
        ]
        train_losses = [
            row["value"]
            for row in train
            if not row["win"]
        ]

        if (
            not train_wins
            or not train_losses
        ):
            continue

        threshold = find_best_threshold(
            train_wins,
            train_losses,
            favorable,
        )["threshold"]

        thresholds.append(threshold)

        for row in test:
            predicted_win = _predict_win(
                row["value"],
                threshold,
                favorable,
            )

            if row["win"]:
                total_wins += 1
                if predicted_win:
                    correct_wins += 1
            else:
                total_losses += 1
                if not predicted_win:
                    correct_losses += 1

    if (
        total_wins == 0
        or total_losses == 0
    ):
        return None

    sensitivity = (
        correct_wins / total_wins
    )
    specificity = (
        correct_losses / total_losses
    )

    return {
        "folds": folds,
        "balanced_accuracy": (
            sensitivity + specificity
        ) / 2,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "median_threshold": (
            median(thresholds)
            if thresholds
            else None
        ),
        "n_test": (
            total_wins + total_losses
        ),
    }


def walk_forward_balanced_accuracy(
    rows,
    favorable,
    initial_fraction=0.50,
    test_blocks=4,
):
    """
    Validation chronologique :
    un seuil n'est appris que sur des games antérieures au bloc testé.
    """
    ordered = sorted(
        rows,
        key=lambda row: (
            row["game_creation"],
            row["match_id"],
        ),
    )

    if len(ordered) < 20:
        return None

    initial_size = max(
        10,
        int(
            len(ordered)
            * initial_fraction
        ),
    )

    if initial_size >= len(ordered) - 4:
        return None

    remaining = (
        len(ordered) - initial_size
    )

    block_size = max(
        1,
        remaining // test_blocks,
    )

    correct_wins = 0
    total_wins = 0
    correct_losses = 0
    total_losses = 0
    thresholds = []
    blocks_used = 0

    start = initial_size

    while start < len(ordered):
        end = min(
            len(ordered),
            start + block_size,
        )

        if (
            len(ordered) - end
            < block_size
        ):
            end = len(ordered)

        train = ordered[:start]
        test = ordered[start:end]

        train_wins = [
            row["value"]
            for row in train
            if row["win"]
        ]
        train_losses = [
            row["value"]
            for row in train
            if not row["win"]
        ]

        if (
            train_wins
            and train_losses
            and test
        ):
            threshold = find_best_threshold(
                train_wins,
                train_losses,
                favorable,
            )["threshold"]

            thresholds.append(threshold)
            blocks_used += 1

            for row in test:
                predicted_win = _predict_win(
                    row["value"],
                    threshold,
                    favorable,
                )

                if row["win"]:
                    total_wins += 1
                    if predicted_win:
                        correct_wins += 1
                else:
                    total_losses += 1
                    if not predicted_win:
                        correct_losses += 1

        start = end

    if (
        total_wins == 0
        or total_losses == 0
    ):
        return None

    sensitivity = (
        correct_wins / total_wins
    )
    specificity = (
        correct_losses / total_losses
    )

    return {
        "blocks": blocks_used,
        "balanced_accuracy": (
            sensitivity + specificity
        ) / 2,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "median_threshold": (
            median(thresholds)
            if thresholds
            else None
        ),
        "n_test": (
            total_wins + total_losses
        ),
    }


def permutation_p_value(
    rows,
    favorable,
    iterations=PERMUTATION_ITERATIONS,
    seed=0,
):
    win_values = [
        row["value"]
        for row in rows
        if row["win"]
    ]
    loss_values = [
        row["value"]
        for row in rows
        if not row["win"]
    ]

    if (
        len(win_values) < 5
        or len(loss_values) < 5
    ):
        return None

    observed = cliffs_delta(
        win_values,
        loss_values,
    )

    observed_aligned = (
        observed
        if favorable == "higher"
        else -observed
    )

    if observed_aligned <= 0:
        return 1.0

    values = [
        row["value"]
        for row in rows
    ]

    n_wins = len(win_values)

    rng = random.Random(seed)

    count = 0

    for _ in range(iterations):
        shuffled = list(values)
        rng.shuffle(shuffled)

        perm_wins = shuffled[:n_wins]
        perm_losses = shuffled[n_wins:]

        delta = cliffs_delta(
            perm_wins,
            perm_losses,
        )

        aligned = (
            delta
            if favorable == "higher"
            else -delta
        )

        if aligned >= observed_aligned:
            count += 1

    return (
        count + 1
    ) / (
        iterations + 1
    )


def _apply_bh_fdr(
    benchmarks,
):
    valid = [
        benchmark
        for benchmark in benchmarks
        if (
            benchmark.get("status") == "OK"
            and benchmark.get(
                "permutation_p"
            ) is not None
        )
    ]

    if not valid:
        return

    ordered = sorted(
        valid,
        key=lambda row:
            row["permutation_p"],
    )

    m = len(ordered)
    previous_q = 1.0

    for index in range(
        m - 1,
        -1,
        -1,
    ):
        rank = index + 1
        raw_q = (
            ordered[index][
                "permutation_p"
            ]
            * m
            / rank
        )

        q_value = min(
            1.0,
            previous_q,
            raw_q,
        )

        ordered[index][
            "fdr_q"
        ] = q_value

        previous_q = q_value


def build_game_death_feature_benchmark(
    game_dataset,
    feature,
):
    config = GAME_DEATH_FEATURE_CONFIG[
        feature
    ]

    favorable = config["favorable"]

    rows = _feature_rows(
        game_dataset,
        feature,
    )

    win_values = [
        row["value"]
        for row in rows
        if row["win"]
    ]
    loss_values = [
        row["value"]
        for row in rows
        if not row["win"]
    ]

    if (
        len(win_values) < 5
        or len(loss_values) < 5
    ):
        return {
            "status": "INSUFFICIENT_DATA",
            "feature": feature,
            "label": config["label"],
            "category": config["category"],
            "scope": config["scope"],
            "derived": config["derived"],
            "n_wins": len(win_values),
            "n_losses": len(loss_values),
        }

    win_stats = describe(win_values)
    loss_stats = describe(loss_values)

    delta = cliffs_delta(
        win_values,
        loss_values,
    )

    if (
        win_stats["median"]
        > loss_stats["median"]
    ):
        observed_direction = "higher"
    elif (
        win_stats["median"]
        < loss_stats["median"]
    ):
        observed_direction = "lower"
    else:
        observed_direction = "equal"

    direction_matches = (
        observed_direction == favorable
    )

    aligned_delta = (
        delta
        if favorable == "higher"
        else -delta
    )

    raw_median_gap = (
        win_stats["median"]
        - loss_stats["median"]
    )

    aligned_median_gap = (
        raw_median_gap
        if favorable == "higher"
        else -raw_median_gap
    )

    threshold = find_best_threshold(
        win_values,
        loss_values,
        favorable,
    )

    overlap = iqr_overlap_ratio(
        win_stats,
        loss_stats,
    )

    bootstrap = bootstrap_effect(
        win_values,
        loss_values,
        favorable,
        iterations=BOOTSTRAP_ITERATIONS,
        seed=_stable_seed(
            "DEATH_V9_BOOT",
            feature,
        ),
    )

    cv = cross_validated_balanced_accuracy(
        rows,
        favorable,
    )

    walk_forward = (
        walk_forward_balanced_accuracy(
            rows,
            favorable,
        )
    )

    validation_scores = []

    if cv is not None:
        validation_scores.append(
            cv["balanced_accuracy"]
        )

    if walk_forward is not None:
        validation_scores.append(
            walk_forward[
                "balanced_accuracy"
            ]
        )

    reliability_accuracy = (
        min(validation_scores)
        if validation_scores
        else threshold[
            "balanced_accuracy"
        ]
    )

    reliability = calculate_reliability(
        len(win_values),
        len(loss_values),
        delta,
        reliability_accuracy,
        overlap,
        direction_matches,
        bootstrap=bootstrap,
    )

    permutation_p = permutation_p_value(
        rows,
        favorable,
        seed=_stable_seed(
            "DEATH_V9_PERM",
            feature,
        ),
    )

    return {
        "status": "OK",
        "feature": feature,
        "label": config["label"],
        "category": config["category"],
        "scope": config["scope"],
        "derived": config["derived"],
        "favorable": favorable,

        "n_wins": len(win_values),
        "n_losses": len(loss_values),

        "wins": win_stats,
        "losses": loss_stats,

        "cliffs_delta": delta,
        "aligned_delta": aligned_delta,
        "effect": cliff_effect_label(
            delta
        ),

        "raw_median_gap": raw_median_gap,
        "aligned_median_gap": (
            aligned_median_gap
        ),

        "observed_direction": (
            observed_direction
        ),
        "direction_matches": (
            direction_matches
        ),

        "iqr_overlap": overlap,

        "threshold": threshold[
            "threshold"
        ],
        "balanced_accuracy_in_sample": (
            threshold[
                "balanced_accuracy"
            ]
        ),

        "cross_validation": cv,
        "walk_forward": walk_forward,
        "bootstrap": bootstrap,

        "permutation_p": permutation_p,
        "fdr_q": None,

        "reliability_score": reliability,
        "reliability": reliability_label(
            reliability
        ),

        "robust_signal": False,
    }


def build_game_death_benchmarks(
    game_dataset,
):
    benchmarks = [
        build_game_death_feature_benchmark(
            game_dataset,
            feature,
        )
        for feature in (
            GAME_DEATH_FEATURE_CONFIG
        )
    ]

    _apply_bh_fdr(benchmarks)

    for benchmark in benchmarks:
        if benchmark.get(
            "status"
        ) != "OK":
            continue

        cv = benchmark.get(
            "cross_validation"
        )
        walk = benchmark.get(
            "walk_forward"
        )
        bootstrap = benchmark.get(
            "bootstrap"
        )
        q_value = benchmark.get(
            "fdr_q"
        )

        benchmark[
            "robust_signal"
        ] = (
            benchmark[
                "direction_matches"
            ]
            and benchmark[
                "aligned_delta"
            ] >= 0.33
            and bootstrap is not None
            and bootstrap[
                "aligned_delta_ci_low"
            ] > 0
            and cv is not None
            and cv[
                "balanced_accuracy"
            ] >= 0.60
            and walk is not None
            and walk[
                "balanced_accuracy"
            ] >= 0.60
            and q_value is not None
            and q_value <= 0.05
            and benchmark[
                "reliability_score"
            ] >= 60
        )

    return benchmarks


def _signal_score(
    benchmark,
):
    if (
        benchmark.get("status") != "OK"
        or not benchmark.get(
            "direction_matches"
        )
    ):
        return 0

    cv = benchmark.get(
        "cross_validation"
    )
    walk = benchmark.get(
        "walk_forward"
    )

    if (
        cv is None
        or walk is None
    ):
        validation_strength = 0
    else:
        validation_strength = max(
            0,
            (
                min(
                    cv[
                        "balanced_accuracy"
                    ],
                    walk[
                        "balanced_accuracy"
                    ],
                )
                - 0.5
            )
            * 2
        )

    bootstrap = benchmark.get(
        "bootstrap"
    )

    bootstrap_factor = 1.0

    if bootstrap is not None:
        if (
            bootstrap[
                "aligned_delta_ci_high"
            ] <= 0
        ):
            bootstrap_factor = 0
        elif (
            bootstrap[
                "aligned_delta_ci_low"
            ] <= 0
        ):
            bootstrap_factor = 0.6

    q_value = benchmark.get(
        "fdr_q"
    )

    fdr_factor = (
        1.0
        if (
            q_value is not None
            and q_value <= 0.05
        )
        else 0.5
    )

    return (
        max(
            0,
            benchmark[
                "aligned_delta"
            ],
        )
        * (
            benchmark[
                "reliability_score"
            ] / 100
        )
        * validation_strength
        * bootstrap_factor
        * fdr_factor
        * 100
    )


def rank_game_death_benchmarks(
    benchmarks,
):
    valid = [
        dict(benchmark)
        for benchmark in benchmarks
        if benchmark.get(
            "status"
        ) == "OK"
    ]

    for benchmark in valid:
        benchmark[
            "signal_score"
        ] = _signal_score(
            benchmark
        )

    return sorted(
        valid,
        key=lambda row:
            row["signal_score"],
        reverse=True,
    )


def _format_value(value):
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def _render_benchmark(
    benchmark,
):
    composite = (
        " | COMPOSITE INTERNE"
        if benchmark["derived"]
        else ""
    )

    lines = [
        "",
        (
            f"{benchmark['label']} "
            f"[{benchmark['category']}]"
            f"{composite}"
        ),
        (
            f"N Win/Loss : "
            f"{benchmark['n_wins']} / "
            f"{benchmark['n_losses']}"
        ),
        (
            "Win médiane : "
            f"{_format_value(benchmark['wins']['median'])} "
            f"| Q25/Q75 "
            f"{_format_value(benchmark['wins']['q25'])} / "
            f"{_format_value(benchmark['wins']['q75'])}"
        ),
        (
            "Loss médiane : "
            f"{_format_value(benchmark['losses']['median'])} "
            f"| Q25/Q75 "
            f"{_format_value(benchmark['losses']['q25'])} / "
            f"{_format_value(benchmark['losses']['q75'])}"
        ),
        (
            "Cliff Delta brut : "
            f"{benchmark['cliffs_delta']:+.3f}"
        ),
        (
            "Cliff Delta orienté : "
            f"{benchmark['aligned_delta']:+.3f} "
            f"({benchmark['effect']})"
        ),
        (
            "Chevauchement IQR : "
            f"{benchmark['iqr_overlap'] * 100:.1f}%"
        ),
        (
            "Seuil historique in-sample : "
            f"{_format_value(benchmark['threshold'])}"
        ),
        (
            "Balanced accuracy in-sample : "
            f"{benchmark['balanced_accuracy_in_sample'] * 100:.1f}%"
        ),
    ]

    cv = benchmark.get(
        "cross_validation"
    )

    if cv is not None:
        lines.append(
            f"Balanced accuracy CV "
            f"({cv['folds']}-fold) : "
            f"{cv['balanced_accuracy'] * 100:.1f}%"
        )
    else:
        lines.append(
            "Balanced accuracy CV : indisponible"
        )

    walk = benchmark.get(
        "walk_forward"
    )

    if walk is not None:
        lines.append(
            f"Walk-forward chronologique "
            f"({walk['blocks']} blocs, "
            f"N test={walk['n_test']}) : "
            f"{walk['balanced_accuracy'] * 100:.1f}% "
            f"| sens. "
            f"{walk['sensitivity'] * 100:.1f}% "
            f"| spéc. "
            f"{walk['specificity'] * 100:.1f}%"
        )
    else:
        lines.append(
            "Walk-forward chronologique : indisponible"
        )

    bootstrap = benchmark.get(
        "bootstrap"
    )

    if bootstrap is not None:
        lines.extend([
            (
                "IC95 Cliff orienté : "
                f"{bootstrap['aligned_delta_ci_low']:+.3f} "
                f"à "
                f"{bootstrap['aligned_delta_ci_high']:+.3f}"
            ),
            (
                "IC95 écart médian orienté : "
                f"{_format_value(bootstrap['aligned_median_gap_ci_low'])} "
                f"à "
                f"{_format_value(bootstrap['aligned_median_gap_ci_high'])}"
            ),
        ])

    if benchmark.get(
        "permutation_p"
    ) is not None:
        lines.append(
            "Permutation p : "
            f"{benchmark['permutation_p']:.4f}"
        )

    if benchmark.get(
        "fdr_q"
    ) is not None:
        lines.append(
            "FDR BH q : "
            f"{benchmark['fdr_q']:.4f}"
        )

    lines.extend([
        (
            "Fiabilité interne : "
            f"{benchmark['reliability_score']:.0f}/100 "
            f"({benchmark['reliability']})"
        ),
        (
            "Verdict : "
            + (
                "SIGNAL ROBUSTE"
                if benchmark[
                    "robust_signal"
                ]
                else "EXPLORATOIRE / NON VALIDÉ"
            )
        ),
    ])

    return lines


def render_game_death_validation(
    game_dataset,
    benchmarks,
):
    wins = sum(
        1
        for row in game_dataset
        if row["win"]
    )
    losses = (
        len(game_dataset) - wins
    )

    ranked = rank_game_death_benchmarks(
        benchmarks
    )

    lines = [
        "================================",
        "DEATH ANALYZER - VALIDATION STATISTIQUE GAME LEVEL V9",
        "================================",
        "",
        f"Une observation = une game : {len(game_dataset)}",
        f"N Win/Loss : {wins} / {losses}",
        "",
        "Games à 0 mort incluses dans les métriques globales.",
        "Les métriques 'par mort' utilisent seulement les games avec >=1 mort.",
        "Objectifs/tours post-mort dédupliqués entre fenêtres chevauchantes.",
        "Validation : CV stratifiée + walk-forward chronologique + bootstrap.",
        "Test de permutation + FDR Benjamini-Hochberg pour multiplicité.",
        "Les objectifs/tours sont CONTEXTE : jamais attribués causalement au joueur.",
    ]

    personal_robust = [
        row
        for row in ranked
        if (
            row["scope"] == "PERSONNEL"
            and row["robust_signal"]
        )
    ]

    context_robust = [
        row
        for row in ranked
        if (
            row["scope"] == "CONTEXTE"
            and row["robust_signal"]
        )
    ]

    exploratory = [
        row
        for row in ranked
        if (
            not row["robust_signal"]
            or row["scope"] == "EXPLORATOIRE"
        )
    ]

    lines.extend([
        "",
        "--------------------------------",
        "SIGNAUX PERSONNELS ROBUSTES",
        "--------------------------------",
    ])

    if not personal_robust:
        lines.append(
            "Aucun signal personnel ne passe tous les critères."
        )
    else:
        for benchmark in personal_robust:
            lines.extend(
                _render_benchmark(
                    benchmark
                )
            )

    lines.extend([
        "",
        "--------------------------------",
        "CONTEXTE POST-MORT ROBUSTE",
        "NON ATTRIBUÉ CAUSALEMENT AU JOUEUR",
        "--------------------------------",
    ])

    if not context_robust:
        lines.append(
            "Aucun contexte ne passe tous les critères."
        )
    else:
        for benchmark in context_robust:
            lines.extend(
                _render_benchmark(
                    benchmark
                )
            )

    lines.extend([
        "",
        "--------------------------------",
        "AUTRES MÉTRIQUES / EXPLORATOIRES",
        "--------------------------------",
    ])

    for benchmark in exploratory:
        lines.extend(
            _render_benchmark(
                benchmark
            )
        )

    return "\n".join(lines)




# ============================================================
# V10 - VALIDATION D'INDÉPENDANCE / REDONDANCE
# ============================================================

CONDITIONAL_PERMUTATION_ITERATIONS = 1500
REDUNDANCY_RHO_THRESHOLD = 0.80


def _average_ranks(values):
    """
    Rangs moyens avec gestion des ex-aequo.
    """
    indexed = sorted(
        enumerate(values),
        key=lambda pair: pair[1],
    )

    ranks = [0.0] * len(values)

    index = 0

    while index < len(indexed):
        end = index + 1

        while (
            end < len(indexed)
            and indexed[end][1]
            == indexed[index][1]
        ):
            end += 1

        average_rank = (
            (index + 1 + end) / 2
        )

        for position in range(
            index,
            end,
        ):
            original_index = indexed[
                position
            ][0]

            ranks[
                original_index
            ] = average_rank

        index = end

    return ranks


def _pearson_correlation(
    x_values,
    y_values,
):
    if (
        len(x_values) != len(y_values)
        or len(x_values) < 3
    ):
        return None

    mean_x = sum(x_values) / len(
        x_values
    )

    mean_y = sum(y_values) / len(
        y_values
    )

    numerator = sum(
        (x - mean_x)
        * (y - mean_y)
        for x, y in zip(
            x_values,
            y_values,
        )
    )

    denominator_x = math.sqrt(
        sum(
            (x - mean_x) ** 2
            for x in x_values
        )
    )

    denominator_y = math.sqrt(
        sum(
            (y - mean_y) ** 2
            for y in y_values
        )
    )

    denominator = (
        denominator_x
        * denominator_y
    )

    if denominator == 0:
        return 0.0

    return (
        numerator
        / denominator
    )


def spearman_correlation(
    game_dataset,
    feature_a,
    feature_b,
):
    pairs = []

    for row in game_dataset:
        value_a = row.get(
            feature_a
        )

        value_b = row.get(
            feature_b
        )

        if (
            value_a is None
            or value_b is None
        ):
            continue

        pairs.append(
            (
                float(value_a),
                float(value_b),
            )
        )

    if len(pairs) < 5:
        return None

    x_values = [
        pair[0]
        for pair in pairs
    ]

    y_values = [
        pair[1]
        for pair in pairs
    ]

    x_ranks = _average_ranks(
        x_values
    )

    y_ranks = _average_ranks(
        y_values
    )

    return _pearson_correlation(
        x_ranks,
        y_ranks,
    )


def _death_volume_stratum(
    deaths,
):
    """
    Strates fixées AVANT de regarder win/loss.

    0-1, 2-3, 4-5, 6-7, 8-9, 10+
    """
    deaths = int(
        deaths
    )

    if deaths >= 10:
        return 5

    return deaths // 2


def conditional_permutation_p_value(
    game_dataset,
    feature,
    favorable,
    iterations=CONDITIONAL_PERMUTATION_ITERATIONS,
):
    """
    Test de permutation CONDITIONNEL au volume de morts.

    Les labels win/loss ne sont mélangés qu'entre games ayant
    un nombre de morts similaire.

    Interprétation :
    si le signal reste significatif, il contient de l'information
    au-delà du simple fait de "mourir plus souvent".

    Ce test est particulièrement important pour :
    - coût moyen par mort ;
    - coûts cumulés ;
    - sévérité ;
    - death chains / spirals.
    """
    rows = []

    for row in game_dataset:
        value = row.get(
            feature
        )

        deaths = row.get(
            "deaths"
        )

        if (
            value is None
            or deaths is None
        ):
            continue

        rows.append({
            "value": float(
                value
            ),
            "win": bool(
                row["win"]
            ),
            "stratum": (
                _death_volume_stratum(
                    deaths
                )
            ),
        })

    win_values = [
        row["value"]
        for row in rows
        if row["win"]
    ]

    loss_values = [
        row["value"]
        for row in rows
        if not row["win"]
    ]

    if (
        len(win_values) < 5
        or len(loss_values) < 5
    ):
        return None

    observed_delta = cliffs_delta(
        win_values,
        loss_values,
    )

    observed_aligned = (
        observed_delta
        if favorable == "higher"
        else -observed_delta
    )

    if observed_aligned <= 0:
        return 1.0

    strata = {}

    for index, row in enumerate(
        rows
    ):
        strata.setdefault(
            row["stratum"],
            [],
        ).append(
            index
        )

    original_labels = [
        row["win"]
        for row in rows
    ]

    rng = random.Random(
        _stable_seed(
            "DEATH_V10_CONDITIONAL",
            feature,
        )
    )

    exceedances = 0

    for _ in range(
        iterations
    ):
        permuted_labels = list(
            original_labels
        )

        for indices in strata.values():
            labels = [
                original_labels[index]
                for index in indices
            ]

            rng.shuffle(
                labels
            )

            for index, label in zip(
                indices,
                labels,
            ):
                permuted_labels[
                    index
                ] = label

        perm_wins = [
            row["value"]
            for row, label in zip(
                rows,
                permuted_labels,
            )
            if label
        ]

        perm_losses = [
            row["value"]
            for row, label in zip(
                rows,
                permuted_labels,
            )
            if not label
        ]

        if (
            not perm_wins
            or not perm_losses
        ):
            continue

        delta = cliffs_delta(
            perm_wins,
            perm_losses,
        )

        aligned = (
            delta
            if favorable == "higher"
            else -delta
        )

        if aligned >= observed_aligned:
            exceedances += 1

    return (
        exceedances + 1
    ) / (
        iterations + 1
    )


def _apply_bh_to_field(
    benchmarks,
    p_field,
    q_field,
):
    valid = [
        benchmark
        for benchmark in benchmarks
        if (
            benchmark.get(
                "status"
            ) == "OK"
            and benchmark.get(
                p_field
            ) is not None
        )
    ]

    if not valid:
        return

    ordered = sorted(
        valid,
        key=lambda benchmark:
            benchmark[
                p_field
            ],
    )

    count = len(
        ordered
    )

    previous_q = 1.0

    for reverse_index in range(
        count - 1,
        -1,
        -1,
    ):
        rank = (
            reverse_index + 1
        )

        benchmark = ordered[
            reverse_index
        ]

        raw_q = (
            benchmark[
                p_field
            ]
            * count
            / rank
        )

        q_value = min(
            1.0,
            previous_q,
            raw_q,
        )

        benchmark[
            q_field
        ] = q_value

        previous_q = q_value


def _is_volume_feature(
    feature,
):
    return feature in {
        "deaths",
        "deaths_per_10",
    }


def _is_core_candidate(
    benchmark,
):
    """
    Les composites internes (severity/spiral) ne deviennent jamais
    des preuves indépendantes du modèle : ils restent utiles comme
    résumés/alertes mais ne font pas partie du noyau statistique brut.
    """
    return (
        benchmark.get(
            "scope"
        ) == "PERSONNEL"
        and not benchmark.get(
            "derived",
            False,
        )
        and benchmark.get(
            "robust_signal",
            False,
        )
    )


def attach_v10_independence_validation(
    game_dataset,
    benchmarks,
):
    """
    Ajoute :
    - p/q conditionnels au nombre de morts ;
    - drapeau d'indépendance vis-à-vis du volume ;
    - corrélations entre signaux CORE ;
    - groupes de redondance.
    """
    for benchmark in benchmarks:
        if benchmark.get(
            "status"
        ) != "OK":
            continue

        feature = benchmark[
            "feature"
        ]

        benchmark[
            "conditional_volume_p"
        ] = None

        benchmark[
            "conditional_volume_q"
        ] = None

        benchmark[
            "independent_of_death_volume"
        ] = None

        benchmark[
            "redundant_with"
        ] = []

        benchmark[
            "canonical_core"
        ] = False

        if _is_volume_feature(
            feature
        ):
            # Une métrique de volume ne peut pas être testée
            # "indépendamment du volume" contre elle-même.
            benchmark[
                "independent_of_death_volume"
            ] = True

        elif benchmark.get(
            "scope"
        ) == "PERSONNEL":
            p_value = (
                conditional_permutation_p_value(
                    game_dataset,
                    feature,
                    benchmark[
                        "favorable"
                    ],
                )
            )

            benchmark[
                "conditional_volume_p"
            ] = p_value

    _apply_bh_to_field(
        benchmarks,
        "conditional_volume_p",
        "conditional_volume_q",
    )

    for benchmark in benchmarks:
        if benchmark.get(
            "status"
        ) != "OK":
            continue

        if _is_volume_feature(
            benchmark[
                "feature"
            ]
        ):
            continue

        if benchmark.get(
            "scope"
        ) != "PERSONNEL":
            continue

        q_value = benchmark.get(
            "conditional_volume_q"
        )

        benchmark[
            "independent_of_death_volume"
        ] = (
            q_value is not None
            and q_value <= 0.05
        )

    # Le ranking V9 retournait des copies. Pour la sélection
    # canonique V10, on attache donc le score directement aux
    # objets originaux.
    for benchmark in benchmarks:
        if benchmark.get(
            "status"
        ) == "OK":
            benchmark[
                "signal_score"
            ] = _signal_score(
                benchmark
            )

    # --------------------------------------------------------
    # Redondance uniquement parmi les candidats CORE bruts.
    # --------------------------------------------------------
    candidates = [
        benchmark
        for benchmark in benchmarks
        if _is_core_candidate(
            benchmark
        )
    ]

    for index, benchmark_a in enumerate(
        candidates
    ):
        for benchmark_b in candidates[
            index + 1:
        ]:
            rho = spearman_correlation(
                game_dataset,
                benchmark_a[
                    "feature"
                ],
                benchmark_b[
                    "feature"
                ],
            )

            if (
                rho is not None
                and abs(
                    rho
                ) >= REDUNDANCY_RHO_THRESHOLD
            ):
                benchmark_a[
                    "redundant_with"
                ].append({
                    "feature": benchmark_b[
                        "feature"
                    ],
                    "label": benchmark_b[
                        "label"
                    ],
                    "rho": rho,
                })

                benchmark_b[
                    "redundant_with"
                ].append({
                    "feature": benchmark_a[
                        "feature"
                    ],
                    "label": benchmark_a[
                        "label"
                    ],
                    "rho": rho,
                })

    # --------------------------------------------------------
    # Choix canonique :
    # - priorité aux métriques indépendantes du volume ;
    # - puis meilleur signal_score ;
    # - une métrique fortement redondante avec une métrique déjà
    #   retenue n'est pas retenue une seconde fois.
    # --------------------------------------------------------
    ranked_candidates = sorted(
        candidates,
        key=lambda benchmark: (
            1
            if benchmark.get(
                "independent_of_death_volume"
            )
            else 0,
            benchmark.get(
                "signal_score",
                0,
            ),
        ),
        reverse=True,
    )

    selected = []

    for benchmark in ranked_candidates:
        feature = benchmark[
            "feature"
        ]

        is_redundant = False

        for selected_benchmark in selected:
            rho = spearman_correlation(
                game_dataset,
                feature,
                selected_benchmark[
                    "feature"
                ],
            )

            if (
                rho is not None
                and abs(
                    rho
                ) >= REDUNDANCY_RHO_THRESHOLD
            ):
                is_redundant = True
                break

        if not is_redundant:
            benchmark[
                "canonical_core"
            ] = True

            selected.append(
                benchmark
            )

    return benchmarks


def _format_optional_probability(
    value,
):
    if value is None:
        return "indisponible"

    return f"{value:.4f}"


def render_v10_final_core(
    game_dataset,
    benchmarks,
):
    """
    Rapport de clôture méthodologique du Death Analyzer.

    Il ne remplace pas le rapport V9 détaillé : il extrait ce qui
    mérite réellement d'entrer plus tard dans le moteur de coaching.
    """
    attach_v10_independence_validation(
        game_dataset,
        benchmarks,
    )

    # Recalcule les scores de ranking avant sélection canonique si
    # le rapport est appelé directement.
    ranked = rank_game_death_benchmarks(
        benchmarks
    )

    # Les dicts de rank_game_death_benchmarks sont des copies.
    # On s'appuie donc sur les objets originaux pour les drapeaux V10.
    core = [
        benchmark
        for benchmark in benchmarks
        if (
            benchmark.get(
                "status"
            ) == "OK"
            and benchmark.get(
                "canonical_core"
            )
        )
    ]

    robust_redundant = [
        benchmark
        for benchmark in benchmarks
        if (
            _is_core_candidate(
                benchmark
            )
            and not benchmark.get(
                "canonical_core"
            )
        )
    ]

    derived_validated = [
        benchmark
        for benchmark in benchmarks
        if (
            benchmark.get(
                "status"
            ) == "OK"
            and benchmark.get(
                "scope"
            ) == "PERSONNEL"
            and benchmark.get(
                "derived",
                False,
            )
            and benchmark.get(
                "robust_signal",
                False,
            )
        )
    ]

    lines = [
        "================================",
        "DEATH ANALYZER - NOYAU FINAL V10",
        "================================",
        "",
        "Objectif : éviter le double comptage de 15 métriques qui racontent la même chose.",
        "CORE = signal brut, robuste, puis dédoublonné par corrélation de Spearman.",
        "Le test conditionnel mélange les wins/losses seulement entre games de volume de morts similaire.",
        "Ainsi on peut vérifier si le coût par mort apporte quelque chose AU-DELÀ de 'je meurs plus'.",
        "",
        "--------------------------------",
        "MÉTRIQUES CORE À CONSERVER",
        "--------------------------------",
    ]

    if not core:
        lines.append(
            "Aucune métrique CORE retenue."
        )

    else:
        for benchmark in core:
            q_value = benchmark.get(
                "conditional_volume_q"
            )

            independence_text = (
                "OUI"
                if benchmark.get(
                    "independent_of_death_volume"
                )
                else "NON / NON DÉMONTRÉ"
            )

            lines.extend([
                "",
                (
                    f"{benchmark['label']} "
                    f"[{benchmark['category']}]"
                ),
                (
                    f"Cliff orienté : "
                    f"{benchmark['aligned_delta']:+.3f}"
                ),
                (
                    f"CV : "
                    f"{benchmark['cross_validation']['balanced_accuracy'] * 100:.1f}%"
                    if benchmark.get(
                        "cross_validation"
                    )
                    else "CV : indisponible"
                ),
                (
                    f"Walk-forward : "
                    f"{benchmark['walk_forward']['balanced_accuracy'] * 100:.1f}%"
                    if benchmark.get(
                        "walk_forward"
                    )
                    else "Walk-forward : indisponible"
                ),
                (
                    "Indépendant du simple volume de morts : "
                    f"{independence_text}"
                ),
                (
                    "FDR conditionnelle volume : "
                    f"{_format_optional_probability(q_value)}"
                ),
            ])

    lines.extend([
        "",
        "--------------------------------",
        "ROBUSTES MAIS REDONDANTES",
        "NE PAS DOUBLE-COMPTER",
        "--------------------------------",
    ])

    if not robust_redundant:
        lines.append(
            "Aucune."
        )
    else:
        for benchmark in robust_redundant:
            correlations = benchmark.get(
                "redundant_with",
                [],
            )

            strongest = sorted(
                correlations,
                key=lambda item:
                    abs(
                        item["rho"]
                    ),
                reverse=True,
            )

            if strongest:
                relation = strongest[0]

                lines.append(
                    f"- {benchmark['label']} "
                    f"~ {relation['label']} "
                    f"(Spearman {relation['rho']:+.2f})"
                )
            else:
                lines.append(
                    f"- {benchmark['label']} "
                    "(non retenue dans le noyau canonique)"
                )

    lines.extend([
        "",
        "--------------------------------",
        "COMPOSITES INTERNES VALIDÉS",
        "À UTILISER COMME RÉSUMÉS / ALERTES",
        "PAS COMME PREUVES INDÉPENDANTES",
        "--------------------------------",
    ])

    if not derived_validated:
        lines.append(
            "Aucun composite."
        )
    else:
        for benchmark in derived_validated:
            q_value = benchmark.get(
                "conditional_volume_q"
            )

            lines.append(
                f"- {benchmark['label']} | "
                f"delta {benchmark['aligned_delta']:+.3f} | "
                f"q conditionnel "
                f"{_format_optional_probability(q_value)}"
            )

    return "\n".join(
        lines
    )


# ============================================================
# V11 - CONDITIONNEMENT EXACT AU NOMBRE DE MORTS
# ============================================================

EXACT_VOLUME_PERMUTATION_ITERATIONS = 2000
MIN_EXACT_VOLUME_GAMES = 15
MIN_EXACT_VOLUME_STRATA = 2


def exact_death_volume_conditional_test(
    game_dataset,
    feature,
    favorable,
    iterations=EXACT_VOLUME_PERMUTATION_ITERATIONS,
):
    """
    Test conditionnel EXACT au nombre de morts.

    Seules les strates de nombre de morts contenant au moins
    une victoire ET une défaite sont informatives.

    Dans chaque strate :
      - on centre la feature par la médiane de la strate ;
      - on conserve exactement le nombre de wins/losses ;
      - on permute uniquement les labels à l'intérieur de la strate.

    Le Cliff Delta sur les résidus centrés mesure donc un signal
    au-delà du nombre exact de morts observé dans la game.
    """
    strata = {}

    for row in game_dataset:
        value = row.get(
            feature
        )

        deaths = row.get(
            "deaths"
        )

        if (
            value is None
            or deaths is None
        ):
            continue

        strata.setdefault(
            int(
                deaths
            ),
            [],
        ).append({
            "value": float(
                value
            ),
            "win": bool(
                row["win"]
            ),
        })

    informative = {}

    for death_count, rows in strata.items():
        has_win = any(
            row[
                "win"
            ]
            for row in rows
        )

        has_loss = any(
            not row[
                "win"
            ]
            for row in rows
        )

        if (
            has_win
            and has_loss
        ):
            values = [
                row[
                    "value"
                ]
                for row in rows
            ]

            center = median(
                values
            )

            informative[
                death_count
            ] = [
                {
                    "residual": (
                        row[
                            "value"
                        ]
                        - center
                    ),
                    "win": row[
                        "win"
                    ],
                }
                for row in rows
            ]

    informative_games = sum(
        len(
            rows
        )
        for rows in informative.values()
    )

    if (
        informative_games
        < MIN_EXACT_VOLUME_GAMES
        or len(
            informative
        )
        < MIN_EXACT_VOLUME_STRATA
    ):
        return None

    observed_wins = []
    observed_losses = []

    for rows in informative.values():
        for row in rows:
            if row[
                "win"
            ]:
                observed_wins.append(
                    row[
                        "residual"
                    ]
                )
            else:
                observed_losses.append(
                    row[
                        "residual"
                    ]
                )

    if (
        len(
            observed_wins
        ) < 5
        or len(
            observed_losses
        ) < 5
    ):
        return None

    observed_delta = cliffs_delta(
        observed_wins,
        observed_losses,
    )

    observed_aligned = (
        observed_delta
        if favorable == "higher"
        else -observed_delta
    )

    rng = random.Random(
        _stable_seed(
            "DEATH_V11_EXACT_VOLUME",
            feature,
        )
    )

    exceedances = 0

    for _ in range(
        iterations
    ):
        perm_wins = []
        perm_losses = []

        for rows in informative.values():
            labels = [
                row[
                    "win"
                ]
                for row in rows
            ]

            rng.shuffle(
                labels
            )

            for row, label in zip(
                rows,
                labels,
            ):
                if label:
                    perm_wins.append(
                        row[
                            "residual"
                        ]
                    )
                else:
                    perm_losses.append(
                        row[
                            "residual"
                        ]
                    )

        delta = cliffs_delta(
            perm_wins,
            perm_losses,
        )

        aligned = (
            delta
            if favorable == "higher"
            else -delta
        )

        if aligned >= observed_aligned:
            exceedances += 1

    p_value = (
        exceedances + 1
    ) / (
        iterations + 1
    )

    return {
        "p_value": p_value,
        "aligned_delta": (
            observed_aligned
        ),
        "n_games": (
            informative_games
        ),
        "n_strata": len(
            informative
        ),
        "n_wins": len(
            observed_wins
        ),
        "n_losses": len(
            observed_losses
        ),
    }


def attach_v11_exact_volume_validation(
    game_dataset,
    benchmarks,
):
    """
    Remplace la notion approximative "indépendant du volume"
    par un test exact au même nombre de morts.
    """
    for benchmark in benchmarks:
        if benchmark.get(
            "status"
        ) != "OK":
            continue

        feature = benchmark[
            "feature"
        ]

        benchmark[
            "exact_volume_test"
        ] = None

        benchmark[
            "exact_volume_p"
        ] = None

        benchmark[
            "exact_volume_q"
        ] = None

        benchmark[
            "survives_exact_volume"
        ] = None

        if _is_volume_feature(
            feature
        ):
            # Non applicable : la feature EST le volume.
            continue

        if benchmark.get(
            "scope"
        ) != "PERSONNEL":
            continue

        result = (
            exact_death_volume_conditional_test(
                game_dataset,
                feature,
                benchmark[
                    "favorable"
                ],
            )
        )

        benchmark[
            "exact_volume_test"
        ] = result

        if result is not None:
            benchmark[
                "exact_volume_p"
            ] = result[
                "p_value"
            ]

    _apply_bh_to_field(
        benchmarks,
        "exact_volume_p",
        "exact_volume_q",
    )

    for benchmark in benchmarks:
        if benchmark.get(
            "status"
        ) != "OK":
            continue

        if _is_volume_feature(
            benchmark[
                "feature"
            ]
        ):
            benchmark[
                "survives_exact_volume"
            ] = None

            continue

        if benchmark.get(
            "scope"
        ) != "PERSONNEL":
            continue

        result = benchmark.get(
            "exact_volume_test"
        )

        q_value = benchmark.get(
            "exact_volume_q"
        )

        benchmark[
            "survives_exact_volume"
        ] = (
            result is not None
            and result[
                "aligned_delta"
            ] >= 0.147
            and q_value is not None
            and q_value <= 0.05
        )

    return benchmarks


def render_v11_freeze_report(
    game_dataset,
    benchmarks,
):
    """
    Rapport final destiné à décider quelles métriques brutes
    sont réellement prêtes à être figées.
    """
    # V10 attaches correlations / canonical core.
    attach_v10_independence_validation(
        game_dataset,
        benchmarks,
    )

    attach_v11_exact_volume_validation(
        game_dataset,
        benchmarks,
    )

    # Attach actual ranking scores to originals.
    for benchmark in benchmarks:
        if benchmark.get(
            "status"
        ) == "OK":
            benchmark[
                "signal_score"
            ] = _signal_score(
                benchmark
            )

    raw_robust = [
        benchmark
        for benchmark in benchmarks
        if (
            benchmark.get(
                "status"
            ) == "OK"
            and benchmark.get(
                "scope"
            ) == "PERSONNEL"
            and not benchmark.get(
                "derived",
                False,
            )
            and benchmark.get(
                "robust_signal",
                False,
            )
        )
    ]

    # First remove highly correlated duplicates using same V10 rule.
    ordered = sorted(
        raw_robust,
        key=lambda benchmark:
            benchmark.get(
                "signal_score",
                0,
            ),
        reverse=True,
    )

    selected = []

    for benchmark in ordered:
        feature = benchmark[
            "feature"
        ]

        if (
            not _is_volume_feature(
                feature
            )
            and benchmark.get(
                "survives_exact_volume"
            )
            is not True
        ):
            continue

        redundant = False

        for chosen in selected:
            rho = spearman_correlation(
                game_dataset,
                feature,
                chosen[
                    "feature"
                ],
            )

            if (
                rho is not None
                and abs(
                    rho
                )
                >= REDUNDANCY_RHO_THRESHOLD
            ):
                redundant = True
                break

        if not redundant:
            selected.append(
                benchmark
            )

    lines = [
        "================================",
        "DEATH ANALYZER - FREEZE REPORT V11",
        "================================",
        "",
        "Scores Severity/Spiral : référence HISTORIQUE uniquement, jamais future.",
        "CORE brut : validation V9 + walk-forward + FDR + conditionnement EXACT au nombre de morts.",
        "Les métriques de volume sont marquées N/A au test conditionnel car elles définissent le volume.",
        "",
        "--------------------------------",
        "CORE BRUT PRÊT À FIGER",
        "--------------------------------",
    ]

    if not selected:
        lines.append(
            "Aucun signal brut ne passe tous les critères V11."
        )
    else:
        for benchmark in selected:
            feature = benchmark[
                "feature"
            ]

            lines.extend([
                "",
                f"{benchmark['label']} [{benchmark['category']}]",
                f"Cliff orienté : {benchmark['aligned_delta']:+.3f}",
                (
                    "Conditionnement exact au nombre de morts : "
                    "N/A (métrique de volume)"
                    if _is_volume_feature(
                        feature
                    )
                    else (
                        "PASS"
                        if benchmark.get(
                            "survives_exact_volume"
                        )
                        else "FAIL"
                    )
                ),
            ])

            exact = benchmark.get(
                "exact_volume_test"
            )

            if exact is not None:
                lines.extend([
                    (
                        f"  Delta conditionnel exact : "
                        f"{exact['aligned_delta']:+.3f}"
                    ),
                    (
                        f"  N informatif : "
                        f"{exact['n_games']} games / "
                        f"{exact['n_strata']} volumes exacts"
                    ),
                    (
                        f"  FDR exacte q : "
                        f"{benchmark['exact_volume_q']:.4f}"
                    ),
                ])

    lines.extend([
        "",
        "--------------------------------",
        "RÈGLES DE FIGEAGE",
        "--------------------------------",
        "- Les conséquences tours/objectifs restent CONTEXTE.",
        "- Les scores Severity/Spiral restent des COMPOSITES d'explication.",
        "- Une métrique brute très corrélée à une CORE n'est pas double-comptée.",
        "- Une métrique brute hors volume doit survivre au même nombre EXACT de morts.",
    ])

    return "\n".join(
        lines
    )
