import random
from collections import defaultdict
from statistics import median

from analysis.benchmarks import cliffs_delta

from analysis.validation_engine import (
    apply_bh_fdr,
    build_feature_validation,
    spearman_correlation,
    stable_seed,
)


CONDITIONAL_PERMUTATIONS = 2000
REDUNDANCY_THRESHOLD = 0.80


# ============================================================
# V15 - TWO DIFFERENT QUESTIONS
# ============================================================
#
# MEASUREMENT CORE:
#   What is tempo/pathing mechanically?
#
# OUTCOME EVIDENCE:
#   Which measurements are associated with wins/losses in the
#   current personal sample?
#
# A valid tempo measurement does not need to predict victory.
# ============================================================


MEASUREMENT_CORE_GROUPS = {
    "TEMPO_GLOBAL_HORS_DEATHS": (
        "clean_relative_gold_per_min",
        "clean_relative_xp_per_min",
        "clean_relative_jungle_cs_per_min",
    ),
    "PATHING_PERSONNEL_FARMABLE": (
        "farmable_player_xp_per_min",
        "farmable_player_jungle_cs_per_min",
    ),
    "COMPARAISON_NEUTRE_MIRRORED": (
        "mirrored_relative_gold_per_min",
        "mirrored_relative_xp_per_min",
        "mirrored_relative_jungle_cs_per_min",
    ),
}


MEASUREMENT_CORE_FEATURES = tuple(
    feature
    for group in MEASUREMENT_CORE_GROUPS.values()
    for feature in group
)


TEMPO_FEATURE_CONFIG = {
    # --------------------------------------------------------
    # GLOBAL TEMPO - HORS DEATHS
    # --------------------------------------------------------
    "clean_relative_gold_per_min": {
        "label": "Gold vs JGL / min hors deaths",
        "category": "TEMPO GLOBAL",
        "family": "PRIMARY_CLEAN",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "clean_relative_xp_per_min": {
        "label": "XP vs JGL / min hors deaths",
        "category": "TEMPO GLOBAL",
        "family": "PRIMARY_CLEAN",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "clean_relative_jungle_cs_per_min": {
        "label": "Jungle CS vs JGL / min hors deaths",
        "category": "TEMPO GLOBAL",
        "family": "PRIMARY_CLEAN",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },

    # --------------------------------------------------------
    # PATHING OWN PRODUCTION
    # --------------------------------------------------------
    "farmable_player_xp_per_min": {
        "label": "XP personnelle / min FARMABLE",
        "category": "PATHING PERSONNEL",
        "family": "PRIMARY_PATHING",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "farmable_player_jungle_cs_per_min": {
        "label": "Jungle CS personnel / min FARMABLE",
        "category": "PATHING PERSONNEL",
        "family": "PRIMARY_PATHING",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },

    # --------------------------------------------------------
    # MIRRORED: direct neutral comparison, neither jungler in
    # kill/assist/death/shop during the window.
    # --------------------------------------------------------
    "mirrored_relative_gold_per_min": {
        "label": "Gold relatif / min MIRRORED",
        "category": "COMPARAISON NEUTRE",
        "family": "PRIMARY_MIRRORED",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "mirrored_relative_xp_per_min": {
        "label": "XP relative / min MIRRORED",
        "category": "COMPARAISON NEUTRE",
        "family": "PRIMARY_MIRRORED",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },
    "mirrored_relative_jungle_cs_per_min": {
        "label": "Jungle CS relatif / min MIRRORED",
        "category": "COMPARAISON NEUTRE",
        "family": "PRIMARY_MIRRORED",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": False,
    },

    # --------------------------------------------------------
    # EXPLANATION COMPOSITES
    # --------------------------------------------------------
    "mean_tempo_score": {
        "label": "Tempo Score contextualisé moyen",
        "category": "COMPOSITE",
        "family": "COMPOSITE",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": True,
    },
    "mean_pathing_score": {
        "label": "Pathing Score personnel moyen",
        "category": "COMPOSITE",
        "family": "COMPOSITE",
        "scope": "PERSONNEL",
        "favorable": "higher",
        "derived": True,
    },
    "sustained_pathing_holes_per_10": {
        "label": "Trous de pathing soutenus / 10 min",
        "category": "PATHING EPISODES",
        "family": "COMPOSITE",
        "scope": "PERSONNEL",
        "favorable": "lower",
        "derived": True,
    },

    # --------------------------------------------------------
    # QUALITY / CONTEXT
    # --------------------------------------------------------
    "clean_coverage_ratio": {
        "label": "Couverture hors deaths",
        "category": "QUALITÉ DONNÉES",
        "family": "CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "higher",
        "derived": False,
    },
    "farmable_coverage_ratio": {
        "label": "Couverture FARMABLE joueur",
        "category": "QUALITÉ DONNÉES",
        "family": "CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "higher",
        "derived": False,
    },
    "mirrored_farmable_coverage_ratio": {
        "label": "Couverture MIRRORED",
        "category": "QUALITÉ DONNÉES",
        "family": "CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "higher",
        "derived": False,
    },
    "reset_context_ratio": {
        "label": "Part du temps avec shop/reset joueur",
        "category": "RESET",
        "family": "CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "lower",
        "derived": False,
    },
    "combat_context_ratio": {
        "label": "Part du temps avec combat joueur",
        "category": "COMBAT",
        "family": "CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "higher",
        "derived": False,
    },
    "opponent_combat_context_ratio": {
        "label": "Part du temps avec combat JGL adverse",
        "category": "COMBAT",
        "family": "CONTEXT",
        "scope": "CONTEXTE",
        "favorable": "lower",
        "derived": False,
    },
}


# Phase validation deliberately tests only the measurements that can
# produce actionable coaching. STRICT_FREE is not retested because its
# coverage is too small and it is already a diagnostic high-purity view.
PHASE_FEATURE_CONFIG = {
    "phase_relative_gold_per_min": {
        "label": "Gold vs JGL / min hors deaths",
        "favorable": "higher",
        "requires": "core",
    },
    "phase_relative_xp_per_min": {
        "label": "XP vs JGL / min hors deaths",
        "favorable": "higher",
        "requires": "core",
    },
    "phase_relative_jungle_cs_per_min": {
        "label": "Jungle CS vs JGL / min hors deaths",
        "favorable": "higher",
        "requires": "core",
    },
    "phase_farmable_player_xp_per_min": {
        "label": "XP personnelle / min FARMABLE",
        "favorable": "higher",
        "requires": "farmable",
    },
    "phase_farmable_player_jungle_cs_per_min": {
        "label": "Jungle CS personnel / min FARMABLE",
        "favorable": "higher",
        "requires": "farmable",
    },
    "phase_mirrored_relative_xp_per_min": {
        "label": "XP relative / min MIRRORED",
        "favorable": "higher",
        "requires": "mirrored",
    },
    "phase_mirrored_relative_jungle_cs_per_min": {
        "label": "Jungle CS relatif / min MIRRORED",
        "favorable": "higher",
        "requires": "mirrored",
    },
}


# ============================================================
# CONDITIONAL PERMUTATION
# ============================================================


def conditional_permutation_test(
    dataset,
    feature,
    favorable,
    strata_fields,
    iterations=CONDITIONAL_PERMUTATIONS,
):
    """
    Permutation conditionnelle dans des strates pré-spécifiées.

    Pour les phases, on utilise les morts AVANT la phase et jamais les
    morts futures. Un second niveau peut aussi contrôler l'état d'entrée.
    """
    strata = defaultdict(list)

    for row in dataset:
        value = row.get(feature)

        if value is None:
            continue

        key_values = []
        missing = False

        for field in strata_fields:
            value_key = row.get(field)

            if value_key is None:
                missing = True
                break

            key_values.append(value_key)

        if missing:
            continue

        strata[
            tuple(key_values)
        ].append({
            "value": float(value),
            "win": bool(row["win"]),
        })

    informative = {}

    for key, rows in strata.items():
        has_win = any(
            row["win"]
            for row in rows
        )

        has_loss = any(
            not row["win"]
            for row in rows
        )

        if not (
            has_win
            and has_loss
        ):
            continue

        center = median(
            row["value"]
            for row in rows
        )

        informative[key] = [
            {
                "residual": (
                    row["value"]
                    - center
                ),
                "win": row["win"],
            }
            for row in rows
        ]

    n_games = sum(
        len(rows)
        for rows in informative.values()
    )

    if (
        n_games < 15
        or len(informative) < 2
    ):
        return None

    observed_wins = []
    observed_losses = []

    for rows in informative.values():
        for row in rows:
            if row["win"]:
                observed_wins.append(
                    row["residual"]
                )
            else:
                observed_losses.append(
                    row["residual"]
                )

    if (
        len(observed_wins) < 5
        or len(observed_losses) < 5
    ):
        return None

    delta = cliffs_delta(
        observed_wins,
        observed_losses,
    )

    aligned_observed = (
        delta
        if favorable == "higher"
        else -delta
    )

    if aligned_observed <= 0:
        return {
            "aligned_delta": aligned_observed,
            "p_value": 1.0,
            "n_games": n_games,
            "n_strata": len(informative),
            "strata_fields": tuple(
                strata_fields
            ),
        }

    rng = random.Random(
        stable_seed(
            "TEMPO_V15_COND",
            feature,
            *strata_fields,
        )
    )

    exceedances = 0

    for _ in range(iterations):
        perm_wins = []
        perm_losses = []

        for rows in informative.values():
            labels = [
                row["win"]
                for row in rows
            ]

            rng.shuffle(labels)

            for row, label in zip(
                rows,
                labels,
            ):
                if label:
                    perm_wins.append(
                        row["residual"]
                    )
                else:
                    perm_losses.append(
                        row["residual"]
                    )

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

    return {
        "aligned_delta": aligned_observed,
        "p_value": (
            exceedances + 1
        ) / (
            iterations + 1
        ),
        "n_games": n_games,
        "n_strata": len(informative),
        "strata_fields": tuple(
            strata_fields
        ),
    }


def _apply_family_fdr(
    benchmarks,
    p_field,
    q_field,
):
    families = defaultdict(list)

    for benchmark in benchmarks:
        if benchmark.get(
            "status"
        ) != "OK":
            continue

        p_value = benchmark.get(
            p_field
        )

        if p_value is None:
            continue

        family = benchmark.get(
            "family",
            "OTHER",
        )

        families[family].append(
            benchmark
        )

    for rows in families.values():
        apply_bh_fdr(
            rows,
            p_field=p_field,
            q_field=q_field,
        )


# ============================================================
# OUTCOME VALIDATION
# ============================================================


def _outcome_robust(
    benchmark,
):
    cv = benchmark.get(
        "cross_validation"
    )

    walk = benchmark.get(
        "walk_forward"
    )

    bootstrap = benchmark.get(
        "bootstrap"
    )

    return (
        benchmark.get("status") == "OK"
        and benchmark.get(
            "direction_matches"
        )
        and benchmark.get(
            "aligned_delta",
            0,
        ) >= 0.33
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
        and benchmark.get(
            "fdr_q"
        ) is not None
        and benchmark[
            "fdr_q"
        ] <= 0.05
        and benchmark.get(
            "reliability_score",
            0,
        ) >= 60
    )


def _signal_score(
    benchmark,
):
    if not benchmark.get(
        "outcome_robust_signal",
        False,
    ):
        return 0

    cv = benchmark[
        "cross_validation"
    ]

    walk = benchmark[
        "walk_forward"
    ]

    validation = max(
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

    return (
        benchmark[
            "aligned_delta"
        ]
        * (
            benchmark[
                "reliability_score"
            ]
            / 100
        )
        * validation
        * 100
    )


def build_tempo_benchmarks(
    game_dataset,
):
    benchmarks = []

    for feature, config in (
        TEMPO_FEATURE_CONFIG.items()
    ):
        benchmark = (
            build_feature_validation(
                game_dataset,
                feature,
                config,
                seed_namespace="TEMPO_V15",
            )
        )

        benchmark[
            "family"
        ] = config[
            "family"
        ]

        benchmark[
            "measurement_core"
        ] = (
            feature
            in MEASUREMENT_CORE_FEATURES
        )

        benchmarks.append(
            benchmark
        )

    _apply_family_fdr(
        benchmarks,
        p_field="permutation_p",
        q_field="fdr_q",
    )

    for benchmark in benchmarks:
        if benchmark.get(
            "status"
        ) != "OK":
            continue

        benchmark[
            "outcome_robust_signal"
        ] = _outcome_robust(
            benchmark
        )

        benchmark[
            "signal_score"
        ] = 0

    for benchmark in benchmarks:
        if benchmark.get(
            "status"
        ) != "OK":
            continue

        benchmark[
            "signal_score"
        ] = _signal_score(
            benchmark
        )

        benchmark[
            "total_death_sensitivity"
        ] = None
        benchmark[
            "total_death_sensitivity_p"
        ] = None
        benchmark[
            "total_death_sensitivity_q"
        ] = None

        # Expensive conditional sensitivity is run only for the
        # measurement core and already-robust outcome signals.
        should_test = (
            benchmark.get(
                "measurement_core"
            )
            or benchmark.get(
                "outcome_robust_signal"
            )
        )

        if (
            should_test
            and benchmark.get(
                "scope"
            ) == "PERSONNEL"
        ):
            sensitivity = (
                conditional_permutation_test(
                    game_dataset,
                    benchmark[
                        "feature"
                    ],
                    benchmark[
                        "favorable"
                    ],
                    strata_fields=(
                        "player_deaths",
                    ),
                )
            )

            benchmark[
                "total_death_sensitivity"
            ] = sensitivity

            if sensitivity:
                benchmark[
                    "total_death_sensitivity_p"
                ] = sensitivity[
                    "p_value"
                ]

    _apply_family_fdr(
        benchmarks,
        p_field=(
            "total_death_sensitivity_p"
        ),
        q_field=(
            "total_death_sensitivity_q"
        ),
    )

    for benchmark in benchmarks:
        sensitivity = benchmark.get(
            "total_death_sensitivity"
        )

        q_value = benchmark.get(
            "total_death_sensitivity_q"
        )

        benchmark[
            "persists_after_total_deaths"
        ] = (
            sensitivity is not None
            and sensitivity[
                "aligned_delta"
            ] >= 0.147
            and q_value is not None
            and q_value <= 0.05
        )

    _attach_outcome_core(
        game_dataset,
        benchmarks,
    )

    return benchmarks


def _attach_outcome_core(
    game_dataset,
    benchmarks,
):
    candidates = [
        benchmark
        for benchmark in benchmarks
        if (
            benchmark.get("status") == "OK"
            and benchmark.get(
                "scope"
            ) == "PERSONNEL"
            and not benchmark.get(
                "derived",
                False,
            )
            and benchmark.get(
                "outcome_robust_signal",
                False,
            )
        )
    ]

    for benchmark in benchmarks:
        benchmark[
            "outcome_core"
        ] = False
        benchmark[
            "redundant_with"
        ] = []

    for index, first in enumerate(
        candidates
    ):
        for second in candidates[
            index + 1:
        ]:
            rho = spearman_correlation(
                game_dataset,
                first["feature"],
                second["feature"],
            )

            if (
                rho is not None
                and abs(rho)
                >= REDUNDANCY_THRESHOLD
            ):
                first[
                    "redundant_with"
                ].append({
                    "label": second[
                        "label"
                    ],
                    "rho": rho,
                })

                second[
                    "redundant_with"
                ].append({
                    "label": first[
                        "label"
                    ],
                    "rho": rho,
                })

    selected = []

    for benchmark in sorted(
        candidates,
        key=lambda row:
            row.get(
                "signal_score",
                0,
            ),
        reverse=True,
    ):
        redundant = False

        for chosen in selected:
            rho = spearman_correlation(
                game_dataset,
                benchmark["feature"],
                chosen["feature"],
            )

            if (
                rho is not None
                and abs(rho)
                >= REDUNDANCY_THRESHOLD
            ):
                redundant = True
                break

        if not redundant:
            benchmark[
                "outcome_core"
            ] = True

            selected.append(
                benchmark
            )


# ============================================================
# PHASE LEVEL - GATED VALIDATION FOR PERFORMANCE
# ============================================================


def _phase_feature_dataset(
    phase_dataset,
    phase,
    feature,
    requires,
):
    minute_key = {
        "core": "phase_core_minutes",
        "farmable": (
            "phase_farmable_minutes"
        ),
        "mirrored": (
            "phase_mirrored_minutes"
        ),
    }[
        requires
    ]

    return [
        row
        for row in phase_dataset
        if (
            row[
                "phase"
            ] == phase
            and row.get(
                minute_key,
                0,
            ) >= 1.0
            and row.get(
                feature
            ) is not None
        )
    ]


def build_phase_tempo_benchmarks(
    phase_dataset,
):
    """
    Stage 1: ordinary phase outcome validation for all pre-specified
             phase features.

    Stage 2: ONLY Stage-1 robust signals receive the expensive
             conditioning on deaths BEFORE the phase.

    Stage 3: ONLY Stage-2 survivors receive the even stricter
             deaths-before-phase + entry-state conditioning.

    Same rigor, far less useless permutation work.
    """
    phases = sorted({
        row["phase"]
        for row in phase_dataset
    })

    benchmarks = []

    for phase in phases:
        for feature, config in (
            PHASE_FEATURE_CONFIG.items()
        ):
            dataset = (
                _phase_feature_dataset(
                    phase_dataset,
                    phase,
                    feature,
                    config[
                        "requires"
                    ],
                )
            )

            validation_config = {
                "label": (
                    f"{phase} - "
                    f"{config['label']}"
                ),
                "category": (
                    f"PHASE {phase}"
                ),
                "scope": "PERSONNEL",
                "favorable": (
                    config[
                        "favorable"
                    ]
                ),
                "derived": False,
            }

            benchmark = (
                build_feature_validation(
                    dataset,
                    feature,
                    validation_config,
                    seed_namespace=(
                        f"TEMPO_PHASE_V15_"
                        f"{phase}"
                    ),
                )
            )

            benchmark[
                "phase"
            ] = phase
            benchmark[
                "phase_feature"
            ] = feature
            benchmark[
                "requires"
            ] = config[
                "requires"
            ]
            benchmark[
                "family"
            ] = (
                f"PHASE_{phase}"
            )

            benchmark[
                "prephase_death_test"
            ] = None
            benchmark[
                "prephase_death_p"
            ] = None
            benchmark[
                "prephase_death_q"
            ] = None
            benchmark[
                "prephase_state_test"
            ] = None
            benchmark[
                "prephase_state_p"
            ] = None
            benchmark[
                "prephase_state_q"
            ] = None

            benchmarks.append(
                benchmark
            )

    # Stage 1 FDR by phase.
    _apply_family_fdr(
        benchmarks,
        p_field="permutation_p",
        q_field="fdr_q",
    )

    stage1 = []

    for benchmark in benchmarks:
        if benchmark.get(
            "status"
        ) != "OK":
            continue

        benchmark[
            "outcome_robust_signal"
        ] = _outcome_robust(
            benchmark
        )

        if benchmark[
            "outcome_robust_signal"
        ]:
            stage1.append(
                benchmark
            )

    # Stage 2 only on Stage-1 robust signals.
    for benchmark in stage1:
        dataset = (
            _phase_feature_dataset(
                phase_dataset,
                benchmark[
                    "phase"
                ],
                benchmark[
                    "phase_feature"
                ],
                benchmark[
                    "requires"
                ],
            )
        )

        prephase = (
            conditional_permutation_test(
                dataset,
                benchmark[
                    "phase_feature"
                ],
                benchmark[
                    "favorable"
                ],
                strata_fields=(
                    "player_deaths_before_phase",
                ),
            )
        )

        benchmark[
            "prephase_death_test"
        ] = prephase

        if prephase:
            benchmark[
                "prephase_death_p"
            ] = prephase[
                "p_value"
            ]

    _apply_family_fdr(
        stage1,
        p_field="prephase_death_p",
        q_field="prephase_death_q",
    )

    stage2 = []

    for benchmark in stage1:
        prephase = benchmark.get(
            "prephase_death_test"
        )

        q_value = benchmark.get(
            "prephase_death_q"
        )

        benchmark[
            "persists_after_prephase_deaths"
        ] = (
            prephase is not None
            and prephase[
                "aligned_delta"
            ] >= 0.147
            and q_value is not None
            and q_value <= 0.05
        )

        if benchmark[
            "persists_after_prephase_deaths"
        ]:
            stage2.append(
                benchmark
            )

    # Stage 3 only on Stage-2 survivors.
    for benchmark in stage2:
        dataset = (
            _phase_feature_dataset(
                phase_dataset,
                benchmark[
                    "phase"
                ],
                benchmark[
                    "phase_feature"
                ],
                benchmark[
                    "requires"
                ],
            )
        )

        prephase_state = (
            conditional_permutation_test(
                dataset,
                benchmark[
                    "phase_feature"
                ],
                benchmark[
                    "favorable"
                ],
                strata_fields=(
                    "player_deaths_before_phase",
                    "phase_entry_state",
                ),
            )
        )

        benchmark[
            "prephase_state_test"
        ] = prephase_state

        if prephase_state:
            benchmark[
                "prephase_state_p"
            ] = prephase_state[
                "p_value"
            ]

    _apply_family_fdr(
        stage2,
        p_field="prephase_state_p",
        q_field="prephase_state_q",
    )

    for benchmark in benchmarks:
        benchmark[
            "persists_after_prephase_state"
        ] = False

        state = benchmark.get(
            "prephase_state_test"
        )

        q_state = benchmark.get(
            "prephase_state_q"
        )

        if (
            state is not None
            and state[
                "aligned_delta"
            ] >= 0.147
            and q_state is not None
            and q_state <= 0.05
        ):
            benchmark[
                "persists_after_prephase_state"
            ] = True

        benchmark[
            "signal_score"
        ] = 0

        if benchmark.get(
            "outcome_robust_signal"
        ):
            # _signal_score expects this flag.
            benchmark[
                "signal_score"
            ] = _signal_score(
                benchmark
            )

    return benchmarks


# ============================================================
# RENDER
# ============================================================


def _format_value(value):
    if value is None:
        return "N/A"

    if abs(value) >= 100:
        return f"{value:.0f}"

    if abs(value) >= 10:
        return f"{value:.1f}"

    return f"{value:.2f}"


def _render_validation(
    benchmark,
):
    lines = [
        "",
        (
            f"{benchmark['label']} "
            f"[{benchmark['category']}]"
            + (
                " | COMPOSITE"
                if benchmark.get(
                    "derived"
                )
                else ""
            )
        ),
        (
            f"N Win/Loss : "
            f"{benchmark['n_wins']} / "
            f"{benchmark['n_losses']}"
        ),
        (
            "Win médiane : "
            f"{_format_value(benchmark['wins']['median'])} | "
            "Loss médiane : "
            f"{_format_value(benchmark['losses']['median'])}"
        ),
        (
            "Cliff orienté : "
            f"{benchmark['aligned_delta']:+.3f} "
            f"({benchmark['effect']})"
        ),
    ]

    cv = benchmark.get(
        "cross_validation"
    )

    walk = benchmark.get(
        "walk_forward"
    )

    if cv:
        lines.append(
            (
                f"CV {cv['folds']}-fold : "
                f"{cv['balanced_accuracy'] * 100:.1f}%"
            )
        )

    if walk:
        lines.append(
            (
                "Walk-forward : "
                f"{walk['balanced_accuracy'] * 100:.1f}% "
                f"(N test={walk['n_test']})"
            )
        )

    bootstrap = benchmark.get(
        "bootstrap"
    )

    if bootstrap:
        lines.append(
            (
                "IC95 Cliff : "
                f"{bootstrap['aligned_delta_ci_low']:+.3f} "
                "à "
                f"{bootstrap['aligned_delta_ci_high']:+.3f}"
            )
        )

    if benchmark.get(
        "fdr_q"
    ) is not None:
        lines.append(
            (
                f"FDR q ({benchmark.get('family', 'N/A')}) : "
                f"{benchmark['fdr_q']:.4f}"
            )
        )

    sensitivity = benchmark.get(
        "total_death_sensitivity"
    )

    if sensitivity:
        lines.append(
            (
                "Sensibilité morts totales : "
                f"delta {sensitivity['aligned_delta']:+.3f} | "
                f"q {benchmark['total_death_sensitivity_q']:.4f}"
            )
        )

    prephase = benchmark.get(
        "prephase_death_test"
    )

    if prephase:
        lines.append(
            (
                "Morts AVANT phase : "
                f"delta {prephase['aligned_delta']:+.3f} | "
                f"q {benchmark['prephase_death_q']:.4f}"
            )
        )

    state = benchmark.get(
        "prephase_state_test"
    )

    if state:
        lines.append(
            (
                "Morts pré-phase + état entrée : "
                f"delta {state['aligned_delta']:+.3f} | "
                f"q {benchmark['prephase_state_q']:.4f}"
            )
        )

    lines.append(
        (
            "Fiabilité : "
            f"{benchmark['reliability_score']:.0f}/100 "
            f"({benchmark['reliability']})"
        )
    )

    return lines


def render_tempo_validation(
    game_dataset,
    benchmarks,
):
    wins = sum(
        1
        for row in game_dataset
        if row["win"]
    )

    losses = (
        len(game_dataset)
        - wins
    )

    by_feature = {
        row[
            "feature"
        ]: row
        for row in benchmarks
    }

    outcome_core = [
        benchmark
        for benchmark in benchmarks
        if benchmark.get(
            "outcome_core"
        )
    ]

    composites = [
        benchmark
        for benchmark in benchmarks
        if (
            benchmark.get(
                "scope"
            ) == "PERSONNEL"
            and benchmark.get(
                "derived"
            )
            and benchmark.get(
                "outcome_robust_signal"
            )
        )
    ]

    lines = [
        "================================",
        "JUNGLE TEMPO - VALIDATION V15",
        "================================",
        "",
        (
            f"Une observation outcome = une game : "
            f"{len(game_dataset)}"
        ),
        (
            f"N Win/Loss : {wins} / {losses}"
        ),
        "",
        "--------------------------------",
        "CORE DE MESURE - TEMPO GLOBAL",
        "--------------------------------",
    ]

    for group_name, features in (
        MEASUREMENT_CORE_GROUPS.items()
    ):
        lines.append("")
        lines.append(group_name)

        for feature in features:
            benchmark = by_feature.get(
                feature
            )

            if benchmark is None:
                continue

            lines.append(
                (
                    f"  - {benchmark['label']} "
                    f"| N={benchmark['n_wins'] + benchmark['n_losses']}"
                )
            )

    lines.extend([
        "",
        (
            "PATHING PERSONNEL n'utilise que la production du joueur. "
            "MIRRORED sert uniquement aux comparaisons directes des deux junglers."
        ),
        "",
        "--------------------------------",
        "OUTCOME EVIDENCE ROBUSTE",
        "--------------------------------",
    ])

    if not outcome_core:
        lines.append(
            "Aucun signal brut outcome robuste."
        )
    else:
        for benchmark in sorted(
            outcome_core,
            key=lambda row:
                row.get(
                    "signal_score",
                    0,
                ),
            reverse=True,
        ):
            lines.extend(
                _render_validation(
                    benchmark
                )
            )

    lines.extend([
        "",
        "--------------------------------",
        "COMPOSITES ROBUSTES - EXPLICATION",
        "--------------------------------",
    ])

    if not composites:
        lines.append(
            "Aucun composite robuste."
        )
    else:
        for benchmark in composites:
            lines.extend(
                _render_validation(
                    benchmark
                )
            )

    lines.extend([
        "",
        "--------------------------------",
        "SENSIBILITÉ AUX DEATHS - CORE DE MESURE",
        "--------------------------------",
        (
            "Ce test reste descriptif : ne pas confondre dépendance statistique "
            "et invalidité mécanique de la mesure."
        ),
    ])

    for feature in MEASUREMENT_CORE_FEATURES:
        benchmark = by_feature.get(
            feature
        )

        if not benchmark:
            continue

        sensitivity = benchmark.get(
            "total_death_sensitivity"
        )

        if not sensitivity:
            lines.append(
                f"- {benchmark['label']} : données conditionnelles insuffisantes"
            )
            continue

        verdict = (
            "PERSISTE"
            if benchmark.get(
                "persists_after_total_deaths"
            )
            else "NON DÉMONTRÉ"
        )

        q_value = benchmark.get(
            "total_death_sensitivity_q"
        )

        lines.append(
            (
                f"- {benchmark['label']} : {verdict} "
                f"(delta {sensitivity['aligned_delta']:+.3f}, "
                f"q {q_value:.4f})"
            )
        )

    return "\n".join(lines)


def render_phase_tempo_validation(
    phase_benchmarks,
):
    stage1 = [
        benchmark
        for benchmark in phase_benchmarks
        if benchmark.get(
            "outcome_robust_signal"
        )
    ]

    stage2 = [
        benchmark
        for benchmark in stage1
        if benchmark.get(
            "persists_after_prephase_deaths"
        )
    ]

    stage3 = [
        benchmark
        for benchmark in stage2
        if benchmark.get(
            "persists_after_prephase_state"
        )
    ]

    lines = [
        "================================",
        "JUNGLE TEMPO - VALIDATION PAR PHASE V15",
        "================================",
        "",
        (
            "Pipeline hiérarchique rapide : global phase -> morts AVANT phase -> "
            "morts pré-phase + état d'entrée."
        ),
        (
            "Les tests coûteux ne sont exécutés que sur les signaux ayant "
            "déjà passé l'étape précédente."
        ),
        "",
        "--------------------------------",
        "STAGE 1 - OUTCOME PHASE ROBUSTE",
        "--------------------------------",
    ]

    if not stage1:
        lines.append(
            "Aucun signal de phase robuste."
        )
    else:
        for benchmark in sorted(
            stage1,
            key=lambda row:
                row.get(
                    "signal_score",
                    0,
                ),
            reverse=True,
        ):
            lines.extend(
                _render_validation(
                    benchmark
                )
            )

    lines.extend([
        "",
        "--------------------------------",
        "STAGE 2 - PERSISTE APRÈS MORTS PRÉ-PHASE",
        "--------------------------------",
    ])

    if not stage2:
        lines.append(
            "Aucun signal confirmé à cette étape."
        )
    else:
        for benchmark in stage2:
            lines.extend(
                _render_validation(
                    benchmark
                )
            )

    lines.extend([
        "",
        "--------------------------------",
        "STAGE 3 - PERSISTE APRÈS ÉTAT D'ENTRÉE",
        "--------------------------------",
    ])

    if not stage3:
        lines.append(
            "Aucun signal confirmé au niveau le plus strict."
        )
    else:
        for benchmark in stage3:
            lines.extend(
                _render_validation(
                    benchmark
                )
            )

    return "\n".join(lines)
