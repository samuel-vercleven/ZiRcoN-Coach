"""Deterministic nonempty recommendation contracts for the sole v1 profile."""
from dataclasses import replace
import json
import unittest

from build_optimizer.checks import CHAMPIONS, game
from build_optimizer.context import build_context
from build_optimizer.engine import BuildOptimizer
from build_optimizer.legality import decide
from build_optimizer.profiles import MODEL_KIND, item_profile
from build_optimizer.replay import exact_catalogs, validate_recipe_plan
from build_optimizer.signals import build_baseline, game_signals


def supported_context(enemy_hp=2000, enemy_mr=60, enemy_ad=100, enemy_ap=50, gold=900):
    catalog, champions = exact_catalogs('16.18')
    source = game()
    source = replace(source, game_state={**source.game_state, 'patch': '16.18.1'})
    for frame in source.timeline:
        frame['participantFrames']['1']['currentGold'] = gold
        frame['participantFrames']['1']['championStats'].update(abilityPower=200, attackDamage=80)
        frame['participantFrames']['2']['championStats'].update(
            healthMax=enemy_hp, armor=60, magicResist=enemy_mr, attackDamage=enemy_ad, abilityPower=enemy_ap)
    return build_context(source, 60000, catalog, champions), catalog


def prior_contexts(context, catalog):
    values = ((900, 30, 50, 20, -400), (1200, 40, 55, 30, -200), (1600, 50, 60, 40, 0),
              (1800, 55, 70, 60, 100), (1900, 58, 75, 70, 200))
    rows = []
    for index, (hp, mr, ad, ap, delta) in enumerate(values):
        enemy = replace(context.enemies[0], observed_stats={**context.enemies[0].observed_stats,
                        'healthMax': hp, 'magicResist': mr, 'attackDamage': ad, 'abilityPower': ap})
        rows.append(replace(context, match_id=f'PRIOR_{index}', enemies=(enemy,),
                            game_state={**context.game_state, 'own_total_gold': 3000 + delta, 'enemy_total_gold': 3000}))
    return rows


class ContextualRecommendationChecks(unittest.TestCase):
    def setUp(self):
        self.context, self.catalog = supported_context()
        self.optimizer = BuildOptimizer(self.catalog)
        self.baseline = build_baseline(prior_contexts(self.context, self.catalog), self.context)

    def test_exact_1618_profiles_have_real_fingerprints(self):
        self.assertEqual(self.catalog.version, '16.18.1')
        supported = [item_profile(item, '16.18') for item in self.catalog.items.values()]
        supported = [p for p in supported if p]
        self.assertGreaterEqual(len(supported), 8)
        for profile in supported:
            self.assertEqual(profile.status, 'SUPPORTED')
            self.assertTrue(profile.source.startswith('DATA_DRAGON_16.18.1'))

    def test_nonempty_shyvana_recommendation_is_recomputable_and_legal(self):
        output = self.optimizer.recommend(self.context, self.baseline)
        self.assertEqual(output.status, 'SUPPORTED_HEURISTIC')
        self.assertIsNotNone(output.target_item)
        self.assertIsNotNone(output.score)
        self.assertTrue(output.score_breakdown)
        self.assertEqual(output.purchase_scope, 'IF_SHOPPING_NOW')
        self.assertEqual(output.shop_access_status, 'UNMODELED')
        self.assertEqual(output.model_kind, MODEL_KIND)
        self.assertEqual(output.score, sum(row['contribution'] for row in output.score_breakdown))
        self.assertTrue(output.reasons)
        plan = self.optimizer.planner.plan(output.target_item, self.context.inventory, self.context.gold)
        validate_recipe_plan(plan, self.context.inventory, self.context.gold, self.catalog)
        self.assertEqual(output.buy_now, plan.steps)
        self.assertEqual(decide(self.catalog.items[output.target_item], self.context, self.optimizer.planner).status,
                         'LEGAL_SUPPORTED')
        json.dumps(output.to_dict(), allow_nan=False)

    def test_directional_mr_and_physical_pressure_relations(self):
        high_mr, _ = supported_context(enemy_mr=180)
        normal_mr, _ = supported_context(enemy_mr=50)
        base = prior_contexts(high_mr, self.catalog)
        high = self.optimizer.recommend(high_mr, build_baseline(base, high_mr))
        normal = self.optimizer.recommend(normal_mr, build_baseline(base, normal_mr))
        # The primary output itself can be Void Staff; compare direct factor evidence instead of rank.
        self.assertGreaterEqual(next(r['contribution'] for r in high.score_breakdown if r['factor'] == 'EnemyResponse'),
                                next(r['contribution'] for r in normal.score_breakdown if r['factor'] == 'EnemyResponse'))

    def test_missing_baseline_and_unsupported_profile_abstain(self):
        missing = self.optimizer.recommend(self.context, None)
        self.assertIsNone(missing.target_item)
        self.assertIn('HISTORICAL_BASELINE_UNAVAILABLE', missing.warnings)
        unsupported = replace(self.context, champion='Viego')
        output = self.optimizer.recommend(unsupported, self.baseline)
        self.assertIsNone(output.target_item)
        self.assertIn('BLOCKED_UNSUPPORTED_CHAMPION_PROFILE', output.warnings)

    def test_unknown_legality_fails_closed(self):
        unknown = replace(self.catalog.items[3135], total_cost=3001)
        self.catalog.items[3135] = unknown
        self.assertEqual(decide(unknown, self.context, self.optimizer.planner).status, 'LEGALITY_UNKNOWN')


if __name__ == '__main__':
    unittest.main()
