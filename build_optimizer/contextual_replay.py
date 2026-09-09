"""Chronological Shyvana AP replay; baseline never receives the current game."""
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

from app.paths import DEFAULT_DB_PATH
from services.local_data import LocalDataService
from services.runtime_settings import RuntimeSettingsService
from services.game_context import load_game_context
from build_optimizer.catalog import patch_of
from build_optimizer.context import build_context
from build_optimizer.engine import BuildOptimizer
from build_optimizer.profiles import SUPPORTED_PATCHES
from build_optimizer.replay import TIMESTAMPS, exact_catalogs, mutate_future, validate_recipe_plan
from build_optimizer.signals import build_baseline

ROOT = Path(__file__).resolve().parents[1]


def sources():
    local = LocalDataService(DEFAULT_DB_PATH, settings=RuntimeSettingsService())
    player = local.player()
    assert player.puuid, 'LOCAL_PLAYER_UNAVAILABLE'
    with sqlite3.connect(DEFAULT_DB_PATH) as connection:
        rows = connection.execute(
            '''SELECT m.match_id, m.game_creation FROM matches m JOIN participants p ON p.match_id=m.match_id
               WHERE p.puuid=? AND p.champion_name='Shyvana' AND m.queue_id=420
               ORDER BY m.game_creation, m.match_id''', (player.puuid,)).fetchall()
    for match_id, creation in rows:
        yield creation, load_game_context(DEFAULT_DB_PATH, match_id, player.puuid)


def run():
    catalogs, history, counts, rows = {}, defaultdict(list), Counter(), []
    for creation, game in sources():
        patch = patch_of(game.game_state.get('patch'))
        counts['shyvana_games_seen'] += 1
        if patch not in SUPPORTED_PATCHES:
            counts['unsupported_patch_games'] += 1
            continue
        catalog, champions = catalogs.setdefault(patch, exact_catalogs(patch))
        optimizer = BuildOptimizer(catalog)
        game_contexts = []
        for nominal in TIMESTAMPS:
            frames = [f['timestamp'] for f in game.timeline if f['timestamp'] <= nominal]
            if not frames:
                continue
            timestamp = max(frames)
            context = build_context(game, timestamp, catalog, champions)
            counts['candidate_snapshots'] += 1
            # Future poison must not alter the exact as-of recommendation.
            poisoned = build_context(mutate_future(game, timestamp), timestamp, catalog, champions)
            assert context == poisoned, 'CONTEXTUAL_FUTURE_CONTEXT_LEAKAGE'
            baseline = build_baseline(history[patch], context)
            recommendation = optimizer.recommend(context, baseline)
            assert recommendation == optimizer.recommend(poisoned, baseline), 'CONTEXTUAL_FUTURE_RECOMMENDATION_LEAKAGE'
            # The context enters history only after this game's every timestamp
            # has been scored; abstention is still an observed prior snapshot.
            game_contexts.append(context)
            if recommendation.target_item is None:
                counts['abstentions'] += 1
                continue
            plan = optimizer.planner.plan(recommendation.target_item, context.inventory, context.gold)
            validate_recipe_plan(plan, context.inventory, context.gold, catalog)
            assert recommendation.buy_now == plan.steps, 'BUY_NOW_PLAN_MISMATCH'
            assert recommendation.score == sum(row['contribution'] for row in recommendation.score_breakdown), 'SCORE_RECOMPUTE_ERROR'
            positive = {reason for line in recommendation.score_breakdown for reason in line['reasons']}
            assert set(recommendation.reasons) <= positive, 'UNTRACEABLE_EXPLANATION'
            counts['nonempty_recommendations'] += 1
            rows.append({'match_id': context.match_id, 'game_creation': creation, 'timestamp': timestamp,
                         'patch': patch, 'inventory': context.inventory, 'gold': context.gold,
                         'baseline_samples': baseline.sample_count, 'target_item': recommendation.target_item,
                         'buy_now': [asdict(step) for step in recommendation.buy_now],
                         'alternatives': recommendation.alternatives, 'score': recommendation.score,
                         'reasons': recommendation.reasons, 'warnings': recommendation.warnings,
                         'classification': 'QUESTIONABLE',
                         'classification_reason': 'Requires human product review; actual purchase is not ground truth.'})
        # Add only after every timestamp in this match was evaluated.
        history[patch].extend(game_contexts)
    result = {'status': 'PASS' if counts['nonempty_recommendations'] else 'REVIEW_REQUIRED',
              'counts': dict(counts), 'invalid_purchases': 0, 'future_leakage': 0,
              'score_recomputation_errors': 0, 'untraceable_explanations': 0,
              'rows': rows, 'model_kind': 'DETERMINISTIC_CONTEXTUAL_HEURISTIC_V1'}
    folder = ROOT / 'logs/build_optimizer'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'contextual_replay.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, ensure_ascii=False, indent=2))
    return result


if __name__ == '__main__':
    run()
