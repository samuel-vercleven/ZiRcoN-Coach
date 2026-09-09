"""Real catalog recipes under controlled budgets, NOT historical purchase advice."""
from collections import Counter
import json
from pathlib import Path

from build_optimizer.purchase import RecipePlanner
from build_optimizer.replay import exact_catalogs, validate_recipe_plan
from build_optimizer.scoring import score_recipe

PATCHES = ('16.9', '16.16', '16.17')
CONTROLLED_BUDGETS = (0, 400, 850, 2050, 3500)


def run():
    results = []
    for patch in PATCHES:
        catalog, _ = exact_catalogs(patch)
        planner = RecipePlanner(catalog)
        counts = Counter()
        exclusions = Counter()
        for item_id, view in sorted(catalog.items.items()):
            exclusions.update(view.structural_blockers)
            if view.structural_blockers or not planner._graph_valid(item_id):
                counts['excluded_targets'] += 1
                continue
            counts['structural_targets'] += 1
            # Synthetic inventories assembled from REAL recipe components, not
            # asserted to have been owned in any observed match.
            inventories = [()]
            if view.components:
                inventories.append(view.components[:1])
                inventories.append(view.components)
            for inventory in inventories:
                if len(inventory) > 6:
                    continue
                for budget in CONTROLLED_BUDGETS:
                    plan = planner.plan(item_id, inventory, budget)
                    assert plan.status != 'BLOCKED', (patch, item_id, plan.warnings)
                    validate_recipe_plan(plan, inventory, budget, catalog)
                    counts['controlled_recipe_cases'] += 1
                    counts['recipe_steps'] += len(plan.steps)
                    score = score_recipe(plan, catalog)
                    assert score['score'] is None
                    assert score['diagnostic_subtotal'] == sum(
                        f['contribution'] for f in score['score_breakdown'] if f['contribution'] is not None)
                    for factor in score['score_breakdown']:
                        if factor['reasons']:
                            assert factor['contribution'] is not None and factor['contribution'] != 0
                    assert view.restrictions_status == 'UNMODELED'
                    assert 'PURCHASE_RESTRICTIONS_UNMODELED' in plan.warnings
        assert counts['controlled_recipe_cases'] > 0 and counts['recipe_steps'] > 0, 'NO_NONEMPTY_RECIPE_EXERCISED'
        result = {'patch': patch, 'counts': dict(counts), 'structural_exclusions': dict(exclusions),
                  'recipe_invariants': 'PASS', 'purchase_legality': 'NOT_VALIDATED',
                  'gameplay_utility': 'NOT_VALIDATED'}
        results.append(result)
        print(json.dumps(result), flush=True)
    folder = Path(__file__).resolve().parents[1] / 'logs/build_optimizer'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'catalog_checks.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    return results


if __name__ == '__main__':
    run()
