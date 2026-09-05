from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from time import sleep
from urllib.parse import quote

import requests


class RiotStatus(str, Enum):
    VALID = "VALID"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNAUTHORIZED = "UNAUTHORIZED_OR_EXPIRED"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"
    NETWORK_ERROR = "NETWORK_ERROR"
    SERVER_ERROR = "RIOT_SERVER_ERROR"
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    ERROR = "ERROR"


@dataclass(frozen=True)
class RiotResult:
    status: RiotStatus
    data: object = None
    message: str = ""
    retry_after: int | None = None

    @property
    def ok(self) -> bool:
        return self.status == RiotStatus.VALID


class DynamicRiotClient:
    REGIONAL = "https://europe.api.riotgames.com"
    PLATFORM = "https://euw1.api.riotgames.com"

    def __init__(self, api_key: str, session: requests.Session | None = None, timeout: float = 12.0):
        self._api_key = api_key.strip()
        self._session = session or requests.Session()
        self.timeout = timeout

    def __repr__(self) -> str:
        return "DynamicRiotClient(api_key=<redacted>)"

    @staticmethod
    def _retry_seconds(raw_value: object) -> int:
        try:
            value = float(str(raw_value).strip())
            if not math.isfinite(value):
                raise ValueError
            return max(1, min(10, int(value)))
        except (TypeError, ValueError, OverflowError):
            return 1

    def _get(self, url: str, params: dict | None = None, retry_rate_limit: bool = True) -> RiotResult:
        if not self._api_key:
            return RiotResult(RiotStatus.NOT_CONFIGURED, message="Riot API key is not configured.")
        attempts = 2 if retry_rate_limit else 1
        for attempt in range(attempts):
            try:
                response = self._session.get(url, headers={"X-Riot-Token": self._api_key}, params=params, timeout=self.timeout)
            except requests.RequestException:
                return RiotResult(RiotStatus.NETWORK_ERROR, message="Riot services are unreachable.")
            if response.status_code == 200:
                try:
                    return RiotResult(RiotStatus.VALID, response.json())
                except ValueError:
                    return RiotResult(RiotStatus.ERROR, message="Riot returned malformed data.")
            if response.status_code == 401:
                return RiotResult(RiotStatus.UNAUTHORIZED, message="API key is invalid or expired.")
            if response.status_code == 403:
                return RiotResult(RiotStatus.FORBIDDEN, message="API key is forbidden for this request.")
            if response.status_code == 404:
                return RiotResult(RiotStatus.ACCOUNT_NOT_FOUND, message="Riot account was not found.")
            if response.status_code == 429:
                retry = self._retry_seconds(response.headers.get("Retry-After", "1"))
                if attempt + 1 < attempts:
                    sleep(retry)
                    continue
                return RiotResult(RiotStatus.RATE_LIMITED, message="Riot rate limit reached.", retry_after=retry)
            if response.status_code >= 500:
                return RiotResult(RiotStatus.SERVER_ERROR, message="Riot service error.")
            return RiotResult(RiotStatus.ERROR, message=f"Riot request failed ({response.status_code}).")
        return RiotResult(RiotStatus.ERROR, message="Riot request failed.")

    def account_by_riot_id(self, game_name: str, tag_line: str) -> RiotResult:
        return self._get(f"{self.REGIONAL}/riot/account/v1/accounts/by-riot-id/{quote(game_name, safe='')}/{quote(tag_line, safe='')}")

    def summoner_by_puuid(self, puuid: str) -> RiotResult:
        return self._get(f"{self.PLATFORM}/lol/summoner/v4/summoners/by-puuid/{quote(puuid, safe='')}")

    def ranked_entries(self, puuid: str) -> RiotResult:
        return self._get(f"{self.PLATFORM}/lol/league/v4/entries/by-puuid/{quote(puuid, safe='')}")

    def match_ids(self, puuid: str, count: int = 20, queue: int = 420) -> RiotResult:
        return self._get(f"{self.REGIONAL}/lol/match/v5/matches/by-puuid/{quote(puuid, safe='')}/ids", {"start": 0, "count": count, "queue": queue})

    def match(self, match_id: str) -> RiotResult:
        return self._get(f"{self.REGIONAL}/lol/match/v5/matches/{quote(match_id, safe='')}")

    def timeline(self, match_id: str) -> RiotResult:
        return self._get(f"{self.REGIONAL}/lol/match/v5/matches/{quote(match_id, safe='')}/timeline")
