import hashlib
import math
import random

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


def stable_seed(*parts):
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


def average_ranks(values):
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
            index + 1 + end
        ) / 2

        for position in range(
            index,
            end,
        ):
            original_index = (
                indexed[position][0]
            )

            ranks[
                original_index
            ] = average_rank

        index = end

    return ranks


def pearson_correlation(
    first,
    second,
):
    if (
        len(first) != len(second)
        or len(first) < 3
    ):
        return None

    mean_first = (
        sum(first) / len(first)
    )

    mean_second = (
        sum(second) / len(second)
    )

    numerator = sum(
        (
            first_value - mean_first
        )
        * (
            second_value - mean_second
        )
        for (
            first_value,
            second_value,
        )
        in zip(
            first,
            second,
        )
    )

    denominator_first = math.sqrt(
        sum(
            (
                value - mean_first
            ) ** 2
            for value in first
        )
    )

    denominator_second = math.sqrt(
        sum(
            (
                value - mean_second
            ) ** 2
            for value in second
        )
    )

    denominator = (
        denominator_first
        * denominator_second
    )

    if denominator == 0:
        return 0.0

    return (
        numerator / denominator
    )


def spearman_correlation(
    dataset,
    feature_a,
    feature_b,
):
    pairs = []

    for row in dataset:
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

    first = [
        pair[0]
        for pair in pairs
    ]

    second = [
        pair[1]
        for pair in pairs
    ]

    return pearson_correlation(
        average_ranks(first),
        average_ranks(second),
    )


def feature_rows(
    dataset,
    feature,
):
    result = []

    for row in dataset:
        value = row.get(
            feature
        )

        if value is None:
            continue

        result.append({
            "match_id": row[
                "match_id"
            ],
            "game_creation": (
                row.get(
                    "game_creation"
                )
                or 0
            ),
            "win": bool(
                row["win"]
            ),
            "value": float(value),
        })

    return result


def predict_win(
    value,
    threshold,
    favorable,
):
    if favorable == "higher":
        return (
            value >= threshold
        )

    return (
        value <= threshold
    )


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
        for index, row in enumerate(
            group
        ):
            assignments[
                row["match_id"]
            ] = (
                index % folds
            )

    correct_wins = 0
    total_wins = 0
    correct_losses = 0
    total_losses = 0

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

        threshold = (
            find_best_threshold(
                train_wins,
                train_losses,
                favorable,
            )[
                "threshold"
            ]
        )

        for row in test:
            predicted = predict_win(
                row["value"],
                threshold,
                favorable,
            )

            if row["win"]:
                total_wins += 1

                if predicted:
                    correct_wins += 1

            else:
                total_losses += 1

                if not predicted:
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
            sensitivity
            + specificity
        ) / 2,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "n_test": (
            total_wins
            + total_losses
        ),
    }


def walk_forward_balanced_accuracy(
    rows,
    favorable,
    initial_fraction=0.50,
    test_blocks=4,
):
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

    if initial_size >= (
        len(ordered) - 4
    ):
        return None

    remaining = (
        len(ordered)
        - initial_size
    )

    block_size = max(
        1,
        remaining // test_blocks,
    )

    correct_wins = 0
    total_wins = 0
    correct_losses = 0
    total_losses = 0
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
            threshold = (
                find_best_threshold(
                    train_wins,
                    train_losses,
                    favorable,
                )[
                    "threshold"
                ]
            )

            blocks_used += 1

            for row in test:
                predicted = predict_win(
                    row["value"],
                    threshold,
                    favorable,
                )

                if row["win"]:
                    total_wins += 1

                    if predicted:
                        correct_wins += 1

                else:
                    total_losses += 1

                    if not predicted:
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
            sensitivity
            + specificity
        ) / 2,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "n_test": (
            total_wins
            + total_losses
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

    delta = cliffs_delta(
        win_values,
        loss_values,
    )

    aligned_observed = (
        delta
        if favorable == "higher"
        else -delta
    )

    if aligned_observed <= 0:
        return 1.0

    values = [
        row["value"]
        for row in rows
    ]

    n_wins = len(win_values)

    rng = random.Random(seed)
    exceedances = 0

    for _ in range(iterations):
        shuffled = list(values)
        rng.shuffle(shuffled)

        perm_wins = shuffled[:n_wins]
        perm_losses = shuffled[n_wins:]

        perm_delta = cliffs_delta(
            perm_wins,
            perm_losses,
        )

        aligned = (
            perm_delta
            if favorable == "higher"
            else -perm_delta
        )

        if aligned >= aligned_observed:
            exceedances += 1

    return (
        exceedances + 1
    ) / (
        iterations + 1
    )


def apply_bh_fdr(
    benchmarks,
    p_field="permutation_p",
    q_field="fdr_q",
):
    valid = [
        benchmark
        for benchmark in benchmarks
        if (
            benchmark.get("status")
            == "OK"
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
            benchmark[p_field],
    )

    count = len(ordered)
    previous_q = 1.0

    for index in range(
        count - 1,
        -1,
        -1,
    ):
        rank = index + 1

        benchmark = ordered[
            index
        ]

        raw_q = (
            benchmark[p_field]
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


def build_feature_validation(
    dataset,
    feature,
    config,
    seed_namespace,
):
    rows = feature_rows(
        dataset,
        feature,
    )

    wins = [
        row["value"]
        for row in rows
        if row["win"]
    ]

    losses = [
        row["value"]
        for row in rows
        if not row["win"]
    ]

    result = {
        "feature": feature,
        "label": config["label"],
        "category": config["category"],
        "scope": config["scope"],
        "derived": config.get(
            "derived",
            False,
        ),
        "favorable": config[
            "favorable"
        ],
        "n_wins": len(wins),
        "n_losses": len(losses),
    }

    if (
        len(wins) < 5
        or len(losses) < 5
    ):
        result["status"] = (
            "INSUFFICIENT_DATA"
        )

        return result

    favorable = config[
        "favorable"
    ]

    win_stats = describe(wins)
    loss_stats = describe(losses)

    delta = cliffs_delta(
        wins,
        losses,
    )

    aligned_delta = (
        delta
        if favorable == "higher"
        else -delta
    )

    if (
        win_stats["median"]
        > loss_stats["median"]
    ):
        observed_direction = (
            "higher"
        )

    elif (
        win_stats["median"]
        < loss_stats["median"]
    ):
        observed_direction = (
            "lower"
        )

    else:
        observed_direction = (
            "equal"
        )

    direction_matches = (
        observed_direction
        == favorable
    )

    threshold = find_best_threshold(
        wins,
        losses,
        favorable,
    )

    overlap = iqr_overlap_ratio(
        win_stats,
        loss_stats,
    )

    bootstrap = bootstrap_effect(
        wins,
        losses,
        favorable,
        iterations=BOOTSTRAP_ITERATIONS,
        seed=stable_seed(
            seed_namespace,
            "BOOT",
            feature,
        ),
    )

    cv = (
        cross_validated_balanced_accuracy(
            rows,
            favorable,
        )
    )

    walk = (
        walk_forward_balanced_accuracy(
            rows,
            favorable,
        )
    )

    validation_scores = []

    if cv:
        validation_scores.append(
            cv["balanced_accuracy"]
        )

    if walk:
        validation_scores.append(
            walk["balanced_accuracy"]
        )

    reliability_accuracy = (
        min(validation_scores)
        if validation_scores
        else threshold[
            "balanced_accuracy"
        ]
    )

    reliability = calculate_reliability(
        len(wins),
        len(losses),
        delta,
        reliability_accuracy,
        overlap,
        direction_matches,
        bootstrap=bootstrap,
    )

    permutation_p = (
        permutation_p_value(
            rows,
            favorable,
            seed=stable_seed(
                seed_namespace,
                "PERM",
                feature,
            ),
        )
    )

    result.update({
        "status": "OK",
        "wins": win_stats,
        "losses": loss_stats,
        "cliffs_delta": delta,
        "aligned_delta": aligned_delta,
        "effect": cliff_effect_label(
            delta
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
        "walk_forward": walk,
        "bootstrap": bootstrap,
        "permutation_p": (
            permutation_p
        ),
        "fdr_q": None,
        "reliability_score": (
            reliability
        ),
        "reliability": (
            reliability_label(
                reliability
            )
        ),
        "robust_signal": False,
    })

    return result
