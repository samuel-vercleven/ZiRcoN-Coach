"""Serializable headless API. Abstains when the requested decision lacks proof."""
from dataclasses import asdict, dataclass

from build_optimizer.context import BuildContext
from build_optimizer.purchase import RecipePlanner
from build_optimizer.scoring import score_recipe


@dataclass(frozen=True)
class BuildRecommendation:
    status: str
    target_item: int | None
    buy_now: tuple
    score: float | None
    score_breakdown: tuple
    alternatives: tuple
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    timestamp: int
    candidate_diagnostics: tuple[dict, ...]

    def to_dict(self):
        return asdict(self)


class BuildOptimizer:
    def __init__(self, catalog):
        self.catalog = catalog
        self.planner = RecipePlanner(catalog)

    def recommend(self, context: BuildContext):
        warnings = set(context.warnings) | set(self.catalog.blockers)
        diagnostics = []
        if context.patch != self.catalog.patch:
            warnings.add('CONTEXT_CATALOG_PATCH_MISMATCH')
        if context.inventory_status != 'OBSERVED_PREFIX':
            warnings.add('INVENTORY_UNRELIABLE')
        if context.gold is None:
            warnings.add('CURRENT_GOLD_UNRESOLVED')
        if not warnings:
            plans = self.planner.candidates(context.inventory, context.gold)
            for plan in plans:
                if plan.status != 'BLOCKED':
                    diagnostics.append({'recipe_plan': plan.to_dict(), **score_recipe(plan, self.catalog)})
        warnings.update(('CONTEXTUAL_SCORING_UNMODELED', 'PURCHASE_RESTRICTIONS_UNMODELED',
                         'SHOP_ACCESS_UNMODELED', 'INVENTORY_COMPLETENESS_UNMODELED',
                         'STAT_OWNER_EXECUTION_GATE_ZERO'))
        # Sorting is for audit stability only. Never rank by price / item ID and
        # label the first entry the best contextual purchase.
        return BuildRecommendation('BLOCKED_REVIEW_REQUIRED', None, (), None, (), (),
            ('Aucun meilleur achat défendable : utilité contextuelle et légalité complète non validées.',),
            tuple(sorted(warnings)), context.timestamp, tuple(diagnostics))
