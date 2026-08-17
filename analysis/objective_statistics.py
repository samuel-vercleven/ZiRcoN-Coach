from collections import defaultdict

from analysis.validation_engine import (
    apply_bh_fdr,
    build_feature_validation,
    spearman_correlation,
)


REDUNDANCY_THRESHOLD = 0.80


MEASUREMENT_CORE_FEATURES = (
    "pre_objective_death_60_rate",
    "mean_prep_player_xp_per_min",
    "mean_prep_player_jungle_cs_per_min",
    "mean_prep_relative_xp_per_min",
    "mean_prep_relative_jungle_cs_per_min",
    "mean_conversion_relative_gold_per_min",
    "mean_conversion_relative_xp_per_min",
    "mean_conversion_relative_jungle_cs_per_min",
)


FEATURE_CONFIG = {
    # ========================================================
    # PERSONAL - AVAILABILITY
    # ========================================================
    "pre_objective_death_60_rate": {
        "label": "Morts <60s avant objectif / opportunité",
        "category": "AVAILABILITY",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "lower",
        "derived": False,
    },
    "pre_objective_death_120_rate": {
        "label": "Morts <120s avant objectif / opportunité",
        "category": "AVAILABILITY",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "lower",
        "derived": False,
    },

    # ========================================================
    # PERSONAL - PREPARATION
    # ========================================================
    "mean_prep_player_xp_per_min": {
        "label": "XP personnelle/min avant objectifs",
        "category": "PREPARATION",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "mean_prep_player_jungle_cs_per_min": {
        "label": "Jungle CS/min avant objectifs",
        "category": "PREPARATION",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "mean_prep_relative_gold_per_min": {
        "label": "Gold vs JGL/min avant objectifs",
        "category": "PREPARATION",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "mean_prep_relative_xp_per_min": {
        "label": "XP vs JGL/min avant objectifs",
        "category": "PREPARATION",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "mean_prep_relative_jungle_cs_per_min": {
        "label": "Jungle CS vs JGL/min avant objectifs",
        "category": "PREPARATION",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },

    # ========================================================
    # PERSONAL - CONVERSION
    # ========================================================
    "mean_conversion_player_xp_per_min": {
        "label": "XP personnelle/min après objectifs",
        "category": "CONVERSION",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "mean_conversion_player_jungle_cs_per_min": {
        "label": "Jungle CS/min après objectifs",
        "category": "CONVERSION",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "mean_conversion_relative_gold_per_min": {
        "label": "Gold vs JGL/min après objectifs",
        "category": "CONVERSION",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "mean_conversion_relative_xp_per_min": {
        "label": "XP vs JGL/min après objectifs",
        "category": "CONVERSION",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "mean_conversion_relative_jungle_cs_per_min": {
        "label": "Jungle CS vs JGL/min après objectifs",
        "category": "CONVERSION",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },

    # ========================================================
    # COMPOSITES - EXPLANATION ONLY
    # ========================================================
    "mean_preparation_score": {
        "label": "Preparation Score moyen",
        "category": "COMPOSITE",
        "family": "COMPOSITE",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": True,
    },
    "low_preparation_rate": {
        "label": "Part des objectifs avec préparation <25/100",
        "category": "COMPOSITE",
        "family": "COMPOSITE",
        "scope": "PERSONNEL",
        "favorable": "lower",
        "derived": True,
    },
    "mean_conversion_score": {
        "label": "Conversion Score moyen",
        "category": "COMPOSITE",
        "family": "COMPOSITE",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": True,
    },
    "mean_frozen_pre_tempo_score": {
        "label": "Tempo v17 moyen avant objectifs",
        "category": "COMPOSITE TEMPO",
        "family": "COMPOSITE",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": True,
    },
    "mean_frozen_post_tempo_score": {
        "label": "Tempo v17 moyen après objectifs",
        "category": "COMPOSITE TEMPO",
        "family": "COMPOSITE",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": True,
    },
    "mean_frozen_tempo_score_change": {
        "label": "Variation Tempo v17 autour des objectifs",
        "category": "COMPOSITE TEMPO",
        "family": "COMPOSITE",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": True,
    },

    # ========================================================
    # TEAM / SEQUENCE CONTEXT - NEVER PERSONAL CORE
    # ========================================================
    "ally_objective_rate": {
        "label": "Taux d'objectifs sécurisés par l'équipe",
        "category": "TEAM CONTEXT",
        "family": "TEAM_CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "higher",
        "derived": False,
    },
    "contest_high_medium_rate": {
        "label": "Part des objectifs avec contest evidence",
        "category": "CONTEST CONTEXT",
        "family": "TEAM_CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "higher",
        "derived": False,
    },
    "lost_with_compensation_rate": {
        "label": "Objectifs perdus avec compensation détectée",
        "category": "TRADE CONTEXT",
        "family": "TEAM_CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "higher",
        "derived": False,
    },
    "player_secured_objective_count": {
        "label": "Objectifs last-hit par le joueur",
        "category": "SECURE CONTEXT",
        "family": "TEAM_CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "higher",
        "derived": False,
    },
}


FAMILY_FEATURES = {
    key: config
    for key, config in FEATURE_CONFIG.items()
    if config["scope"] == "PERSONNEL"
}


def _apply_family_fdr(benchmarks):
    grouped = defaultdict(list)

    for benchmark in benchmarks:
        if benchmark.get("status") != "OK":
            continue
        grouped[benchmark.get("family", "OTHER")].append(benchmark)

    for rows in grouped.values():
        apply_bh_fdr(rows)


def _outcome_robust(benchmark):
    if benchmark.get("status") != "OK":
        return False

    cv = benchmark.get("cross_validation")
    walk = benchmark.get("walk_forward")
    bootstrap = benchmark.get("bootstrap")

    return (
        benchmark.get("direction_matches")
        and benchmark.get("aligned_delta", 0) >= 0.33
        and bootstrap is not None
        and bootstrap.get("aligned_delta_ci_low", 0) > 0
        and cv is not None
        and cv.get("balanced_accuracy", 0) >= 0.60
        and walk is not None
        and walk.get("balanced_accuracy", 0) >= 0.60
        and benchmark.get("fdr_q") is not None
        and benchmark["fdr_q"] <= 0.05
        and benchmark.get("reliability_score", 0) >= 60
    )


def _signal_score(benchmark):
    if not benchmark.get("outcome_robust_signal"):
        return 0.0

    cv = benchmark["cross_validation"]["balanced_accuracy"]
    walk = benchmark["walk_forward"]["balanced_accuracy"]
    validation = max(0.0, (min(cv, walk) - 0.5) * 2)

    return (
        benchmark["aligned_delta"]
        * benchmark["reliability_score"] / 100
        * validation
        * 100
    )


def _dedupe_outcome_core(dataset, benchmarks):
    candidates = [
        benchmark
        for benchmark in benchmarks
        if (
            benchmark.get("scope") == "PERSONNEL"
            and not benchmark.get("derived")
            and benchmark.get("outcome_robust_signal")
        )
    ]

    for benchmark in benchmarks:
        benchmark["outcome_core"] = False
        benchmark["redundant_with"] = []

    for index, first in enumerate(candidates):
        for second in candidates[index + 1:]:
            rho = spearman_correlation(
                dataset,
                first["feature"],
                second["feature"],
            )

            if rho is not None and abs(rho) >= REDUNDANCY_THRESHOLD:
                first["redundant_with"].append({
                    "label": second["label"],
                    "rho": rho,
                })
                second["redundant_with"].append({
                    "label": first["label"],
                    "rho": rho,
                })

    selected = []

    for benchmark in sorted(
        candidates,
        key=lambda row: row.get("signal_score", 0),
        reverse=True,
    ):
        redundant = False

        for chosen in selected:
            rho = spearman_correlation(
                dataset,
                benchmark["feature"],
                chosen["feature"],
            )

            if rho is not None and abs(rho) >= REDUNDANCY_THRESHOLD:
                redundant = True
                break

        if not redundant:
            benchmark["outcome_core"] = True
            selected.append(benchmark)


def build_objective_benchmarks(game_dataset):
    benchmarks = []

    for feature, config in FEATURE_CONFIG.items():
        benchmark = build_feature_validation(
            game_dataset,
            feature,
            config,
            seed_namespace="OBJECTIVE_V18",
        )
        benchmark["family"] = config["family"]
        benchmark["measurement_core"] = feature in MEASUREMENT_CORE_FEATURES
        benchmarks.append(benchmark)

    _apply_family_fdr(benchmarks)

    for benchmark in benchmarks:
        benchmark["outcome_robust_signal"] = _outcome_robust(benchmark)
        benchmark["signal_score"] = _signal_score(benchmark)

    _dedupe_outcome_core(game_dataset, benchmarks)
    return benchmarks


def build_objective_family_benchmarks(family_game_dataset):
    families = sorted({
        row["objective_family"]
        for row in family_game_dataset
    })

    benchmarks = []

    for family in families:
        family_rows = [
            row
            for row in family_game_dataset
            if row["objective_family"] == family
        ]

        family_benchmarks = []

        for feature, config in FAMILY_FEATURES.items():
            family_config = {
                **config,
                "label": f"{family} - {config['label']}",
                "category": f"{family} / {config['category']}",
            }

            benchmark = build_feature_validation(
                family_rows,
                feature,
                family_config,
                seed_namespace=f"OBJECTIVE_V18_{family}",
            )

            benchmark["objective_family"] = family
            benchmark["family"] = f"OBJECTIVE_{family}"
            benchmark["measurement_core"] = feature in MEASUREMENT_CORE_FEATURES
            family_benchmarks.append(benchmark)

        apply_bh_fdr([
            benchmark
            for benchmark in family_benchmarks
            if benchmark.get("status") == "OK"
        ])

        for benchmark in family_benchmarks:
            benchmark["outcome_robust_signal"] = _outcome_robust(benchmark)
            benchmark["signal_score"] = _signal_score(benchmark)

        benchmarks.extend(family_benchmarks)

    return benchmarks


def _format_value(value):
    if value is None:
        return "N/A"
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def _render_benchmark(benchmark):
    lines = [
        "",
        f"{benchmark['label']} [{benchmark['category']}]"
        + (" | COMPOSITE" if benchmark.get("derived") else ""),
        f"N Win/Loss : {benchmark['n_wins']} / {benchmark['n_losses']}",
    ]

    if benchmark.get("status") != "OK":
        lines.append(f"Statut : {benchmark.get('status')}")
        return lines

    lines.extend([
        (
            f"Win médiane : {_format_value(benchmark['wins']['median'])} | "
            f"Loss médiane : {_format_value(benchmark['losses']['median'])}"
        ),
        (
            f"Cliff orienté : {benchmark['aligned_delta']:+.3f} "
            f"({benchmark['effect']})"
        ),
    ])

    cv = benchmark.get("cross_validation")
    walk = benchmark.get("walk_forward")
    bootstrap = benchmark.get("bootstrap")

    if cv:
        lines.append(
            f"CV {cv['folds']}-fold : {cv['balanced_accuracy'] * 100:.1f}%"
        )

    if walk:
        lines.append(
            f"Walk-forward : {walk['balanced_accuracy'] * 100:.1f}% "
            f"(N test={walk['n_test']})"
        )

    if bootstrap:
        lines.append(
            "IC95 Cliff : "
            f"{bootstrap['aligned_delta_ci_low']:+.3f} à "
            f"{bootstrap['aligned_delta_ci_high']:+.3f}"
        )

    if benchmark.get("fdr_q") is not None:
        lines.append(
            f"FDR q ({benchmark.get('family', 'N/A')}) : "
            f"{benchmark['fdr_q']:.4f}"
        )

    lines.append(
        f"Fiabilité : {benchmark['reliability_score']:.0f}/100 "
        f"({benchmark['reliability']})"
    )

    return lines


def render_objective_validation(game_dataset, benchmarks):
    wins = sum(row["win"] for row in game_dataset)
    losses = len(game_dataset) - wins

    outcome_core = [
        row
        for row in benchmarks
        if row.get("outcome_core")
    ]

    robust_composites = [
        row
        for row in benchmarks
        if (
            row.get("scope") == "PERSONNEL"
            and row.get("derived")
            and row.get("outcome_robust_signal")
        )
    ]

    context = [
        row
        for row in benchmarks
        if row.get("scope") == "CONTEXTE" and row.get("status") == "OK"
    ]

    lines = [
        "================================",
        "OBJECTIVE ANALYZER - VALIDATION V20",
        "================================",
        "",
        f"Une observation outcome = une game : {len(game_dataset)}",
        f"N Win/Loss : {wins} / {losses}",
        "",
        "CORE DE MESURE PERSONNEL :",
    ]

    for feature in MEASUREMENT_CORE_FEATURES:
        benchmark = next(
            (row for row in benchmarks if row["feature"] == feature),
            None,
        )
        if benchmark:
            lines.append(
                f"  - {benchmark['label']} | "
                f"N={benchmark['n_wins'] + benchmark['n_losses']}"
            )

    lines.extend([
        "",
        "Résultat objectif / taux de capture / tours = CONTEXTE D'ÉQUIPE,",
        "jamais attribué automatiquement au joueur.",
        "",
        "--------------------------------",
        "OUTCOME EVIDENCE PERSONNEL ROBUSTE",
        "--------------------------------",
    ])

    if not outcome_core:
        lines.append("Aucun signal brut personnel ne passe tous les critères.")
    else:
        for benchmark in sorted(
            outcome_core,
            key=lambda row: row.get("signal_score", 0),
            reverse=True,
        ):
            lines.extend(_render_benchmark(benchmark))

    lines.extend([
        "",
        "--------------------------------",
        "COMPOSITES ROBUSTES - EXPLICATION",
        "--------------------------------",
    ])

    if not robust_composites:
        lines.append("Aucun composite robuste.")
    else:
        for benchmark in robust_composites:
            lines.extend(_render_benchmark(benchmark))

    lines.extend([
        "",
        "--------------------------------",
        "CONTEXTE D'ÉQUIPE / SÉQUENCE",
        "NON ATTRIBUÉ AU JOUEUR",
        "--------------------------------",
    ])

    for benchmark in context:
        lines.extend(_render_benchmark(benchmark))

    return "\n".join(lines)


def render_objective_family_validation(benchmarks):
    robust = [
        row
        for row in benchmarks
        if row.get("outcome_robust_signal")
    ]

    promising = sorted(
        [
            row
            for row in benchmarks
            if (
                row.get("status") == "OK"
                and not row.get("outcome_robust_signal")
                and row.get("aligned_delta", 0) >= 0.25
            )
        ],
        key=lambda row: row.get("aligned_delta", 0),
        reverse=True,
    )[:20]

    lines = [
        "================================",
        "OBJECTIVE ANALYZER - VALIDATION PAR TYPE V20",
        "================================",
        "",
        "Une observation = une game x un type d'objectif présent dans la game.",
        "Cette vue évite de mélanger Dragon, Herald, Baron, etc.",
        "",
        "--------------------------------",
        "SIGNAUX PAR TYPE ROBUSTES",
        "--------------------------------",
    ]

    if not robust:
        lines.append("Aucun signal par type ne passe encore tous les critères.")
    else:
        for benchmark in sorted(
            robust,
            key=lambda row: row.get("signal_score", 0),
            reverse=True,
        ):
            lines.extend(_render_benchmark(benchmark))

    lines.extend([
        "",
        "--------------------------------",
        "PROMETTEURS / NON FIGÉS",
        "--------------------------------",
    ])

    if not promising:
        lines.append("Aucun.")
    else:
        for benchmark in promising:
            lines.extend(_render_benchmark(benchmark))

    return "\n".join(lines)
