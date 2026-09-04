from __future__ import annotations

from pathlib import Path

import requests

from app.paths import PROJECT_ROOT


class AssetService:
    """Display-only Data Dragon cache, separate from frozen semantic catalogs."""

    DEFAULT_VERSION = "16.16.1"

    def __init__(self, cache_dir: Path | str | None = None, session=None):
        self.cache_dir = Path(cache_dir or PROJECT_ROOT / ".cache" / "zircon" / "assets")
        self.session = session or requests.Session()

    @staticmethod
    def display_version(game_version: str = "") -> str:
        parts = game_version.split(".")
        return ".".join(parts[:2]) + ".1" if len(parts) >= 2 else AssetService.DEFAULT_VERSION

    def _spec(self, kind: str, identity: str | int, version: str) -> tuple[Path, str]:
        safe_id = str(identity).replace("/", "_")
        path = self.cache_dir / version / kind / f"{safe_id}.png"
        base = f"https://ddragon.leagueoflegends.com/cdn/{version}/img"
        routes = {"champion": f"champion/{identity}.png", "item": f"item/{identity}.png",
                  "profileicon": f"profileicon/{identity}.png"}
        return path, f"{base}/{routes[kind]}"

    def load(self, kind: str, identity: str | int, game_version: str = "") -> bytes | None:
        if not identity:
            return None
        version = self.display_version(game_version)
        path, url = self._spec(kind, identity, version)
        try:
            if path.exists():
                return path.read_bytes()
            response = self.session.get(url, timeout=8)
            response.raise_for_status()
            data = response.content
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return data
        except (OSError, requests.RequestException):
            return None

    def load_cached(self, kind: str, identity: str | int, game_version: str = "") -> bytes | None:
        if not identity:
            return None
        path, _url = self._spec(kind, identity, self.display_version(game_version))
        try:
            return path.read_bytes() if path.exists() else None
        except OSError:
            return None
