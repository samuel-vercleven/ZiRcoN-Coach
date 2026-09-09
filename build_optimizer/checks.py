"""Synthetic contracts test mechanics, not fabricated champion recommendations."""
from copy import deepcopy
from dataclasses import replace
import json
import unittest

from knowledge.item_knowledge import build_item_knowledge_catalog
from services.game_context import GameContext
from build_optimizer.catalog import CatalogView
from build_optimizer.context import build_context
from build_optimizer.purchase import RecipePlanner
from build_optimizer.scoring import BUILD_SCORE_WEIGHTS, score_recipe
from build_optimizer.engine import BuildOptimizer


VERSION = '16.16.1'


def item(name, total, base=None, components=(), **extra):
    return {'name': name, 'gold': {'total': total, 'base': total if base is None else base,
                                  'purchasable': True}, 'maps': {'11': True},
            'tags': ['Damage'], 'stats': {'FlatPhysicalDamageMod': 10},
            'description': '', 'from': [str(i) for i in components], **extra}


def catalog(extra=None):
    # Synthetic prices/IDs are fixture facts, never production item advice.
    raw = {'1': item('A', 100), '2': item('B', 200),
           '3': item('AB', 350, 50, (1, 2)), '4': item('ABAA', 700, 150, (3, 1, 1)),
           '5': item('Repeated', 250, 50, (1, 1)),
           '6': item('Filler', 120), '7': item('Filler2', 120),
           '8': item('Filler3', 120), '9': item('Filler4', 120),
           '10': item('Filler5', 120), '11': item('ZeroCombine', 300, 0, (1, 2))}
    raw.update(extra or {})
    return CatalogView(build_item_knowledge_catalog(VERSION, raw_items=raw, versions=[VERSION]), VERSION)


def game(events=()):
    player = {'puuid': 'p', 'participantId': 1, 'teamId': 100, 'teamPosition': 'JUNGLE',
              'championName': 'Shyvana', 'kills': 0, 'deaths': 0, 'assists': 0,
              'win': False, 'totalMinionsKilled': 0, 'neutralMinionsKilled': 0,
              'item0': 99999, 'champLevel': 18, 'goldEarned': 30000}
    enemy = {**player, 'puuid': 'q', 'participantId': 2, 'teamId': 200}
    frames = [{'timestamp': ts, 'participantFrames': {
        str(pid): {'participantId': pid, 'totalGold': 1500, 'currentGold': 500,
                   'level': 6, 'xp': 900, 'minionsKilled': 0, 'jungleMinionsKilled': 10,
                   'championStats': {'healthMax': 1000, 'armor': 40}}
        for pid in (1, 2)}, 'events': []} for ts in (0, 60000, 120000)]
    for event in events:
        frames[min(2, event['timestamp'] // 60000)]['events'].append(event)
    raw = {'metadata': {'matchId': 'TEST'}, 'info': {'participants': [player, enemy],
           'gameDuration': 120, 'gameVersion': VERSION, 'queueId': 420}}
    timeline = {'metadata': {'matchId': 'TEST'}, 'info': {'frames': frames}}
    return GameContext.from_raw(raw, timeline, 'p')


def event(ts, kind='ITEM_PURCHASED', item_id=1, pid=1, **fields):
    return {'timestamp': ts, 'type': kind, 'itemId': item_id, 'participantId': pid, **fields}


CHAMPIONS = {'Shyvana': {'ddragon_version': VERSION, 'version_fallback_used': False}}


class ContextChecks(unittest.TestCase):
    def test_projection_uses_frame_not_final_values(self):
        context = build_context(game(), 60000, catalog(), CHAMPIONS)
        self.assertEqual(context.level, 6)
        self.assertEqual(context.gold, 500)
        self.assertEqual(context.inventory, ())
        serialized = json.dumps(context.to_dict())
        for key in ('goldEarned', 'champLevel', 'win', 'duration_seconds', 'puuid'):
            self.assertNotIn(key, serialized)

    def test_future_mutation_does_not_change_context_or_output(self):
        source = game([event(30000)])
        changed = deepcopy(source)
        changed.player.update(item0=4, kills=100, deaths=100, win=True, goldEarned=999999)
        changed.game_state.update(duration_seconds=99999, role='TOP')
        changed.timeline[-1]['participantFrames']['1'].update(currentGold=999999, level=18)
        changed = replace(changed, events=(*changed.events, event(90000, item_id=4)), issues=('FUTURE_ERROR',))
        cat = catalog()
        first = build_context(source, 60000, cat, CHAMPIONS)
        second = build_context(changed, 60000, cat, CHAMPIONS)
        self.assertEqual(first, second)
        self.assertEqual(BuildOptimizer(cat).recommend(first), BuildOptimizer(cat).recommend(second))
        # Positive control: the prefix does affect observed inventory.
        earlier = replace(source, events=(event(30000, item_id=2),))
        self.assertNotEqual(first.inventory, build_context(earlier, 60000, cat, CHAMPIONS).inventory)

    def test_invalid_timestamp(self):
        for ts in (-1, True, float('nan'), float('inf'), '60000'):
            with self.subTest(ts=ts), self.assertRaisesRegex(ValueError, 'INVALID_TIMESTAMP'):
                build_context(game(), ts, catalog(), CHAMPIONS)

    def test_missing_or_stale_gold_is_not_spendable(self):
        source = game()
        for ts in (59000, 61000, 150000):
            self.assertIsNone(build_context(source, ts, catalog(), CHAMPIONS).gold)
        source.timeline[1]['participantFrames']['1']['currentGold'] = None
        self.assertIsNone(build_context(source, 60000, catalog(), CHAMPIONS).gold)

    def test_same_timestamp_gold_order_unknown(self):
        context = build_context(game([event(60000)]), 60000, catalog(), CHAMPIONS)
        self.assertIsNone(context.gold)
        self.assertIn('GOLD_ITEM_SAME_TIMESTAMP_ORDER_UNRESOLVED', context.warnings)

    def test_realistic_frame_jitter_and_separate_asof_budget(self):
        source = game([event(59999)])
        source.timeline[1]['timestamp'] = 60003
        nominal = build_context(source, 60000, catalog(), CHAMPIONS)
        self.assertIsNone(nominal.gold)
        asof = build_context(source, 60003, catalog(), CHAMPIONS)
        self.assertEqual(asof.gold, 500)
        self.assertNotIn('PREFIX_FRAME_GAP', asof.warnings)
        before = build_context(source, nominal.sample_timestamp, catalog(), CHAMPIONS)
        self.assertEqual(before.timestamp, 0)
        self.assertEqual(before.inventory, ())  # No mixing old gold with newer purchases.

    def test_missing_frame_unknown_champion_and_item(self):
        source = game([event(1000, item_id=888)])
        source.timeline[1]['participantFrames'].pop('2')
        context = build_context(source, 60000, catalog(), {})
        self.assertIn('UNKNOWN_OR_PATCH_MISMATCH_CHAMPION', context.warnings)
        self.assertIn('UNKNOWN_INVENTORY_ITEM', context.warnings)
        self.assertIn('ENEMY_INFORMATION_PARTIAL', context.warnings)

    def test_prefix_inventory_reuses_frozen_undo(self):
        source = game([event(1000), event(2000, item_id=2), event(3000, item_id=3),
                       event(4000, 'ITEM_UNDO', None, beforeId=3, afterId=0)])
        context = build_context(source, 60000, catalog(), CHAMPIONS)
        self.assertEqual(context.inventory, (1, 2))

    def test_ambiguous_destroy_is_not_retroactively_resolved(self):
        source = game([event(1000), event(2000, 'ITEM_DESTROYED')])
        context = build_context(source, 60000, catalog(), CHAMPIONS)
        self.assertEqual(context.inventory_status, 'PARTIAL')
        self.assertIn('PREFIX_TRANSACTION_UNRELIABLE', context.warnings)

    def test_rune_grants_remain_unmodeled(self):
        source = game()
        source.player['perks'] = {'styles': [{'selections': [{'perk': 8304, 'var1': 9999}]}]}
        context = build_context(source, 60000, catalog(), CHAMPIONS)
        self.assertIn('UNOBSERVED_RUNE_GRANT_UNMODELED', context.warnings)
        self.assertEqual(context.inventory, ())


class RecipeChecks(unittest.TestCase):
    def setUp(self):
        self.catalog = catalog()
        self.planner = RecipePlanner(self.catalog)

    def validate(self, plan, original, budget):
        self.assertNotEqual(plan.status, 'BLOCKED')
        held, spent = tuple(sorted(original)), 0
        for step in plan.steps:
            quote = self.planner.quote(held, step.item_id)
            self.assertEqual(step, quote)
            self.assertGreaterEqual(step.cost, 0)
            spent += step.cost
            self.assertLessEqual(spent, budget)
            self.assertLessEqual(len(step.inventory_after), 6)
            held = step.inventory_after
        self.assertEqual(spent, plan.total_spend)
        self.assertEqual(plan.target_completed, plan.target_item in held)

    def test_empty_inventory_exact_and_insufficient_gold(self):
        for budget in (0, 99, 100, 349, 350, 700):
            with self.subTest(budget=budget):
                plan = self.planner.plan(3, (), budget)
                self.validate(plan, (), budget)
                self.assertEqual(plan.target_completed, budget >= 350)

    def test_existing_components_reduce_cost_once(self):
        self.assertEqual(self.planner.quote((1, 2), 3).cost, 50)
        quote = self.planner.quote((1,), 5)
        self.assertEqual(quote.cost, 150)
        self.assertEqual(quote.consumed, (1,))
        self.assertEqual(self.planner.quote((1, 1), 5).cost, 50)

    def test_transitive_components_and_exact_budget(self):
        quote = self.planner.quote((1, 2, 1), 4)
        self.assertEqual(quote.cost, 300)
        self.assertEqual(quote.consumed, (1, 1, 2))
        plan = self.planner.plan(4, (1, 2, 1), 300)
        self.validate(plan, (1, 2, 1), 300)
        self.assertTrue(plan.target_completed)

    def test_full_inventory_can_combine_but_not_add_unrelated(self):
        full = (1, 2, 6, 7, 8, 9)
        plan = self.planner.plan(3, full, 50)
        self.validate(plan, full, 50)
        self.assertTrue(plan.target_completed)
        plan = self.planner.plan(3, (6, 7, 8, 9, 10, 6), 1000)
        self.validate(plan, (6, 7, 8, 9, 10, 6), 1000)
        self.assertEqual(plan.steps, ())

    def test_multi_component_plan_preserves_budget_and_demand(self):
        plan = self.planner.plan(4, (), 300)
        self.validate(plan, (), 300)
        self.assertEqual(plan.total_spend, 300)
        self.assertEqual(plan.remaining_cost_after, 400)
        self.assertEqual(self.planner.plan(4, (), 300), plan)

    def test_already_owned_and_invalid_inputs(self):
        for inventory, budget in (((3,), 1000), ((999,), 1000), ((), None), ((), -1), ((), True)):
            self.assertEqual(self.planner.plan(3, inventory, budget).status, 'BLOCKED')

    def test_excludes_special_nonpurchasable_mode_and_boots(self):
        raw = {'20': item('OtherMap', 100, maps={'11': False}),
               '21': item('Boot', 100, tags=['Boots']),
               '22': item('Hidden', 100, inStore=False),
               '23': item('ChampionOnly', 100, requiredChampion='Ornn'),
               '24': item('Special', 100, specialRecipe=1),
               '25': item('Generated', 100, gold={'total': 100, 'base': 100, 'purchasable': False})}
        planner = RecipePlanner(catalog(raw))
        for key in raw:
            self.assertEqual(planner.plan(int(key), (), 1000).status, 'BLOCKED')

    def test_graph_cycle_missing_price_and_inconsistent_recipe(self):
        raw = {'20': item('Cycle', 100, 0, (20,)), '21': item('Missing', 100, 0, (999,)),
               '22': item('BadPrice', 500, 1, (1, 2))}
        planner = RecipePlanner(catalog(raw))
        for key in raw:
            self.assertEqual(planner.plan(int(key), (), 1000).status, 'BLOCKED')

    def test_zero_combine_cost_terminates(self):
        plan = self.planner.plan(11, (1, 2), 0)
        self.assertTrue(plan.target_completed)
        self.validate(plan, (1, 2), 0)

    def test_patch_mismatch_rejected(self):
        raw = build_item_knowledge_catalog(VERSION, raw_items={'1': item('A', 100)}, versions=[VERSION])
        wrong = CatalogView(raw, '16.17.1')
        self.assertIn('CATALOG_PATCH_UNRESOLVED', wrong.blockers)
        self.assertEqual(RecipePlanner(wrong).plan(1, (), 100).status, 'BLOCKED')

    def test_independent_flat_recipe_oracle(self):
        # Independent exhaustive multiset oracle for A+A+50. No planner quote
        # or frozen component helper is used to compute the optimum here.
        for owned in range(3):
            for budget in range(0, 351, 25):
                inventory = (1,) * owned
                plan = self.planner.plan(5, inventory, budget)
                best_credit = max(100 * bought for bought in range(3 - owned) if bought * 100 <= budget)
                expected_complete = budget >= 250 - 100 * owned
                expected_remaining = 0 if expected_complete else 250 - 100 * owned - best_credit
                self.assertEqual(plan.target_completed, expected_complete)
                self.assertEqual(plan.remaining_cost_after, expected_remaining)

    def test_breakdown_and_explanations_are_recomputable_not_final_utility(self):
        plan = self.planner.plan(3, (1,), 200)
        result = score_recipe(plan, self.catalog)
        self.assertIsNone(result['score'])
        self.assertEqual(result['diagnostic_subtotal'], sum(f['contribution'] for f in result['score_breakdown'] if f['contribution'] is not None))
        for factor in result['score_breakdown']:
            if factor['status'] == 'UNMODELED':
                self.assertIsNone(factor['value'])
                self.assertIsNone(factor['contribution'])
            for reason in factor['reasons']:
                self.assertGreater(factor['contribution'], 0)
                self.assertIn(reason, result['positive_reasons'])
        self.assertIsNone(BUILD_SCORE_WEIGHTS['ChampionSynergy'])


class ScenarioChecks(unittest.TestCase):
    def test_ten_required_scenarios_do_not_invent_combat_facts(self):
        scenarios = ('Shyvana AP double frontline', 'Shyvana AP squishy', 'AD threat', 'AP threat',
                     'high MR', 'enemy healing', 'partial inventory', 'low gold', 'component gold', 'complete gold')
        cat = catalog()
        for index, label in enumerate(scenarios):
            with self.subTest(scenario=label):
                source = game([event(1000)] if index == 6 else [])
                source.timeline[1]['participantFrames']['1']['currentGold'] = (50 if index == 7 else 200 if index == 8 else 700)
                source.timeline[1]['participantFrames']['1']['championStats']['abilityPower'] = 250
                if index in (0, 1):
                    second_enemy = {**source.enemies[0], 'participantId': 3, 'puuid': 'r'}
                    source = replace(source, enemies=(*source.enemies, second_enemy))
                    for frame in source.timeline:
                        frame['participantFrames']['3'] = deepcopy(frame['participantFrames']['2'])
                        frame['participantFrames']['3']['participantId'] = 3
                        for pid in ('2', '3'):
                            frame['participantFrames'][pid]['championStats'].update(
                                healthMax=3000 if index == 0 else 900, armor=150 if index == 0 else 30)
                # Scenario names are NOT evidence. Enemy values are only frame facts.
                stats = source.timeline[1]['participantFrames']['2']['championStats']
                if index == 2:
                    stats['attackDamage'] = 250
                if index == 3:
                    stats['abilityPower'] = 500
                if index == 4:
                    stats['magicResist'] = 200
                context = build_context(source, 60000, cat, CHAMPIONS)
                if index in (0, 1):
                    self.assertEqual(len(context.enemies), 2)
                    self.assertTrue(all(enemy.observed_stats['healthMax'] == (3000 if index == 0 else 900)
                                        for enemy in context.enemies))
                output = BuildOptimizer(cat).recommend(context)
                self.assertIsNone(output.target_item)
                self.assertEqual(output.buy_now, ())
                self.assertEqual(output.alternatives, ())
                self.assertEqual(output.status, 'BLOCKED_REVIEW_REQUIRED')
                self.assertIn('CONTEXTUAL_SCORING_UNMODELED', output.warnings)
                self.assertTrue(output.candidate_diagnostics)
                json.dumps(output.to_dict(), allow_nan=False)


if __name__ == '__main__':
    unittest.main()
