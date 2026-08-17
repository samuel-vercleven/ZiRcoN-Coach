import sys
from time import perf_counter


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from riot.riot_api import (
    get_account_by_riot_id,
    get_match_ids_by_puuid,
    get_match_details,
    get_match_timeline,
)

from database.database import (
    initialize_database,
    initialize_timeline_tables,

    match_exists,
    save_match,

    filter_match_ids_by_position,

    timeline_exists,
    save_timeline,

    get_player_stats,
    get_champion_stats,

    get_timeline_snapshots,
    get_timeline_database_stats,

    get_timeline_dataset,
    aggregate_timeline_dataset,

    get_event_window_dataset,
    aggregate_event_windows,
    get_local_account_by_riot_id,
    get_local_match_ids_by_puuid,
)

from analysis.benchmarks import (
    build_all_benchmarks,
    rank_benchmarks,
)

from analysis.coaching_engine import (
    analyze_match,
    render_match_analysis,
)

from analysis.event_explainer import (
    build_critical_window_report,
)

from analysis.death_cost_analyzer import (
    build_death_cost_dataset,
    summarize_death_costs,
    build_game_death_summary_dataset,
    summarize_game_death_profiles,
    get_match_death_costs,
    render_death_cost_summary,
    render_game_level_summary,
    render_match_death_costs,
)

from analysis.death_statistics import (
    build_game_death_benchmarks,
    render_game_death_validation,
    render_v10_final_core,
    render_v11_freeze_report,
)


from database.tempo_reader import (
    load_tempo_bundles,
)

from analysis.jungle_tempo_analyzer import (
    build_tempo_intervals,
    build_game_tempo_dataset,
    build_game_phase_tempo_dataset,
    summarize_tempo_profile,
    render_tempo_profile,
    render_match_tempo_report,
    render_pathing_alert_audit,
)

from analysis.tempo_statistics import (
    build_tempo_benchmarks,
    build_phase_tempo_benchmarks,
    render_tempo_validation,
    render_phase_tempo_validation,
)

from analysis.objective_analyzer import (
    build_objective_dataset,
    build_game_objective_dataset,
    build_objective_family_game_dataset,
    summarize_objective_profile,
    render_objective_profile,
    render_objective_audit,
    render_match_objective_report,
)

from analysis.objective_statistics import (
    build_objective_benchmarks,
    build_objective_family_benchmarks,
    render_objective_validation,
    render_objective_family_validation,
)

from analysis.reset_analyzer import (
    build_reset_dataset,
    build_game_reset_dataset,
    build_reset_phase_dataset,
    summarize_reset_profile,
    render_reset_profile,
    render_reset_audit,
    render_match_reset_report,
)

from analysis.reset_statistics import (
    build_reset_benchmarks,
    build_reset_phase_benchmarks,
    render_reset_validation,
    render_reset_phase_validation,
)

from analysis.itemization_analyzer import (
    TARGET_MATCH_ID as ITEMIZATION_TARGET_MATCH_ID,
    build_itemization_history,
    render_itemization_audit,
    render_match_itemization_report,
)


# ============================================================
# CONFIGURATION
# ============================================================

GAME_NAME = "ZiRcoN1977"
TAG_LINE = "EUW"

SOLOQ_QUEUE_ID = 420
MATCH_COUNT = 100

ROLE_FILTER = "JUNGLE"
MIN_CHAMPION_GAMES = 5


# ============================================================
# AFFICHAGE TIMELINE
# ============================================================

def print_timeline_summary(
    title,
    summary,
):
    print()
    print("--------------------------------")
    print(title)
    print("--------------------------------")

    if not summary:
        print("Pas assez de données.")
        return

    for minute, stats in summary.items():
        print()

        print(
            f"{minute} MIN "
            f"({stats['games']} games)"
        )

        print(
            f"Gold moyen : "
            f"{stats['gold']:.0f}"
        )

        print(
            f"CS moyen : "
            f"{stats['cs']:.1f}"
        )

        print(
            f"Niveau moyen : "
            f"{stats['level']:.2f}"
        )

        print(
            f"Écart Gold : "
            f"{stats['gold_diff']:+.0f}"
        )

        print(
            f"Écart CS : "
            f"{stats['cs_diff']:+.1f}"
        )

        print(
            f"Écart niveau : "
            f"{stats['level_diff']:+.2f}"
        )

        print(
            f"Écart XP : "
            f"{stats['xp_diff']:+.0f}"
        )

        print(
            f"Devant en Gold : "
            f"{stats['gold_ahead_percent']:.1f}%"
        )

        print(
            f"Devant en CS : "
            f"{stats['cs_ahead_percent']:.1f}%"
        )


# ============================================================
# AFFICHAGE ÉVÉNEMENTS
# ============================================================

def print_event_summary(
    title,
    summary,
):
    print()
    print("================================")
    print(title)
    print("================================")

    if not summary:
        print("Pas assez de données.")
        return

    for (
        start_min,
        end_min,
    ), stats in summary.items():

        print()

        print(
            f"{start_min}-{end_min} MIN "
            f"({stats['games']} games)"
        )

        print()

        print(
            f"K/D/A fenêtre : "
            f"{stats['kills']:.2f} / "
            f"{stats['deaths']:.2f} / "
            f"{stats['assists']:.2f}"
        )

        print(
            f"Gold gagné : "
            f"{stats['gold_gained']:.0f}"
        )

        print(
            f"CS gagnés : "
            f"{stats['cs_gained']:.1f}"
        )

        print(
            f"XP gagnée : "
            f"{stats['xp_gained']:.0f}"
        )

        print()

        print(
            "Évolution contre le jungler adverse :"
        )

        print(
            f"Variation écart Gold : "
            f"{stats['gold_diff_change']:+.0f}"
        )

        print(
            f"Variation écart CS : "
            f"{stats['cs_diff_change']:+.1f}"
        )

        print(
            f"Variation écart XP : "
            f"{stats['xp_diff_change']:+.0f}"
        )

        print()

        print(
            f"Dragons équipe : "
            f"{stats['dragons']:.2f}"
        )

        print(
            f"Grubs équipe : "
            f"{stats['grubs']:.2f}"
        )

        print(
            f"Heralds équipe : "
            f"{stats['heralds']:.2f}"
        )

        print(
            f"Barons équipe : "
            f"{stats['barons']:.2f}"
        )

        print(
            f"Tours équipe : "
            f"{stats['towers']:.2f}"
        )

        print()

        print(
            f"Morts <60s avant objectif : "
            f"{stats['deaths_before_objective']:.2f}"
        )

        print(
            f"Morts <60s après objectif : "
            f"{stats['deaths_after_objective']:.2f}"
        )

        print(
            f"Kills <60s avant objectif : "
            f"{stats['kills_before_objective']:.2f}"
        )


# ============================================================
# AFFICHAGE BENCHMARK
# ============================================================

def print_benchmark(benchmark):
    print()

    print(
        f"{benchmark['start_min']}-"
        f"{benchmark['end_min']} | "
        f"{benchmark['label']}"
    )

    print(
        f"N Win/Loss : "
        f"{benchmark['n_wins']} / "
        f"{benchmark['n_losses']}"
    )

    print(
        f"Win médiane : "
        f"{benchmark['wins']['median']:.2f}"
    )

    print(
        f"Loss médiane : "
        f"{benchmark['losses']['median']:.2f}"
    )

    print(
        f"Q25/Q75 Win : "
        f"{benchmark['wins']['q25']:.2f} / "
        f"{benchmark['wins']['q75']:.2f}"
    )

    print(
        f"Q25/Q75 Loss : "
        f"{benchmark['losses']['q25']:.2f} / "
        f"{benchmark['losses']['q75']:.2f}"
    )

    print(
        f"Cliff Delta : "
        f"{benchmark['cliffs_delta']:+.3f}"
    )

    print(
        f"Effet : "
        f"{benchmark['effect']}"
    )

    print(
        f"Seuil historique : "
        f"{benchmark['threshold']:.2f}"
    )

    print(
        f"Balanced accuracy : "
        f"{benchmark['balanced_accuracy'] * 100:.1f}%"
    )

    print(
        f"Chevauchement IQR : "
        f"{benchmark['iqr_overlap'] * 100:.1f}%"
    )

    bootstrap = benchmark.get("bootstrap")

    if bootstrap is not None:
        print(
            "IC95 Cliff orienté : "
            f"{bootstrap['aligned_delta_ci_low']:+.3f} "
            f"à "
            f"{bootstrap['aligned_delta_ci_high']:+.3f}"
        )

        print(
            "IC95 écart médian orienté : "
            f"{bootstrap['aligned_median_gap_ci_low']:+.2f} "
            f"à "
            f"{bootstrap['aligned_median_gap_ci_high']:+.2f}"
        )

    else:
        print(
            "Bootstrap : échantillon trop faible."
        )

    print(
        f"Fiabilité interne : "
        f"{benchmark['reliability_score']:.0f}/100 "
        f"({benchmark['reliability']})"
    )


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():
    print(
        "Initialisation de ZiRcoN Coach..."
    )

    initialize_database()
    initialize_timeline_tables()

    # ========================================================
    # COMPTE RIOT
    # ========================================================

    account = get_account_by_riot_id(
        GAME_NAME,
        TAG_LINE,
    )

    use_local_match_history = False

    if not account:
        account = get_local_account_by_riot_id(
            GAME_NAME,
            TAG_LINE,
            queue_id=SOLOQ_QUEUE_ID,
        )

        if not account:
            print(
                "Compte Riot introuvable."
            )
            return

        use_local_match_history = True

        print()
        print(
            "API Riot indisponible pour le compte ; "
            "historique local utilise."
        )

    puuid = account["puuid"]

    print()

    print(
        f"Compte : "
        f"{account['gameName']}#"
        f"{account['tagLine']}"
    )

    # ========================================================
    # MATCHS SOLOQ
    # ========================================================

    print()
    if use_local_match_history:
        print(
            "Chargement des matchs SoloQ depuis l'historique local..."
        )

        match_ids = get_local_match_ids_by_puuid(
            puuid=puuid,
            queue_id=SOLOQ_QUEUE_ID,
            count=MATCH_COUNT,
        )

    else:
        print(
            "Recherche des matchs SoloQ..."
        )

        match_ids = get_match_ids_by_puuid(
            puuid=puuid,
            count=MATCH_COUNT,
            queue=SOLOQ_QUEUE_ID,
        )

        if not match_ids:
            match_ids = get_local_match_ids_by_puuid(
                puuid=puuid,
                queue_id=SOLOQ_QUEUE_ID,
                count=MATCH_COUNT,
            )

            if match_ids:
                use_local_match_history = True
                print(
                    "Aucun match recupere via API ; "
                    "historique local utilise."
                )

    if not match_ids:
        print(
            "Aucun match SoloQ trouvé."
        )
        return

    print(
        f"{len(match_ids)} "
        f"matchs SoloQ trouvés."
    )

    # ========================================================
    # IMPORT MATCHS
    # ========================================================

    new_matches = 0
    existing_matches = 0
    failed_matches = 0

    total_matches = len(match_ids)

    print()
    print("==============================")
    print("IMPORT MATCHS")
    print("==============================")

    for index, match_id in enumerate(
        match_ids,
        start=1,
    ):
        print(
            f"[{index}/{total_matches}] "
            f"{match_id}",
            end=" ",
        )

        if match_exists(match_id):
            print(
                "déjà enregistré"
            )
            existing_matches += 1
            continue

        match = get_match_details(
            match_id
        )

        if not match:
            print(
                "ERREUR"
            )
            failed_matches += 1
            continue

        save_match(match)

        new_matches += 1

        print(
            "enregistré"
        )

    print()
    print("==============================")
    print("MATCHS TERMINÉS")
    print("==============================")

    print(
        "Nouveaux :",
        new_matches,
    )

    print(
        "Déjà présents :",
        existing_matches,
    )

    print(
        "Erreurs :",
        failed_matches,
    )

    # ========================================================
    # FILTRE JUNGLE
    # ========================================================

    jungle_match_ids = (
        filter_match_ids_by_position(
            match_ids,
            puuid,
            ROLE_FILTER,
        )
    )

    print()
    print("==============================")
    print("FILTRE JUNGLE")
    print("==============================")

    print(
        f"{len(jungle_match_ids)} "
        f"games Jungle sur les "
        f"{len(match_ids)} SoloQ."
    )

    if not jungle_match_ids:
        print(
            "Aucune game Jungle trouvée."
        )
        return

    # ========================================================
    # IMPORT TIMELINES JUNGLE
    # ========================================================

    print()
    print("==============================")
    print("IMPORT TIMELINES JUNGLE")
    print("==============================")

    new_timelines = 0
    existing_timelines = 0
    failed_timelines = 0

    total_jungle_matches = len(
        jungle_match_ids
    )

    for index, match_id in enumerate(
        jungle_match_ids,
        start=1,
    ):
        print(
            f"[{index}/{total_jungle_matches}] "
            f"{match_id}",
            end=" ",
        )

        if timeline_exists(match_id):
            print(
                "timeline déjà enregistrée"
            )
            existing_timelines += 1
            continue

        timeline = get_match_timeline(
            match_id
        )

        if not timeline:
            print(
                "ERREUR TIMELINE"
            )
            failed_timelines += 1
            continue

        save_timeline(
            match_id,
            timeline,
        )

        new_timelines += 1

        print(
            "timeline enregistrée"
        )

    # ========================================================
    # RÉSUMÉ TIMELINES
    # ========================================================

    print()
    print("==============================")
    print("TIMELINES TERMINÉES")
    print("==============================")

    print(
        "Nouvelles timelines :",
        new_timelines,
    )

    print(
        "Déjà présentes :",
        existing_timelines,
    )

    print(
        "Erreurs :",
        failed_timelines,
    )

    timeline_stats = (
        get_timeline_database_stats()
    )

    print()

    print(
        "Timelines totales en base :",
        timeline_stats["timelines"],
    )

    print(
        "Frames en base :",
        timeline_stats["frames"],
    )

    print(
        "Événements en base :",
        timeline_stats["events"],
    )

    # ========================================================
    # PROFIL JUNGLE
    # ========================================================

    print()
    print("==============================")
    print("PROFIL ZiRcoN - SOLOQ JUNGLE")
    print("==============================")

    stats = get_player_stats(
        puuid,
        position=ROLE_FILTER,
    )

    if not stats:
        print(
            "Aucune statistique Jungle."
        )
        return

    print(
        "Matchs :",
        stats["games"],
    )

    print(
        "Victoires :",
        stats["wins"],
    )

    print(
        "Défaites :",
        stats["losses"],
    )

    print(
        f"Winrate : "
        f"{stats['winrate']:.1f}%"
    )

    print()

    print(
        f"KDA moyen : "
        f"{stats['kills']:.1f} / "
        f"{stats['deaths']:.1f} / "
        f"{stats['assists']:.1f}"
    )

    print()

    print(
        f"Durée moyenne : "
        f"{stats['average_duration']:.1f} min"
    )

    print(
        f"CS/min : "
        f"{stats['cs_per_min']:.2f}"
    )

    print(
        f"Gold/min : "
        f"{stats['gold_per_min']:.0f}"
    )

    print(
        f"Dégâts/min : "
        f"{stats['damage_per_min']:.0f}"
    )

    # ========================================================
    # CHAMPIONS JUNGLE
    # ========================================================

    print()
    print("==============================")
    print("CHAMPIONS - SOLOQ JUNGLE")
    print("==============================")

    champions = get_champion_stats(
        puuid,
        position=ROLE_FILTER,
    )

    for champion in champions:
        print()

        print(
            f"{champion['champion']} | "
            f"{champion['games']} games | "
            f"{champion['winrate']:.1f}% WR"
        )

        print(
            f"KDA : "
            f"{champion['kills']:.1f}/"
            f"{champion['deaths']:.1f}/"
            f"{champion['assists']:.1f}"
        )

        print(
            f"CS/min : "
            f"{champion['cs_per_min']:.2f} | "
            f"Gold/min : "
            f"{champion['gold_per_min']:.0f} | "
            f"Dégâts/min : "
            f"{champion['damage_per_min']:.0f}"
        )

    # ========================================================
    # DERNIÈRE GAME JUNGLE
    # ========================================================

    latest_match_id = jungle_match_ids[0]

    print()
    print("==============================")
    print("TIMELINE DERNIÈRE GAME JUNGLE")
    print("==============================")

    print(
        "Match :",
        latest_match_id,
    )

    snapshots = get_timeline_snapshots(
        latest_match_id,
        puuid,
        minutes=(
            10,
            15,
            20,
        ),
    )

    for snapshot in snapshots:
        player = snapshot["player"]

        print()

        print(
            f"----- "
            f"{snapshot['minute']} MIN "
            f"-----"
        )

        print(
            "Rôle :",
            snapshot["position"],
        )

        print(
            "Gold :",
            player["gold"],
        )

        print(
            "CS :",
            player["cs"],
        )

        print(
            "Niveau :",
            player["level"],
        )

        print(
            "XP :",
            player["xp"],
        )

        if snapshot["opponent"] is not None:
            print()

            print(
                "Écart jungler adverse :"
            )

            print(
                f"Gold : "
                f"{snapshot['gold_diff']:+}"
            )

            print(
                f"CS : "
                f"{snapshot['cs_diff']:+}"
            )

            print(
                f"Niveau : "
                f"{snapshot['level_diff']:+}"
            )

            print(
                f"XP : "
                f"{snapshot['xp_diff']:+}"
            )

    # ========================================================
    # DATASET TIMELINE JUNGLE
    # ========================================================

    print()
    print("==============================")
    print("ANALYSE TEMPORELLE - JUNGLE")
    print("==============================")

    timeline_dataset = (
        get_timeline_dataset(
            puuid,
            minutes=(
                10,
                15,
                20,
            ),
            position=ROLE_FILTER,
        )
    )

    print(
        f"{len(timeline_dataset)} "
        f"points temporels exploitables."
    )

    print_timeline_summary(
        "JUNGLE - GLOBAL",
        aggregate_timeline_dataset(
            timeline_dataset
        ),
    )

    print_timeline_summary(
        "JUNGLE - VICTOIRES",
        aggregate_timeline_dataset(
            timeline_dataset,
            win=True,
        ),
    )

    print_timeline_summary(
        "JUNGLE - DÉFAITES",
        aggregate_timeline_dataset(
            timeline_dataset,
            win=False,
        ),
    )

    # ========================================================
    # TIMELINE PAR CHAMPION
    # ========================================================

    print()
    print("==============================")
    print("TIMELINES PAR CHAMPION JUNGLE")
    print("==============================")

    for champion in champions:
        if (
            champion["games"]
            < MIN_CHAMPION_GAMES
        ):
            continue

        champion_name = champion["champion"]

        print_timeline_summary(
            f"{champion_name} - GLOBAL",
            aggregate_timeline_dataset(
                timeline_dataset,
                champion=champion_name,
            ),
        )

        print_timeline_summary(
            f"{champion_name} - VICTOIRES",
            aggregate_timeline_dataset(
                timeline_dataset,
                champion=champion_name,
                win=True,
            ),
        )

        print_timeline_summary(
            f"{champion_name} - DÉFAITES",
            aggregate_timeline_dataset(
                timeline_dataset,
                champion=champion_name,
                win=False,
            ),
        )

    # ========================================================
    # DATASET ÉVÉNEMENTS JUNGLE
    # ========================================================

    print()
    print("==============================")
    print("ANALYSE ÉVÉNEMENTS - JUNGLE")
    print("==============================")

    print(
        "Analyse des fenêtres "
        "0-10 / 10-15 / 15-20..."
    )

    event_dataset = (
        get_event_window_dataset(
            puuid,
            windows=(
                (0, 10),
                (10, 15),
                (15, 20),
            ),
            position=ROLE_FILTER,
        )
    )

    print(
        f"{len(event_dataset)} "
        f"fenêtres exploitables."
    )

    print_event_summary(
        "JUNGLE - GLOBAL",
        aggregate_event_windows(
            event_dataset
        ),
    )

    print_event_summary(
        "JUNGLE - VICTOIRES",
        aggregate_event_windows(
            event_dataset,
            win=True,
        ),
    )

    print_event_summary(
        "JUNGLE - DÉFAITES",
        aggregate_event_windows(
            event_dataset,
            win=False,
        ),
    )

    # ========================================================
    # EVENTS PAR CHAMPION
    # ========================================================

    print()
    print("==============================")
    print("ÉVÉNEMENTS PAR CHAMPION JUNGLE")
    print("==============================")

    for champion in champions:
        if (
            champion["games"]
            < MIN_CHAMPION_GAMES
        ):
            continue

        champion_name = champion["champion"]

        print_event_summary(
            f"{champion_name} - GLOBAL",
            aggregate_event_windows(
                event_dataset,
                champion=champion_name,
            ),
        )

        print_event_summary(
            f"{champion_name} - VICTOIRES",
            aggregate_event_windows(
                event_dataset,
                champion=champion_name,
                win=True,
            ),
        )

        print_event_summary(
            f"{champion_name} - DÉFAITES",
            aggregate_event_windows(
                event_dataset,
                champion=champion_name,
                win=False,
            ),
        )

    # ========================================================
    # BENCHMARKS GLOBAL JUNGLE
    # ========================================================

    print()
    print("==============================")
    print("BENCHMARKS PERSONNELS - JUNGLE")
    print("==============================")

    global_benchmarks = build_all_benchmarks(
        event_dataset
    )

    ranked_global = rank_benchmarks(
        global_benchmarks,
        minimum_reliability=35,
    )

    print()

    personal_ranked = [
        benchmark
        for benchmark in ranked_global
        if benchmark.get("scope") == "player"
    ]

    team_ranked = [
        benchmark
        for benchmark in ranked_global
        if benchmark.get("scope") == "team"
    ]

    print(
        "Signaux PERSONNELS les plus discriminants "
        "victoires / défaites :"
    )

    if not personal_ranked:
        print(
            "Pas assez de signaux personnels fiables."
        )

    else:
        for benchmark in personal_ranked[:12]:
            print_benchmark(
                benchmark
            )

    print()
    print(
        "Contexte D'ÉQUIPE le plus discriminant "
        "(informatif, non attribué automatiquement au joueur) :"
    )

    if not team_ranked:
        print(
            "Pas assez de signaux d'équipe fiables."
        )

    else:
        for benchmark in team_ranked[:6]:
            print_benchmark(
                benchmark
            )

    # ========================================================
    # BENCHMARKS PAR CHAMPION
    # ========================================================

    print()
    print("==============================")
    print("BENCHMARKS PAR CHAMPION")
    print("==============================")

    for champion in champions:
        if (
            champion["games"]
            < MIN_CHAMPION_GAMES
        ):
            continue

        champion_name = champion["champion"]

        print()
        print(
            "================================"
        )

        print(
            f"{champion_name.upper()} "
            f"- {champion['games']} GAMES"
        )

        print(
            "================================"
        )

        champion_benchmarks = (
            build_all_benchmarks(
                event_dataset,
                champion=champion_name,
            )
        )

        ranked = rank_benchmarks(
            champion_benchmarks,
            minimum_reliability=20,
        )

        if not ranked:
            print(
                "Pas encore assez de données."
            )
            continue

        for benchmark in ranked[:8]:
            print_benchmark(
                benchmark
            )

    # ========================================================
    # COACH AUTOMATIQUE
    # ========================================================

    print()
    print("==============================")
    print("COACH - DERNIÈRE GAME JUNGLE")
    print("==============================")

    match_analysis = analyze_match(
        event_dataset,
        latest_match_id,
    )

    print()

    print(
        render_match_analysis(
            match_analysis
        )
    )

    # ========================================================
    # EXPLICATION DE LA FENÊTRE CRITIQUE
    # ========================================================

    print()
    print()

    print(
        build_critical_window_report(
            event_dataset,
            match_analysis,
            latest_match_id,
            puuid,
        )
    )

    # ========================================================
    # DEATH COST ANALYZER
    # ========================================================

    print()
    print()
    print("==============================")
    print("DEATH COST ANALYZER - JUNGLE")
    print("==============================")

    print()
    print(
        "Construction du dataset de coût des morts..."
    )

    death_dataset = (
        build_death_cost_dataset(
            puuid,
            position=ROLE_FILTER,
            queue_id=SOLOQ_QUEUE_ID,
        )
    )

    print(
        f"{len(death_dataset)} "
        f"morts exploitables."
    )

    death_global = (
        summarize_death_costs(
            death_dataset
        )
    )

    print()
    print(
        render_death_cost_summary(
            "PROFIL GLOBAL - COÛT DES MORTS",
            death_global,
        )
    )

    death_wins = (
        summarize_death_costs(
            death_dataset,
            win=True,
        )
    )

    print()
    print()
    print(
        render_death_cost_summary(
            "VICTOIRES - COÛT DES MORTS",
            death_wins,
        )
    )

    death_losses = (
        summarize_death_costs(
            death_dataset,
            win=False,
        )
    )

    print()
    print()
    print(
        render_death_cost_summary(
            "DÉFAITES - COÛT DES MORTS",
            death_losses,
        )
    )

    # --------------------------------------------------------
    # Analyse au niveau GAME
    # --------------------------------------------------------
    # Important : plusieurs morts d'une même game ne sont pas
    # des observations totalement indépendantes. Cette couche
    # donne donc un poids égal à chaque partie.

    game_death_dataset = (
        build_game_death_summary_dataset(
            death_dataset,
            puuid=puuid,
            position=ROLE_FILTER,
            queue_id=SOLOQ_QUEUE_ID,
        )
    )

    print()
    print()
    print(
        render_game_level_summary(
            "GAME LEVEL - GLOBAL",
            summarize_game_death_profiles(
                game_death_dataset
            ),
        )
    )

    print()
    print()
    print(
        render_game_level_summary(
            "GAME LEVEL - VICTOIRES",
            summarize_game_death_profiles(
                game_death_dataset,
                win=True,
            ),
        )
    )

    print()
    print()
    print(
        render_game_level_summary(
            "GAME LEVEL - DÉFAITES",
            summarize_game_death_profiles(
                game_death_dataset,
                win=False,
            ),
        )
    )

    # --------------------------------------------------------
    # VALIDATION STATISTIQUE GAME-LEVEL
    # --------------------------------------------------------

    game_death_benchmarks = (
        build_game_death_benchmarks(
            game_death_dataset
        )
    )

    print()
    print()
    print(
        render_game_death_validation(
            game_death_dataset,
            game_death_benchmarks,
        )
    )

    print()
    print()

    print(
        render_v10_final_core(
            game_death_dataset,
            game_death_benchmarks,
        )
    )

    print()
    print()

    print(
        render_v11_freeze_report(
            game_death_dataset,
            game_death_benchmarks,
        )
    )

    # --------------------------------------------------------
    # Par champion si l'échantillon le permet
    # --------------------------------------------------------

    for champion in champions:
        if (
            champion["games"]
            < MIN_CHAMPION_GAMES
        ):
            continue

        champion_name = (
            champion["champion"]
        )

        champion_deaths = (
            summarize_death_costs(
                death_dataset,
                champion=champion_name,
            )
        )

        if not champion_deaths:
            continue

        print()
        print()
        print(
            render_death_cost_summary(
                f"{champion_name.upper()} "
                f"- COÛT DES MORTS",
                champion_deaths,
            )
        )

    # --------------------------------------------------------
    # Morts de la dernière game
    # --------------------------------------------------------

    latest_deaths = (
        get_match_death_costs(
            death_dataset,
            latest_match_id,
        )
    )

    print()
    print()

    print(
        render_match_death_costs(
            latest_deaths
        )
    )

    # ========================================================
    # JUNGLE TEMPO ANALYZER
    # ========================================================

    print()
    print()
    print("==============================")
    print("JUNGLE TEMPO ANALYZER")
    print("==============================")

    print()
    print(
        "Chargement bulk des frames + événements..."
    )

    tempo_bundles = (
        load_tempo_bundles(
            puuid,
            position=ROLE_FILTER,
            queue_id=SOLOQ_QUEUE_ID,
        )
    )

    print(
        f"{len(tempo_bundles)} "
        f"games Jungle avec timeline exploitable."
    )

    tempo_intervals = (
        build_tempo_intervals(
            tempo_bundles
        )
    )

    print(
        f"{len(tempo_intervals)} "
        f"intervalles temporels construits."
    )

    core_tempo_intervals = [
        row
        for row in tempo_intervals
        if row[
            "core_interval"
        ]
    ]

    print(
        f"{len(core_tempo_intervals)} "
        f"intervalles hors contamination death."
    )

    farmable_tempo_intervals = [
        row
        for row in tempo_intervals
        if row[
            "farmable_tempo_interval"
        ]
    ]

    mirrored_tempo_intervals = [
        row
        for row in tempo_intervals
        if row[
            "mirrored_farmable_interval"
        ]
    ]

    strict_free_tempo_intervals = [
        row
        for row in tempo_intervals
        if row[
            "strict_free_tempo_interval"
        ]
    ]

    print(
        f"{len(farmable_tempo_intervals)} "
        f"intervalles FARMABLE joueur."
    )

    print(
        f"{len(mirrored_tempo_intervals)} "
        f"intervalles MIRRORED."
    )

    print(
        f"{len(strict_free_tempo_intervals)} "
        f"intervalles STRICT FREE."
    )

    game_tempo_dataset = (
        build_game_tempo_dataset(
            tempo_intervals,
            tempo_bundles,
        )
    )

    phase_tempo_dataset = (
        build_game_phase_tempo_dataset(
            tempo_intervals,
            game_tempo_dataset,
        )
    )

    print()
    print(
        render_tempo_profile(
            "TEMPO - GLOBAL",
            summarize_tempo_profile(
                game_tempo_dataset
            ),
        )
    )

    print()
    print()
    print(
        render_tempo_profile(
            "TEMPO - VICTOIRES",
            summarize_tempo_profile(
                game_tempo_dataset,
                win=True,
            ),
        )
    )

    print()
    print()
    print(
        render_tempo_profile(
            "TEMPO - DÉFAITES",
            summarize_tempo_profile(
                game_tempo_dataset,
                win=False,
            ),
        )
    )

    tempo_benchmarks = (
        build_tempo_benchmarks(
            game_tempo_dataset
        )
    )

    print()
    print()
    print(
        render_tempo_validation(
            game_tempo_dataset,
            tempo_benchmarks,
        )
    )

    print()
    print()
    print(
        "Validation par phase V15 en cours "
        "(pipeline hiérarchique optimisé)..."
    )

    phase_validation_started = (
        perf_counter()
    )

    phase_tempo_benchmarks = (
        build_phase_tempo_benchmarks(
            phase_tempo_dataset
        )
    )

    phase_validation_seconds = (
        perf_counter()
        - phase_validation_started
    )

    print(
        f"Validation phases terminée en "
        f"{phase_validation_seconds:.1f}s."
    )

    print()
    print()
    print(
        render_phase_tempo_validation(
            phase_tempo_benchmarks
        )
    )

    print()
    print()
    print(
        render_pathing_alert_audit(
            tempo_intervals
        )
    )

    print()
    print()

    print(
        render_match_tempo_report(
            tempo_intervals,
            latest_match_id,
        )
    )

    # ========================================================
    # OBJECTIVE ANALYZER V20
    # ========================================================

    print()
    print()
    print("==============================")
    print("OBJECTIVE ANALYZER V20")
    print("==============================")

    objective_dataset = (
        build_objective_dataset(
            tempo_bundles,
            death_dataset=death_dataset,
            tempo_intervals=tempo_intervals,
        )
    )

    print(
        f"{len(objective_dataset)} "
        f"séquences objectifs analysées."
    )

    game_objective_dataset = (
        build_game_objective_dataset(
            objective_dataset,
            tempo_bundles,
        )
    )

    family_objective_dataset = (
        build_objective_family_game_dataset(
            objective_dataset,
            tempo_bundles,
        )
    )

    print()
    print(
        render_objective_profile(
            "OBJECTIFS - GLOBAL",
            summarize_objective_profile(
                game_objective_dataset
            ),
        )
    )

    print()
    print()
    print(
        render_objective_profile(
            "OBJECTIFS - VICTOIRES",
            summarize_objective_profile(
                game_objective_dataset,
                win=True,
            ),
        )
    )

    print()
    print()
    print(
        render_objective_profile(
            "OBJECTIFS - DÉFAITES",
            summarize_objective_profile(
                game_objective_dataset,
                win=False,
            ),
        )
    )

    objective_benchmarks = (
        build_objective_benchmarks(
            game_objective_dataset
        )
    )

    print()
    print()
    print(
        render_objective_validation(
            game_objective_dataset,
            objective_benchmarks,
        )
    )

    print()
    print()
    print(
        "Validation objectifs par type en cours..."
    )

    objective_family_started = perf_counter()

    objective_family_benchmarks = (
        build_objective_family_benchmarks(
            family_objective_dataset
        )
    )

    objective_family_seconds = (
        perf_counter()
        - objective_family_started
    )

    print(
        f"Validation par type terminée en "
        f"{objective_family_seconds:.1f}s."
    )

    print()
    print()
    print(
        render_objective_family_validation(
            objective_family_benchmarks
        )
    )

    print()
    print()
    print(
        render_objective_audit(
            objective_dataset
        )
    )

    print()
    print()
    print(
        render_match_objective_report(
            objective_dataset,
            latest_match_id,
        )
    )


    # ========================================================
    # RECALL / RESET ANALYZER V21
    # ========================================================

    print()
    print()
    print("==============================")
    print("RECALL / RESET ANALYZER V21")
    print("==============================")

    reset_dataset = build_reset_dataset(
        tempo_bundles,
        death_dataset=death_dataset,
        tempo_intervals=tempo_intervals,
        objective_dataset=objective_dataset,
    )

    print(
        f"{len(reset_dataset)} "
        f"séquences shop/reset proxy analysées."
    )

    game_reset_dataset = build_game_reset_dataset(
        reset_dataset,
        tempo_bundles,
    )

    reset_phase_dataset = build_reset_phase_dataset(
        reset_dataset,
        tempo_bundles,
    )

    print()
    print(
        render_reset_profile(
            "RESETS - GLOBAL",
            summarize_reset_profile(
                game_reset_dataset
            ),
        )
    )

    print()
    print()
    print(
        render_reset_profile(
            "RESETS - VICTOIRES",
            summarize_reset_profile(
                game_reset_dataset,
                win=True,
            ),
        )
    )

    print()
    print()
    print(
        render_reset_profile(
            "RESETS - DÉFAITES",
            summarize_reset_profile(
                game_reset_dataset,
                win=False,
            ),
        )
    )

    reset_benchmarks = build_reset_benchmarks(
        game_reset_dataset
    )

    print()
    print()
    print(
        render_reset_validation(
            game_reset_dataset,
            reset_benchmarks,
        )
    )

    print()
    print()
    print("Validation resets par phase en cours...")

    reset_phase_started = perf_counter()

    reset_phase_benchmarks = build_reset_phase_benchmarks(
        reset_phase_dataset
    )

    reset_phase_seconds = (
        perf_counter()
        - reset_phase_started
    )

    print(
        f"Validation resets par phase terminée en "
        f"{reset_phase_seconds:.1f}s."
    )

    print()
    print()
    print(
        render_reset_phase_validation(
            reset_phase_benchmarks
        )
    )

    print()
    print()
    print(
        render_reset_audit(
            reset_dataset
        )
    )

    print()
    print()
    print(
        render_match_reset_report(
            reset_dataset,
            latest_match_id,
        )
    )


    # ========================================================
    # BUILD / ITEMIZATION ANALYZER V22 - PHASE 1
    # ========================================================

    print()
    print()
    print("==============================")
    print("BUILD / ITEMIZATION ANALYZER V22 - PHASE 1")
    print("==============================")

    itemization_history = build_itemization_history(
        puuid,
        position=ROLE_FILTER,
        queue_id=SOLOQ_QUEUE_ID,
    )

    print()
    print(
        render_itemization_audit(
            itemization_history
        )
    )

    print()
    print()
    print(
        render_match_itemization_report(
            itemization_history,
            ITEMIZATION_TARGET_MATCH_ID,
        )
    )


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":
    main()
