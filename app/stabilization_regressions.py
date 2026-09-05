"""Regressions for concrete stable-base defects; synthetic fixtures only."""
import sqlite3
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import patch
from pathlib import Path

from app.v01_alpha_checks import _database
from services.cache_repository import CacheRepository
from services.local_data import LocalDataService
from services.post_game_analysis import PostGameAnalysisService
from services.analysis_contracts import ANALYZER_CACHE_VERSIONS
from services.game_context import GameContext, ContextUnavailable


def raw_fixture():
    player = {'puuid': 'p', 'participantId': 1, 'teamId': 100, 'teamPosition': 'JUNGLE',
              'championName': 'Annie', 'kills': 0, 'deaths': 0, 'assists': 0, 'win': True,
              'totalMinionsKilled': 0, 'neutralMinionsKilled': 0}
    opponent = {**player, 'puuid': 'q', 'participantId': 2, 'teamId': 200}
    match = {'metadata': {'matchId': 'EUW1_TEST'}, 'info': {'participants': [player, opponent], 'gameDuration': 120, 'queueId': 420, 'gameVersion': '16.16.1'}}
    frames = [{'timestamp': ts, 'events': [], 'participantFrames': {
        str(i): {'participantId': i, 'totalGold': 500, 'currentGold': 500, 'xp': 0, 'level': 1, 'minionsKilled': 0, 'jungleMinionsKilled': 0}
        for i in (1, 2)}} for ts in (0, 60000, 120000)]
    return match, {'metadata': {'matchId': 'EUW1_TEST'}, 'info': {'frames': frames}}


class ContextChecks(unittest.TestCase):
    def test_valid_context_is_a_copy_not_mutable_raw_alias(self):
        match, timeline = raw_fixture()
        context = GameContext.from_raw(match, timeline, 'p')
        self.assertEqual(context.issues, ())
        self.assertEqual(context.death_timestamps, ())
        context.player['championName'] = 'changed'
        self.assertEqual(match['info']['participants'][0]['championName'], 'Annie')

    def test_missing_invalid_and_wrong_timeline_fail_explicitly(self):
        match, timeline = raw_fixture()
        for value in (None, {}, [], {'info': {'frames': []}, 'metadata': {'matchId': 'OTHER'}}):
            with self.subTest(value=value), self.assertRaises(ContextUnavailable):
                GameContext.from_raw(match, value, 'p')
        with self.assertRaisesRegex(ContextUnavailable, 'PARTICIPANT_UNRESOLVED'):
            GameContext.from_raw(match, timeline, 'missing')

    def test_none_resource_role_and_death_count_remain_issues(self):
        match, timeline = raw_fixture()
        match['info']['participants'][0].update(teamPosition=None, deaths=1)
        timeline['info']['frames'][1]['participantFrames']['1']['xp'] = None
        context = GameContext.from_raw(match, timeline, 'p')
        self.assertIn('ROLE_UNRESOLVED', context.issues)
        self.assertIn('FRAME_RESOURCE_MISSING', context.issues)
        self.assertIn('DEATH_EVENT_COUNT_MISMATCH', context.issues)

    def test_missing_frame_and_bad_event_timestamp(self):
        match, timeline = raw_fixture()
        del timeline['info']['frames'][1]['participantFrames']['1']
        self.assertIn('PARTICIPANT_FRAME_MISSING', GameContext.from_raw(match, timeline, 'p').issues)
        for ts in (-1, None, 99999999):
            bad = deepcopy(timeline)
            bad['info']['frames'][1]['events'] = [{'type': 'CHAMPION_KILL', 'timestamp': ts}]
            with self.subTest(timestamp=ts), self.assertRaisesRegex(ContextUnavailable, 'EVENT_TIMESTAMP_INVALID'):
                GameContext.from_raw(match, bad, 'p')

    def test_empty_frozen_output_cannot_erase_observed_death(self):
        match, timeline = raw_fixture()
        match['info']['participants'][0]['deaths'] = 1
        timeline['info']['frames'][1]['events'] = [{'timestamp': 50000, 'type': 'CHAMPION_KILL', 'victimId': 1}]
        context = GameContext.from_raw(match, timeline, 'p')
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / 'fixture.db'
            _database(db)
            cache = CacheRepository(db)
            service = PostGameAnalysisService(LocalDataService(db, cache), cache)
            with patch('database.database.DB_PATH', db), patch('services.post_game_analysis.load_game_context', return_value=context), \
                 patch('services.post_game_analysis.build_death_cost_dataset', return_value=[]), \
                 patch('services.post_game_analysis.build_itemization_history', return_value={}), \
                 patch('services.post_game_analysis.load_tempo_bundles', return_value=[]), \
                 patch('services.post_game_analysis.build_tempo_intervals', return_value=[]), \
                 patch('services.post_game_analysis.build_objective_dataset', return_value=[]), \
                 patch('services.post_game_analysis.build_reset_dataset', return_value=[]):
                service.generate_for_matches(['EUW1_TEST'])
            death = service.get_match_insights('EUW1_TEST').insights[0]
            self.assertEqual(death.status, 'PARTIAL')
            self.assertIn('0/1', death.summary)

    def test_death_bracket_is_visible_and_experimental(self):
        payload = PostGameAnalysisService(None, None)._death_payload([{'timestamp': 65000, 'impact_interval_seconds': 60, 'gold_cost_60': 100}])
        event = payload['events'][0]
        self.assertTrue(any(m['raw_key'] == 'impact_interval_seconds' and '60' in m['value'] for m in event['metrics']))
        self.assertTrue(any('EXPERIMENTAL' in value for value in event['context']))


class CacheIsolationChecks(unittest.TestCase):
    def test_same_match_two_accounts_never_share_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / 'fixture.db'
            _database(db)
            cache = CacheRepository(db)
            for player in ('a', 'b'):
                cache.save_report('M', 'death', 'v', 'AVAILABLE', {'summary': player}, puuid=player)
            self.assertEqual(cache.reports('M', puuid='a')[0]['payload']['summary'], 'a')
            self.assertEqual(cache.reports('M', puuid='b')[0]['payload']['summary'], 'b')
            self.assertEqual(cache.reports('M', puuid='c'), [])

    def test_unscoped_legacy_report_is_not_current_player_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / 'fixture.db'
            _database(db)
            cache = CacheRepository(db)
            cache.save_report('EUW1_TEST', 'death', ANALYZER_CACHE_VERSIONS['death'], 'AVAILABLE', {'summary': 'legacy'})
            local = LocalDataService(db, cache)
            self.assertEqual(local.matches()[0].analysis_status, 'UNAVAILABLE')
            self.assertEqual(PostGameAnalysisService(local, cache).get_match_insights('EUW1_TEST').status, 'UNAVAILABLE')

    def test_null_metrics_are_not_zero_or_loss(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / 'fixture.db'
            _database(db)
            connection = sqlite3.connect(db)
            connection.execute('UPDATE participants SET kills=NULL, deaths=NULL, assists=NULL, cs=NULL, win=NULL')
            connection.execute('UPDATE matches SET game_duration=NULL')
            connection.commit()
            connection.close()
            local = LocalDataService(db)
            match = local.matches()[0]
            self.assertEqual(match.result, 'UNKNOWN')
            self.assertIsNone(match.cs)
            self.assertIsNone(match.duration_seconds)
            self.assertEqual(match.kda_text, '—/—/—')
            self.assertIsNone(local.progress().win_rate)
            self.assertIsNone(local.progress().kda)
            self.assertIsNone(local.progress().deaths_per_match)


if __name__ == '__main__':
    unittest.main()
