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
from services.analysis_contracts import SOLO_QUEUE_ID


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

    @staticmethod
    def _valid_match(data, match_id, puuid):
        if not isinstance(data, dict) or not isinstance(data.get('info'), dict) or not isinstance(data.get('metadata'), dict):
            return False
        info = data['info']
        players = info.get('participants')
        return (data['metadata'].get('matchId') == match_id and info.get('queueId') == SOLO_QUEUE_ID
                and isinstance(players, list) and bool(players)
                and all(isinstance(p, dict) and isinstance(p.get('puuid'), str)
                        and all(isinstance(p.get(k), (int, float)) for k in ('totalMinionsKilled', 'neutralMinionsKilled')) for p in players)
                and sum(p['puuid'] == puuid for p in players) == 1)

    @staticmethod
    def _valid_timeline(data, match_id):
        if not isinstance(data, dict) or not isinstance(data.get('info'), dict) or not isinstance(data.get('metadata'), dict):
            return False
        frames = data['info'].get('frames')
        return (data['metadata'].get('matchId') == match_id and isinstance(frames, list) and len(frames) >= 2
                and all(isinstance(f, dict) and isinstance(f.get('timestamp'), (int, float))
                        and isinstance(f.get('participantFrames'), dict)
                        and all(isinstance(p, dict) for p in f['participantFrames'].values())
                        and isinstance(f.get('events'), list) and all(isinstance(e, dict) for e in f['events']) for f in frames))

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
            if account.status in (RiotStatus.UNAUTHORIZED, RiotStatus.FORBIDDEN):
                self.settings.set_api_status(account.status.value)
            return {"status": account.status.value, "message": account.message}
        self.settings.set_api_status(RiotStatus.VALID.value)
        puuid = str((account.data or {}).get("puuid") or "")
        if not puuid:
            return {'status': 'ERROR', 'message': 'Identifiant du compte absent de la réponse Riot.'}
        from database import database as legacy_database
        if self.local_data.db_path.resolve() != legacy_database.DB_PATH.resolve():
            return {'status': 'REVIEW_REQUIRED', 'message': 'Sync vers une DB alternative non prise en charge ; aucune donnée écrite.'}
        initialize_database()
        initialize_timeline_tables()
        update("Fetching profile and rank", 12)
        summoner = client.summoner_by_puuid(puuid)
        ranked = client.ranked_entries(puuid)
        profile = {**(self.cache.profile(puuid) or {}), "riot_id": identity.riot_id, "puuid": puuid,
                   "profile_status": "CURRENT" if summoner.ok and ranked.ok else 'CACHED',
                   'rank_status': ranked.status.value, 'summoner_status': summoner.status.value}
        if summoner.ok:
            profile.update({"profile_icon_id": summoner.data.get("profileIconId"), "summoner_level": summoner.data.get("summonerLevel")})
        if ranked.ok:
            for field in ('tier', 'rank', 'lp', 'ranked_wins', 'ranked_losses'):
                profile.pop(field, None)
            solo = next((entry for entry in ranked.data if entry.get("queueType") == "RANKED_SOLO_5x5"), None)
            if solo:
                profile.update({"tier": solo.get("tier"), "rank": solo.get("rank"), "lp": solo.get("leaguePoints"),
                                "ranked_wins": solo.get("wins"), "ranked_losses": solo.get("losses")})
        self.cache.save_profile(puuid, profile)
        self.settings.mark_profile_current(puuid)
        if not (summoner.ok and ranked.ok):
            self.settings.mark_profile_current('')

        update("Fetching match IDs", 20)
        match_ids = client.match_ids(puuid, self.settings.sync_scope(), queue=SOLO_QUEUE_ID)
        if not match_ids.ok:
            return {"status": match_ids.status.value, "message": match_ids.message}
        ids = list(dict.fromkeys(match_ids.data or []))
        failures = [name + ':' + result.status.value for name, result in (('profile', summoner), ('rank', ranked)) if not result.ok]
        available_matches = set()
        counters = {
            "target_ids": len(ids), "new_matches": 0, "existing_matches": 0,
            "new_timelines": 0, "existing_timelines": 0,
            "failed_details": 0, "failed_timelines": 0,
            "analyses_generated": 0, "analyses_current": 0,
            "profile_status": summoner.status.value,
            "rank_status": ranked.status.value,
        }
        unavailable_matches = set()
        for index, match_id in enumerate(ids, start=1):
            update(f"Downloading match {index}/{len(ids)}", 20 + int(index / max(1, len(ids)) * 30))
            if not match_exists(match_id):
                result = client.match(match_id)
                if result.ok and not self._valid_match(result.data, match_id, puuid):
                    result = RiotResult(RiotStatus.ERROR, message='Match invalide ou hors compte/queue demandé.')
                if result.ok:
                    save_match(result.data)
                    counters["new_matches"] += 1
                    available_matches.add(match_id)
                else:
                    failures.append(f"match:{match_id}:{result.status.value}")
                    unavailable_matches.add(match_id)
                    counters["failed_details"] += 1
            else:
                counters["existing_matches"] += 1
                available_matches.add(match_id)
        for index, match_id in enumerate(ids, start=1):
            update(f"Downloading timeline {index}/{len(ids)}", 50 + int(index / max(1, len(ids)) * 20))
            if match_id in unavailable_matches:
                continue
            if not timeline_exists(match_id):
                result = client.timeline(match_id)
                if result.ok and not self._valid_timeline(result.data, match_id):
                    result = RiotResult(RiotStatus.ERROR, message='Timeline invalide ou incomplète.')
                if result.ok:
                    save_timeline(match_id, result.data)
                    counters["new_timelines"] += 1
                else:
                    failures.append(f"timeline:{match_id}:{result.status.value}")
                    counters["failed_timelines"] += 1
            else:
                counters["existing_timelines"] += 1
        update("Running cached post-game analysis", 75)
        analysis_ids = [match_id for match_id in ids if match_id in available_matches]
        analysis_result = self.analysis.generate_for_matches(analysis_ids, lambda message: update(message, 85))
        analysis_result = analysis_result if isinstance(analysis_result, dict) else {}
        counters["analyses_generated"] = int(analysis_result.get("generated") or 0)
        counters["analyses_current"] = int(analysis_result.get("current") or 0)
        update("Refreshing local views", 100)
        status = "PARTIAL" if failures else "COMPLETE"
        message = (
            f"SoloQ ciblées {len(ids)} · parties +{counters['new_matches']} / existantes {counters['existing_matches']} / échecs {counters['failed_details']} · "
            f"timelines +{counters['new_timelines']} / existantes {counters['existing_timelines']} / échecs {counters['failed_timelines']} · "
            f"analyses courantes {counters['analyses_current']} · profil {counters['profile_status']} · rang {counters['rank_status']}."
        )
        self.cache.save_sync_result(status, message, puuid, SOLO_QUEUE_ID, counters)
        return {"status": status, "message": message, "failures": failures, **counters,
                "puuid": puuid, "queue_id": SOLO_QUEUE_ID}
