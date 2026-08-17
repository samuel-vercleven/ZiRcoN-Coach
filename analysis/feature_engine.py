from math import floor, ceil
from statistics import mean, median, stdev


# ============================================================
# CONFIGURATION DES FEATURES
# ============================================================

FEATURE_CONFIG = {
    # TEMPO
    "gold_diff_change": {
        "label": "Variation écart Gold",
        "category": "TEMPO",
        "favorable": "higher",
        "scope": "player",
    },
    "xp_diff_change": {
        "label": "Variation écart XP",
        "category": "TEMPO",
        "favorable": "higher",
        "scope": "player",
    },
    "cs_diff_change": {
        "label": "Variation écart CS",
        "category": "TEMPO",
        "favorable": "higher",
        "scope": "player",
    },

    # FARM / ECONOMIE
    "gold_gained": {
        "label": "Gold gagné",
        "category": "FARM",
        "favorable": "higher",
        "scope": "player",
    },
    "cs_gained": {
        "label": "CS gagnés",
        "category": "FARM",
        "favorable": "higher",
        "scope": "player",
    },
    "xp_gained": {
        "label": "XP gagnée",
        "category": "FARM",
        "favorable": "higher",
        "scope": "player",
    },

    # COMBAT
    "kills": {
        "label": "Kills",
        "category": "COMBAT",
        "favorable": "higher",
        "scope": "player",
    },
    "deaths": {
        "label": "Morts",
        "category": "COMBAT",
        "favorable": "lower",
        "scope": "player",
    },
    "assists": {
        "label": "Assists",
        "category": "COMBAT",
        "favorable": "higher",
        "scope": "player",
    },

    # OBJECTIFS / CONTEXTE D'EQUIPE
    "dragons": {
        "label": "Dragons équipe",
        "category": "OBJECTIFS",
        "favorable": "higher",
        "scope": "team",
    },
    "grubs": {
        "label": "Void Grubs équipe",
        "category": "OBJECTIFS",
        "favorable": "higher",
        "scope": "team",
    },
    "heralds": {
        "label": "Heralds équipe",
        "category": "OBJECTIFS",
        "favorable": "higher",
        "scope": "team",
    },
    "barons": {
        "label": "Barons équipe",
        "category": "OBJECTIFS",
        "favorable": "higher",
        "scope": "team",
    },
    "towers": {
        "label": "Tours équipe",
        "category": "OBJECTIFS",
        "favorable": "higher",
        "scope": "team",
    },

    # RISQUE PERSONNEL
    "deaths_before_objective": {
        "label": "Morts <60s avant objectif",
        "category": "RISQUE",
        "favorable": "lower",
        "scope": "player",
    },
    "deaths_after_objective": {
        "label": "Morts <60s après objectif",
        "category": "RISQUE",
        "favorable": "lower",
        "scope": "player",
    },
    "kills_before_objective": {
        "label": "Kills <60s avant objectif",
        "category": "RISQUE",
        "favorable": "higher",
        "scope": "player",
    },
}


def percentile(values, percent):
    """Percentile avec interpolation linéaire."""
    if not values:
        return None

    ordered = sorted(float(value) for value in values)

    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * (percent / 100)
    lower = floor(position)
    upper = ceil(position)

    if lower == upper:
        return ordered[lower]

    weight = position - lower

    return (
        ordered[lower] * (1 - weight)
        + ordered[upper] * weight
    )


def percentile_rank(values, value):
    """
    Rang percentile d'une valeur.
    80 signifie que la valeur est au-dessus d'environ 80 % de l'historique.
    """
    if not values:
        return None

    values = [float(v) for v in values]
    value = float(value)

    below = sum(1 for v in values if v < value)
    equal = sum(1 for v in values if v == value)

    rank = (below + 0.5 * equal) / len(values)
    return rank * 100


def describe(values):
    """Statistiques descriptives robustes."""
    if not values:
        return None

    values = [float(value) for value in values]
    count = len(values)

    q25 = percentile(values, 25)
    q50 = percentile(values, 50)
    q75 = percentile(values, 75)

    standard_deviation = stdev(values) if count >= 2 else 0.0

    return {
        "n": count,
        "mean": mean(values),
        "median": median(values),
        "q25": q25,
        "q50": q50,
        "q75": q75,
        "iqr": q75 - q25,
        "std": standard_deviation,
        "min": min(values),
        "max": max(values),
    }


def filter_dataset(
    dataset,
    start_min=None,
    end_min=None,
    champion=None,
    win=None,
):
    results = []

    for row in dataset:
        if start_min is not None and row["start_min"] != start_min:
            continue

        if end_min is not None and row["end_min"] != end_min:
            continue

        if champion is not None and row["champion"] != champion:
            continue

        if win is not None and row["win"] != win:
            continue

        results.append(row)

    return results


def get_feature_values(
    dataset,
    feature,
    start_min,
    end_min,
    champion=None,
    win=None,
):
    rows = filter_dataset(
        dataset,
        start_min=start_min,
        end_min=end_min,
        champion=champion,
        win=win,
    )

    values = []

    for row in rows:
        value = row.get(feature)

        if value is None:
            continue

        values.append(float(value))

    return values


def count_unique_games(dataset, champion=None):
    match_ids = set()

    for row in dataset:
        if champion is not None and row["champion"] != champion:
            continue

        match_ids.add(row["match_id"])

    return len(match_ids)