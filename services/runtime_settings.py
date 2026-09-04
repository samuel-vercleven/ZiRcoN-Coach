from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values, set_key

from app.paths import PROJECT_ROOT


@dataclass(frozen=True)
class RiotIdentity:
    game_name: str
    tag_line: str

    @property
    def riot_id(self) -> str:
        return f"{self.game_name}#{self.tag_line}"


class RuntimeSettingsService:
    def __init__(self, env_path: Path | str | None = None, settings_path: Path | str | None = None):
        self.env_path = Path(env_path or PROJECT_ROOT / ".env")
        self.settings_path = Path(settings_path or PROJECT_ROOT / ".cache" / "zircon" / "settings.json")
        self._runtime_key: str | None = None
        self._api_status: str | None = None

    def api_key(self) -> str:
        if self._runtime_key is not None:
            return self._runtime_key
        values = dotenv_values(self.env_path) if self.env_path.exists() else {}
        return str(values.get("RIOT_API_KEY") or os.getenv("RIOT_API_KEY") or "").strip()

    def masked_key(self) -> str:
        value = self.api_key()
        return "Not configured" if not value else f"••••••••{value[-4:]}"

    def save_api_key(self, api_key: str) -> None:
        value = api_key.strip()
        if not value:
            raise ValueError("API key cannot be empty")
        self.env_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.env_path.exists():
            self.env_path.touch()
        set_key(str(self.env_path), "RIOT_API_KEY", value, quote_mode="never")
        self._runtime_key = value
        self._api_status = "VALID"

    def set_api_status(self, status: str) -> None:
        self._api_status = status

    def api_status(self) -> str:
        if self._api_status:
            return self._api_status
        return "CONFIGURED_UNVALIDATED" if self.api_key() else "NOT_CONFIGURED"

    def _read_settings(self) -> dict:
        try:
            return json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return {}

    def identity(self) -> RiotIdentity | None:
        data = self._read_settings()
        game_name = str(data.get("game_name") or "").strip()
        tag_line = str(data.get("tag_line") or "").strip()
        return RiotIdentity(game_name, tag_line) if game_name and tag_line else None

    def save_identity(self, riot_id: str, sync_scope: int = 20) -> RiotIdentity:
        game_name, separator, tag_line = riot_id.strip().partition("#")
        if not separator or not game_name.strip() or not tag_line.strip():
            raise ValueError("Use the Riot ID format GameName#TagLine")
        identity = RiotIdentity(game_name.strip(), tag_line.strip())
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps({
            "game_name": identity.game_name, "tag_line": identity.tag_line,
            "sync_scope": int(sync_scope),
        }, indent=2), encoding="utf-8")
        return identity

    def sync_scope(self) -> int:
        value = self._read_settings().get("sync_scope", 20)
        return int(value) if value in (20, 50, 100) else 20
