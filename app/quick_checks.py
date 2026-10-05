"""Focused data/thread/navigation contracts for the opt-in QML presentation."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from PySide6.QtCore import QThread
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlEngine, QQmlComponent
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
from ui.quick.bridge import QuickBridge
from viewmodels import MatchSummaryViewModel, MatchDetailViewModel, CoachingReport, PlayerViewModel, ProgressViewModel


class QuickChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.match = MatchSummaryViewModel('M1', 'Viego', 'UNKNOWN', None, None, None, None, None, '2026-09-01', 'Solo', items=(0, 3153, 0), game_version='16.18.1')
        local = Mock()
        local.matches.return_value = [self.match]
        local.match_compositions.return_value = {}
        local.progress.return_value = ProgressViewModel()
        local.player.return_value = PlayerViewModel()
        local.match_detail.side_effect = lambda identity: MatchDetailViewModel(self.match) if identity == 'M1' else None
        local.match_roster.return_value = ({'team_id': 100, 'is_player': True, 'is_enemy': False, 'champion': 'Viego', 'display_name': 'Local', 'position': 'JUNGLE', 'kills': None, 'deaths': None, 'assists': None, 'cs': None, 'gold': None, 'damage': None, 'vision': None, 'items': (0, 3153), 'trinket': 0, 'win': None},)
        local.match_story.return_value = {'points': ({'timestamp': 0, 'delta': None},), 'events': ()}
        optimizer = Mock()
        optimizer.recommendation_for_match.return_value = {'status': 'UNAVAILABLE', 'reason': 'Contexte insuffisant'}
        self.context = SimpleNamespace(local_data=local, assets=Mock(), analysis=Mock(), build_optimizer=optimizer)
        self.context.analysis.get_match_insights.return_value = CoachingReport('M1')
        self.bridge = QuickBridge(self.context, offline=True)

    def tearDown(self):
        self.bridge.shutdown()
        self.app.processEvents()

    def finish(self):
        self.bridge.wait_for_workers()
        self.app.processEvents()

    def test_missing_metrics_stay_missing(self):
        row = self.bridge.state['matches'][0]
        self.assertEqual(row['cs'], '—')
        self.assertEqual(row['kda'], '— / — / —')
        self.assertEqual(row['items'], [3153])
        self.assertEqual(self.bridge.state['metrics'][0]['value'], '—')

    def test_roster_and_chart_keep_gaps(self):
        self.bridge.openMatch('M1'); self.finish()
        row = self.bridge.detail['allies'][0]
        self.assertEqual(row['items'], [3153])
        self.assertEqual(row['goldText'], '—')
        self.assertIsNone(self.bridge.detail['points'][0]['delta'])
        self.assertEqual(self.bridge.detail['focuses'], [])

    def test_background_delivery_is_gui_thread(self):
        threads = []
        self.bridge._work(lambda: 7, (), lambda value: threads.append((value, QThread.currentThread())))
        self.finish()
        self.assertEqual(threads, [(7, self.app.thread())])

    def test_successful_build_lists_and_prefix_only_context(self):
        original = {'status': 'SUPPORTED_HEURISTIC', 'score': 75, 'target_item': 3153, 'target_name': 'Test', 'snapshot_label': '09:00', 'patch': '16.18', 'reasons': ('Raison contextuelle',), 'buy_now_named': ({'item_id': 1036, 'name': 'Épée longue', 'cost': 350},), 'enemy_snapshot': ({'champion': 'Garen', 'health_max': 1000},), 'alternatives_named': (), 'profile': 'PRIVATE_ENGINE_DIAGNOSTIC'}
        self.context.build_optimizer.recommendation_for_match.return_value = original
        self.bridge.openMatch('M1'); self.finish()
        for field in ('reasons', 'enemy_snapshot', 'buy_now_named'):
            self.assertIsInstance(self.bridge.build[field], list)
        self.assertEqual(self.bridge.build['enemy_snapshot'][0]['health_max'], 1000)
        self.assertNotIn('profile', self.bridge.build)
        self.assertIsInstance(original['reasons'], tuple)

    def test_build_cache_avoids_recomputation(self):
        self.bridge.openMatch('M1'); self.finish()
        self.bridge.openMatch('M1')
        self.assertFalse(self.bridge.busy)
        self.context.build_optimizer.recommendation_for_match.assert_called_once_with('M1')

    def test_invalid_match_does_not_replace_selection(self):
        self.bridge.openMatch('M1'); self.finish()
        self.assertFalse(self.bridge.openMatch('OTHER_ACCOUNT_GAME'))
        self.assertEqual(self.bridge.detail['id'], 'M1')

    def test_refresh_invalidates_account_bound_cache(self):
        self.bridge.openMatch('M1'); self.finish()
        previous_generation, previous_token = self.bridge._generation, self.bridge._token
        self.bridge.refresh()
        self.bridge._build_ready('M1', previous_token, previous_generation, {'status': 'SUPPORTED_HEURISTIC'})
        self.assertEqual(self.bridge._match_cache, {})
        self.assertEqual(self.bridge.detail, {})
        self.assertEqual(self.bridge.build, {})

    def test_stale_match_completion_cannot_replace_current_view(self):
        self.bridge._token = 5
        self.bridge._build_ready('M1', 4, self.bridge._generation, {'status': 'UNAVAILABLE'})
        self.assertEqual(self.bridge.build, {})
        self.assertIn('M1', self.bridge._match_cache)

    def test_empty_assets_have_no_source(self):
        self.assertEqual(self.bridge.assetUrl('item', '0', '16.18'), '')
        self.assertEqual(self.bridge.assetUrl('item', '', '16.18'), '')
        self.assertFalse(self.bridge._workers)

    def test_theme_binding_switches_without_new_components(self):
        from app.paths import PROJECT_ROOT
        from shiboken6 import delete
        engine = QQmlEngine()
        engine.rootContext().setContextProperty('initialTheme', 'turquoise')
        component = QQmlComponent(engine)
        source = b'''import QtQuick
QtObject {
    property color background: ZTheme.color("#09131f")
    property color textColor: ZTheme.color("#edf3fa")
    property color muted: ZTheme.color("#95acc3")
    property color buttonBackground: ZTheme.color("#58dfc0")
    property color buttonText: ZTheme.color("#062a2b")
}'''
        component.setData(source, QUrl.fromLocalFile(str(PROJECT_ROOT / 'ui/quick/qml/ThemeProbe.qml')))
        probe = component.create()
        self.assertIsNotNone(probe, str(component.errors()))
        probe.setParent(engine)
        try:
            self.assertEqual(probe.property('background'), QColor('#09131f'))
            self.assertEqual(probe.property('buttonBackground'), QColor('#58dfc0'))
            engine.rootContext().setContextProperty('initialTheme', 'belveth')
            self.app.processEvents()
            self.assertEqual(probe.property('background'), QColor('#100b1b'))
            self.assertEqual(probe.property('buttonBackground'), QColor('#c5a6fa'))
            def luminance(color):
                def linear(channel):
                    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
                return sum(weight * linear(channel) for weight, channel in zip((0.2126, 0.7152, 0.0722), (color.redF(), color.greenF(), color.blueF())))
            for foreground, background in (('textColor', 'background'), ('muted', 'background'), ('buttonText', 'buttonBackground')):
                values = sorted((luminance(probe.property(foreground)), luminance(probe.property(background))))
                self.assertGreaterEqual((values[1] + 0.05) / (values[0] + 0.05), 4.5)
            engine.rootContext().setContextProperty('initialTheme', 'turquoise')
            self.app.processEvents()
            self.assertEqual(probe.property('background'), QColor('#09131f'))
        finally:
            delete(component)
            delete(engine)


if __name__ == '__main__':
    unittest.main()
