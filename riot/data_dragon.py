import requests


DDRAGON_BASE_URL = "https://ddragon.leagueoflegends.com"


def get_ddragon_versions():
    url = f"{DDRAGON_BASE_URL}/api/versions.json"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return response.json()


def get_ddragon_version_for_game(game_version):
    versions = get_ddragon_versions()

    # Exemple :
    # game_version = "16.16.702.1234"
    # patch = "16.16"
    parts = game_version.split(".")

    patch = f"{parts[0]}.{parts[1]}"

    for version in versions:
        if version.startswith(patch + "."):
            return version

    # Sécurité : si aucune version exacte n'est trouvée
    return versions[0]


def get_items(version):
    url = (
        f"{DDRAGON_BASE_URL}/cdn/"
        f"{version}/data/fr_FR/item.json"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return response.json()["data"]


def get_item_name(item_id, items):
    if item_id == 0:
        return "Emplacement vide"

    item = items.get(str(item_id))

    if item:
        return item["name"]

    return f"Item inconnu ({item_id})"