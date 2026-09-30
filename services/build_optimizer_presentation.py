"""Read-only post-game presentation bridge for the Build Optimizer.

This module keeps local SQLite/catalog access outside the optimizer engine. It
never downloads a catalog: a missing exact local patch is an explicit UI
abstention rather than a network request or a latest-patch fallback.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sqlite3

from app.paths import PROJECT_ROOT
from build_optimizer.catalog import CatalogView, patch_of
from build_optimizer.context import build_context
from build_optimizer.engine import BuildOptimizer
from build_optimizer.profiles import SUPPORTED_PATCHES, champion_profile
from build_optimizer.signals import build_baseline, phase
from knowledge.champion_knowledge import build_champion_record
from knowledge.item_knowledge import build_item_knowledge_catalog
from services.game_context import ContextUnavailable, load_game_context
from services.local_data import LocalDataService


CATALOGS = PROJECT_ROOT / '.cache' / 'zircon' / 'stabilization-catalogs'


def _clock(timestamp: int) -> str:
    return f'{timestamp // 60000:02d}:{timestamp // 1000 % 60:02d}'


_PLAYER_TRAITS = {
    'ABILITY_HASTE': 'la réduction du délai de récupération de tes compétences',
    'AD': 'les dégâts physiques', 'AP': 'la puissance magique',
    'ARMOR': 'l’armure', 'ATTACK_SPEED': 'la vitesse d’attaque',
    'BURST': 'les dégâts rapides', 'CRIT': 'les coups critiques',
    'DEFENSE_MR': 'la protection contre les dégâts magiques',
    'HEALTH': 'les points de vie', 'LIFESTEAL': 'le vol de vie',
    'MR': 'la résistance magique', 'ON_HIT': 'les effets à l’impact',
    'PERCENT_MAGIC_PEN': 'la pénétration magique', 'RAW_DAMAGE': 'les dégâts directs',
    'SURVIVABILITY': 'la résistance en combat', 'SUSTAINED_DAMAGE': 'les dégâts dans les combats qui durent',
    'UTILITY': 'des outils supplémentaires',
}


def player_facing_reasons(reasons, champion: str = '') -> tuple[str, ...]:
    """Translate engine scoring traces into concise explanations for players."""
    readable = []
    for reason in reasons or ():
        text = str(reason)
        direction = re.match(r"Direction ([A-Z_]+) compatible avec (?:le profil [\w_]+|l’archétype .+)\.", text)
        if direction:
            trait = _PLAYER_TRAITS.get(direction.group(1))
            if trait:
                readable.append(f"Cet objet apporte {trait}" + (f", utile pour {champion}." if champion else "."))
            continue
        folded = text.casefold()
        if 'composition observée peut favoriser burst / pénétration magique plate' in folded:
            readable.append("Les adversaires présents peuvent rendre utiles les dégâts rapides et la pénétration magique.")
        elif 'composition observée peut favoriser crit / burst / pénétration physique plate' in folded:
            readable.append("Les adversaires présents peuvent rendre utiles les coups critiques, les dégâts rapides et la pénétration d’armure.")
        elif 'menace magique relative est très élevée' in folded:
            readable.append("Les dégâts magiques adverses étaient particulièrement élevés à ce moment.")
        elif 'menace physique relative est très élevée' in folded:
            readable.append("Les dégâts physiques adverses étaient particulièrement élevés à ce moment.")
        elif 'pression hp ennemie est élevée dans la référence historique' in folded:
            readable.append("Tes adversaires avaient souvent beaucoup de points de vie dans tes parties précédentes.")
        elif 'résistance magique ennemie est élevée dans la référence historique' in folded:
            readable.append("Tes adversaires avaient souvent beaucoup de résistance magique dans tes parties précédentes.")
        elif 'armure ennemie est élevée dans la référence historique' in folded:
            readable.append("Tes adversaires avaient souvent beaucoup d’armure dans tes parties précédentes.")
        elif 'delta de gold d’équipe est bas dans la référence historique' in folded:
            readable.append("Dans tes parties précédentes, ton équipe avait souvent peu d’avance en or à ce moment.")
        elif 'delta de gold d’équipe est positif dans la référence historique' in folded:
            readable.append("Dans tes parties précédentes, ton équipe était souvent en avance en or à ce moment.")
        elif 'item complet est réalisable dans le modèle de recette' in folded:
            readable.append("Tu avais assez d’or pour terminer cet objet à ce moment.")
        elif 'progrès de recette réalisable est disponible' in folded:
            readable.append("Avec l’or dont tu disposais, tu pouvais déjà avancer dans l’achat de cet objet.")
        # Engine/model plumbing is intentionally omitted from player copy.
    return tuple(dict.fromkeys(readable)) or (
        'Cette piste s’appuie sur les objets, l’or et les adversaires observés à ce moment.',
    )


class BuildOptimizerPresentationService:
    """Creates a local, latest-observed-frame recommendation for the UI."""

    def __init__(self, local_data: LocalDataService):
        self.local_data = local_data
        self._catalogs: dict[str, tuple[CatalogView, dict]] = {}

    @staticmethod
    def _unavailable(reason_code: str, **details) -> dict:
        messages = {
            'PARTIE_OU_JOUEUR_LOCAL_INDISPONIBLE': 'Cette partie ou ce profil joueur n’est pas disponible.',
            'PATCH_NON_SUPPORTÉ': 'Cette partie vient d’une version du jeu que le conseil ne reconnaît pas encore.',
            'CATALOGUE_EXACT_LOCAL_INDISPONIBLE': 'Les informations sur les objets de cette version ne sont pas disponibles.',
            'CHAMPION_SANS_CLASSE_DATA_DRAGON_FIABLE': 'Je n’ai pas encore assez d’informations sur ce champion pour te conseiller.',
            'AUCUNE_FRAME_OBSERVÉE': 'Je n’ai pas assez de moments enregistrés pour situer un conseil dans cette partie.',
            'PARTIE_LOCALE_INTRouvable': 'Cette partie n’est plus disponible.',
            'CONTEXTE_DE_RECOMMANDATION_INDISPONIBLE': 'Les informations de cette partie ne suffisent pas pour proposer un conseil fiable.',
        }
        if reason_code.startswith('CONTEXTE_LOCAL_INDISPONIBLE:'):
            message = 'Impossible de lire les détails de cette partie sur cet ordinateur.'
        else:
            message = messages.get(reason_code, 'Les données disponibles ne suffisent pas pour proposer un conseil fiable.')
        return {'status': 'UNAVAILABLE', 'reason': message, 'reason_code': reason_code, **details}

    @staticmethod
    def _abstention_reasons(warnings) -> tuple[str, ...]:
        warnings = set(warnings or ())
        reasons = []
        if 'INVENTORY_UNRELIABLE' in warnings:
            reasons.append('Je ne peux pas confirmer les objets que tu avais à ce moment-là ; je préfère éviter un doublon ou un achat incorrect.')
        if 'CURRENT_GOLD_UNRESOLVED' in warnings:
            reasons.append('Je ne peux pas confirmer combien d’or tu avais à ce moment-là.')
        if 'HISTORICAL_BASELINE_UNAVAILABLE' in warnings:
            reasons.append('Je n’ai pas assez de parties précédentes comparables pour étayer ce conseil.')
        if 'UNSUPPORTED_QUEUE' in warnings:
            reasons.append('Ce mode de jeu n’est pas encore pris en charge.')
        if 'CONTEXT_CATALOG_PATCH_MISMATCH' in warnings:
            reasons.append('Les informations de la partie ne correspondent pas à cette version du jeu.')
        return tuple(reasons) or ('Je n’ai pas assez d’informations pour te proposer un achat précis.',)

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
            return self._unavailable('PARTIE_OU_JOUEUR_LOCAL_INDISPONIBLE')
        try:
            game = load_game_context(self.local_data.db_path, match_id, player.puuid)
        except (ContextUnavailable, OSError, sqlite3.Error) as error:
            return self._unavailable(f'CONTEXTE_LOCAL_INDISPONIBLE:{type(error).__name__}')
        patch = patch_of(game.game_state.get('patch'))
        if patch not in SUPPORTED_PATCHES:
            return self._unavailable('PATCH_NON_SUPPORTÉ', champion=game.player.get('championName'), patch=patch)
        catalog_data = self._catalog(patch)
        if catalog_data is None:
            return self._unavailable('CATALOGUE_EXACT_LOCAL_INDISPONIBLE', patch=patch)
        catalog, champions = catalog_data
        champion = game.player.get('championName')
        champion_record = champions.get(champion) or {}
        profile = champion_profile(champion, patch, champion_record.get('tags', ()))
        if profile is None:
            return self._unavailable('CHAMPION_SANS_CLASSE_DATA_DRAGON_FIABLE', champion=champion, patch=patch)
        timestamps = self._candidate_timestamps(game)
        if not timestamps:
            return self._unavailable('AUCUNE_FRAME_OBSERVÉE', patch=patch)
        with sqlite3.connect(self.local_data.db_path) as connection:
            row = connection.execute('SELECT game_creation FROM matches WHERE match_id=?', (match_id,)).fetchone()
        if not row:
            return self._unavailable('PARTIE_LOCALE_INTRouvable')
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
        return latest or self._unavailable('CONTEXTE_DE_RECOMMANDATION_INDISPONIBLE')

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
        if recommendation.status != 'SUPPORTED_HEURISTIC':
            payload['reason'] = ' '.join(BuildOptimizerPresentationService._abstention_reasons(recommendation.warnings))
            payload['reason_code'] = 'RECOMMENDATION_ABSTAINED'
        name = lambda item_id: catalog.items[item_id].name if item_id in catalog.items else str(item_id)
        payload.update({
            'status': recommendation.status,
            'champion': context.champion,
            'profile': profile.version,
            'profile_archetype': profile.archetype,
            'profile_scope': ('GENERIC_CLASS_ARCHETYPE' if profile.version == 'generic_class_build_profile_v1'
                             else 'CHAMPION_SPECIFIC_REVIEWED'),
            'patch': context.patch,
            'snapshot_timestamp': context.timestamp,
            'snapshot_label': _clock(context.timestamp),
            'baseline_samples': baseline.sample_count,
            'reasons': player_facing_reasons(recommendation.reasons, context.champion),
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
