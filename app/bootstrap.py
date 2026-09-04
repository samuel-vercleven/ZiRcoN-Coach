from __future__ import annotations

from dataclasses import dataclass

from services.local_data import LocalDataService


@dataclass(frozen=True)
class AppContext:
    local_data: LocalDataService


def build_app_context() -> AppContext:
    # Keep V0.1 bootstrap offline-safe: importing Riot code currently loads
    # config/settings.py, which intentionally raises when RIOT_API_KEY is absent.
    # Network/Riot services will therefore be lazy in a later integration batch.
    return AppContext(local_data=LocalDataService())
