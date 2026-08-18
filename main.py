import sys


# ============================================================
# CONSOLE UTF-8
# ============================================================

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# RIOT API
# ============================================================

from riot.riot_api import (
    get_account_by_riot_id,
    get_match_ids_by_puuid,
    get_match_details,
    get_match_timeline,
)


# ============================================================
# DATABASE
# ============================================================

from database.database import (
    initialize_database,
    initialize_timeline_tables,
    match_exists,
    save_match,
    timeline_exists,
    save_timeline,
    filter_match_ids_by_position,
    get_player_stats,
    get_timeline_database_stats,
    get_local_account_by_riot_id,
    get_local_match_ids_by_puuid,
)


# ============================================================
# CONFIGURATION
# ============================================================

GAME_NAME = "ZiRcoN1977"
TAG_LINE = "EUW"

SOLOQ_QUEUE_ID = 420
MATCH_COUNT = 100
ROLE_FILTER = "JUNGLE"


# ============================================================
# ACCOUNT
# ============================================================

def load_account():
    """
    Charge le compte Riot.

    Si l'API Riot est indisponible, utilise les informations
    déjà présentes dans la base locale.
    """

    account = get_account_by_riot_id(
        GAME_NAME,
        TAG_LINE,
    )

    if account:
        return account, False

    account = get_local_account_by_riot_id(
        GAME_NAME,
        TAG_LINE,
        queue_id=SOLOQ_QUEUE_ID,
    )

    if account:
        return account, True

    return None, True


# ============================================================
# MATCH IDS
# ============================================================

def load_match_ids(puuid, local_only=False):
    """
    Récupère les derniers matchs SoloQ.

    Retourne :
    - match_ids
    - True si l'historique local est utilisé
    """

    if not local_only:
        match_ids = get_match_ids_by_puuid(
            puuid=puuid,
            count=MATCH_COUNT,
            queue=SOLOQ_QUEUE_ID,
        )

        if match_ids:
            return match_ids, False

    match_ids = get_local_match_ids_by_puuid(
        puuid=puuid,
        queue_id=SOLOQ_QUEUE_ID,
        count=MATCH_COUNT,
    )

    return match_ids or [], True


# ============================================================
# SYNC MATCHS
# ============================================================

def sync_matches(match_ids, local_only=False):
    """
    Enregistre uniquement les matchs qui ne sont pas encore
    présents dans la base.

    Aucun affichage match par match.
    """

    result = {
        "new": 0,
        "existing": 0,
        "failed": 0,
    }

    for match_id in match_ids:

        if match_exists(match_id):
            result["existing"] += 1
            continue

        if local_only:
            result["failed"] += 1
            continue

        match = get_match_details(match_id)

        if not match:
            result["failed"] += 1
            continue

        save_match(match)

        result["new"] += 1

    return result


# ============================================================
# SYNC TIMELINES
# ============================================================

def sync_timelines(match_ids, local_only=False):
    """
    Télécharge uniquement les timelines manquantes.

    Aucun affichage timeline par timeline.
    """

    result = {
        "new": 0,
        "existing": 0,
        "failed": 0,
    }

    for match_id in match_ids:

        if timeline_exists(match_id):
            result["existing"] += 1
            continue

        if local_only:
            result["failed"] += 1
            continue

        timeline = get_match_timeline(match_id)

        if not timeline:
            result["failed"] += 1
            continue

        save_timeline(
            match_id,
            timeline,
        )

        result["new"] += 1

    return result


# ============================================================
# PROFILE
# ============================================================

def print_profile(puuid):
    stats = get_player_stats(
        puuid,
        position=ROLE_FILTER,
    )

    if not stats:
        print("Profil Jungle : aucune donnée.")
        return

    print()
    print("PROFIL SOLOQ JUNGLE")
    print("-------------------")

    print(
        f"{stats['games']} games | "
        f"{stats['winrate']:.1f}% WR"
    )

    print(
        f"KDA : "
        f"{stats['kills']:.1f} / "
        f"{stats['deaths']:.1f} / "
        f"{stats['assists']:.1f}"
    )

    print(
        f"CS/min {stats['cs_per_min']:.2f} | "
        f"Gold/min {stats['gold_per_min']:.0f} | "
        f"Dégâts/min {stats['damage_per_min']:.0f}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("ZiRcoN Coach")
    print("============")

    initialize_database()
    initialize_timeline_tables()

    # --------------------------------------------------------
    # ACCOUNT
    # --------------------------------------------------------

    account, local_only = load_account()

    if not account:
        print("Compte Riot introuvable.")
        return

    puuid = account["puuid"]

    print(
        f"Compte : "
        f"{account['gameName']}#"
        f"{account['tagLine']}"
    )

    if local_only:
        print("Source : historique local")
    else:
        print("Source : Riot API")

    # --------------------------------------------------------
    # MATCHES
    # --------------------------------------------------------

    match_ids, local_history = load_match_ids(
        puuid,
        local_only=local_only,
    )

    if not match_ids:
        print("Aucun match SoloQ disponible.")
        return

    print(
        f"SoloQ trouvées : {len(match_ids)}"
    )

    match_sync = sync_matches(
        match_ids,
        local_only=local_history,
    )

    # --------------------------------------------------------
    # JUNGLE
    # --------------------------------------------------------

    jungle_match_ids = filter_match_ids_by_position(
        match_ids,
        puuid,
        ROLE_FILTER,
    )

    timeline_sync = sync_timelines(
        jungle_match_ids,
        local_only=local_history,
    )

    # --------------------------------------------------------
    # SYNC SUMMARY
    # --------------------------------------------------------

    print()
    print("SYNCHRONISATION")
    print("---------------")

    print(
        f"Matchs : "
        f"{match_sync['new']} nouveaux | "
        f"{match_sync['existing']} déjà présents | "
        f"{match_sync['failed']} erreurs"
    )

    print(
        f"Jungle : "
        f"{len(jungle_match_ids)} games"
    )

    print(
        f"Timelines : "
        f"{timeline_sync['new']} nouvelles | "
        f"{timeline_sync['existing']} déjà présentes | "
        f"{timeline_sync['failed']} erreurs"
    )

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    timeline_stats = get_timeline_database_stats()

    print(
        f"Base timeline : "
        f"{timeline_stats['timelines']} games | "
        f"{timeline_stats['frames']} frames | "
        f"{timeline_stats['events']} événements"
    )

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    print_profile(puuid)

    print()
    print("Prêt.")


if __name__ == "__main__":
    main()