"""Economic diagnostics only. Unsupported gameplay factors are not numeric zeros."""
from dataclasses import asdict, dataclass

BUILD_SCORE_WEIGHTS = {
    'ChampionSynergy': None,
    'EnemyCounter': None,
    'CurrentBuildSynergy': None,
    'GameNeed': None,
    'PowerSpikeValue': None,
    'EconomyValue': 1,
    'PurchaseFeasibility': None,
    'RedundancyPenalty': None,
    'IncompatibilityPenalty': None,
}
# 1 preserves the unit of the diagnostic fraction: recipe cost covered / total
# price. It is NOT a calibrated gameplay weight or a cross-item utility scale.


@dataclass(frozen=True)
class Contribution:
    factor: str
    status: str
    value: float | None
    weight: int | None
    contribution: float | None
    reasons: tuple[str, ...]
    supporting_facts: dict


def score_recipe(plan, catalog):
    item = catalog.items[plan.target_item]
    factors = []
    for name, weight in BUILD_SCORE_WEIGHTS.items():
        if name == 'EconomyValue' and plan.remaining_cost_after is not None:
            covered = item.total_cost - plan.remaining_cost_after
            value = covered / item.total_cost
            factors.append(Contribution(name, 'EXPERIMENTAL', value, weight, value * weight,
                (f'{covered}/{item.total_cost} PO de recette couvertes après le plan diagnostique.',) if value else (),
                {'target_total_cost': item.total_cost, 'remaining_cost': plan.remaining_cost_after,
                 'plan_spend': plan.total_spend, 'source': 'ITEM_KNOWLEDGE_RECIPE'}))
        else:
            factors.append(Contribution(name, 'UNMODELED', None, weight, None, (), {}))
    return {'target_item': plan.target_item, 'score': None, 'status': 'PARTIAL',
            'diagnostic_subtotal': sum(f.contribution for f in factors if f.contribution is not None),
            'score_breakdown': [asdict(f) for f in factors],
            'positive_reasons': [reason for f in factors if f.contribution is not None and f.contribution > 0 for reason in f.reasons],
            'negative_reasons': [reason for f in factors if f.contribution is not None and f.contribution < 0 for reason in f.reasons],
            'warnings': ['NO_CONTEXTUAL_UTILITY_CONTRACT', 'ECONOMIC_SUBTOTAL_IS_NOT_FINAL_SCORE']}
