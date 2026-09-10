"""Read-only post-game presentation bridge for the Build Optimizer.

This module keeps local SQLite/catalog access outside the optimizer engine. It
never downloads a catalog: a missing exact local patch is an explicit UI
abstention rather than a network request or a latest-patch fallback.
"""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3

from app.paths import PROJECT_ROOT
from build_optimizer.catalog import CatalogView, patch_of
from build_optimizer.context import build_context
from build_optimizer.engine import BuildOptimizer
from build_optimizer.profiles import champion_profile
from build_optimizer.signals import build_baseline, phase
from knowledge.champion_knowledge import build_champion_record
from knowledge.item_knowledge import build_item_knowledge_catalog
from services.game_context import ContextUnavailable, load_game_context
from services.local_data import LocalDataService


CATALOGS = PROJECT_ROOT / '.cache' / 'zircon' / 'stabilization-catalogs'


def _clock(timestamp: int) -> str:
    return f'{timestamp // 60000:02d}:{timestamp // 1000 % 60:02d}'


class BuildOptimizerPresentationService:
    """Creates a local, latest-observed-frame recommendation for the UI."""

    def __init__(self, local_data: LocalDataService):
        self.local_data = local_data
        self._catalogs: dict[str, tuple[CatalogView, dict]] = {}

    def _catalog(self, patch: str) -> tuple[CatalogView, dict] | None:
        if patch in self._catalogs:
            return self._catalogs[patch]
        version = patch + '.1'
        item_path, champion_path = CATALOGS / version / 'item.json', CATALOGS / version / 'champion.json'
        if not item_path.exists() or not champion_path.exists():
            return None
        items, champions = json.loads(item_path.read_text(encoding='utf-8')), json.loads(champion_path.read_text(encoding='utf-8'))
        if items.get('version') != version or champions.get('version') != version:
            return None
        knowledge = build_item_knowledge_catalog(version, raw_items=items.get('data') or {}, versions=[version])
        info = {'requested_game_version': version, 'resolved_ddragon_version': version,
                'resolution_status': 'EXACT_VERSION', 'fallback_used': False}
        records = {name: build_champion_record(name, row, {}, info, 'fr_FR')
                   for name, row in (champions.get('data') or {}).items()}
        result = CatalogView(knowledge, patch), records
        self._catalogs[patch] = result
        return result

    @staticmethod
    def _candidate_timestamps(game) -> tuple[int, ...]:
        """Match the audited replay snapshots, latest first, without using a future frame."""
        frame_times = sorted({frame.get('timestamp') for frame in game.timeline
                              if type(frame.get('timestamp')) is int and frame['timestamp'] >= 0})
        candidates = {max((value for value in frame_times if value <= nominal), default=None)
                      for nominal in (600000, 900000, 1200000, 1500000)}
        return tuple(sorted((value for value in candidates if value is not None), reverse=True))

    def recommendation_for_match(self, match_id: str) -> dict:
        """Return a serializable UI payload or a reasoned abstention."""
        player = self.local_data.player()
        detail = self.local_data.match_detail(match_id)
        if not player.puuid or detail is None:
            return {'status': 'UNAVAILABLE', 'reason': 'PARTIE_OU_JOUEUR_LOCAL_INDISPONIBLE'}
        try:
            game = load_game_context(self.local_data.db_path, match_id, player.puuid)
        except (ContextUnavailable, OSError, sqlite3.Error) as error:
            return {'status': 'UNAVAILABLE', 'reason': f'CONTEXTE_LOCAL_INDISPONIBLE:{type(error).__name__}'}
        patch = patch_of(game.game_state.get('patch'))
        profile = champion_profile(game.player.get('championName'), patch)
        if patch is None or profile is None:
            return {'status': 'UNAVAILABLE', 'reason': 'CHAMPION_OU_PATCH_NON_SUPPORTÉ',
                    'champion': game.player.get('championName'), 'patch': patch}
        catalog_data = self._catalog(patch)
        if catalog_data is None:
            return {'status': 'UNAVAILABLE', 'reason': 'CATALOGUE_EXACT_LOCAL_INDISPONIBLE', 'patch': patch}
        catalog, champions = catalog_data
        timestamps = self._candidate_timestamps(game)
        if not timestamps:
            return {'status': 'UNAVAILABLE', 'reason': 'AUCUNE_FRAME_OBSERVÉE', 'patch': patch}
        with sqlite3.connect(self.local_data.db_path) as connection:
            row = connection.execute('SELECT game_creation FROM matches WHERE match_id=?', (match_id,)).fetchone()
        if not row:
            return {'status': 'UNAVAILABLE', 'reason': 'PARTIE_LOCALE_INTRouvABLE'}
        prior_cache = {}
        latest = None
        for timestamp in timestamps:
            context = build_context(game, timestamp, catalog, champions)
            bucket = phase(timestamp)
            if bucket not in prior_cache:
                prior_cache[bucket] = self._prior_contexts(player.puuid, row[0], context, catalog, champions)
            result = self._recommend(context, catalog, profile, prior_cache[bucket])
            latest = latest or result
            if result['status'] == 'SUPPORTED_HEURISTIC':
                return result
        return latest or {'status': 'UNAVAILABLE', 'reason': 'CONTEXTE_DE_RECOMMANDATION_INDISPONIBLE'}

    def _prior_contexts(self, puuid: str, creation: int, context, catalog, champions) -> list:
        """Build only pre-match same-patch contexts in the same phase bucket."""
        with sqlite3.connect(self.local_data.db_path) as connection:
            rows = connection.execute(
                '''SELECT m.match_id FROM matches m JOIN participants p ON p.match_id=m.match_id
                   WHERE p.puuid=? AND m.queue_id=420 AND m.game_creation<?
                     AND m.game_version LIKE ?
                   ORDER BY m.game_creation, m.match_id''',
                (puuid, creation, context.patch + '.%'),
            ).fetchall()
        priors = []
        for (prior_id,) in rows:
            try:
                prior = load_game_context(self.local_data.db_path, prior_id, puuid)
                if patch_of(prior.game_state.get('patch')) != context.patch:
                    continue
                timestamps = [frame.get('timestamp') for frame in prior.timeline
                              if type(frame.get('timestamp')) is int and phase(frame['timestamp']) == phase(context.timestamp)]
                if timestamps:
                    priors.append(build_context(prior, max(timestamps), catalog, champions))
            except (ContextUnavailable, OSError, sqlite3.Error, ValueError):
                continue
        return priors

    @staticmethod
    def _recommend(context, catalog, profile, priors) -> dict:
        baseline = build_baseline(priors, context)
        recommendation = BuildOptimizer(catalog).recommend(context, baseline)
        payload = recommendation.to_dict()
        name = lambda item_id: catalog.items[item_id].name if item_id in catalog.items else str(item_id)
        payload.update({
            'status': recommendation.status,
            'champion': context.champion,
            'profile': profile.version,
            'patch': context.patch,
            'snapshot_timestamp': context.timestamp,
            'snapshot_label': _clock(context.timestamp),
            'baseline_samples': baseline.sample_count,
            'target_name': name(recommendation.target_item) if recommendation.target_item else None,
            'buy_now_named': tuple({'item_id': step.item_id, 'name': name(step.item_id), 'cost': step.cost}
                                  for step in recommendation.buy_now),
            'alternatives_named': tuple({'item_id': row['target_item'], 'name': name(row['target_item']),
                                         'score': row['score'], 'reasons': tuple(row['positive_reasons'])}
                                        for row in recommendation.alternatives),
            # Observations at exactly the decision snapshot.  They explain
            # contextual scoring without leaking final-game information into it.
            'enemy_snapshot': tuple({'champion': enemy.champion, 'level': enemy.level,
                                     'health_max': enemy.observed_stats.get('healthMax'),
                                     'armor': enemy.observed_stats.get('armor'),
                                     'magic_resist': enemy.observed_stats.get('magicResist')}
                                    for enemy in context.enemies),
        })
        return payload
