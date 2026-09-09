"""Real prefix replay and adversarial future mutation; no Riot credential use."""
import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path

from app.paths import DEFAULT_DB_PATH
from app.stabilization_golden_checks import catalog_json, SNAPSHOT
from knowledge.champion_knowledge import build_champion_record
from knowledge.item_knowledge import build_item_knowledge_catalog
from services.game_context import GameContext, load_game_context
from services.local_data import LocalDataService
from services.runtime_settings import RuntimeSettingsService
from build_optimizer.catalog import CatalogView, patch_of
from build_optimizer.context import build_context
from build_optimizer.engine import BuildOptimizer
from build_optimizer.purchase import RecipePlanner

ROOT = Path(__file__).resolve().parents[1]
TIMESTAMPS = (600000, 900000, 1200000, 1500000)


def golden_sources():
    expected = json.loads((ROOT / 'tests/fixtures/golden_games/expected.json').read_text(encoding='utf-8'))
    for row in expected:
        pair = []
        for kind in ('match', 'timeline'):
            payload = (SNAPSHOT / row['match_id'] / f'{kind}.json').read_bytes()
            assert hashlib.sha256(payload).hexdigest() == row[f'{kind}_sha256'], 'GOLDEN_SOURCE_DRIFT'
            pair.append(json.loads(payload))
        match, timeline = pair
        player = next(p for p in match['info']['participants'] if p['participantId'] == row['participant_id'])
        yield GameContext.from_raw(match, timeline, player['puuid'])


def batch_sources():
    local = LocalDataService(DEFAULT_DB_PATH, settings=RuntimeSettingsService())
    player = local.player()
    assert player.puuid, 'LOCAL_PLAYER_UNAVAILABLE'
    matches = local.matches()
    assert matches, 'LOCAL_HISTORY_UNAVAILABLE'
    for match in matches:
        yield load_game_context(DEFAULT_DB_PATH, match.match_id, player.puuid)


def exact_catalogs(patch):
    version = patch + '.1'
    raw_items = catalog_json(version, 'item.json')
    assert raw_items['version'] == version, 'ITEM_SOURCE_VERSION_MISMATCH'
    item_catalog = build_item_knowledge_catalog(version, raw_items=raw_items['data'], versions=[version])
    raw_champions = catalog_json(version, 'champion.json')
    assert raw_champions['version'] == version, 'CHAMPION_SOURCE_VERSION_MISMATCH'
    info = {'requested_game_version': version, 'resolved_ddragon_version': version,
            'resolution_status': 'EXACT_VERSION', 'fallback_used': False}
    # Only champion identity is consumed. No detail-file/kit completeness claim.
    champions = {key: build_champion_record(key, value, {}, info, 'fr_FR')
                 for key, value in raw_champions['data'].items()}
    return CatalogView(item_catalog, patch), champions


def mutate_future(game, timestamp):
    altered = deepcopy(game)
    for player in (altered.player, *altered.allies, *altered.enemies):
        player.update(win=not bool(player.get('win')), champLevel=99, goldEarned=999999,
                      kills=999, deaths=999, totalDamageDealtToChampions=999999)
        for slot in range(7):
            player[f'item{slot}'] = 999999
    altered.game_state['duration_seconds'] = 999999
    altered.game_state['role'] = 'FUTURE_ROLE'
    for frame in altered.timeline:
        if frame['timestamp'] > timestamp:
            for values in frame.get('participantFrames', {}).values():
                values.update(currentGold=999999, level=99, championStats={'armor': 999999})
    return replace(altered, events=tuple(e for e in altered.events if e['timestamp'] <= timestamp) + (
        {'timestamp': timestamp + 1, 'type': 'ITEM_PURCHASED', 'participantId': altered.player['participantId'], 'itemId': 999999},),
        items=(999999,) * 7, gold=({'timestamp': timestamp + 1, 'current': 999999},),
        objectives=(), issues=('FUTURE_INFORMATION_POISONED',))


def validate_recipe_plan(plan, inventory, budget, catalog):
    """Independent invoice/counter checks, not equality with planner output."""
    def recipe_tree(item_id, ancestors=()):
        assert item_id in catalog.items and item_id not in ancestors, 'INVALID_RECIPE_GRAPH'
        item = catalog.items[item_id]
        assert not item.structural_blockers, 'ITEM_STRUCTURALLY_BLOCKED'
        children = tuple(recipe_tree(c, (*ancestors, item_id)) for c in item.components)
        assert item.total_cost == item.purchase_cost + sum(
            catalog.items[c].total_cost for c in item.components), 'INCONSISTENT_RECIPE_PRICE'
        return item_id, children

    def check_consumed(tree, consumed):
        # Match claimed credits to a cut through the recipe tree: accepting a
        # built component forbids also crediting its descendants on that branch.
        # Multiplicity is preserved. No production consumption helper is called.
        unassigned = Counter(consumed)

        def assign(node):
            item_id, children = node
            if unassigned[item_id]:
                unassigned[item_id] -= 1
            else:
                for child in children:
                    assign(child)

        for child in tree[1]:
            assign(child)
        assert not +unassigned, 'INVALID_RECIPE_COMPONENTS'

    target_tree = recipe_tree(plan.target_item)

    def node_ids(tree):
        item_id, children = tree
        return {item_id, *(node_id for child in children for node_id in node_ids(child))}

    valid_step_ids = node_ids(target_tree)
    remaining = Counter(inventory)
    spent = 0
    for step in plan.steps:
        assert step.item_id in valid_step_ids, 'STEP_NOT_IN_TARGET_RECIPE'
        tree = recipe_tree(step.item_id)
        check_consumed(tree, step.consumed)
        consumed = Counter(step.consumed)
        assert not consumed - remaining, 'CONSUMED_COMPONENT_NOT_OWNED'
        price = catalog.items[step.item_id].total_cost - sum(catalog.items[i].total_cost for i in step.consumed)
        assert step.cost == price and price >= 0, 'INVALID_INCREMENTAL_PRICE'
        spent += price
        assert spent <= budget, 'BUDGET_EXCEEDED'
        remaining.subtract(consumed)
        remaining[step.item_id] += 1
        remaining = +remaining
        assert Counter(step.inventory_after) == remaining, 'INVENTORY_TRANSITION_MISMATCH'
        # Conservative slot bound: stackable mechanics are not used to expand it.
        assert sum(remaining.values()) <= 6, 'SLOT_CAPACITY_EXCEEDED'
    assert spent == plan.total_spend, 'TOTAL_SPEND_MISMATCH'
    assert plan.target_completed == (plan.target_item in remaining), 'COMPLETION_MISMATCH'


def run(mode):
    catalogs = {}
    counts = Counter()
    notes = Counter()
    rows = []
    sources = golden_sources() if mode == 'golden' else batch_sources()
    for game in sources:
        counts['games'] += 1
        patch = patch_of(game.game_state.get('patch'))
        assert patch, 'PATCH_UNAVAILABLE'
        if patch not in catalogs:
            catalogs[patch] = exact_catalogs(patch)
        catalog, champions = catalogs[patch]
        optimizer = BuildOptimizer(catalog)
        planner = RecipePlanner(catalog)
        for timestamp in TIMESTAMPS:
            counts['requested_timestamps'] += 1
            context = build_context(game, timestamp, catalog, champions)
            recommendation = optimizer.recommend(context)
            changed_context = build_context(mutate_future(game, timestamp), timestamp, catalog, champions)
            assert context == changed_context, 'FUTURE_CONTEXT_LEAKAGE'
            assert recommendation == optimizer.recommend(changed_context), 'FUTURE_RECOMMENDATION_LEAKAGE'
            counts['temporal_invariance_pairs'] += 1
            # Verify observed inventory responds to removal of prefix items.
            item_events = [e for e in game.events if e['timestamp'] <= timestamp
                           and e.get('type') == 'ITEM_PURCHASED' and e.get('participantId') == game.player['participantId']]
            if item_events and context.inventory:
                stripped = replace(game, events=tuple(e for e in game.events if e.get('type') not in ('ITEM_PURCHASED','ITEM_UNDO','ITEM_SOLD','ITEM_DESTROYED')))
                assert build_context(stripped, timestamp, catalog, champions).inventory != context.inventory
                counts['prefix_sensitivity_checks'] += 1
            if context.gold is not None:
                sample = next(f for f in game.timeline if f['timestamp'] == timestamp)
                assert context.gold == sample['participantFrames'][str(game.player['participantId'])]['currentGold']
                counts['exact_budget_samples'] += 1
            if timestamp > game.timeline[-1]['timestamp']:
                counts['timestamps_after_last_frame'] += 1
            notes.update(context.warnings)
            plans_checked = 0
            # Nominal minute and observed frame are distinct times. A previous
            # gold sample must never be combined with later inventory events.
            asof = build_context(game, context.sample_timestamp, catalog, champions) if context.sample_timestamp is not None else None
            if asof is not None:
                changed_asof = build_context(mutate_future(game, asof.timestamp), asof.timestamp, catalog, champions)
                assert asof == changed_asof, 'ASOF_TEMPORAL_LEAKAGE'
                counts['asof_temporal_invariance_pairs'] += 1
                if asof.gold is not None:
                    counts['asof_observed_budget_samples'] += 1
            # These diagnostics are not recommendations at the nominal timestamp.
            if asof and asof.gold is not None and asof.inventory_status == 'OBSERVED_PREFIX' and not catalog.blockers:
                plans = planner.candidates(asof.inventory, asof.gold)
                for plan in plans:
                    if plan.status == 'BLOCKED':
                        continue
                    validate_recipe_plan(plan, asof.inventory, asof.gold, catalog)
                    plans_checked += 1
                    counts['recipe_plans_checked'] += 1
                    counts['recipe_steps_checked'] += len(plan.steps)
                    if plan.target_completed:
                        counts['recipe_targets_completed_in_model'] += 1
            assert recommendation.target_item is None and not recommendation.buy_now
            counts['abstentions'] += 1
            rows.append({'match_id': context.match_id, 'timestamp': timestamp, 'patch': patch,
                         'sample_timestamp': context.sample_timestamp, 'context_status': context.status,
                         'recipe_plan_timestamp': asof.timestamp if asof else None,
                         'inventory_status': context.inventory_status, 'warnings': context.warnings,
                         'recipe_plans_checked': plans_checked, 'recommendation': recommendation.to_dict(),
                         'evaluation': 'QUESTIONABLE',
                         'evaluation_reason': 'ABSTENTION_SAFE_BUT_REQUESTED_CONTEXTUAL_DECISION_UNAVAILABLE'})
        print(f'{mode}: {counts["games"]} games / {counts["requested_timestamps"]} timestamp checks', flush=True)
    assert counts['games'] > 0 and counts['temporal_invariance_pairs'] > 0, 'NO_REAL_REPLAY'
    result = {'mode': mode, 'counts': dict(counts), 'context_warnings': dict(notes),
              'temporal_integrity': 'PASS',
              'recipe_invariants': 'PASS' if counts['recipe_plans_checked'] else 'NOT_EXERCISED_NO_ADMISSIBLE_INVENTORY',
              'contextual_recommendations_validated': 0, 'invalid_buy_now': 0,
              'purchase_legality': 'BLOCKED_NOT_VALIDATED_BY_EMPTY_BUY_NOW',
              'scoring_quality': 'BLOCKED', 'freeze': 'NO FREEZE', 'rows': rows}
    folder = ROOT / 'logs/build_optimizer'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f'{mode}_replay.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('golden', 'batch'), default='golden')
    run(parser.parse_args().mode)
