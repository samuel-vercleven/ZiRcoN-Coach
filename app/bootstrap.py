from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from services.asset_service import AssetService
from services.cache_repository import CacheRepository
from services.local_data import LocalDataService
from services.post_game_analysis import PostGameAnalysisService
from services.riot_sync import RiotSyncService
from services.runtime_settings import RuntimeSettingsService


@dataclass(frozen=True)
class AppContext:
    local_data: LocalDataService
    settings: RuntimeSettingsService
    assets: AssetService
    cache: CacheRepository
    analysis: PostGameAnalysisService
    sync: RiotSyncService


def build_app_context(db_path: Path | str | None = None) -> AppContext:
    settings = RuntimeSettingsService()
    cache = CacheRepository(db_path) if db_path else CacheRepository()
    cache.initialize()
    local_data = LocalDataService(db_path or cache.db_path, cache=cache, settings=settings)
    assets = AssetService()
    analysis = PostGameAnalysisService(local_data, cache)
    sync = RiotSyncService(settings, local_data, cache, analysis)
    return AppContext(local_data, settings, assets, cache, analysis, sync)
