"""Serializable headless API. Abstains when the requested decision lacks proof."""
from dataclasses import asdict, dataclass

from build_optimizer.context import BuildContext
from build_optimizer.purchase import RecipePlanner
from build_optimizer.scoring import score_recipe
from build_optimizer.scoring import score_contextual
from build_optimizer.profiles import MODEL_KIND, champion_profile, item_profile
from build_optimizer.legality import decide
from build_optimizer.signals import game_signals


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
    purchase_scope: str = 'IF_SHOPPING_NOW'
    shop_access_status: str = 'UNMODELED'
    model_kind: str = MODEL_KIND
    coverage: float | None = None
    confidence: str = 'UNKNOWN'
    limitations: tuple[str, ...] = ()

    def to_dict(self):
        return asdict(self)


class BuildOptimizer:
    def __init__(self, catalog):
        self.catalog = catalog
        self.planner = RecipePlanner(catalog)

    def recommend(self, context: BuildContext, baseline=None):
        warnings = set(context.warnings) | set(self.catalog.blockers)
        diagnostics = []
        if context.patch != self.catalog.patch:
            warnings.add('CONTEXT_CATALOG_PATCH_MISMATCH')
        if context.inventory_status != 'OBSERVED_PREFIX':
            warnings.add('INVENTORY_UNRELIABLE')
        if context.gold is None:
            warnings.add('CURRENT_GOLD_UNRESOLVED')
        profile = champion_profile(context.champion, context.patch)
        signals = game_signals(context, baseline)
        essential = {'CURRENT_GOLD_UNRESOLVED', 'INVENTORY_UNRELIABLE', 'CONTEXT_CATALOG_PATCH_MISMATCH', 'UNSUPPORTED_QUEUE'}
        diagnostic_context = not warnings & essential
        if profile is None:
            warnings.add('BLOCKED_UNSUPPORTED_CHAMPION_PROFILE')
        if baseline is None or signals['status'] != 'SUPPORTED':
            warnings.add('HISTORICAL_BASELINE_UNAVAILABLE')
        if not warnings & essential and profile is not None and signals['status'] == 'SUPPORTED':
            candidates = []
            for item in self.catalog.items.values():
                semantic = item_profile(item, context.patch, context.champion)
                legality = decide(item, context, self.planner)
                if semantic is None or legality.status != 'LEGAL_SUPPORTED':
                    continue
                plan = self.planner.plan(item.item_id, context.inventory, context.gold)
                if plan.status == 'BLOCKED':
                    continue
                score = score_contextual(semantic, plan, legality, signals, context, self.catalog)
                candidates.append((score, plan, legality, semantic))
            if candidates:
                candidates.sort(key=lambda x: (-x[0]['score'], x[0]['target_item']))
                best, plan, legality, semantic = candidates[0]
                offensive = next((x[0] for x in candidates[1:] if {'BURST', 'RAW_DAMAGE', 'SUSTAINED_DAMAGE'} & x[3].traits), None)
                defensive = next((x[0] for x in candidates[1:] if {'SURVIVABILITY', 'STASIS', 'SPELL_SHIELD'} & x[3].traits), None)
                alternatives = tuple(x for x in (offensive, defensive) if x is not None)
                coverage = 1.0
                return BuildRecommendation('SUPPORTED_HEURISTIC', best['target_item'], tuple(plan.steps), best['score'],
                    tuple(best['score_breakdown']), alternatives, tuple(best['positive_reasons']),
                    tuple(sorted(set(context.warnings) | set(best['warnings']))), context.timestamp,
                    tuple(), 'IF_SHOPPING_NOW', 'UNMODELED', MODEL_KIND, coverage,
                    'MEDIUM', ('Heuristic product contract; not a combat simulation or optimality proof.',))
        if diagnostic_context:
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
