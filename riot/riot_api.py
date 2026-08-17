import time
import requests

from config.settings import RIOT_API_KEY


BASE_URL = "https://europe.api.riotgames.com"


# ============================================================
# REQUÊTE RIOT GÉNÉRIQUE
# ============================================================

def riot_get(url, params=None):
    """
    Effectue une requête GET vers l'API Riot.

    Si Riot répond 429 (rate limit),
    le programme attend automatiquement puis réessaie.
    """

    headers = {
        "X-Riot-Token": RIOT_API_KEY
    }

    while True:
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=15
            )

        except requests.RequestException as error:
            print()
            print("Erreur réseau :", error)
            return None

        # Succès
        if response.status_code == 200:
            return response

        # ==============================
        # RATE LIMIT
        # ==============================

        if response.status_code == 429:
            retry_after = response.headers.get(
                "Retry-After",
                "5"
            )

            try:
                retry_after = int(float(retry_after))
            except ValueError:
                retry_after = 5

            print()
            print(
                "Rate limit Riot atteint."
                f" Attente de {retry_after} secondes..."
            )

            time.sleep(retry_after + 1)

            print("Reprise des requêtes Riot...")

            continue

        # ==============================
        # AUTRES ERREURS
        # ==============================

        print()
        print(
            "Erreur Riot API :",
            response.status_code
        )

        if response.text:
            print(response.text)

        return None


# ============================================================
# COMPTE RIOT
# ============================================================

def get_account_by_riot_id(
    game_name,
    tag_line
):
    url = (
        f"{BASE_URL}/riot/account/v1/accounts/"
        f"by-riot-id/{game_name}/{tag_line}"
    )

    response = riot_get(url)

    if response:
        return response.json()

    return None


# ============================================================
# LISTE DES MATCHS
# ============================================================

def get_match_ids_by_puuid(
    puuid,
    count=100,
    queue=420,
    start=0
):
    url = (
        f"{BASE_URL}/lol/match/v5/matches/"
        f"by-puuid/{puuid}/ids"
    )

    params = {
        "start": start,
        "count": count,
        "queue": queue
    }

    response = riot_get(
        url,
        params=params
    )

    if response:
        return response.json()

    return []


# ============================================================
# DÉTAIL D'UN MATCH
# ============================================================

def get_match_details(match_id):
    url = (
        f"{BASE_URL}/lol/match/v5/"
        f"matches/{match_id}"
    )

    response = riot_get(url)

    if response:
        return response.json()

    return None

# ============================================================
# TIMELINE D'UN MATCH
# ============================================================

def get_match_timeline(match_id):
    url = (
        f"{BASE_URL}/lol/match/v5/"
        f"matches/{match_id}/timeline"
    )

    response = riot_get(url)

    if response:
        return response.json()

    return None