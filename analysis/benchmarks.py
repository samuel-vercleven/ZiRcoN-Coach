import hashlib
import random
from bisect import bisect_left, bisect_right

from analysis.feature_engine import (
    FEATURE_CONFIG,
    describe,
    get_feature_values,
    count_unique_games,
    percentile,
)


BOOTSTRAP_ITERATIONS = 500


# ============================================================
# CLIFF'S DELTA
# ============================================================

def cliffs_delta(first_values, second_values):
    """
    Cliff's Delta efficace.

    +1 : les valeurs du premier groupe sont presque toujours supérieures.
    -1 : elles sont presque toujours inférieures.
     0 : fort chevauchement.
    """
    if not first_values or not second_values:
        return None

    second_sorted = sorted(second_values)

    greater = 0
    lower = 0

    for first in first_values:
        # Nombre de valeurs second strictement inférieures à first.
        greater += bisect_left(second_sorted, first)

        # Nombre de valeurs second strictement supérieures à first.
        lower += (
            len(second_sorted)
            - bisect_right(second_sorted, first)
        )

    comparisons = len(first_values) * len(second_values)

    if comparisons == 0:
        return None

    return (greater - lower) / comparisons


def cliff_effect_label(delta):
    if delta is None:
        return "INCONNU"

    value = abs(delta)

    if value < 0.147:
        return "NÉGLIGEABLE"

    if value < 0.33:
        return "FAIBLE"

    if value < 0.474:
        return "MODÉRÉ"

    return "FORT"


# ============================================================
# BOOTSTRAP
# ============================================================

def _stable_seed(*parts):
    text = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def bootstrap_effect(
    win_values,
    loss_values,
    favorable,
    iterations=BOOTSTRAP_ITERATIONS,
    seed=42,
):
    """
    Bootstrap de Cliff's Delta et de l'écart de médiane.

    Les intervalles retournés sont orientés :
    une valeur positive signifie une direction favorable aux victoires.
    """
    if len(win_values) < 4 or len(loss_values) < 4:
        return None

    rng = random.Random(seed)

    aligned_deltas = []
    aligned_median_gaps = []

    for _ in range(iterations):
        sampled_wins = [
            rng.choice(win_values)
            for _ in range(len(win_values))
        ]

        sampled_losses = [
            rng.choice(loss_values)
            for _ in range(len(loss_values))
        ]

        delta = cliffs_delta(
            sampled_wins,
            sampled_losses,
        )

        win_median = describe(sampled_wins)["median"]
        loss_median = describe(sampled_losses)["median"]

        median_gap = win_median - loss_median

        if favorable == "higher":
            aligned_delta = delta
            aligned_median_gap = median_gap
        else:
            aligned_delta = -delta
            aligned_median_gap = -median_gap

        aligned_deltas.append(aligned_delta)
        aligned_median_gaps.append(aligned_median_gap)

    delta_low = percentile(aligned_deltas, 2.5)
    delta_high = percentile(aligned_deltas, 97.5)

    median_low = percentile(aligned_median_gaps, 2.5)
    median_high = percentile(aligned_median_gaps, 97.5)

    return {
        "iterations": iterations,
        "aligned_delta_ci_low": delta_low,
        "aligned_delta_ci_high": delta_high,
        "aligned_median_gap_ci_low": median_low,
        "aligned_median_gap_ci_high": median_high,
        "delta_ci_crosses_zero": (
            delta_low <= 0 <= delta_high
        ),
        "median_ci_crosses_zero": (
            median_low <= 0 <= median_high
        ),
        "aligned_delta_ci_width": (
            delta_high - delta_low
        ),
    }


# ============================================================
# DISTRIBUTIONS
# ============================================================

def iqr_overlap_ratio(first_stats, second_stats):
    """
    0 = aucun chevauchement des IQR.
    1 = chevauchement maximal.
    """
    if not first_stats or not second_stats:
        return None

    left = max(
        first_stats["q25"],
        second_stats["q25"],
    )

    right = min(
        first_stats["q75"],
        second_stats["q75"],
    )

    overlap = max(0, right - left)

    union_left = min(
        first_stats["q25"],
        second_stats["q25"],
    )

    union_right = max(
        first_stats["q75"],
        second_stats["q75"],
    )

    union = union_right - union_left

    if union <= 0:
        # Deux distributions constantes identiques.
        return 1.0

    return overlap / union


# ============================================================
# SEUIL / BALANCED ACCURACY
# ============================================================

def calculate_balanced_accuracy(
    win_values,
    loss_values,
    threshold,
    favorable,
):
    if not win_values or not loss_values:
        return None

    if favorable == "higher":
        correct_wins = sum(
            1
            for value in win_values
            if value >= threshold
        )

        correct_losses = sum(
            1
            for value in loss_values
            if value < threshold
        )

    else:
        correct_wins = sum(
            1
            for value in win_values
            if value <= threshold
        )

        correct_losses = sum(
            1
            for value in loss_values
            if value > threshold
        )

    sensitivity = correct_wins / len(win_values)
    specificity = correct_losses / len(loss_values)

    balanced_accuracy = (
        sensitivity + specificity
    ) / 2

    return {
        "balanced_accuracy": balanced_accuracy,
        "sensitivity": sensitivity,
        "specificity": specificity,
    }


def find_best_threshold(
    win_values,
    loss_values,
    favorable,
):
    if not win_values or not loss_values:
        return None

    all_values = sorted(
        set(win_values + loss_values)
    )

    if len(all_values) == 1:
        return {
            "threshold": all_values[0],
            "balanced_accuracy": 0.5,
            "sensitivity": 0.5,
            "specificity": 0.5,
        }

    thresholds = [
        (
            all_values[index]
            + all_values[index + 1]
        ) / 2
        for index in range(len(all_values) - 1)
    ]

    best = None

    median_center = (
        describe(win_values)["median"]
        + describe(loss_values)["median"]
    ) / 2

    for threshold in thresholds:
        result = calculate_balanced_accuracy(
            win_values,
            loss_values,
            threshold,
            favorable,
        )

        candidate = {
            "threshold": threshold,
            **result,
        }

        if best is None:
            best = candidate
            continue

        current_accuracy = candidate["balanced_accuracy"]
        best_accuracy = best["balanced_accuracy"]

        if current_accuracy > best_accuracy:
            best = candidate

        elif current_accuracy == best_accuracy:
            current_distance = abs(
                threshold - median_center
            )

            best_distance = abs(
                best["threshold"] - median_center
            )

            if current_distance < best_distance:
                best = candidate

    return best


# ============================================================
# FIABILITÉ
# ============================================================

def calculate_reliability(
    n_wins,
    n_losses,
    delta,
    balanced_accuracy,
    overlap,
    direction_matches,
    bootstrap=None,
):
    """
    Indicateur interne ZiRcoN Coach.

    Ce n'est PAS une probabilité statistique.
    """
    total_games = n_wins + n_losses
    smallest_group = min(n_wins, n_losses)

    # 25 points : taille totale.
    sample_score = min(
        total_games / 80,
        1,
    ) * 25

    # 10 points : taille du plus petit groupe.
    group_score = min(
        smallest_group / 25,
        1,
    ) * 10

    # 20 points : taille d'effet.
    effect_score = min(
        abs(delta) / 0.474,
        1,
    ) * 20

    # 20 points : qualité du seuil.
    accuracy_strength = (
        balanced_accuracy - 0.5
    ) / 0.25

    accuracy_strength = max(
        0,
        min(accuracy_strength, 1),
    )

    accuracy_score = accuracy_strength * 20

    # 10 points : faible chevauchement.
    overlap_score = (1 - overlap) * 10

    # 15 points : stabilité bootstrap.
    bootstrap_score = 0

    if bootstrap is not None:
        low = bootstrap["aligned_delta_ci_low"]
        high = bootstrap["aligned_delta_ci_high"]

        if low >= 0.147:
            bootstrap_score = 15

        elif low > 0:
            bootstrap_score = 12

        elif high <= 0:
            bootstrap_score = 0

        else:
            bootstrap_score = 5

    total = (
        sample_score
        + group_score
        + effect_score
        + accuracy_score
        + overlap_score
        + bootstrap_score
    )

    if not direction_matches:
        total *= 0.45

    # --------------------------------------------------------
    # CAP DE FIABILITÉ SELON LE PLUS PETIT GROUPE
    # --------------------------------------------------------
    # Un bootstrap ne crée pas de nouvelles informations.
    # Avec 4 wins et 9 losses, un Delta parfait peut rester
    # extrêmement instable. On empêche donc les petits
    # échantillons d'être étiquetés "très fiables".
    if smallest_group < 5:
        total = min(total, 50)

    elif smallest_group < 8:
        total = min(total, 62)

    elif smallest_group < 12:
        total = min(total, 72)

    elif smallest_group < 20:
        total = min(total, 85)

    return max(
        0,
        min(total, 100),
    )


def reliability_label(score):
    if score < 35:
        return "FAIBLE"

    if score < 60:
        return "MOYENNE"

    if score < 80:
        return "ÉLEVÉE"

    return "TRÈS ÉLEVÉE"


# ============================================================
# BENCHMARK D'UNE FEATURE
# ============================================================

def build_feature_benchmark(
    dataset,
    feature,
    start_min,
    end_min,
    champion=None,
):
    config = FEATURE_CONFIG[feature]
    favorable = config["favorable"]

    win_values = get_feature_values(
        dataset,
        feature,
        start_min,
        end_min,
        champion=champion,
        win=True,
    )

    loss_values = get_feature_values(
        dataset,
        feature,
        start_min,
        end_min,
        champion=champion,
        win=False,
    )

    if len(win_values) < 3 or len(loss_values) < 3:
        return {
            "status": "INSUFFICIENT_DATA",
            "feature": feature,
            "label": config["label"],
            "category": config["category"],
            "scope": config["scope"],
            "start_min": start_min,
            "end_min": end_min,
            "champion": champion,
            "n_wins": len(win_values),
            "n_losses": len(loss_values),
        }

    win_stats = describe(win_values)
    loss_stats = describe(loss_values)
    all_values = win_values + loss_values
    all_stats = describe(all_values)

    delta = cliffs_delta(
        win_values,
        loss_values,
    )

    effect = cliff_effect_label(delta)

    if win_stats["median"] > loss_stats["median"]:
        observed_direction = "higher"
    elif win_stats["median"] < loss_stats["median"]:
        observed_direction = "lower"
    else:
        observed_direction = "equal"

    direction_matches = (
        observed_direction == favorable
    )

    if favorable == "higher":
        aligned_delta = delta
    else:
        aligned_delta = -delta

    threshold_result = find_best_threshold(
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
            feature,
            start_min,
            end_min,
            champion,
        ),
    )

    reliability = calculate_reliability(
        len(win_values),
        len(loss_values),
        delta,
        threshold_result["balanced_accuracy"],
        overlap,
        direction_matches,
        bootstrap=bootstrap,
    )

    return {
        "status": "OK",

        "feature": feature,
        "label": config["label"],
        "category": config["category"],
        "scope": config["scope"],
        "favorable": favorable,

        "start_min": start_min,
        "end_min": end_min,
        "champion": champion,

        "n_wins": len(win_values),
        "n_losses": len(loss_values),
        "n_total": len(win_values) + len(loss_values),

        "wins": win_stats,
        "losses": loss_stats,
        "all": all_stats,

        "cliffs_delta": delta,
        "aligned_delta": aligned_delta,
        "effect": effect,

        "observed_direction": observed_direction,
        "direction_matches": direction_matches,

        "iqr_overlap": overlap,

        "threshold": threshold_result["threshold"],
        "balanced_accuracy": threshold_result["balanced_accuracy"],
        "sensitivity": threshold_result["sensitivity"],
        "specificity": threshold_result["specificity"],

        "bootstrap": bootstrap,

        "reliability_score": reliability,
        "reliability": reliability_label(reliability),
    }


def build_all_benchmarks(
    dataset,
    champion=None,
):
    windows = sorted(
        {
            (
                row["start_min"],
                row["end_min"],
            )
            for row in dataset
        }
    )

    benchmarks = []

    for start_min, end_min in windows:
        for feature in FEATURE_CONFIG:
            benchmarks.append(
                build_feature_benchmark(
                    dataset,
                    feature,
                    start_min,
                    end_min,
                    champion=champion,
                )
            )

    return benchmarks


# ============================================================
# RANKING
# ============================================================

def benchmark_signal_score(benchmark):
    if benchmark.get("status") != "OK":
        return 0

    if not benchmark["direction_matches"]:
        return 0

    delta_strength = max(
        0,
        benchmark["aligned_delta"],
    )

    reliability = (
        benchmark["reliability_score"]
        / 100
    )

    accuracy = max(
        0,
        (
            benchmark["balanced_accuracy"]
            - 0.5
        ) * 2
    )

    bootstrap_factor = 1.0

    bootstrap = benchmark.get("bootstrap")

    if bootstrap is not None:
        if bootstrap["aligned_delta_ci_high"] <= 0:
            bootstrap_factor = 0.0

        elif bootstrap["aligned_delta_ci_low"] <= 0:
            bootstrap_factor = 0.65

    return (
        delta_strength
        * reliability
        * accuracy
        * bootstrap_factor
        * 100
    )


def rank_benchmarks(
    benchmarks,
    minimum_reliability=30,
):
    valid = []

    for benchmark in benchmarks:
        if benchmark.get("status") != "OK":
            continue

        if (
            benchmark["reliability_score"]
            < minimum_reliability
        ):
            continue

        benchmark = dict(benchmark)

        benchmark["signal_score"] = (
            benchmark_signal_score(
                benchmark
            )
        )

        valid.append(benchmark)

    return sorted(
        valid,
        key=lambda row: row["signal_score"],
        reverse=True,
    )


# ============================================================
# BENCHMARK HIÉRARCHIQUE
# ============================================================

def _blend_stats(
    champion_stats,
    global_stats,
    champion_weight,
):
    if not champion_stats:
        return global_stats

    if not global_stats:
        return champion_stats

    global_weight = 1 - champion_weight

    result = dict(champion_stats)

    for key in (
        "mean",
        "median",
        "q25",
        "q50",
        "q75",
        "iqr",
        "std",
    ):
        result[key] = (
            champion_weight * champion_stats[key]
            + global_weight * global_stats[key]
        )

    return result


def build_hierarchical_benchmark(
    dataset,
    feature,
    start_min,
    end_min,
    champion,
):
    """
    >= 30 games champion : benchmark champion.
    10-29 games           : benchmark hybride.
    < 10 games            : benchmark Jungle global.
    """
    global_benchmark = build_feature_benchmark(
        dataset,
        feature,
        start_min,
        end_min,
        champion=None,
    )

    champion_games = count_unique_games(
        dataset,
        champion=champion,
    )

    champion_benchmark = build_feature_benchmark(
        dataset,
        feature,
        start_min,
        end_min,
        champion=champion,
    )

    if (
        champion_games >= 30
        and champion_benchmark.get("status") == "OK"
    ):
        source = "CHAMPION"
        selected = champion_benchmark
        champion_weight = 1.0
        global_weight = 0.0

    elif (
        champion_games >= 10
        and champion_benchmark.get("status") == "OK"
        and global_benchmark.get("status") == "OK"
    ):
        source = "HYBRIDE"

        # Shrinkage progressif vers le profil Jungle.
        champion_weight = (
            champion_games
            / (champion_games + 20)
        )

        global_weight = 1 - champion_weight

        selected = dict(champion_benchmark)

        for key in (
            "threshold",
            "reliability_score",
            "balanced_accuracy",
            "aligned_delta",
            "iqr_overlap",
        ):
            selected[key] = (
                champion_weight * champion_benchmark[key]
                + global_weight * global_benchmark[key]
            )

        selected["wins"] = _blend_stats(
            champion_benchmark["wins"],
            global_benchmark["wins"],
            champion_weight,
        )

        selected["losses"] = _blend_stats(
            champion_benchmark["losses"],
            global_benchmark["losses"],
            champion_weight,
        )

        selected["all"] = _blend_stats(
            champion_benchmark["all"],
            global_benchmark["all"],
            champion_weight,
        )

        selected["effect"] = cliff_effect_label(
            selected["aligned_delta"]
        )

        selected["direction_matches"] = (
            selected["aligned_delta"] > 0
        )

        selected["reliability"] = reliability_label(
            selected["reliability_score"]
        )

        # En hybride, on garde le bootstrap champion pour transparence,
        # mais on ne le présente pas comme un IC formel du mélange.
        selected["bootstrap"] = (
            champion_benchmark.get("bootstrap")
        )

    else:
        source = "JUNGLE_GLOBAL"
        selected = global_benchmark
        champion_weight = 0.0
        global_weight = 1.0

    return {
        "source": source,
        "champion": champion,
        "champion_games": champion_games,
        "champion_weight": champion_weight,
        "global_weight": global_weight,
        "benchmark": selected,
        "champion_benchmark": champion_benchmark,
        "global_benchmark": global_benchmark,
    }
