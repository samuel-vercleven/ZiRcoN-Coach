from analysis.feature_engine import FEATURE_CONFIG
from analysis.benchmarks import build_hierarchical_benchmark


MIN_ACTIONABLE_RELIABILITY = 55
MIN_ACTIONABLE_BALANCED_ACCURACY = 0.60
MIN_ACTIONABLE_ALIGNED_DELTA = 0.33

MIN_STRENGTH_RELIABILITY = 50
MIN_STRENGTH_ALIGNED_DELTA = 0.147


def clamp(value, minimum, maximum):
    return max(
        minimum,
        min(value, maximum),
    )


def calculate_feature_score(value, benchmark):
    """
    50 = proche du seuil historique.
    >50 = côté favorable.
    <50 = côté défavorable.
    """
    threshold = benchmark["threshold"]
    favorable = benchmark["favorable"]

    iqr = benchmark["all"]["iqr"] or 0

    median_gap = abs(
        benchmark["wins"]["median"]
        - benchmark["losses"]["median"]
    )

    scale = max(
        iqr,
        median_gap,
        1,
    )

    if favorable == "higher":
        oriented_distance = (
            value - threshold
        ) / scale
    else:
        oriented_distance = (
            threshold - value
        ) / scale

    score = 50 + 35 * oriented_distance

    return clamp(
        score,
        0,
        100,
    )


def calculate_signal_weight(benchmark):
    reliability = (
        benchmark["reliability_score"]
        / 100
    )

    effect = max(
        0,
        benchmark["aligned_delta"],
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
            bootstrap_factor = 0.75

    return (
        reliability
        * effect
        * accuracy
        * bootstrap_factor
    )


def is_actionable_benchmark(benchmark):
    if benchmark.get("status") != "OK":
        return False

    if not benchmark.get("direction_matches", False):
        return False

    if (
        benchmark["aligned_delta"]
        < MIN_ACTIONABLE_ALIGNED_DELTA
    ):
        return False

    if (
        benchmark["reliability_score"]
        < MIN_ACTIONABLE_RELIABILITY
    ):
        return False

    if (
        benchmark["balanced_accuracy"]
        < MIN_ACTIONABLE_BALANCED_ACCURACY
    ):
        return False

    bootstrap = benchmark.get("bootstrap")

    if (
        bootstrap is not None
        and bootstrap["aligned_delta_ci_high"] <= 0
    ):
        return False

    return True


def is_strength_benchmark(benchmark):
    if benchmark.get("status") != "OK":
        return False

    if not benchmark.get("direction_matches", False):
        return False

    # Un vrai "point fort historique" doit au moins
    # présenter un effet modéré.
    if (
        benchmark["aligned_delta"]
        < 0.33
    ):
        return False

    if (
        benchmark["reliability_score"]
        < MIN_STRENGTH_RELIABILITY
    ):
        return False

    # Si l'IC95 de l'effet traverse 0, on peut dire que la
    # performance brute est bonne, mais pas que cette feature
    # est un point fort historiquement démontré.
    bootstrap = benchmark.get(
        "bootstrap"
    )

    if (
        bootstrap is not None
        and bootstrap[
            "aligned_delta_ci_low"
        ] <= 0
    ):
        return False

    return True


def _weighted_category_scores(values_by_category):
    category_scores = {}

    for category, values in values_by_category.items():
        total_weight = sum(
            weight
            for score, weight in values
        )

        if total_weight <= 0:
            continue

        weighted_score = sum(
            score * weight
            for score, weight in values
        ) / total_weight

        category_scores[category] = weighted_score

    return category_scores


def _severity_label(score):
    if score < 35:
        return "CRITIQUE"

    if score < 50:
        return "FAIBLE"

    if score < 65:
        return "MIXTE"

    if score < 80:
        return "BON"

    return "EXCELLENT"


def analyze_window(dataset, row):
    champion = row["champion"]
    start_min = row["start_min"]
    end_min = row["end_min"]

    personal_signals = []
    team_signals = []

    personal_category_values = {}
    team_category_values = {}

    for feature, config in FEATURE_CONFIG.items():
        if feature not in row:
            continue

        hierarchical = build_hierarchical_benchmark(
            dataset,
            feature,
            start_min,
            end_min,
            champion,
        )

        benchmark = hierarchical["benchmark"]

        if benchmark.get("status") != "OK":
            continue

        value = float(row[feature])

        score = calculate_feature_score(
            value,
            benchmark,
        )

        weight = calculate_signal_weight(
            benchmark
        )

        if weight <= 0:
            continue

        signal = {
            "status": "OK",
            "direction_matches": benchmark["direction_matches"],
            "feature": feature,
            "label": config["label"],
            "category": config["category"],
            "scope": config["scope"],
            "value": value,
            "score": score,
            "weight": weight,
            "threshold": benchmark["threshold"],
            "effect": benchmark["effect"],
            "cliffs_delta": benchmark["cliffs_delta"],
            "aligned_delta": benchmark["aligned_delta"],
            "balanced_accuracy": benchmark["balanced_accuracy"],
            "reliability": benchmark["reliability"],
            "reliability_score": benchmark["reliability_score"],
            "bootstrap": benchmark.get("bootstrap"),
            "source": hierarchical["source"],
            "champion_games": hierarchical["champion_games"],
        }

        category = config["category"]

        if config["scope"] == "player":
            personal_signals.append(signal)

            personal_category_values.setdefault(
                category,
                []
            ).append(
                (score, weight)
            )

        else:
            team_signals.append(signal)

            team_category_values.setdefault(
                category,
                []
            ).append(
                (score, weight)
            )

    personal_category_scores = _weighted_category_scores(
        personal_category_values
    )

    team_category_scores = _weighted_category_scores(
        team_category_values
    )

    if personal_category_scores:
        personal_score = (
            sum(personal_category_scores.values())
            / len(personal_category_scores)
        )
    else:
        personal_score = 50

    if team_category_scores:
        team_context_score = (
            sum(team_category_scores.values())
            / len(team_category_scores)
        )
    else:
        team_context_score = 50

    # Priorités : uniquement des signaux personnels suffisamment robustes.
    negative_signals = [
        signal
        for signal in personal_signals
        if (
            signal["score"] < 45
            and is_actionable_benchmark(signal)
        )
    ]

    positive_signals = [
        signal
        for signal in personal_signals
        if (
            signal["score"] > 55
            and is_strength_benchmark(signal)
        )
    ]

    team_negative_context = [
        signal
        for signal in team_signals
        if (
            signal["score"] < 45
            and is_actionable_benchmark(signal)
        )
    ]

    team_positive_context = [
        signal
        for signal in team_signals
        if (
            signal["score"] > 55
            and is_strength_benchmark(signal)
        )
    ]

    negative_signals.sort(
        key=lambda signal: (
            (50 - signal["score"])
            * signal["weight"]
        ),
        reverse=True,
    )

    positive_signals.sort(
        key=lambda signal: (
            (signal["score"] - 50)
            * signal["weight"]
        ),
        reverse=True,
    )

    team_negative_context.sort(
        key=lambda signal: (
            (50 - signal["score"])
            * signal["weight"]
        ),
        reverse=True,
    )

    team_positive_context.sort(
        key=lambda signal: (
            (signal["score"] - 50)
            * signal["weight"]
        ),
        reverse=True,
    )

    return {
        "match_id": row["match_id"],
        "champion": champion,
        "start_min": start_min,
        "end_min": end_min,
        "win": row["win"],

        "personal_score": personal_score,
        "team_context_score": team_context_score,
        "severity": _severity_label(personal_score),

        "personal_category_scores": personal_category_scores,
        "team_category_scores": team_category_scores,

        "negative_signals": negative_signals,
        "positive_signals": positive_signals,

        "team_negative_context": team_negative_context,
        "team_positive_context": team_positive_context,

        "raw_row": row,
    }


def analyze_match(dataset, match_id):
    rows = [
        row
        for row in dataset
        if row["match_id"] == match_id
    ]

    rows.sort(
        key=lambda row: row["start_min"]
    )

    return [
        analyze_window(
            dataset,
            row,
        )
        for row in rows
    ]


def find_critical_window(analyses):
    if not analyses:
        return None

    return min(
        analyses,
        key=lambda analysis:
            analysis["personal_score"],
    )


def format_value(feature, value):
    if feature in (
        "gold_diff_change",
        "gold_gained",
        "xp_diff_change",
        "xp_gained",
    ):
        return f"{value:+.0f}"

    if feature in (
        "cs_diff_change",
        "cs_gained",
    ):
        return f"{value:+.1f}"

    return f"{value:.2f}"


def _render_signal(lines, signal, prefix="-"):
    value = format_value(
        signal["feature"],
        signal["value"],
    )

    threshold = format_value(
        signal["feature"],
        signal["threshold"],
    )

    lines.append(
        f"  {prefix} {signal['label']} : {value}"
    )

    lines.append(
        f"    seuil personnel : {threshold}"
    )

    lines.append(
        f"    effet : {signal['effect']} | "
        f"fiabilité : {signal['reliability']} | "
        f"source : {signal['source']}"
    )

    bootstrap = signal.get("bootstrap")

    if bootstrap is not None:
        lines.append(
            "    IC95 Delta orienté : "
            f"{bootstrap['aligned_delta_ci_low']:+.3f} "
            f"à "
            f"{bootstrap['aligned_delta_ci_high']:+.3f}"
        )


def render_match_analysis(analyses):
    if not analyses:
        return (
            "Aucune analyse disponible "
            "pour ce match."
        )

    lines = []

    lines.append(
        "================================"
    )

    lines.append(
        "ZIRCON COACH - RAPPORT MATCH"
    )

    lines.append(
        "================================"
    )

    critical = find_critical_window(
        analyses
    )

    if critical is not None:
        lines.append("")
        lines.append(
            "Fenêtre la plus faible : "
            f"{critical['start_min']}-"
            f"{critical['end_min']} min | "
            f"{critical['personal_score']:.0f}/100 | "
            f"{critical['severity']}"
        )

    for analysis in analyses:
        lines.append("")

        lines.append(
            f"{analysis['start_min']}-"
            f"{analysis['end_min']} MIN"
        )

        lines.append(
            f"Score personnel : "
            f"{analysis['personal_score']:.0f}/100 "
            f"({analysis['severity']})"
        )

        lines.append(
            f"Contexte équipe : "
            f"{analysis['team_context_score']:.0f}/100"
        )

        if analysis["personal_category_scores"]:
            lines.append("")
            lines.append(
                "Scores personnels :"
            )

            for category, score in sorted(
                analysis[
                    "personal_category_scores"
                ].items()
            ):
                lines.append(
                    f"  {category:<10} "
                    f"{score:.0f}/100"
                )

        problems = analysis["negative_signals"][:3]

        if problems:
            lines.append("")
            lines.append(
                "Priorités personnelles :"
            )

            for signal in problems:
                _render_signal(
                    lines,
                    signal,
                    prefix="-",
                )

        strengths = analysis["positive_signals"][:2]

        if strengths:
            lines.append("")
            lines.append(
                "Points forts personnels :"
            )

            for signal in strengths:
                _render_signal(
                    lines,
                    signal,
                    prefix="+",
                )

        negative_context = (
            analysis["team_negative_context"][:2]
        )

        positive_context = (
            analysis["team_positive_context"][:2]
        )

        if negative_context or positive_context:
            lines.append("")
            lines.append(
                "Contexte d'équipe "
                "(pas attribué automatiquement au joueur) :"
            )

            for signal in negative_context:
                lines.append(
                    f"  - {signal['label']} : "
                    f"{signal['value']:.2f}"
                )

            for signal in positive_context:
                lines.append(
                    f"  + {signal['label']} : "
                    f"{signal['value']:.2f}"
                )

    return "\n".join(lines)