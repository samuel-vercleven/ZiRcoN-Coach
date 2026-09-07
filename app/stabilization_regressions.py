"""Regressions for concrete stable-base defects; synthetic fixtures only."""
import sqlite3
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import patch, Mock
import json
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path

from app.v01_alpha_checks import _database
from services.cache_repository import CacheRepository
from services.local_data import LocalDataService
from services.post_game_analysis import PostGameAnalysisService
from services.analysis_contracts import ANALYZER_CACHE_VERSIONS
from services.game_context import GameContext, ContextUnavailable
from services.riot_client import DynamicRiotClient, RiotResult, RiotStatus
from services.riot_sync import RiotSyncService
from services.runtime_settings import RuntimeSettingsService
from services.asset_service import AssetService


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

    def test_objective_team_context_never_becomes_personal_severity(self):
        payload = PostGameAnalysisService(None, None)._objective_payload([{'timestamp': 60000, 'sequence_classification': 'LOST_WITH_COMPENSATION'}])
        self.assertEqual(payload['findings'], [])
        self.assertIn('pas une faute individuelle', str(payload['events']))

    def test_build_reliability_and_patch_are_not_hidden(self):
        payload = PostGameAnalysisService(None, None)._build_payload({
            'game_version': '16.9.123', 'ddragon_version': '16.17.1',
            'final_validation': {'status': 'EXACT'},
            'inventory_reliability': {'intervals': [{'status': 'AMBIGUOUS_TEMPORARY_STATE'}]},
            'milestones': {'completed_major_items': [{'item_id': 1, 'timestamp': 60000}]}})
        self.assertEqual(payload['status'], 'PARTIAL')
        self.assertEqual(payload['events'][1]['status'], 'PARTIAL')
        self.assertIn('EXPERIMENTAL', str(payload))
        self.assertIn('final_validation.status=EXACT', payload['evidence'])


class RobustnessChecks(unittest.TestCase):
    def test_asset_path_traversal_never_fetches_or_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            session = Mock()
            assets = AssetService(directory, session)
            for identity in ('../escape', '..\\escape', 'C:\\escape'):
                self.assertIsNone(assets.load('champion', identity))
                self.assertIsNone(assets.load_cached('champion', identity))
            session.get.assert_not_called()

    def test_missing_tempo_alert_count_is_not_zero(self):
        payload = PostGameAnalysisService(None, None)._tempo_payload({'EARLY': {'minutes': 1}})
        self.assertIn('sustained_pathing_holes=None', payload['evidence'][0])
        self.assertEqual(payload['findings'], [])

    def test_malformed_success_is_not_valid_account_or_ids(self):
        session = Mock()
        session.get.return_value.status_code = 200
        client = DynamicRiotClient('FAKE_TEST_KEY', session)
        for value in (None, [], {}, {'puuid': None}):
            session.get.return_value.json.return_value = value
            self.assertEqual(client.account_by_riot_id('x', 'y').status, RiotStatus.ERROR)
        session.get.return_value.json.return_value = {'ids': []}
        self.assertEqual(client.match_ids('p').status, RiotStatus.ERROR)

    def test_invalid_or_wrong_queue_match_is_rejected_before_persistence(self):
        match, timeline = raw_fixture()
        self.assertTrue(RiotSyncService._valid_match(match, 'EUW1_TEST', 'p'))
        self.assertTrue(RiotSyncService._valid_timeline(timeline, 'EUW1_TEST'))
        for value in (None, {}, []):
            self.assertFalse(RiotSyncService._valid_match(value, 'EUW1_TEST', 'p'))
            self.assertFalse(RiotSyncService._valid_timeline(value, 'EUW1_TEST'))
        match['info']['queueId'] = 450
        self.assertFalse(RiotSyncService._valid_match(match, 'EUW1_TEST', 'p'))

    def test_settings_array_is_safe_and_mask_reveals_no_key_fragment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = RuntimeSettingsService(root / '.env', root / 'settings.json')
            settings.settings_path.write_text('[]')
            self.assertIsNone(settings.identity())
            settings.save_api_key('FAKE_TEST_KEY')
            self.assertEqual(settings.masked_key(), '••••••••')

    def test_corrupt_report_is_error_and_legacy_sync_is_not_an_account_status(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / 'fixture.db'
            _database(db)
            cache = CacheRepository(db)
            cache.save_report('M', 'death', 'v', 'AVAILABLE', {}, puuid='p')
            connection = sqlite3.connect(db)
            connection.execute("UPDATE app_player_analysis_reports SET report_json='[]'")
            connection.commit(); connection.close()
            self.assertEqual(cache.reports('M', puuid='p')[0]['status'], 'ERROR')
            cache.save_sync_result('COMPLETE', 'old account')
            self.assertIsNone(cache.sync_state('new_account'))
            settings = RuntimeSettingsService(Path(directory) / '.env', Path(directory) / 'settings.json')
            settings.save_identity('NewPlayer#EUW')
            local = LocalDataService(db, cache, settings)
            self.assertEqual(local.status().sync_status, 'OFFLINE')
            settings.mark_profile_current('new_account')
            self.assertEqual(local.status().sync_status, 'OFFLINE')
            cache.save_sync_result('PARTIAL', 'new account', puuid='new_account')
            self.assertEqual(local.status().sync_status, 'PARTIAL')
            self.assertEqual(local.status().match_count, 0)

    def test_rank_failure_preserves_cached_rank_without_current_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); db = root / 'fixture.db'
            _database(db)
            cache = CacheRepository(db)
            cache.save_profile('p', {'tier': 'GOLD', 'rank': 'II'})
            settings = RuntimeSettingsService(root / '.env', root / 'settings.json')
            settings.save_identity('Player#EUW')
            local = LocalDataService(db, cache, settings)
            client = Mock()
            client.account_by_riot_id.return_value = RiotResult(RiotStatus.VALID, {'puuid': 'p'})
            client.summoner_by_puuid.return_value = RiotResult(RiotStatus.NETWORK_ERROR)
            client.ranked_entries.return_value = RiotResult(RiotStatus.SERVER_ERROR)
            client.match_ids.return_value = RiotResult(RiotStatus.VALID, [])
            analysis = Mock(); analysis.generate_for_matches.return_value = {'generated': 0, 'current': 0}
            service = RiotSyncService(settings, local, cache, analysis, client_factory=lambda _: client)
            with patch('database.database.DB_PATH', db):
                result = service.sync()
            self.assertEqual(result['status'], 'PARTIAL')
            self.assertEqual(local.player().rank, 'GOLD II')
            self.assertEqual(local.player().profile_status, 'CACHED')


class HistoricalAndUiChecks(unittest.TestCase):
    def test_overlapping_death_windows_deduplicate_team_objectives_per_game(self):
        from analysis.death_cost_analyzer import build_game_death_summary_dataset
        rows = [{'match_id': 'game', 'game_creation': 1, 'champion': 'Annie', 'win': True,
                 'timestamp': ts, 'enemy_objectives_after': 1, 'enemy_towers_after': 0,
                 'advantage_state_before_death': 'UNKNOWN',
                 'enemy_objective_event_keys_after': [('DRAGON', 100000)]} for ts in (50000, 60000)]
        result = build_game_death_summary_dataset(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['enemy_objectives_after_deaths_overlapping'], 2)
        self.assertEqual(result[0]['enemy_objectives_after_deaths'], 1)

    def test_corrupt_database_is_not_replaced_and_settings_still_open(self):
        from PySide6.QtWidgets import QApplication
        from app.bootstrap import build_app_context
        from ui.main_window import MainWindow
        application = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); db = root / 'fixture.db'
            db.write_bytes(b'not a SQLite database')
            settings = RuntimeSettingsService(root / '.env', root / 'settings.json')
            context = build_app_context(db, settings)
            window = MainWindow(context)
            window.navigate(3)
            self.assertFalse(context.local_data.status().db_available)
            self.assertEqual(db.read_bytes(), b'not a SQLite database')
            window.close(); application.processEvents()

    def test_frozen_scoring_never_uses_same_or_future_game(self):
        from analysis.death_cost_analyzer import _attach_personal_cost_scores
        past = [{'match_id': 'past', 'game_creation': 1, 'timestamp': i * 1000,
                 'gold_cost_60': i, 'xp_cost_60': i, 'cs_cost_60': i} for i in range(10)]
        current = [{'match_id': 'current', 'game_creation': 2, 'timestamp': i * 1000,
                    'gold_cost_60': 1000, 'xp_cost_60': 1000, 'cs_cost_60': 10} for i in range(2)]
        first = deepcopy(past + current)
        _attach_personal_cost_scores(first)
        self.assertTrue(all(r['resource_cost_score'] is None for r in first[:10]))
        self.assertEqual([r['score_reference_size'] for r in first[10:]], [10, 10])
        second = deepcopy(past + current + [{'match_id': 'future', 'game_creation': 3, 'timestamp': 1, 'gold_cost_60': 99999}])
        _attach_personal_cost_scores(second)
        self.assertEqual(first, second[:12])

    def test_refresh_detaches_old_cards_and_minimum_layout_survives_missing_values(self):
        from PySide6.QtWidgets import QApplication, QWidget
        from app.bootstrap import build_app_context
        from ui.main_window import MainWindow
        from ui.theme import APP_STYLESHEET
        application = QApplication.instance() or QApplication([])
        application.setStyleSheet(APP_STYLESHEET)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); db = root / 'fixture.db'
            _database(db)
            settings = RuntimeSettingsService(root / '.env', root / 'settings.json')
            context = build_app_context(db, settings)
            with patch.object(context.assets, 'load', return_value=None):
                window = MainWindow(context)
                old_card = window.dashboard_page.match_layout.itemAt(0).widget()
                window.dashboard_page.refresh()
                self.assertIsNone(old_card.parent())
                self.assertTrue(old_card.isHidden())
                connection = sqlite3.connect(db)
                connection.execute('UPDATE participants SET cs=NULL, deaths=NULL, win=NULL')
                connection.execute('UPDATE matches SET game_duration=NULL')
                connection.commit(); connection.close()
                window.resize(1100, 700)
                for _ in range(3):
                    for page in range(4):
                        window.navigate(page)
                window.open_match('EUW1_TEST')
                window.show(); application.processEvents()
                self.assertEqual(window.width(), 1100)
                self.assertLessEqual(window.sync_text.maximumWidth(), 140)
                window.navigate(3); application.processEvents()
                self.assertGreaterEqual(window.settings_page.riot_id.height(), 30)
                window.close(); application.processEvents()


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
