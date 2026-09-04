from __future__ import annotations

from collections.abc import Callable

from database.database import (
    initialize_database, initialize_timeline_tables, match_exists, save_match,
    save_timeline, timeline_exists,
)
from services.cache_repository import CacheRepository
from services.local_data import LocalDataService
from services.post_game_analysis import PostGameAnalysisService
from services.riot_client import DynamicRiotClient, RiotResult, RiotStatus
from services.runtime_settings import RuntimeSettingsService


class RiotSyncService:
    def __init__(self, settings: RuntimeSettingsService, local_data: LocalDataService,
                 cache: CacheRepository, analysis: PostGameAnalysisService,
                 client_factory=DynamicRiotClient):
        self.settings, self.local_data, self.cache, self.analysis = settings, local_data, cache, analysis
        self.client_factory = client_factory

    def validate_key(self, proposed_key: str, riot_id: str) -> RiotResult:
        game_name, separator, tag_line = riot_id.strip().partition("#")
        if not separator or not game_name or not tag_line:
            return RiotResult(RiotStatus.ERROR, message="Use Riot ID format GameName#TagLine.")
        return self.client_factory(proposed_key).account_by_riot_id(game_name, tag_line)

    def sync(self, progress: Callable[[str, int], None] | None = None) -> dict:
        identity = self.settings.identity()
        if identity is None:
            player = self.local_data.player()
            if "#" not in player.riot_id:
                return {"status": "FAILED", "message": "Configure a Riot ID in Settings."}
            game_name, tag_line = player.riot_id.rsplit("#", 1)
            identity = self.settings.save_identity(f"{game_name}#{tag_line}", self.settings.sync_scope())
        client = self.client_factory(self.settings.api_key())

        def update(message: str, value: int):
            if progress:
                progress(message, value)

        update("Validating Riot API", 5)
        account = client.account_by_riot_id(identity.game_name, identity.tag_line)
        if not account.ok:
            return {"status": account.status.value, "message": account.message}
        puuid = str((account.data or {}).get("puuid") or "")
        update("Fetching profile and rank", 12)
        summoner = client.summoner_by_puuid(puuid)
        ranked = client.ranked_entries(puuid)
        profile = {"riot_id": identity.riot_id, "puuid": puuid, "profile_status": "CURRENT"}
        if summoner.ok:
            profile.update({"profile_icon_id": summoner.data.get("profileIconId"), "summoner_level": summoner.data.get("summonerLevel")})
        if ranked.ok:
            solo = next((entry for entry in ranked.data if entry.get("queueType") == "RANKED_SOLO_5x5"), None)
            if solo:
                profile.update({"tier": solo.get("tier"), "rank": solo.get("rank"), "lp": solo.get("leaguePoints"),
                                "ranked_wins": solo.get("wins"), "ranked_losses": solo.get("losses")})
        self.cache.save_profile(puuid, profile)

        update("Fetching match IDs", 20)
        match_ids = client.match_ids(puuid, self.settings.sync_scope())
        if not match_ids.ok:
            return {"status": match_ids.status.value, "message": match_ids.message}
        ids = list(match_ids.data or [])
        initialize_database()
        initialize_timeline_tables()
        failures = []
        for index, match_id in enumerate(ids, start=1):
            update(f"Downloading match {index}/{len(ids)}", 20 + int(index / max(1, len(ids)) * 30))
            if not match_exists(match_id):
                result = client.match(match_id)
                if result.ok:
                    save_match(result.data)
                else:
                    failures.append(f"match:{match_id}:{result.status.value}")
                    continue
            update(f"Downloading timeline {index}/{len(ids)}", 50 + int(index / max(1, len(ids)) * 20))
            if not timeline_exists(match_id):
                result = client.timeline(match_id)
                if result.ok:
                    save_timeline(match_id, result.data)
                else:
                    failures.append(f"timeline:{match_id}:{result.status.value}")
        update("Running cached post-game analysis", 75)
        self.analysis.generate_for_matches(ids, lambda message: update(message, 85))
        update("Refreshing local views", 100)
        return {"status": "PARTIAL" if failures else "COMPLETE", "message": f"Synced {len(ids)} match(es).", "failures": failures}
