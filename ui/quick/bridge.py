"""Explicit player-facing QML DTOs over the existing account-scoped services."""
from dataclasses import asdict
from functools import partial

from PySide6.QtCore import QObject, Property, QThreadPool, Signal, Slot
from PySide6.QtGui import QImage, QColor
from PySide6.QtQuick import QQuickImageProvider

from services.build_optimizer_presentation import player_facing_reasons
from ui.components.coaching_card import _player_text
from ui.player_coach import coaching_focuses, coaching_empty_message
from ui.workers import FunctionWorker


def shown(value, decimals=0, suffix=''):
    return '—' if value is None else f'{value:,.{decimals}f}'.replace(',', ' ') + suffix


def clock(timestamp):
    seconds = max(0, int(timestamp or 0) // 1000)
    return f'{seconds // 60:02}:{seconds % 60:02}'


class _Delivery(QObject):
    """Queued worker delivery has an explicit GUI-thread QObject receiver."""
    def __init__(self, bridge, worker, completed, failed):
        super().__init__(bridge)
        self.bridge, self.worker = bridge, worker
        self.completed, self.failed = completed, failed

    @Slot(object)
    def result(self, value):
        self.completed(value)

    @Slot(str)
    def error(self, message):
        self.failed(message)

    @Slot()
    def finished(self):
        self.bridge._workers.pop(self.worker, None)
        self.deleteLater()


class CachedImages(QQuickImageProvider):
    """Render cache only; never block the scene graph with network requests."""
    def __init__(self, assets):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self.assets = assets

    def requestImage(self, identity, size, requested_size):
        parts = identity.split('?')[0].split('/')
        data = self.assets.load_cached(*parts) if len(parts) == 3 else None
        result = QImage.fromData(data) if data else QImage()
        if result.isNull():
            result = QImage(64, 64, QImage.Format.Format_ARGB32)
            result.fill(QColor('#203448'))
        size.setWidth(result.width())
        size.setHeight(result.height())
        return result


class QuickBridge(QObject):
    changed = Signal()
    assetChanged = Signal()
    classicRequested = Signal(bool)

    def __init__(self, context, offline=False):
        super().__init__()
        self.context, self.offline = context, offline
        self._state = {'player': {}, 'metrics': [], 'matches': [], 'champions': [], 'count': 0}
        self._detail = {}
        self._build = {}
        self._busy = False
        self._notice = ''
        self._revision = 0
        self._token = 0
        self._generation = 0
        self._workers = {}
        self._requested_assets = set()
        self._asset_revisions = {}
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(4)
        self._match_cache = {}
        self.refresh()

    @Property('QVariantMap', notify=changed)
    def state(self):
        return self._state

    @Property('QVariantMap', notify=changed)
    def detail(self):
        return self._detail

    @Property('QVariantMap', notify=changed)
    def build(self):
        return self._build

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Property(str, notify=changed)
    def notice(self):
        return self._notice

    @Property(int, notify=assetChanged)
    def assetRevision(self):
        return self._revision

    @Slot(str, str, str, result=str)
    def assetUrl(self, kind, identity, version):
        if not identity or identity in ('0', 'None'):
            return ''
        version = self.context.assets.display_version(version)
        try:
            self.context.assets._spec(kind, identity, version)
        except ValueError:
            return ''
        key = (kind, identity, version)
        if not self.offline and key not in self._requested_assets:
            self._requested_assets.add(key)
            if not self.context.assets.load_cached(*key):
                self._work(self.context.assets.load, key, partial(self._asset_loaded, key))
        return f'image://cached/{kind}/{identity}/{version}?r={self._asset_revisions.get(key, 0)}'

    def _asset_loaded(self, key, data):
        if data:
            self._revision += 1
            self._asset_revisions[key] = self._revision
            self.assetChanged.emit()

    def _work(self, function, args, completed, failed=None):
        worker = FunctionWorker(function, *args)
        worker.setAutoDelete(False)
        delivery = _Delivery(self, worker, completed, failed or self._error)
        self._workers[worker] = delivery
        worker.signals.result.connect(delivery.result)
        worker.signals.error.connect(delivery.error)
        worker.signals.finished.connect(delivery.finished)
        self.pool.start(worker)

    def _error(self, _message):
        self._notice = 'Cette action n’a pas pu être terminée. Tes parties restent enregistrées.'
        self._busy = False
        self.changed.emit()

    @Slot()
    def refresh(self):
        # A changed account or freshly imported history invalidates UI-only caches.
        self._token += 1
        self._generation += 1
        self._match_cache.clear()
        self._detail, self._build, self._busy = {}, {}, False
        service = self.context.local_data
        matches = service.matches()
        compositions = service.match_compositions(m.match_id for m in matches)
        summaries = []
        for match in matches:
            row = self._summary(match)
            composition = compositions.get(match.match_id, {})
            for side in ('allies', 'enemies'):
                row[side] = [name.split(' ')[-1] for name in composition.get(side, ())]
            summaries.append(row)
        progress = service.progress(20)
        player = service.player()
        self._state = {
            'player': {'name': player.riot_id if player.puuid else 'Ton compte', 'rank': player.rank if player.rank not in ('UNAVAILABLE', 'UNRANKED') else 'Classement non disponible',
                       'lp': shown(player.lp, suffix=' LP')},
            'count': len(matches), 'matches': summaries,
            'metrics': [{'label': 'Victoires', 'value': shown(progress.win_rate, suffix=' %'), 'hint': '20 dernières parties au maximum'},
                        {'label': 'KDA moyen', 'value': shown(progress.kda, 2), 'hint': '(éliminations + assistances) / morts'},
                        {'label': 'Farm par minute', 'value': shown(progress.cs_per_min, 1), 'hint': 'CS / minute de jeu'}],
            'champions': [{**dict(row), 'rate': shown(row.get('win_rate'), suffix=' %')} for row in progress.champion_rows],
        }
        self.changed.emit()

    @staticmethod
    def _summary(match):
        return {'id': match.match_id, 'champion': match.champion, 'result': match.result,
                'resultText': match.result_text, 'kda': ' / '.join(shown(value) for value in (match.kills, match.deaths, match.assists)), 'cs': shown(match.cs),
                'cspm': shown(match.cs_per_min, 1), 'duration': match.duration_text,
                'date': match.played_at, 'role': {'JUNGLE': 'Jungle', 'TOP': 'Top', 'MIDDLE': 'Mid', 'BOTTOM': 'ADC', 'UTILITY': 'Support'}.get(match.position, 'Rôle non précisé'),
                'version': match.game_version, 'patch': '.'.join(match.game_version.split('.')[:2]),
                'items': [int(item) for item in match.items if item]}

    @Slot(str, result=bool)
    def openMatch(self, match_id):
        match = self.context.local_data.match_detail(match_id)
        if not match:
            return False
        self._token += 1
        token = self._token
        self._detail = self._summary(match.match)
        self._build = {}
        self._busy = False
        roster = []
        for original in self.context.local_data.match_roster(match_id):
            row = dict(original)
            row.update({'kda': ' / '.join(shown(row[field]) for field in ('kills', 'deaths', 'assists')),
                        'goldText': shown(row['gold']), 'csText': shown(row['cs']),
                        'damageText': shown(row['damage']), 'visionText': shown(row['vision']),
                        'items': [int(item) for item in (*row['items'], row['trinket']) if item]})
            roster.append(row)
        self._detail['allies'] = [row for row in roster if not row['is_enemy']]
        self._detail['enemies'] = [row for row in roster if row['is_enemy']]
        story = self.context.local_data.match_story(match_id)
        self._detail['points'] = list(story.get('points', ()))
        labels = {'DRAGON': 'Dragon', 'RIFTHERALD': 'Héraut', 'BARON_NASHOR': 'Baron', 'HORDE': 'Larves', 'ATAKHAN': 'Atakhan'}
        self._detail['events'] = [{**event, 'time': clock(event['timestamp']), 'label': labels.get(event['label'], event['label'])} for event in story.get('events', ())]
        report = self.context.analysis.get_match_insights(match_id)
        self._detail['focuses'] = [{field: [_player_text(text) for text in value] if isinstance(value, tuple) else _player_text(value)
                                   for field, value in asdict(focus).items()} for focus in coaching_focuses(report)]
        self._detail['coachEmpty'] = coaching_empty_message(report)
        if match_id in self._match_cache:
            self._build = self._match_cache[match_id]
        else:
            self._busy = True
            self._work(self.context.build_optimizer.recommendation_for_match, (match_id,),
                       partial(self._build_ready, match_id, token, self._generation), partial(self._build_failed, token))
        self.changed.emit()
        return True

    def _build_ready(self, match_id, token, generation, result):
        if generation != self._generation:
            return
        # Only presentation fields are exposed. Final rosters never feed scoring.
        payload = {key: result.get(key) for key in ('status', 'reason', 'target_item', 'target_name', 'score', 'snapshot_label', 'patch', 'reasons', 'buy_now_named', 'enemy_snapshot')}
        for field in ('reasons', 'buy_now_named', 'enemy_snapshot'):
            payload[field] = list(payload.get(field) or ())
        payload['alternatives'] = [{**row, 'reasons': list(player_facing_reasons(row.get('reasons'), result.get('champion', '')))}
                                   for row in result.get('alternatives_named', ())]
        self._match_cache[match_id] = payload
        if token == self._token:
            self._build, self._busy = payload, False
            self.changed.emit()

    def _build_failed(self, token, _message):
        if token == self._token:
            self._build = {'status': 'UNAVAILABLE', 'reason': 'Le conseil n’a pas pu être préparé. Réouvre cette partie pour réessayer.'}
            self._busy = False
            self.changed.emit()

    @Slot(bool)
    def openClassic(self, settings=False):
        self.classicRequested.emit(settings)

    @Slot()
    def importMatches(self):
        # Account and key configuration remain in the proven classic settings.
        self.openClassic(True)

    def wait_for_workers(self):
        self.pool.waitForDone()

    def shutdown(self):
        self.pool.clear()
        self.pool.waitForDone()
