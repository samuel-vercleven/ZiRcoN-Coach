"""Explicit player-facing QML DTOs over the existing account-scoped services."""
from dataclasses import asdict
from functools import partial
from datetime import datetime

from PySide6.QtCore import QObject, Property, QThreadPool, Signal, Slot
from PySide6.QtGui import QImage, QColor
from PySide6.QtQuick import QQuickImageProvider

from services.build_optimizer_presentation import player_facing_reasons
from ui.components.coaching_card import _player_text
from ui.player_coach import coaching_focuses, coaching_empty_message
from ui.workers import FunctionWorker
from ui.components.insight_card import player_insight_title, player_insight_summary, event_timestamp_seconds, _player_text as event_text
from ui.pages.progress_page import rolling_win_rate
from ui.pages.settings_page import _player_validation_message
from ui.player_labels import player_label


def shown(value, decimals=0, suffix=''):
    return '—' if value is None else f'{value:,.{decimals}f}'.replace(',', ' ') + suffix


def clock(timestamp):
    seconds = max(0, int(timestamp or 0) // 1000)
    return f'{seconds // 60:02}:{seconds % 60:02}'


def readable_date(value):
    try:
        return datetime.fromisoformat(str(value)).astimezone().strftime('%d/%m/%Y à %H:%M')
    except (TypeError, ValueError):
        return player_label(value)


class _Delivery(QObject):
    """Queued worker delivery has an explicit GUI-thread QObject receiver."""
    def __init__(self, bridge, worker, completed, failed, progress=None):
        super().__init__(bridge)
        self.bridge, self.worker = bridge, worker
        self.completed, self.failed = completed, failed
        self.on_progress = progress

    @Slot(str, int)
    def progress(self, text, value):
        if self.on_progress:
            self.on_progress(text, value)

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
    settingsRequested = Signal()
    credentialSaved = Signal()
    refreshed = Signal()

    def __init__(self, context, offline=False):
        super().__init__()
        self.context, self.offline = context, offline
        self._state = {'player': {}, 'metrics': [], 'matches': [], 'champions': [], 'count': 0}
        self._detail = {}
        self._build = {}
        self._busy = False
        self._notice = ''
        self._operation = {'working': False, 'progress': 0, 'text': ''}
        self._progress = {}
        self._progress_window = 20
        self._revision = 0
        self._token = 0
        self._generation = 0
        self._workers = {}
        self._requested_assets = set()
        self._asset_revisions = {}
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(2)
        self.assets_pool = QThreadPool(self)
        self.assets_pool.setMaxThreadCount(3)
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

    @Property('QVariantMap', notify=changed)
    def operation(self):
        return self._operation

    @Property('QVariantMap', notify=changed)
    def progressData(self):
        return self._progress

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
                self._work(self.context.assets.load, key, partial(self._asset_loaded, key), asset_job=True)
        return f'image://cached/{kind}/{identity}/{version}?r={self._asset_revisions.get(key, 0)}'

    def _asset_loaded(self, key, data):
        if data:
            self._revision += 1
            self._asset_revisions[key] = self._revision
            self.assetChanged.emit()

    def _work(self, function, args, completed, failed=None, progress=None, asset_job=False):
        worker = FunctionWorker(function, *args, with_progress=progress is not None)
        worker.setAutoDelete(False)
        delivery = _Delivery(self, worker, completed, failed or self._error, progress)
        self._workers[worker] = delivery
        worker.signals.result.connect(delivery.result)
        worker.signals.error.connect(delivery.error)
        worker.signals.finished.connect(delivery.finished)
        worker.signals.progress.connect(delivery.progress)
        (self.assets_pool if asset_job else self.pool).start(worker)

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
        cache = getattr(self.context, 'cache', None)
        starred = cache.starred_match_ids() if cache else set()
        compositions = service.match_compositions(m.match_id for m in matches)
        summaries = []
        for match in matches:
            row = self._summary(match)
            row['starred'] = match.match_id in starred
            composition = compositions.get(match.match_id, {})
            for side in ('allies', 'enemies'):
                row[side] = [name.split(' ')[-1] for name in composition.get(side, ())]
            summaries.append(row)
        progress = service.progress(20)
        player = service.player()
        self._state = {
            'player': {'name': player.riot_id if player.puuid else 'Ton compte', 'rank': player.rank if player.rank not in ('UNAVAILABLE', 'UNRANKED') else 'Classement non disponible',
                       'lp': shown(player.lp, suffix=' LP')},
            'count': len(matches), 'matches': summaries, 'noteScope': player.puuid or player.riot_id,
            'metrics': [{'label': 'Victoires', 'value': shown(progress.win_rate, suffix=' %'), 'hint': '20 dernières parties au maximum'},
                        {'label': 'KDA moyen', 'value': shown(progress.kda, 2), 'hint': '(éliminations + assistances) / morts'},
                        {'label': 'Farm par minute', 'value': shown(progress.cs_per_min, 1), 'hint': 'CS / minute de jeu'}],
            'champions': [{**dict(row), 'rate': shown(row.get('win_rate'), suffix=' %')} for row in progress.champion_rows],
            'roles': sorted({row['role'] for row in summaries}),
            'patches': sorted({row['patch'] for row in summaries}, reverse=True),
            'connection': self._connection_data(),
        }
        self.setProgressWindow(self._progress_window)
        self.changed.emit()
        self.refreshed.emit()

    def _connection_data(self):
        settings = getattr(self.context, 'settings', None)
        if not settings:
            return {}
        status = self.context.local_data.status()
        identity = settings.identity()
        return {'riotId': identity.riot_id if identity else '', 'scope': settings.sync_scope(),
                'keySaved': bool(settings.api_key()), 'keyStatus': {'VALID': 'Connexion vérifiée', 'CONFIGURED_UNVALIDATED': 'Clé enregistrée, à vérifier', 'NOT_CONFIGURED': 'Clé non configurée', 'UNAUTHORIZED_OR_EXPIRED': 'Clé expirée ou refusée'}.get(status.api_status, 'Connexion à vérifier'),
                'matches': status.match_count, 'timelines': status.timeline_count, 'analysed': status.analyzed_match_count,
                'latest': readable_date(status.latest_match_date), 'lastSync': readable_date(status.last_sync_at)}

    @Slot(int)
    def setProgressWindow(self, size):
        if size not in (0, 10, 20, 50):
            return
        self._progress_window = size
        service = self.context.local_data
        summary = service.progress(size or None)
        matches = service.matches()
        selected = list(reversed(matches[:size] if size else matches))
        self._progress = {'window': size, 'count': len(selected), 'comparison': summary.recent_comparison,
                          'metrics': [{'label': label, 'value': shown(value, decimals, suffix)} for label, value, decimals, suffix in (
                              ('Victoires', summary.win_rate, 0, ' %'), ('KDA', summary.kda, 2, ''), ('CS / minute', summary.cs_per_min, 1, ''), ('Morts / partie', summary.deaths_per_match, 1, ''))],
                          'champions': [{**dict(row), 'rate': shown(row.get('win_rate'), suffix=' %')} for row in summary.champion_rows],
                          'labels': [match.champion + ' · ' + match.played_at for match in selected],
                          'victories': rolling_win_rate(selected), 'farm': [m.cs_per_min for m in selected],
                          'deaths': [m.deaths for m in selected]}
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
        own_team = story.get('own_team')
        self._detail['events'] = [{**event, 'time': clock(event['timestamp']), 'label': labels.get(event['label'], event['label']),
                                  'sideLabel': ('Tour détruite' if event['label'] == 'Tour' else 'Équipe non précisée' if own_team not in (100, 200) or event.get('team_id') not in (100, 200) else 'Ton équipe' if event['team_id'] == own_team else 'Équipe adverse')}
                                 for event in story.get('events', ())]
        report = self.context.analysis.get_match_insights(match_id)
        cache = getattr(self.context, 'cache', None)
        self._detail['journal'] = cache.match_journal(match_id) if cache else {'starred': False, 'note': ''}
        self._detail['sections'] = [{'title': player_insight_title(insight), 'summary': player_insight_summary(insight),
                                    'status': {'AVAILABLE': 'Détails disponibles', 'PARTIAL': 'Détails incomplets'}.get(insight.status, 'Données insuffisantes'),
                                    'events': [self._event(event) for event in insight.events]} for insight in report.insights]
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

    @staticmethod
    def _event(event):
        timestamp = event_timestamp_seconds(event)
        return {'title': event_text(event.get('title') or 'Moment observé'), 'subtitle': event_text(event.get('subtitle')),
                'time': clock(timestamp * 1000) if timestamp is not None else '',
                'seconds': timestamp, 'items': [int(item) for item in (event.get('item_ids') or ()) if item],
                'metrics': [{'label': event_text(row.get('label')), 'value': event_text(row.get('value')) if row.get('value') is not None else '—'} for row in (event.get('metrics') or ()) if isinstance(row, dict)],
                'context': [event_text(value) for value in (event.get('context') or ())]}

    @Slot(str, bool, str, result=bool)
    def saveJournal(self, match_id, starred, note):
        if not self.context.local_data.match_detail(match_id):
            return False
        try:
            self.context.cache.save_match_journal(match_id, starred, note)
        except Exception:
            self._notice = 'La note n’a pas pu être enregistrée. Réessaie avant de fermer la partie.'
            self.changed.emit()
            return False
        if self._detail.get('id') == match_id:
            self._detail['journal'] = {'starred': starred, 'note': note.strip()[:1000]}
        for row in self._state['matches']:
            if row['id'] == match_id:
                row['starred'] = starred
        self._notice = 'Note et favori enregistrés sur cet ordinateur.'
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
        if self._operation['working']:
            return
        if not self.context.settings.identity() or not self.context.settings.api_key():
            self._notice = 'Configure ton compte et ta clé Riot avant d’importer des parties.'
            self.changed.emit()
            self.settingsRequested.emit()
            return
        self._operation = {'working': True, 'progress': 0, 'text': 'Préparation de l’import…'}
        self.changed.emit()
        self._work(self.context.sync.sync, (), self._sync_done, self._operation_failed, progress=self._sync_progress)

    def _sync_progress(self, message, value):
        steps = [('Validating Riot', 'Vérification de la connexion…'), ('Fetching profile', 'Récupération du profil…'),
                 ('Fetching match IDs', 'Recherche des parties…'), ('Downloading match', 'Import des parties…'),
                 ('Downloading timeline', 'Import des moments de partie…'), ('Running cached', 'Analyse de tes parties…')]
        self._operation.update({'text': next((label for prefix, label in steps if message.startswith(prefix)), 'Mise à jour de tes parties…'), 'progress': max(0, min(100, value))})
        self.changed.emit()

    def _sync_done(self, result):
        self._operation = {'working': False, 'progress': 100, 'text': ''}
        if result.get('status') == 'COMPLETE':
            self._notice = f"Import terminé : {result.get('new_matches', 0)} nouvelle(s) partie(s), {result.get('existing_matches', 0)} déjà enregistrée(s)."
        else:
            self._notice = 'L’import n’a pas été entièrement terminé. Vérifie la connexion dans Réglages ; les parties enregistrées restent disponibles.'
        self.refresh()

    def _operation_failed(self, _message):
        self._operation = {'working': False, 'progress': 0, 'text': ''}
        self._notice = 'La demande n’a pas pu être terminée. Tes données restent enregistrées.'
        self.changed.emit()

    @Slot(str, int, result=bool)
    def saveAccount(self, riot_id, size):
        if self._operation['working'] or size not in (20, 50, 100):
            return False
        try:
            self.context.settings.save_identity(riot_id, size)
        except (ValueError, OSError):
            self._notice = 'Utilise le format Pseudo#TAG et vérifie que le dossier est accessible.'
            self.changed.emit()
            return False
        self._notice = 'Compte enregistré. Tu peux importer tes parties.'
        self.refresh()
        return True

    @Slot(str, str, int, bool)
    def validateKey(self, key, riot_id, size, activate):
        if self._operation['working']:
            return
        name, separator, tag = riot_id.strip().partition('#')
        if not separator or not name.strip() or not tag.strip() or size not in (20, 50, 100):
            self._notice = 'Renseigne ton identifiant sous la forme Pseudo#TAG.'
            self.changed.emit()
            return
        candidate = key.strip() or self.context.settings.api_key()
        if not candidate:
            self._notice = 'Colle une clé Riot pour vérifier la connexion.'
            self.changed.emit()
            return
        self._operation = {'working': True, 'progress': 0, 'text': 'Vérification de la clé…'}
        self.changed.emit()
        self._work(self.context.sync.validate_key, (candidate, riot_id),
                   partial(self._key_done, candidate, riot_id, size, activate), self._operation_failed)

    def _key_done(self, key, riot_id, size, activate, result):
        self._operation = {'working': False, 'progress': 0, 'text': ''}
        self._notice = _player_validation_message(result)
        if result.ok and activate:
            try:
                self.context.settings.save_identity(riot_id, size)
                self.context.settings.save_api_key(key)
                self._notice = 'Clé vérifiée et enregistrée. Tu peux importer tes parties.'
                self.credentialSaved.emit()
                self.refresh()
            except Exception:
                self._notice = 'Clé vérifiée, mais l’enregistrement n’a pas pu être terminé.'
        self.changed.emit()

    @Slot()
    def dismissNotice(self):
        self._notice = ''
        self.changed.emit()

    def wait_for_workers(self):
        self.pool.waitForDone()
        self.assets_pool.waitForDone()

    def shutdown(self):
        self.pool.clear()
        self.assets_pool.clear()
        self.pool.waitForDone()
        self.assets_pool.waitForDone()
