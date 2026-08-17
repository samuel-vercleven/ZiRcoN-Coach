from collections import defaultdict

from analysis.validation_engine import (
    apply_bh_fdr,
    build_feature_validation,
    spearman_correlation,
)


REDUNDANCY_THRESHOLD = 0.80


MEASUREMENT_CORE_FEATURES = (
    "mean_post_reset_player_xp_per_min",
    "mean_post_reset_player_jungle_cs_per_min",
    "mean_post_reset_relative_gold_per_min",
    "mean_post_reset_relative_xp_per_min",
    "mean_post_reset_relative_jungle_cs_per_min",
)


FEATURE_CONFIG = {
    # ========================================================
    # PERSONAL - REENTRY MEASUREMENT
    # ========================================================
    "mean_post_reset_player_xp_per_min": {
        "label": "XP personnelle/min après reset volontaire",
        "category": "REENTRY",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "mean_post_reset_player_jungle_cs_per_min": {
        "label": "Jungle CS/min après reset volontaire",
        "category": "REENTRY",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "mean_post_reset_relative_gold_per_min": {
        "label": "Gold vs JGL/min après reset volontaire",
        "category": "REENTRY RELATIF",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "mean_post_reset_relative_xp_per_min": {
        "label": "XP vs JGL/min après reset volontaire",
        "category": "REENTRY RELATIF",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "mean_post_reset_relative_jungle_cs_per_min": {
        "label": "Jungle CS vs JGL/min après reset volontaire",
        "category": "REENTRY RELATIF",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "post_reset_death_120_rate": {
        "label": "Death <=120s après reset volontaire",
        "category": "REENTRY RISK",
        "family": "PERSONAL_RAW",
        "scope": "PERSONNEL",
        "favorable": "lower",
        "derived": False,
    },

    # ========================================================
    # COMPOSITES - EXPLANATION ONLY
    # ========================================================
    "mean_reentry_score": {
        "label": "Reentry Score moyen",
        "category": "COMPOSITE",
        "family": "COMPOSITE",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": True,
    },
    "low_reentry_rate": {
        "label": "Part des ré-entrées <25/100",
        "category": "COMPOSITE",
        "family": "COMPOSITE",
        "scope": "PERSONNEL",
        "favorable": "lower",
        "derived": True,
    },
    "mean_frozen_post_tempo_score": {
        "label": "Tempo v17 moyen après reset",
        "category": "COMPOSITE TEMPO",
        "family": "COMPOSITE",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": True,
    },
    "mean_frozen_tempo_score_change": {
        "label": "Variation Tempo v17 autour du reset",
        "category": "COMPOSITE TEMPO",
        "family": "COMPOSITE",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": True,
    },

    # ========================================================
    # CONTEXT - NEVER PERSONAL CORE
    # ========================================================
    "death_shop_rate": {
        "label": "Part des shops après death",
        "category": "DEATH CONTEXT",
        "family": "CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "lower",
        "derived": False,
    },
    "tight_pre_objective_reset_rate": {
        "label": "Resets <=45s avant objectif",
        "category": "OBJECTIVE TIMING CONTEXT",
        "family": "CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "lower",
        "derived": False,
    },
    "pre_objective_reset_rate": {
        "label": "Resets <=120s avant objectif",
        "category": "OBJECTIVE TIMING CONTEXT",
        "family": "CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "lower",
        "derived": False,
    },
    "post_objective_reset_rate": {
        "label": "Resets <=90s après objectif",
        "category": "OBJECTIVE TIMING CONTEXT",
        "family": "CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "higher",
        "derived": False,
    },
    "mirrored_reset_rate": {
        "label": "Reset du JGL adverse à +/-120s",
        "category": "MIRRORED CONTEXT",
        "family": "CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "higher",
        "derived": False,
    },
    "high_unspent_gold_context_rate": {
        "label": "Current Gold >=1500 avant reset (frame proxy)",
        "category": "EXPLORATORY GOLD CONTEXT",
        "family": "EXPLORATORY",
        "scope": "EXPLORATOIRE",
        "favorable": "lower",
        "derived": False,
    },
    "median_pre_current_gold_voluntary": {
        "label": "Current Gold médian avant reset volontaire",
        "category": "EXPLORATORY GOLD CONTEXT",
        "family": "EXPLORATORY",
        "scope": "EXPLORATOIRE",
        "favorable": "lower",
        "derived": False,
    },
}


PHASE_FEATURES = {
    key: config
    for key, config in FEATURE_CONFIG.items()
    if key in {
        "mean_post_reset_player_xp_per_min",
        "mean_post_reset_player_jungle_cs_per_min",
        "mean_post_reset_relative_gold_per_min",
        "mean_post_reset_relative_xp_per_min",
        "mean_post_reset_relative_jungle_cs_per_min",
        "post_reset_death_120_rate",
        "mean_reentry_score",
        "tight_pre_objective_reset_rate",
    }
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
                benchmark["redundant_with"].append({
                    "label": chosen["label"],
                    "rho": rho,
                })
                redundant = True
                break

        if not redundant:
            benchmark["outcome_core"] = True
            selected.append(benchmark)


def build_reset_benchmarks(game_dataset):
    benchmarks = []

    for feature, config in FEATURE_CONFIG.items():
        benchmark = build_feature_validation(
            game_dataset,
            feature,
            config,
            seed_namespace="RESET_V21",
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


def build_reset_phase_benchmarks(phase_dataset):
    phases = sorted({row["phase"] for row in phase_dataset})
    benchmarks = []

    for phase in phases:
        rows = [row for row in phase_dataset if row["phase"] == phase]
        phase_benchmarks = []

        for feature, config in PHASE_FEATURES.items():
            phase_config = {
                **config,
                "label": f"{phase} - {config['label']}",
                "category": f"{phase} / {config['category']}",
            }

            benchmark = build_feature_validation(
                rows,
                feature,
                phase_config,
                seed_namespace=f"RESET_V21_{phase}",
            )
            benchmark["phase"] = phase
            benchmark["family"] = f"RESET_PHASE_{phase}"
            phase_benchmarks.append(benchmark)

        apply_bh_fdr([
            benchmark
            for benchmark in phase_benchmarks
            if benchmark.get("status") == "OK"
        ])

        for benchmark in phase_benchmarks:
            benchmark["outcome_robust_signal"] = _outcome_robust(benchmark)
            benchmark["signal_score"] = _signal_score(benchmark)

        benchmarks.extend(phase_benchmarks)

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


def render_reset_validation(game_dataset, benchmarks):
    wins = sum(row["win"] for row in game_dataset)
    losses = len(game_dataset) - wins

    outcome_core = [row for row in benchmarks if row.get("outcome_core")]
    composites = [
        row
        for row in benchmarks
        if row.get("derived") and row.get("outcome_robust_signal")
    ]
    context = [
        row
        for row in benchmarks
        if row.get("scope") == "CONTEXTE" and row.get("status") == "OK"
    ]
    exploratory = [
        row
        for row in benchmarks
        if row.get("scope") == "EXPLORATOIRE" and row.get("status") == "OK"
    ]

    lines = [
        "================================",
        "RECALL / RESET ANALYZER - VALIDATION V21",
        "================================",
        "",
        f"Une observation outcome = une game : {len(game_dataset)}",
        f"N Win/Loss : {wins} / {losses}",
        "",
        "IMPORTANT : le module mesure des SHOP/RESET PROXY, pas des recalls exacts.",
        "CORE DE MESURE = qualité de ré-entrée observée après un reset volontaire proxy.",
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

    if not composites:
        lines.append("Aucun composite robuste.")
    else:
        for benchmark in composites:
            lines.extend(_render_benchmark(benchmark))

    lines.extend([
        "",
        "--------------------------------",
        "CONTEXTE TIMING / OBJECTIFS",
        "NON ATTRIBUÉ AUTOMATIQUEMENT AU JOUEUR",
        "--------------------------------",
    ])

    for benchmark in context:
        lines.extend(_render_benchmark(benchmark))

    lines.extend([
        "",
        "--------------------------------",
        "EXPLORATOIRE - CURRENT GOLD",
        "--------------------------------",
        "Le currentGold vient d'une frame Riot <=75s et n'est pas un coût exact.",
    ])

    for benchmark in exploratory:
        lines.extend(_render_benchmark(benchmark))

    return "\n".join(lines)


def render_reset_phase_validation(benchmarks):
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
        "RECALL / RESET ANALYZER - VALIDATION PAR PHASE V21",
        "================================",
        "",
        "Une observation = une game x phase contenant >=1 reset volontaire proxy.",
        "FDR est appliqué séparément dans chaque phase.",
        "",
        "--------------------------------",
        "SIGNAUX PAR PHASE ROBUSTES",
        "--------------------------------",
    ]

    if not robust:
        lines.append("Aucun signal par phase ne passe encore tous les critères.")
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
        lines.append("Aucun signal prometteur supplémentaire.")
    else:
        for benchmark in promising:
            lines.extend(_render_benchmark(benchmark))

    return "\n".join(lines)
