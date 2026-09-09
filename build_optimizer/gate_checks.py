"""Adversarial checks of the independent audit and the headless product boundary."""
from dataclasses import replace
import json
import unittest
from unittest.mock import patch

from build_optimizer.checks import CHAMPIONS, catalog, game
from build_optimizer.context import build_context
from build_optimizer.engine import BuildOptimizer
from build_optimizer.purchase import PurchaseStep, RecipePlan, RecipePlanner
from build_optimizer.replay import validate_recipe_plan
from build_optimizer.validation import product_zero_gate


class GateChecks(unittest.TestCase):
    def setUp(self):
        self.catalog = catalog()
        self.planner = RecipePlanner(self.catalog)

    def test_unrelated_owned_item_cannot_pay_for_recipe(self):
        # The old invoice-only audit accepted this: 350 - 120 = 230,
        # but Filler (6) is not a component of AB (3).
        step = PurchaseStep(3, 230, (6,), (3,))
        forged = RecipePlan(3, 'PARTIAL', (step,), 230, 350, 0, True, ())
        with self.assertRaisesRegex(AssertionError, 'INVALID_RECIPE_COMPONENTS'):
            validate_recipe_plan(forged, (6,), 230, self.catalog)

    def test_repeated_component_credit_cannot_exceed_recipe_demand(self):
        step = PurchaseStep(3, 50, (1, 1, 1), (3,))
        forged = RecipePlan(3, 'PARTIAL', (step,), 50, 50, 0, True, ())
        with self.assertRaisesRegex(AssertionError, 'INVALID_RECIPE_COMPONENTS'):
            validate_recipe_plan(forged, (1, 1, 1), 50, self.catalog)

    def test_ancestor_and_descendants_cannot_both_receive_credit(self):
        step = PurchaseStep(4, 50, (1, 2, 3), (4,))
        forged = RecipePlan(4, 'PARTIAL', (step,), 50, 50, 0, True, ())
        with self.assertRaisesRegex(AssertionError, 'INVALID_RECIPE_COMPONENTS'):
            validate_recipe_plan(forged, (1, 2, 3), 50, self.catalog)

    def test_excluded_item_cannot_pass_invoice_audit(self):
        excluded = self.catalog.items[3]
        self.catalog.items[3] = replace(excluded, structural_blockers=('NOT_IN_STORE',))
        step = PurchaseStep(3, 350, (), (3,))
        forged = RecipePlan(3, 'PARTIAL', (step,), 350, 350, 0, True, ())
        with self.assertRaisesRegex(AssertionError, 'ITEM_STRUCTURALLY_BLOCKED'):
            validate_recipe_plan(forged, (), 350, self.catalog)

    def test_unrelated_step_cannot_be_part_of_target_plan(self):
        step = PurchaseStep(6, 120, (), (6,))
        forged = RecipePlan(3, 'PARTIAL', (step,), 120, 350, 350, False, ())
        with self.assertRaisesRegex(AssertionError, 'STEP_NOT_IN_TARGET_RECIPE'):
            validate_recipe_plan(forged, (), 120, self.catalog)

    def test_quote_rejects_unknown_bool_and_overcapacity_inventory(self):
        for held in ((999,), (True,), (6,) * 7):
            with self.subTest(held=held):
                self.assertIsNone(self.planner.quote(held, 3))

    def test_invalid_target_id_cannot_alias_integer_item(self):
        for target in (True, 1.0, '1', None, -1, 999):
            with self.subTest(target=target):
                self.assertIsNone(self.planner.quote((), target))
                self.assertEqual(self.planner.plan(target, (), 500).status, 'BLOCKED')

    def test_valid_transitive_and_repeated_recipes_pass_independent_audit(self):
        for target, held, gold in ((3, (1, 2), 50), (4, (1, 2, 1), 300),
                                   (5, (1, 1), 50), (4, (), 300)):
            plan = self.planner.plan(target, held, gold)
            self.assertTrue(plan.steps)
            validate_recipe_plan(plan, held, gold, self.catalog)

    def test_budget_and_slot_violations_are_detected(self):
        plan = self.planner.plan(3, (), 350)
        with self.assertRaisesRegex(AssertionError, 'BUDGET_EXCEEDED'):
            validate_recipe_plan(plan, (), 349, self.catalog)
        held = (6, 7, 8, 9, 10, 6)
        step = PurchaseStep(3, 350, (), tuple(sorted((*held, 3))))
        forged = RecipePlan(3, 'PARTIAL', (step,), 350, 350, 0, True, ())
        with self.assertRaisesRegex(AssertionError, 'SLOT_CAPACITY_EXCEEDED'):
            validate_recipe_plan(forged, held, 350, self.catalog)

    def test_search_truncation_never_claims_optimality(self):
        with patch('build_optimizer.purchase.MAX_SEARCH_STATES', 0):
            plan = self.planner.plan(4, (), 700)
        self.assertEqual(plan.status, 'PARTIAL')
        self.assertIn('SEARCH_LIMIT_REACHED', plan.warnings)

    def test_end_to_end_serialization_and_diagnostic_explanations(self):
        context = build_context(game(), 60000, self.catalog, CHAMPIONS)
        output = BuildOptimizer(self.catalog).recommend(context)
        payload = json.loads(json.dumps(output.to_dict(), allow_nan=False))
        self.assertEqual(payload['timestamp'], context.timestamp)
        self.assertIsNone(payload['target_item'])
        self.assertIsNone(payload['score'])
        self.assertEqual(payload['buy_now'], [])
        self.assertTrue(payload['candidate_diagnostics'])
        for diagnostic in payload['candidate_diagnostics']:
            factors = diagnostic['score_breakdown']
            supported = [f for f in factors if f['contribution'] is not None]
            self.assertEqual(diagnostic['diagnostic_subtotal'], sum(f['contribution'] for f in supported))
            self.assertIsNone(diagnostic['score'])
            for factor in supported:
                self.assertEqual(factor['contribution'], factor['value'] * factor['weight'])
            self.assertEqual(diagnostic['positive_reasons'],
                             [r for f in supported if f['contribution'] > 0 for r in f['reasons']])
            self.assertEqual(diagnostic['negative_reasons'],
                             [r for f in supported if f['contribution'] < 0 for r in f['reasons']])

    def test_caller_flags_do_not_validate_missing_gameplay_contracts(self):
        context = build_context(game(), 60000, self.catalog, CHAMPIONS)
        asserted = replace(context, game_state={**context.game_state,
                           'shop_access': 'VALIDATED', 'inventory_completeness': 'VALIDATED'})
        output = BuildOptimizer(self.catalog).recommend(asserted)
        self.assertIsNone(output.target_item)
        self.assertEqual(output.buy_now, ())
        self.assertIn('PURCHASE_RESTRICTIONS_UNMODELED', output.warnings)
        self.assertIn('CONTEXTUAL_SCORING_UNMODELED', output.warnings)

    def test_green_commands_and_empty_outputs_cannot_freeze_product(self):
        commands = [{'command': name, 'passed': True} for name in
                    ('stable_base', 'unit_scenarios', 'product_gate_checks',
                     'real_catalog_recipes', 'golden_replay', 'historical_batch', 'contextual_replay')]
        context = build_context(game(), 60000, self.catalog, CHAMPIONS)
        replay = {'rows': [{'recommendation': BuildOptimizer(self.catalog).recommend(context).to_dict()}],
                  'temporal_integrity': 'PASS'}
        contextual = {'counts': {'nonempty_recommendations': 1}, 'invalid_purchases': 0,
                      'untraceable_explanations': 0, 'score_recomputation_errors': 0}
        gate = product_zero_gate(commands, replay, True, contextual)
        self.assertEqual(gate['freeze'], 'NO FREEZE')
        self.assertEqual(gate['status'], 'REVIEW_REQUIRED')
        self.assertEqual(gate['gates']['Purchase feasibility (emitted recommendations)'], 'PASS')
        self.assertEqual(gate['nonempty_recommendations'], 1)
        self.assertEqual(gate['final_scores_exercised'], 1)
        self.assertEqual(gate['fatal_scoring_errors'], 0)

    def test_missing_tests_or_replay_are_not_zero_error_evidence(self):
        gate = product_zero_gate([], {}, True, {})
        self.assertEqual(gate['status'], 'FAIL')
        self.assertIsNone(gate['invalid_purchase_count'])
        self.assertIsNone(gate['unexplained_recommendations'])
        self.assertIsNone(gate['future_information_leakage'])

    def test_nonempty_output_is_not_automatically_validated(self):
        output = {'target_item': 3, 'buy_now': [3], 'score': 123}
        gate = product_zero_gate([], {'rows': [{'recommendation': output}]}, True, {})
        self.assertEqual(gate['nonempty_recommendations'], 0)
        self.assertIsNone(gate['invalid_purchase_count'])
        self.assertIsNone(gate['unexplained_recommendations'])
        self.assertEqual(gate['freeze'], 'NO FREEZE')


if __name__ == '__main__':
    unittest.main()
